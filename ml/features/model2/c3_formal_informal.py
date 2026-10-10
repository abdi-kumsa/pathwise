"""M2.C3 — Formal versus informal sector structure."""
SPEC_IDS = ("M2.C3.V1", "M2.C3.V2", "M2.C3.V3", "M2.C3.V4", "M2.C3.V5", "M2.C3.V6")
COLUMNS = (
    "formal_wage_employment", "informal_employment", "self_employment",
    "underemployment", "microenterprise_activity", "sector_absorption_rate",
)
TABLE = "formal_informal"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
