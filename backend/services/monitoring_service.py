"""
Prediction monitoring service.

Logs every call to predict-placement to data/monitoring/predictions.jsonl
and computes drift relative to the training-time baseline probability.

Two public functions used by the rest of the backend:
  log_prediction(inputs, result, latency_ms) -- append one record
  get_drift_report(window)                   -- analyse recent predictions
  get_recent_predictions(n)                  -- tail the log for inspection
"""
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

_ROOT        = Path(__file__).resolve().parent.parent.parent
_MONITOR_DIR = _ROOT / "data" / "monitoring"
_LOG_FILE    = _MONITOR_DIR / "predictions.jsonl"
_M1_CMP      = _ROOT / "ml" / "models" / "model1_layer1_comparison.json"
_M2_CMP      = _ROOT / "ml" / "models" / "model2_comparison.json"

# ── Baseline ──────────────────────────────────────────────────────────────────
# Training-time mean placement probability across 2,400 training rows.
# XGBoost: accuracy 88.17 %, precision 88.17 %, recall 100 % → the model
# rarely predicts Not Placed; mean probability ≈ 0.88.
BASELINE_MEAN_PROB = 0.88

# Raise alert when |mean - baseline| exceeds this fraction
DRIFT_THRESHOLD = 0.10


# ── Internal ──────────────────────────────────────────────────────────────────

def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def _mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _ethiopia_metrics() -> dict:
    m1 = _read_json(_M1_CMP) or {}
    m2 = _read_json(_M2_CMP) or {}
    ethiopia = {
        "model1": _ethiopia_block(m1, "M1 enrollment"),
        "model2": _ethiopia_block(m2, "M2 employment"),
        "not_compared": sorted(set(
            list(m1.get("not_compared") or [])
            + list(m2.get("not_compared") or [])
        )),
    }
    naive = ethiopia["model1"].get("estimators", {}).get("seasonal_naive") or {}
    selected = ethiopia["model1"].get("selected") or ethiopia["model2"].get("selected") or {}
    headline = naive or selected
    return {
        "mae": headline.get("mae"),
        "rmse": headline.get("rmse"),
        "last_retrained": _mtime(_M1_CMP) or _mtime(_M2_CMP),
        "ethiopia": ethiopia,
        "us_models_not_compared": ethiopia["not_compared"],
    }


def _ethiopia_block(cmp: dict, label: str) -> dict:
    estimators = cmp.get("estimators") or {}
    selected_name = "ols_lags" if "ols_lags" in estimators else next(iter(estimators), None)
    selected = estimators.get(selected_name) or {}
    return {
        "label": label,
        "split": cmp.get("split"),
        "estimators": estimators,
        "selected_name": selected_name,
        "selected": selected,
        "mae": selected.get("mae"),
        "rmse": selected.get("rmse"),
        "not_compared": cmp.get("not_compared") or [],
    }


def _ensure_dir() -> None:
    _MONITOR_DIR.mkdir(parents=True, exist_ok=True)


# ── Public API ────────────────────────────────────────────────────────────────

def log_prediction(inputs: dict, result: dict, latency_ms: float) -> None:
    """Append one prediction record to predictions.jsonl.

    Always non-fatal — a write failure is logged as a warning and swallowed
    so it never breaks the HTTP response to the user.
    """
    _ensure_dir()
    record = {
        "ts":          time.time(),
        "inputs":      inputs,
        "probability": result.get("placement_probability"),
        "prediction":  result.get("prediction"),
        "latency_ms":  round(latency_ms, 1),
    }
    try:
        with _LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception as exc:
        log.warning("Monitoring log write failed: %s", exc)


def get_drift_report(window: int = 100) -> dict:
    """Read the last *window* predictions and compare to the training baseline.

    Returns
    -------
    total_logged      -- total rows in the log file
    window            -- how many rows were analysed (may be < requested if log is small)
    mean_probability  -- mean placement_probability over the window
    baseline          -- training-time mean (BASELINE_MEAN_PROB)
    drift             -- abs(mean - baseline), rounded to 4 dp
    alert             -- True when drift > DRIFT_THRESHOLD
    recommendation    -- plain-language action string
    """
    if not _LOG_FILE.exists():
        return {
            "total_logged":     0,
            "window":           0,
            "mean_probability": None,
            "baseline":         BASELINE_MEAN_PROB,
            "drift":            None,
            "alert":            False,
            "recommendation":   "No predictions logged yet.",
            **_ethiopia_metrics(),
        }

    lines  = _LOG_FILE.read_text(encoding="utf-8").splitlines()
    total  = len(lines)
    recent = lines[-window:]

    probs = []
    for line in recent:
        try:
            rec = json.loads(line)
            p   = rec.get("probability")
            if isinstance(p, (int, float)):
                probs.append(float(p))
        except Exception:
            pass

    if not probs:
        return {
            "total_logged":     total,
            "window":           len(recent),
            "mean_probability": None,
            "baseline":         BASELINE_MEAN_PROB,
            "drift":            None,
            "alert":            False,
            "recommendation":   "No valid probability values found in window.",
            **_ethiopia_metrics(),
        }

    mean_prob = round(sum(probs) / len(probs), 4)
    drift     = round(abs(mean_prob - BASELINE_MEAN_PROB), 4)
    alert     = drift > DRIFT_THRESHOLD

    extras = _ethiopia_metrics()

    if alert:
        recommendation = (
            f"ALERT: mean probability has drifted {drift:.1%} from the training "
            f"baseline ({mean_prob:.1%} vs {BASELINE_MEAN_PROB:.1%}). "
            "Run scripts/retrain.sh to update the models."
        )
    else:
        recommendation = (
            f"OK: model is within {drift:.1%} of baseline. No action needed."
        )

    return {
        "total_logged":     total,
        "window":           len(probs),
        "mean_probability": mean_prob,
        "baseline":         BASELINE_MEAN_PROB,
        "drift":            drift,
        "alert":            alert,
        "recommendation":   recommendation,
        **extras,
    }


def get_recent_predictions(n: int = 20) -> list:
    """Return the last *n* raw prediction log entries as a list of dicts."""
    if not _LOG_FILE.exists():
        return []

    lines  = _LOG_FILE.read_text(encoding="utf-8").splitlines()
    recent = lines[-n:]
    result = []
    for line in recent:
        try:
            result.append(json.loads(line))
        except Exception:
            pass
    return result
