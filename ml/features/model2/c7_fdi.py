"""M2.C7 — FDI and industrial development pipeline."""
SPEC_IDS = ("M2.C7.V1", "M2.C7.V2", "M2.C7.V3", "M2.C7.V4", "M2.C7.V5", "M2.C7.V6")
COLUMNS = (
    "fdi_inflow_usd", "industrial_park", "industrial_park_operational_flag",
    "new_investment_project_count", "factory_expansion_count",
    "expected_employment", "private_investment_pipeline_etb",
)
TABLE = "fdi_industrial"


def frame():
    from . import _load
    return _load.load(TABLE, COLUMNS)
