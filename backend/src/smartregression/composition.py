"""Local CLI composition; no Git/filesystem adapters leak into application logic."""

from pathlib import Path
from typing import Literal

from smartregression.adapters.git_local import LocalGit
from smartregression.application.analysis import analyze
from smartregression.application.snapshots import RepositoryAuthorization
from smartregression.contracts.stages import StageAnalysisReport


def analyze_local(
    *,
    repository: Path,
    repository_id: str,
    authorized_root: Path,
    base: str,
    target: str,
    data_kind: Literal["demo", "real"],
) -> StageAnalysisReport:
    return analyze(
        LocalGit(repository),
        authorization=RepositoryAuthorization(repository_id, authorized_root),
        repository_id=repository_id,
        base=base,
        target=target,
        data_kind=data_kind,
    )
