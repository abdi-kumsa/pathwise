"""M1.C5 — Demographic pipeline."""
SPEC_IDS = ("M1.C5.V1", "M1.C5.V2", "M1.C5.V3", "M1.C5.V4")
COLUMNS = (
    "grade12_completers_count",
    "university_age_population",
    "regional_youth_population",
    "net_internal_migration",
)
TABLE = "demographics"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
