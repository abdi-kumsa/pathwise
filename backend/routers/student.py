"""
Student-facing Model 3 slices and Wave 5 widgets.

Widget paths for W.STU.01–09. ADMIN satisfies require_roles as a superset.
Identity is JWT `sub` via student_scope; query username/student_id are ignored.
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from services import alignment_service as m3
from services import trend_service as trends
from services import student_service as stu
from services.auth_service import student_scope

router = APIRouter(
    prefix="/student",
    tags=["Student — Alignment"],
)


@router.get("/profile")  # /student/profile
def profile(user: dict = Depends(student_scope), username: str | None = Query(None), student_id: str | None = Query(None)):
    try:
        return stu.profile(user)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/labour-outlook")  # /student/labour-outlook
def labour_outlook(user: dict = Depends(student_scope), field: str | None = Query(None)):
    try:
        return stu.labour_outlook(field or user.get("field"), horizons=(3, 5))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/demand-comparison")  # /student/demand-comparison
def demand_comparison(user: dict = Depends(student_scope)):
    try:
        return stu.demand_comparison(user.get("field"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/field-alignment")  # /student/field-alignment
def field_alignment(horizon: int = Query(1, ge=1, le=5), user: dict = Depends(student_scope)):
    try:
        payload = m3.field_alignment(horizon=horizon)
        field = user.get("field")
        payload["field"] = field
        for row in payload.get("rows") or []:
            row["is_own_field"] = bool(field) and str(row.get("field")) == str(field)
        return payload
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/supply-demand-gap")  # /student/supply-demand-gap
def supply_demand_gap(horizon: int = Query(1, ge=1, le=5), user: dict = Depends(student_scope)):
    try:
        df = m3.gap(horizon=horizon, group=("field", "period"))
        field = user.get("field")
        trend = trends.enrolment_trend(("field",))
        rows = trends.attach(m3.as_records(df), trend, ("field",))
        for row in rows:
            row["is_own_field"] = bool(field) and str(row.get("field")) == str(field)
        return {"n": int(len(rows)), "field": field, "rows": rows}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/alternatives")  # /student/alternatives
def alternatives(
    current_field: str | None = Query(None),
    horizon: int = Query(1, ge=1, le=5),
    user: dict = Depends(student_scope),
):
    try:
        return m3.alternatives(current_field=current_field or user.get("field"), horizon=horizon)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/skill-gaps")  # /student/skill-gaps
def skill_gaps(horizon: int = Query(1, ge=1, le=5), user: dict = Depends(student_scope)):
    try:
        return m3.skill_gaps(horizon=horizon)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/pathways")  # /student/pathways
def pathways(user: dict = Depends(student_scope)):
    try:
        return m3.pathway_graph()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/opportunities")  # /student/opportunities
def opportunities(user: dict = Depends(student_scope)):
    try:
        return stu.opportunities(user.get("field"), user.get("program"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
