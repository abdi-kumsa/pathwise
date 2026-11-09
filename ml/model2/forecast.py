"""
M2 — multi-target labour-market forecast.

Produces the five DOC1 targets (employment demand, employment growth, vacancies,
occupational demand, skill shortages) by sector, occupation, region and period.

Employment, vacancies and the skill-shortage index are forecast by
ml/forecasting.py: four candidates scored on a rolling-origin backtest, the
lowest-error candidate chosen per horizon, a 90% interval from its backtest
residuals. Employment growth and occupational demand are derived from those
forecasts, not estimated separately. Industrial-park and mega-project steps
are applied after the smooth forecast (M2.R1), and the interval moves with the
step.
"""
from __future__ import annotations

from typing import Iterable

import pandas as pd

from ml._memo import memo
from ml.features.model2 import c5_skills
from ml.forecasting import forecast as engine_forecast
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
_EMPTY = {
    "employment_demand": None, "employment_growth": None, "vacancies": None,
    "occupational_demand": None, "skill_shortages": None,
}


@memo
def forecast_employment(horizon: int = 3) -> pd.DataFrame:
    fc = engine_forecast("M2.employment_demand", horizon)
    rows = []
    for r in fc.itertuples(index=False):
        stepped, brk = apply_step(float(r.point), r.region, int(r.year))
        scale = stepped / r.point if r.point else 1.0
        prev = float(r.last_observed)
        growth = ((stepped / prev) - 1) * 100 if prev else None
        rows.append({
            "region": r.region,
            "sector": r.sector,
            "occupation": None,
            "period": int(r.year),
            "horizon_step": int(r.horizon_step),
            **_EMPTY,
            "employment_demand": round(stepped, 1),
            # Growth over the whole horizon from the last observed year, so it
            # is cumulative at steps 2 and 3, not annual.
            "employment_growth": round(growth, 2) if growth is not None else None,
            "selected_model": r.selected_model,
            "interval_low": round(float(r.interval_low) * scale, 1),
            "interval_high": round(float(r.interval_high) * scale, 1),
            "interval_level": r.interval_level,
            "break_applied": brk["break_applied"],
            "break_types": brk["break_types"],
            "grain": "region_sector",
        })
    return pd.DataFrame(rows)


@memo
def forecast_vacancies(horizon: int = 3) -> pd.DataFrame:
    fc = engine_forecast("M2.vacancies", horizon)
    if fc.empty:
        return fc
    # Each occupation's share of its region's vacancy mix in the last observed
    # year, so occupational demand is a distinct quantity from the vacancy point.
    origin = int(fc["year"].min()) - 1
    last = fc[fc["horizon_step"] == 1][["region", "occupation", "last_observed"]]
    region_sum = last.groupby("region")["last_observed"].transform("sum")
    share = (last["last_observed"] / region_sum.where(region_sum > 0)).fillna(0.0)
    share_map = dict(zip(zip(last["region"], last["occupation"]), share))
    rows = []
    for r in fc.itertuples(index=False):
        s = share_map.get((r.region, r.occupation), 0.0)
        rows.append({
            "region": r.region,
            "sector": getattr(r, "sector", None),
            "occupation": r.occupation,
            "field": getattr(r, "field", None),
            "period": int(r.year),
            "horizon_step": int(r.horizon_step),
            **_EMPTY,
            "vacancies": round(float(r.point), 1),
            "occupational_demand": round(float(r.point) * s, 1),
            "occupational_demand_method": OCCUPATIONAL_DEMAND_METHOD,
            "selected_model": r.selected_model,
            "interval_low": round(float(r.interval_low), 1),
            "interval_high": round(float(r.interval_high), 1),
            "interval_level": r.interval_level,
            "break_applied": False,
            "break_types": [],
            "grain": "region_occupation",
            "share_origin_year": origin,
        })
    return pd.DataFrame(rows)


@memo
def forecast_skills(horizon: int = 3) -> pd.DataFrame:
    fc = engine_forecast("M2.skill_shortages", horizon)
    hist = c5_skills.frame()
    latest = hist.sort_values("year").groupby("field").last() if not hist.empty else pd.DataFrame()
    rows = []
    for r in fc.itertuples(index=False):
        last = latest.loc[r.field] if r.field in latest.index else {}
        rows.append({
            "region": None,
            "sector": None,
            "occupation": None,
            "field": r.field,
            "period": int(r.year),
            "horizon_step": int(r.horizon_step),
            **_EMPTY,
            # The engine clips this index to [0, 1]; it is a share-like score.
            "skill_shortages": round(float(r.point), 3),
            "technical_skill_demand": float(last.get("technical_skill_demand", 0) or 0),
            "digital_skill_demand": float(last.get("digital_skill_demand", 0) or 0),
            "soft_skill_demand": float(last.get("soft_skill_demand", 0) or 0),
            "emerging_skill_demand": float(last.get("emerging_skill_demand", 0) or 0),
            "skill_oversupply_index": float(last.get("skill_oversupply_index", 0) or 0),
            "selected_model": r.selected_model,
            "interval_low": round(float(r.interval_low), 3),
            "interval_high": round(float(r.interval_high), 3),
            "interval_level": r.interval_level,
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
    out = df.groupby(dims, dropna=False, as_index=False)[numeric].sum(min_count=1)
    # Per-target 90% bounds, summed within each target's own rows: employment
    # and vacancy intervals live on different scales and must never be added
    # together. Summed bounds are conservative for the aggregate.
    if {"interval_low", "interval_high", "grain"} <= set(df.columns):
        for grain, col in (("region_sector", "employment_demand"),
                           ("region_occupation", "vacancies")):
            # Only where the target has every grouping dimension: employment rows
            # carry no occupation, so an occupation grain gets vacancy bounds only.
            part = df[df["grain"] == grain].dropna(subset=dims)
            if part.empty:
                continue
            bounds = (part.groupby(dims, dropna=False, as_index=False)
                          [["interval_low", "interval_high"]].sum(min_count=1)
                          .rename(columns={"interval_low": f"{col}_low",
                                           "interval_high": f"{col}_high"}))
            out = out.merge(bounds, on=dims, how="left")
    return out
