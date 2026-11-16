"""Real orchestration with bounded, recorded GitHub/LLM boundaries; no paid calls."""

import hashlib
import io
import json
import zipfile
from contextlib import contextmanager

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from smartregression.adapters.github_repository import GithubRepository
from smartregression.api.main import create_app
from smartregression.application.repository_analysis import RepositoryService, narrative_input
from smartregression.contracts.repository import RepositoryAnalysisRequest, RepositoryLookup
from smartregression.contracts.stages import StageAnalysisReport

BASE, TARGET = "a" * 40, "b" * 40
FILES = {
    "src/__init__.py": b"",
    "src/math.py": b"def add(a, b):\n    return a + b\n",
    "app.py": b"from src.math import add\n\ndef run():\n    return add(1, 2)\n",
}


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def remote(tmp_path, *, redirect=False, corrupt=False, tree_mutation=None, snapshot_error=None):
    def handle(request):
        path = request.url.path
        if redirect:
            return httpx.Response(302, headers={"location": "http://127.0.0.1/secret"})
        if request.url.host == "codeload.github.com":
            sha = path.rsplit("/", 1)[-1]
            files = dict(FILES)
            if sha == TARGET:
                files["src/math.py"] = b"def add(a, b):\n    return max(0, a + b)\n"
            archive = io.BytesIO()
            with zipfile.ZipFile(archive, "w") as zipped:
                for name, raw in files.items():
                    zipped.writestr("repo-" + sha + "/" + name, b"bad" if corrupt else raw)
            return httpx.Response(200, content=archive.getvalue())
        if path.endswith("/commits"):
            return httpx.Response(
                200,
                json=[
                    {
                        "sha": sha,
                        "commit": {"message": "change", "author": {"date": "2026-11-10T00:00:00Z"}},
                    }
                    for sha in (TARGET, BASE)
                ],
            )
        if "/git/commits/" in path:
            if snapshot_error == "github_rate_limit":
                return httpx.Response(429)
            if snapshot_error == "github_timeout":
                raise httpx.ReadTimeout("private transport details", request=request)
            sha = path.rsplit("/", 1)[-1]
            return httpx.Response(200, json={"sha": sha, "tree": {"sha": sha}})
        if "/git/trees/" in path:
            sha = path.rsplit("/", 1)[-1]
            files = dict(FILES)
            if sha == TARGET:
                files["src/math.py"] = b"def add(a, b):\n    return max(0, a + b)\n"
            tree = {
                "sha": sha,
                "truncated": False,
                "tree": [
                    dict(path=n, type="blob", mode="100644", sha=blob(v), size=len(v))
                    for n, v in files.items()
                ],
            }
            if tree_mutation:
                tree_mutation(tree)
            return httpx.Response(200, json=tree)
        return httpx.Response(
            200,
            json={
                "full_name": "owner/repo",
                "private": False,
                "default_branch": "main",
                "language": "Python",
            },
        )

    return GithubRepository(
        "https://github.com/owner/repo",
        tmp_path,
        httpx.Client(transport=httpx.MockTransport(handle), follow_redirects=False),
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/a/b",
        "https://github.com.evil.test/a/b",
        "https://github.com/a/b?token=secret",
        "https://user:secret@github.com/a/b",
        "https://127.0.0.1/a/b",
        "https://github.com/a/../b",
        "file:///tmp/repo",
    ],
)
def test_reject_unsafe_repository_url(url):
    with pytest.raises(ValidationError):
        RepositoryLookup(repository_url=url)


def test_static_analysis_and_routes_preserve_real_snapshot_identity(tmp_path):
    @contextmanager
    def factory(url):
        assert url == "https://github.com/owner/repo"
        yield remote(tmp_path)

    service = RepositoryService(factory, None)
    with TestClient(create_app(repository_service=service)) as client:
        info = client.post(
            "/repositories/inspect", json={"repository_url": "https://github.com/owner/repo"}
        )
        assert info.status_code == 200
        assert info.json()["commits"][0]["sha"] == TARGET
        result = client.post(
            "/repository-analyses",
            json={
                "repository_url": "https://github.com/owner/repo",
                "base": BASE,
                "target": TARGET,
                "use_llm": False,
            },
        )
    assert result.status_code == 200, result.text
    body = result.json()
    report = body["report"]
    assert report["data_kind"] == "real"
    assert report["identity"]["target"]["commit"] == TARGET
    assert report["stages"]["changes"]["data"]["components"]
    assert any(c["path"] == "app.py" for c in report["stages"]["impact"]["data"]["candidates"])
    assert body["narrative"]["status"] == "not_run"
    assert body["selection_status"] == body["execution_status"] == "not_run"
    payload = narrative_input(
        body["repository"], body["files"], StageAnalysisReport.model_validate(report)
    )
    assert "return max" not in json.dumps(payload)
    assert "excerpt" not in json.dumps(payload)


def test_redirect_is_not_followed(tmp_path):
    with pytest.raises(ValueError, match="github_redirect_rejected"):
        remote(tmp_path, redirect=True).inspect()


def test_downloaded_blob_must_match_git_identity(tmp_path):
    source = remote(tmp_path, corrupt=True)
    with pytest.raises(ValueError, match="snapshot_mismatch"):
        source.snapshot_entries(TARGET)


def test_egress_consent_required():
    with pytest.raises(ValidationError):
        RepositoryAnalysisRequest(
            repository_url="https://github.com/owner/repo",
            base=BASE,
            target=TARGET,
            use_llm=True,
            allow_metadata_egress=False,
        )


def test_static_mode_and_invalid_consent_never_invoke_provider(tmp_path):
    class MustNotCall:
        def explain(self, payload, *, run_id):
            raise AssertionError("provider must not be called")

    @contextmanager
    def factory(url):
        yield remote(tmp_path)

    with TestClient(
        create_app(repository_service=RepositoryService(factory, MustNotCall()))
    ) as client:
        body = dict(repository_url="https://github.com/owner/repo", base=BASE, target=TARGET)
        denied = client.post("/repository-analyses", json=body | dict(use_llm=True))
        assert denied.status_code == 422
        static = client.post("/repository-analyses", json=body | dict(use_llm=False))
        assert static.status_code == 200
        assert static.json()["narrative"]["status"] == "not_run"


def test_recognized_secret_in_question_is_blocked_before_network():
    def must_not_read(url):
        raise AssertionError("request must stop before source acquisition")

    service = RepositoryService(must_not_read, None)
    body = RepositoryAnalysisRequest(
        repository_url="https://github.com/owner/repo",
        base=BASE,
        target=TARGET,
        use_llm=True,
        allow_metadata_egress=True,
        question='Explain this: api_key="synthetic-secret-for-test"',
    )
    with pytest.raises(ValueError, match="sensitive_question"):
        service.analyze(body)


@pytest.mark.parametrize("code", ["github_rate_limit", "github_timeout", "repository_limit"])
def test_snapshot_failure_keeps_actionable_safe_error_at_web_boundary(tmp_path, code):
    @contextmanager
    def factory(url):
        yield remote(
            tmp_path,
            snapshot_error=code,
            tree_mutation=(lambda tree: tree["tree"][0].update(size=1_000_001))
            if code == "repository_limit"
            else None,
        )

    with TestClient(create_app(repository_service=RepositoryService(factory, None))) as client:
        response = client.post(
            "/repository-analyses",
            json={
                "repository_url": "https://github.com/owner/repo",
                "base": BASE,
                "target": TARGET,
                "use_llm": False,
            },
        )
    assert response.status_code == 422
    assert response.json()["message"] == code
    assert "private transport details" not in response.text


def test_hostile_origin_and_validation_errors_do_not_echo_input():
    client = TestClient(create_app())
    response = client.post(
        "/repositories/inspect",
        headers={"origin": "https://attacker.test"},
        json={"repository_url": "https://github.com/owner/repo"},
    )
    assert response.status_code == 403
    response = client.post(
        "/repositories/inspect", json={"repository_url": "https://user:secret@github.com/a/b"}
    )
    assert response.status_code == 422
    assert "secret" not in response.text


@pytest.mark.parametrize(
    "mutate",
    [
        lambda tree: tree.update(truncated=True),
        lambda tree: tree["tree"][0].update(mode="120000"),
        lambda tree: tree["tree"][0].update(path="../escape.py"),
        lambda tree: tree["tree"][0].update(size=1_000_001),
    ],
)
def test_unsafe_or_incomplete_snapshots_fail_before_archive_read(tmp_path, mutate):
    with pytest.raises(ValueError):
        remote(tmp_path, tree_mutation=mutate).snapshot_entries(TARGET)


def test_request_body_limit_and_host_protection():
    client = TestClient(create_app())
    response = client.post(
        "/repositories/inspect", content=b"x" * 8193, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 413
    response = client.post(
        "/repositories/inspect",
        headers={"host": "attacker.test"},
        json={"repository_url": "https://github.com/owner/repo"},
    )
    assert response.status_code == 403
    response = client.post(
        "/repositories/inspect", content="{}", headers={"Content-Type": "text/plain"}
    )
    assert response.status_code == 415
