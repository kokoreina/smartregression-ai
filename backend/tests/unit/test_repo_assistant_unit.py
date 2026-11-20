"""Known graph edges, missing evidence, snapshot identity and signed event boundaries."""

import hashlib
import hmac
import json
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError

from smartregression.adapters.github_repository import GithubRepository
from smartregression.adapters.github_webhooks import receive_delivery
from smartregression.application.auth import AuthFailure
from smartregression.contracts.models import ChangedComponent
from smartregression.contracts.repo_assistant import WatchInput
from smartregression.core.explorer.graph import build_graph
from smartregression.core.explorer.repository_assistant import answer, change_report, overview

A, B = "a" * 40, "b" * 40


def test_optional_github_credential_is_sent_only_to_api_host(tmp_path):
    requests = []

    def transport(request):
        requests.append(request)
        return httpx.Response(200, content=b"{}")

    with httpx.Client(transport=httpx.MockTransport(transport)) as client:
        source = GithubRepository(
            "https://github.com/owner/repo", tmp_path, client, token="synthetic-read-token"
        )
        source._get("repos/owner/repo")
        source._get("owner/repo/zip/" + A, archive=True)
    assert requests[0].headers["authorization"] == "Bearer synthetic-read-token"
    assert "authorization" not in requests[1].headers


def graph(commit, sources):
    return build_graph("repo", commit, sources, lambda *args: None)


def test_deleted_imports_still_affect_consumer_from_base_snapshot():
    before = graph(A, {"consumer.py": "import dependency\n", "dependency.py": "x = 1\n"})
    after = graph(B, {"consumer.py": "x = 2\n"})
    report = change_report(
        before,
        after,
        [ChangedComponent(path="dependency.py", change="deleted")],
        "main",
        ["consumer.py"],
    )
    assert report.scope_impacts[0].path == "consumer.py"
    assert report.scope_impacts[0].relationship == "direct"
    assert report.scope_impacts[0].chain == ["dependency.py", "consumer.py"]
    assert report.scope_impacts[0].evidence[0].commit == A


def test_scope_prefix_does_not_include_same_named_sibling_and_unknown_is_retained():
    sources = {"src/a.py": "x=1\n", "src_other/b.py": "x=2\n", "config.toml": "foo=1"}
    before, after = graph(A, sources), graph(B, sources)
    report = change_report(
        before, after, [ChangedComponent(path="src_other/b.py", change="modified")], "main", ["src"]
    )
    assert report.scope_impacts == []
    assert report.target_coverage.status == "partial"
    assert "không chứng minh" in " ".join(report.limitations)


def test_unsupported_changed_file_is_still_directly_relevant():
    sources = {"app.py": "x=1\n", "app.ts": "const x = 1;"}
    report = change_report(
        graph(A, sources),
        graph(B, sources),
        [ChangedComponent(path="app.ts", change="modified")],
        "main",
        ["app.ts"],
    )
    assert report.scope_impacts[0].relationship == "changed"
    assert report.scope_impacts[0].evidence == []


def test_two_snapshot_identity_must_match():
    a, b = graph(A, {"a.py": "x=1"}), graph(B, {"a.py": "x=2"})
    b.repository_id = "another-repo"
    with pytest.raises(ValueError, match="change_snapshot_mismatch"):
        change_report(a, b, [], "main", [])


def test_static_overview_and_followup_use_pinned_source_ranges():
    sources = {"README.md": "# Example library\n", "billing.py": "def invoice():\n    return 1\n"}
    value = graph(A, sources)
    result = overview(value, sources)
    assert result.kind == "overview"
    assert result.excerpts[0].path == "README.md"
    found = answer(value, sources, "nó làm gì", ["invoice"])
    assert found.kind == "search"
    assert any(p.path == "billing.py" and p.commit == A for f in found.facts for p in f.evidence)
    assert answer(value, sources, "xyznonexistent").kind == "no_evidence"


@pytest.mark.parametrize("branch", ["../main", "main?x=1", "main.lock", "a//b", "a..b", "a\\b"])
def test_branch_rejects_ambiguous_or_unsafe_refs(branch):
    with pytest.raises(ValidationError):
        WatchInput(branch=branch)


class Inbox:
    def __init__(self):
        self.items = {}

    def delivery(self, identity, signature, repository, event, branch, actor):
        old = self.items.get(identity)
        if old:
            if old != signature:
                raise AuthFailure("webhook_delivery_conflict", 409)
            return True, 0
        self.items[identity] = signature
        assert repository == "owner/repo" and branch == "main"
        return False, 1


def delivery(value, event="push", identity=None):
    secret = "s" * 40
    raw = json.dumps(value).encode()
    headers = {
        "x-hub-signature-256": "sha256="
        + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest(),
        "x-github-delivery": identity or str(uuid4()),
        "x-github-event": event,
    }
    return raw, headers, secret


def test_webhook_signature_replay_and_tag_filtering():
    value = {
        "repository": {"full_name": "owner/repo"},
        "ref": "refs/heads/main",
        "before": A,
        "after": B,
    }
    raw, headers, secret = delivery(value)
    store = Inbox()
    assert receive_delivery(store, raw, headers, secret).scheduled == 1
    assert receive_delivery(store, raw, headers, secret).duplicate
    with pytest.raises(AuthFailure, match="invalid_webhook_signature"):
        receive_delivery(store, raw + b" ", headers, secret)
    value["ref"] = "refs/tags/v1"
    assert not receive_delivery(store, *delivery(value)).accepted
    assert len(store.items) == 1


def test_closed_unmerged_pr_is_not_a_merge_and_fork_base_is_verified():
    value = {
        "repository": {"full_name": "owner/repo"},
        "action": "closed",
        "pull_request": {
            "merged": False,
            "base": {"ref": "main", "repo": {"full_name": "owner/repo"}},
        },
    }
    assert not receive_delivery(Inbox(), *delivery(value, "pull_request")).accepted
    value["pull_request"]["merged"] = True
    assert receive_delivery(Inbox(), *delivery(value, "pull_request")).scheduled == 1
    value["pull_request"]["base"]["repo"]["full_name"] = "other/repo"
    with pytest.raises(AuthFailure, match="invalid_webhook_payload"):
        receive_delivery(Inbox(), *delivery(value, "pull_request"))
