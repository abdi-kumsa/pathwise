"""
M1.L1 — unconstrained student-demand forecast.

Enrollment is forecast by institution, campus, region, programme and academic
year (DOC1 line 5). Two estimators are always produced:

  * seasonal_naive — last observed enrollment carried forward
  * ols_lags — LinearRegression on lag-1, lag-2, 3-year rolling mean and
    applications, trained with a chronological split (no random shuffle)

The selected figure is ols_lags when at least four history years are present,
otherwise seasonal_naive. Prediction intervals are residual RMSE × 1.96.

This module does not apply policy or capacity caps — that is Layer 2.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from ml.features.model1.assemble import assemble_panel

DIMENSIONS = ("institution", "campus", "region", "program", "academic_year")
SERIES_KEYS = ("institution", "campus", "region", "program")
_LAG_FEATURES = (
    "enrollment_lag_1y",
    "enrollment_lag_2y",
    "enrollment_rolling_3y_avg",
    "applications_count",
)


def _history() -> pd.DataFrame:
    panel = assemble_panel()
    panel = panel.rename(columns={"year": "academic_year"})
    return panel.sort_values(list(SERIES_KEYS) + ["academic_year"])


def _fit_ols(hist: pd.DataFrame) -> tuple[LinearRegression | None, float]:
    work = hist.dropna(subset=["program_enrollment_count", *_LAG_FEATURES])
    if len(work) < 4:
        return None, float("nan")
    split = max(3, len(work) - 2)
    train, test = work.iloc[:split], work.iloc[split:]
    model = LinearRegression()
    model.fit(train[list(_LAG_FEATURES)], train["program_enrollment_count"])
    if len(test):
        pred = model.predict(test[list(_LAG_FEATURES)])
        rmse = float(np.sqrt(np.mean((test["program_enrollment_count"] - pred) ** 2)))
    else:
        fitted = model.predict(train[list(_LAG_FEATURES)])
        rmse = float(np.sqrt(np.mean((train["program_enrollment_count"] - fitted) ** 2)))
    return model, rmse


def _naive_interval(hist: pd.DataFrame) -> float:
    y = hist["program_enrollment_count"].astype(float)
    if len(y) < 2:
        return max(float(y.std() if len(y) else 20.0), 8.0)
    diffs = y.diff().dropna()
    return max(float(diffs.std()) if len(diffs) else 8.0, 8.0)


def _project_features(last: pd.Series, horizon_year: int) -> pd.Series:
    """Carry the last observed lag features forward one or more years."""
    feat = last.copy()
    feat["academic_year"] = horizon_year
    lag1 = float(last["program_enrollment_count"])
    lag2 = float(last["enrollment_lag_1y"]) if pd.notna(last.get("enrollment_lag_1y")) else lag1
    feat["enrollment_lag_1y"] = lag1
    feat["enrollment_lag_2y"] = lag2
    roll = last.get("enrollment_rolling_3y_avg")
    feat["enrollment_rolling_3y_avg"] = float(roll) if pd.notna(roll) else lag1
    apps = last.get("applications_count")
    feat["applications_count"] = float(apps) if pd.notna(apps) else lag1 * 2.2
    return feat


def forecast_unconstrained(
    horizon: int = 3,
    origin_year: int | None = None,
) -> pd.DataFrame:
    """Forecast `horizon` academic years past the last observed year."""
    hist = _history()
    origin = int(origin_year or hist["academic_year"].max())
    rows: list[dict] = []

    for keys, series in hist.groupby(list(SERIES_KEYS), sort=False):
        series = series[series["academic_year"] <= origin]
        if series.empty:
            continue
        last = series.iloc[-1]
        naive_sd = _naive_interval(series)
        ols, ols_rmse = _fit_ols(series)
        interval_ols = ols_rmse if ols is not None and np.isfinite(ols_rmse) else naive_sd
        selected = "ols_lags" if ols is not None else "seasonal_naive"
        last_y = float(last["program_enrollment_count"])

        for step in range(1, horizon + 1):
            year = origin + step
            feat = _project_features(last, year)
            naive = last_y
            if ols is not None:
                X = feat[list(_LAG_FEATURES)].to_frame().T
                ols_hat = float(ols.predict(X)[0])
            else:
                ols_hat = naive
            chosen = ols_hat if selected == "ols_lags" else naive
            half = 1.96 * (interval_ols if selected == "ols_lags" else naive_sd)
            rows.append({
                "institution": last["institution"],
                "campus": last["campus"],
                "region": last["region"],
                "program": last["program"],
                "field": last.get("field"),
                "band": last.get("band"),
                "academic_year": year,
                "horizon_step": step,
                "unconstrained_demand": max(0.0, round(chosen, 1)),
                "seasonal_naive": max(0.0, round(naive, 1)),
                "ols_lags": max(0.0, round(ols_hat, 1)),
                "selected_model": selected,
                "interval_low": max(0.0, round(chosen - half, 1)),
                "interval_high": round(chosen + half, 1),
            })
            last = feat
            last["program_enrollment_count"] = chosen
            last_y = chosen

    return pd.DataFrame(rows)


def group_forecast(
    df: pd.DataFrame,
    dimensions: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Aggregate an unconstrained forecast to any of the five DOC1 dimensions."""
    dims = [d for d in (dimensions or DIMENSIONS) if d in df.columns]
    if not dims:
        dims = ["academic_year"]
    numeric = [
        "unconstrained_demand", "seasonal_naive", "ols_lags",
        "interval_low", "interval_high",
    ]
    out = df.groupby(dims, as_index=False)[numeric].sum()
    out["selected_model"] = "aggregated"
    return out
