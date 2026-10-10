"""M2.C5 — skills demand and shortage index, mapped onto the MoE programme list."""
from __future__ import annotations

from ml.model2.forecast import forecast_skills

_PROGRAM_BY_FIELD = {
    "Engineering & Technology": "BSc Civil Engineering",
    "Natural & Computational Sciences": "BSc Computer Science",
    "Medicine & Health Sciences": "MD Medicine",
    "Agriculture & Life Sciences": "BSc Agriculture",
    "Business & Economics": "BA Accounting",
    "Social Sciences & Humanities": "BA Sociology",
    "Law": "LLB Law",
    "Education": "BEd Education",
}


def skills_shortage(horizon: int = 3):
    out = forecast_skills(horizon)
    out["program"] = out["field"].map(_PROGRAM_BY_FIELD)
    if "skill_oversupply_index" in out.columns:
        out["net_pressure"] = (
            out["skill_shortages"].astype(float) - out["skill_oversupply_index"].fillna(0).astype(float)
        )
    else:
        out["net_pressure"] = out["skill_shortages"].astype(float)
    return out
