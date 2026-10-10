"""M2.C4 — Job vacancy and recruitment signals."""
SPEC_IDS = ("M2.C4.V1", "M2.C4.V2", "M2.C4.V3", "M2.C4.V4", "M2.C4.V5")
COLUMNS = (
    "vacancy_count", "occupation", "occupation_frequency",
    "required_education", "required_experience_years",
    "hiring_trend_pct", "time_to_fill_days",
)
TABLE = "vacancies"


def frame():
    from . import _load
    df = _load.load(TABLE, COLUMNS)
    keys = [c for c in ("region", "occupation") if c in df.columns]
    if df.empty or not keys or "vacancy_count" not in df.columns:
        return df
    df = df.sort_values(keys + ["year"])
    grouped = df.groupby(keys, sort=False)["vacancy_count"]
    df["vacancy_lag_1y"] = grouped.shift(1)
    df["vacancy_lag_2y"] = grouped.shift(2)
    return df
