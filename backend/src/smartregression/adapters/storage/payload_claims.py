"""Insert-only run payload ledger shared by report and evidence transactions."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from smartregression.adapters.storage.schema import (
    evidence_bundles,
    run_reports,
    run_stage_payloads,
)
from smartregression.application.evidence_store import decode_evidence
from smartregression.application.payloads import BUNDLE_STAGES, payload_digest
from smartregression.application.run_store import RunPayloadConflict, RunStorageError
from smartregression.contracts.stages import RunIdentity


def claim_payloads(
    connection: sa.Connection,
    identity: RunIdentity,
    digests: dict[str, str],
    *,
    verified_report_id: str | None = None,
) -> None:
    scope = {"repository_id": identity.repository_id, "run_id": identity.run_id}
    predicates = [run_stage_payloads.c[k] == v for k, v in scope.items()]
    # Never backfill a legacy report from a different writer's unverified data.
    # Exact report replay may seed its own claims only after immutable catalog
    # comparison succeeds. Other legacy reports require explicit reconciliation.
    reports = connection.execute(
        sa.select(run_reports.c.report_id, run_reports.c.stage_summary).where(
            *[run_reports.c[k] == v for k, v in scope.items()]
        )
    ).all()
    # Read claims after materializing report rows. Under READ COMMITTED, claims
    # committed atomically with any visible report must now be visible too.
    # The reverse order can misclassify a concurrently committed report as legacy.
    known = dict(
        connection.execute(
            sa.select(run_stage_payloads.c.stage_name, run_stage_payloads.c.payload_sha256).where(
                *predicates
            )
        ).all()
    )
    for report_id, summary in reports:
        if report_id != verified_report_id and any(
            summary[name]["status"] in {"completed", "partial"} and name not in known
            for name in BUNDLE_STAGES
        ):
            raise RunStorageError()
    stored_bundle = (
        connection.execute(
            sa.select(evidence_bundles).where(
                *[evidence_bundles.c[k] == v for k, v in scope.items()]
            )
        )
        .mappings()
        .one_or_none()
    )
    if stored_bundle is not None:
        bundle = decode_evidence(
            stored_bundle["payload"],
            stored_bundle["bundle_format"],
            stored_bundle["payload_sha256"],
            identity,
        )
        for name, digest in (known | digests).items():
            if payload_digest(getattr(bundle, name)) != digest:
                raise RunPayloadConflict()
    # Stable lock order avoids crossed claims. Unique keys arbitrate concurrent
    # INSERTs; the loser compares the committed digest under READ COMMITTED.
    for name, digest in sorted(digests.items()):
        inserted = connection.execute(
            insert(run_stage_payloads)
            .values(**scope, stage_name=name, payload_sha256=digest)
            .on_conflict_do_nothing()
            .returning(run_stage_payloads.c.stage_name)
        ).scalar_one_or_none()
        if inserted is None:
            stored = connection.scalar(
                sa.select(run_stage_payloads.c.payload_sha256).where(
                    *predicates, run_stage_payloads.c.stage_name == name
                )
            )
            if stored != digest:
                raise RunPayloadConflict()
