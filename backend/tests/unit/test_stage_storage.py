"""Protocol/application boundary checks; these are NOT PostgreSQL acceptance."""

from copy import deepcopy

import pytest
from pydantic import ValidationError

from smartregression.application.evidence_store import (
    EvidenceConflict,
    EvidenceStorageError,
    load_evidence,
    save_evidence,
)
from smartregression.contracts.stages import EvidenceBundle, RunIdentity
from smartregression.core.git.snapshots import canonical_json


def bundle_from_report(data: dict) -> EvidenceBundle:
    return EvidenceBundle(
        identity=data["identity"],
        **{
            name: data["stages"][name]["data"]
            for name in ("changes", "graph", "impact", "evidence")
        },
    )


class MemoryStore:
    """Reference fake for key/idempotency semantics; no transactions or concurrency."""

    def __init__(self):
        self.items = {}

    def save(self, bundle: EvidenceBundle) -> None:
        key = (bundle.identity.repository_id, bundle.identity.run_id)
        content = canonical_json(bundle.model_dump(mode="json"))
        if key in self.items and self.items[key] != content:
            raise EvidenceConflict()
        self.items[key] = content

    def load(self, identity: RunIdentity) -> EvidenceBundle | None:
        raw = self.items.get((identity.repository_id, identity.run_id))
        return None if raw is None else EvidenceBundle.model_validate_json(raw)


def test_round_trip_and_identical_retry_have_one_immutable_key(stage_artifacts: dict) -> None:
    store = MemoryStore()
    bundle = bundle_from_report(stage_artifacts)
    assert load_evidence(store, bundle.identity) is None
    save_evidence(store, bundle)
    save_evidence(store, bundle)
    assert len(store.items) == 1
    assert load_evidence(store, bundle.identity) == bundle
    different = deepcopy(stage_artifacts)
    different["stages"]["evidence"]["data"]["items"][0]["excerpt"] = "changed payload"
    with pytest.raises(EvidenceConflict):
        save_evidence(store, bundle_from_report(different))
    assert load_evidence(store, bundle.identity) == bundle


def test_corrupt_or_wrong_run_storage_response_is_rejected(stage_artifacts: dict) -> None:
    bundle = bundle_from_report(stage_artifacts)

    class WrongStore(MemoryStore):
        def load(self, identity):
            return bundle

    wrong_identity = bundle.identity.model_copy(update={"run_id": "other-run"})
    with pytest.raises(ValueError, match="stored_evidence_identity_mismatch"):
        load_evidence(WrongStore(), wrong_identity)
    bundle.impact.candidates[0].evidence_ids.append("unknown")
    with pytest.raises(ValidationError):
        load_evidence(WrongStore(), bundle.identity)
    with pytest.raises(ValidationError):
        save_evidence(MemoryStore(), bundle)


def test_storage_failure_is_not_not_found_or_success(stage_artifacts: dict) -> None:
    class Unavailable(MemoryStore):
        def load(self, identity):
            raise EvidenceStorageError()

        def save(self, bundle):
            raise EvidenceStorageError()

    bundle = bundle_from_report(stage_artifacts)
    with pytest.raises(EvidenceStorageError):
        load_evidence(Unavailable(), bundle.identity)
    with pytest.raises(EvidenceStorageError):
        save_evidence(Unavailable(), bundle)
