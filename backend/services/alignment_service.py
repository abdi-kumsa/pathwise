"""
Model 3 service wrapper — alignment, recommendations, pathways and scenarios.

Rules stay in ml/model3 so they can be unit-tested without FastAPI.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ml.model3.gap import ALIGNMENT_METHOD, ALIGNMENT_WEIGHTS, alignment_score, supply_demand_gap
from ml.model3.pathways import pathway_graph
from ml.model3.recommend import (
    POLICY_METHOD,
    POLICY_WEIGHTS,
    STUDENT_METHOD,
    STUDENT_WEIGHTS,
    institution_actions,
    policy_priority,
    student_alternatives,
)
from ml.model3.scenario import run_scenario
from services._cache import ttl_cache
from ml.model3.supply import graduate_supply


def as_records(df: pd.DataFrame | None) -> list[dict]:
    if df is None or getattr(df, "empty", True):
        return []
    return json.loads(df.to_json(orient="records"))


def supply(horizon: int = 1, institution: str | None = None) -> pd.DataFrame:
    df = graduate_supply(horizon=horizon)
    if institution and "institution" in df.columns:
        return df[df["institution"] == institution].copy()
    return df


def gap(horizon: int = 1, group: tuple[str, ...] = ("field", "period")) -> pd.DataFrame:
    return supply_demand_gap(horizon=horizon, group=group)


def field_alignment(horizon: int = 1) -> dict:
    df = alignment_score(horizon=horizon)
    return {
        "n": int(len(df)),
        "weights": ALIGNMENT_WEIGHTS,
        "method": ALIGNMENT_METHOD,
        "ranking_factors": list(ALIGNMENT_WEIGHTS),
        "fit_classification_used": False,
        "rows": as_records(df),
    }


def alternatives(current_field: str | None = None, horizon: int = 1) -> dict:
    df = student_alternatives(current_field=current_field, horizon=horizon)
    return {
        "n": int(len(df)),
        "weights": STUDENT_WEIGHTS,
        "method": STUDENT_METHOD,
        "ranking_factors": list(STUDENT_WEIGHTS),
        "fit_classification_used": False,
        "rows": as_records(df),
    }


def program_health(horizon: int = 1, institution: str | None = None) -> dict:
    df = institution_actions(horizon=horizon, institution=institution)
    return {
        "n": int(len(df)),
        "severity_buckets": ["shortage", "balanced", "oversupply"],
        "actions": ["expand", "maintain", "review", "consolidate"],
        "weights": {"labour_demand": 1.0, "expected_graduates": -1.0},
        "ranking_factors": ["labour_demand", "expected_graduates", "gap"],
        "fit_classification_used": False,
        "method": (
            "Status is the sign of labour demand minus expected graduates. "
            "Severity is the quartile of |gap| (not a fixed coverage threshold). "
            "Actions follow severity: expand / maintain / review / consolidate. "
            "Graduate fit classification does not enter."
        ),
        "rows": as_records(df),
    }


def policy_ranking(horizon: int = 1) -> dict:
    df = policy_priority(horizon=horizon)
    return {
        "n": int(len(df)),
        "weights": POLICY_WEIGHTS,
        "method": POLICY_METHOD,
        "ranking_factors": list(POLICY_WEIGHTS),
        "fit_classification_used": False,
        "rows": as_records(df),
    }


def regional_alignment(horizon: int = 1) -> pd.DataFrame:
    return supply_demand_gap(horizon=horizon, group=("region", "field", "period"))


def three_way(horizon: int = 1, institution: str | None = None) -> pd.DataFrame:
    """Student demand, expected graduates and labour demand by field."""
    from ml.model1.layer1_demand import forecast_unconstrained
    from ml.model1.layer2_constraints import apply_constraints

    constrained = apply_constraints(forecast_unconstrained(horizon=horizon))
    if institution and "institution" in constrained.columns:
        constrained = constrained[constrained["institution"] == institution]
    g = graduate_supply(horizon=horizon, constrained=constrained)
    demand = supply_demand_gap(horizon=horizon, group=("field", "period"))
    year = int(g["academic_year"].max()) if not g.empty else None
    if year is not None:
        g = g[g["academic_year"] == year]
        constrained = constrained[constrained["academic_year"] == year]
        demand = demand[demand["period"] == year]
    left = constrained.groupby("field", as_index=False).agg(
        student_demand=("unconstrained_demand", "sum"),
        constrained_enrollment=("constrained_enrollment", "sum"),
    )
    grads = g.groupby("field", as_index=False)["expected_graduates"].sum()
    out = left.merge(grads, on="field", how="outer").merge(
        demand[["field", "labour_demand", "signed_gap", "status", "severity"]],
        on="field",
        how="outer",
    )
    for col in ("student_demand", "constrained_enrollment", "expected_graduates", "labour_demand", "signed_gap", "severity"):
        if col in out.columns:
            out[col] = out[col].fillna(0)
    if "status" in out.columns:
        out["status"] = out["status"].fillna("balanced")
    return out


def skill_gaps(horizon: int = 1) -> dict:
    from ml.model2.skills import skills_shortage
    df = skills_shortage(horizon=horizon)
    return {
        "n": int(len(df)),
        "skill_classes": ["technical", "digital", "soft", "emerging"],
        "rows": as_records(df),
    }


def curriculum_alignment(horizon: int = 1, institution: str | None = None) -> dict:
    graph = pathway_graph()
    health = program_health(horizon=horizon, institution=institution)
    return {
        "pathways": graph,
        "program_health": health,
        "note": (
            "Employer skill demand is mapped onto the MoE field/programme list. "
            "Curriculum coverage is inferred from that mapping until a ministry "
            "curriculum file exists."
        ),
    }


def simulate(**levers: Any) -> dict:
    return run_scenario(**levers)


def persist_scenario(db, *, owner: str, name: str, payload: dict) -> dict:
    """Write the what-if to `scenarios`. Failures are returned, not raised, so a
    missing table cannot take the simulator off the request path."""
    from sqlalchemy.exc import SQLAlchemyError
    from models.governance import Scenario

    assumptions = dict(payload.get("assumptions") or {})
    assumptions["official_forecast"] = False
    try:
        row = Scenario(
            name=name,
            owner=owner,
            assumptions={
                "assumptions": assumptions,
                "baseline": payload.get("baseline"),
                "scenario": payload.get("scenario"),
                "delta": payload.get("delta"),
                "official_forecast": False,
            },
            status="draft",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return {
            "persisted": True,
            "id": row.id,
            "status": row.status,
            "official_forecast": False,
        }
    except SQLAlchemyError as exc:
        db.rollback()
        return {
            "persisted": False,
            "official_forecast": False,
            "reason": str(exc.__class__.__name__),
        }


@ttl_cache
def resource_planning(institution: str, quota_scale: float = 1.0, capacity_scale: float = 1.0) -> dict:
    """Institution-grain resource table plus an unofficial intake what-if."""
    from ml.features.model1 import c4_quota, c8_institution, c9_finance
    from ml.model1.layer1_demand import forecast_unconstrained
    from ml.model1.layer2_constraints import apply_constraints
    from ml.model3.scenario import apply_levers
    from ml.model3.supply import graduate_supply

    def _scope(df):
        if df.empty or "institution" not in df.columns:
            return df
        return df[df["institution"] == institution].copy()

    cap = _scope(c8_institution.frame())
    fin = _scope(c9_finance.frame())
    quota = c4_quota.frame()
    unconstrained = forecast_unconstrained(horizon=1)
    unconstrained = _scope(unconstrained)
    baseline = apply_constraints(unconstrained) if not unconstrained.empty else unconstrained
    scenario_quota = apply_levers(quota, quota_scale=quota_scale, capacity_scale=capacity_scale)
    scenario = (
        apply_constraints(unconstrained, quota=scenario_quota)
        if not unconstrained.empty else unconstrained
    )
    base_g = graduate_supply(constrained=baseline) if not getattr(baseline, "empty", True) else baseline
    scen_g = graduate_supply(constrained=scenario) if not getattr(scenario, "empty", True) else scenario

    def _sum(df, col):
        if df is None or getattr(df, "empty", True) or col not in df.columns:
            return 0.0
        return round(float(df[col].sum()), 1)

    return {
        "institution": institution,
        "official_forecast": False,
        "assumptions": {
            "quota_scale": quota_scale,
            "capacity_scale": capacity_scale,
            "levers": ["quota", "capacity"],
        },
        "capacity": as_records(cap[cap["year"] == cap["year"].max()] if not cap.empty else cap),
        "finance": as_records(fin[fin["year"] == fin["year"].max()] if not fin.empty else fin),
        "baseline": {
            "constrained_enrollment": _sum(baseline, "constrained_enrollment"),
            "expected_graduates": _sum(base_g, "expected_graduates"),
        },
        "scenario": {
            "constrained_enrollment": _sum(scenario, "constrained_enrollment"),
            "expected_graduates": _sum(scen_g, "expected_graduates"),
        },
        "note": (
            "What-if against this institution's simulated baseline, not an official "
            "MoE forecast. Assumptions travel with the run."
        ),
    }
