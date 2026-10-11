"""M1.C1 — Historical enrollment time series."""
SPEC_IDS = (
    "M1.C1.V1", "M1.C1.V2", "M1.C1.V3", "M1.C1.V4", "M1.C1.V5", "M1.C1.V6",
)
COLUMNS = (
    "enrollment_lag_1y",
    "enrollment_lag_2y",
    "enrollment_rolling_3y_avg",
    "enrollment_rolling_5y_avg",
    "enrollment_growth_rate_pct",
    "program_enrollment_count",
    "campus_enrollment_count",
    "region_enrollment_count",
)
TABLE = "enrollment_history"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
