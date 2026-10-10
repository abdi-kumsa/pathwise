"""M1.C9 — Tuition, financial support and scholarships."""
SPEC_IDS = ("M1.C9.V1", "M1.C9.V2", "M1.C9.V3", "M1.C9.V4")
COLUMNS = (
    "tuition_fee_etb",
    "stipend_etb",
    "scholarship_availability",
    "cost_sharing_loan_etb",
)
TABLE = "finance_support"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
