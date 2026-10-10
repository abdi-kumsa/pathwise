"""
M1.L1 estimator comparison on a chronological holdout.

DOC1 step 4 asks for more than one model. Layer 1 always produces
seasonal-naive and OLS-on-lags; this module scores them on the last two
observed years of each HEI × programme series (no random split).

The US LSTM / Prophet artefacts remain on the old enrollment path. They are
not Ethiopia models and are not mixed into these scores.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from ml.features.model1.assemble import assemble_panel

_LAGS = (
    "enrollment_lag_1y",
    "enrollment_lag_2y",
    "enrollment_rolling_3y_avg",
    "applications_count",
)
OUT = Path(__file__).resolve().parents[1] / "models" / "model1_layer1_comparison.json"


def compare_estimators() -> dict:
    panel = assemble_panel().sort_values(
        ["institution", "campus", "program", "year"]
    )
    naive_sq, ols_sq, mean_sq, n = [], [], [], 0
    naive_abs, ols_abs, mean_abs = [], [], []
    keys = ["institution", "campus", "program"]
    ycol = "program_enrollment_count"
    for _, series in panel.groupby(keys, sort=False):
        work = series.dropna(subset=[ycol, *_LAGS])
        if len(work) < 6:
            continue
        train, test = work.iloc[:-2], work.iloc[-2:]
        y_test = test[ycol]
        naive = train[ycol].iloc[-1]
        hist_mean = float(train[ycol].mean())
        naive_err = y_test - naive
        mean_err = y_test - hist_mean
        naive_sq.extend(naive_err ** 2)
        naive_abs.extend(naive_err.abs())
        mean_sq.extend(mean_err ** 2)
        mean_abs.extend(mean_err.abs())
        model = LinearRegression()
        model.fit(train[list(_LAGS)], train[ycol])
        pred = model.predict(test[list(_LAGS)])
        ols_err = y_test - pred
        ols_sq.extend(ols_err ** 2)
        ols_abs.extend(ols_err.abs())
        n += len(test)

    def _score(sq, abs_err):
        if not sq:
            return {"rmse": None, "mae": None}
        return {
            "rmse": round(float(np.sqrt(np.mean(sq))), 2),
            "mae": round(float(np.mean(abs_err)), 2),
        }

    result = {
        "n_holdout_rows": n,
        "split": "chronological last-2-years per series",
        "target": ycol,
        "estimators": {
            "seasonal_naive": _score(naive_sq, naive_abs),
            "historical_mean": _score(mean_sq, mean_abs),
            "ols_lags": _score(ols_sq, ols_abs),
        },
        "selected_for_request_path": "ols_lags if a series has 4+ history years, else seasonal_naive",
        "not_compared": [
            "US LSTM (ml/models/enrollment_lstm.keras) — univariate US enrollment path",
            "US Prophet (ml/models/demand_prophet.pkl) — US labour-demand path",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
