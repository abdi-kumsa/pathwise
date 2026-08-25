from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from services import labour_market_service, mismatch_service
from services.auth_service import require_roles, ROLE_MOL, ROLE_MOE

# MoE also reads labour demand — it is the input to their investment decisions —
# so both ministries are admitted here. Education supply data is MoE-only.
router = APIRouter(
    prefix="/labour",
    tags=["Labour Market (MoL)"],
    dependencies=[Depends(require_roles(ROLE_MOL, ROLE_MOE))],
)


@router.get("/overview")
def get_overview():
    try:
        return labour_market_service.get_overview()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emerging")
def get_emerging(
    level: str = Query("family", pattern="^(family|title)$",
                       description="'family' for the 9 fields, 'title' for the 33 occupations"),
    top_n: int = Query(10, ge=1, le=33),
):
    """Occupations or fields ranked by demand growth, with their yearly series."""
    try:
        return labour_market_service.get_emerging(level=level, top_n=top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supply-demand")
def get_supply_demand():
    """Workforce shortfall per field — the signal with real between-field variance."""
    try:
        return labour_market_service.get_supply_demand_gap()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mismatch")
def get_mismatch(
    by: str = Query("overview", pattern="^(overview|field|program)$"),
):
    """Graduate-to-role fit: Matched / Overeducated / Undereducated.

    Every response carries `comparable: false` and a caveat — the distribution is
    near-uniform across fields in this dataset, so it describes the system as a
    whole rather than ranking fields against each other.
    """
    try:
        if by == "field":
            return mismatch_service.get_by_field()
        if by == "program":
            return mismatch_service.get_by_program()
        return mismatch_service.get_overview()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regional")
def get_regional(
    field: Optional[str] = Query(None, description="Narrow to one field of study"),
    top_n: int = Query(20, ge=1, le=50),
):
    try:
        return labour_market_service.get_regional_demand(field=field, top_n=top_n)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/occupation/{job_title}")
def get_occupation(job_title: str):
    try:
        return labour_market_service.get_occupation_detail(job_title)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
