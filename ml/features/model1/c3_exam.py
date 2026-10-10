"""M1.C3 — National entrance exam and placement data."""
SPEC_IDS = (
    "M1.C3.V1", "M1.C3.V2", "M1.C3.V3", "M1.C3.V4", "M1.C3.V5", "M1.C3.V6",
)
COLUMNS = (
    "exam_candidates_count",
    "exam_pass_rate_pct",
    "exam_score_mean",
    "exam_score_sd",
    "exam_score_p25",
    "exam_score_p50",
    "exam_score_p75",
    "program_cutoff_score",
    "placed_count",
    "placement_rate_pct",
    "field_allocation_count",
    "band_allocation_ratio",
)
TABLE = "exam_placement"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
