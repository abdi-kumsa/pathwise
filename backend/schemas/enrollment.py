from pydantic import BaseModel
from typing import List, Optional


class EnrollmentSummary(BaseModel):
    total_students: int
    total_programs: int
    avg_placement_rate: float
    top_program: str
    enrollment_by_year: dict


class ForecastPoint(BaseModel):
    year: int
    predicted_count: int


class EnrollmentForecastResponse(BaseModel):
    program: str
    historical: List[ForecastPoint]
    forecast: List[ForecastPoint]


class AdmissionRisk(BaseModel):
    program: str
    risk_score: float
    recommended_intake: int
    trend: str


class PlacementByStream(BaseModel):
    program: str
    placement_rate: float
    avg_salary: float
    student_count: int


class StudentProfile(BaseModel):
    gpa: float
    internships: int
    projects: int
    communication_score: int
    program: str


class SHAPContribution(BaseModel):
    feature: str
    value: float
    shap: float


class PlacementPrediction(BaseModel):
    placement_probability: float
    prediction: str
    base_value: float
    shap_values: List[SHAPContribution]


class SkillRecommendation(BaseModel):
    skill: str
    priority: str
    reason: str


class SkillRecommendationsResponse(BaseModel):
    student_id: Optional[int]
    recommendations: List[SkillRecommendation]
    alternative_pathways: List[str]


class SkillRoadmapRequest(BaseModel):
    gpa: float
    internships: int
    projects: int
    communication_score: int
    program: str


class SkillRoadmapItem(BaseModel):
    skill: str
    action: str
    priority: str
    probability_gain: float
    reason: str


class SkillRoadmapResponse(BaseModel):
    current_probability: float
    program: str
    recommendations: List[SkillRoadmapItem]
    alternative_pathways: List[str]
