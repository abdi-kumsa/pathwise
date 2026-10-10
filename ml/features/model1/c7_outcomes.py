"""M1.C7 — Lagged employment outcomes by field."""
SPEC_IDS = ("M1.C7.V1", "M1.C7.V2", "M1.C7.V3", "M1.C7.V4", "M1.C7.V5")
COLUMNS = (
    "graduate_employment_rate_pct",
    "graduate_unemployment_rate_pct",
    "median_earnings_etb",
    "vacancy_demand_by_field",
    "skills_shortage_signal",
)
TABLE = "graduate_outcomes"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
