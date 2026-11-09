"""
Prediction monitoring service.

Two concerns, reported together for the admin Model performance monitor
(W.ADM.03):

* Ethiopia Models 1–2 — input drift (PSI) and error drift (latest backtest
  error vs earlier origins) per forecast target, from ml/drift.py. This is the
  monitoring that matters for the request path.
* Leftover US placement model (only with LEGACY_US_MODELS=1) — logs every
  predict-placement call to data/monitoring/predictions.jsonl and compares
  recent mean probability with the earliest logged window. The baseline used
  to be a hard-coded 0.88 copied from a stale metrics file.

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

# Raise alert when |recent mean − reference mean| exceeds this
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
        "model1": _ethiopia_block(m1, "M1 applications (unconstrained demand)"),
        "model2": _ethiopia_block(m2, "M2 employment"),
        "not_compared": sorted(set(
            list(m1.get("not_compared") or [])
            + list(m2.get("not_compared") or [])
        )),
    }
    headline = ethiopia["model1"].get("selected") or ethiopia["model2"].get("selected") or {}
    return {
        "mae": headline.get("mae"),
        "rmse": headline.get("rmse"),
        "last_retrained": _mtime(_M1_CMP) or _mtime(_M2_CMP),
        "ethiopia": ethiopia,
        "us_models_not_compared": ethiopia["not_compared"],
    }


def _ethiopia_block(cmp: dict, label: str) -> dict:
    """Headline is the candidate the backtest selected at horizon 1."""
    estimators = cmp.get("estimators") or {}
    selected_name = (cmp.get("selected_by_horizon") or {}).get("1") or next(iter(estimators), None)
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


def _ethiopia_drift() -> dict:
    try:
        from ml.drift import ethiopia_drift
        return ethiopia_drift()
    except Exception as exc:  # monitoring must not take the admin page down
        log.warning("Ethiopia drift computation failed: %s", exc)
        return {"targets": {}, "alert": False, "error": str(exc)}


def _probabilities(lines: list[str]) -> list[float]:
    out = []
    for line in lines:
        try:
            p = json.loads(line).get("probability")
        except ValueError:
            continue
        if isinstance(p, (int, float)):
            out.append(float(p))
    return out


def _placement_drift(window: int) -> dict:
    """Leftover US placement check: recent window vs the earliest window."""
    from services.feature_flags import LEGACY_US_MODELS

    base = {"enabled": LEGACY_US_MODELS, "total_logged": 0, "window": 0,
            "mean_probability": None, "baseline": None, "baseline_source": None,
            "drift": None, "alert": False}
    if not LEGACY_US_MODELS:
        return {**base, "recommendation": "Leftover US placement model is switched off."}
    if not _LOG_FILE.exists():
        return {**base, "recommendation": "No predictions logged yet."}
    lines = _LOG_FILE.read_text(encoding="utf-8").splitlines()
    probs = _probabilities(lines)
    if len(probs) < 2 * window:
        return {**base, "total_logged": len(lines),
                "recommendation": f"Need {2 * window} logged predictions to compare windows."}
    reference = sum(probs[:window]) / window
    recent = sum(probs[-window:]) / window
    drift = round(abs(recent - reference), 4)
    return {
        **base,
        "total_logged": len(lines),
        "window": window,
        "mean_probability": round(recent, 4),
        "baseline": round(reference, 4),
        "baseline_source": f"first {window} logged predictions",
        "drift": drift,
        "alert": drift > DRIFT_THRESHOLD,
        "recommendation": (
            f"ALERT: recent mean probability moved {drift:.1%} from the reference window."
            if drift > DRIFT_THRESHOLD else "Placement predictions are stable against the reference window."
        ),
    }


def get_drift_report(window: int = 100) -> dict:
    """Ethiopia drift first; the US placement block is secondary and optional.

    Top-level `alert` / `recommendation` describe the Ethiopia models. The US
    fields keep their old names (`mean_probability`, `baseline`, `drift`) so
    existing clients still render.
    """
    ethiopia = _ethiopia_drift()
    placement = _placement_drift(window)
    return {
        **{k: placement[k] for k in ("total_logged", "window", "mean_probability",
                                     "baseline", "drift")},
        "alert": bool(ethiopia.get("alert")),
        "recommendation": ethiopia.get("recommendation") or placement["recommendation"],
        "ethiopia_drift": ethiopia,
        "placement": placement,
        **_ethiopia_metrics(),
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
