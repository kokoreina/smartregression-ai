"""Synthetic fixture provenance and explicit secret-file parsing, without inference."""

import hashlib
import importlib.util
from pathlib import Path

import pytest

from smartregression.application.gemini_runtime import RuntimePolicy

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("gemini_smoke", ROOT / "scripts/llm/smoke.py")
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


def test_synthetic_snapshots_and_evidence_match_bytes(tmp_path):
    request = smoke.synthetic_request(tmp_path, RuntimePolicy(), "fixture-test")
    assert request.provenance.identity.base.commit != request.provenance.identity.target.commit
    assert request.inventory.test_ids == [
        "tests/test_math.py::test_add",
        "tests/test_math.py::test_add_negative",
        "tests/test_math.py::test_multiply",
    ]
    assert len(request.context) == 3
    for context in request.context:
        assert hashlib.sha256(context.text.encode()).hexdigest() == context.reference.content_sha256
    assert (
        request.evidence.items[-1].excerpt
        == "def test_add_negative():\n    assert add(-2, 1) == -1"
    )
    assert all(
        e.resolution == "resolved" and e.verification_reason == "source_span_verified"
        for e in request.evidence.items
    )


def test_secret_file_is_explicit_and_conflicts_are_rejected(tmp_path, monkeypatch):
    for key in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
    path = tmp_path / "secret.env"
    path.write_text('GEMINI_API_KEY="synthetic-secret"\nIGNORED=value\n')
    assert smoke.credential_environment(None) == {}
    assert smoke.credential_environment(path) == {"GEMINI_API_KEY": "synthetic-secret"}
    monkeypatch.setenv("GEMINI_API_KEY", "other-synthetic")
    with pytest.raises(ValueError, match="conflicting_secret_sources"):
        smoke.credential_environment(path)


def test_outside_workspace_target_is_rejected_without_creation(capsys):
    target = ROOT.parent / "forbidden-smoke-output"
    assert not target.exists()
    assert smoke.main(["--session-root", str(target)]) == 2
    assert not target.exists() and "smoke_failed" in capsys.readouterr().out
