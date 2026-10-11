"""
M3.3 — recommendation engines.

Student alternatives, institution programme actions, and policy field
prioritisation. Ranking factors are labour demand, expected supply,
eligibility and skills mapping. Graduate fit classification is a displayed
caveat elsewhere and does not enter these scores (RANK.R1).
"""
from __future__ import annotations

import pandas as pd

from ml.features.model2 import c5_skills
from ml.model1.layer1_demand import forecast_unconstrained
from ml.model1.layer2_constraints import apply_constraints
from ml.model3.gap import _minmax, eligibility_by_field, supply_demand_gap

STUDENT_WEIGHTS = {
    "labour_demand": 0.35,
    "expected_supply": 0.25,
    "eligibility": 0.20,
    "skills_fit": 0.20,
}
STUDENT_METHOD = (
    "Each factor is min-max normalised across MoE fields, then combined with "
    "the published weights. expected_supply is inverted so a thinner graduate "
    "pipeline ranks higher. Eligibility is the field's ESSLCE pass rate, not a "
    "student-level score. Skills fit is the employer shortage index mapped onto "
    "the same field taxonomy."
)

POLICY_WEIGHTS = {
    "labour_shortage": 0.35,
    "national_priority": 0.25,
    "student_demand": 0.20,
    "feasibility": 0.20,
}
POLICY_METHOD = (
    "Each factor is min-max normalised across fields, then combined with the "
    "published weights. national_priority is the share of forecast intake in "
    "programmes flagged strategic. feasibility is 1 − constraint-loss ratio. "
    "Scores are relative, not absolute."
)


def _skills_by_field() -> pd.DataFrame:
    skills = c5_skills.frame()
    if skills.empty:
        return pd.DataFrame(columns=["field", "skills_fit"])
    latest = int(skills["year"].max())
    now = skills[skills["year"] == latest]
    return (
        now.groupby("field", as_index=False)["skill_shortage_index"]
        .mean()
        .rename(columns={"skill_shortage_index": "skills_fit"})
    )


def student_alternatives(current_field: str | None = None, horizon: int = 1) -> pd.DataFrame:
    gap = supply_demand_gap(horizon=horizon, group=("field", "period"))
    if gap.empty:
        return gap
    latest = gap[gap["period"] == gap["period"].max()].copy()
    elig = eligibility_by_field()
    skills = _skills_by_field()
    if not elig.empty:
        latest = latest.merge(elig, on="field", how="left")
    if not skills.empty:
        latest = latest.merge(skills, on="field", how="left")
    latest["eligibility_pct"] = latest.get("eligibility_pct", pd.Series(50.0, index=latest.index)).fillna(50.0)
    latest["skills_fit"] = latest.get("skills_fit", pd.Series(0.5, index=latest.index)).fillna(0.5)
    components = {
        "labour_demand": _minmax(latest["labour_demand"]),
        "expected_supply": _minmax(-latest["expected_graduates"].astype(float)),
        "eligibility": _minmax(latest["eligibility_pct"]),
        "skills_fit": _minmax(latest["skills_fit"]),
    }
    latest["score"] = (
        sum(components[k] * w for k, w in STUDENT_WEIGHTS.items()) * 100
    ).round(1)
    if current_field:
        latest["is_current"] = latest["field"].astype(str).eq(current_field)
    else:
        latest["is_current"] = False
    ranked = latest.sort_values(["is_current", "score"], ascending=[True, False])
    rows = []
    rank = 0
    for idx, r in ranked.iterrows():
        if r["is_current"]:
            rec_rank = None
        else:
            rank += 1
            rec_rank = rank
        rows.append({
            **{k: r[k] for k in r.index if k != "factors"},
            "rank": rec_rank,
            "factors": [
                {
                    "factor": k,
                    "weight": w,
                    "normalised": round(float(components[k].loc[idx]), 3),
                    "contribution": round(float(components[k].loc[idx]) * w * 100, 1),
                }
                for k, w in STUDENT_WEIGHTS.items()
            ],
            "weights": STUDENT_WEIGHTS,
            "method": STUDENT_METHOD,
        })
    return pd.DataFrame(rows)


def _action(status: str, severity: int) -> str:
    if status == "shortage" and severity >= 3:
        return "expand"
    if status == "shortage":
        return "maintain"
    if status == "balanced":
        return "maintain"
    if severity >= 3:
        return "consolidate"
    return "review"


def institution_actions(horizon: int = 1, institution: str | None = None) -> pd.DataFrame:
    gap = supply_demand_gap(horizon=horizon, group=("field", "program", "period"))
    if gap.empty:
        return gap
    latest = gap[gap["period"] == gap["period"].max()].copy()
    from ml.model3.supply import graduate_supply
    raw = graduate_supply(horizon=horizon)
    if institution and "institution" in raw.columns:
        raw = raw[raw["institution"] == institution]
        prog_gap = supply_demand_gap(horizon=horizon, group=("program", "field", "period"))
        latest = prog_gap[prog_gap["period"] == prog_gap["period"].max()].copy()
        offered = set(raw["program"].astype(str))
        latest = latest[latest["program"].astype(str).isin(offered)]
    latest["action"] = [
        _action(str(s), int(q)) for s, q in zip(latest["status"], latest["severity"])
    ]
    latest["fit_classification_used"] = False
    return latest.sort_values(["severity", "abs_gap"], ascending=[False, False])


def policy_priority(horizon: int = 1) -> pd.DataFrame:
    gap = supply_demand_gap(horizon=horizon, group=("field", "period"))
    if gap.empty:
        return gap
    latest = gap[gap["period"] == gap["period"].max()].copy()
    constrained = apply_constraints(forecast_unconstrained(horizon=horizon))
    if constrained.empty:
        return latest
    year = int(constrained["academic_year"].max())
    now = constrained[constrained["academic_year"] == year]
    demand = now.groupby("field", as_index=False)["unconstrained_demand"].sum()
    loss = now.groupby("field", as_index=False).agg(
        unconstrained_demand=("unconstrained_demand", "sum"),
        constrained_enrollment=("constrained_enrollment", "sum"),
    )
    loss["feasibility"] = (
        1.0 - (loss["unconstrained_demand"] - loss["constrained_enrollment"]).clip(lower=0)
        / loss["unconstrained_demand"].replace(0, pd.NA)
    ).fillna(0.5)
    if "strategic_priority_flag" in now.columns and "field" in now.columns:
        flag = now["strategic_priority_flag"].fillna(False).astype(bool)
        tagged = now[flag].groupby("field")["constrained_enrollment"].sum()
        total = now.groupby("field")["constrained_enrollment"].sum()
        priority = (tagged / total).reindex(total.index).fillna(0.0)
        prio = priority.rename("national_priority").reset_index()
    else:
        prio = pd.DataFrame({"field": latest["field"].unique(), "national_priority": 0.0})
    latest = latest.merge(demand, on="field", how="left")
    latest = latest.merge(loss[["field", "feasibility"]], on="field", how="left")
    latest = latest.merge(prio, on="field", how="left")
    latest["unconstrained_demand"] = latest["unconstrained_demand"].fillna(0.0)
    latest["feasibility"] = latest["feasibility"].fillna(0.5)
    latest["national_priority"] = latest["national_priority"].fillna(0.0)
    shortage = latest["signed_gap"].clip(lower=0)
    components = {
        "labour_shortage": _minmax(shortage),
        "national_priority": _minmax(latest["national_priority"]),
        "student_demand": _minmax(latest["unconstrained_demand"]),
        "feasibility": _minmax(latest["feasibility"]),
    }
    latest["score"] = (
        sum(components[k] * w for k, w in POLICY_WEIGHTS.items()) * 100
    ).round(1)
    latest = latest.sort_values("score", ascending=False)
    latest["rank"] = range(1, len(latest) + 1)
    rows = []
    for idx, r in latest.iterrows():
        rows.append({
            **r.to_dict(),
            "factors": [
                {
                    "factor": k,
                    "weight": w,
                    "normalised": round(float(components[k].loc[idx]), 3),
                    "contribution": round(float(components[k].loc[idx]) * w * 100, 1),
                }
                for k, w in POLICY_WEIGHTS.items()
            ],
            "weights": POLICY_WEIGHTS,
            "method": POLICY_METHOD,
        })
    return pd.DataFrame(rows)
