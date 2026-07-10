from pydantic import BaseModel, Field
from typing import List


class EscapeRouteRequest(BaseModel):
    gpa: float = Field(..., ge=0.0, le=4.0)
    internships: int = Field(..., ge=0)
    projects: int = Field(..., ge=0)
    communication_score: int = Field(..., ge=1, le=10)
    program: str
    top_n: int = Field(5, ge=1, le=11)


class EscapeRouteCard(BaseModel):
    program: str
    placement_probability: float
    avg_salary: float
    placement_rate: float
    rationale: str


class EscapeRouteResponse(BaseModel):
    current_program: str
    current_probability: float
    routes: List[EscapeRouteCard]
