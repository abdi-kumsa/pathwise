"""Model 2 — labour-market trend prediction."""
from .forecast import DIMENSIONS, TARGETS, forecast_all
from .formal_informal import CAVEAT as ABSORPTION_CAVEAT
from .formal_informal import forecast_absorption
from .skills import skills_shortage
from .structural_breaks import annotate, apply_step

__all__ = [
    "DIMENSIONS",
    "TARGETS",
    "forecast_all",
    "forecast_absorption",
    "skills_shortage",
    "annotate",
    "apply_step",
    "ABSORPTION_CAVEAT",
]
