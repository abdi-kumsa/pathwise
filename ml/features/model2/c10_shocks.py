"""M2.C10 — Seasonality, commodity and external shocks."""
SPEC_IDS = ("M2.C10.V1", "M2.C10.V2", "M2.C10.V3", "M2.C10.V4")
COLUMNS = (
    "agricultural_season", "hiring_season_index",
    "commodity_price_index", "external_shock_flag",
)
TABLE = "shocks_seasonality"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
