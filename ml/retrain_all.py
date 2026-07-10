"""
PathWise — Full Retraining Pipeline

Runs all ML pipeline steps in dependency order using subprocess so each
script gets a clean Python environment. Stops immediately if any step fails
and names the failing step.

Steps:
  1/6  feature_engineering.py    — rebuild features.parquet from Postgres
  2/6  train_xgboost.py          — placement classification model
  3/6  train_salary_xgboost.py   — salary regression model
  4/6  train_lstm.py             — enrollment forecasting model
  5/6  train_prophet.py          — demand forecasting model
  6/6  generate_model_metrics.py — refresh model_metrics.json

Usage (from project root):
  python ml/retrain_all.py

Or via the shell wrappers:
  bash scripts/retrain.sh          # local
  bash scripts/retrain_docker.sh   # inside Docker container
"""

import os
import subprocess
import sys
import time

# ── Path setup ─────────────────────────────────────────────────────────────────

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_DIR = os.path.join(ROOT, "ml")

STEPS = [
    ("feature_engineering.py",   "Rebuild feature parquet from Postgres"),
    ("train_xgboost.py",         "Train XGBoost placement model"),
    ("train_salary_xgboost.py",  "Train XGBoost salary regression model"),
    ("train_lstm.py",            "Train LSTM enrollment forecast model"),
    ("train_prophet.py",         "Train Prophet demand forecast model"),
    ("generate_model_metrics.py","Refresh model_metrics.json"),
]

# ── Runner ─────────────────────────────────────────────────────────────────────

def run_step(index: int, script: str, description: str) -> None:
    """Run one pipeline step, raising RuntimeError on failure."""
    total   = len(STEPS)
    label   = f"[{index}/{total}]"
    script_path = os.path.join(ML_DIR, script)

    print(f"\n{label} {description}")
    print(f"       python ml/{script}")
    print("-" * 60)

    t0 = time.monotonic()
    result = subprocess.run(
        [sys.executable, script_path],
        cwd=ML_DIR,          # scripts expect to run from the ml/ directory
        env=os.environ.copy(),
    )
    elapsed = time.monotonic() - t0

    if result.returncode != 0:
        raise RuntimeError(
            f"Step {label} '{script}' failed with exit code {result.returncode}."
        )

    print(f"       done in {elapsed:.1f}s")


def main() -> int:
    print("=" * 60)
    print("  PathWise — Full ML Retraining Pipeline")
    print(f"  {len(STEPS)} steps · run from: {ROOT}")
    print("=" * 60)

    wall_start = time.monotonic()

    for i, (script, description) in enumerate(STEPS, start=1):
        try:
            run_step(i, script, description)
        except RuntimeError as err:
            print(f"\n[FAILED] {err}")
            print("  Fix the error above and re-run `python ml/retrain_all.py`.")
            print("=" * 60)
            return 1

    wall = time.monotonic() - wall_start
    print("\n" + "=" * 60)
    print(f"  Retraining complete in {wall:.1f}s")
    print()
    print("  Next steps:")
    print("    docker compose restart backend   # reload models inside Docker")
    print("    python ml/monitor_models.py      # verify new performance")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
