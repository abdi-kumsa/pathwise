from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.database import get_db
from schemas.scenarios import ScenarioRequest
from services import rate_limit
from services import alignment_service as m3
from services import education_service
from services.auth_service import ROLE_MOE, get_current_user, log_audit, require_roles

router = APIRouter(
    prefix="/education",
    tags=["Education Supply (MoE)"],
    dependencies=[Depends(require_roles(ROLE_MOE))],
)


@router.get("/overview")  # /education/overview
def get_overview():
    try:
        return education_service.get_overview()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/field-trends")
def get_field_trends():
    """Enrolment and applications per field per year — the supply trajectory."""
    try:
        return education_service.get_field_trends()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investment-quadrant")
def get_investment_quadrant():
    """Labour-demand growth against graduate-supply growth, per field.

    Fields are split at the median of each axis into Invest / Sustain /
    Oversupply risk / Review. This is the MoE centrepiece: it identifies where
    new capacity is justified because demand is outpacing the supply meant to
    serve it.
    """
    try:
        return education_service.get_investment_quadrant()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investment-priority")  # /education/investment-priority
def get_investment_priority():
    """Fields ranked for investment, with the weight and contribution of each
    factor so the ranking can be audited rather than taken on trust."""
    try:
        return education_service.get_investment_priority()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supply-demand-gap")  # /education/supply-demand-gap
def supply_demand_gap(horizon: int = Query(1, ge=1, le=5)):
    try:
        df = m3.gap(horizon=horizon, group=("field", "period"))
        return {"n": int(len(df)), "rows": m3.as_records(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policy-simulator")  # /education/policy-simulator
def policy_simulator(
    quota_scale: float = Query(1.0, ge=0.25, le=3.0),
    capacity_scale: float = Query(1.0, ge=0.25, le=3.0),
    priority_field: str | None = Query(None),
    natural_share: float = Query(0.70, ge=0.5, le=0.9),
    pass_rate_shift_pp: float = Query(0.0, ge=-15.0, le=15.0),
    horizon: int = Query(1, ge=1, le=5),
    user: dict = Depends(rate_limit.per_user("scenario-whatif", 60, 60)),
):
    """Unsaved what-if. Still a scenario run, so it is attributable (SCOPE.MOE.R3)."""
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    log_audit(user, "scenario_run", "policy-simulator", {
        "owner": user.get("username"),
        "assumptions": payload.get("assumptions"),
        "persisted": False,
        "official_forecast": False,
    })
    return payload


@router.post("/policy-simulator")  # /education/policy-simulator
def persist_policy_simulator(
    body: ScenarioRequest,
    user: dict = Depends(rate_limit.per_user("scenario-run", 10, 60)),
    db: Session = Depends(get_db),
):
    try:
        payload = m3.simulate(**body.levers())
        saved = m3.persist_scenario(
            db,
            owner=user.get("username") or "unknown",
            name=body.name or "policy-simulator",
            payload=payload,
        )
        log_audit(user, "scenario_run", "policy-simulator", {
            "owner": user.get("username"),
            "assumptions": payload.get("assumptions"),
            "official_forecast": False,
        })
        return {**payload, **saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demand-constrained-comparison")  # /education/demand-constrained-comparison
def demand_constrained_comparison(horizon: int = Query(3, ge=1, le=5)):
    try:
        return education_service.demand_constrained_comparison(horizon=horizon)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/institution-comparison")  # /education/institution-comparison
def institution_comparison(
    horizon: int = Query(1, ge=1, le=5),
    user: dict = Depends(get_current_user),
):
    try:
        payload = education_service.institution_comparison(horizon=horizon)
        log_audit(user, "institution_drilldown", "institution-comparison", {
            "n": payload.get("n"),
            "year": payload.get("year"),
        })
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policy-impact")  # /education/policy-impact
def policy_impact():
    try:
        return education_service.policy_impact()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regional-alignment")  # /education/regional-alignment
def regional_alignment(horizon: int = Query(1, ge=1, le=5)):
    try:
        df = m3.regional_alignment(horizon=horizon)
        return {"n": int(len(df)), "rows": m3.as_records(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/field/{field:path}")
def get_field_detail(field: str):
    """Detail for one field of study.

    Uses the `:path` converter because one field name contains a forward slash
    — "AI/ML Engineering". A client percent-encodes it as %2F, but the ASGI
    server decodes that back to a literal "/" before routing, so a plain
    `{field}` segment never matches and the request 404s. `:path` accepts the
    remainder of the URL, slash included.
    """
    try:
        return education_service.get_field_detail(field)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
