"""Canonical fingerprints for overlap checks; hashes never prove source validity."""

import hashlib

from smartregression.contracts.stages import StageValue
from smartregression.core.git.snapshots import canonical_json

BUNDLE_STAGES = ("changes", "graph", "impact", "evidence")


def payload_digest(value: StageValue) -> str:
    return hashlib.sha256(canonical_json(value.model_dump(mode="json"))).hexdigest()
