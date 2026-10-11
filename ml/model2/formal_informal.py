"""
M2.R2 — formal / informal / self-employment / underemployment absorption.

A distinct output, not a vacancy column. Job-board counts undercount absorption
(DOC1 line 191). Shares are forecast from the labour-force structure table and
forced to sum to 1.
"""
from __future__ import annotations

import pandas as pd

from ml.features.model2 import c3_formal_informal
from ml.model2.forecast import _fit_project

COUNTS = (
    "formal_wage_employment",
    "informal_employment",
    "self_employment",
    "underemployment",
)
CAVEAT = (
    "These shares come from the labour-force structure table, not from job-board "
    "vacancies. Postings undercount informal work, self-employment and "
    "underemployment. Simulated Ethiopian structure — not official ESS LFS figures."
)


def forecast_absorption(horizon: int = 3) -> pd.DataFrame:
    hist = c3_formal_informal.frame()
    origin = int(hist["year"].max())
    rows = []
    for (region, sector), series in hist.groupby(["region", "sector"], sort=False):
        projections = {
            col: _fit_project(series, col, (), horizon, origin)
            for col in COUNTS if col in series.columns
        }
        if not projections:
            continue
        n_steps = len(next(iter(projections.values())))
        for i in range(n_steps):
            counts = {col: projections[col][i]["point"] for col in projections}
            total = sum(counts.values()) or 1.0
            share_map = {
                "formal": counts.get("formal_wage_employment", 0) / total,
                "informal": counts.get("informal_employment", 0) / total,
                "self_employment": counts.get("self_employment", 0) / total,
                "underemployment": counts.get("underemployment", 0) / total,
            }
            ssum = sum(share_map.values()) or 1.0
            names = list(share_map)
            raw = [share_map[k] / ssum for k in names]
            bps = [int(round(v * 10000)) for v in raw]
            bps[-1] += 10000 - sum(bps)
            share_map = {k: bps[i] / 10000 for i, k in enumerate(names)}
            item = next(iter(projections.values()))[i]
            rows.append({
                "region": region,
                "sector": sector,
                "period": item["period"],
                "horizon_step": item["horizon_step"],
                "formal_wage_employment": round(counts.get("formal_wage_employment", 0), 1),
                "informal_employment": round(counts.get("informal_employment", 0), 1),
                "self_employment": round(counts.get("self_employment", 0), 1),
                "underemployment": round(counts.get("underemployment", 0), 1),
                "share_formal": share_map["formal"],
                "share_informal": share_map["informal"],
                "share_self_employment": share_map["self_employment"],
                "share_underemployment": share_map["underemployment"],
                "source": "labour_force_structure",
                "not_from_job_board": True,
            })
    return pd.DataFrame(rows)
