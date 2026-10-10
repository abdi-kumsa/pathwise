"""M1.C10 — Macroeconomic and regional socio-economic conditions."""
SPEC_IDS = ("M1.C10.V1", "M1.C10.V2", "M1.C10.V3", "M1.C10.V4")
COLUMNS = (
    "inflation_rate_pct",
    "household_income_proxy_etb",
    "youth_unemployment_rate_pct",
    "regional_socioeconomic_index",
)
TABLE = "macro_regional"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
