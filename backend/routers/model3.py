"""
Model 3 — education–employment alignment engine.

Roles: MoE, MoL and University. ADMIN satisfies require_roles as a superset.
Student-facing slices live on /api/student/*.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.database import get_db
from schemas.scenarios import ScenarioRequest
from services import rate_limit
from services import alignment_service as m3
from services.auth_service import (
    ROLE_MOE,
    ROLE_MOL,
    ROLE_UNIVERSITY,
    get_current_user,
    log_audit,
    require_roles,
    resolve_institution,
)

router = APIRouter(
    prefix="/model3",
    tags=["Model 3 — Alignment"],
    dependencies=[Depends(require_roles(ROLE_MOE, ROLE_MOL, ROLE_UNIVERSITY))],
)


def _records(df):
    return m3.as_records(df)


# Dimensions a gap may be grouped by. Anything else is a 422, not a pandas error.
GAP_DIMENSIONS = ("field", "program", "region", "period", "institution", "campus")

# A UNIVERSITY caller sees national aggregates by field / programme / period.
# Institution or campus grain would expose every other HEI's figures, and
# region grain identifies an HEI wherever a region has only one (SCOPE.UNI.R1).
_UNIVERSITY_GAP_DIMENSIONS = {"field", "program", "period"}


@router.get("/supply")  # /model3/supply
def supply(
    horizon: int = Query(1, ge=1, le=5),
    institution: str | None = Query(
        None,
        description="UNIVERSITY: defaults to own HEI; another HEI needs the cross-institution grant.",
    ),
    user: dict = Depends(get_current_user),
):
    """Expected graduate supply per HEI × programme.

    UNIVERSITY rows are scoped to the caller's own institution from the signed
    token. A crafted `?institution=` is 403 unless the grant is on the record
    (SCOPE.UNI.R2, SCOPE.G3). MoE / MoL / ADMIN may filter by any HEI.
    """
    if user.get("role") == ROLE_UNIVERSITY:
        institution = resolve_institution(user, institution)
    try:
        df = m3.supply(horizon=horizon, institution=institution)
        return {"n": int(len(df)), "institution": institution, "rows": _records(df)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/gap")  # /model3/gap
def gap(
    horizon: int = Query(1, ge=1, le=5),
    group_by: str = Query("field,period"),
    user: dict = Depends(get_current_user),
):
    dims = tuple(d.strip() for d in group_by.split(",") if d.strip())
    unknown = [d for d in dims if d not in GAP_DIMENSIONS]
    if unknown or not dims:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown dimension(s) {unknown}. Allowed: {list(GAP_DIMENSIONS)}",
        )
    if user.get("role") == ROLE_UNIVERSITY:
        denied = [d for d in dims if d not in _UNIVERSITY_GAP_DIMENSIONS]
        if denied:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"University accounts may group the gap by "
                    f"{sorted(_UNIVERSITY_GAP_DIMENSIONS)} only; {denied} would "
                    "expose other institutions' figures."
                ),
            )
    try:
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
    pass_rate_shift_pp: float = Query(0.0, ge=-15.0, le=15.0),
    horizon: int = Query(1, ge=1, le=5),
    user: dict = Depends(rate_limit.per_user("scenario-whatif", 60, 60)),
):
    try:
        fields = [priority_field] if priority_field else None
        payload = m3.simulate(
            quota_scale=quota_scale,
            capacity_scale=capacity_scale,
            priority_fields=fields,
            natural_share=natural_share,
            social_share=round(1.0 - natural_share, 4),
            pass_rate_shift_pp=pass_rate_shift_pp,
            horizon=horizon,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    log_audit(user, "scenario_run", "model3/scenarios", {
        "owner": user.get("username"),
        "assumptions": payload.get("assumptions"),
        "persisted": False,
        "official_forecast": False,
    })
    return payload


@router.post("/scenarios")  # /model3/scenarios
def persist_scenario(
    body: ScenarioRequest,
    user: dict = Depends(rate_limit.per_user("scenario-run", 10, 60)),
    db: Session = Depends(get_db),
):
    try:
        payload = m3.simulate(**body.levers())
        saved = m3.persist_scenario(
            db,
            owner=user.get("username") or "unknown",
            name=body.name or "untitled-scenario",
            payload=payload,
        )
        log_audit(user, "scenario_run", "model3/scenarios", {
            "owner": user.get("username"),
            "assumptions": payload.get("assumptions"),
            "persisted": True,
            "official_forecast": False,
        })
        return {**payload, **saved}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
