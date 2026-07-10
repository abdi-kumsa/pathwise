from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from services import salary_service, escape_route_service
from schemas.salary import (
    SalaryRequest,
    SalaryPrediction,
    SalaryForecastResponse,
)
from schemas.escape_route import (
    EscapeRouteRequest,
    EscapeRouteResponse,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/salary-forecast", response_model=SalaryForecastResponse)
def get_salary_forecast():
    """Per-program average and median salary for all 12 programmes."""
    try:
        return salary_service.get_program_salary_breakdown()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/salary-predict", response_model=SalaryPrediction)
def predict_salary(profile: SalaryRequest):
    """Predict early-career salary for a student profile using XGBoost."""
    try:
        return salary_service.predict_student_salary(profile.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/escape-routes", response_model=EscapeRouteResponse)
def post_escape_routes(profile: EscapeRouteRequest):
    """
    Personalised escape route map for a specific student profile.
    Simulates the student across all 12 programmes using the placement
    model and returns the top alternatives ranked by placement probability.
    """
    try:
        data = profile.model_dump()
        top_n = data.pop("top_n", 5)
        return escape_route_service.get_escape_routes(data, top_n=top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/escape-routes", response_model=EscapeRouteResponse)
def get_escape_routes(
    program: str = Query(..., description="Programme name, e.g. 'Certificate Data Analytics'"),
    top_n: Optional[int] = Query(5, ge=1, le=11),
):
    """
    Aggregate escape route map for the median student in a given programme.
    Useful for advisory dashboards that don't have a specific student profile.
    """
    try:
        return escape_route_service.get_program_escape_routes(program, top_n=top_n)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
