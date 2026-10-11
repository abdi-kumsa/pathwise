"""
M2.R1 — structural-break handling.

Industrial-park openings and mega-project staffing jumps are step changes.
A smooth lag extrapolation on its own would miss them (DOC1 line 194).
This module annotates a region × year frame with the break and, when asked,
adds the step onto an employment forecast rather than folding it into a trend.
"""
from __future__ import annotations

import pandas as pd

from ml.features.model2 import c6_public, c7_fdi, c10_shocks


def park_openings() -> pd.DataFrame:
    """First year each park is operational — the step, not the subsequent level."""
    fdi = c7_fdi.frame()
    if fdi.empty or "industrial_park_operational_flag" not in fdi.columns:
        return pd.DataFrame(columns=["region", "year", "industrial_park", "expected_employment"])
    open_ = fdi[fdi["industrial_park_operational_flag"].astype(bool)]
    first = (
        open_.sort_values("year")
        .groupby(["region", "industrial_park"], as_index=False)
        .first()
    )
    keep = [c for c in ("region", "year", "industrial_park", "expected_employment") if c in first.columns]
    return first[keep]


def megaproject_jumps() -> pd.DataFrame:
    """Years where mega-project staffing at least doubles versus the prior year."""
    pub = c6_public.frame().sort_values(["region", "year"])
    if pub.empty or "megaproject_staffing_demand" not in pub.columns:
        return pd.DataFrame(columns=["region", "year", "megaproject_staffing_demand"])
    pub = pub.copy()
    pub["prev"] = pub.groupby("region")["megaproject_staffing_demand"].shift(1)
    jumped = pub[(pub["prev"].fillna(0) > 0) & (pub["megaproject_staffing_demand"] >= 2 * pub["prev"])]
    return jumped[["region", "year", "megaproject_staffing_demand"]]


def shock_years() -> pd.DataFrame:
    shocks = c10_shocks.frame()
    if shocks.empty or "external_shock_flag" not in shocks.columns:
        return pd.DataFrame(columns=["region", "year"])
    flagged = shocks[shocks["external_shock_flag"].astype(bool)]
    return flagged[["region", "year"]].drop_duplicates()


def annotate(region: str, year: int) -> dict:
    """Inspectable break record for one region-year."""
    parks = park_openings()
    mega = megaproject_jumps()
    shocks = shock_years()
    park_hit = parks[(parks["region"] == region) & (parks["year"] == year)]
    mega_hit = mega[(mega["region"] == region) & (mega["year"] == year)]
    shock_hit = shocks[(shocks["region"] == region) & (shocks["year"] == year)]
    kinds = []
    extra_jobs = 0.0
    if not park_hit.empty:
        kinds.append("industrial_park_opening")
        if "expected_employment" in park_hit.columns:
            extra_jobs += float(park_hit["expected_employment"].sum())
    if not mega_hit.empty:
        kinds.append("megaproject_start")
        extra_jobs += float(mega_hit["megaproject_staffing_demand"].sum())
    if not shock_hit.empty:
        kinds.append("external_shock")
    return {
        "region": region,
        "year": year,
        "break_applied": bool(kinds),
        "break_types": kinds,
        "step_employment": round(extra_jobs, 1),
    }


def apply_step(employment: float, region: str, year: int) -> tuple[float, dict]:
    """Add park/mega steps onto a smooth forecast. Shocks are flagged, not added."""
    info = annotate(region, year)
    types = info["break_types"]
    step = info["step_employment"] if "external_shock" not in types or len(types) > 1 else info["step_employment"]
    if "industrial_park_opening" in types or "megaproject_start" in types:
        return max(0.0, employment + step * 0.15), info
    return max(0.0, employment), info
