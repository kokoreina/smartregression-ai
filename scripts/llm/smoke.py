"""Opt-in synthetic G1 proof. Never runs fixture code or accepts repository input."""

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from smartregression.adapters.git_local import LocalGit
from smartregression.adapters.llm.budget import BudgetLedger
from smartregression.adapters.llm.gemini import GeminiSettings
from smartregression.application.gemini_runtime import ProposalRuntime, RuntimePolicy
from smartregression.application.snapshots import RepositoryAuthorization, prepare_snapshots
from smartregression.composition import gemini_provider
from smartregression.contracts.stages import StageEvidence
from smartregression.contracts.workflow import (
    ProposalRequest,
    context_fingerprint,
    evidence_fingerprint,
    inventory_fingerprint,
)
from smartregression.core.evidence.resolution import resolve_source, source_lines
from smartregression.gemini_config import GeminiCredential

FIXTURE_VERSION = "s3-g1-synthetic-v1"
TESTS = (
    "from src.math_demo import add, multiply\n\n"
    "def test_add():\n    assert add(1, 2) == 3\n\n"
    "def test_add_negative():\n    assert add(-2, 1) == -1\n\n"
    "def test_multiply():\n    assert multiply(2, 3) == 6\n"
)


def safe_directory(path: Path) -> Path:
    path = path.absolute()
    if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
        raise ValueError("unsafe_smoke_directory")
    path.mkdir(parents=True, exist_ok=True)
    return path


def git(repo: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0")
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.hooksPath=",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "user.name=Synthetic Smoke",
            "-c",
            "user.email=synthetic@example.invalid",
            "-C",
            str(repo),
            *args,
        ],
        capture_output=True,
        timeout=15,
        env=env,
        check=True,
    )
    return result.stdout.decode().strip()


def synthetic_request(directory: Path, policy: RuntimePolicy, run_id: str) -> ProposalRequest:
    repo = safe_directory(directory / "repository")
    safe_directory(repo / "src")
    safe_directory(repo / "tests")
    (repo / "src/math_demo.py").write_text(
        "def add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b\n",
        encoding="utf-8",
    )
    (repo / "tests/test_math.py").write_text(TESTS, encoding="utf-8")
    git(repo, "init")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Synthetic base")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "src/math_demo.py").write_text(
        "def add(a, b):\n    return max(0, a + b)\n\ndef multiply(a, b):\n    return a * b\n",
        encoding="utf-8",
    )
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Synthetic target")
    target = git(repo, "rev-parse", "HEAD")
    pair = prepare_snapshots(
        LocalGit(repo),
        authorization=RepositoryAuthorization("synthetic-g1", repo),
        repository_id="synthetic-g1",
        base=base,
        target=target,
    )

    def identity(snapshot):
        return dict(
            repository_id="synthetic-g1",
            commit=snapshot.manifest.commit,
            snapshot_id=snapshot.manifest.snapshot_id,
        )

    base_identity = identity(pair.base)
    target_identity = identity(pair.target)
    names = [n.name for n in ast.parse(TESTS).body if isinstance(n, ast.FunctionDef)]
    inventory = dict(
        snapshot=target_identity,
        framework="pytest",
        completeness="complete",
        test_ids=["tests/test_math.py::" + n for n in names],
    )
    sources = []
    contexts = []
    evidence = []
    for rank, (snapshot, path, start, end, name) in enumerate(
        [
            (pair.base, "src/math_demo.py", 1, 2, "base-add"),
            (pair.target, "src/math_demo.py", 1, 2, "synthetic-e1"),
            (pair.target, "tests/test_math.py", 6, 7, "synthetic-e2"),
        ],
        1,
    ):
        data = snapshot.contents[[f.path for f in snapshot.manifest.files].index(path)]
        text = "".join(data.decode().splitlines(keepends=True)[start - 1 : end])
        source = dict(
            snapshot=identity(snapshot),
            index_id="synthetic-index",
            configuration_id=FIXTURE_VERSION,
        )
        if source not in sources:
            sources.append(source)
        reference = source | dict(
            id=name,
            path=path,
            location=dict(line_start=start, line_end=end),
            content_sha256=hashlib.sha256(text.encode()).hexdigest(),
            rank=rank,
        )
        contexts.append(dict(reference=reference, text=text))
        if name != "base-add":
            item = StageEvidence.model_validate(
                dict(
                    id=name,
                    snapshot=identity(snapshot),
                    path=path,
                    location=reference["location"],
                    excerpt="\n".join(source_lines(data.decode())[start - 1 : end]),
                    support="unverified",
                )
            )
            item = resolve_source(item, data)
            if item.resolution != "resolved":
                raise ValueError("synthetic_evidence_mismatch")
            evidence.append(item.model_dump(mode="json"))
    retrieval = dict(sources=sources, items=[c["reference"] for c in contexts])
    evidence_payload = dict(items=evidence)
    return ProposalRequest.model_validate(
        dict(
            schema_version="3.0.0",
            inventory=inventory,
            retrieval=retrieval,
            evidence=evidence_payload,
            context=contexts,
            provenance=dict(
                identity=dict(
                    repository_id="synthetic-g1",
                    run_id=run_id,
                    base=base_identity,
                    target=target_identity,
                    comparison_mode="direct_two_tree",
                ),
                inventory_sha256=inventory_fingerprint(inventory),
                context_sha256=context_fingerprint(retrieval),
                evidence_sha256=evidence_fingerprint(evidence_payload),
                prompt_version="proposal/1",
                configuration_id=policy.configuration_id,
                provider="gemini",
                model="gemini-3.5-flash-lite",
            ),
        )
    )


def credential_environment(path: Path | None) -> dict[str, str]:
    env = {k: os.environ[k] for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY") if k in os.environ}
    if path is not None:
        if path.is_symlink() or path.stat().st_size > 65536:
            raise ValueError("invalid_secret_file")
        values = {}
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.removeprefix("export ").split("=", 1)
            key = key.strip()
            if key not in {"GEMINI_API_KEY", "GOOGLE_API_KEY"}:
                continue
            if key in values:
                raise ValueError("duplicate_secret_configuration")
            values[key] = value.strip().strip("\"'")
        for key, value in values.items():
            if key in env and env[key] != value:
                raise ValueError("conflicting_secret_sources")
            env[key] = value
    return env


def fixture_support(result) -> bool:
    if result.status != "completed" or not result.data or not result.data.suggestions:
        return False
    return any(
        s.test_id == "tests/test_math.py::test_add_negative" for s in result.data.suggestions
    ) and all(
        s.test_id in {"tests/test_math.py::test_add", "tests/test_math.py::test_add_negative"}
        and set(s.evidence_ids) <= {"synthetic-e1", "synthetic-e2"}
        for s in result.data.suggestions
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--session-root", type=Path, required=True)
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args(argv)
    try:
        if not args.session_root.resolve().is_relative_to(Path(__file__).resolve().parents[2]):
            raise ValueError("unsafe_smoke_directory")
        root = safe_directory(args.session_root)
        run_id = uuid.uuid4().hex
        directory = safe_directory(root / "runs" / run_id)
        policy = RuntimePolicy()
        request = synthetic_request(directory, policy, run_id)
        frozen = request.model_dump_json()
        digest = hashlib.sha256(frozen.encode()).hexdigest()
        summary = dict(
            fixture=FIXTURE_VERSION,
            data_kind="demo",
            run_id=run_id,
            timestamp=datetime.now(UTC).isoformat(),
            request_sha256=digest,
            configuration_id=policy.configuration_id,
            live_requested=args.live,
            selection="not_run",
            execution="not_run",
            g1=False,
        )
        project = Path(__file__).resolve().parents[2]
        paths = [
            "backend/src/smartregression/adapters/llm/gemini.py",
            "backend/src/smartregression/adapters/llm/budget.py",
            "backend/src/smartregression/application/gemini_runtime.py",
            "backend/src/smartregression/gemini_config.py",
            "scripts/llm/smoke.py",
        ]
        summary["implementation_sha256"] = hashlib.sha256(
            b"".join(p.encode() + b"\0" + (project / p).read_bytes() for p in paths)
        ).hexdigest()
        (directory / "request.synthetic.json").write_text(frozen, encoding="utf-8")
        if args.live:
            credential = GeminiCredential.from_environment(credential_environment(args.env_file))
            transport = gemini_provider(
                api_key=credential.api_key,
                settings=GeminiSettings(
                    api_version=policy.api_version, max_output_tokens=policy.output_tokens
                ),
            )
            ledger = BudgetLedger(root / "budget.json", session_id="s3-g1-synthetic-v1")
            runtime = ProposalRuntime(transport, ledger, policy)
            call_started = time.monotonic()
            result = runtime.run(request, authorized_sha256=digest)
            (directory / "provider-result.json").write_text(
                result.model_dump_json(indent=2), encoding="utf-8"
            )
            summary.update(
                status=result.status,
                error_code=result.error_code,
                attempts=result.attempts,
                actual_model_version=result.actual_model_version,
                usage=result.usage.model_dump(mode="json") if result.usage else None,
                g1=fixture_support(result),
                diagnostic=transport.diagnostic,
                counted_input_tokens=runtime.counted_input_tokens,
                runtime_seconds=time.monotonic() - call_started,
            )
        else:
            summary["status"] = "dry_run_no_network"
        summary["source_sha"] = git(Path(__file__).resolve().parents[2], "rev-parse", "HEAD")
        (directory / "evidence.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 0 if not args.live or summary["g1"] else 1
    except Exception as exc:
        # Stable local codes only; never show raw SDK/validation/secret-file values.
        allowed = {
            "missing_gemini_api_key",
            "invalid_gemini_api_key",
            "conflicting_gemini_api_keys",
            "conflicting_secret_sources",
            "invalid_secret_file",
            "duplicate_secret_configuration",
        }
        code = str(exc) if isinstance(exc, ValueError) and str(exc) in allowed else "smoke_failed"
        print(json.dumps({"status": "failed", "error_code": code, "g1": False}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
