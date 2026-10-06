"""Future out-of-process runner boundary. No implementation is provided."""

from typing import Protocol

from smartregression.contracts.models import CommitPair, ExecutionResult, TestSelection


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
