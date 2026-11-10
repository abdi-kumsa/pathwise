"""
Model 2 — labour-market trend prediction.

Roles: MoL and MoE. ADMIN satisfies require_roles as a superset.
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from services.auth_service import ROLE_MOE, ROLE_MOL, require_roles
from services import model2_service as m2

router = APIRouter(
    prefix="/model2",
    tags=["Model 2 — Labour Demand"],
    dependencies=[Depends(require_roles(ROLE_MOL, ROLE_MOE))],
)


def _dimensions(group_by: str | None) -> list[str] | None:
    if not group_by:
        return None
    wanted = [d.strip() for d in group_by.split(",") if d.strip()]
    bad = [d for d in wanted if d not in m2.DIMENSIONS]
    if bad:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown dimension(s) {bad}. Allowed: {list(m2.DIMENSIONS)}",
        )
    return wanted


def _records(df) -> list[dict]:
    return m2.as_records(df)


@router.get("/forecast")  # /model2/forecast
def forecast(
    horizon: int = Query(3, ge=1, le=5),
    group_by: str | None = Query(
        None,
        description="Comma-separated DOC1 dimensions: sector,occupation,region,period",
    ),
):
    try:
        dims = _dimensions(group_by)
        df = m2.labour_forecast(horizon=horizon, dimensions=dims)
        hist = m2.forecast_history(dims)
        from ml.forecasting import accuracy_summary
        return {
            "targets": list(m2.TARGETS),
            "dimensions": list(m2.DIMENSIONS),
            "horizon": horizon,
            "n": int(len(df)),
            "accuracy": {
                tid: accuracy_summary(tid)
                for tid in ("M2.employment_demand", "M2.vacancies", "M2.skill_shortages")
            },
            "rows": _records(df),
            "history": _records(hist),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/formal-informal")  # /model2/formal-informal
def formal_informal(horizon: int = Query(3, ge=1, le=5)):
    try:
        df, caveat = m2.absorption(horizon=horizon)
        return {
            "n": int(len(df)),
            "caveat": caveat,
            "not_from_job_board": True,
            "rows": _records(df),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/skills-shortage")  # /model2/skills-shortage
def skills_shortage(horizon: int = Query(3, ge=1, le=5)):
    try:
        df = m2.skills(horizon=horizon)
        return {"n": int(len(df)), "rows": _records(df)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/public-pipeline")  # /model2/public-pipeline
def public_pipeline():
    try:
        df = m2.public_pipeline()
        return {"n": int(len(df)), "rows": _records(df)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/fdi-pipeline")  # /model2/fdi-pipeline
def fdi_pipeline():
    try:
        df = m2.fdi_pipeline()
        return {"n": int(len(df)), "rows": _records(df)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/migration")  # /model2/migration
def migration():
    try:
        return m2.migration()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/occupation/{code}")  # /model2/occupation/{code}
def occupation(code: str):
    try:
        return m2.occupation(code)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
