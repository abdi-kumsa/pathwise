"""M2.C2 — Sector-level employment and economic output."""
SPEC_IDS = ("M2.C2.V1", "M2.C2.V2", "M2.C2.V3", "M2.C2.V4", "M2.C2.V5", "M2.C2.V6")
COLUMNS = (
    "sector_value_added_etb", "sector_growth_rate_pct", "sector_output_index",
    "business_formation_count", "sector_investment_etb", "employment_intensity",
)
TABLE = "sector_output"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
