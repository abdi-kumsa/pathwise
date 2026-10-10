"""M1.C8 — Institutional capacity and quality."""
SPEC_IDS = ("M1.C8.V1", "M1.C8.V2", "M1.C8.V3", "M1.C8.V4", "M1.C8.V5")
COLUMNS = (
    "faculty_student_ratio",
    "laboratory_count",
    "classroom_count",
    "accreditation_status",
    "program_quality_index",
)
TABLE = "institution_capacity"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
