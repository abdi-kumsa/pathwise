from fastapi import APIRouter, Depends, HTTPException

from services import education_service
from services.auth_service import require_roles, ROLE_MOE

router = APIRouter(
    prefix="/education",
    tags=["Education Supply (MoE)"],
    dependencies=[Depends(require_roles(ROLE_MOE))],
)


@router.get("/overview")
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


@router.get("/investment-priority")
def get_investment_priority():
    """Fields ranked for investment, with the weight and contribution of each
    factor so the ranking can be audited rather than taken on trust."""
    try:
        return education_service.get_investment_priority()
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
