"""
M3.5 — policy / capacity scenario engine.

What-ifs over quota, priority field, placement rule and capacity.
Each run is labelled unofficial so it cannot be mistaken for a baseline
forecast (the reason W.ADM.05 exists). Persistence lives in the service layer.

Levers and what they change in the Layer 2 inputs:

    quota            approved intake quota and available seats  (× quota_scale)
    capacity         programme capacity                          (× capacity_scale)
    priority_field   quota and seats of the named fields         (× priority_boost)
    placement_rule   ESSLCE pass rate, in percentage points       (+ pass_rate_shift_pp)
    band_allocation  natural : social science directive           (natural_share)

Graduate supply follows cohorts (ml/model3/supply.py), so a lever reaches
expected graduates only for intakes after the origin — about four years out.
"""
from __future__ import annotations

import pandas as pd

from ml.features.model1 import c3_exam, c4_quota
from ml.model1.layer1_demand import forecast_unconstrained
from ml.model1.layer2_constraints import NATURAL_SHARE, SOCIAL_SHARE, apply_constraints
from ml.model3.supply import graduate_supply

LEVERS = ("quota", "priority_field", "placement_rule", "capacity", "band_allocation")
PASS_RATE_SHIFT_LIMIT = 15.0


def apply_placement_rule(exam: pd.DataFrame, pass_rate_shift_pp: float = 0.0) -> pd.DataFrame:
    """Move the ESSLCE pass rate by a number of percentage points, clipped 0–100."""
    e = exam.copy()
    if pass_rate_shift_pp and "exam_pass_rate_pct" in e.columns:
        e["exam_pass_rate_pct"] = (
            e["exam_pass_rate_pct"].astype(float) + float(pass_rate_shift_pp)
        ).clip(0, 100)
    return e


def apply_levers(
    quota: pd.DataFrame,
    *,
    quota_scale: float = 1.0,
    capacity_scale: float = 1.0,
    priority_fields: list[str] | None = None,
    priority_boost: float = 1.25,
) -> pd.DataFrame:
    q = quota.copy()
    if "approved_intake_quota" in q.columns:
        q["approved_intake_quota"] = q["approved_intake_quota"].astype(float) * quota_scale
    if "available_seats" in q.columns:
        q["available_seats"] = q["available_seats"].astype(float) * quota_scale
    if "program_capacity" in q.columns:
        q["program_capacity"] = q["program_capacity"].astype(float) * capacity_scale
    if priority_fields and "field" in q.columns:
        mask = q["field"].astype(str).isin(priority_fields)
        if "approved_intake_quota" in q.columns:
            q.loc[mask, "approved_intake_quota"] *= priority_boost
        if "available_seats" in q.columns:
            q.loc[mask, "available_seats"] *= priority_boost
        if "strategic_priority_flag" in q.columns:
            q.loc[mask, "strategic_priority_flag"] = True
    return q


def _totals(constrained: pd.DataFrame) -> dict:
    if constrained.empty:
        return {
            "unconstrained_demand": 0.0,
            "constrained_enrollment": 0.0,
            "expected_graduates": 0.0,
            "n": 0,
        }
    supply = graduate_supply(constrained=constrained)
    return {
        "unconstrained_demand": round(float(constrained["unconstrained_demand"].sum()), 1),
        "constrained_enrollment": round(float(constrained["constrained_enrollment"].sum()), 1),
        "expected_graduates": round(float(supply["expected_graduates"].sum()), 1),
        "n": int(len(constrained)),
    }


def run_scenario(
    *,
    quota_scale: float = 1.0,
    capacity_scale: float = 1.0,
    priority_fields: list[str] | None = None,
    priority_boost: float = 1.25,
    natural_share: float = NATURAL_SHARE,
    social_share: float = SOCIAL_SHARE,
    pass_rate_shift_pp: float = 0.0,
    horizon: int = 1,
) -> dict:
    if abs(float(pass_rate_shift_pp)) > PASS_RATE_SHIFT_LIMIT:
        raise ValueError(f"pass_rate_shift_pp must be within ±{PASS_RATE_SHIFT_LIMIT}")
    unconstrained = forecast_unconstrained(horizon=horizon)
    quota = c4_quota.frame()
    baseline = apply_constraints(unconstrained)
    scenario_quota = apply_levers(
        quota,
        quota_scale=quota_scale,
        capacity_scale=capacity_scale,
        priority_fields=priority_fields,
        priority_boost=priority_boost,
    )
    scenario = apply_constraints(
        unconstrained,
        quota=scenario_quota,
        exam=apply_placement_rule(c3_exam.frame(), pass_rate_shift_pp),
        natural_share=natural_share,
        social_share=social_share,
    )
    base_tot = _totals(baseline)
    scen_tot = _totals(scenario)
    assumptions = {
        "quota_scale": quota_scale,
        "capacity_scale": capacity_scale,
        "priority_fields": list(priority_fields or []),
        "priority_boost": priority_boost,
        "natural_share": natural_share,
        "social_share": social_share,
        "pass_rate_shift_pp": pass_rate_shift_pp,
        "horizon": horizon,
        "levers": list(LEVERS),
    }
    return {
        "official_forecast": False,
        "status": "draft",
        "assumptions": assumptions,
        "baseline": base_tot,
        "scenario": scen_tot,
        "delta": {
            "unconstrained_demand": round(scen_tot["unconstrained_demand"] - base_tot["unconstrained_demand"], 1),
            "constrained_enrollment": round(scen_tot["constrained_enrollment"] - base_tot["constrained_enrollment"], 1),
            "expected_graduates": round(scen_tot["expected_graduates"] - base_tot["expected_graduates"], 1),
        },
        "note": (
            "This is a what-if against the simulated baseline, not an official "
            "MoE forecast. Assumptions are stored with the run so it cannot be "
            "quoted without them. Expected graduates change only for cohorts that "
            "enter after the last observed year, so at short horizons the graduate "
            "delta is zero by design: those graduates are already enrolled."
        ),
    }
