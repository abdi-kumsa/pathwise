"""M2.C1 — Historical employment and unemployment trends."""
SPEC_IDS = (
    "M2.C1.V1", "M2.C1.V2", "M2.C1.V3", "M2.C1.V4",
    "M2.C1.V5", "M2.C1.V6", "M2.C1.V7", "M2.C1.V8",
)
COLUMNS = (
    "employment_level", "unemployment_rate_pct", "youth_unemployment_rate_pct",
    "sector_employment", "employment_growth_pct", "job_creation_count",
    "labour_force_participation_pct", "employment_lag_1y", "employment_lag_2y",
)
TABLE = "labour_history"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
