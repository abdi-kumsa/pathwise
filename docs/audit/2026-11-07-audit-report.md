# PathWise end-to-end audit — 7 November 2026

Branch `feedback-implementation` at commit `3cb462b`. Read-only audit: no source file was
changed. Evidence was gathered from the code, the two client feedback documents, the YAML
spec of record under `docs/spec/`, three test suites, live probes against the local Docker
stack, dependency scanners, and re-evaluation of every model artefact. Every headline
finding was reproduced twice (once by a delegated reviewer, once by hand) before it was
written here.

Companion document: [2026-11-07-improvement-plan.md](2026-11-07-improvement-plan.md).

---

## 1. Scorecard

Scores are against the rubric in section 8, so they can be re-measured after the fixes.

| Area | Weight | Score | One-line reason |
|---|---|---|---|
| Functional completeness vs spec | 20% | **82** | 44/44 DOC2 widgets exist, are wired, and return data. Three cannot be used in the browser (timeouts) and one can never render. |
| Correctness and test coverage | 15% | **70** | 1,015 tests run; every one of the 22 failures is a stale assertion from the retired US dataset. No CI, 36-minute root suite, 3 modules fail to import. |
| ML validity | 20% | **25** | Both Ethiopia learners train on leaked targets; the M1 "forecast" is the last three years replayed with zero-width intervals; all four US models lose to trivial baselines. |
| Data integrity and provenance | 10% | **60** | Every payload is honestly stamped `simulated`; ingestion contracts exist. The generator itself produces leaky, memoryless series. (Accuracy of real data is parked by agreement.) |
| Security | 15% | **58** | Strong authorization core. Four High findings: Model 3 cross-institution leak, empty-secret signing, CPU denial of service with no rate limit, demo admin password shipped in the UI and deploy config. |
| Maintainability | 10% | **65** | Clear layering, zero TODOs, good inline rationale. ~20 leftover US routes, 5 dead pages, stale TECHNICAL.md, 500 lint findings, no CI. |
| Performance and deployment readiness | 10% | **35** | Model endpoints take 5–120 s per request with no cache; single worker; dev server and root containers in compose; Postgres bound to all interfaces. |
| **Weighted overall** | | **57 / 100** | |

Reading: the platform is **structurally complete and honestly labelled**, the **access-control
design is sound**, but the **forecasting core does not forecast** and the stack is **not safe to
expose publicly** as deployed today.

---

## 2. What the system does (end to end)

PathWise is a five-role education–employment alignment platform for Ethiopia.

- **Data.** Twenty simulated fact tables under `data/ethiopia/` (2016–2025, real region, HEI
  and field names, generated values from `data/ethiopia/generate.py`). Postgres holds only
  users, audit log, scenarios, AHP matrices and expert validations. Dashboards read parquet.
- **Model 1** (`ml/model1/`): per-series OLS on lag features, then a deterministic seven-rule
  constraint layer (suspension, ESSLCE pass rate, cutoff, quota, seats, capacity, 70:30 band).
- **Model 2** (`ml/model2/`): per-series OLS on lags for employment, vacancies and skills, with
  industrial-park step adjustments.
- **Model 3** (`ml/model3/`): expected graduates vs projected vacancies, quartile severity,
  three weighted composite scores with published weights, scenario levers, pathways.
- **Methodology** (`ml/ahp/`, `ml/compare_models.py`, `ml/explain_predictions.py`): three-
  candidate comparison, coefficient and permutation importance, Saaty AHP kept separate.
- **Backend** (`backend/`): FastAPI, 117 routes, JWT HS256 with role and institution in the
  token, router-level `require_roles`, ADMIN superset, TTL-cached dataset readers, provenance
  middleware stamping every JSON object.
- **Frontend** (`frontend/`): React + Vite, 60+ pages, nav per role, route guard as usability
  only, token in `localStorage`, 60 s client timeout.
- **Deploy**: docker-compose for local (DB 5434, API 8000, UI 3001); Render free tier for
  production (shared Postgres, `pathwise` schema).

---

## 3. Does it do what the spec says?

Spec of record: `docs/spec/widgets.yaml` (44 widgets), `scopes.yaml`, `methodology.yaml`
(PROC.S1–S7, RANK.R1–R4), the two client feedback documents under `docs/feedback/`.

### 3.1 Widget coverage

| Dashboard | Widgets | Fully working | Partial | Detail |
|---|---|---|---|---|
| Student | 9 | 8 | 1 | **W.STU.02** always returns `occupations: []`, `cell_withheld: true`: each field maps to one occupation so the minimum-cell rule (5) can never pass (`backend/services/student_service.py:83`). |
| University | 10 | 8 | 2 | **W.UNI.05** program-health and **W.UNI.10** curriculum-alignment take 77 s cold, over the 60 s client timeout, so the first visit after cache expiry fails in the browser. |
| MoE | 8 | 6 | 2 | **W.MOE.05** policy-priority 15–40 s, **W.MOE.02** 38 s; two concurrent users push these over the timeout. |
| MoL | 9 | 7 | 2 | **W.MOL.09** workforce-report takes about 120 s every time (uncached) and never completes in the UI. **W.MOL.03** model2 forecast 40–90 s. |
| Admin | 8 | 8 | 0 | All sub-second except data-quality (4–7 s). |

No endpoint returned a 500 or empty rows. Every payload carries provenance and `tier:
simulated`.

### 3.2 Methodology and ranking constraints

| Rule | Verdict |
|---|---|
| PROC.S1 attribute registry | Genuine |
| PROC.S2 expert validation | Nominal: endpoint and table exist, all six rows are seeded `simulated`; no real expert input |
| PROC.S3 priority tiers | Genuine |
| PROC.S4 multi-model comparison | Present but hollow: three candidates and chronological split exist, but the winner is hard-coded and the OLS numbers are a leakage artefact (see §4) |
| PROC.S5 post-training importance | Mechanically genuine, measures the leak |
| PROC.S6 learned vs priority never merged | Genuine, test-enforced |
| PROC.S7 AHP separate | Genuine; eigenvector and CR correct, inconsistent matrices refused |
| RANK.R1–R4 | Genuine, test-enforced |

### 3.3 Scope and audit rules

| Rule | Status |
|---|---|
| SCOPE.STU.R1–R3 | Enforced; identity from JWT; crafted `?username=` ignored |
| SCOPE.UNI.R1 | **Violated on two routes**: `/api/model3/supply` and `/api/model3/gap?group_by=institution` return all 19 HEIs to a UNIVERSITY token (152 rows). `/api/model1/*` and `/api/institution/*` scope correctly. |
| SCOPE.UNI.R2 | Enforced on `/api/institution/*` (403 with grant message). `/api/model1/*` silently narrows instead of 403 (contradicts SCOPE.G3). |
| SCOPE.UNI.R3 | Code present but untestable: no seeded user has the grant and no admin endpoint can issue it |
| SCOPE.MOE.R2 | **Gap**: institution-grain reads via `/api/model1/demand/*?group_by=institution`, `/model1/funnel`, `/model1/cohort-progression` write no audit row |
| SCOPE.MOE.R3 | Partial: POST simulator audited, GET what-if not |
| SCOPE.MOL.R3 | OK |
| SCOPE.ADM.R2 | OK (self-service password change is the one unaudited mutation) |
| W.ADM.08 `query` action | **Gap**: `/api/search` never writes an audit row |

### 3.4 Test results

| Suite | Result | Verdict |
|---|---|---|
| `backend/tests/test_api.py` (in container) | 173 passed, 20 failed | All 20 failures assert retired US counts/names (33 jobs, 8 institutions, "Data Scientist", "Southern State"). Zero real regressions. |
| `tests/` root suite (36 min, live API) | 649 passed, 2 failed | Both failures assert 5 retrain steps; there are now 6. |
| `tests/test_phase4.py`, `test_phase5.py`, `test_integration_docker.py` | Fail at import | Target a retired port-8080 API |
| Frontend Vitest | 193 passed | Clean |

### 3.5 Documentation drift

`docs/TECHNICAL.md` lists about 40 of 117 routes and omits every `/api/model1|2|3`,
`/admin`, `/methodology`, `/ahp`, `/monitoring` and `/search` path. It describes the backend
suite as covering leftover routes without saying it is red. README ports, demo accounts and
role landing pages are correct.

### 3.6 Leftovers

Thirteen off-nav US routes remain in `App.jsx`; backend routers `market.py`, `enrollment.py`,
`recommendations.py` and services `market_service`, `enrollment_service`, `salary_service`,
`escape_route_service` serve them. Five pages have no route at all (`AdmissionRiskPage`,
`HiringAnalyticsPage`, `PlacementByStreamPage`, `SkillGapPage`, `RegionalOpportunityPage`).
The admin search result route `/admin/institutions?name=` does not exist (lands on 404).
TensorFlow, XGBoost and Prophet are all loaded at startup solely for the leftover routes.

---

## 4. Model audit

### 4.1 Ethiopia Model 1 (education demand)

**Verdict: the forecast is the history replayed.** Reproduced by hand.

- `generate.py:82` computes `enrollment_rolling_3y_avg` over a window that includes the
  current year, so `program_enrollment_count == 3·roll3 − lag1 − lag2` **exactly** (residual
  0.0 across all 1,520 rows). `applications_count` is drawn from the same-year enrollment
  (`generate.py:95-99`), a second leak.
- `ml/model1/layer1_demand.py:42-56` fits 5 parameters on 6 rows per series and recovers the
  identity: coefficients are `[−1, −1, +3, 0]` in 152 of 152 series, holdout RMSE 0.0.
- `_project_features` carries `roll3` forward unchanged, so step 1 = y₍T−2₎, step 2 = y₍T−1₎,
  step 3 = y₍T₎. **152/152 series' three-year forecast equals their last three observed years
  in order.**
- Prediction interval width is **0 in 456/456 rows** (`interval = ols_rmse = 0`), so the UI
  shows certainty. `seasonal_naive` is computed and discarded; `selected_model` is
  `ols_lags` in 100% of rows regardless of the comparison.
- The generator draws each year independently around a trend (detrended lag-1
  autocorrelation −0.09), so no lag model can legitimately beat trend + mean on this data.

### 4.2 Ethiopia Model 2 (labour demand)

**Verdict: employment is `last × 1.02ⁿ`; vacancies are unstable; selection is hard-coded.**

- `generate.py:244-245` sets `employment_lag_1y = emp/1.02` and `lag_2y = emp/1.05`: fake
  lags with correlation 0.011 to the true prior year and 1.0 to the target. Stored OLS RMSE
  0.28 vs naive 11,837 is this arithmetic.
- Vacancies use true shifts, and per-series OLS on 6 rows produces step-1 ratios of 0.33–2.24
  to the last value (one series clipped to zero). The stored comparison already shows
  `ols_lags` is **worse** than historical mean for growth, vacancies, occupational demand and
  skills, yet `forecast.py:72` always selects it. Skill index exceeds 1.0 in one of 24 forecasts.

### 4.3 Ethiopia Model 3 (alignment)

- `supply.py:46-48`: expected graduates = constrained intake of the **same** year × completion
  rate. No cohort lag; `time_to_graduation_years` (≈4.3) is loaded and unused.
- Units: persons vs annual vacancy postings. At national grain every field has graduates <
  vacancies (ratio 0.73–0.89); "balanced" is purely the bottom quartile of |gap| regardless
  of an 11% shortfall. At field × region grain the ratio spans 0.0–2.93, so the unit mismatch
  drives status.
- Scenario levers quota, capacity, priority fields and band shares propagate correctly.
  `placement_rule` is advertised in `LEVERS` with no implementation. 149/152 baseline rows bind
  on `esslce_eligibility`, so quota/capacity levers rarely bite.
- Composite scores correctly return weights, method and per-factor decomposition.

### 4.4 Leftover US models (re-evaluated on the original splits)

| Model | Stored claim | Measured | Trivial baseline | Verdict |
|---|---|---|---|---|
| Placement XGBoost | acc 0.882, recall 1.00 | acc **0.878**, AUC 0.715, predicts "not placed" 17/600 times | Majority class acc **0.883** | Below baseline; stored JSON is stale vs the pickle |
| Salary XGBoost | R² 0.36 | R² 0.3615 | Programme-mean lookup R² **0.374** | Below baseline |
| Enrollment LSTM | RMSE 7.88 | pooled RMSE 8.82 on 12 points, 1 year | Historical mean 9.00 | Indistinguishable from the mean; series are noise |
| Prophet demand | MAPE 3.41 | 3.41 | Seasonal naive 7.14 | "Wins" by fitting the hand-coded monthly weights that generated its own training set |

### 4.5 Explainability and monitoring

Importance for M1/M2 is computed from a pooled OLS on leaked features, so it reports the
generator's arithmetic (M1 coefficients 3/1/1/0). Drift monitoring compares the mean placement
probability of a leftover US model against a hard-coded 0.88 taken from the stale metrics
file; it cannot detect anything on the Ethiopia path. AHP is numerically correct.

### 4.6 What "accuracy" can honestly mean today

All data is a seeded simulation. The only defensible claims are: the pipeline is leak-free
(currently false), candidates are selected by backtest (currently false), skill is measured
against naive and mean baselines (present but overridden), and intervals have stated
coverage (currently zero width). Numbers become meaningful only after the same backtest runs
on official MoE / MoLS series.

---

## 5. Security findings

Scope: code review of all 17 routers and services, live probes on the local stack only,
`pip-audit` in the container, `npm audit`, Docker and Render configuration.

### 5.1 Findings

| ID | Severity | Finding | Location | Fix |
|---|---|---|---|---|
| S1 | **High** | Demo admin password `pathwise123` hard-coded in the login page, baked into the production bundle, and committed in `render.yaml`. Anyone reaching the public site can sign in as admin. | `frontend/src/pages/LoginPage.jsx:79,325`, `render.yaml:33`, `frontend/dist` | Remove quick-fill and hint from the production build (gate on `import.meta.env.DEV`); `sync: false` for `DEMO_PASSWORD`; rotate all five demo accounts on Render; require password change on first login. |
| S2 | **High** | UNIVERSITY reads every institution's constrained enrollment, completion rate and expected graduates. | `backend/routers/model3.py:25-45` | Inject the caller, apply `scope_to_institution`, reject `institution` in `group_by` without a grant; add row-content assertions to `tests/test_scopes.py`. |
| S3 | **High** | `JWT_SECRET=` (empty, as shipped in `.env.example`) signs and verifies tokens with an empty key and triggers no warning. Verified in-container. | `auth_service.py:31,417`, `.env.example:25` | `os.getenv("JWT_SECRET") or None`; refuse to start if unset or shorter than 32 bytes outside dev. |
| S4 | **High** | No rate limiting anywhere; `/api/labour/workforce-report` runs four uncached Model 2 forecasts synchronously. Two requests held the container at 120% CPU for over 10 minutes after the clients disconnected. 25 bad logins in a row returned 401 every time. | `labour.py:89`, `labour_market_service.py:372` | Cache the report payload; add `slowapi` (or proxy) limits on login, signup, report, scenarios, page-view. |
| S5 | Medium | `/api/model1/*` silently narrows a crafted `?institution=` to own rows (200) instead of 403. | `model1.py:24-33` | Route through `_institution_of()` as `institution.py` does. |
| S6 | Medium | `POST /health/reload` is unauthenticated and re-runs TensorFlow/Prophet loads when an artefact is missing. | `main.py:239` | ADMIN-only or remove. |
| S7 | Medium | Known CVEs reachable unauthenticated on the login form path: starlette 0.37.2 (multipart DoS, CVE-2024-47874 and 7 more advisories), python-multipart 0.0.9 (7 advisories), python-jose 3.3.0 (4 advisories, not reachable with HS256 but EOL-adjacent). Also scikit-learn, urllib3, setuptools, python-dotenv. | `backend/requirements.txt` | `fastapi>=0.115`, `python-multipart>=0.0.18` (ideally latest), move to PyJWT. |
| S8 | Medium | Every router returns `HTTPException(500, detail=str(exc))`, echoing internal exception text. | all routers | Global handler, generic message, `log.exception`. |
| S9 | Medium | Audit-log flooding: any authenticated user writes one row per `page-view` call; no retention. | `auth.py:168-177` | Per-user rate limit, route allow-list, retention. |
| S10 | Medium | Compose runs the Vite dev server on 0.0.0.0, both containers as root, Postgres published on 0.0.0.0:5434 with default credentials. | `docker/Dockerfile.*`, `docker-compose.yml` | Static build + nginx, `USER`, bind DB to 127.0.0.1. |
| S11 | Medium | No token revocation; role and institution changes do not take effect until expiry (7 days on Render). Only `is_active` is re-checked. | `auth_service.py:98-110`, `render.yaml` | Re-read role/institution behind the 30 s cache or add `token_version`; cut Render expiry to 8 h with refresh. |
| S12 | Low | Scenario runs via `/api/model3/scenarios` not audited; body floats unbounded (`nan`, `1e308`). | `model3.py:85-115` | Pydantic model with bounds; `log_audit`. |
| S13 | Low | `pickle.load` of repo artefacts; `data/monitoring/predictions.jsonl` is git-tracked and appended by any STUDENT via the evaluator route. | `ml_service.py:41-75`, `monitoring_service.py:113` | Pin artefact hashes or use native JSON formats; move the log out of git. |
| S14 | Low | Password policy is length ≥ 8 only; no `max_length` (1 MB password → 500); bcrypt truncates at 72 bytes; passlib is EOL. | `schemas/signup.py`, `schemas/users.py` | `max_length=72`, 422 on oversize, breached-password check, migrate to `bcrypt`/`argon2`. |
| S15 | Low | No Content-Security-Policy or HSTS; token in `localStorage` (no XSS sink found today). | `main.py:46-52`, `client.js:5` | Add both headers; consider httpOnly cookie + CSRF token. |
| S16 | Low | Admin audit filter accepts LIKE wildcards (`?actor=%25`); parametrised, not injection. | `admin_service.py:279` | Escape `%` and `_`. |
| S17 | Info | `/docs` and `/openapi.json` public; `PYTHON_VERSION 3.11.0` in `render.yaml` vs `.python-version 3.11.9`; username enumeration via signup 409. | `main.py:17`, `render.yaml:16` | `docs_url=None` outside dev; align versions. |

Frontend `npm audit`: 15 advisories (10 high). Runtime-relevant for the static build: `axios`
(upgrade). `react-router` CSRF applies to RSC mode only. The rest (vite launch-editor, postcss,
browserslist, nanoid, undici, vitest) are build/dev-only, except that the compose stack ships
the dev server, which makes the vite advisory live there.

### 5.2 What is already good

- Role guards are declared once per router, so a new route cannot be added unguarded; ADMIN
  superset is centralised.
- Institution and student identity come from the signed JWT; `alg=none` and wrong-secret
  tokens are rejected; CORS is an explicit allow-list and does not reflect.
- Cross-institution access needs a DB-side grant re-read per request and audited; last-admin,
  self-demote and self-delete guards live in the service layer.
- Login is uniform across unknown user / wrong password / disabled; bcrypt hashing; hashes
  opt-in in serialisation; DB outage surfaces as 503.
- All DB access is through the ORM; the only raw SQL is static DDL; YAML is `safe_load`; no
  `dangerouslySetInnerHTML`, `innerHTML` or `eval` in the React code.
- `tests/test_scopes.py` asserts 200/403 across five roles for about 40 endpoints and passes.

---

## 6. Performance

Measured against the local stack twice: once with the API idle, once while three reviewers
were querying it concurrently (a realistic two-to-three-user load). The frontend client
timeout is 60 s.

| Endpoint | Role | Idle | Under 3 concurrent users | Cached? |
|---|---|---|---|---|
| `/api/labour/workforce-report` | MoL | 25 s | ~120 s, every call | No |
| `/api/model2/forecast?horizon=3` | MoL | 7.7 s | 40–90 s | No |
| `/api/institution/program-health` | University | 6.4 s | 77 s cold / 15 s warm | Partially |
| `/api/institution/curriculum-alignment` | University | 6.4 s | 77 s cold / 28 s warm | Partially |
| `/api/institution/demand-vs-labour` | University | – | 37 s | No |
| `/api/model3/policy-priority` | MoE | 3.9 s | 15–40 s | No |
| `/api/model3/gap` | MoE | 3.2 s | 8 s | No |
| `/api/model1/demand/constrained` | MoE | 3.0 s | 5 s | No |
| `/api/student/alternatives` | Student | 2.7 s | 13–34 s | No |
| `/api/education/overview`, `/api/labour/overview` | MoE / MoL | 20 ms warm | 0.5–16 s cold | Yes (TTL 300 s) |

Two conclusions. First, even idle, no model widget meets a 5 s target and the workforce
report is 25 s. Second, latency multiplies roughly tenfold with two or three simultaneous
users, pushing five widgets past the 60 s client timeout. Cause: every Model 1/2/3 request
re-fits up to 152 + 112 + 24 per-series regressions and rebuilds the constraint layer. The
`ttl_cache` decorator exists and is used by the legacy services but by none of
`constraint_service`, `model2_service`, `alignment_service` or `student_service`. Single
uvicorn worker; CPU-bound sync handlers serialise on the GIL. Sync handlers also keep running
after the client disconnects, which is what turned S4 into a sustained CPU pin.

---

## 7. Traces left by this audit (local Docker only)

- `data/monitoring/predictions.jsonl` (git-tracked) gained rows from probe calls to the
  placement evaluator. Restore with `git checkout -- data/monitoring/predictions.jsonl`.
- Accounts `audit_probe_x1` and `audit_probe_x2` were created by signup probes and are
  **deactivated**; hard-delete via `DELETE /api/users/{name}/permanent` as admin.
- Accounts `testuser` … `testuser5` pre-date this audit.
- Two scenario rows created by a reviewer were deleted. `pip-audit` and `ruff` were installed
  inside the running backend container (not in the image).

---

## 8. Rubric

Each area is scored 0–100 on the listed criteria; the weighted sum is the overall.

| Area | Criteria |
|---|---|
| Functional completeness (20) | Every spec widget has endpoint, page, nav, returns data (60); usable within client timeout under two concurrent users (25); no stub or placeholder content (15) |
| Correctness and tests (15) | Suites green (40); tests describe the current product (20); CI runs them (20); unit tests runnable without the live stack in < 5 min (20) |
| ML validity (20) | No target leakage (30); selection by out-of-sample error vs ≥ 2 baselines (25); honest intervals with measured coverage (15); units and timing consistent across models (15); importance and monitoring on the served models (15) |
| Data integrity (10) | Provenance on every figure (40); ingestion contracts validated (25); generator produces realistic dependence structure (35) |
| Security (15) | No High findings (40); no Medium (25); dependencies clean (15); infra hardening (20) |
| Maintainability (10) | Dead code removed (30); docs match code (30); lint clean (20); structure and comments (20) |
| Performance and deployment (10) | p95 < 5 s for every widget (50); multi-worker or precomputed (20); production-grade containers (30) |
