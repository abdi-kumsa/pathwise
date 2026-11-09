"""
Drift monitoring for the Ethiopia Model 1 / Model 2 request path (W.ADM.03).

Two signals per forecast target, both computed from data the platform already
holds, so they work today and keep working when official series replace the
simulated parquets:

* Input drift — population stability index (PSI) of the year-on-year change
  (the pooled model's `latest_change` input) in the latest year, against the
  reference years. It is scale-free, so an upward trend in levels is not read
  as drift. The other input, distance from the series' running mean, is not
  tested: in a trending series it rises over time by construction, so its
  PSI would always "shift". Targets with fewer than 20 series in the latest
  year report "insufficient data" rather than a PSI from a handful of points.
* Error drift — the selected candidate's backtest error for the latest origin
  against its average over earlier origins. A model that was fine and has
  started missing shows up here first.

Thresholds follow common practice: PSI < 0.1 stable, 0.1–0.25 watch, > 0.25
shift; an error ratio above 1.5 is flagged.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ml._memo import memo
from ml.forecasting import TARGETS, backtest, evaluation, pooled_pairs

DRIFT_INPUTS = ("latest_change",)

PSI_WATCH = 0.10
PSI_ALERT = 0.25
ERROR_RATIO_ALERT = 1.5
REFERENCE_GAP = 3          # reference = target years up to latest − 3


def psi(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float | None:
    reference = np.asarray(reference, dtype=float)
    current = np.asarray(current, dtype=float)
    reference = reference[np.isfinite(reference)]
    current = current[np.isfinite(current)]
    if len(reference) < 40 or len(current) < 20:
        return None
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return None
    edges[0], edges[-1] = -np.inf, np.inf
    ref = np.histogram(reference, edges)[0] / len(reference)
    cur = np.histogram(current, edges)[0] / len(current)
    ref, cur = np.clip(ref, 1e-4, None), np.clip(cur, 1e-4, None)
    return round(float(np.sum((cur - ref) * np.log(cur / ref))), 4)


def _band(value: float | None) -> str:
    if value is None:
        return "insufficient data"
    if value > PSI_ALERT:
        return "shift"
    if value > PSI_WATCH:
        return "watch"
    return "stable"


@memo
def target_drift(target_id: str) -> dict:
    pairs = pooled_pairs(target_id, horizon=1)
    if pairs.empty:
        return {"target": target_id, "alert": False, "inputs": [], "error": None}
    latest = int(pairs["target_year"].max())
    ref = pairs[pairs["target_year"] <= latest - REFERENCE_GAP]
    cur = pairs[pairs["target_year"] == latest]
    inputs = []
    for f in DRIFT_INPUTS:
        value = psi(ref[f].to_numpy(), cur[f].to_numpy())
        inputs.append({"feature": f, "psi": value, "status": _band(value)})

    ev = evaluation(target_id)
    selected = ev["selected"].get(1, "seasonal_naive")
    bt = backtest(target_id)
    h1 = bt[(bt["horizon"] == 1) & (bt["candidate"] == selected)]
    error = None
    if not h1.empty:
        by_origin = h1.assign(sq=(h1["actual"] - h1["pred"]) ** 2).groupby("origin")["sq"].mean() ** 0.5
        last_origin = int(by_origin.index.max())
        earlier = by_origin.drop(index=last_origin)
        ratio = float(by_origin[last_origin] / earlier.mean()) if len(earlier) and earlier.mean() else None
        error = {
            "selected_model": selected,
            "latest_origin": last_origin,
            "latest_rmse": round(float(by_origin[last_origin]), 4),
            "earlier_mean_rmse": round(float(earlier.mean()), 4) if len(earlier) else None,
            "ratio": round(ratio, 3) if ratio is not None else None,
            "status": "degraded" if ratio is not None and ratio > ERROR_RATIO_ALERT else "stable",
        }
    alert = any(i["status"] == "shift" for i in inputs) or bool(error and error["status"] == "degraded")
    return {
        "target": target_id,
        "label": TARGETS[target_id].label,
        "reference_years": f"target years ≤ {latest - REFERENCE_GAP}",
        "current_year": latest,
        "inputs": inputs,
        "error": error,
        "alert": alert,
        "thresholds": {"psi_watch": PSI_WATCH, "psi_alert": PSI_ALERT,
                       "error_ratio_alert": ERROR_RATIO_ALERT},
    }


def ethiopia_drift() -> dict:
    targets = {tid: target_drift(tid) for tid in TARGETS}
    alerts = [tid for tid, d in targets.items() if d["alert"]]
    return {
        "targets": targets,
        "alert": bool(alerts),
        "alerting_targets": alerts,
        "recommendation": (
            f"Review {', '.join(alerts)}: inputs have shifted or recent errors have grown. "
            "Re-run the model comparison (POST /api/methodology/model-comparison)."
            if alerts else
            "Ethiopia forecast inputs and backtest errors are within tolerance."
        ),
    }


def as_frame(report: dict) -> pd.DataFrame:
    rows = []
    for tid, d in report["targets"].items():
        for i in d["inputs"]:
            rows.append({"target": tid, **i})
    return pd.DataFrame(rows)
