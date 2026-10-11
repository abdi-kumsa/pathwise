"""Join the ten Model 1 category frames onto the HEI × programme × year panel."""
from __future__ import annotations

import pandas as pd

from . import (
    c1_enrollment,
    c2_funnel,
    c3_exam,
    c4_quota,
    c5_demographics,
    c6_cohort,
    c7_outcomes,
    c8_institution,
    c9_finance,
    c10_macro,
)

FEATURE_MODULES = (
    c1_enrollment,
    c2_funnel,
    c3_exam,
    c4_quota,
    c5_demographics,
    c6_cohort,
    c7_outcomes,
    c8_institution,
    c9_finance,
    c10_macro,
)

_PANEL_KEYS = ["institution", "campus", "region", "program", "field", "year"]


def _merge(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
    keys = [c for c in _PANEL_KEYS if c in left.columns and c in right.columns]
    extra = [c for c in right.columns if c not in left.columns or c in keys]
    right = right[extra]
    return left.merge(right, on=keys, how="left")


def assemble_panel() -> pd.DataFrame:
    """Multivariate panel used by Layer 1. Grain: institution × campus × program × year."""
    panel = c1_enrollment.frame()
    panel = _merge(panel, c2_funnel.frame())
    panel = _merge(panel, c4_quota.frame())
    panel = _merge(panel, c6_cohort.frame())
    panel = _merge(panel, c7_outcomes.frame())
    panel = _merge(panel, c8_institution.frame())
    panel = _merge(panel, c9_finance.frame())
    panel = _merge(panel, c3_exam.frame())
    panel = _merge(panel, c5_demographics.frame())
    panel = _merge(panel, c10_macro.frame())
    return panel
