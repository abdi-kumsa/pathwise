"""M2.C8 — Macroeconomic and financial conditions."""
SPEC_IDS = ("M2.C8.V1", "M2.C8.V2", "M2.C8.V3", "M2.C8.V4", "M2.C8.V5", "M2.C8.V6")
COLUMNS = (
    "gdp_growth_rate_pct", "cpi_index", "inflation_rate_pct",
    "exchange_rate_etb_usd", "forex_reserve_months",
    "gross_investment_etb", "interest_rate_pct",
)
TABLE = "macro_financial"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
