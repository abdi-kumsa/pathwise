"""
Model 1 — two-layer higher-education demand forecasting.

Roles: MoE (national) and University (own institution). ADMIN satisfies
require_roles as a superset. A UNIVERSITY caller is scoped from the signed
token; `institution` is never taken from the query string.
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from services.auth_service import (
    ROLE_MOE,
    ROLE_UNIVERSITY,
    get_current_user,
    require_roles,
)
from services import constraint_service as m1

router = APIRouter(
    prefix="/model1",
    tags=["Model 1 — Education Demand"],
    dependencies=[Depends(require_roles(ROLE_MOE, ROLE_UNIVERSITY))],
)


def _institution_scope(user: dict) -> str | None:
    if user.get("role") == ROLE_UNIVERSITY:
        institution = user.get("institution")
        if not institution:
            raise HTTPException(
                status_code=403,
                detail="University account is not linked to an institution.",
            )
        return institution
    return None


def _dimensions(group_by: str | None) -> list[str] | None:
    if not group_by:
        return None
    wanted = [d.strip() for d in group_by.split(",") if d.strip()]
    bad = [d for d in wanted if d not in m1.DIMENSIONS]
    if bad:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown dimension(s) {bad}. Allowed: {list(m1.DIMENSIONS)}",
        )
    return wanted


def _records(df) -> list[dict]:
    if df is None or df.empty:
        return []
    return df.where(df.notna(), None).to_dict(orient="records")


@router.get("/demand/unconstrained")  # /model1/demand/unconstrained
def unconstrained_demand(
    horizon: int = Query(3, ge=1, le=5),
    group_by: str | None = Query(
        None,
        description="Comma-separated DOC1 dimensions: institution,campus,region,program,academic_year",
    ),
    user: dict = Depends(get_current_user),
):
    try:
        df = m1.unconstrained_demand(horizon=horizon, dimensions=_dimensions(group_by))
        df = m1.scope_to_institution(df, _institution_scope(user))
        return {
            "layer": "M1.L1",
            "horizon": horizon,
            "n": int(len(df)),
            "rows": _records(df),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/demand/constrained")  # /model1/demand/constrained
def constrained_demand(
    horizon: int = Query(3, ge=1, le=5),
    group_by: str | None = Query(None),
    user: dict = Depends(get_current_user),
):
    try:
        df = m1.constrained_demand(horizon=horizon, dimensions=_dimensions(group_by))
        df = m1.scope_to_institution(df, _institution_scope(user))
        return {
            "layer": "M1.L2",
            "horizon": horizon,
            "n": int(len(df)),
            "rows": _records(df),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/constraints/explain")  # /model1/constraints/explain
def constraints_explain():
    """Inspectable rule order — the constraint layer is not a learned model."""
    try:
        return {"layer": "M1.L2", **m1.constraint_explain()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/cohort-progression")  # /model1/cohort-progression
def cohort_progression(user: dict = Depends(get_current_user)):
    try:
        df = m1.scope_to_institution(m1.cohort_progression(), _institution_scope(user))
        return {"n": int(len(df)), "rows": _records(df)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/funnel")  # /model1/funnel
def admissions_funnel(user: dict = Depends(get_current_user)):
    try:
        df = m1.scope_to_institution(m1.admissions_funnel(), _institution_scope(user))
        return {"n": int(len(df)), "rows": _records(df)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
