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
- Load all four ML models plus the SHAP cache into memory (~60–90 s on first start)
- Build the React image and start the Vite dev server

Once you see `PathWise API ready.` in the logs the stack is fully up.

| Service | URL | Set by |
|---|---|---|
| React frontend | http://localhost:3001 | `FRONTEND_HOST_PORT` |
| FastAPI backend | http://localhost:8000 | `API_HOST_PORT` |
| Interactive API docs | http://localhost:8000/docs | `API_HOST_PORT` |
| PostgreSQL | localhost:5434 (user: `pathwise_user`, db: `pathwise_db`) | `DB_HOST_PORT` |

Every host port is configurable from `.env` — see §3. The shipped defaults avoid
`3000` and `5432`, which are the two most commonly occupied ports on a developer
machine running more than one project.

To stop: `docker compose down`
To stop and wipe the database volume: `docker compose down -v`

---

## 3. Environment Variables

All variables live in `.env` (copied from `.env.example`). The docker-compose file injects them into each container automatically.

There are two distinct kinds of port variable, and mixing them up is the most
common way to break the stack:

- **In-container ports** (`DB_PORT`, `API_PORT`) — what a process binds to *inside*
  its container, and what sibling containers dial over the Docker network.
  **Do not change these.**
- **Host ports** (`DB_HOST_PORT`, `API_HOST_PORT`, `FRONTEND_HOST_PORT`) — the
  left-hand side of each docker-compose port mapping, i.e. what you reach from your
  browser or `psql`. **Change these** when another project already owns a port.

| Variable | Default | Used by | Description |
|---|---|---|---|
| `DB_USER` | `pathwise_user` | backend, db | PostgreSQL username |
| `DB_PASSWORD` | `pathwise_pass` | backend, db | PostgreSQL password |
| `DB_NAME` | `pathwise_db` | backend, db | PostgreSQL database name |
| `DB_HOST` | `db` | backend | Hostname of the Postgres container (Docker internal DNS) |
| `DB_PORT` | `5432` | backend | In-container Postgres port — do not change |
| `DATABASE_URL` | _(constructed)_ | backend | Full SQLAlchemy connection string; overrides individual vars |
| `API_HOST` | `0.0.0.0` | backend | Uvicorn bind address |
| `API_PORT` | `8000` | backend | In-container port uvicorn binds to — do not change |
| `BACKEND_RELOAD` | _(empty)_ | backend | Set to `--reload` for auto-reload while editing backend code. See below. |
| `DB_HOST_PORT` | `5434` | host | Host port mapped to Postgres |
| `API_HOST_PORT` | `8000` | host, frontend | Host port mapped to the backend |
| `FRONTEND_HOST_PORT` | `3001` | host | Host port mapped to the Vite dev server |
| `FRONTEND_URL` | `http://localhost:3001` | backend | Allowed CORS origin; comma-separate multiple values |
| `VITE_API_URL` | `http://localhost:8000` | frontend | Base URL the React app uses for all API calls |

Two values must be kept in sync by hand:
- `FRONTEND_URL` must match `FRONTEND_HOST_PORT` — it is the Origin header the
  browser sends, and CORS rejects the request if it doesn't match.
- `VITE_API_URL` must match `API_HOST_PORT` — the browser resolves it, not the
  container, so it needs the host port.

**To add a second allowed CORS origin** (e.g. a production domain alongside local dev):
```
FRONTEND_URL=http://localhost:3001,https://pathwise.example.com
```

### 3.1 Backend auto-reload

`BACKEND_RELOAD` is empty by default, so uvicorn runs without its file watcher.
The watcher is unreliable on Windows bind mounts — it crash-loops with
`WatchfilesRustInternalError: IO error for operation on /app`, which leaves the API
answering requests but with **zero models loaded**.

With the default, backend code changes need an explicit restart:
```bash
docker compose restart backend
```
If you are actively iterating on backend code and not on Windows, set
`BACKEND_RELOAD=--reload` in `.env` and `docker compose up -d backend`.

---

## 4. Architecture

```
Browser
  │
  │  HTTP (port 3000)
  ▼
┌─────────────────────────────┐
│  React + Vite (frontend)    │
│  /src/pages/  12 dashboard  │
│  /src/api/     Axios calls  │
└─────────────┬───────────────┘
              │  HTTP (port 8000)
              ▼
┌─────────────────────────────────────────────────┐
│  FastAPI (backend)                              │
│                                                 │
│  /api/market/*          market_service.py       │
│  /api/enrollment/*      enrollment_service.py   │
│  /api/monitoring/*      monitoring_service.py   │
│  /api/recommendations/* recommendations.py      │
│                                                 │
│  services/ml_service.py  ──►  /ml/models/      │
│    placement_xgboost.pkl  (XGBoost)             │
│    salary_xgboost.pkl     (XGBoost Regressor)   │
│    enrollment_lstm.keras  (TensorFlow LSTM)     │
│    enrollment_scaler.pkl                        │
│    demand_prophet.pkl     (Prophet)             │
│                                                 │
│  data/processed/features.parquet  (all ML I/O) │
│  data/monitoring/predictions.jsonl (drift log) │
└─────────────────────────────────────────────────┘

        (not on the request path — see below)

  data/*.csv ──► startup_seed.py ──► psycopg2 ──► ┌─────────────────────────────┐
                 data/load_to_db.py               │  PostgreSQL 15              │
                                                  │  students · enrollments     │
                                                  │  job_postings · placements  │
                                                  └─────────────────────────────┘
```

**Startup sequence** (enforced by docker-compose `depends_on` + healthchecks):
1. Postgres starts → schema applied (first run only) → `pg_isready` passes
2. Backend starts → seeds DB if empty → pre-warms all 4 ML models + SHAP cache → `/health` returns `ok`
3. Frontend starts → Vite serves React app

**Parquet is the serving layer; Postgres is the ETL sink.**

This is the single most important thing to know before reading the backend. **No
router or service touches PostgreSQL.** Every `/api/*` endpoint is served from flat
files:

| Source | Read by |
|---|---|
| `data/processed/features.parquet` | `enrollment_service.py`, `salary_service.py`, `escape_route_service.py`, `market_service.py`, and all ML inference |
| `data/mock/placements.csv` | `market_service.py`, `enrollment_service.py` |
| `data/monitoring/predictions.jsonl` | `monitoring_service.py` |

Postgres, `backend/db/schema.sql`, `backend/db/migrations/`, and the SQLAlchemy
models in `backend/models/` form a separate relational warehouse. It is populated
once by `backend/startup_seed.py` → `data/load_to_db.py` and exists for ad-hoc SQL
and future analytical work. Nothing in the request path reads from it, so **the API
serves all 12 dashboard pages correctly even when the database is down** — the
startup log will show `Startup seed skipped — database unreachable.` and everything
else still works.

A consequence worth knowing: a Postgres outage is silent from the dashboard's
perspective. Check `docker compose ps` rather than the UI to confirm the DB is
healthy.

---

## 5. API Reference

Base URL: `http://localhost:8000`

All endpoints return JSON. Errors return `{"detail": "<message>"}` with an appropriate HTTP status.

### 5.1 Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Per-model load status. Returns `status: "ok"` when all 5 artefacts are loaded, `"degraded"` if any failed. |
| POST | `/health/reload` | Retry loading any artefact that is not currently resident. |
| GET | `/` | Simple liveness check. |

**`GET /health` response:**
```json
{
  "status": "ok",
  "models": {
    "xgboost": true,
    "salary":  true,
    "lstm":    true,
    "prophet": true,
    "shap":    true
  }
}
```

`/health` reads the in-memory model singletons on every call, so it always reports
current state rather than a snapshot taken at startup.

**`POST /health/reload`** is the recovery path for a backend that came up before its
volume mounts were ready — the symptom is a reachable API reporting
`"status":"degraded"` with all five models `false`, and log lines like
`[fail] XGBoost: [Errno 2] No such file or directory: '/ml/models/placement_xgboost.pkl'`.
Rather than restarting the container, retry the load in place:

```bash
curl -X POST http://localhost:8000/health/reload
```

```json
{
  "status": "ok",
  "models": { "xgboost": true, "salary": true, "lstm": true, "prophet": true, "shap": true },
  "recovered": ["xgboost", "salary", "lstm", "prophet", "shap"]
}
```

`recovered` lists only the artefacts that flipped `false → true` on this call; it is
`[]` when everything was already loaded. The call is safe to repeat — loaders no-op
on an already-warm singleton. Loading all five from cold takes ~15 s.

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
Backend must be running locally on port 8000, or set `BASE_URL`:

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

### 6.3 Backend API test suite (pytest)

`backend/tests/test_api.py` is the primary backend suite — 55 tests covering
every endpoint: status codes, response schemas, parameter forwarding, error
handling, data consistency, and directional ML correctness.

Run inside the running container:

```bash
docker exec pathwise_backend pytest tests/test_api.py -v
```

Or locally against a running backend:

```bash
pytest backend/tests/test_api.py -v
# override the target
BASE_URL=http://127.0.0.1:8000 pytest backend/tests/test_api.py -v
```

`pytest` is pinned in `backend/requirements.txt`, so it is available inside the
backend image without any extra install step.

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

**`/health` returns `"degraded"` with all five models `false`**
The backend started before its `./ml` and `./data` bind mounts were ready, so every
artefact lookup missed. The mounts usually recover on their own moments later, but
the models are not retried automatically. Retry them in place:
```bash
curl -X POST http://localhost:8000/health/reload
```
If that still reports `degraded`, confirm the files are actually visible inside the
container: `docker exec pathwise_backend ls /ml/models`.

**Backend log is a repeating loop of `WatchfilesRustInternalError: IO error for operation on /app`**
Uvicorn's `--reload` watcher does not survive Windows bind mounts. Make sure
`BACKEND_RELOAD` is empty in `.env` (the default), then `docker compose up -d backend`.

**Frontend shows "Network Error" on every page**
The React app cannot reach the backend. Check:
1. `docker compose ps` — is `pathwise_backend` healthy?
2. `VITE_API_URL` in `.env` — must match `API_HOST_PORT`
3. CORS — `FRONTEND_URL` in `.env` must match `FRONTEND_HOST_PORT` and the origin your browser uses

**`psycopg2.OperationalError: could not connect to server`**
The backend started before Postgres was ready. This should not happen with the healthcheck in `docker-compose.yml`, but if it does: `docker compose restart backend`. Note the API still serves every dashboard page without Postgres — see §4.

**Port already in use / `bind: address already in use`**
Another project on your machine owns that host port. Change the **host** port in
`.env` — never the in-container `DB_PORT` / `API_PORT`:

| Symptom | Fix |
|---|---|
| `Bind for 0.0.0.0:5434 failed` | Raise `DB_HOST_PORT` |
| `listen tcp 0.0.0.0:3001: bind:` | Raise `FRONTEND_HOST_PORT`, then update `FRONTEND_URL` to match |
| `Bind for 0.0.0.0:8000 failed` | Raise `API_HOST_PORT`, then update `VITE_API_URL` to match |

Find a free port first:
```bash
netstat -ano | grep LISTENING | grep ':5434 '   # no output = free
```
Then `docker compose down && docker compose up -d`.

**`could not translate host name "db" to address` even though the db container exists**
This is the downstream symptom of the port clash above. When Postgres cannot bind its
host port, the container fails to start its networking and ends up attached to **no
Docker network at all**, so the backend cannot resolve `db`. Confirm with:
```bash
docker inspect pathwise_db --format '{{json .NetworkSettings.Networks}}'   # {} means unattached
```
Fix the port conflict, then `docker compose down && docker compose up -d` — a
`restart` is not enough, the container has to be recreated.

**`UnicodeEncodeError` running Python test scripts on Windows**
Run with the UTF-8 flag: `python -X utf8 tests/test_phase5.py`

**Model metrics look wrong after retraining**
`generate_model_metrics.py` reads the current `features.parquet`. If the parquet was regenerated with a different feature set, re-run `data/build_parquet_from_csv.py` first, then retrain.
