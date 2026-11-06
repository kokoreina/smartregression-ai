"""Immutable index artifacts under the existing guarded filesystem publisher."""

from smartregression.adapters.storage.report_publication import ReportFiles
from smartregression.application.index_store import (
    MAX_INDEX_ARTIFACT_BYTES,
    IndexCorrupt,
    IndexPublication,
    IndexRecord,
    IndexStorageError,
)
from smartregression.application.run_store import ReportArtifact, RunStorageError


class IndexArtifactFiles(ReportFiles):
    """Reuse no-link/path/fsync/atomic-link rules; index has a separate bounded codec."""

    _max_bytes = MAX_INDEX_ARTIFACT_BYTES

    @staticmethod
    def descriptor(record: IndexRecord) -> ReportArtifact:
        record.validate()
        return ReportArtifact(
            record.manifest.index_id,
            record.storage_key,
            record.artifact_sha256,
            record.artifact_size,
        )

    def publish(self, publication: IndexPublication) -> None:
        try:
            super().publish(self.descriptor(publication.record), publication.raw)
        except OSError, RunStorageError:
            raise IndexStorageError() from None

    def read(self, record: IndexRecord) -> bytes:
        try:
            return self._bytes(self.descriptor(record))
        except OSError, RunStorageError:
            raise IndexCorrupt() from None
