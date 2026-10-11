"""M2.C5 — Skills demand and shortage indicators."""
SPEC_IDS = ("M2.C5.V1", "M2.C5.V2", "M2.C5.V3", "M2.C5.V4", "M2.C5.V5", "M2.C5.V6")
COLUMNS = (
    "technical_skill_demand", "digital_skill_demand", "soft_skill_demand",
    "emerging_skill_demand", "skill_shortage_index", "skill_oversupply_index",
)
TABLE = "skills_demand"


def frame():
    from . import _load
    df = _load.load(TABLE, COLUMNS)
    if df.empty or "field" not in df.columns or "skill_shortage_index" not in df.columns:
        return df
    df = df.sort_values(["field", "year"])
    grouped = df.groupby("field", sort=False)["skill_shortage_index"]
    df["skill_shortage_lag_1y"] = grouped.shift(1)
    df["skill_shortage_lag_2y"] = grouped.shift(2)
    return df
