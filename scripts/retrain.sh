#!/usr/bin/env bash
# PathWise — Model Retraining Pipeline
#
# Retrains all three ML models in dependency order, then refreshes the
# metrics JSON.  Run from the project root:
#
#   bash scripts/retrain.sh
#
# After this completes, restart the backend so uvicorn picks up the new
# model files:
#
#   docker compose restart backend      # if running in Docker
#   # OR kill/restart uvicorn manually  # if running locally
#
# The script exits immediately (set -e) if any step fails so you never
# end up with a partial retrain where some models are old and some are new.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "========================================================"
echo "  PathWise Model Retraining Pipeline"
echo "  Root: $ROOT"
echo "========================================================"

# ── Step 1: XGBoost placement model ──────────────────────────────────────────
echo ""
echo "[1/4] Training XGBoost placement model ..."
python "$ROOT/ml/train_xgboost.py"
echo "      -> ml/models/placement_xgboost.pkl  updated"

# ── Step 2: LSTM enrollment forecasting model ─────────────────────────────────
echo ""
echo "[2/4] Training LSTM enrollment model ..."
python "$ROOT/ml/train_lstm.py"
echo "      -> ml/models/enrollment_lstm.keras  updated"
echo "      -> ml/models/enrollment_scaler.pkl  updated"
echo "      -> ml/models/enrollment_lstm_meta.pkl updated"

# ── Step 3: Prophet demand forecasting model ──────────────────────────────────
echo ""
echo "[3/4] Training Prophet demand model ..."
python "$ROOT/ml/train_prophet.py"
echo "      -> ml/models/demand_prophet.pkl     updated"

# ── Step 4: Refresh model metrics JSON ───────────────────────────────────────
echo ""
echo "[4/4] Refreshing model metrics ..."
python "$ROOT/ml/generate_model_metrics.py"
echo "      -> ml/models/model_metrics.json     updated"

echo ""
echo "========================================================"
echo "  Retraining complete."
echo "  Restart the backend to load the new models:"
echo "    docker compose restart backend"
echo "========================================================"
