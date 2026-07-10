#!/usr/bin/env bash
# PathWise — Containerised Model Retraining
#
# Runs the full retraining pipeline inside the running backend container,
# then restarts the container so uvicorn hot-reloads the new model files.
#
# Usage (from the project root):
#   bash scripts/retrain_docker.sh
#
# Requirements:
#   - Docker Compose stack must be running (docker compose up -d)
#   - The /ml volume must be mounted read-write (it is by default in
#     docker-compose.yml: ./ml:/ml)

set -euo pipefail

CONTAINER="pathwise_backend"

echo "========================================================"
echo "  PathWise Containerised Retraining"
echo "  Container: $CONTAINER"
echo "========================================================"

# Verify the container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo ""
  echo "ERROR: container '$CONTAINER' is not running."
  echo "Start the stack first:  docker compose up -d"
  exit 1
fi

# ── Run retraining inside the container ──────────────────────────────────────
# /scripts is not a volume mount, but the project root is mounted at /app
# and the ml/ dir at /ml, so we call the scripts directly via python.
echo ""
echo "[1/4] XGBoost ..."
docker exec "$CONTAINER" python /ml/train_xgboost.py

echo "[2/4] LSTM ..."
docker exec "$CONTAINER" python /ml/train_lstm.py

echo "[3/4] Prophet ..."
docker exec "$CONTAINER" python /ml/train_prophet.py

echo "[4/4] Metrics ..."
docker exec "$CONTAINER" python /ml/generate_model_metrics.py

# ── Restart the backend so uvicorn reloads the new .pkl / .keras files ────────
echo ""
echo "Restarting backend container ..."
docker compose restart backend

echo ""
echo "========================================================"
echo "  Retrain complete. New models are live."
echo "  Check model status: curl http://localhost:8000/health"
echo "  Check drift report: curl http://localhost:8000/api/monitoring/drift"
echo "========================================================"
