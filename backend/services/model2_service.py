"""
Model 2 service wrapper — labour-market forecasts for the MoL / MoE request path.

Rules and estimators stay in ml/model2 so they can be unit-tested without FastAPI.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ml.features.model2 import c4_vacancies, c6_public, c7_fdi, c9_demographics
from ml.model2.forecast import DIMENSIONS, TARGETS, forecast_all, forecast_vacancies, group_forecast
from ml.model2.formal_informal import CAVEAT as ABSORPTION_CAVEAT
from ml.model2.formal_informal import forecast_absorption
from ml.model2.skills import skills_shortage
from ml.model2.structural_breaks import park_openings

DIMENSIONS = DIMENSIONS
TARGETS = TARGETS


def as_records(df: pd.DataFrame | None) -> list[dict]:
    """JSON-safe records. Concatenated forecasts carry NaN in unused targets,
    and FastAPI's encoder rejects NaN."""
    if df is None or getattr(df, "empty", True):
        return []
    return json.loads(df.to_json(orient="records"))


def labour_forecast(horizon: int = 3, dimensions: Iterable[str] | None = None) -> pd.DataFrame:
    raw = forecast_all(horizon=horizon)
    if dimensions:
        return group_forecast(raw, dimensions)
    return raw


def absorption(horizon: int = 3) -> tuple[pd.DataFrame, str]:
    return forecast_absorption(horizon=horizon), ABSORPTION_CAVEAT


def skills(horizon: int = 3) -> pd.DataFrame:
    return skills_shortage(horizon=horizon)


def public_pipeline() -> pd.DataFrame:
    df = c6_public.frame().sort_values(["region", "year"])
    df["freeze"] = df.get("hiring_policy_state", "").astype(str).eq("freeze")
    return df


def fdi_pipeline() -> pd.DataFrame:
    fdi = c7_fdi.frame()
    openings = park_openings()
    if openings.empty:
        fdi["opening_year"] = False
        return fdi
    mark = openings[["region", "year", "industrial_park"]].assign(opening_year=True)
    out = fdi.merge(mark, on=["region", "year", "industrial_park"], how="left")
    out["opening_year"] = out["opening_year"].fillna(False).astype(bool)
    return out


def migration() -> dict:
    demo = c9_demographics.frame()
    if demo.empty:
        return {"available": False, "reason": "No migration series in the current Ethiopia tables.", "rows": []}
    latest = int(demo["year"].max())
    now = demo[demo["year"] == latest]
    return {
        "available": True,
        "as_of": latest,
        "rows": as_records(now),
        "series": as_records(demo.sort_values(["region", "year"])),
        "note": "Where a ministry file is missing, this degrades to available=false rather than inventing coverage.",
    }


def occupation(code: str) -> dict:
    vac = c4_vacancies.frame()
    if vac.empty:
        raise ValueError(f"Unknown occupation '{code}'")
    titles = set(vac["occupation"].astype(str))
    match = code
    if code not in titles:
        # Allow an ETH-### code from the jobs compat frame.
        try:
            from services._datasets import jobs
        except ImportError:
            from backend.services._datasets import jobs
        j = jobs()
        hit = j[j["soc_code"].astype(str) == code]
        if hit.empty:
            hit = j[j["job_title"].str.lower() == code.lower()]
        if hit.empty:
            raise ValueError(f"Unknown occupation '{code}'")
        match = str(hit["job_title"].iloc[0])
    sub = vac[vac["occupation"] == match]
    fc = forecast_vacancies(horizon=3)
    occ_fc = fc[fc["occupation"] == match] if "occupation" in fc.columns else fc.iloc[0:0]
    latest = int(sub["year"].max())
    last = sub[sub["year"] == latest]
    return {
        "code": code,
        "occupation": match,
        "sector": last["sector"].iloc[0] if "sector" in last.columns and len(last) else None,
        "field": last["field"].iloc[0] if "field" in last.columns and len(last) else None,
        "history": as_records(sub.sort_values("year")),
        "forecast": as_records(occ_fc),
    }
