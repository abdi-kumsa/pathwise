"""
M1.L1 — unconstrained student-demand forecast.

Demand is forecast by institution, campus, region, programme and academic year
(DOC1 line 5). The target is **applications**: what students apply for before
any eligibility, placement, quota or capacity rule. DOC1's two-layer design
puts those rules in Layer 2; forecasting actual enrolment here (as earlier
waves did) applied them twice, because observed enrolment has already passed
every real-world constraint.

Estimation is ml/forecasting.py: four candidates scored on a rolling-origin
backtest, the lowest-error candidate chosen per horizon, and a 90% interval
from that candidate's backtest residuals. Every row records which candidate
produced it.

This module does not apply policy or capacity caps — that is Layer 2.
"""
from __future__ import annotations

from typing import Iterable

import pandas as pd

from ml._memo import memo
from ml.forecasting import CANDIDATES, forecast

DIMENSIONS = ("institution", "campus", "region", "program", "academic_year")
SERIES_KEYS = ("institution", "campus", "region", "program")
TARGET_ID = "M1.applications"


@memo
def forecast_unconstrained(
    horizon: int = 3,
    origin_year: int | None = None,
) -> pd.DataFrame:
    """Forecast applications `horizon` academic years past the last observed year."""
    fc = forecast(TARGET_ID, horizon)
    if origin_year is not None and not fc.empty:
        latest = int(fc["year"].min()) - 1
        if int(origin_year) != latest:
            raise ValueError(
                f"origin_year {origin_year} is not supported; forecasts start from the "
                f"last observed year ({latest}). Use ml.forecasting.backtest for "
                "historical origins."
            )
    if fc.empty:
        return fc
    out = fc.rename(columns={"year": "academic_year", "point": "unconstrained_demand"})
    keep = [
        *SERIES_KEYS, "field", "band", "academic_year", "horizon_step",
        "unconstrained_demand", *CANDIDATES, "selected_model",
        "interval_low", "interval_high", "interval_level", "last_observed",
    ]
    out = out[[c for c in keep if c in out.columns]].copy()
    for col in ("unconstrained_demand", "interval_low", "interval_high", *CANDIDATES):
        out[col] = out[col].round(1)
    return out.reset_index(drop=True)


def group_forecast(
    df: pd.DataFrame,
    dimensions: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Aggregate an unconstrained forecast to any of the five DOC1 dimensions."""
    dims = [d for d in (dimensions or DIMENSIONS) if d in df.columns]
    if not dims:
        dims = ["academic_year"]
    numeric = [
        c for c in ("unconstrained_demand", *CANDIDATES, "interval_low", "interval_high")
        if c in df.columns
    ]
    out = df.groupby(dims, as_index=False)[numeric].sum()
    out["selected_model"] = "aggregated"
    # Summed per-series bounds are wider than a true aggregate interval (the
    # series errors are not perfectly correlated). Labelled so nobody reads
    # them as a 90% interval for the total.
    out["interval_note"] = "sum of per-series 90% bounds — conservative for the aggregate"
    return out
