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
from pathlib import Path

log = logging.getLogger(__name__)

_ROOT        = Path(__file__).resolve().parent.parent.parent
_MONITOR_DIR = _ROOT / "data" / "monitoring"
_LOG_FILE    = _MONITOR_DIR / "predictions.jsonl"

# ── Baseline ──────────────────────────────────────────────────────────────────
# Training-time mean placement probability across 2,400 training rows.
# XGBoost: accuracy 88.17 %, precision 88.17 %, recall 100 % → the model
# rarely predicts Not Placed; mean probability ≈ 0.88.
BASELINE_MEAN_PROB = 0.88

# Raise alert when |mean - baseline| exceeds this fraction
DRIFT_THRESHOLD = 0.10


# ── Internal ──────────────────────────────────────────────────────────────────

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
        }

    mean_prob = round(sum(probs) / len(probs), 4)
    drift     = round(abs(mean_prob - BASELINE_MEAN_PROB), 4)
    alert     = drift > DRIFT_THRESHOLD

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
