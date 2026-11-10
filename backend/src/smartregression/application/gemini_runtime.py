"""One owner for egress admission, preflight, retries and persistent reservations."""

import asyncio
import hashlib
import json
import math
import time
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import asdict, dataclass
from decimal import ROUND_CEILING, Decimal
from typing import Protocol

from smartregression.application.proposals import ProposalBoundaryError, request_proposal
from smartregression.contracts.workflow import ProposalRequest, ProviderResult, ProviderUsage


@dataclass(frozen=True)
class RuntimePolicy:
    api_version: str = "v1beta"
    overall_seconds: float = 45.0
    count_seconds: float = 5.0
    attempt_seconds: float = 15.0
    input_tokens: int = 8192
    output_tokens: int = 2048
    attempts: int = 2
    run_budget_micro_usd: int = 20000
    input_usd_per_million: str = "0.30"
    output_usd_per_million: str = "2.50"
    price_version: str = "gemini-3.5-flash-lite/standard-text/2026-11-10"

    def __post_init__(self) -> None:
        if self.api_version not in {"v1", "v1beta"}:
            raise ValueError("invalid_provider_policy")
        caps = [(self.overall_seconds, 45), (self.count_seconds, 5), (self.attempt_seconds, 15)]
        if any(isinstance(v, bool) or not math.isfinite(v) or not 0 < v <= cap for v, cap in caps):
            raise ValueError("invalid_provider_policy")
        for value, cap in [
            (self.input_tokens, 8192),
            (self.output_tokens, 2048),
            (self.attempts, 2),
            (self.run_budget_micro_usd, 20000),
        ]:
            if type(value) is not int or not 0 < value <= cap:
                raise ValueError("invalid_provider_policy")
        if (self.input_usd_per_million, self.output_usd_per_million, self.price_version) != (
            "0.30",
            "2.50",
            "gemini-3.5-flash-lite/standard-text/2026-11-10",
        ):
            raise ValueError("unverified_provider_price")

    @property
    def configuration_id(self) -> str:
        value = asdict(self) | {
            "model": "gemini-3.5-flash-lite",
            "api": self.api_version,
            "prompt": "proposal/1",
            "wire_bytes": 65536,
            "thinking": "MINIMAL",
            "schema": "suggestions/2-common-subset",
            "count": "full-request/1",
        }
        return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

    def price(self, inputs: int, outputs: int) -> int:
        # USD/million tokens is numerically micro-USD/token.
        return int(
            (
                Decimal(inputs) * Decimal(self.input_usd_per_million)
                + Decimal(outputs) * Decimal(self.output_usd_per_million)
            ).to_integral_value(rounding=ROUND_CEILING)
        )


class CountedTransport(Protocol):
    retry_after_seconds: float | None

    async def count(self, request: ProposalRequest, timeout: float) -> int: ...
    async def attempt(self, request: ProposalRequest, timeout: float) -> ProviderResult: ...


class RunBudget(Protocol):
    def reserve(self, kind: str, amount: int) -> int: ...
    def settle(self, entry: int, amount: int | None) -> None: ...


class SessionBudget(Protocol):
    def open_run(self, run_id: str, config: str, cap: int) -> AbstractContextManager[RunBudget]: ...


class PreflightError(ValueError):
    """A stable local code; never carries provider response text."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class _ObservedResult:
    def __init__(self, value: ProviderResult) -> None:
        self.value = value

    def propose(self, request: ProposalRequest) -> ProviderResult:
        return self.value


class ProposalRuntime:
    def __init__(
        self,
        transport: CountedTransport,
        ledger: SessionBudget,
        policy: RuntimePolicy,
        *,
        sleep: Callable[[float], object] | None = None,
    ) -> None:
        self.transport = transport
        self.ledger = ledger
        self.policy = policy
        self.sleep = sleep
        self.counted_input_tokens: int | None = None

    def run(self, request: ProposalRequest, *, authorized_sha256: str) -> ProviderResult:
        self.counted_input_tokens = None
        frozen = request.model_dump_json()
        checked = ProposalRequest.model_validate_json(frozen)
        common = dict(provenance=checked.provenance)
        if hashlib.sha256(frozen.encode()).hexdigest() != authorized_sha256:
            return ProviderResult(
                status="failed", error_code="provider_permission", attempts=0, **common
            )
        if checked.provenance.configuration_id != self.policy.configuration_id:
            return ProviderResult(
                status="failed", error_code="provider_configuration", attempts=0, **common
            )
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            return ProviderResult(
                status="failed", error_code="provider_configuration", attempts=0, **common
            )
        try:
            with self.ledger.open_run(
                checked.provenance.identity.run_id,
                self.policy.configuration_id,
                self.policy.run_budget_micro_usd,
            ) as budget:
                return asyncio.run(self._run(frozen, budget))
        except ValueError, OSError:
            return ProviderResult(
                status="failed", error_code="provider_budget", attempts=0, **common
            )

    async def _run(self, frozen: str, budget: RunBudget) -> ProviderResult:
        checked = ProposalRequest.model_validate_json(frozen)
        common = dict(provenance=checked.provenance)
        attempted = 0
        observed = []
        started = time.monotonic()
        deadline = started + self.policy.overall_seconds
        last = None
        try:
            async with asyncio.timeout(self.policy.overall_seconds):
                # Official token-counting operation is unbilled; still journal before dispatch.
                entry = budget.reserve("count", 0)
                async with asyncio.timeout(
                    min(self.policy.count_seconds, deadline - time.monotonic())
                ):
                    count = await self.transport.count(
                        checked, min(self.policy.count_seconds, deadline - time.monotonic())
                    )
                budget.settle(entry, 0)
                self.counted_input_tokens = count
                if type(count) is not int or not 0 <= count <= self.policy.input_tokens:
                    raise PreflightError("provider_budget")
                for number in range(self.policy.attempts):
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError
                    # Reserve full admitted input cap, not an optimistic count-based cost.
                    entry = budget.reserve(
                        "generation",
                        self.policy.price(self.policy.input_tokens, self.policy.output_tokens),
                    )
                    attempted += 1
                    request = ProposalRequest.model_validate_json(frozen)
                    async with asyncio.timeout(min(self.policy.attempt_seconds, remaining)):
                        result = await self.transport.attempt(
                            request, min(self.policy.attempt_seconds, remaining)
                        )
                    result = request_proposal(
                        _ObservedResult(result), ProposalRequest.model_validate_json(frozen)
                    )
                    if result.attempts not in (0, 1):
                        raise PreflightError("provider_invalid_output")
                    if result.attempts == 0:
                        attempted -= 1
                        budget.settle(entry, 0)
                    usage = result.usage
                    cost = None
                    if usage and all(
                        v is not None
                        for v in (usage.input_tokens, usage.output_tokens, usage.thinking_tokens)
                    ):
                        if (
                            usage.input_tokens > self.policy.input_tokens
                            or usage.output_tokens + usage.thinking_tokens
                            > self.policy.output_tokens
                        ):
                            raise PreflightError("provider_budget")
                        cost = self.policy.price(
                            usage.input_tokens, usage.output_tokens + usage.thinking_tokens
                        )
                    budget.settle(entry, cost if result.attempts else 0)
                    observed.append((usage, cost))
                    last = result
                    if result.status == "completed" or result.error_code not in {
                        "provider_transport",
                        "provider_timeout",
                        "provider_rate_limit",
                    }:
                        break
                    if number + 1 == self.policy.attempts:
                        break
                    delay = max(1.0, self.transport.retry_after_seconds or 0)
                    if not math.isfinite(delay) or delay >= deadline - time.monotonic():
                        raise TimeoutError
                    if self.sleep is None:
                        await asyncio.sleep(delay)
                    else:
                        self.sleep(delay)
                if last is None:
                    raise PreflightError("provider_configuration")
                usage = self._aggregate(observed, time.monotonic() - started)
                return last.model_copy(update={"attempts": attempted, "usage": usage})
        except TimeoutError:
            code = "provider_timeout"
        except PreflightError as exc:
            code = exc.code
        except ProposalBoundaryError:
            code = "provider_invalid_output"
        except OSError, ValueError:
            code = "provider_budget"
        return ProviderResult(status="failed", error_code=code, attempts=attempted, **common)

    @staticmethod
    def _aggregate(
        values: list[tuple[ProviderUsage | None, int | None]], duration: float
    ) -> ProviderUsage | None:
        if not values or any(u is None for u, _ in values):
            return None
        totals = {}
        for field in ("input_tokens", "output_tokens", "thinking_tokens", "total_tokens"):
            items = [getattr(u, field) for u, _ in values]
            totals[field] = sum(items) if all(v is not None for v in items) else None
        costs = [cost for _, cost in values]
        return ProviderUsage(
            **totals,
            duration_seconds=duration,
            cost_usd=sum(costs) / 1_000_000 if all(c is not None for c in costs) else None,
        )
