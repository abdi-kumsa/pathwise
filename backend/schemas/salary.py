from pydantic import BaseModel, Field
from typing import List


class SalaryRequest(BaseModel):
    gpa: float = Field(..., ge=0.0, le=4.0)
    internships: int = Field(..., ge=0)
    projects: int = Field(..., ge=0)
    communication_score: int = Field(..., ge=1, le=10)
    program: str


class SalaryPrediction(BaseModel):
    predicted_salary: float
    confidence_low: float
    confidence_high: float
    program_avg_salary: float


class ProgramSalaryPoint(BaseModel):
    program: str
    avg_salary: float
    median_salary: float
    placement_rate: float
    student_count: int


class SalaryForecastResponse(BaseModel):
    programs: List[ProgramSalaryPoint]
    overall_avg_salary: float
    top_program: str
