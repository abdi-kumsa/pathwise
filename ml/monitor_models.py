"""
PathWise — Model Performance Monitor

Loads the trained XGBoost placement model, evaluates it against the 50 most
recent student records in the feature store, and compares the result against
the baseline metrics stored in ml/models/model_metrics.json.

Exit codes:
  0 — performance is within acceptable bounds
  1 — drift detected (performance dropped >10 pp from baseline)

Usage (from project root):
  python ml/monitor_models.py

Cron (weekly, every Monday at 07:00):
  0 7 * * 1 cd /app && python ml/monitor_models.py >> logs/monitor.log 2>&1
"""

import json
import os
import pickle
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
try:
    from artifacts import verified_open, verify  # noqa: F401  (ml/ on sys.path)
except ImportError:  # imported as part of the ml package
    from ml.artifacts import verified_open, verify  # noqa: F401

# ── Paths ──────────────────────────────────────────────────────────────────────

def _project_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)

ROOT      = _project_root()
PARQUET   = os.path.join(ROOT, "data", "processed", "features.parquet")
MODEL_DIR = os.path.join(ROOT, "ml", "models")
METRICS   = os.path.join(MODEL_DIR, "model_metrics.json")

DRIFT_THRESHOLD = 0.10   # flag if any key metric drops >10 percentage points
SAMPLE_SIZE     = 50     # evaluate against the N most recent student records

# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_model():
    with verified_open(os.path.join(MODEL_DIR, "placement_xgboost.pkl")) as f:
        model = pickle.load(f)
    with verified_open(os.path.join(MODEL_DIR, "placement_feature_names.pkl")) as f:
        feature_names = pickle.load(f)
    return model, feature_names


def _load_baseline() -> dict:
    with open(METRICS) as f:
        metrics = json.load(f)
    return metrics.get("xgboost_placement", {})


def _load_recent_records(feature_names: list) -> tuple:
    df = pd.read_parquet(PARQUET)

    # Sort by enrollment_year descending, take the most recent SAMPLE_SIZE rows
    if "enrollment_year" in df.columns:
        df = df.sort_values("enrollment_year", ascending=False)
    sample = df.head(SAMPLE_SIZE)

    X = sample[feature_names]
    y = sample["placed"]
    return X, y


# ── Main ───────────────────────────────────────────────────────────────────────

def run_monitor() -> int:
    print("=" * 60)
    print("  PathWise — XGBoost Placement Model Monitor")
    print(f"  Evaluating on last {SAMPLE_SIZE} student records")
    print("=" * 60)

    # Load assets
    try:
        model, feature_names = _load_model()
    except FileNotFoundError as e:
        print(f"\n[ERROR] Model file not found: {e}")
        print("  Run `bash scripts/retrain.sh` to train the model first.")
        return 1

    try:
        baseline = _load_baseline()
    except FileNotFoundError:
        print(f"\n[ERROR] {METRICS} not found.")
        print("  Run `python ml/generate_model_metrics.py` to create it.")
        return 1

    # Load recent records
    try:
        X, y = _load_recent_records(feature_names)
    except FileNotFoundError:
        print(f"\n[ERROR] Feature parquet not found at {PARQUET}")
        return 1

    if len(y) < 10:
        print(f"\n[WARN] Only {len(y)} records available — sample too small for reliable drift detection.")

    # Compute current metrics
    y_pred      = model.predict(X)
    y_pred_prob = model.predict_proba(X)[:, 1]

    current_accuracy = float(accuracy_score(y, y_pred))
    current_f1       = float(f1_score(y, y_pred, zero_division=0))
    current_roc_auc  = float(roc_auc_score(y, y_pred_prob)) if len(set(y)) > 1 else float("nan")

    baseline_accuracy = float(baseline.get("accuracy", 0.0))
    baseline_f1       = float(baseline.get("f1_score", 0.0))

    drop_accuracy = baseline_accuracy - current_accuracy
    drop_f1       = baseline_f1       - current_f1

    # Report
    print("\n  Baseline  (model_metrics.json)")
    print(f"    Accuracy : {baseline_accuracy:.4f}")
    print(f"    F1-Score : {baseline_f1:.4f}")

    print(f"\n  Current   (last {SAMPLE_SIZE} records)")
    print(f"    Accuracy : {current_accuracy:.4f}  (Δ {drop_accuracy:+.4f})")
    print(f"    F1-Score : {current_f1:.4f}  (Δ {drop_f1:+.4f})")
    if not np.isnan(current_roc_auc):
        print(f"    ROC-AUC  : {current_roc_auc:.4f}")

    # Drift decision
    drifted = drop_accuracy > DRIFT_THRESHOLD or drop_f1 > DRIFT_THRESHOLD
    print()

    if drifted:
        print("  [DRIFT DETECTED] Model drift detected — retrain recommended.")
        if drop_accuracy > DRIFT_THRESHOLD:
            print(f"    Accuracy dropped {drop_accuracy:.1%} (threshold {DRIFT_THRESHOLD:.0%})")
        if drop_f1 > DRIFT_THRESHOLD:
            print(f"    F1-Score dropped {drop_f1:.1%} (threshold {DRIFT_THRESHOLD:.0%})")
        print()
        print("  To retrain:")
        print("    bash scripts/retrain.sh                # local")
        print("    bash scripts/retrain_docker.sh         # inside Docker")
        print("=" * 60)
        return 1
    else:
        print("  [OK] Model performance is within acceptable bounds.")
        print(f"    Accuracy drop {drop_accuracy:.1%} < {DRIFT_THRESHOLD:.0%} threshold")
        print(f"    F1-Score drop {drop_f1:.1%} < {DRIFT_THRESHOLD:.0%} threshold")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(run_monitor())
