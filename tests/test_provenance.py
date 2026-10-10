"""Wave 0 provenance stamp — the shape that every later wave must keep."""
from __future__ import annotations

import json

import pytest

from backend.services._provenance import (
    DATASET_LABEL,
    Provenance,
    attach_default_if_missing,
    default_provenance,
    stamp,
)


def test_default_tier_is_simulated_until_ethiopia_rebase():
    p = default_provenance()
    assert p.tier == "simulated"
    assert "not official" in p.caveat.lower()
    assert p.source
    assert p.as_of
    assert p.method


def test_stamp_adds_provenance_and_dataset_label():
    out = stamp({"total": 3})
    assert out["total"] == 3
    assert out["provenance"]["tier"] == "simulated"
    assert out["dataset_label"] == DATASET_LABEL


def test_stamp_does_not_overwrite_a_more_specific_block():
    existing = {"source": "MoE EMIS", "tier": "official", "as_of": "2016–2025", "method": "upload"}
    out = stamp({"rows": 1, "provenance": existing})
    assert out["provenance"] == existing


def test_stamp_rejects_non_dicts():
    with pytest.raises(TypeError):
        stamp([1, 2, 3])


def test_unknown_tier_is_rejected():
    with pytest.raises(ValueError):
        Provenance(source="x", tier="guesswork", as_of="2025", method="n/a")


def test_middleware_helper_stamps_objects_only():
    stamped = json.loads(attach_default_if_missing(b'{"ok": true}'))
    assert stamped["ok"] is True
    assert stamped["provenance"]["tier"] == "simulated"

    listed = attach_default_if_missing(b"[1, 2]")
    assert listed == b"[1, 2]"

    already = b'{"provenance": {"tier": "official", "source": "ESS", "as_of": "2024", "method": "LFS"}}'
    assert json.loads(attach_default_if_missing(already))["provenance"]["tier"] == "official"
