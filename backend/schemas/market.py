from pydantic import BaseModel
from typing import List


class MarketOverview(BaseModel):
    total_companies: int
    total_placements: int
    avg_salary: float
    avg_time_to_hire: float
    top_role: str


class CompanyCount(BaseModel):
    company: str
    count: int


class RegionalHiring(BaseModel):
    location: str
    count: int


class JobInternshipRatio(BaseModel):
    job_count: int
    internship_count: int
    ratio: float


class SkillItem(BaseModel):
    skill: str
    demand_score: float
    curriculum_coverage: float
    gap_score: float


class SkillGapResponse(BaseModel):
    skills: List[SkillItem]
    top_gap_skill: str
    avg_gap_score: float


class HiringSource(BaseModel):
    source: str
    count: int


class DemandForecastPoint(BaseModel):
    month: str
    predicted_postings: int
    lower_bound: int
    upper_bound: int
