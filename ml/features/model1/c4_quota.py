"""M1.C4 — Program capacity and quota policy."""
SPEC_IDS = (
    "M1.C4.V1", "M1.C4.V2", "M1.C4.V3", "M1.C4.V4", "M1.C4.V5", "M1.C4.V6",
)
COLUMNS = (
    "approved_intake_quota",
    "available_seats",
    "program_capacity",
    "program_expansion_flag",
    "program_suspension_flag",
    "strategic_priority_flag",
)
TABLE = "capacity_quota"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
