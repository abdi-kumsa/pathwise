"""
Model 1 — two-layer higher-education demand forecasting.

Roles: MoE (national) and University (own institution). ADMIN satisfies
require_roles as a superset. A UNIVERSITY caller is scoped from the signed
token: a different `?institution=` is 403 unless the cross-institution grant
is on the record, and its groupings always keep `institution` so the rows it
receives are its own rather than sums across every HEI.
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from services.auth_service import (
    ROLE_MOE,
    ROLE_UNIVERSITY,
    get_current_user,
    log_audit,
    require_roles,
    resolve_institution,
)
from services import constraint_service as m1
from ml.forecasting import accuracy_summary

router = APIRouter(
    prefix="/model1",
    tags=["Model 1 — Education Demand"],
    dependencies=[Depends(require_roles(ROLE_MOE, ROLE_UNIVERSITY))],
)

_INSTITUTION_GRAIN = {"institution", "campus"}

_INSTITUTION_QUERY = Query(
    None,
    description=(
        "UNIVERSITY: defaults to own HEI; another HEI is 403 without the "
        "cross-institution grant. MoE / ADMIN: optional filter."
    ),
)


def _institution_scope(user: dict, requested: str | None) -> str | None:
    """Which institution's rows to return, or None for all.

    UNIVERSITY is pinned to the JWT institution; a crafted `?institution=` is
    403 unless the grant is on the record (SCOPE.UNI.R2, SCOPE.G3) rather than
    being silently narrowed. MoE and ADMIN may read any HEI.
    """
    if user.get("role") == ROLE_UNIVERSITY:
        return resolve_institution(user, requested)
    return requested


def _audit_drilldown(user: dict, resource: str, dims: list[str] | None, n: int,
                     institution: str | None) -> None:
    """SCOPE.MOE.R2 — institution-level reads by a ministry are logged.

    A UNIVERSITY reading its own rows is not a drill-down (cross reads are
    logged by resolve_institution). Rows are institution-level unless the
    caller grouped them above institution and campus.
    """
    if user.get("role") == ROLE_UNIVERSITY:
        return
    institution_grain = dims is None or bool(_INSTITUTION_GRAIN & set(dims))
    if institution_grain:
        log_audit(user, "institution_drilldown", resource, {
            "group_by": dims, "n": n, "institution": institution,
        })


def _dimensions(group_by: str | None, user: dict | None = None) -> list[str] | None:
    if not group_by:
        return None
    wanted = [d.strip() for d in group_by.split(",") if d.strip()]
    bad = [d for d in wanted if d not in m1.DIMENSIONS]
    if bad:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown dimension(s) {bad}. Allowed: {list(m1.DIMENSIONS)}",
        )
    if user and user.get("role") == ROLE_UNIVERSITY and "institution" not in wanted:
        # Grouping happens before scoping. Without `institution` in the key a
        # region grouping would sum every HEI in the region, which identifies
        # another institution wherever a region has only one.
        wanted = ["institution", *wanted]
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
    institution: str | None = _INSTITUTION_QUERY,
    user: dict = Depends(get_current_user),
):
    dims = _dimensions(group_by, user)
    scope = _institution_scope(user, institution)
    try:
        df = m1.unconstrained_demand(horizon=horizon, dimensions=dims)
        df = m1.scope_to_institution(df, scope)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    _audit_drilldown(user, "model1/demand/unconstrained", dims, int(len(df)), scope)
    return {"layer": "M1.L1", "horizon": horizon, "n": int(len(df)),
            "accuracy": accuracy_summary("M1.applications"), "rows": _records(df)}


@router.get("/demand/constrained")  # /model1/demand/constrained
def constrained_demand(
    horizon: int = Query(3, ge=1, le=5),
    group_by: str | None = Query(None),
    institution: str | None = _INSTITUTION_QUERY,
    user: dict = Depends(get_current_user),
):
    dims = _dimensions(group_by, user)
    scope = _institution_scope(user, institution)
    try:
        df = m1.constrained_demand(horizon=horizon, dimensions=dims)
        df = m1.scope_to_institution(df, scope)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    _audit_drilldown(user, "model1/demand/constrained", dims, int(len(df)), scope)
    return {"layer": "M1.L2", "horizon": horizon, "n": int(len(df)),
            "accuracy": accuracy_summary("M1.applications"), "rows": _records(df)}


@router.get("/constraints/explain")  # /model1/constraints/explain
def constraints_explain():
    """Inspectable rule order — the constraint layer is not a learned model."""
    try:
        return {"layer": "M1.L2", **m1.constraint_explain()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/cohort-progression")  # /model1/cohort-progression
def cohort_progression(
    institution: str | None = _INSTITUTION_QUERY,
    user: dict = Depends(get_current_user),
):
    scope = _institution_scope(user, institution)
    try:
        df = m1.scope_to_institution(m1.cohort_progression(), scope)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    _audit_drilldown(user, "model1/cohort-progression", None, int(len(df)), scope)
    return {"n": int(len(df)), "rows": _records(df)}


@router.get("/funnel")  # /model1/funnel
def admissions_funnel(
    institution: str | None = _INSTITUTION_QUERY,
    user: dict = Depends(get_current_user),
):
    scope = _institution_scope(user, institution)
    try:
        df = m1.scope_to_institution(m1.admissions_funnel(), scope)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    _audit_drilldown(user, "model1/funnel", None, int(len(df)), scope)
    return {"n": int(len(df)), "rows": _records(df)}
