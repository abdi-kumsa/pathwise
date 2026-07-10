"""
Phase 6 -- Full-Stack Integration Smoke Test
Tests the entire stack running inside Docker Compose:
  - Postgres (5432) -- schema seeded
  - FastAPI backend (8000) -- all models loaded
  - React frontend (3000) -- Vite dev server reachable

Sections:
  I   Health       -- /health on backend; React HTML on frontend
  II  Market       -- all 7 GET market endpoints
  III Enrollment   -- 5 GET enrollment endpoints
  IV  Prediction   -- POST predict-placement + GET skill-recommendations
  V   Parameters   -- months / n / years / limit forwarding
  VI  Performance  -- warm response-time budget (< 500 ms)
  VII Data         -- cross-endpoint consistency

Run after: docker compose up -d
    python tests/test_integration_docker.py

Override service URLs via environment variables:
    BACKEND_URL=http://127.0.0.1:8000
    FRONTEND_URL=http://127.0.0.1:3000
"""

import os
import sys
import time
import requests

# Ensure UTF-8 output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND  = os.getenv("BACKEND_URL",  "http://127.0.0.1:8000")
FRONTEND = os.getenv("FRONTEND_URL", "http://127.0.0.1:3000")

PASS = "\033[32m  [PASS]\033[0m"
FAIL = "\033[31m  [FAIL]\033[0m"
SECT = "\033[36m"
ENDC = "\033[0m"

passed = 0
failed = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"{PASS}  {label}" + (f"  |  {detail}" if detail else ""))
    else:
        failed += 1
        print(f"{FAIL}  {label}" + (f"  |  {detail}" if detail else ""))


def section(title: str) -> None:
    print(f"\n{SECT}{'=' * 66}")
    print(f"  {title}")
    print(f"{'=' * 66}{ENDC}")


def get(path: str, **kwargs) -> requests.Response:
    return requests.get(BACKEND + path, timeout=30, **kwargs)


def post(path: str, **kwargs) -> requests.Response:
    return requests.post(BACKEND + path, timeout=30, **kwargs)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

STRONG_STUDENT = {
    "gpa": 3.9, "internships": 4, "projects": 5,
    "communication_score": 9, "program": "MS Data Science",
}

WEAK_STUDENT = {
    "gpa": 2.3, "internships": 0, "projects": 1,
    "communication_score": 3, "program": "Certificate Data Analytics",
}


# =============================================================================
# Section I -- Health Checks
# =============================================================================

section("I -- Health Checks")

# Backend /health
try:
    r = requests.get(BACKEND + "/health", timeout=15)
    body = r.json()
    check("Backend /health returns 200",        r.status_code == 200)
    check("Response has 'status' field",         "status" in body)
    check("Response has 'models' field",         "models" in body)
    models = body.get("models", {})
    check("XGBoost reported as loaded",          models.get("xgboost") is True,
          f"got {models.get('xgboost')}")
    check("LSTM reported as loaded",             models.get("lstm") is True,
          f"got {models.get('lstm')}")
    check("Prophet reported as loaded",          models.get("prophet") is True,
          f"got {models.get('prophet')}")
    check("SHAP cache reported as loaded",       models.get("shap") is True,
          f"got {models.get('shap')}")
except Exception as exc:
    check("Backend /health reachable", False, str(exc))
    print("\n  [FATAL] Backend not reachable. Is `docker compose up` running?")
    sys.exit(1)

# Backend /docs (Swagger UI)
try:
    r = requests.get(BACKEND + "/docs", timeout=10)
    check("Backend /docs (Swagger UI) returns 200", r.status_code == 200)
except Exception as exc:
    check("Backend /docs reachable", False, str(exc))

# Frontend
try:
    r = requests.get(FRONTEND, timeout=15)
    check("Frontend returns 200",                r.status_code == 200,
          f"status={r.status_code}")
    check("Frontend serves HTML",               "text/html" in r.headers.get("content-type", ""),
          r.headers.get("content-type"))
    check("Frontend HTML contains 'PathWise'",  "PathWise" in r.text or "pathwise" in r.text.lower())
except Exception as exc:
    check("Frontend reachable", False, str(exc))


# =============================================================================
# Section II -- Market Demand Endpoints
# =============================================================================

section("II -- Market Demand Endpoints (all 7 routes)")

# /api/market/overview
r = get("/api/market/overview")
check("GET /api/market/overview       -- 200",          r.status_code == 200)
body = r.json()
check("overview.total_companies       -- int",          isinstance(body.get("total_companies"), int))
check("overview.total_placements      -- int",          isinstance(body.get("total_placements"), int))
check("overview.avg_salary            -- numeric",      isinstance(body.get("avg_salary"), (int, float)))
check("overview.avg_time_to_hire      -- numeric",      isinstance(body.get("avg_time_to_hire"), (int, float)))
check("overview.top_role              -- str",          isinstance(body.get("top_role"), str))

# /api/market/top-companies
r = get("/api/market/top-companies")
check("GET /api/market/top-companies  -- 200",          r.status_code == 200)
companies = r.json()
check("top-companies returns list",                     isinstance(companies, list) and len(companies) > 0)
if companies:
    c = companies[0]
    check("company[].company -- str",                   isinstance(c.get("company"), str))
    check("company[].count   -- int",                   isinstance(c.get("count"), int))

# /api/market/regional-hiring
r = get("/api/market/regional-hiring")
check("GET /api/market/regional-hiring -- 200",         r.status_code == 200)
regions = r.json()
check("regional-hiring returns list",                   isinstance(regions, list) and len(regions) > 0)
if regions:
    check("region[].location -- str",                   isinstance(regions[0].get("location"), str))
    check("region[].count    -- int",                   isinstance(regions[0].get("count"), int))

# /api/market/job-internship-ratio
r = get("/api/market/job-internship-ratio")
check("GET /api/market/job-internship-ratio -- 200",    r.status_code == 200)
body = r.json()
check("ratio.job_count        -- int",                  isinstance(body.get("job_count"), int))
check("ratio.internship_count -- int",                  isinstance(body.get("internship_count"), int))
check("ratio.ratio            -- numeric",              isinstance(body.get("ratio"), (int, float)))

# /api/market/skill-gap
r = get("/api/market/skill-gap")
check("GET /api/market/skill-gap       -- 200",         r.status_code == 200)
body = r.json()
skills = body.get("skills", [])
check("skill-gap.skills list non-empty",                len(skills) > 0)
check("skill-gap.top_gap_skill -- str",                 isinstance(body.get("top_gap_skill"), str))
check("skill-gap.avg_gap_score -- numeric",             isinstance(body.get("avg_gap_score"), (int, float)))
if skills:
    s = skills[0]
    check("skill[].skill              -- str",          isinstance(s.get("skill"), str))
    check("skill[].demand_score       -- numeric",      isinstance(s.get("demand_score"), (int, float)))
    check("skill[].curriculum_coverage -- numeric",     isinstance(s.get("curriculum_coverage"), (int, float)))
    check("skill[].gap_score          -- numeric",      isinstance(s.get("gap_score"), (int, float)))

# /api/market/hiring-sources
r = get("/api/market/hiring-sources")
check("GET /api/market/hiring-sources  -- 200",         r.status_code == 200)
sources = r.json()
check("hiring-sources returns list",                    isinstance(sources, list) and len(sources) > 0)
if sources:
    check("source[].source -- str",                     isinstance(sources[0].get("source"), str))
    check("source[].count  -- int",                     isinstance(sources[0].get("count"), int))

# /api/market/demand-forecast
r = get("/api/market/demand-forecast")
check("GET /api/market/demand-forecast -- 200",         r.status_code == 200)
fc = r.json()
check("demand-forecast returns 12 points",              isinstance(fc, list) and len(fc) == 12)
if fc:
    pt = fc[0]
    check("forecast[].month              -- str",       isinstance(pt.get("month"), str))
    check("forecast[].predicted_postings -- numeric",   isinstance(pt.get("predicted_postings"), (int, float)))
    check("forecast[].lower_bound        -- numeric",   isinstance(pt.get("lower_bound"), (int, float)))
    check("forecast[].upper_bound        -- numeric",   isinstance(pt.get("upper_bound"), (int, float)))


# =============================================================================
# Section III -- Enrollment Intelligence Endpoints
# =============================================================================

section("III -- Enrollment Intelligence Endpoints")

# /api/enrollment/summary
r = get("/api/enrollment/summary")
check("GET /api/enrollment/summary         -- 200",     r.status_code == 200)
summary = r.json()
check("summary.total_students    -- int",               isinstance(summary.get("total_students"), int))
check("summary.total_programs    -- int",               isinstance(summary.get("total_programs"), int))
check("summary.avg_placement_rate -- numeric",          isinstance(summary.get("avg_placement_rate"), (int, float)))
check("summary.top_program       -- str",               isinstance(summary.get("top_program"), str))
check("summary.enrollment_by_year -- dict",             isinstance(summary.get("enrollment_by_year"), dict))

# /api/enrollment/forecast
r = get("/api/enrollment/forecast", params={"program": "MS Data Science", "years": 3})
check("GET /api/enrollment/forecast        -- 200",     r.status_code == 200)
body = r.json()
check("forecast.program   -- str",                      isinstance(body.get("program"), str))
check("forecast.historical -- list",                    isinstance(body.get("historical"), list))
check("forecast.forecast   -- list of 3",               isinstance(body.get("forecast"), list) and len(body.get("forecast", [])) == 3)

# /api/enrollment/admission-risk
r = get("/api/enrollment/admission-risk")
check("GET /api/enrollment/admission-risk  -- 200",     r.status_code == 200)
risks = r.json()
check("admission-risk returns list",                    isinstance(risks, list) and len(risks) > 0)
if risks:
    rk = risks[0]
    check("risk[].program            -- str",           isinstance(rk.get("program"), str))
    check("risk[].risk_score         -- numeric",       isinstance(rk.get("risk_score"), (int, float)))
    check("risk[].trend              -- str",           isinstance(rk.get("trend"), str))
    check("risk[].recommended_intake -- int",           isinstance(rk.get("recommended_intake"), int))

# /api/enrollment/placement-by-stream
r = get("/api/enrollment/placement-by-stream")
check("GET /api/enrollment/placement-by-stream -- 200", r.status_code == 200)
streams = r.json()
check("placement-by-stream returns 12 programmes",      isinstance(streams, list) and len(streams) == 12)
if streams:
    st = streams[0]
    check("stream[].program        -- str",             isinstance(st.get("program"), str))
    check("stream[].placement_rate -- numeric",         isinstance(st.get("placement_rate"), (int, float)))
    check("stream[].avg_salary     -- numeric",         isinstance(st.get("avg_salary"), (int, float)))
    check("stream[].student_count  -- int",             isinstance(st.get("student_count"), int))

# /api/enrollment/skill-recommendations
r = get("/api/enrollment/skill-recommendations")
check("GET /api/enrollment/skill-recommendations -- 200", r.status_code == 200)
recs = r.json()
check("recs.recommendations      -- list",              isinstance(recs.get("recommendations"), list))
check("recs.alternative_pathways -- list",              isinstance(recs.get("alternative_pathways"), list))


# =============================================================================
# Section IV -- Prediction Flow (POST predict + GET recs)
# =============================================================================

section("IV -- Prediction Flow (predict -> explain -> recommend)")

# Strong student
r = post("/api/enrollment/predict-placement", json=STRONG_STUDENT)
check("POST predict-placement strong -- 200",           r.status_code == 200, f"status={r.status_code}")
pred = r.json()
check("prediction.placement_probability -- float",      isinstance(pred.get("placement_probability"), float))
check("prediction.prediction           -- str",         isinstance(pred.get("prediction"), str))
check("prediction.base_value           -- numeric",     isinstance(pred.get("base_value"), (int, float)))
check("prediction.shap_values          -- list",        isinstance(pred.get("shap_values"), list))
check("strong student probability > 0.5",               pred.get("placement_probability", 0) > 0.5,
      f"got {pred.get('placement_probability'):.3f}")
check("strong student predicted Placed",                pred.get("prediction") == "Placed")

# Weak student
r = post("/api/enrollment/predict-placement", json=WEAK_STUDENT)
check("POST predict-placement weak   -- 200",           r.status_code == 200)
pred_weak = r.json()
check("weak student probability < strong student's",
      pred_weak.get("placement_probability", 1) < pred.get("placement_probability", 0),
      f"weak={pred_weak.get('placement_probability'):.3f} strong={pred.get('placement_probability'):.3f}")

# SHAP values structure
shap = pred.get("shap_values", [])
check("shap_values non-empty",                          len(shap) > 0)
if shap:
    sv = shap[0]
    check("shap_value[].feature -- str",                isinstance(sv.get("feature"), str))
    check("shap_value[].value   -- numeric",            isinstance(sv.get("value"), (int, float)))
    check("shap_value[].shap    -- numeric",            isinstance(sv.get("shap"), (int, float)))

# Skill recommendations after prediction
r = get("/api/enrollment/skill-recommendations")
check("GET skill-recommendations after predict -- 200", r.status_code == 200)
rec_body = r.json()
recs_list = rec_body.get("recommendations", [])
check("recommendations list non-empty",                 len(recs_list) > 0)
if recs_list:
    rec = recs_list[0]
    check("rec[].skill     -- str",                     isinstance(rec.get("skill"), str))
    check("rec[].priority  -- High/Medium/Low",
          rec.get("priority") in ("High", "Medium", "Low"),
          f"got {rec.get('priority')}")
    check("rec[].reason    -- str",                     isinstance(rec.get("reason"), str))
pathways = rec_body.get("alternative_pathways", [])
check("alternative_pathways non-empty",                 len(pathways) > 0)


# =============================================================================
# Section V -- Parameter Forwarding
# =============================================================================

section("V -- API Parameter Forwarding")

# months param for demand-forecast
for months in (6, 9, 12):
    r = get("/api/market/demand-forecast", params={"months": months})
    fc = r.json()
    check(f"demand-forecast?months={months} returns {months} points",
          isinstance(fc, list) and len(fc) == months,
          f"got {len(fc)}")

# n param for top-companies
r3  = get("/api/market/top-companies", params={"n": 3}).json()
r10 = get("/api/market/top-companies", params={"n": 10}).json()
check("top-companies?n=3  returns at most 3",           len(r3)  <= 3,  f"got {len(r3)}")
check("top-companies?n=10 returns at most 10",          len(r10) <= 10, f"got {len(r10)}")
check("n=10 returns more than n=3",                     len(r10) > len(r3))

# years param for enrollment-forecast
for years in (2, 3, 5):
    r = get("/api/enrollment/forecast",
            params={"program": "MS Data Science", "years": years})
    fc = r.json().get("forecast", [])
    check(f"enrollment/forecast?years={years} returns {years} points",
          len(fc) == years, f"got {len(fc)}")

# limit param for admission-risk
r5  = get("/api/enrollment/admission-risk", params={"limit": 5}).json()
r12 = get("/api/enrollment/admission-risk", params={"limit": 12}).json()
check("admission-risk?limit=5  returns at most 5",      len(r5)  <= 5,  f"got {len(r5)}")
check("admission-risk?limit=12 returns at most 12",     len(r12) <= 12, f"got {len(r12)}")
check("limit=12 returns more than limit=5",             len(r12) > len(r5))


# =============================================================================
# Section VI -- Response-Time Budget
# =============================================================================

section("VI -- Response-Time Budget (warm cache)")

COLD_BUDGET_MS  = 500   # first-ever hit may load from parquet
WARM_BUDGET_MS  = 200   # cached endpoints must be well below this

endpoints_cached = [
    "/api/market/overview",
    "/api/market/top-companies",
    "/api/market/skill-gap",
    "/api/market/regional-hiring",
    "/api/market/hiring-sources",
]

# Warm up
for ep in endpoints_cached:
    get(ep)

# Measure warm
for ep in endpoints_cached:
    t0 = time.monotonic()
    r  = get(ep)
    ms = (time.monotonic() - t0) * 1000
    check(f"{ep.split('/')[-1]:<25} warm < {WARM_BUDGET_MS} ms",
          ms < WARM_BUDGET_MS, f"{ms:.0f} ms")

# Enrollment endpoints (not cached with TTL, but still fast from parquet)
enroll_endpoints = [
    ("/api/enrollment/summary",          {}),
    ("/api/enrollment/placement-by-stream", {}),
]
for ep, params in enroll_endpoints:
    t0 = time.monotonic()
    get(ep, params=params)
    ms = (time.monotonic() - t0) * 1000
    check(f"{ep.split('/')[-1]:<25} < {COLD_BUDGET_MS} ms",
          ms < COLD_BUDGET_MS, f"{ms:.0f} ms")


# =============================================================================
# Section VII -- Cross-Endpoint Data Consistency
# =============================================================================

section("VII -- Data Consistency (cross-endpoint)")

# Reload summary and streams fresh
summary = get("/api/enrollment/summary").json()
streams = get("/api/enrollment/placement-by-stream").json()

total_students = summary.get("total_students", 0)
stream_total   = sum(s.get("student_count", 0) for s in streams)
check("sum(stream student counts) == summary.total_students",
      total_students == stream_total,
      f"{stream_total} == {total_students}")

check("summary.total_programs == 12 (number of programmes)",
      summary.get("total_programs") == 12,
      f"got {summary.get('total_programs')}")

check("summary.avg_placement_rate in realistic range [70, 100]",
      70 <= summary.get("avg_placement_rate", 0) <= 100,
      f"got {summary.get('avg_placement_rate')}")

check("placement-by-stream contains exactly 12 programmes",
      len(streams) == 12, f"got {len(streams)}")

# All stream programs appear in a known list
KNOWN_PROGRAMS = {
    "BS Computer Science", "BS Data Science", "Certificate Data Analytics",
    "MBA Product Management", "MS Artificial Intelligence", "MS Business Analytics",
    "MS Cloud Computing", "MS Computer Science", "MS Cybersecurity",
    "MS Data Science", "MS Human-Computer Interaction", "MS Information Technology",
}
stream_progs = {s["program"] for s in streams}
check("all stream programmes are in the 12-programme list",
      stream_progs.issubset(KNOWN_PROGRAMS),
      f"unexpected: {stream_progs - KNOWN_PROGRAMS}")

# Forecast lower_bound <= predicted_postings <= upper_bound for every point
fc_data = get("/api/market/demand-forecast").json()
bounds_ok = all(
    pt["lower_bound"] <= pt["predicted_postings"] <= pt["upper_bound"]
    for pt in fc_data
)
check("all forecast points: lower <= predicted <= upper",
      bounds_ok)

# Admission risk scores are non-negative
risks = get("/api/enrollment/admission-risk", params={"limit": 12}).json()
check("all risk_scores >= 0",
      all(r["risk_score"] >= 0 for r in risks),
      f"min={min((r['risk_score'] for r in risks), default=0):.1f}")

# Trend values are valid
valid_trends = {"up", "down", "stable"}
check("all trend values are 'up' | 'down' | 'stable'",
      all(r["trend"] in valid_trends for r in risks))

# SHAP contributions sum direction: positive shap -> placed more likely
r = post("/api/enrollment/predict-placement", json=STRONG_STUDENT)
shap_vals = r.json().get("shap_values", [])
pos_shap = [sv["shap"] for sv in shap_vals if sv["shap"] > 0]
check("strong student has at least one positive SHAP contribution",
      len(pos_shap) > 0, f"positive contribs: {len(pos_shap)}")


# =============================================================================
# Section VIII -- System Health & Edge Cases
# =============================================================================

section("VIII -- System Health & Edge Cases")

# 1. Root endpoint
r = get("/")
check("GET /  -- 200",                       r.status_code == 200)
body_root = r.json()
check("GET /  -- message field present",     "message" in body_root)
check("GET /  -- message mentions PathWise", "PathWise" in body_root.get("message", ""))

# 2. /health re-confirms all models True (belt-and-suspenders from Section I)
r = get("/health")
hbody = r.json()
check("/health status == 'ok'",              hbody.get("status") == "ok",
      f"got '{hbody.get('status')}'")
check("/health all 4 models True",
      all(hbody.get("models", {}).values()),
      str(hbody.get("models", {})))

# 3. Monitoring — drift endpoint
try:
    r = get("/api/monitoring/drift")
    check("GET /api/monitoring/drift -- 200",                r.status_code == 200)
    d = r.json()
    check("drift.total_logged    -- int >= 0",               isinstance(d.get("total_logged"), int) and d["total_logged"] >= 0)
    check("drift.window          -- int",                    isinstance(d.get("window"), int))
    check("drift.baseline        -- numeric",                isinstance(d.get("baseline"), (int, float)))
    check("drift.drift           -- numeric",                isinstance(d.get("drift"), (int, float)))
    check("drift.alert           -- bool",                   isinstance(d.get("alert"), bool))
    check("drift.recommendation  -- str",                    isinstance(d.get("recommendation"), str))
except Exception as exc:
    check("GET /api/monitoring/drift reachable", False, str(exc))

# 4. Monitoring — recent predictions log
try:
    r = get("/api/monitoring/predictions")
    check("GET /api/monitoring/predictions -- 200",          r.status_code == 200)
    preds_log = r.json()
    check("predictions endpoint returns a list",             isinstance(preds_log, list))
    # After Section IV we made 2+ predictions, so the log should be non-empty
    check("predictions log non-empty after predict calls",   len(preds_log) > 0,
          f"got {len(preds_log)} entries")
    if preds_log:
        entry = preds_log[0]
        check("log entry has 'ts'          field",           "ts" in entry)
        check("log entry has 'probability' field",           "probability" in entry)
        check("log entry has 'prediction'  field",           "prediction" in entry)
        check("log entry has 'latency_ms'  field",           "latency_ms" in entry)
except Exception as exc:
    check("GET /api/monitoring/predictions reachable", False, str(exc))

# 5. Monitoring — n param forwarding
r10 = get("/api/monitoring/predictions", params={"n": 10})
r1  = get("/api/monitoring/predictions", params={"n": 1})
check("predictions?n=10 returns at most 10 entries",         len(r10.json()) <= 10)
check("predictions?n=1  returns at most 1 entry",            len(r1.json())  <= 1)

# 6. CORS preflight — OPTIONS on a known endpoint
try:
    r = requests.options(
        BACKEND + "/api/enrollment/predict-placement",
        headers={
            "Origin":                        "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
        timeout=10,
    )
    # FastAPI CORSMiddleware responds 200 to OPTIONS preflight
    check("OPTIONS preflight returns 200",
          r.status_code == 200,
          f"got {r.status_code}")
    check("CORS allow-origin header present",
          "access-control-allow-origin" in {k.lower() for k in r.headers},
          str(dict(r.headers)))
except Exception as exc:
    check("OPTIONS preflight reachable", False, str(exc))

# 7. Error handling — missing required field (program) returns 422
r = post("/api/enrollment/predict-placement", json={
    "gpa": 3.5, "internships": 2, "projects": 3, "communication_score": 7
    # program intentionally omitted
})
check("predict-placement missing 'program' -- 422",
      r.status_code == 422,
      f"got {r.status_code}")

# 8. Error handling — GPA out of valid range returns 422
r = post("/api/enrollment/predict-placement", json={
    "gpa": 9.9, "internships": 2, "projects": 3,
    "communication_score": 7, "program": "MS Data Science",
})
check("predict-placement GPA=9.9 (invalid) -- 422",
      r.status_code == 422,
      f"got {r.status_code}")

# 9. Demand forecast bounds sanity — all values non-negative
fc_data = get("/api/market/demand-forecast").json()
check("all forecast lower_bound values >= 0",
      all(pt.get("lower_bound", -1) >= 0 for pt in fc_data),
      f"min lower_bound={min((pt.get('lower_bound',0) for pt in fc_data), default=0):.0f}")
check("all forecast predicted_postings > 0",
      all(pt.get("predicted_postings", 0) > 0 for pt in fc_data))

# 10. Prediction POST latency within 1000 ms (cold budget — model is warm)
t0 = time.monotonic()
post("/api/enrollment/predict-placement", json=STRONG_STUDENT)
pred_ms = (time.monotonic() - t0) * 1000
check(f"POST predict-placement latency < 1000 ms",
      pred_ms < 1000, f"{pred_ms:.0f} ms")

# 11. DB connectivity implied — enrollment/summary would 500 if Postgres is down
r = get("/api/enrollment/summary")
check("DB connectivity implied by enrollment/summary 200",
      r.status_code == 200,
      f"status={r.status_code}  (500 = DB unreachable)")

# 12. Drift alert is False on a fresh/small log (baseline-matching synthetic data)
r = get("/api/monitoring/drift", params={"window": 5})
if r.status_code == 200:
    drift5 = r.json()
    check("drift window=5 returns valid structure",
          all(k in drift5 for k in ("alert", "drift", "mean_probability")))


# =============================================================================
# Summary
# =============================================================================

total = passed + failed
print(f"\n{'=' * 66}")
print(f"  Phase 6 Integration Smoke Test")
print(f"  {passed}/{total} passed", end="")
if failed == 0:
    print("  \033[32m-- ALL PASS\033[0m")
else:
    print(f"  \033[31m-- {failed} FAILED\033[0m")
print(f"{'=' * 66}\n")

sys.exit(0 if failed == 0 else 1)
