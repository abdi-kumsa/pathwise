from pydantic import BaseModel, Field
from typing import List, Optional


class JobOption(BaseModel):
    job_title:  str
    job_family: str


class RecommendRequest(BaseModel):
    """Target occupation, plus an optional student profile.

    When the profile is present the recommender runs the XGBoost placement model
    per programme; when it is absent it falls back to historical placement rates,
    so the page works before the student has entered anything.

    Bounds mirror StudentProfile in schemas/enrollment.py — the same values reach
    the same model, so they must be validated identically.
    """
    job_title:           str = Field(..., min_length=1, max_length=150)
    gpa:                 Optional[float] = Field(None, ge=0.0, le=4.0)
    internships:         Optional[int]   = Field(None, ge=0, le=20)
    projects:            Optional[int]   = Field(None, ge=0, le=50)
    communication_score: Optional[int]   = Field(None, ge=1, le=10)
    top_n:               int = Field(5, ge=1, le=12)

    def profile(self) -> Optional[dict]:
        """The four model features, or None if the student supplied none of them.

        Partial profiles are treated as absent: feeding the model a default for
        an unanswered field would produce a confident-looking number the student
        never actually provided the inputs for.
        """
        fields = (self.gpa, self.internships, self.projects, self.communication_score)
        if any(f is None for f in fields):
            return None
        return {
            'gpa':                 self.gpa,
            'internships':         self.internships,
            'projects':            self.projects,
            'communication_score': self.communication_score,
        }


class FactorContribution(BaseModel):
    factor:       str
    weight:       float
    normalised:   float
    contribution: float


class ProgramRecommendation(BaseModel):
    rank:                   int
    program:                str
    field:                  str
    score:                  float
    is_direct_route:        bool
    why:                    str
    placement_probability:  float
    employment_rate_pct:    float
    median_salary:          float
    acceptance_rate_pct:    float
    net_price:              float
    roi_10yr:               float
    level:                  str
    factors:                List[FactorContribution]


class DemandPoint(BaseModel):
    year:     int
    openings: int


class MetroPoint(BaseModel):
    metro:    str
    openings: int


class DemandContext(BaseModel):
    total_openings:      int
    openings_cagr_pct:   float
    avg_growth_pct:      float
    avg_salary:          float
    supply_demand_ratio: float
    time_to_fill_days:   float
    remote_share_pct:    float
    outlook:             str
    series:              List[DemandPoint]
    top_metros:          List[MetroPoint]


class RecommendResponse(BaseModel):
    job_title:       str
    job_family:      str
    demand:          DemandContext
    recommendations: List[ProgramRecommendation]
    all_programs:    List[ProgramRecommendation]
    weights:         dict
    personalised:    bool
    method:          str
    dataset_label:   str
