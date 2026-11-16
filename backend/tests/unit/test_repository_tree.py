"""Tree browsing reads only Git metadata, independently of analysis and Gemini."""

from contextlib import contextmanager

import httpx
import pytest
from fastapi.testclient import TestClient

from smartregression.adapters.github_repository import GithubRepository
from smartregression.api.main import create_app
from smartregression.application.repository_analysis import RepositoryService

COMMIT, TREE, BLOB = "a" * 40, "b" * 40, "c" * 40


def fixture_client(tmp_path, mutate=None, status=200):
    calls = []

    def handle(request):
        calls.append(str(request.url))
        assert request.url.host == "api.github.com", "Must not download an archive or file"
        path = request.url.path
        if "/git/commits/" in path:
            return httpx.Response(status, json={"sha": COMMIT, "tree": {"sha": TREE}})
        if "/git/trees/" in path:
            data = {
                "sha": TREE,
                "truncated": False,
                "tree": [
                    {"path": "src", "type": "tree", "mode": "040000", "sha": TREE},
                    {
                        "path": "src/app.js",
                        "type": "blob",
                        "mode": "100644",
                        "sha": BLOB,
                        "size": 25,
                    },
                    {
                        "path": "demo.mov",
                        "type": "blob",
                        "mode": "100644",
                        "sha": BLOB,
                        "size": 51_384_541,
                    },
                    {"path": "link", "type": "blob", "mode": "120000", "sha": BLOB, "size": 8},
                    {"path": "vendor", "type": "commit", "mode": "160000", "sha": BLOB},
                ],
            }
            if mutate:
                mutate(data)
            return httpx.Response(200, json=data)
        return httpx.Response(200, json={"private": False, "full_name": "owner/repo"})

    @contextmanager
    def factory(url):
        with httpx.Client(transport=httpx.MockTransport(handle)) as client:
            yield GithubRepository(url, tmp_path, client)

    return TestClient(create_app(repository_service=RepositoryService(factory, None))), calls


def request_tree(client, **kwargs):
    return client.post(
        "/repositories/tree",
        json={
            "repository_url": "https://github.com/owner/repo",
            "commit": COMMIT,
        },
        **kwargs,
    )


def test_tree_works_for_large_non_python_repo_without_downloading_sources(tmp_path):
    client, calls = fixture_client(tmp_path)
    response = request_tree(client)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["commit"] == COMMIT and body["tree_sha"] == TREE
    entries = {e["path"]: e for e in body["entries"]}
    assert entries["src"]["kind"] == "directory"
    assert entries["src/app.js"]["kind"] == "file"
    assert entries["demo.mov"]["size"] == 51_384_541
    assert entries["link"]["kind"] == "symlink"
    assert entries["vendor"]["kind"] == "submodule"
    assert len(calls) == 3


@pytest.mark.parametrize(
    "mutate, code",
    [
        (lambda x: x.update(truncated=True), "repository_tree_incomplete"),
        (lambda x: x.update(sha=BLOB), "snapshot_mismatch"),
        (lambda x: x["tree"][1].update(path="../escape.js"), "github_invalid_response"),
        (lambda x: x["tree"].append(x["tree"][1]), "github_invalid_response"),
        (
            lambda x: x["tree"][0].update(type="blob", mode="100644", size=3),
            "github_invalid_response",
        ),
        (lambda x: x["tree"][1].update(size=-1), "github_invalid_response"),
        (lambda x: x["tree"][1].update(mode="160000"), "github_invalid_response"),
        (lambda x: x.update(tree=x["tree"] * 1001), "repository_tree_limit"),
    ],
)
def test_invalid_or_incomplete_tree_is_not_claimed_complete(tmp_path, mutate, code):
    client, _ = fixture_client(tmp_path, mutate=mutate)
    response = request_tree(client)
    assert response.status_code == 422
    assert response.json()["message"] == code


def test_empty_tree_is_valid(tmp_path):
    client, _ = fixture_client(tmp_path, mutate=lambda x: x.update(tree=[]))
    response = request_tree(client)
    assert response.status_code == 200
    assert response.json()["entries"] == []


def test_tree_rate_limit_is_actionable(tmp_path):
    client, _ = fixture_client(tmp_path, status=429)
    response = request_tree(client)
    assert response.status_code == 422
    assert response.json()["message"] == "github_rate_limit"


def test_tree_guards_origin_input_and_request_size(tmp_path):
    client, calls = fixture_client(tmp_path)
    assert request_tree(client, headers={"origin": "https://attacker.test"}).status_code == 403
    assert (
        client.post(
            "/repositories/tree",
            json={
                "repository_url": "https://github.com/owner/repo",
                "commit": "main",
            },
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/repositories/tree", content="x" * 8193, headers={"content-type": "application/json"}
        ).status_code
        == 413
    )
    assert calls == []
