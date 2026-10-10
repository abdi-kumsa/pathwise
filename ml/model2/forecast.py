"""
M2 — multi-target labour-market forecast.

Produces the five DOC1 targets (employment demand, employment growth, vacancies,
occupational demand, skill shortages) by sector, occupation, region and period.
Estimators: seasonal-naive and OLS on lags, chronological split. Industrial-park
and mega-project steps are applied after the smooth forecast (M2.R1).
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from ml.features.model2 import c1_labour, c4_vacancies, c5_skills
from ml.model2.structural_breaks import apply_step

DIMENSIONS = ("sector", "occupation", "region", "period")
OCCUPATIONAL_DEMAND_METHOD = (
    "vacancy × occupation share of the region's vacancy mix — "
    "not a copy of the vacancy point"
)
TARGETS = (
    "employment_demand",
    "employment_growth",
    "vacancies",
    "occupational_demand",
    "skill_shortages",
)


def _fit_project(series: pd.DataFrame, ycol: str, lags: tuple[str, ...], horizon: int, origin: int) -> list[dict]:
    work = series.dropna(subset=[ycol]).sort_values("year")
    if work.empty:
        return []
    last = work.iloc[-1]
    last_y = float(last[ycol])
    lag_ok = [c for c in lags if c in work.columns]
    usable = work.dropna(subset=[ycol, *lag_ok]) if lag_ok else work
    model = None
    rmse = float("nan")
    if lag_ok and len(usable) >= 4:
        split = max(3, len(usable) - 2)
        train, test = usable.iloc[:split], usable.iloc[split:]
        model = LinearRegression()
        model.fit(train[lag_ok], train[ycol])
        if len(test):
            pred = model.predict(test[lag_ok])
            rmse = float(np.sqrt(np.mean((test[ycol] - pred) ** 2)))
        else:
            fitted = model.predict(train[lag_ok])
            rmse = float(np.sqrt(np.mean((train[ycol] - fitted) ** 2)))
    diffs = work[ycol].astype(float).diff().dropna()
    naive_sd = max(float(diffs.std()) if len(diffs) else abs(last_y) * 0.08, 1.0)
    half_ols = 1.96 * (rmse if np.isfinite(rmse) and rmse > 0 else naive_sd)
    half_naive = 1.96 * naive_sd
    rows = []
    lag1 = last_y
    lag2 = float(last[lag_ok[0]]) if lag_ok and pd.notna(last.get(lag_ok[0])) else last_y
    for step in range(1, horizon + 1):
        year = origin + step
        naive = last_y
        ols_hat = naive
        if model is not None:
            feat = {lag_ok[0]: lag1}
            if len(lag_ok) > 1:
                feat[lag_ok[1]] = lag2
            X = pd.DataFrame([feat], columns=lag_ok)
            ols_hat = float(model.predict(X)[0])
        selected = "ols_lags" if model is not None else "seasonal_naive"
        chosen = ols_hat if selected == "ols_lags" else naive
        half = half_ols if selected == "ols_lags" else half_naive
        rows.append({
            "period": year,
            "horizon_step": step,
            "seasonal_naive": max(0.0, round(naive, 1)),
            "ols_lags": max(0.0, round(ols_hat, 1)),
            "selected_model": selected,
            "point": max(0.0, round(chosen, 1)),
            "interval_low": max(0.0, round(chosen - half, 1)),
            "interval_high": round(chosen + half, 1),
            "last_observed": last_y,
        })
        lag2, lag1, last_y = lag1, chosen, chosen
    return rows


def forecast_employment(horizon: int = 3) -> pd.DataFrame:
    hist = c1_labour.frame()
    origin = int(hist["year"].max())
    rows = []
    for (region, sector), series in hist.groupby(["region", "sector"], sort=False):
        projected = _fit_project(
            series, "employment_level",
            ("employment_lag_1y", "employment_lag_2y"),
            horizon, origin,
        )
        growth_hist = series.sort_values("year")
        last_growth = float(growth_hist["employment_growth_pct"].iloc[-1]) if "employment_growth_pct" in growth_hist else 0.0
        for item in projected:
            stepped, brk = apply_step(item["point"], region, item["period"])
            prev = item["last_observed"]
            growth = ((stepped / prev) - 1) * 100 if prev else last_growth
            rows.append({
                "region": region,
                "sector": sector,
                "occupation": None,
                "period": item["period"],
                "horizon_step": item["horizon_step"],
                "employment_demand": round(stepped, 1),
                "employment_growth": round(growth, 2),
                "vacancies": None,
                "occupational_demand": None,
                "skill_shortages": None,
                "selected_model": item["selected_model"],
                "interval_low": item["interval_low"],
                "interval_high": item["interval_high"],
                "break_applied": brk["break_applied"],
                "break_types": brk["break_types"],
                "grain": "region_sector",
            })
    return pd.DataFrame(rows)


def forecast_vacancies(horizon: int = 3) -> pd.DataFrame:
    hist = c4_vacancies.frame()
    origin = int(hist["year"].max())
    rows = []
    keys = [c for c in ("region", "occupation", "sector", "field") if c in hist.columns]
    group_keys = ["region", "occupation"]
    for _, series in hist.groupby(group_keys, sort=False):
        last = series.sort_values("year").iloc[-1]
        region_latest = hist[hist["year"] == origin]
        if "region" in region_latest.columns:
            region_latest = region_latest[region_latest["region"] == last["region"]]
        region_sum = float(region_latest["vacancy_count"].sum()) if not region_latest.empty else 0.0
        share = (float(last["vacancy_count"]) / region_sum) if region_sum else 0.0
        projected = _fit_project(
            series, "vacancy_count",
            ("vacancy_lag_1y", "vacancy_lag_2y"),
            horizon, origin,
        )
        for item in projected:
            rows.append({
                "region": last["region"],
                "sector": last.get("sector"),
                "occupation": last["occupation"],
                "field": last.get("field"),
                "period": item["period"],
                "horizon_step": item["horizon_step"],
                "employment_demand": None,
                "employment_growth": None,
                "vacancies": item["point"],
                "occupational_demand": round(float(item["point"]) * share, 1),
                "occupational_demand_method": OCCUPATIONAL_DEMAND_METHOD,
                "skill_shortages": None,
                "selected_model": item["selected_model"],
                "interval_low": item["interval_low"],
                "interval_high": item["interval_high"],
                "break_applied": False,
                "break_types": [],
                "grain": "region_occupation",
            })
    return pd.DataFrame(rows)


def forecast_skills(horizon: int = 3) -> pd.DataFrame:
    hist = c5_skills.frame()
    origin = int(hist["year"].max())
    rows = []
    for field, series in hist.groupby("field", sort=False):
        projected = _fit_project(
            series, "skill_shortage_index",
            ("skill_shortage_lag_1y", "skill_shortage_lag_2y"),
            horizon, origin,
        )
        last = series.sort_values("year").iloc[-1]
        for item in projected:
            rows.append({
                "region": None,
                "sector": None,
                "occupation": None,
                "field": field,
                "period": item["period"],
                "horizon_step": item["horizon_step"],
                "employment_demand": None,
                "employment_growth": None,
                "vacancies": None,
                "occupational_demand": None,
                "skill_shortages": round(float(item["point"]), 3),
                "technical_skill_demand": float(last.get("technical_skill_demand", 0) or 0),
                "digital_skill_demand": float(last.get("digital_skill_demand", 0) or 0),
                "soft_skill_demand": float(last.get("soft_skill_demand", 0) or 0),
                "emerging_skill_demand": float(last.get("emerging_skill_demand", 0) or 0),
                "skill_oversupply_index": float(last.get("skill_oversupply_index", 0) or 0),
                "selected_model": item["selected_model"],
                "interval_low": item["interval_low"],
                "interval_high": item["interval_high"],
                "break_applied": False,
                "break_types": [],
                "grain": "field",
            })
    return pd.DataFrame(rows)


def forecast_all(horizon: int = 3) -> pd.DataFrame:
    parts = [forecast_employment(horizon), forecast_vacancies(horizon), forecast_skills(horizon)]
    return pd.concat(parts, ignore_index=True)


def group_forecast(df: pd.DataFrame, dimensions: Iterable[str] | None) -> pd.DataFrame:
    dims = [d for d in (dimensions or DIMENSIONS) if d in df.columns]
    if not dims:
        dims = ["period"]
    numeric = [c for c in TARGETS if c in df.columns]
    return df.groupby(dims, dropna=False, as_index=False)[numeric].sum(min_count=1)
