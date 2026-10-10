"""M1.C2 — Admissions funnel data."""
SPEC_IDS = (
    "M1.C2.V1", "M1.C2.V2", "M1.C2.V3", "M1.C2.V4", "M1.C2.V5", "M1.C2.V6",
)
COLUMNS = (
    "applications_count",
    "offers_count",
    "accepted_offers_count",
    "yield_rate_pct",
    "applicants_per_seat",
    "first_choice_demand_count",
)
TABLE = "admissions_funnel"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
