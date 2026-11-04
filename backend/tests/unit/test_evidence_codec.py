import hashlib

import pytest

from smartregression.application.evidence_store import (
    EVIDENCE_FORMAT,
    MAX_EVIDENCE_BYTES,
    EvidenceConflict,
    EvidenceCorrupt,
    EvidenceFormatUnsupported,
    EvidenceTooLarge,
    decode_evidence,
    prepare_evidence,
)
from smartregression.contracts.stages import EvidenceBundle


def bundle_from(data):
    return EvidenceBundle(
        identity=data["identity"],
        **{
            name: data["stages"][name]["data"]
            for name in ("changes", "graph", "impact", "evidence")
        },
    )


def test_codec_preserves_order_unicode_defaults_and_detaches(stage_artifacts):
    bundle = bundle_from(stage_artifacts)
    item = bundle.evidence.items[0]
    bundle.evidence.items[0] = item.model_copy(update={"excerpt": "x\u0000é e\u0301"})
    raw = prepare_evidence(bundle)
    loaded = decode_evidence(raw, EVIDENCE_FORMAT, hashlib.sha256(raw).hexdigest(), bundle.identity)
    assert loaded.evidence.items[0].excerpt == "x\u0000é e\u0301"
    assert b"\\u0000" in raw and b"\\u00e9" in raw
    assert loaded.impact.paths == bundle.impact.paths


def test_roundtrip_and_exact_canonical_representation(stage_artifacts):
    bundle = bundle_from(stage_artifacts)
    raw = prepare_evidence(bundle)
    assert raw.endswith(b"\n")
    digest = hashlib.sha256(raw).hexdigest()
    loaded = decode_evidence(raw, EVIDENCE_FORMAT, digest, bundle.identity)
    assert loaded == bundle and loaded is not bundle
    assert prepare_evidence(loaded) == raw
    bundle.evidence.items.clear()
    assert loaded.evidence.items


@pytest.mark.parametrize("change", ["digest", "json", "noncanonical", "format", "identity"])
def test_bad_storage_data_is_not_returned(stage_artifacts, change):
    bundle = bundle_from(stage_artifacts)
    raw = prepare_evidence(bundle)
    identity, codec = bundle.identity, EVIDENCE_FORMAT
    error = EvidenceCorrupt
    if change == "json":
        raw = b"{broken"
    elif change == "noncanonical":
        raw = bundle.model_dump_json(indent=2).encode()
    elif change == "format":
        codec, error = "future/99", EvidenceFormatUnsupported
    elif change == "identity":
        identity, error = identity.model_copy(update={"run_id": "foreign"}), EvidenceConflict
    digest = "0" * 64 if change == "digest" else hashlib.sha256(raw).hexdigest()
    with pytest.raises(error):
        decode_evidence(raw, codec, digest, identity)


def test_exact_size_boundary_is_measured_after_canonical_encoding(stage_artifacts):
    bundle = bundle_from(stage_artifacts)
    item = bundle.evidence.items[0]
    bundle.evidence.items[0] = item.model_copy(update={"excerpt": "x"})
    needed = MAX_EVIDENCE_BYTES - len(prepare_evidence(bundle))
    bundle.evidence.items[0] = item.model_copy(update={"excerpt": "x" * (needed + 1)})
    assert len(prepare_evidence(bundle)) == MAX_EVIDENCE_BYTES
    bundle.evidence.items[0] = item.model_copy(update={"excerpt": "x" * (needed + 2)})
    with pytest.raises(EvidenceTooLarge, match="evidence_payload_too_large"):
        prepare_evidence(bundle)
