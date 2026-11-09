"""
M2 estimator comparison (DOC1 step 4 / PROC.S4).

Thin wrapper over ml/forecasting.py for the three estimated Model 2 targets —
employment, vacancies, skill-shortage index — each with four candidates on a
rolling-origin backtest. Employment growth and occupational demand are
*derived* from those forecasts, so they are listed with their derivation
rather than scored as if they had their own estimator.

The US Prophet artefact is not an Ethiopia model and is not scored.
"""
from __future__ import annotations

import json
from pathlib import Path

from ml.forecasting import comparison
from ml.model2.forecast import OCCUPATIONAL_DEMAND_METHOD

OUT = Path(__file__).resolve().parents[1] / "models" / "model2_comparison.json"
NOT_COMPARED = ["US Prophet (ml/models/demand_prophet.pkl) — US labour-demand path"]
ESTIMATED = ("M2.employment_demand", "M2.vacancies", "M2.skill_shortages")
DERIVED = [
    {
        "id": "M2.employment_growth",
        "target": "employment_growth_pct",
        "derived_from": "M2.employment_demand",
        "method": "(forecast employment / last observed employment − 1) × 100",
    },
    {
        "id": "M2.occupational_demand",
        "target": "occupational_demand",
        "derived_from": "M2.vacancies",
        "method": OCCUPATIONAL_DEMAND_METHOD,
    },
]


def compare_estimators(persist: bool = True) -> dict:
    targets = [comparison(tid) for tid in ESTIMATED]
    head = targets[0]
    result = {
        **head,
        "targets": targets,
        "derived_targets": DERIVED,
        "occupational_demand_method": OCCUPATIONAL_DEMAND_METHOD,
        "not_compared": NOT_COMPARED,
    }
    if persist:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
