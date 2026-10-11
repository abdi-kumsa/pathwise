"""M1.C6 — Cohort progression and retention."""
SPEC_IDS = ("M1.C6.V1", "M1.C6.V2", "M1.C6.V3", "M1.C6.V4", "M1.C6.V5")
COLUMNS = (
    "retention_rate_pct",
    "dropout_rate_pct",
    "transfer_rate_pct",
    "completion_rate_pct",
    "time_to_graduation_years",
)
TABLE = "cohort_progression"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
