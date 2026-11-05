"""Immutable evidence port and bounded codec; independent of database infrastructure."""

import hashlib
from typing import Protocol

from smartregression.contracts.stages import EvidenceBundle, RunIdentity
from smartregression.core.git.snapshots import canonical_json

EVIDENCE_FORMAT = "evidence-bundle/1"
MAX_EVIDENCE_BYTES = 2_097_152


class EvidenceStorageError(RuntimeError):
    """Adapter must translate infrastructure errors; never include a DSN or SQL."""

    code = "evidence_storage_failed"

    def __init__(self) -> None:
        super().__init__(self.code)


class EvidenceConflict(EvidenceStorageError):
    """Same run key, different immutable bundle (code: evidence_conflict)."""

    code = "evidence_conflict"


class EvidenceTooLarge(EvidenceStorageError):
    code = "evidence_payload_too_large"


class EvidenceFormatUnsupported(EvidenceStorageError):
    code = "evidence_format_unsupported"


class EvidenceCorrupt(EvidenceStorageError):
    code = "evidence_corrupt"


def prepare_evidence(bundle: EvidenceBundle) -> bytes:
    """Detach/revalidate mutable nested values, then capture the exact immutable bytes."""
    checked = EvidenceBundle.model_validate_json(bundle.model_dump_json())
    raw = canonical_json(checked.model_dump(mode="json"))
    if len(raw) > MAX_EVIDENCE_BYTES:
        raise EvidenceTooLarge()
    if "\0" in checked.identity.run_id or len(checked.identity.run_id.encode("utf-8")) > 512:
        raise EvidenceStorageError()
    return raw


def decode_evidence(raw: bytes, codec: str, digest: str, identity: RunIdentity) -> EvidenceBundle:
    """Stored bytes must be canonical and valid, not just JSON with a matching digest."""
    if codec != EVIDENCE_FORMAT:
        raise EvidenceFormatUnsupported()
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_EVIDENCE_BYTES:
        raise EvidenceCorrupt()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise EvidenceCorrupt()
    try:
        checked = EvidenceBundle.model_validate_json(raw.decode("utf-8", errors="strict"))
        if prepare_evidence(checked) != raw:
            raise EvidenceCorrupt()
    except ValueError, TypeError, UnicodeError, EvidenceStorageError:
        raise EvidenceCorrupt() from None
    if checked.identity != identity:
        raise EvidenceConflict()
    return checked


class EvidenceStore(Protocol):
    """Key: repository_id + run_id; the complete identity is immutable.

    Save is atomic for the entire bundle. An identical canonical JSON retry is a
    no-op; any different payload for an existing key raises EvidenceConflict.
    Arrays retain order. Loading an absent key returns None; unavailable storage
    raises EvidenceStorageError. Implementations enforce these rules in DB
    transactions, including concurrent writes. A Protocol does not enforce them.
    """

    def save(self, bundle: EvidenceBundle) -> None: ...

    def load(self, identity: RunIdentity) -> EvidenceBundle | None: ...


def save_evidence(store: EvidenceStore, bundle: EvidenceBundle) -> None:
    # Revalidate nested mutable lists before handing values to an adapter.
    checked = EvidenceBundle.model_validate_json(bundle.model_dump_json())
    store.save(checked)


def load_evidence(store: EvidenceStore, identity: RunIdentity) -> EvidenceBundle | None:
    bundle = store.load(identity)
    if bundle is None:
        return None
    checked = EvidenceBundle.model_validate_json(bundle.model_dump_json())
    if checked.identity != identity:
        raise ValueError("stored_evidence_identity_mismatch")
    return checked
