"""
Model 3 — education–employment alignment engine.

Roles: MoE, MoL and University. ADMIN satisfies require_roles as a superset.
Student-facing slices live on /api/student/*.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.database import get_db
from services import alignment_service as m3
from services.auth_service import ROLE_MOE, ROLE_MOL, ROLE_UNIVERSITY, get_current_user, require_roles

router = APIRouter(
    prefix="/model3",
    tags=["Model 3 — Alignment"],
    dependencies=[Depends(require_roles(ROLE_MOE, ROLE_MOL, ROLE_UNIVERSITY))],
)


def _records(df):
    return m3.as_records(df)


@router.get("/supply")  # /model3/supply
def supply(horizon: int = Query(1, ge=1, le=5)):
    try:
        df = m3.supply(horizon=horizon)
        return {"n": int(len(df)), "rows": _records(df)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/gap")  # /model3/gap
def gap(
    horizon: int = Query(1, ge=1, le=5),
    group_by: str = Query("field,period"),
):
    try:
        dims = tuple(d.strip() for d in group_by.split(",") if d.strip())
        df = m3.gap(horizon=horizon, group=dims)
        return {"n": int(len(df)), "rows": _records(df)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/pathways")  # /model3/pathways
def pathways():
    try:
        return m3.pathway_graph()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/policy-priority")  # /model3/policy-priority
def policy_priority(horizon: int = Query(1, ge=1, le=5)):
    try:
        return m3.policy_ranking(horizon=horizon)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/scenarios")  # /model3/scenarios
def scenarios(
    quota_scale: float = Query(1.0, ge=0.25, le=3.0),
    capacity_scale: float = Query(1.0, ge=0.25, le=3.0),
    priority_field: str | None = None,
    natural_share: float = Query(0.70, ge=0.5, le=0.9),
    horizon: int = Query(1, ge=1, le=5),
):
    try:
        fields = [priority_field] if priority_field else None
        return m3.simulate(
            quota_scale=quota_scale,
            capacity_scale=capacity_scale,
            priority_fields=fields,
            natural_share=natural_share,
            social_share=round(1.0 - natural_share, 4),
            horizon=horizon,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/scenarios")  # /model3/scenarios
def persist_scenario(
    body: dict,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        fields = body.get("priority_fields") or (
            [body["priority_field"]] if body.get("priority_field") else None
        )
        natural = float(body.get("natural_share", 0.70))
        payload = m3.simulate(
            quota_scale=float(body.get("quota_scale", 1.0)),
            capacity_scale=float(body.get("capacity_scale", 1.0)),
            priority_fields=fields,
            priority_boost=float(body.get("priority_boost", 1.25)),
            natural_share=natural,
            social_share=float(body.get("social_share", round(1.0 - natural, 4))),
            horizon=int(body.get("horizon", 1)),
        )
        saved = m3.persist_scenario(
            db,
            owner=user.get("username") or "unknown",
            name=str(body.get("name") or "untitled-scenario"),
            payload=payload,
        )
        return {**payload, **saved}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
