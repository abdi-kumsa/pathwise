# PathWise improvement plan — phased

Derived from [2026-11-07-audit-report.md](2026-11-07-audit-report.md). Ordered by risk: what
is unsafe first, what is misleading second, what is slow third, what is unfinished last.
Effort: S = under a day, M = 1–3 days, L = a week or more. Every item has an acceptance check
so the phase can be signed off rather than declared done.

Data accuracy (official MoE / MoLS / ESS series) is deliberately out of scope here and is
tracked as Phase 5 so the hooks for it are visible.

Target scores after each phase use the rubric in the audit report (current overall: 57).

---

## Phase 0 — Stop the bleeding (1–2 days, do before anything else is shared)

Goal: the public deployment is no longer trivially compromised or trivially knocked over.
Target: Security 58 → 75.

**Status (2026-11-07): implemented and verified locally, uncommitted.** Regression tests:
`tests/test_phase0_security.py` (live + memo) and `backend/tests/test_phase0_unit.py`
(container). Notes on what differs from the table below:

- 0.1 done in code. **Still to do by hand on Render:** set `DEMO_PASSWORD` in the dashboard
  and reset the five existing accounts through the admin console, because the seeder never
  overwrites existing users. Outside `ENV=dev` the seeder now refuses the published password.
- 0.4 caches at the ML layer (`ml/_memo.py`, 30-minute TTL, per-key lock, copy on return)
  plus a background prewarm at startup. Warm widget latency is now 30–170 ms; the workforce
  report is 30 ms warm and about 11 s on the very first cold call.
- 0.5 is an in-process limiter (`backend/services/rate_limit.py`), not `slowapi`, valid while
  the API runs one worker. Login throttles failed attempts per IP and username; signup
  counts only requests that pass validation.
- 0.7 went to FastAPI 0.162 / Starlette 1.10 (the remaining Starlette advisories needed
  1.3.1+), so startup moved to a lifespan handler. Frontend `npm audit` is 0 for runtime and
  dev. Backend `pip-audit` still lists TensorFlow/Prophet transitive packages, `pyarrow`,
  `fpdf2` and `scikit-learn`; most disappear with Phase 1.4. The running container still has
  `python-jose` installed until the image is rebuilt.
- Rebuild the backend image (`docker compose build backend`) so the container matches
  `backend/requirements.txt`; the local container was upgraded in place for testing.

| # | Item | Effort | Acceptance |
|---|---|---|---|
| 0.1 | Remove the demo password hint and quick-fill from production builds (`LoginPage.jsx:79,325`, gate on `import.meta.env.DEV`); set `DEMO_PASSWORD` to `sync: false` in `render.yaml`; rotate all five demo accounts on Render. | S | `grep pathwise123 frontend/dist` returns nothing; Render login with the old password fails. |
| 0.2 | Scope `/api/model3/supply` and `/api/model3/gap` to the caller's institution for UNIVERSITY; reject `institution` in `group_by` without a grant. | S | New test in `tests/test_scopes.py` asserts a UNIVERSITY token sees exactly one `institution` value in the rows. |
| 0.3 | JWT secret fail-fast: treat empty as unset; refuse to start outside `ENV=dev` if the key is missing or under 32 bytes. Remove the `JWT_SECRET=` line from `.env.example` in favour of the generate command. | S | Container with `JWT_SECRET=` exits with a clear error. |
| 0.4 | Cache `workforce_report` and the Model 1/2/3 service entry points with the existing `ttl_cache` (keyed on horizon and levers); render exports from the cached payload. | S | `/api/labour/workforce-report` second call < 1 s; all model widgets < 5 s warm. |
| 0.5 | Rate limiting (`slowapi`): login 10/min/IP, signup 5/min/IP, report and scenario POSTs 10/min/user, page-view 60/min/user. | S | 11th bad login in a minute returns 429. |
| 0.6 | Require ADMIN on `POST /health/reload`. | S | Anonymous POST returns 401. |
| 0.7 | Bump `fastapi` ≥ 0.115 (starlette ≥ 0.40), `python-multipart` ≥ 0.0.18, `axios` latest; replace `python-jose` with `PyJWT`. | S | `pip-audit` and `npm audit --omit=dev` report no High on runtime packages. |
| 0.8 | Generic 500 handler; log the exception, never echo `str(exc)`. | S | Forced exception returns `{"detail":"Internal error","ref":"<id>"}`. |

---

## Phase 1 — Stabilise and clean (week 1–2)

Goal: the test suites describe the current product, run in CI, and the repo contains only
what ships. Target: Correctness 70 → 88, Maintainability 65 → 80, Functional 82 → 90.

**Status (2026-11-08): implemented and verified locally, uncommitted.** All suites green on
a freshly built image: backend 158 passed (56 legacy-route tests skipped while the flag is
off), root 669 passed in under 4 minutes (was 36), frontend 162 passed, ruff clean, route
table check passes. Notes on what differs from the table below:

- 1.1 The four `test_xgboost/shap/lstm/prophet.py` files were also script-style (checks ran
  at import, no pytest tests, TensorFlow loaded during every collection). All seven US-era
  scripts are in `archive/legacy_tests/` with a README. Frontend tests for the six deleted
  dead pages went with them (193 → 162).
- 1.3 Workflow written (`.github/workflows/ci.yml`, four jobs). **Not yet run on GitHub**:
  nothing is pushed. Branch protection on `main` is a GitHub setting you enable.
- 1.4 Flag `LEGACY_US_MODELS` (backend) / `VITE_LEGACY_US_MODELS` (build), default off.
  TensorFlow, Prophet, XGBoost and SHAP moved to `backend/requirements-legacy.txt`;
  backend image 4.9 GB → 1.53 GB; API healthy in ~11 s. The ten off-nav pages that read
  Ethiopia data stay (search links to them). The career explorer no longer claims to be
  "personalised" when no model used the profile.
- 1.5 The minimum cell size is applied to each row's count, not to the number of rows.
- 1.7 Also: the policy simulator is debounced, because each settled what-if is now audited
  and rate limited.
- 1.8 Grant/revoke via `PATCH /api/users/{u}` and an admin-console button, with dedicated
  `cross_institution_grant` / `_revoke` audit actions. No dev user is pre-seeded with the
  grant; the live test grants and revokes it.
- 1.9 Also closed a related leak: a UNIVERSITY grouping that omitted `institution` summed
  every HEI before scoping. Its groupings now always keep `institution`.
- 1.10 `scripts/gen_route_table.py` writes the table (99 operations with role guards) and
  `--check` runs in CI.
- 1.11 Lint is for bugs (`ruff.toml`: E9, F, B), not style; all findings fixed. Import
  sorting and syntax modernisation were left out on purpose to keep the diff reviewable.
  `B904`/`B905` are ignored with reasons in the config.
- 1.12 72-byte cap, common-password deny-list, at-least-three-distinct-characters rule;
  passlib removed in favour of `bcrypt`. Existing hashes still verify.
- Rate limits were retuned while testing: login and password change count only *failed*
  attempts, and signup allows 20/min per IP, because a class registering from one campus
  network shares an IP. Admin reactivation or password reset clears an account's lockout.

| # | Item | Effort | Acceptance |
|---|---|---|---|
| 1.1 | Rewrite the 20 stale assertions in `backend/tests/test_api.py` and the 2 in `tests/test_phase7.py` against the Ethiopia dataset; delete or fix `test_phase4.py`, `test_phase5.py`, `test_integration_docker.py`. | M | Both suites green. |
| 1.2 | Split tests into unit (no live API, < 5 min) and live (opt-in via `BASE_URL`). | M | `pytest -m "not live"` < 5 min with no Docker. |
| 1.3 | GitHub Actions: ruff, pytest unit, vitest, `pip-audit`, `npm audit --omit=dev`, Docker build. Branch protection on `main`. | M | A PR with a failing test cannot merge. |
| 1.4 | Remove or quarantine the US leftovers behind a feature flag off by default: 13 routes in `App.jsx`, `market.py`, `enrollment.py`, `recommendations.py`, the 5 dead pages, `salary_service`, `escape_route_service`, and the TensorFlow / Prophet / XGBoost pre-warm. Keep artefacts in `archive/`. | M | Backend starts without importing TensorFlow; image size and cold start drop; `test_spec_coverage` still 44/44. |
| 1.5 | Fix W.STU.02: release the occupation panel at field level (the rule protects persons, not occupation labels) or map fields to several occupations. | S | `/api/student/labour-outlook` returns ≥ 1 occupation for every field. |
| 1.6 | Fix the admin search route (`/admin/institutions?name=` does not exist) and URL-encode search labels. | S | Clicking any search result lands on a real page. |
| 1.7 | Audit gaps: `log_audit` on `/api/model1/*` institution-grain reads for MOE, on `/api/search` (`query`), on `/api/model3/scenarios` POST, on GET policy-simulator what-ifs, on self-service password change. | S | Each action appears in `/api/admin/audit-log`. |
| 1.8 | Add an admin endpoint and UI toggle for the `cross_institution` grant so SCOPE.UNI.R2/R3 are exercisable; seed one granted user in dev. | S | Live test: granted user gets 200 + audit row; ungranted gets 403. |
| 1.9 | `/api/model1/*` returns 403 on a crafted `?institution=` (SCOPE.G3) instead of silently narrowing. | S | Test asserts 403. |
| 1.10 | Regenerate `docs/TECHNICAL.md` route table from OpenAPI; note suite runtimes; drop the US references. | S | Every path in `/openapi.json` appears in the doc. |
| 1.11 | `ruff --fix` the 200 auto-fixable findings; add `ruff` and `oxlint` to pre-commit. | S | Lint clean in CI. |
| 1.12 | Password policy: `max_length=72`, 422 on oversize, breached-password list check for admin-provisioned accounts; migrate passlib → `bcrypt` direct. | S | 1 MB password returns 422. |

---

## Phase 2 — Make the models honest (week 2–5)

Goal: the forecasting core forecasts, selection is by evidence, and every number on screen
has an interval with known coverage. Target: ML validity 25 → 70, Data integrity 60 → 75.

**Status (2026-11-08): implemented and verified locally, uncommitted.** Tests:
`tests/test_phase2_models.py` (35), plus updated model tests. Differences from the table:

- 2.1 Lags are true shifts and rolling means cover prior years only; series are AR(1)
  around per-series trends. The pooled AR estimate on 10-year series is ~0.38 for
  enrolment and employment (the plan's 0.4–0.8 target assumed longer series; short
  series bias the estimate down). WV.OLS1 is retired.
- **Bigger than planned:** Layer 1 now forecasts *applications* (demand), not enrolment.
  Forecasting observed enrolment and then applying the constraint layer applied every
  rule twice: 149/152 series bound on exam eligibility and constrained enrolment was ~60%
  of reality. Now 452/456 bind on available seats and the constrained forecast is 94% of
  actual enrolment.
- 2.2–2.5 One engine (`ml/forecasting.py`) for all targets: four candidates, rolling-origin
  backtest (origins 2019–2024, horizons 1–5), lowest-RMSE candidate per horizon, intervals
  from that candidate's residuals with leave-one-origin-out coverage (88–90% for M1/M2 at
  90% nominal). Selection is per target and horizon, not per series: four backtest points
  per series would overfit.
- 2.6 Recursive projection replaced by direct per-horizon forecasts; no series replays history.
- 2.7 Graduates follow cohorts (intake of P − time-to-graduation × completion). Status is
  coverage-based (0.85 / 1.15); severity stays quartile (RANK.R4).
- 2.8 `placement_rule` shifts the ESSLCE pass rate (±15 pp); bodies are validated models.
- 2.10 Importance is computed on the pooled model with model-based, exact linear SHAP and
  permutation methods. 2.11 Drift: PSI of year-on-year change plus error drift per target;
  the hard-coded 0.88 baseline is gone.
- 2.13 Every forecast page carries the accuracy note; Model 1/2 APIs carry an `accuracy` block.
- Also fixed: Model 2 absorption now scales with the employment forecast; NaN metrics no
  longer break JSON; generated docs (`scripts/model_report.py`) are checked in CI.

Order matters: 2.1 is a prerequisite for everything after it.

| # | Item | Effort | Acceptance |
|---|---|---|---|
| 2.1 | **Fix the generator.** `enrollment_rolling_3y_avg` from `shift(1).rolling(3)`; `employment_lag_*` from true group shifts; applications drawn from the *previous* year's intake plus noise; replace i.i.d. draws with an AR(1) / local-linear-trend process (φ ≈ 0.6–0.8) with shocks that persist. Regenerate parquets and CSVs. | L | Tests: `corr(lag1, true shift) == 1`; detrended lag-1 autocorrelation in [0.4, 0.8]; `ols_lags` holdout RMSE > 0. Retire waiver WV.OLS1. |
| 2.2 | **Rolling-origin backtest** replacing the single last-2-years fold: origins 2020–2023 × horizons 1–3, per target, ≥ 3 candidates including seasonal-naive and historical mean. Store per-horizon error. Expose on `/api/methodology/model-comparison`. | M | JSON contains error per (target, candidate, horizon, origin). |
| 2.3 | **Pooled estimator** as a candidate: ridge (or GBM) with series fixed effects and trend, minimum 5 years to be eligible; ETS per series once autocorrelation exists. Baseline measurement on current data: per-series OLS 104/280 RMSE at h=1/2 vs pooled ridge 49/48 vs historical mean 54/56. | M | Pooled beats both baselines at h = 1..3 on ≥ 2 origins. |
| 2.4 | **Data-driven selection** per series and target in `layer1_demand.py` and `forecast.py`: argmin of backtest error; store the chosen name and its error on every row; remove the hard-coded `ols_lags`. | S | On current data `historical_mean` wins M1 and M2 vacancies/growth, and the API says so. |
| 2.5 | **Honest intervals** from empirical residual quantiles per horizon from 2.2; never training RMSE; never zero. | S | Reported coverage per horizon ≥ 80% on the backtest; zero rows with width 0. |
| 2.6 | Fix M1 projection: recompute rolling features from the forecast path at each step; drop `applications_count` as a same-year regressor. | S | 3-step forecast no longer equals the last three observed years. |
| 2.7 | Model 3 timing and units: lag graduates by `time_to_graduation_years` with cohort progression (2026 supply = 2022 intake × completion); express demand as annual openings per field or label both axes as a simulated index; make status depend on coverage thresholds (e.g. < 0.85 shortage, > 1.15 oversupply) with quartile severity secondary. | M | National-grain status is not uniform; a unit test checks a known cohort lag. |
| 2.8 | Scenario engine: implement `placement_rule` (alter the cutoff / pass-rate frames) or remove it from `LEVERS`; bound all lever floats with a Pydantic model. | S | Lever changes a result or is gone; `nan` rejected with 422. |
| 2.9 | Bound the skill-shortage index to [0, 1]; clip negative vacancy forecasts before they reach the UI with an explicit flag. | S | No forecast outside its domain. |
| 2.10 | Importance on the right things: permutation importance on the *selected* pooled model over the backtest holdout; SHAP for the GBM candidate; drop |coef| on unscaled features. AHP stays in its own panel. | S | `/api/methodology/feature-importance` cites the model and fold it came from. |
| 2.11 | Monitoring on the Ethiopia path: PSI / KS on inputs per model, backtest error refreshed when a new year lands, alert thresholds. Remove the hard-coded 0.88 placement baseline. | M | `/api/monitoring/drift` reports per-model input drift and last backtest error. |
| 2.12 | Retire the US artefacts (placement below majority baseline, salary below programme mean, LSTM ≈ mean, Prophet fits its own generator) or retrain on `graduate_outcomes` and relabel. If retained for demo: `scale_pos_weight`, PR-AUC, threshold chosen on validation, regenerate `model_metrics.json` from the actual pickle. | S–M | Either no US route exists or every US metric in the UI matches a re-run. |
| 2.13 | Add a plain-language "what accuracy means here" note to every forecast page: seeded simulation; errors measure recovery of the generator's process; claims limited to leak-free, backtest-selected, baseline-beating, interval-covered. | S | Note present; `test_honesty_live` asserts it. |

---

## Phase 3 — Performance and production shape (week 5–7)

Goal: every widget under 5 s for the 95th percentile with several concurrent users, and
containers that are safe to expose. Target: Performance/deployment 35 → 80.

**Status (2026-11-08): implemented and verified locally, uncommitted.** Load test
(`scripts/load_test.py`, all 44 widget endpoints): worst p95 2.3 s with 10 concurrent users.

- 3.1 Precomputation is the in-memory forecast memo plus a background prewarm (~8 s after
  start), not a file store; it meets the target without stale-file risk.
- 3.2 Not needed: with the payload cached, CSV/XLSX/PDF exports take ≤ 0.32 s.
- 3.3 Kept to one worker on purpose: the rate limiter and memo are per process, and Render's
  free tier has 512 MB. Multi-worker needs a shared store first (Redis).
- 3.4 Production frontend image (nginx, unprivileged, CSP/HSTS) built and checked; backend
  runs as uid 10001; dev ports bound to 127.0.0.1; `docker-compose.prod.yml` requires every
  secret; API refuses the default DB password outside dev. The prod compose stack has not
  been run end to end.
- 3.5 API: strict CSP, no-store, HSTS outside dev, docs off outside dev. Render static
  headers added; Node raised to 22 (Vite 8 needs it) and `npm ci`.
- 3.6 Token version per account; role and institution read per request; refresh endpoint and
  client renewal; password changes end other sessions.
- 3.7 Audit retention (365 days, daily, audited), page-view allow-list, literal LIKE
  filters, true `total`.
- 3.8 SHA-256 manifest verified before every pickle / Keras load; prediction log untracked.

| # | Item | Effort | Acceptance |
|---|---|---|---|
| 3.1 | Precompute Model 1/2/3 outputs at startup and after retrain into a forecast store (parquet or JSON under `ml/models/forecasts/`); request path reads the store; scenarios compute deltas against it. | M | Any widget p95 < 2 s idle; < 5 s with 5 concurrent users (`locust` or `hey` script in `scripts/`). |
| 3.2 | Long computations (workforce report export, scenario runs) as background jobs with a job id and polling endpoint; client shows progress instead of a 60 s spinner. | M | Export returns 202 then a download link. |
| 3.3 | Run uvicorn with workers (`--workers 2–4`) or gunicorn; make heavy handlers `async` with `run_in_threadpool` and cancel on disconnect. | S | CPU returns to idle within 5 s of client disconnect. |
| 3.4 | Production containers: static Vite build served by nginx (no dev server); `USER` in both Dockerfiles; read-only bind mounts or none; Postgres bound to `127.0.0.1:5434`; non-default DB credentials required. | M | `docker exec … id` ≠ root; `docker port pathwise_db` shows 127.0.0.1. |
| 3.5 | Security headers: `Strict-Transport-Security` in production, `Content-Security-Policy` (`default-src 'self'; connect-src <API>`); `docs_url=None` outside dev. | S | Headers present on Render; `/docs` 404 in prod. |
| 3.6 | Session hardening: re-read role and institution behind the existing 30 s cache (or `token_version` column); Render expiry 8 h with a refresh endpoint; optional httpOnly cookie + CSRF token. | M | Demoting a user takes effect within 30 s. |
| 3.7 | Audit log retention and partitioning; `page-view` allow-list of known routes. | S | Rows older than policy are archived; unknown paths are not stored. |
| 3.8 | Artefact integrity: SHA-256 manifest verified before any `pickle.load`; prefer XGBoost JSON and Prophet `model_to_json`; move `predictions.jsonl` out of git and the bind mount. | S | Startup fails on a tampered artefact; `git status` stays clean under use. |
| 3.9 | Align `PYTHON_VERSION` in `render.yaml` with `.python-version`; document Render cold-start behaviour or move to a paid instance for the demo window. | S | Render build log shows 3.11.9. |

---

## Phase 4 — Governance and readiness for real data (week 7–9)

Goal: the methodology steps that are currently nominal become real, and the ingestion path
is proven end to end with at least one official-shaped file. Target: overall ≥ 85.

**Status (2026-11-08): software done, inputs pending.**

- 4.1 Reviews need the expert's name and organisation and a valid DOC1 id; seeded rows are
  flagged by a column, never count, and can be cleared; coverage and CSV export in the
  admin page. **No real review is recorded**: that needs your reviewers.
- 4.2 Pairwise grid editor with live CR on the full Saaty scale; the server now also
  rejects non-reciprocal matrices.
- 4.3 `scripts/ingest_official.py` (dry run by default) validates, key-checks, runs the
  consistency rules, stamps provenance, reconciles against the simulation and re-runs the
  backtest. Proven on official-*shaped* fixtures; **no official file has been ingested.**
- 4.4 `docs/DATA_GOVERNANCE.md`; draft/rejected scenarios purge after 180 days.
- 4.5 Re-score: `docs/audit/2026-11-08-rescore.md`.

| # | Item | Effort | Acceptance |
|---|---|---|---|
| 4.1 | Expert validation workflow (PROC.S2): invite flow, per-domain reviewer accounts, sign-off state, export of the validated attribute list. Replace the six seeded rows. | M | At least one non-seeded validation per domain, or a documented plan with named reviewers. |
| 4.2 | AHP in the admin UI: pairwise matrix editor, live CR, refusal above 0.1, side-by-side with learned importance (never merged). | M | Admin can produce and save weights; `test_learned_and_priority_never_merged` still passes. |
| 4.3 | Official-file dry run: take one real public table (e.g. an MoE enrollment summary), map it through `docs/spec/ingestion/<table>.md`, validate with `_validate.py`, restamp `tier: official`, and watch the backtest numbers change. | M | One series in the UI shows `official`; the model comparison for it is re-run. |
| 4.4 | Retention, export and erasure policies for users, audit log, scenarios; admin UI for them. | S | Documented in `docs/`, enforced by a scheduled job. |
| 4.5 | Re-run this audit's rubric and security probes; publish the delta. | S | New scorecard in `docs/audit/`. |

---

## Phase 5 — Data accuracy track (parked, to be scoped separately)

**Status (2026-11-08): groundwork done; scoping in `docs/DATA_ACCURACY_PLAN.md`.**
13 cross-table consistency rules (`ml/consistency.py`) feed the data-quality page and block
bad official files. They caught a real generator error on first run: cohort rates summed
past 100% in 947 of 1,520 rows (fixed). The agreements, files and reviewers are yours.

Placeholder so the dependencies are visible. Everything in Phase 2 is designed so that
replacing a parquet with an official file re-runs the same backtest and re-stamps the
provenance, which is the only way the "accuracy" figures become meaningful. Items to scope
when this is discussed: source agreements with MoE EMIS, MoLS and ESS; table-by-table
priority (Tier 1 first: enrollment history, admissions funnel, exam placement, quota,
labour history, sector output, formal/informal); reconciliation rules; vintage tracking;
back-casting the simulated years.

---

## Suggested sequencing and effort

| Phase | Calendar | Rough effort | Score after |
|---|---|---|---|
| 0 | Days 1–2 | 2 dev-days | ~62 |
| 1 | Weeks 1–2 | 8 dev-days | ~70 |
| 2 | Weeks 2–5 | 15 dev-days | ~80 |
| 3 | Weeks 5–7 | 8 dev-days | ~86 |
| 4 | Weeks 7–9 | 8 dev-days | ~90 |

Phases 1 and 2 can run in parallel if two people are available: one on tests, CI and
cleanup, one on the generator and models. Phase 3's forecast store (3.1) depends on Phase 2's
selection logic being final, so start it in week 4 at the earliest.
