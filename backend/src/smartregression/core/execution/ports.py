"""Future out-of-process runner boundary. No implementation is provided."""

from typing import Protocol

from smartregression.contracts.models import CommitPair, ExecutionResult, TestSelection
from smartregression.contracts.stages import StageResult
from smartregression.contracts.workflow import ExecutionPayload, SelectionManifest


class TestRunner(Protocol):
    def run(
        self, repository: str, commits: CommitPair, selection: TestSelection
    ) -> list[ExecutionResult]:
        """Run selected framework-native IDs at commits.target in an isolated worker.

        repository is an opaque repository identity, not an executable command.
        The caller must validate IDs against the target inventory before dispatch.
        Return at most one observation per selected ID; a failed test is not a fault label.
        No implementation exists. Timeout, cancellation, transport and infrastructure
        error reporting remain pending; settle these before implementing a worker.
        Never execute repository code inside API/CLI processes.
        """
        ...


class ManifestRunner(Protocol):
    """Sprint 3 consumer port; no runner or dispatch authorization is implemented."""

    def run(self, manifest: SelectionManifest) -> StageResult[ExecutionPayload]:
        """Execute only after trusted manifest/environment/isolation verification.

        A deserialized manifest does not prove acquisition, semantic validation,
        full-suite eligibility or authority. Implementation belongs to task 3.09.
        """
        ...
