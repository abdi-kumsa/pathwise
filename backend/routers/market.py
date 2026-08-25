from fastapi import APIRouter, Depends, HTTPException
from typing import List

from services import market_service
from services.auth_service import (
    require_roles, ROLE_MOE, ROLE_MOL, ROLE_UNIVERSITY, ROLE_STUDENT,
)
from schemas.market import (
    MarketOverview,
    CompanyCount,
    RegionalHiring,
    JobInternshipRatio,
    SkillGapResponse,
    HiringSource,
    DemandForecastPoint,
)

# Market demand is background context for every role, so all four are admitted
# (ADMIN is implicit). It is no longer reachable unauthenticated.
router = APIRouter(
    prefix="/market",
    tags=["Market Demand"],
    dependencies=[Depends(require_roles(ROLE_MOE, ROLE_MOL, ROLE_UNIVERSITY, ROLE_STUDENT))],
)


@router.get("/overview", response_model=MarketOverview)
def get_market_overview():
    try:
        return market_service.get_market_overview()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-companies", response_model=List[CompanyCount])
def get_top_companies(n: int = 10):
    try:
        return market_service.get_top_companies(n=n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regional-hiring", response_model=List[RegionalHiring])
def get_regional_hiring():
    try:
        return market_service.get_regional_hiring()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job-internship-ratio", response_model=JobInternshipRatio)
def get_job_internship_ratio():
    try:
        return market_service.get_job_internship_ratio()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skill-gap", response_model=SkillGapResponse)
def get_skill_gap():
    try:
        return market_service.get_skill_gap()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hiring-sources", response_model=List[HiringSource])
def get_hiring_sources():
    try:
        return market_service.get_hiring_sources()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demand-forecast", response_model=List[DemandForecastPoint])
def get_demand_forecast(months: int = 12):
    try:
        return market_service.get_demand_forecast(months_ahead=months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
