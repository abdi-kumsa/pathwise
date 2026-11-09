"""
M1.L2 service wrapper — unconstrained demand passed through the inspectable
policy/capacity rule engine.

Lives on the request path. The rules themselves stay in ml/model1/layer2_constraints.py
so they can be unit-tested without FastAPI.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ml.features.model1 import c2_funnel, c6_cohort
from ml.model1.layer1_demand import DIMENSIONS, forecast_unconstrained, group_forecast  # noqa: F401  (DIMENSIONS re-exported for routers/model1.py)
from ml.model1.layer2_constraints import apply_constraints, explain_rules


def unconstrained_demand(
    horizon: int = 3,
    dimensions: Iterable[str] | None = None,
) -> pd.DataFrame:
    raw = forecast_unconstrained(horizon=horizon)
    if dimensions:
        return group_forecast(raw, dimensions)
    return raw


def constrained_demand(
    horizon: int = 3,
    dimensions: Iterable[str] | None = None,
) -> pd.DataFrame:
    raw = apply_constraints(forecast_unconstrained(horizon=horizon))
    if not dimensions:
        return raw
    dims = [d for d in dimensions if d in raw.columns]
    numeric = [
        c for c in (
            "unconstrained_demand", "constrained_enrollment", "constraint_loss",
            "seasonal_naive", "historical_mean", "drift", "pooled_ridge",
            "interval_low", "interval_high",
        ) if c in raw.columns
    ]
    grouped = raw.groupby(dims, as_index=False)[numeric].sum()
    # Binding constraint of an aggregate is the mode among member rows.
    mode = (
        raw.groupby(dims)["binding_constraint"]
        .agg(lambda s: s.value_counts().index[0] if len(s) else "none")
        .reset_index()
    )
    return grouped.merge(mode, on=dims, how="left")


def constraint_explain() -> dict:
    return explain_rules()


def cohort_progression() -> pd.DataFrame:
    return c6_cohort.frame()


def admissions_funnel() -> pd.DataFrame:
    return c2_funnel.frame()


def graduate_outcomes() -> pd.DataFrame:
    from ml.features.model1 import c7_outcomes
    return c7_outcomes.frame()


def scope_to_institution(df: pd.DataFrame, institution: str | None) -> pd.DataFrame:
    """UNIVERSITY row scope — institution comes from the JWT, never a query."""
    if not institution or "institution" not in df.columns:
        return df
    return df[df["institution"] == institution].copy()
