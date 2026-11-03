"""Persistence boundary for 2.05/2.20; no database implementation yet."""

from typing import Protocol

from smartregression.contracts.stages import EvidenceBundle, RunIdentity


class EvidenceStorageError(RuntimeError):
    """Adapter must translate infrastructure errors; never include a DSN or SQL."""

    code = "evidence_storage_failed"


class EvidenceConflict(EvidenceStorageError):
    """Same run key, different immutable bundle (code: evidence_conflict)."""

    code = "evidence_conflict"


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
