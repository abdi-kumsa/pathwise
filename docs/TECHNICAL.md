# PathWise — Technical Reference

This document covers environment setup, architecture, all API endpoints, how to run the test suites, how to retrain the models, and how to read the monitoring dashboard.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Quick Start](#2-quick-start)
3. [Environment Variables](#3-environment-variables)
4. [Architecture](#4-architecture)
5. [Roles & Permissions](#5-roles--permissions)
6. [API Reference](#6-api-reference)
7. [Running Tests](#7-running-tests)
8. [Model Retraining](#8-model-retraining)
9. [Monitoring & Drift Detection](#9-monitoring--drift-detection)
10. [Troubleshooting](#10-troubleshooting)

See [DATA_PROVENANCE.md](DATA_PROVENANCE.md) — Ethiopia 2016–2025 simulated
structure, twenty fact tables, and how leftover US tools are labelled.

See also [METHODOLOGY.md](METHODOLOGY.md) and [USER_GUIDE.md](USER_GUIDE.md).

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
Browser  (http://localhost:3001)
  │
  ▼
┌─────────────────────────────┐
│  React + Vite               │
│  five role UIs (navConfig)  │
│  ProvenanceBadge in the shell│
└─────────────┬───────────────┘
              │  HTTP :8000
              ▼
┌─────────────────────────────────────────────────┐
│  FastAPI                                        │
│                                                 │
│  /api/student/*         student_service         │
│  /api/institution/*     institution_service     │
│  /api/education/*       education_service       │
│  /api/labour/*          labour_market_service   │
│  /api/model1/*          constraint_service      │
│  /api/model2/*          model2_service          │
│  /api/model3/*          alignment_service       │
│  /api/admin/*           admin_service           │
│  /api/methodology/*     methodology_service     │
│  /api/ahp/*             ml/ahp                  │
│  /api/users             auth_service            │
│  /api/monitoring/*      monitoring_service      │
│                                                 │
│  leftover tools (not Ethiopia M1/M2):           │
│    /api/market/*        market_service          │
│    /api/enrollment/*    enrollment_service      │
│    /api/careers/*       career_service (US odds)│
│                                                 │
│  data/ethiopia/*.parquet     request-path facts │
│  ml/model1, ml/model2, ml/model3                │
│  ml/models/ethiopia_comparison.json             │
└─────────────────────────────────────────────────┘

  Postgres 15  — users, audit_log, scenarios, ahp_matrices, expert_validations
  (not the analytics store)
```

**Startup sequence** (docker-compose `depends_on` + healthchecks):
1. Postgres starts → schema applied (first run) → `pg_isready` passes
2. Backend starts → seeds users if empty → pre-warms leftover US artefacts + SHAP → `/health`
3. Frontend starts → Vite on host port 3001

**Parquet is the serving layer for dashboards.** Ethiopia fact tables under
`data/ethiopia/` feed Models 1–3 and the five role UIs. Postgres on the request
path is authentication plus governance tables. A database outage blocks sign-in;
analytics still read parquet.

Leftover US CSVs (`Assets/`, `data/mock/`, `data/processed/features.parquet`)
are **not** the backbone. They remain on the placement / salary / LSTM tool
routes. See [DATA_PROVENANCE.md](DATA_PROVENANCE.md) and waiver WV.US1.

See also [METHODOLOGY.md](METHODOLOGY.md).

---

## 5. Roles & Permissions

PathWise is role based. Every `/api/*` endpoint except `/health`, `/` and
`/api/auth/*` requires a bearer token, and most require a specific role.

### 5.1 The five roles

| Role | Lands on | Answers |
|---|---|---|
| `STUDENT` | `/student/profile` | "What is my field outlook and which alternatives rank on labour demand?" |
| `MOL` | `/mol/overview` | "Which occupations are emerging and where is the workforce short?" |
| `MOE` | `/moe/overview` | "Which fields should we invest new education capacity in?" |
| `UNIVERSITY` | `/university/overview` | "Which of our programmes should we expand or consolidate?" |
| `ADMIN` | `/admin/overview` | Everything, plus model monitoring |

`ADMIN` satisfies every `require_roles` check by construction
(`services/auth_service.py`), so a new router cannot accidentally lock the
administrator out of its own system.

The landing route is served by the API (`ROLE_HOME`) and returned on login, so
the role→page mapping lives in one place rather than being duplicated in the
React router.

### 5.2 Permission matrix

Enforced server-side. A disallowed role gets `403`; no token gets `401`.

| Endpoint prefix | ADMIN | STUDENT | MOE | MOL | UNIVERSITY |
|---|:--:|:--:|:--:|:--:|:--:|
| `/api/student` | ✓ | ✓ | | | |
| `/api/institution` | ✓ | | | | ✓ |
| `/api/education` | ✓ | | ✓ | | |
| `/api/labour` | ✓ | | ✓ | ✓ | |
| `/api/model1` | ✓ | | ✓ | | ✓ |
| `/api/model2` | ✓ | | ✓ | ✓ | |
| `/api/model3` | ✓ | | ✓ | ✓ | ✓ |
| `/api/admin` | ✓ | | | | |
| `/api/methodology` | ✓ | | | | |
| `/api/ahp` | ✓ | | | | |
| `/api/users` | ✓ | | | | |
| `/api/monitoring` | ✓ | | | | |
| `/api/careers` | ✓ | ✓ | | | |
| `/api/market` (leftover US) | ✓ | ✓ | ✓ | ✓ | ✓ |
| `/api/enrollment` (leftover US) | ✓ | ✓ | ✓ | | ✓ |
| `/api/search` | ✓ | ✓ | ✓ | ✓ | ✓ |

MoE reads `/api/labour` because labour demand is the input to their investment
decisions. MoL has no enrolment-planning remit, so it is excluded from
`/api/enrollment`.

`/api/search` is open to every role but **filters its results server-side** — a
student never receives institution records in the response.

### 5.3 Row-level scoping for universities

A `UNIVERSITY` token carries an `institution` claim. Every
`/api/institution/*` handler reads the institution from that signed claim and
**never from a request parameter**, so one university cannot read another's data
by crafting a URL. Peer benchmarks are anonymised to "Peer A/B/C…".

A `UNIVERSITY` token with no institution claim is rejected rather than falling
back to all-institution access.

### 5.4 Authentication

- bcrypt password hashing (passlib), HS256 JWTs (python-jose)
- token carries `sub`, `role`, `institution`, `exp`; no server-side session store
- `JWT_SECRET` and `JWT_EXPIRE_MINUTES` come from `.env`. If `JWT_SECRET` is
  unset the API falls back to a built-in development key **and logs a warning at
  startup** — set it before deploying anywhere real
- login returns one generic `401` for both an unknown username and a wrong
  password, so the endpoint cannot be used to enumerate accounts

**This puts Postgres on the request path for the first time.** Before the
role-based work the database was an unused ETL sink and the dashboards worked
with it down. Now the `users` table is queried on every login, so **a database
outage blocks sign-in** — though an already-issued token keeps working, because
authorisation reads the token claims rather than the database. Login failure due
to an unreachable database returns `503`, not `401`, so the cause is not
mistaken for bad credentials.

### 5.5 Demo accounts

Five accounts are seeded on first start when the `users` table is empty, using
the password in `DEMO_PASSWORD` (default `pathwise123`):

`admin` · `student` · `moe` · `mol` · `university` (scoped to Addis Ababa University)

Seeding is idempotent — it exits silently once any user exists, so a changed
password is never overwritten on restart. **These are demo credentials.**
See §5.6 for how to replace them with real accounts.

### 5.6 User management

An administrator manages accounts from **Accounts** in the sidebar
(`/admin/users`). Every rule below is enforced in
`services/auth_service.py`, not in the router or the UI, so it holds regardless
of caller.

**Deactivation, not deletion.** `DELETE /api/users/{username}` sets
`is_active = false`. The row survives, the action is reversible, and the record
that the account existed is preserved. A permanent-delete route
(`DELETE /api/users/{username}/permanent`) exists for genuine erasure and test
teardown but is deliberately **not** surfaced as a button — an irreversible
action one click from a reversible one is a trap.

**Revocation is not instant, and here is why.** `get_current_user` authorises
from token claims with no database hit — that is what keeps it fast and lets it
survive a brief Postgres outage (§5.4). With an 8-hour token lifetime, checking
`is_active` only at login would let a deactivated user keep full access for the
rest of their token's life; revoking access would revoke nothing.

So the status is checked per request behind a **30-second TTL cache**
(`_ACTIVE_TTL` in `auth_service.py`):

| Change made via | Takes effect |
|---|---|
| The API (admin console) | Immediately — the cache entry is evicted |
| Directly in the database | Within 30 seconds |

If the lookup fails, the last known value is served (defaulting to active), so a
database blip degrades to the previous behaviour rather than locking every user
out at once.

**Guard rails.** These exist because each one is a realistic way to make the
platform unmanageable:

1. You cannot deactivate or demote **your own** account.
2. You cannot deactivate, demote or delete the **last active administrator**.
3. **Usernames are immutable.** The username is the JWT `sub`; changing it would
   orphan every token already issued to that person. Role, display name,
   institution and password are all editable.
4. A `UNIVERSITY` account must be scoped to an institution, and it must be one of
   the eight in the dataset — otherwise the account authenticates and then shows
   empty dashboards, which reads as a bug rather than a mistake.
5. Passwords are at least 8 characters. Length only; no composition rules.

The UI disables the controls that these guards would reject, with the reason in
the tooltip, so the constraint is visible before the click rather than as an
error afterwards.

**Self-service.** `POST /api/auth/change-password` is available to **every
role**, not just administrators, and requires the current password — without
that, an unattended session could be used to lock the real owner out of their own
account. Reachable at `/account`, via the name in the sidebar footer.

**Replacing the demo accounts.** Do it in this order, or guard 2 will (correctly)
stop you:

1. Sign in as `admin`, create your own administrator account
2. Sign out, sign in as the new administrator
3. Deactivate the five seeded accounts
4. Rotate `DEMO_PASSWORD` in `.env` so a future `docker compose down -v` does not
   reseed the old credentials

---

## 6. API Reference

Base URL: `http://localhost:8000`

All endpoints return JSON. Errors return `{"detail": "<message>"}` with an appropriate HTTP status.

Except where noted, every endpoint below requires
`Authorization: Bearer <token>` — see §5.

### 6.0 Authentication

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/login` | public | OAuth2 password form → `{access_token, token_type, expires_in, user}` |
| GET | `/api/auth/me` | any role | Current caller; used to rehydrate a session on page load |
| GET | `/api/auth/roles` | any role | Role vocabulary and landing routes |
| POST | `/api/auth/change-password` | any role | Change your own password; requires the current one. 204 on success. |

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -d 'username=student&password=pathwise123' \
  | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/auth/me
```

### 6.1 Careers — leftover US tool (`STUDENT`)

Not Ethiopia Model 1 or 2. Hidden from role nav; the route still exists.

| Method | Path | Description |
|---|---|---|
| GET | `/api/careers/jobs` | All 33 occupations with their field |
| GET | `/api/careers/search?q=` | Typeahead; prefix matches rank first |
| GET | `/api/careers/job/{title}` | Labour-market profile for one occupation |
| POST | `/api/careers/recommend` | **Job → ranked departments**, with per-factor breakdown |

`recommend` takes `job_title` plus an optional `gpa`/`internships`/`projects`/
`communication_score`. A **partial** profile is treated as absent — the API will
not default an unanswered field and then present the result as personalised.
With a full profile, placement odds come from the XGBoost model; without one,
from each programme's historical rate. The response reports which via
`personalised`.

### 6.2 Labour market — `MOL`, `MOE`

| Method | Path | Description |
|---|---|---|
| GET | `/api/labour/overview` | Headline demand figures |
| GET | `/api/labour/emerging?level=family\|title` | Ranked by growth, with yearly series |
| GET | `/api/labour/supply-demand` | Workforce shortfall per field |
| GET | `/api/labour/mismatch?by=overview\|field\|program` | Graduate-to-role fit |
| GET | `/api/labour/regional?field=` | Demand by region (leftover explorer; not a DOC2 widget) |
| GET | `/api/labour/occupation/{title}` | Full occupation profile |

`mismatch` always returns `comparable: false` and a `caveat` — the distribution
is near-uniform across fields in this dataset and must not be charted as a
league table. See [DATA_PROVENANCE.md §4.1](DATA_PROVENANCE.md).

### 6.3 Education supply — `MOE`

| Method | Path | Description |
|---|---|---|
| GET | `/api/education/overview` | National enrolment and outcomes |
| GET | `/api/education/field-trends` | Enrolment and applications per field per year |
| GET | `/api/education/investment-quadrant` | Demand growth vs supply growth, split at each axis median |
| GET | `/api/education/investment-priority` | Ranked fields with weighted factor breakdown |
| GET | `/api/education/field/{field}` | Full field profile |

### 6.4 Institution — `UNIVERSITY`

Scoped to the caller's own institution; no institution parameter is accepted.

| Method | Path | Description |
|---|---|---|
| GET | `/api/institution/me` | Institution profile |
| GET | `/api/institution/portfolio` | All 12 programmes with funnel and cost |
| GET | `/api/institution/expansion` | Expand / Hold / Consolidate, with rationale |
| GET | `/api/institution/resources` | Recruitment funnel and cost per enrolment |
| GET | `/api/institution/benchmark` | Standing vs anonymised peers |

### 6.5 User management — `ADMIN`

| Method | Path | Description |
|---|---|---|
| GET | `/api/users` | All accounts, active first. Never returns password hashes. |
| POST | `/api/users` | Create. 409 if the username is taken, 422 on invalid input. |
| PATCH | `/api/users/{username}` | Role, display name, institution, active status |
| POST | `/api/users/{username}/password` | Admin reset — no current password needed |
| DELETE | `/api/users/{username}` | Deactivate (soft). Returns the updated account. |
| DELETE | `/api/users/{username}/permanent` | Erase and free the username. Not in the UI. |
| GET | `/api/users/meta/institutions` | The eight institutions a `UNIVERSITY` account may use |

`DELETE` returns a body rather than 204 so the client can re-render the row
without a second request. `PATCH` accepts no `username` field — see guard 3 in
§5.6.

The institution route is nested under `/meta/` so it cannot be shadowed by a
username in `/{username}`. `GET /api/users` returns `{ n, rows }` so provenance
middleware can stamp the object.

### 6.5a Student widgets — `STUDENT`

| Method | Path | Description |
|---|---|---|
| GET | `/api/student/profile` | JWT identity; query `username` / `student_id` ignored |
| GET | `/api/student/labour-outlook` | 3- and 5-year vacancies |
| GET | `/api/student/demand-comparison` | Student vs labour demand |
| GET | `/api/student/field-alignment` | Alignment score + weights |
| GET | `/api/student/supply-demand-gap` | Field gap rows |
| GET | `/api/student/alternatives` | Ranked fields; `fit_classification_used: false` |
| GET | `/api/student/skill-gaps` | Skill classes |
| GET | `/api/student/pathways` | Programme graph |
| GET | `/api/student/opportunities` | Scholarships / internships / training |

### 6.5b Models 1–3

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/api/model1/demand/unconstrained` | MOE, UNIVERSITY | Layer 1 |
| GET | `/api/model1/demand/constrained` | MOE, UNIVERSITY | After constraint layer |
| GET | `/api/model2/forecast` | MOL, MOE | Sector / occupation forecast |
| GET | `/api/model2/formal-informal` | MOL, MOE | Formal vs informal |
| GET | `/api/model2/skills-shortage` | MOL, MOE | Skills heatmap data |
| GET | `/api/model2/public-pipeline` | MOL, MOE | Public hiring |
| GET | `/api/model2/fdi-pipeline` | MOL, MOE | FDI / parks |
| GET | `/api/model2/migration` | MOL, MOE | Migration |
| GET | `/api/model3/policy-priority` | MOE, MOL, UNIVERSITY | MoE priority page ranker |

University `GET /api/institution/program-health` and `/funnel`, `/cohort-progression`,
`/graduate-outcomes`, `/resource-planning`, `/curriculum-alignment`,
`/demand-vs-labour` are the remaining DOC2 university widgets.

### 6.5c Admin, methodology, AHP — `ADMIN`

| Method | Path | Description |
|---|---|---|
| GET | `/api/admin/platform-health` | API + account counts |
| GET | `/api/admin/pipeline-status` | 20 Ethiopia feeds |
| GET | `/api/admin/data-quality` | Validation failures |
| GET | `/api/admin/scenarios` | Persisted what-ifs |
| GET | `/api/admin/audit-log` | Searchable audit |
| GET | `/api/methodology/feature-importance` | SHAP / permutation |
| GET | `/api/methodology/priority-tiers` | Collection-priority panels |
| GET | `/api/methodology/model-comparison` | M1/M2 holdout table |
| GET | `/api/methodology/expert-validations` | Step 2 records |
| POST | `/api/ahp/weights` | Eigenvector weights; CR > 0.1 → 422 |
| POST | `/api/ahp/consistency` | Consistency ratio only |

---

### 6.6 Search — any role

| Method | Path | Description |
|---|---|---|
| GET | `/api/search?q=&limit=` | Occupations, fields, programmes, institutions — filtered by role |

Each result carries the route the frontend should navigate to.

### 6.7 Health

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

### 6.8 Market Demand (leftover US tools)

Not Ethiopia Model 1 or Model 2. Pages that still call these routes carry a
DataNote (WV.US1).


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

### 6.9 Enrollment Intelligence (leftover US LSTM / XGBoost)

Not Ethiopia Model 1. University **Enrolment forecast** still uses the LSTM
route; Ethiopia constrained demand is `/api/model1/demand/constrained`.


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

### 6.10 Monitoring

| Method | Path | Query params | Description |
|---|---|---|---|
| GET | `/api/monitoring/drift` | `window=100` | Ethiopia M1/M2 RMSE vs seasonal-naive, plus leftover US placement drift |
| GET | `/api/monitoring/predictions` | `n=20` | Raw tail of the prediction log |

**`GET /api/monitoring/drift` response:**
```json
{
  "rmse":             12.4,
  "mae":              9.1,
  "ethiopia":         { "model1": {}, "model2": {} },
  "total_logged":     847,
  "window":           100,
  "mean_probability": 0.8741,
  "baseline":         0.88,
  "drift":            0.0059,
  "alert":            false,
  "recommendation":   "OK: Ethiopia seasonal-naive RMSE is the headline. US placement drift is leftover."
}
```

Headline `rmse` / `mae` are Ethiopia seasonal-naive. The 0.88 baseline is leftover US placement probability.

When `alert` is `true`, run the retraining pipeline (see §7).

---

## 7. Running Tests

Wave 8 gate (host, with Docker API on `:8000`):

```text
python scripts/spec_report.py
pytest tests/test_spec_coverage.py -m "integrity or honesty or coverage"
pytest tests/test_honesty_live.py tests/test_scopes.py tests/test_ahp.py tests/test_constraints.py
cd frontend && npm test
```

`spec_report.py` must print **259/259**. Honesty live and scopes need the
backend up (`BASE_URL` defaults to `http://127.0.0.1:8000`).

### 7.1 Frontend unit tests (Vitest)

```bash
cd frontend
npm test              # single run
npm run test:watch    # watch mode for development
npm run test:coverage # generates coverage report in frontend/coverage/
```

### 7.2 Live RBAC and honesty

```bash
pytest tests/test_scopes.py -q
pytest tests/test_honesty_live.py -q
pytest tests/test_ahp.py tests/test_constraints.py -q
```

Every `satisfied_by.endpoint` in `docs/spec/widgets.yaml` is in the 200/403
matrix (own role + admin 200; out-of-scope 403). Student lists must not include
other accounts’ usernames.

No Playwright / browser MCP in this environment. The five-role click script is
[WALKTHROUGH.md](WALKTHROUGH.md).

### 7.3 Backend API test suite (pytest)

`backend/tests/test_api.py` covers leftover US routes plus role clients.

Run inside the running container:

```bash
docker exec pathwise_backend pytest tests/test_api.py -v
```

Or locally against a running backend:

```bash
pytest backend/tests/test_api.py -v
BASE_URL=http://127.0.0.1:8000 pytest backend/tests/test_api.py -v
```

`pytest` is pinned in `backend/requirements.txt`.

On Windows, backend code changes need `docker compose restart backend` (uvicorn
`--reload` is off by default).

Older `tests/test_phase5.py` / `tests/test_integration_docker.py` still exist for
leftover US routes. They are not the Wave 8 gate.

---

## 8. Model Retraining

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

## 9. Monitoring & Drift Detection

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

The drift endpoint **leads with Ethiopia M1/M2 RMSE** against seasonal-naive
(`ethiopia` + `rmse` / `mae` on the payload). A leftover US placement-probability
window (baseline **0.88**) remains on the same response for the old XGBoost tool
and is not Ethiopia accuracy.

### What leftover US placement drift means

(Not Ethiopia accuracy.)

| Scenario | Likely cause | Action |
|---|---|---|
| Mean drops below 0.78 | Input profiles shifting toward weaker students; or model degrading | Retrain or investigate input distribution |
| Mean rises above 0.98 | Unusually strong cohort; or data quality issue | Inspect recent inputs via `/api/monitoring/predictions` |
| No predictions logged | Nobody has used the Student Evaluator yet | Normal on a fresh install |

---

## 10. Troubleshooting

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
