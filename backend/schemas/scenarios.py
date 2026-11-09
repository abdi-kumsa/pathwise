"""
Scenario run bodies (W.MOE.04, W.ADM.05).

Bounded so a POST cannot carry nan, inf or 1e308 into the constraint layer.
The ranges match the GET query parameters and the policy-simulator sliders.
"""
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class ScenarioRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=120)
    quota_scale: float = Field(1.0, ge=0.25, le=3.0, allow_inf_nan=False)
    capacity_scale: float = Field(1.0, ge=0.25, le=3.0, allow_inf_nan=False)
    priority_field: Optional[str] = Field(None, max_length=120)
    priority_fields: Optional[List[str]] = Field(None, max_length=8)
    priority_boost: float = Field(1.25, ge=1.0, le=3.0, allow_inf_nan=False)
    natural_share: float = Field(0.70, ge=0.5, le=0.9, allow_inf_nan=False)
    social_share: Optional[float] = Field(None, ge=0.1, le=0.5, allow_inf_nan=False)
    pass_rate_shift_pp: float = Field(0.0, ge=-15.0, le=15.0, allow_inf_nan=False)
    horizon: int = Field(1, ge=1, le=5)

    @model_validator(mode="after")
    def _shares_sum_to_one(self):
        if self.social_share is not None and abs(self.natural_share + self.social_share - 1) > 1e-6:
            raise ValueError("natural_share and social_share must sum to 1")
        return self

    def levers(self) -> dict:
        fields = self.priority_fields or ([self.priority_field] if self.priority_field else None)
        return {
            "quota_scale": self.quota_scale,
            "capacity_scale": self.capacity_scale,
            "priority_fields": fields,
            "priority_boost": self.priority_boost,
            "natural_share": self.natural_share,
            "social_share": self.social_share if self.social_share is not None
                            else round(1.0 - self.natural_share, 4),
            "pass_rate_shift_pp": self.pass_rate_shift_pp,
            "horizon": self.horizon,
        }
