"""
M1.L1 estimator comparison (DOC1 step 4 / PROC.S4).

Thin wrapper over ml/forecasting.py: four candidates (seasonal-naive,
historical mean, drift, pooled ridge) on a rolling-origin backtest of the
Layer 1 target, applications by HEI × programme. The request path uses the
candidate this backtest selects at each horizon.

The US LSTM / Prophet artefacts are not Ethiopia models and are not scored.
"""
from __future__ import annotations

import json
from pathlib import Path

from ml.forecasting import comparison

OUT = Path(__file__).resolve().parents[1] / "models" / "model1_layer1_comparison.json"
NOT_COMPARED = [
    "US LSTM (ml/models/enrollment_lstm.keras) — univariate US enrollment path",
    "US Prophet (ml/models/demand_prophet.pkl) — US labour-demand path",
]


def compare_estimators(persist: bool = True) -> dict:
    result = {**comparison("M1.applications"), "not_compared": NOT_COMPARED}
    if persist:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
