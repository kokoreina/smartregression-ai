"""PostgreSQL immutable, run-bound evidence; no source verification or provisioning."""

import hashlib

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.payload_claims import claim_payloads
from smartregression.adapters.storage.schema import analysis_runs, evidence_bundles
from smartregression.application.evidence_store import (
    EVIDENCE_FORMAT,
    EvidenceConflict,
    EvidenceStorageError,
    decode_evidence,
    prepare_evidence,
)
from smartregression.application.payloads import BUNDLE_STAGES, payload_digest
from smartregression.application.run_store import RunPayloadConflict, RunStorageError
from smartregression.contracts.stages import EvidenceBundle, RunIdentity


class BoundEvidenceStore:
    """Caller owns an active transaction; this adapter never commits or retries."""

    def __init__(self, connection: sa.Connection) -> None:
        self.connection = connection

    def _run(self, identity: RunIdentity) -> None:
        if self.connection.closed or not self.connection.in_transaction():
            raise EvidenceStorageError()
        row = (
            self.connection.execute(
                sa.select(analysis_runs).where(
                    analysis_runs.c.repository_id == identity.repository_id,
                    analysis_runs.c.run_id == identity.run_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise EvidenceStorageError()
        expected = {
            "base_sha": identity.base.commit,
            "target_sha": identity.target.commit,
            "base_snapshot_id": identity.base.snapshot_id,
            "target_snapshot_id": identity.target.snapshot_id,
            "comparison_mode": identity.comparison_mode,
        }
        if any(row[key] != value for key, value in expected.items()):
            raise EvidenceConflict()

    def save(self, bundle: EvidenceBundle) -> None:
        raw = prepare_evidence(bundle)
        digest = hashlib.sha256(raw).hexdigest()
        checked = decode_evidence(raw, EVIDENCE_FORMAT, digest, bundle.identity)
        try:
            self._run(checked.identity)
            claim_payloads(
                self.connection,
                checked.identity,
                {name: payload_digest(getattr(checked, name)) for name in BUNDLE_STAGES},
            )
            inserted = self.connection.execute(
                insert(evidence_bundles)
                .values(
                    repository_id=checked.identity.repository_id,
                    run_id=checked.identity.run_id,
                    bundle_format=EVIDENCE_FORMAT,
                    payload=raw,
                    payload_sha256=digest,
                )
                .on_conflict_do_nothing()
                .returning(evidence_bundles.c.run_id)
            ).scalar_one_or_none()
            if inserted is None:
                stored = self.load(checked.identity)
                if stored is None or prepare_evidence(stored) != raw:
                    raise EvidenceConflict()
        except RunPayloadConflict:
            raise EvidenceConflict() from None
        except sa.exc.SQLAlchemyError, RunStorageError:
            raise EvidenceStorageError() from None

    def load(self, identity: RunIdentity) -> EvidenceBundle | None:
        identity = RunIdentity.model_validate_json(identity.model_dump_json())
        if self.connection.closed or not self.connection.in_transaction():
            raise EvidenceStorageError()
        try:
            row = (
                self.connection.execute(
                    sa.select(evidence_bundles).where(
                        evidence_bundles.c.repository_id == identity.repository_id,
                        evidence_bundles.c.run_id == identity.run_id,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            self._run(identity)
            return decode_evidence(
                row["payload"], row["bundle_format"], row["payload_sha256"], identity
            )
        except sa.exc.SQLAlchemyError:
            raise EvidenceStorageError() from None


class PostgresEvidenceStore:
    def __init__(self, engine: sa.Engine) -> None:
        self.engine = engine

    def save(self, bundle: EvidenceBundle) -> None:
        raw = prepare_evidence(bundle)  # Reject invalid/oversized data before connecting.
        checked = decode_evidence(
            raw, EVIDENCE_FORMAT, hashlib.sha256(raw).hexdigest(), bundle.identity
        )
        try:
            with database_transaction(self.engine) as connection:
                BoundEvidenceStore(connection).save(checked)
        except RunStorageError:
            raise EvidenceStorageError() from None

    def load(self, identity: RunIdentity) -> EvidenceBundle | None:
        try:
            with database_transaction(self.engine) as connection:
                return BoundEvidenceStore(connection).load(identity)
        except RunStorageError:
            raise EvidenceStorageError() from None
