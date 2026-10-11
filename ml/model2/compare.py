"""
M2 estimator comparison on a chronological holdout.

DOC1 step 4 asks for more than one model. Each of the five forecast targets is
scored with seasonal-naive, historical-mean and OLS-on-lags on the last two
observed years of each series (no random split).

The US Prophet artefact remains on the old labour-demand path. It is not an
Ethiopia model and is not mixed into these scores.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LinearRegression

from ml.features.model2 import c1_labour, c4_vacancies, c5_skills

OUT = Path(__file__).resolve().parents[1] / "models" / "model2_comparison.json"


def _score_panel(panel, ycol, lags, keys, target_id) -> dict:
    naive_sq, ols_sq, mean_sq, n = [], [], [], 0
    naive_abs, ols_abs, mean_abs = [], [], []
    work_lags = [c for c in lags if c in panel.columns]
    if not work_lags or ycol not in panel.columns or panel.empty:
        return {
            "id": target_id,
            "target": ycol,
            "n_holdout_rows": 0,
            "estimators": {
                "seasonal_naive": {"rmse": None, "mae": None},
                "historical_mean": {"rmse": None, "mae": None},
                "ols_lags": {"rmse": None, "mae": None},
            },
        }
    group = [c for c in keys if c in panel.columns]
    for _, series in panel.groupby(group or [ycol], sort=False):
        work = series.dropna(subset=[ycol, *work_lags])
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
        model.fit(train[work_lags], train[ycol])
        pred = model.predict(test[work_lags])
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

    return {
        "id": target_id,
        "target": ycol,
        "n_holdout_rows": n,
        "split": "chronological last-2-years per series",
        "estimators": {
            "seasonal_naive": _score(naive_sq, naive_abs),
            "historical_mean": _score(mean_sq, mean_abs),
            "ols_lags": _score(ols_sq, ols_abs),
        },
        "selected_for_request_path": "ols_lags if a series has 4+ history years, else seasonal-naive",
    }


def _occupational_panel():
    vac = c4_vacancies.frame()
    if vac.empty or "vacancy_count" not in vac.columns:
        return vac
    out = vac.copy()
    keys = [c for c in ("region", "year") if c in out.columns]
    if keys:
        totals = out.groupby(keys)["vacancy_count"].transform("sum").replace(0, 1.0)
        out["occupational_demand"] = out["vacancy_count"] * (out["vacancy_count"] / totals)
    else:
        out["occupational_demand"] = out["vacancy_count"]
    return out


def compare_estimators() -> dict:
    employment = _score_panel(
        c1_labour.frame().sort_values(["region", "sector", "year"]),
        "employment_level",
        ("employment_lag_1y", "employment_lag_2y"),
        ["region", "sector"],
        "M2.employment_demand",
    )
    growth = _score_panel(
        c1_labour.frame().sort_values(["region", "sector", "year"]),
        "employment_growth_pct",
        ("employment_lag_1y", "employment_lag_2y"),
        ["region", "sector"],
        "M2.employment_growth",
    )
    vacancies = _score_panel(
        c4_vacancies.frame().sort_values(["region", "occupation", "year"]),
        "vacancy_count",
        ("vacancy_lag_1y", "vacancy_lag_2y"),
        ["region", "occupation"],
        "M2.vacancies",
    )
    occupational = _score_panel(
        _occupational_panel().sort_values(["region", "occupation", "year"]),
        "occupational_demand",
        ("vacancy_lag_1y", "vacancy_lag_2y"),
        ["region", "occupation"],
        "M2.occupational_demand",
    )
    skills = _score_panel(
        c5_skills.frame().sort_values(["field", "year"]),
        "skill_shortage_index",
        ("skill_shortage_lag_1y", "skill_shortage_lag_2y"),
        ["field"],
        "M2.skill_shortages",
    )
    result = {
        **employment,
        "id": "M2.employment_demand",
        "targets": [employment, growth, vacancies, occupational, skills],
        "not_compared": [
            "US Prophet (ml/models/demand_prophet.pkl) — US labour-demand path",
        ],
        "occupational_demand_method": (
            "vacancy × occupation share of the region's vacancy mix — "
            "not a copy of the vacancy point"
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
