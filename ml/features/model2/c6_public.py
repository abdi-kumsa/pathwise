"""M2.C6 — Public-sector hiring and government project pipeline."""
SPEC_IDS = ("M2.C6.V1", "M2.C6.V2", "M2.C6.V3", "M2.C6.V4")
COLUMNS = (
    "civil_service_hiring_plan", "hiring_policy_state",
    "public_project_count", "megaproject_staffing_demand",
)
TABLE = "public_hiring"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
