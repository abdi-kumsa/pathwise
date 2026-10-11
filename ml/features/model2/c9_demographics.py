"""M2.C9 — Labor-force demographics, migration and regional variation."""
SPEC_IDS = ("M2.C9.V1", "M2.C9.V2", "M2.C9.V3", "M2.C9.V4", "M2.C9.V5")
COLUMNS = (
    "working_age_population", "education_level_distribution",
    "skilled_emigration_count", "return_migration_count",
    "regional_absorption_rate",
)
TABLE = "labour_demographics"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
