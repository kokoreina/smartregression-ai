"""Admission, persistent reservations, finite retries; no provider network."""

import asyncio
import hashlib
import json
from pathlib import Path

import pytest

from smartregression.adapters.llm.budget import BudgetLedger
from smartregression.application.gemini_runtime import ProposalRuntime, RuntimePolicy
from smartregression.contracts.workflow import ProposalRequest, ProviderResult, ProviderUsage
from smartregression.gemini_config import GeminiCredential

ROOT = Path(__file__).resolve().parents[3]


def request_value(policy=None):
    policy = policy or RuntimePolicy()
    data = json.loads((ROOT / "examples/reports/proposal-request.demo.json").read_text())
    data["provenance"]["model"] = "gemini-3.5-flash-lite"
    data["provenance"]["configuration_id"] = policy.configuration_id
    return ProposalRequest.model_validate(data)


def permit(request):
    return hashlib.sha256(request.model_dump_json().encode()).hexdigest()


class Transport:
    retry_after_seconds = None

    def __init__(self, outcomes=None, count=100):
        self.calls = []
        self.outcomes = outcomes or ["completed"]
        self.tokens = count

    async def count(self, request, timeout):
        self.calls.append("count")
        return self.tokens

    async def attempt(self, request, timeout):
        self.calls.append("generation")
        status = self.outcomes.pop(0)
        common = dict(provenance=request.provenance, attempts=1)
        if status == "completed":
            return ProviderResult(
                status="completed",
                data={"suggestions": []},
                usage=ProviderUsage(input_tokens=100, output_tokens=10, thinking_tokens=0),
                **common,
            )
        return ProviderResult(status="failed", error_code=status, **common)


def run(tmp_path, transport, policy=None, request=None):
    policy = policy or RuntimePolicy()
    request = request or request_value(policy)
    ledger = BudgetLedger(tmp_path / "budget.json", session_id="session-1")
    runtime = ProposalRuntime(transport, ledger, policy, sleep=lambda seconds: None)
    return runtime.run(request, authorized_sha256=permit(request)), ledger


def test_success_counts_once_and_records_reservations(tmp_path):
    transport = Transport()
    result, ledger = run(tmp_path, transport)
    assert result.status == "completed" and result.attempts == 1
    assert transport.calls == ["count", "generation"]
    state = ledger.read()
    assert len(state["runs"]) == 1 and state["runs"][0]["entries"][1]["reserved_micro_usd"] == 7578


def test_transient_retry_is_bounded_and_unknown_usage_retained(tmp_path):
    transport = Transport(["provider_transport", "completed"])
    result, ledger = run(tmp_path, transport)
    assert result.status == "completed" and result.attempts == 2 and result.usage is None
    assert transport.calls == ["count", "generation", "generation"]
    assert ledger.read()["runs"][0]["entries"][1]["charged_micro_usd"] == 7578


@pytest.mark.parametrize(
    "error",
    [
        "provider_auth",
        "provider_permission",
        "provider_quota",
        "provider_configuration",
        "provider_refusal",
        "provider_invalid_output",
        "provider_truncated",
    ],
)
def test_terminal_errors_never_retry(tmp_path, error):
    transport = Transport([error])
    result, _ = run(tmp_path, transport)
    assert result.error_code == error and transport.calls == ["count", "generation"]


def test_count_over_limit_blocks_generation(tmp_path):
    transport = Transport(count=8193)
    result, _ = run(tmp_path, transport)
    assert result.error_code == "provider_budget" and result.attempts == 0
    assert transport.calls == ["count"]


def test_run_budget_insufficient_for_retry(tmp_path):
    policy = RuntimePolicy(run_budget_micro_usd=10000)
    transport = Transport(["provider_transport", "completed"])
    result, _ = run(tmp_path, transport, policy)
    assert result.error_code == "provider_budget" and result.attempts == 1
    assert transport.calls == ["count", "generation"]


def test_restart_and_run_limit_do_not_reset_budget(tmp_path):
    for i in range(5):
        request = request_value().model_dump(mode="json")
        request["provenance"]["identity"]["run_id"] = f"run-{i}"
        result, _ = run(tmp_path, Transport(), request=ProposalRequest.model_validate(request))
        assert result.status == "completed"
    transport = Transport()
    result, _ = run(tmp_path, transport)
    assert result.error_code == "provider_budget" and not transport.calls


def test_tampered_ledger_and_wrong_authorization_block_network(tmp_path):
    ledger = BudgetLedger(tmp_path / "budget.json", session_id="session-1")
    ledger.path.write_text("{broken")
    transport = Transport()
    runtime = ProposalRuntime(transport, ledger, RuntimePolicy())
    req = request_value()
    assert runtime.run(req, authorized_sha256=permit(req)).error_code == "provider_budget"
    assert runtime.run(req, authorized_sha256="0" * 64).error_code == "provider_permission"
    assert not transport.calls


def test_deadline_cancels_count_before_generation(tmp_path):
    class Slow(Transport):
        async def count(self, request, timeout):
            self.calls.append("count")
            await asyncio.sleep(10)

    transport = Slow()
    policy = RuntimePolicy(overall_seconds=0.01)
    result, _ = run(tmp_path, transport, policy)
    assert result.error_code == "provider_timeout" and result.attempts == 0


def test_concurrent_session_access_fails_closed(tmp_path):
    ledger = BudgetLedger(tmp_path / "budget.json", session_id="session-1")
    with ledger.open_run("first", "c" * 64, 20000):
        transport = Transport()
        result, _ = run(tmp_path, transport)
        assert result.error_code == "provider_budget" and not transport.calls


@pytest.mark.parametrize(
    "env",
    [
        {},
        {"GEMINI_API_KEY": " "},
        {"GOOGLE_API_KEY": "only-alias"},
        {"GEMINI_API_KEY": "one", "GOOGLE_API_KEY": "two"},
    ],
)
def test_credential_failure_does_not_echo_values(env):
    with pytest.raises(ValueError) as raised:
        GeminiCredential.from_environment(env)
    assert "one" not in str(raised.value) and "two" not in str(raised.value)


def test_credential_repr_redacts_and_canonical_same_alias_works():
    credential = GeminiCredential.from_environment(
        {"GEMINI_API_KEY": "secret-demo", "GOOGLE_API_KEY": "secret-demo"}
    )
    assert credential.api_key == "secret-demo" and "secret-demo" not in repr(credential)


def test_count_failure_and_unknown_generation_preserve_ledger(tmp_path):
    from smartregression.application.gemini_runtime import PreflightError

    class CountError(Transport):
        async def count(self, request, timeout):
            raise PreflightError("provider_quota")

    result, ledger = run(tmp_path, CountError())
    assert result.error_code == "provider_quota" and result.attempts == 0
    assert ledger.read()["runs"][0]["entries"][0]["state"] == "unknown"


def test_excessive_retry_after_does_not_dispatch_second_attempt(tmp_path):
    transport = Transport(["provider_rate_limit", "completed"])
    transport.retry_after_seconds = 100
    result, _ = run(tmp_path, transport)
    assert result.error_code == "provider_timeout" and result.attempts == 1
    assert transport.calls == ["count", "generation"]


def test_wrong_config_and_unknown_pricing_fail_before_network(tmp_path):
    request = request_value().model_copy(
        update={
            "provenance": request_value().provenance.model_copy(
                update={"configuration_id": "0" * 64}
            )
        }
    )
    transport = Transport()
    result, _ = run(tmp_path, transport, request=request)
    assert result.error_code == "provider_configuration" and not transport.calls
    with pytest.raises(ValueError, match="unverified_provider_price"):
        RuntimePolicy(input_usd_per_million="0")


def test_ledger_write_failure_prevents_dispatch(tmp_path, monkeypatch):
    ledger = BudgetLedger(tmp_path / "budget.json", session_id="session-1")

    def fail():
        raise OSError("private-path")

    monkeypatch.setattr(ledger, "_save", fail)
    request = request_value()
    transport = Transport()
    result = ProposalRuntime(transport, ledger, RuntimePolicy()).run(
        request, authorized_sha256=permit(request)
    )
    assert result.error_code == "provider_budget" and result.attempts == 0 and not transport.calls


def test_generation_timeout_keeps_unknown_reservation(tmp_path):
    class Slow(Transport):
        async def attempt(self, request, timeout):
            self.calls.append("generation")
            await asyncio.sleep(10)

    result, ledger = run(tmp_path, Slow(), RuntimePolicy(attempt_seconds=0.01))
    assert result.error_code == "provider_timeout"
    entry = ledger.read()["runs"][0]["entries"][1]
    assert entry["charged_micro_usd"] == 7578 and entry["actual_micro_usd"] is None


def test_session_budget_and_invalid_state_do_not_reset(tmp_path):
    ledger = BudgetLedger(tmp_path / "budget.json", session_id="session-1")
    with ledger.open_run("first", "c" * 64, 20000) as run_budget:
        run_budget.reserve("count", 0)
        run_budget.reserve("generation", 15000)
    with pytest.raises(ValueError):
        BudgetLedger(ledger.path, session_id="new-session").read()
    state = ledger.read()
    state["runs"][0]["entries"][1]["charged_micro_usd"] = -1
    ledger.path.write_text(json.dumps(state))
    with pytest.raises(ValueError):
        ledger.read()


def test_actual_sdk_count_and_generation_share_frozen_payload(tmp_path):
    import httpx2
    from google import genai

    from smartregression.adapters.llm.gemini import GeminiProvider, GeminiSettings

    calls = []

    async def handler(request):
        body = json.loads(request.content)
        calls.append((request.url.path, body))
        if request.url.path.endswith(":countTokens"):
            return httpx2.Response(200, json={"totalTokens": 120})
        return httpx2.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {"parts": [{"text": '{"suggestions": []}'}]},
                        "finishReason": "STOP",
                    }
                ]
            },
        )

    def factory(options):
        options.httpx_async_client = httpx2.AsyncClient(
            transport=httpx2.MockTransport(handler), trust_env=False
        )
        return genai.Client(api_key="synthetic-not-real", enterprise=False, http_options=options)

    result, _ = run(
        tmp_path, GeminiProvider(factory, GeminiSettings(api_version=RuntimePolicy().api_version))
    )
    assert result.status == "completed" and len(calls) == 2
    counted = calls[0][1]["generateContentRequest"]
    assert counted.pop("model") == "models/gemini-3.5-flash-lite"
    assert counted == calls[1][1]


def test_changed_provenance_cannot_cross_runtime_boundary(tmp_path):
    class Mutator(Transport):
        async def attempt(self, request, timeout):
            result = await super().attempt(request, timeout)
            return result.model_copy(
                update={
                    "provenance": result.provenance.model_copy(
                        update={"configuration_id": "0" * 64}
                    )
                }
            )

    result, ledger = run(tmp_path, Mutator())
    assert result.error_code == "provider_invalid_output" and result.attempts == 1
    assert ledger.read()["runs"][0]["entries"][1]["actual_micro_usd"] is None
