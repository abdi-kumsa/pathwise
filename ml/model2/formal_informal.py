"""
M2.R2 — formal / informal / self-employment / underemployment absorption.

A distinct output, not a vacancy column. Job-board counts undercount absorption
(DOC1 line 191). Shares sum to 1.

Method: each component keeps its last observed ratio to total employment in
that region × sector, and is scaled by the Model 2 employment forecast for the
same cell. Labour-force structure moves slowly, so holding the ratios is the
baseline; the employment forecast carries the level. (Earlier waves carried
every count forward unchanged, so absorption never moved with employment.)
"""
from __future__ import annotations

import pandas as pd

from ml.features.model2 import c1_labour, c3_formal_informal
from ml.model2.forecast import forecast_employment

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


def _shares(counts: dict) -> dict:
    total = sum(counts.values()) or 1.0
    names = ["formal", "informal", "self_employment", "underemployment"]
    raw = [counts.get(c, 0) / total for c in COUNTS]
    bps = [int(round(v * 10000)) for v in raw]
    bps[-1] += 10000 - sum(bps)
    return {k: bps[i] / 10000 for i, k in enumerate(names)}


def forecast_absorption(horizon: int = 3) -> pd.DataFrame:
    hist = c3_formal_informal.frame()
    labour = c1_labour.frame()
    if hist.empty or labour.empty:
        return pd.DataFrame()
    origin = int(hist["year"].max())
    now = hist[hist["year"] == origin].merge(
        labour[labour["year"] == origin][["region", "sector", "employment_level"]],
        on=["region", "sector"], how="left",
    )
    ratios = {}
    for r in now.itertuples(index=False):
        emp = float(r.employment_level or 0)
        ratios[(r.region, r.sector)] = {
            col: (float(getattr(r, col)) / emp if emp else 0.0)
            for col in COUNTS if hasattr(r, col)
        }
    emp_fc = forecast_employment(horizon)
    rows = []
    for r in emp_fc.itertuples(index=False):
        ratio = ratios.get((r.region, r.sector))
        if not ratio:
            continue
        counts = {col: ratio[col] * float(r.employment_demand) for col in ratio}
        share = _shares(counts)
        rows.append({
            "region": r.region,
            "sector": r.sector,
            "period": int(r.period),
            "horizon_step": int(r.horizon_step),
            **{col: round(counts.get(col, 0.0), 1) for col in COUNTS},
            "share_formal": share["formal"],
            "share_informal": share["informal"],
            "share_self_employment": share["self_employment"],
            "share_underemployment": share["underemployment"],
            "employment_forecast": float(r.employment_demand),
            "method": "last observed component ratio × Model 2 employment forecast",
            "source": "labour_force_structure",
            "not_from_job_board": True,
        })
    return pd.DataFrame(rows)
