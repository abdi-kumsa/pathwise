"""Wave 2.1 — every Model 1 spec id is produced by a feature module."""
from __future__ import annotations

from ml.features.model1 import FEATURE_MODULES
from backend import spec_registry as S


def test_one_module_per_model1_category():
    ids = {m.__name__.split(".")[-1] for m in FEATURE_MODULES}
    assert len(FEATURE_MODULES) == 10
    assert len(ids) == 10


def test_feature_modules_claim_every_model1_variable():
    claimed = {spec_id for mod in FEATURE_MODULES for spec_id in mod.SPEC_IDS}
    expected = {v["id"] for v in S.variables("model1")}
    assert claimed == expected, (
        f"unclaimed {sorted(expected - claimed)}; extra {sorted(claimed - expected)}"
    )
