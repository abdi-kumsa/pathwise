from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from schemas.careers import JobOption, RecommendRequest, RecommendResponse
from services import career_service, labour_market_service
from services.auth_service import require_roles, ROLE_STUDENT

router = APIRouter(
    prefix="/careers",
    tags=["Careers (Student)"],
    dependencies=[Depends(require_roles(ROLE_STUDENT))],
)


@router.get("/jobs", response_model=List[JobOption])
def list_jobs():
    """All 33 occupations with their field — populates the target-job picker."""
    try:
        return career_service.list_jobs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[JobOption])
def search_jobs(
    q: str = Query(..., min_length=1, max_length=100, description="Partial occupation or field name"),
    limit: int = Query(10, ge=1, le=33),
):
    """Typeahead over occupations and fields. Prefix matches rank first."""
    try:
        return career_service.search(q, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_title}")
def get_job_detail(job_title: str):
    """Full labour-market profile for one occupation."""
    try:
        return labour_market_service.get_occupation_detail(job_title)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend", response_model=RecommendResponse)
def recommend_programs(body: RecommendRequest):
    """Recommend which department to join to reach a target job.

    The headline student feature. Returns every programme ranked, each with the
    per-factor breakdown that produced its score, so the student can see why.
    """
    try:
        return career_service.recommend(
            job_title = body.job_title,
            profile   = body.profile(),
            top_n     = body.top_n,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
