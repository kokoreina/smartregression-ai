"""Local immutable report files under an explicit authorized artifact root."""

import hashlib
import os
import tempfile
from pathlib import Path

from smartregression.application.run_store import ReportArtifact, RunConflict, RunStorageError
from smartregression.contracts.stages import RunIdentity, StageAnalysisReport

MAX_REPORT_BYTES = 16 * 1024 * 1024


class _ArtifactMismatch(RunStorageError):
    pass


def _no_links(path: Path) -> None:
    if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
        raise RunStorageError()


class ReportFiles:
    def __init__(self, root: Path, *, source_repository: Path) -> None:
        try:
            root = root.absolute()
            _no_links(root)
            self.root = root.resolve(strict=True)
            source = source_repository.resolve(strict=True)
            if (
                not self.root.is_dir()
                or self.root.is_relative_to(source)
                or source.is_relative_to(self.root)
            ):
                raise RunStorageError()
        except OSError:
            raise RunStorageError() from None

    def _path(self, artifact: ReportArtifact) -> Path:
        ReportArtifact(
            artifact.artifact_id, artifact.storage_key, artifact.sha256, artifact.size_bytes
        )
        if artifact.size_bytes > MAX_REPORT_BYTES:
            raise RunStorageError()
        path = self.root / artifact.storage_key
        _no_links(path)
        if not path.resolve().is_relative_to(self.root):
            raise RunStorageError()
        return path

    def _bytes(self, artifact: ReportArtifact) -> bytes:
        path = self._path(artifact)
        if not path.is_file():
            raise RunStorageError()
        if path.stat().st_size != artifact.size_bytes:
            raise _ArtifactMismatch()
        with path.open("rb") as stream:
            raw = stream.read(MAX_REPORT_BYTES + 1)
        if len(raw) != artifact.size_bytes or hashlib.sha256(raw).hexdigest() != artifact.sha256:
            raise _ArtifactMismatch()
        return raw

    def publish(self, artifact: ReportArtifact, raw: bytes) -> None:
        try:
            path = self._path(artifact)
            if (
                len(raw) != artifact.size_bytes
                or hashlib.sha256(raw).hexdigest() != artifact.sha256
            ):
                raise RunStorageError()
            if path.exists():
                if self._bytes(artifact) != raw:
                    raise RunConflict()
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            _no_links(path)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(
                    dir=path.parent, prefix=".publish-", delete=False
                ) as stream:
                    temporary = Path(stream.name)
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                try:
                    os.link(temporary, path)
                except FileExistsError:
                    if self._bytes(artifact) != raw:
                        raise RunConflict() from None
            finally:
                if temporary is not None:
                    temporary.unlink()
        except _ArtifactMismatch:
            raise RunConflict() from None
        except RunConflict:
            raise
        except OSError, ValueError:
            raise RunStorageError() from None

    def read(
        self, artifact: ReportArtifact, *, expected_identity: RunIdentity, expected_report_id: str
    ) -> StageAnalysisReport:
        try:
            report = StageAnalysisReport.model_validate_json(self._bytes(artifact))
            if report.identity != expected_identity or report.report_id != expected_report_id:
                raise RunStorageError()
            return report
        except OSError, ValueError:
            raise RunStorageError() from None

    def read_bytes(self, artifact: ReportArtifact) -> bytes:
        """Verified bounded bytes for authorized internal sidecar/index consumers.

        Content interpretation/identity checks remain with the specific consumer;
        this method never treats arbitrary JSON as a canonical report.
        """
        try:
            return self._bytes(artifact)
        except OSError, ValueError:
            raise RunStorageError() from None
