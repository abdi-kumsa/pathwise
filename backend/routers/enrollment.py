import time
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from services import enrollment_service
from services.auth_service import (
    require_roles, ROLE_STUDENT, ROLE_MOE, ROLE_UNIVERSITY,
)
from schemas.enrollment import (
    EnrollmentSummary,
    EnrollmentForecastResponse,
    AdmissionRisk,
    PlacementByStream,
    StudentProfile,
    PlacementPrediction,
    SkillRecommendationsResponse,
    SkillRoadmapRequest,
    SkillRoadmapResponse,
)

# Students use the evaluator and roadmap; MoE and universities use the
# institutional forecasts. MoL has no enrolment-planning remit, so it is excluded.
router = APIRouter(
    prefix="/enrollment",
    tags=["Enrollment Intelligence"],
    dependencies=[Depends(require_roles(ROLE_STUDENT, ROLE_MOE, ROLE_UNIVERSITY))],
)


@router.get("/summary", response_model=EnrollmentSummary)
def get_enrollment_summary():
    try:
        return enrollment_service.get_enrollment_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast", response_model=EnrollmentForecastResponse)
def get_enrollment_forecast(
    program: str = Query(..., description="Program name, e.g. 'MS Data Science'"),
    years: int = Query(3, description="Number of future years to forecast"),
):
    try:
        return enrollment_service.get_enrollment_forecast(program=program, n_years=years)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admission-risk", response_model=List[AdmissionRisk])
def get_admission_risk(limit: int = Query(10, description="Max number of programmes to return")):
    try:
        return enrollment_service.get_admission_risk(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/placement-by-stream", response_model=List[PlacementByStream])
def get_placement_by_stream():
    try:
        return enrollment_service.get_placement_by_stream()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict-placement", response_model=PlacementPrediction)
def predict_placement(profile: StudentProfile):
    """Run XGBoost placement prediction and log the result for drift monitoring."""
    t0 = time.monotonic()
    try:
        result = enrollment_service.predict_student_placement(profile.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    latency_ms = (time.monotonic() - t0) * 1000

    # Log asynchronously — a monitoring failure must never break the response
    try:
        from services import monitoring_service
        monitoring_service.log_prediction(profile.model_dump(), result, latency_ms)
    except Exception:
        pass

    return result


@router.get("/skill-recommendations", response_model=SkillRecommendationsResponse)
def get_skill_recommendations(student_id: Optional[int] = Query(None)):
    try:
        return enrollment_service.get_skill_recommendations(student_id=student_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skill-roadmap", response_model=SkillRoadmapResponse)
def get_skill_roadmap(profile: SkillRoadmapRequest):
    """
    Personalised skill roadmap: runs the placement model with each feature
    improved to compute the actual probability gain per skill, then ranks
    recommendations by that gain.
    """
    try:
        return enrollment_service.get_personalised_skill_roadmap(profile.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
