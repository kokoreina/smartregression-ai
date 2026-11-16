"""Immutable owner/project/SHA/config explorer cache with digest verification."""

import hashlib
import json

from smartregression.adapters.storage.connection import database_transaction
from smartregression.adapters.storage.project_store import BoundProjectStore
from smartregression.application.auth import AuthFailure
from smartregression.contracts.snapshots import ExplorerSnapshot


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


class PostgresExplorerStore:
    def __init__(self, engine):
        self.engine = engine

    def project(self, owner, project):
        with database_transaction(self.engine) as conn:
            return BoundProjectStore(conn).get(owner, project)

    def load(self, owner, project, commit, config):
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.get(owner, project)
            row = (
                tx.execute(
                    "SELECT * FROM smartregression.web_explorer_snapshots WHERE "
                    "owner_id=:owner AND project_id=:project AND commit=:commit "
                    "AND config_digest=:config",
                    owner=owner,
                    project=project,
                    commit=commit,
                    config=config,
                )
                .mappings()
                .first()
            )
            if row is None:
                return None
            if (
                digest(row["payload"]) != row["payload_digest"]
                or digest(row["sources"]) != row["sources_digest"]
            ):
                raise AuthFailure("snapshot_integrity_failed", 503)
            snapshot = ExplorerSnapshot.model_validate(row["payload"])
            if (
                snapshot.graph.commit != commit
                or snapshot.tree.commit != commit
                or snapshot.graph.config_digest != config
            ):
                raise AuthFailure("snapshot_identity_mismatch", 503)
            return snapshot, row["sources"]

    def save(self, owner, project, snapshot, sources):
        checked = ExplorerSnapshot.model_validate_json(snapshot.model_dump_json())
        payload = checked.model_dump(mode="json")
        with database_transaction(self.engine) as conn:
            tx = BoundProjectStore(conn)
            tx.lock_owner(owner)
            current = tx.get(owner, project, lock=True)
            if current.archived:
                raise AuthFailure("project_archived", 409)
            if checked.tree.repository_url != current.repository_url:
                raise AuthFailure("snapshot_identity_mismatch", 409)
            params = dict(
                owner=owner,
                project=project,
                commit=checked.graph.commit,
                config=checked.graph.config_digest,
                payload=encoded(payload),
                sources=encoded(sources),
                pd=digest(payload),
                sd=digest(sources),
            )
            inserted = tx.execute(
                "INSERT INTO smartregression.web_explorer_snapshots(owner_id,"
                "project_id,commit,config_digest,payload,sources,"
                "payload_digest,sources_digest) VALUES(:owner,:project,"
                ":commit,:config,CAST(:payload AS jsonb),CAST(:sources AS "
                "jsonb),:pd,:sd) ON CONFLICT(owner_id,project_id,commit,"
                "config_digest) DO NOTHING RETURNING commit",
                **params,
            ).first()
            if inserted:
                tx.activity(owner, project, "snapshot_created", checked.graph.commit)
            else:
                existing = tx.execute(
                    "SELECT payload_digest,sources_digest FROM "
                    "smartregression.web_explorer_snapshots WHERE "
                    "owner_id=:owner AND project_id=:project AND commit=:commit "
                    "AND config_digest=:config",
                    **{k: params[k] for k in ["owner", "project", "commit", "config"]},
                ).one()
                if tuple(existing) != (params["pd"], params["sd"]):
                    raise AuthFailure("snapshot_conflict", 409)
