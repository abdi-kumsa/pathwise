# PathWise — Technical Reference

This document covers environment setup, architecture, all API endpoints, how to run the test suites, how to retrain the models, and how to read the monitoring dashboard.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Quick Start](#2-quick-start)
3. [Environment Variables](#3-environment-variables)
4. [Architecture](#4-architecture)
5. [API Reference](#5-api-reference)
6. [Running Tests](#6-running-tests)
7. [Model Retraining](#7-model-retraining)
8. [Monitoring & Drift Detection](#8-monitoring--drift-detection)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

| Dependency | Minimum version | Notes |
|---|---|---|
| Docker Desktop | 4.x | Must be running before any `docker compose` command |
| Python | 3.11 | Only needed to run test scripts outside Docker |
| Node.js | 20 LTS | Only needed for local frontend development outside Docker |
| Git | any | To clone the repository |

All ML packages (TensorFlow, XGBoost, Prophet, SHAP) are installed **inside the Docker image**. You do not need to install them on your host machine.

---

## 2. Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/abdi-kumsa/pathwise.git
cd pathwise

# 2. Create your environment file
cp .env.example .env
# (the defaults in .env.example work out of the box — no changes needed)

# 3. Start all three services
docker compose up
```

Docker will:
- Pull `postgres:15-alpine` and start the database
- Build the FastAPI image (~5–8 min on first run, cached thereafter)
- Run the schema migration and seed all 4 database tables automatically
- Load all three ML models into memory (~60–90 s on first start)
- Build the React image and start the Vite dev server

Once you see `PathWise API ready.` in the logs the stack is fully up.

| Service | URL |
|---|---|
| React frontend | http://localhost:3000 |
| FastAPI backend | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 (user: `pathwise_user`, db: `pathwise_db`) |

To stop: `docker compose down`
To stop and wipe the database volume: `docker compose down -v`

---

## 3. Environment Variables

All variables live in `.env` (copied from `.env.example`). The docker-compose file injects them into each container automatically.

| Variable | Default | Used by | Description |
|---|---|---|---|
| `DB_USER` | `pathwise_user` | backend, db | PostgreSQL username |
| `DB_PASSWORD` | `pathwise_pass` | backend, db | PostgreSQL password |
| `DB_NAME` | `pathwise_db` | backend, db | PostgreSQL database name |
| `DB_HOST` | `db` | backend | Hostname of the Postgres container (Docker internal DNS) |
| `DB_PORT` | `5432` | backend | PostgreSQL port |
| `DATABASE_URL` | _(constructed)_ | backend | Full SQLAlchemy connection string; overrides individual vars |
| `API_HOST` | `0.0.0.0` | backend | Uvicorn bind address |
| `API_PORT` | `8000` | backend, frontend | Port the FastAPI backend listens on |
| `FRONTEND_URL` | `http://localhost:3000` | backend | Allowed CORS origin; comma-separate multiple values |
| `VITE_API_URL` | `http://localhost:8000` | frontend | Base URL the React app uses for all API calls |

**To add a second allowed CORS origin** (e.g. a production domain alongside local dev):
```
FRONTEND_URL=http://localhost:3000,https://pathwise.example.com
```

---

## 4. Architecture

```
Browser
  │
  │  HTTP (port 3000)
  ▼
┌─────────────────────────────┐
│  React + Vite (frontend)    │
│  /src/pages/   8 dashboard  │
│  /src/api/     Axios calls  │
└─────────────┬───────────────┘
              │  HTTP (port 8000)
              ▼
┌─────────────────────────────────────────────────┐
│  FastAPI (backend)                              │
│                                                 │
│  /api/market/*      market_service.py           │
│  /api/enrollment/*  enrollment_service.py       │
│  /api/monitoring/*  monitoring_service.py       │
│                                                 │
│  services/ml_service.py  ──►  /ml/models/      │
│    placement_xgboost.pkl  (XGBoost)             │
│    enrollment_lstm.keras  (TensorFlow LSTM)     │
│    enrollment_scaler.pkl                        │
│    demand_prophet.pkl     (Prophet)             │
│                                                 │
│  data/processed/features.parquet  (all ML I/O) │
│  data/monitoring/predictions.jsonl (drift log) │
└──────────────┬──────────────────────────────────┘
               │  psycopg2 (port 5432)
               ▼
┌─────────────────────────────┐
│  PostgreSQL 15              │
│  students · enrollments     │
│  job_postings · placements  │
└─────────────────────────────┘
```

**Startup sequence** (enforced by docker-compose `depends_on` + healthchecks):
1. Postgres starts → schema applied (first run only) → `pg_isready` passes
2. Backend starts → seeds DB if empty → pre-warms all 4 ML models → `/health` returns `ok`
3. Frontend starts → Vite serves React app

**Data flow for ML endpoints:**
All ML inference reads from `data/processed/features.parquet` — not from PostgreSQL. Postgres holds the relational data (students, placements etc.) for potential future analytical queries; the parquet file is the denormalised feature store the models were trained on and continue to read at inference time.

---

## 5. API Reference

Base URL: `http://localhost:8000`

All endpoints return JSON. Errors return `{"detail": "<message>"}` with an appropriate HTTP status.

### 5.1 Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Per-model load status. Returns `status: "ok"` when all 4 models are loaded, `"degraded"` if any failed. |
| GET | `/` | Simple liveness check. |

**`GET /health` response:**
```json
{
  "status": "ok",
  "models": {
    "xgboost": true,
    "lstm":    true,
    "prophet": true,
    "shap":    true
  }
}
```

---

### 5.2 Market Demand

| Method | Path | Query params | Description |
|---|---|---|---|
| GET | `/api/market/overview` | — | KPI summary: companies, placements, avg salary, time-to-hire, top role |
| GET | `/api/market/top-companies` | `n=10` | Top N hiring companies by placement count |
| GET | `/api/market/regional-hiring` | — | Placement counts by geographic region |
| GET | `/api/market/job-internship-ratio` | — | Total jobs vs internships and their ratio |
| GET | `/api/market/skill-gap` | — | Demand vs curriculum coverage per skill, top gap skill, avg gap score |
| GET | `/api/market/hiring-sources` | — | Placement counts by industry sector |
| GET | `/api/market/demand-forecast` | `months=12` | N-month Prophet demand forecast with confidence bounds |

**`GET /api/market/overview` response:**
```json
{
  "total_companies":  30,
  "total_placements": 2649,
  "avg_salary":       118526.4,
  "avg_time_to_hire": 54.2,
  "top_role":         "Full Stack Developer"
}
```

**`GET /api/market/demand-forecast?months=12` response (array):**
```json
[
  {
    "month":               "2025-01-01",
    "predicted_postings":  312,
    "lower_bound":         289,
    "upper_bound":         335
  }
]
```

---

### 5.3 Enrollment Intelligence

| Method | Path | Query params | Description |
|---|---|---|---|
| GET | `/api/enrollment/summary` | — | Total students, programmes, avg placement rate, top programme, enrolment by year |
| GET | `/api/enrollment/forecast` | `program` (required), `years=3` | LSTM rolling forecast for a given programme |
| GET | `/api/enrollment/admission-risk` | `limit=10` | Programmes ranked by admission risk score (declining enrolment) |
| GET | `/api/enrollment/placement-by-stream` | — | Placement rate, avg salary, student count per programme |
| POST | `/api/enrollment/predict-placement` | — | XGBoost placement probability + SHAP contributions (body: StudentProfile) |
| GET | `/api/enrollment/skill-recommendations` | `student_id` (optional) | Global SHAP-derived skill recommendations + alternative pathways |

**`POST /api/enrollment/predict-placement` request body:**
```json
{
  "gpa":                 3.8,
  "internships":         3,
  "projects":            5,
  "communication_score": 9,
  "program":             "MS Data Science"
}
```

**`POST /api/enrollment/predict-placement` response:**
```json
{
  "placement_probability": 0.9535,
  "prediction":            "Placed",
  "base_value":            2.0377,
  "shap_values": [
    { "feature": "gpa_scaled",    "value": 0.95, "shap": 1.29 },
    { "feature": "internships",   "value": 3.0,  "shap": 0.74 }
  ]
}
```

**`GET /api/enrollment/forecast?program=MS Data Science&years=3` response:**
```json
{
  "program": "MS Data Science",
  "historical": [
    { "year": 2019, "predicted_count": 40 }
  ],
  "forecast": [
    { "year": 2025, "predicted_count": 43 },
    { "year": 2026, "predicted_count": 46 },
    { "year": 2027, "predicted_count": 49 }
  ]
}
```

---

### 5.4 Monitoring

| Method | Path | Query params | Description |
|---|---|---|---|
| GET | `/api/monitoring/drift` | `window=100` | Drift report comparing recent prediction probabilities to the training baseline |
| GET | `/api/monitoring/predictions` | `n=20` | Raw tail of the prediction log |

**`GET /api/monitoring/drift` response:**
```json
{
  "total_logged":     847,
  "window":           100,
  "mean_probability": 0.8741,
  "baseline":         0.88,
  "drift":            0.0059,
  "alert":            false,
  "recommendation":   "OK: model is within 0.6% of baseline. No action needed."
}
```

When `alert` is `true`, run the retraining pipeline (see §7).

---

## 6. Running Tests

### 6.1 Frontend unit tests (Vitest)

```bash
cd frontend
npm test              # single run — all 116 tests
npm run test:watch    # watch mode for development
npm run test:coverage # generates coverage report in frontend/coverage/
```

### 6.2 Backend integration tests (Python)

**Phase 5 tests** — validate API contracts, cache behaviour, ML flows.
Backend must be running locally on port 8080, or set `BASE_URL`:

```bash
python tests/test_phase5.py
# or
BASE_URL=http://127.0.0.1:8000 python tests/test_phase5.py
```

**Phase 6 smoke test** — full-stack Docker integration (all 114 checks).
Requires `docker compose up -d` and all containers healthy:

```bash
python tests/test_integration_docker.py
# or with custom URLs
BACKEND_URL=http://127.0.0.1:8000 FRONTEND_URL=http://127.0.0.1:3000 \
  python tests/test_integration_docker.py
```

Exit code: `0` = all pass, `1` = at least one failure.

---

## 7. Model Retraining

Re-run the training pipeline whenever:
- New student/placement data has been loaded into the database
- The monitoring drift report shows `alert: true`
- More than 6 months have passed since the last retrain

### Local retraining (outside Docker)

```bash
bash scripts/retrain.sh
```

Runs all four steps in order and exits on any failure. After it completes, restart the backend:

```bash
# if running with docker compose
docker compose restart backend

# if running uvicorn directly
# kill uvicorn and start again — --reload will pick up the new .pkl files
```

### Retraining inside Docker (no local Python needed)

```bash
bash scripts/retrain_docker.sh
```

Runs each training script inside the `pathwise_backend` container via `docker exec`, then automatically restarts the container. Requires the stack to be running (`docker compose up -d`).

### What gets updated

| File | Updated by |
|---|---|
| `ml/models/placement_xgboost.pkl` | `train_xgboost.py` |
| `ml/models/placement_feature_names.pkl` | `train_xgboost.py` |
| `ml/models/enrollment_lstm.keras` | `train_lstm.py` |
| `ml/models/enrollment_scaler.pkl` | `train_lstm.py` |
| `ml/models/enrollment_lstm_meta.pkl` | `train_lstm.py` |
| `ml/models/demand_prophet.pkl` | `train_prophet.py` |
| `ml/models/model_metrics.json` | `generate_model_metrics.py` |

---

## 8. Monitoring & Drift Detection

Every call to `POST /api/enrollment/predict-placement` is automatically logged to `data/monitoring/predictions.jsonl`. Each log line is a JSON object:

```json
{
  "ts":          1720612345.123,
  "inputs":      { "gpa": 3.8, "internships": 3, ... },
  "probability": 0.9535,
  "prediction":  "Placed",
  "latency_ms":  12.4
}
```

### Checking model health

```bash
# Quick check via curl
curl http://localhost:8000/api/monitoring/drift

# Or open in a browser
http://localhost:8000/api/monitoring/drift
```

The drift endpoint compares the mean `probability` of the last 100 predictions against the training-time baseline of **0.88**. If the mean drifts more than **10 percentage points** in either direction, `alert: true` is returned.

### What drift means

| Scenario | Likely cause | Action |
|---|---|---|
| Mean drops below 0.78 | Input profiles shifting toward weaker students; or model degrading | Retrain or investigate input distribution |
| Mean rises above 0.98 | Unusually strong cohort; or data quality issue | Inspect recent inputs via `/api/monitoring/predictions` |
| No predictions logged | Nobody has used the Student Evaluator yet | Normal on a fresh install |

---

## 9. Troubleshooting

**`docker compose up` hangs on "Building backend"**
The first build installs TensorFlow (~400 MB). This can take 5–10 minutes on a slow connection. Subsequent builds are cached — rebuilds take under 30 seconds unless `requirements.txt` changes.

**Backend shows `[fail] LSTM: ...` in logs**
The `.keras` model file is missing or corrupt. Re-run `python ml/train_lstm.py` (or `bash scripts/retrain.sh`) then restart the backend.

**Frontend shows "Network Error" on every page**
The React app cannot reach the backend. Check:
1. `docker compose ps` — is `pathwise_backend` healthy?
2. `VITE_API_URL` in `.env` — should be `http://localhost:8000`
3. CORS — `FRONTEND_URL` in `.env` must match the origin your browser uses

**`psycopg2.OperationalError: could not connect to server`**
The backend started before Postgres was ready. This should not happen with the healthcheck in `docker-compose.yml`, but if it does: `docker compose restart backend`.

**Port 3000 / 8000 already in use**
Another process is using the port. Either stop that process or change the port in `.env` (`API_PORT`, `VITE_API_URL`) and `docker-compose.yml`.

**`UnicodeEncodeError` running Python test scripts on Windows**
Run with the UTF-8 flag: `python -X utf8 tests/test_phase5.py`

**Model metrics look wrong after retraining**
`generate_model_metrics.py` reads the current `features.parquet`. If the parquet was regenerated with a different feature set, re-run `data/build_parquet_from_csv.py` first, then retrain.
