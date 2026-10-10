"""
M3.2 — supply–demand gap and alignment scoring.

Expected graduates vs projected occupational demand. Status is shortage /
balanced / oversupply; severity is a quartile of |gap| (RANK.R4), not a fixed
coverage threshold. Composite scores return weights, method and per-factor
decomposition (RANK.R3). Graduate fit classification does not enter.
"""
from __future__ import annotations

import pandas as pd

from ml.features.model1 import c3_exam, c7_outcomes
from ml.model2.forecast import forecast_vacancies
from ml.model3.supply import graduate_supply

ALIGNMENT_WEIGHTS = {
    "labour_demand": 0.40,
    "supply_shortfall": 0.35,
    "employment_outcome": 0.25,
}

ALIGNMENT_METHOD = (
    "Each factor is min-max normalised across the comparison set, then combined "
    "with the published weights. Scores are relative, not absolute. Severity is "
    "the quartile of |demand − supply|, not a fixed coverage cut."
)


def _minmax(series: pd.Series) -> pd.Series:
    s = series.astype(float)
    lo, hi = float(s.min()), float(s.max())
    span = hi - lo
    if pd.isna(span) or span < 1e-12:
        return pd.Series(0.5, index=s.index)
    return (s - lo) / span


def _quartile(abs_gap: pd.Series) -> pd.Series:
    pct = abs_gap.rank(method="average", pct=True)
    return pd.cut(pct, bins=[-0.01, 0.25, 0.50, 0.75, 1.01], labels=[1, 2, 3, 4]).astype(int)


def _status(signed: float, severity: int) -> str:
    if severity <= 1:
        return "balanced"
    return "shortage" if signed > 0 else "oversupply"


def _demand(horizon: int) -> pd.DataFrame:
    vac = forecast_vacancies(horizon=horizon)
    if vac.empty:
        return pd.DataFrame(columns=["field", "region", "period", "labour_demand"])
    keys = [c for c in ("field", "region", "period") if c in vac.columns]
    out = vac.groupby(keys, dropna=False, as_index=False)["vacancies"].sum()
    return out.rename(columns={"vacancies": "labour_demand"})


def _employment_by_field() -> pd.DataFrame:
    out = c7_outcomes.frame()
    if out.empty or "field" not in out.columns:
        return pd.DataFrame(columns=["field", "employment_rate_pct"])
    latest = int(out["year"].max())
    now = out[out["year"] == latest]
    return (
        now.groupby("field", as_index=False)["graduate_employment_rate_pct"]
        .mean()
        .rename(columns={"graduate_employment_rate_pct": "employment_rate_pct"})
    )


def supply_demand_gap(
    horizon: int = 1,
    group: tuple[str, ...] = ("field", "period"),
) -> pd.DataFrame:
    """Aggregate gap. `group` must be a subset of field / region / program / period."""
    supply = graduate_supply(horizon=horizon)
    demand = _demand(horizon)
    s_keys = [c for c in group if c in supply.columns]
    if "period" in group and "period" not in supply.columns and "academic_year" in supply.columns:
        supply = supply.copy()
        supply["period"] = supply["academic_year"]
        s_keys = [c for c in group if c in supply.columns]
    if "constrained_enrollment" in supply.columns:
        supplied = supply.groupby(s_keys, dropna=False, as_index=False).agg(
            expected_graduates=("expected_graduates", "sum"),
            enrollment=("constrained_enrollment", "sum"),
        )
    else:
        supplied = supply.groupby(s_keys, dropna=False, as_index=False)["expected_graduates"].sum()
    d_keys = [c for c in group if c in demand.columns]
    demanded = demand.groupby(d_keys, dropna=False, as_index=False)["labour_demand"].sum()
    merged = supplied.merge(demanded, on=[c for c in s_keys if c in d_keys], how="outer")
    merged["expected_graduates"] = merged["expected_graduates"].fillna(0.0)
    merged["labour_demand"] = merged["labour_demand"].fillna(0.0)
    if "enrollment" in merged.columns:
        merged["enrollment"] = merged["enrollment"].fillna(0.0)
    merged["signed_gap"] = (merged["labour_demand"] - merged["expected_graduates"]).round(1)
    merged["abs_gap"] = merged["signed_gap"].abs()
    merged["severity"] = _quartile(merged["abs_gap"])
    merged["status"] = [
        _status(float(s), int(q)) for s, q in zip(merged["signed_gap"], merged["severity"])
    ]
    coverage = merged["labour_demand"].replace(0, pd.NA)
    merged["coverage_pct"] = (
        (merged["expected_graduates"] / coverage * 100).clip(upper=999).round(1)
    )
    emp = _employment_by_field()
    if "field" in merged.columns and not emp.empty:
        merged = merged.merge(emp, on="field", how="left")
    return merged


def alignment_score(horizon: int = 1) -> pd.DataFrame:
    """Field-level opportunity score with RANK.R3 decomposition."""
    gap = supply_demand_gap(horizon=horizon, group=("field", "period"))
    if gap.empty:
        return gap
    latest = gap[gap["period"] == gap["period"].max()].copy()
    shortfall = (latest["labour_demand"] - latest["expected_graduates"]).clip(lower=0)
    components = {
        "labour_demand": _minmax(latest["labour_demand"]),
        "supply_shortfall": _minmax(shortfall),
        "employment_outcome": _minmax(latest.get("employment_rate_pct", pd.Series(0.5, index=latest.index)).fillna(0.5)),
    }
    latest["score"] = (
        sum(components[k] * w for k, w in ALIGNMENT_WEIGHTS.items()) * 100
    ).round(1)
    latest = latest.sort_values("score", ascending=False)
    latest["rank"] = range(1, len(latest) + 1)
    rows = []
    for idx, r in latest.iterrows():
        factors = [
            {
                "factor": k,
                "weight": w,
                "normalised": round(float(components[k].loc[idx]), 3),
                "contribution": round(float(components[k].loc[idx]) * w * 100, 1),
            }
            for k, w in ALIGNMENT_WEIGHTS.items()
        ]
        rec = r.to_dict()
        rec["factors"] = factors
        rec["weights"] = ALIGNMENT_WEIGHTS
        rec["method"] = ALIGNMENT_METHOD
        rows.append(rec)
    return pd.DataFrame(rows)


def eligibility_by_field() -> pd.DataFrame:
    """ESSLCE pass rate as a field accessibility proxy — not a student score."""
    exam = c3_exam.frame()
    if exam.empty or "field" not in exam.columns:
        return pd.DataFrame(columns=["field", "eligibility_pct"])
    latest = int(exam["year"].max())
    now = exam[exam["year"] == latest]
    return (
        now.groupby("field", as_index=False)["exam_pass_rate_pct"]
        .mean()
        .rename(columns={"exam_pass_rate_pct": "eligibility_pct"})
    )
