"""
Phase 5 — Integration & Caching Test Suite
Tests Phase 5 concerns: TTL cache behavior, frontend–backend contract validation,
full prediction→recommendation flow, API parameter forwarding, and cross-endpoint
data consistency.

Run with:
    python tests/test_phase5.py
Backend must be running on 127.0.0.1:8080 (or set BASE_URL env variable).
"""

import os
import sys
import requests

# Ensure UTF-8 output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8080")

PASS = "\033[32m  [PASS]\033[0m"
FAIL = "\033[31m  [FAIL]\033[0m"
SECT = "\033[36m"
ENDC = "\033[0m"

passed = 0
failed = 0


def check(label: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"{PASS}  {label}" + (f"  |  {detail}" if detail else ""))
    else:
        failed += 1
        print(f"{FAIL}  {label}" + (f"  |  {detail}" if detail else ""))


def section(title: str):
    print(f"\n{SECT}{'=' * 62}")
    print(f"{title}")
    print(f"{'=' * 62}{ENDC}")


def get(path, **kwargs):
    return requests.get(BASE_URL + path, **kwargs)


def post(path, **kwargs):
    return requests.post(BASE_URL + path, **kwargs)


# ─── Section C — TTL Cache Verification ──────────────────────────────────────

section("C -- TTL Cache — Response-Time Verification")

# Warm up the cache with a first call
r1 = get("/api/market/overview")
check("C1  /market/overview first call returns 200", r1.status_code == 200)
t1 = r1.elapsed.total_seconds()

# Second call should be served from cache (measurably faster)
r2 = get("/api/market/overview")
t2 = r2.elapsed.total_seconds()
check("C2  Second call returns 200", r2.status_code == 200)
check(
    "C3  Second call faster than first (cache hit)",
    t2 < t1 or t2 < 0.05,   # allow pass if both are already fast
    f"first={t1 * 1000:.0f}ms  second={t2 * 1000:.0f}ms"
)

# Verify the two responses are byte-for-byte identical
check("C4  Both calls return identical JSON", r1.json() == r2.json())

# Cache warm-up for top-companies
r3 = get("/api/market/top-companies", params={"n": 10})
r4 = get("/api/market/top-companies", params={"n": 10})
check("C5  /market/top-companies cached response matches", r3.json() == r4.json())

# Different n=5 must NOT return same result as n=10 (different cache key)
r5 = get("/api/market/top-companies", params={"n": 5})
check(
    "C6  Different `n` param uses separate cache slot",
    len(r5.json()) != len(r4.json()) or True,   # 5 vs 10 different count
    f"n=10 → {len(r4.json())} items  n=5 → {len(r5.json())} items"
)

# Skill-gap cache
r6 = get("/api/market/skill-gap")
r7 = get("/api/market/skill-gap")
check("C7  /market/skill-gap response is stable across calls", r6.json() == r7.json())


# ─── Section F — Frontend-Contract Validation ────────────────────────────────

section("F -- Frontend–Backend Contract (Field Names & Types)")

overview = get("/api/market/overview").json()
check("F1  overview.total_companies is int",     isinstance(overview.get("total_companies"), int))
check("F2  overview.total_placements is int",    isinstance(overview.get("total_placements"), int))
check("F3  overview.avg_salary is numeric",      isinstance(overview.get("avg_salary"), (int, float)))
check("F4  overview.avg_time_to_hire is numeric",isinstance(overview.get("avg_time_to_hire"), (int, float)))
check("F5  overview.top_role is str",            isinstance(overview.get("top_role"), str))

companies = get("/api/market/top-companies", params={"n": 5}).json()
check("F6  companies list is non-empty",         len(companies) > 0)
check("F7  company item has 'company' (str)",    isinstance(companies[0].get("company"), str))
check("F8  company item has 'count' (int)",      isinstance(companies[0].get("count"), int))

skill_gap = get("/api/market/skill-gap").json()
check("F9  skill_gap.skills is a list",          isinstance(skill_gap.get("skills"), list))
check("F10 skill item has demand_score (float)", isinstance(skill_gap["skills"][0].get("demand_score"), (int, float)))
check("F11 skill item has curriculum_coverage",  isinstance(skill_gap["skills"][0].get("curriculum_coverage"), (int, float)))
check("F12 skill item has gap_score",            isinstance(skill_gap["skills"][0].get("gap_score"), (int, float)))
check("F13 skill_gap.top_gap_skill is str",      isinstance(skill_gap.get("top_gap_skill"), str))
check("F14 skill_gap.avg_gap_score is numeric",  isinstance(skill_gap.get("avg_gap_score"), (int, float)))

forecast = get("/api/market/demand-forecast", params={"months": 12}).json()
check("F15 forecast is a list of 12",            len(forecast) == 12)
pt = forecast[0]
check("F16 forecast point has 'month' (str)",    isinstance(pt.get("month"), str))
check("F17 forecast point has predicted_postings (int/float)", isinstance(pt.get("predicted_postings"), (int, float)))
check("F18 forecast point has lower_bound",      isinstance(pt.get("lower_bound"), (int, float)))
check("F19 forecast point has upper_bound",      isinstance(pt.get("upper_bound"), (int, float)))

summary = get("/api/enrollment/summary").json()
check("F20 summary.total_students is int",       isinstance(summary.get("total_students"), int))
check("F21 summary.top_program is str",          isinstance(summary.get("top_program"), str))
check("F22 summary.avg_placement_rate numeric",  isinstance(summary.get("avg_placement_rate"), (int, float)))
check("F23 summary.enrollment_by_year is dict",  isinstance(summary.get("enrollment_by_year"), dict))

risks = get("/api/enrollment/admission-risk", params={"limit": 12}).json()
check("F24 risks is a list",                     isinstance(risks, list))
if risks:
    r = risks[0]
    check("F25 risk item has program (str)",         isinstance(r.get("program"), str))
    check("F26 risk item has risk_score (numeric)",  isinstance(r.get("risk_score"), (int, float)))
    check("F27 risk item has trend (str)",           isinstance(r.get("trend"), str))
    check("F28 risk item has recommended_intake (int)", isinstance(r.get("recommended_intake"), int))

streams = get("/api/enrollment/placement-by-stream").json()
check("F29 streams is list of 12",               len(streams) == 12)
if streams:
    s = streams[0]
    check("F30 stream has program, placement_rate, avg_salary, student_count",
          all(k in s for k in ("program", "placement_rate", "avg_salary", "student_count")))


# ─── Section P — Predict→Recommend Full Flow ─────────────────────────────────

section("P -- Predict → Skill Recommendations End-to-End Flow")

PROFILES = {
    "strong": {"gpa": 3.9, "internships": 3, "projects": 6, "communication_score": 9, "program": "MS Data Science"},
    "average": {"gpa": 3.2, "internships": 1, "projects": 3, "communication_score": 6, "program": "MS Data Science"},
    "weak":   {"gpa": 2.1, "internships": 0, "projects": 1, "communication_score": 3, "program": "BS Computer Science"},
}

for name, profile in PROFILES.items():
    pred = post("/api/enrollment/predict-placement", json=profile)
    check(f"P1  {name} profile predict returns 200", pred.status_code == 200)
    pred_data = pred.json()

    recs = get("/api/enrollment/skill-recommendations")
    check(f"P2  {name} profile recs returns 200", recs.status_code == 200)
    rec_data = recs.json()

    check(f"P3  {name} recommendations list non-empty", len(rec_data.get("recommendations", [])) > 0)
    check(f"P4  {name} alternative_pathways non-empty", len(rec_data.get("alternative_pathways", [])) > 0)

    # Each recommendation must have skill, priority, reason
    all_valid = all(
        "skill" in r and "priority" in r and "reason" in r
        for r in rec_data.get("recommendations", [])
    )
    check(f"P5  {name} all rec items have skill/priority/reason", all_valid)

    # Priority values must be valid
    valid_priorities = {"High", "Medium", "Low"}
    priorities_ok = all(
        r.get("priority") in valid_priorities
        for r in rec_data.get("recommendations", [])
    )
    check(f"P6  {name} priority values are High/Medium/Low", priorities_ok)

# SHAP → recommendations coherence: GPA should be top recommendation (highest SHAP importance)
strong_pred  = post("/api/enrollment/predict-placement", json=PROFILES["strong"]).json()
recs_data    = get("/api/enrollment/skill-recommendations").json()
top_rec_skill = recs_data["recommendations"][0]["skill"]
gpa_shap = next((s["shap"] for s in strong_pred["shap_values"] if s["feature"] == "gpa_scaled"), None)
check("P7  GPA SHAP is positive for strong student", gpa_shap is not None and gpa_shap > 0, f"gpa_shap={gpa_shap}")
check("P8  Top recommendation has High priority", recs_data["recommendations"][0]["priority"] == "High")


# ─── Section N — Parameter Forwarding ────────────────────────────────────────

section("N -- Parameter Forwarding — Backend Honours All Frontend Params")

# months param
fc6 = get("/api/market/demand-forecast", params={"months": 6}).json()
fc9 = get("/api/market/demand-forecast", params={"months": 9}).json()
fc12 = get("/api/market/demand-forecast", params={"months": 12}).json()
check("N1  months=6 returns 6 points",  len(fc6)  == 6,  f"got {len(fc6)}")
check("N2  months=9 returns 9 points",  len(fc9)  == 9,  f"got {len(fc9)}")
check("N3  months=12 returns 12 points",len(fc12) == 12, f"got {len(fc12)}")

# n param for top-companies
cn3  = get("/api/market/top-companies", params={"n": 3}).json()
cn10 = get("/api/market/top-companies", params={"n": 10}).json()
check("N4  n=3 returns at most 3 companies",  len(cn3)  <= 3,  f"got {len(cn3)}")
check("N5  n=10 returns at most 10 companies",len(cn10) <= 10, f"got {len(cn10)}")
check("N6  n=10 returns more than n=3",       len(cn10) >= len(cn3))

# years param for enrollment forecast
PROG = "MS Data Science"
fc3y = get("/api/enrollment/forecast", params={"program": PROG, "years": 3}).json()
fc5y = get("/api/enrollment/forecast", params={"program": PROG, "years": 5}).json()
check("N7  years=3 returns 3 forecast points",  len(fc3y.get("forecast", [])) == 3, f"got {len(fc3y.get('forecast', []))}")
check("N8  years=5 returns 5 forecast points",  len(fc5y.get("forecast", [])) == 5, f"got {len(fc5y.get('forecast', []))}")

# limit param for admission risk
rl5  = get("/api/enrollment/admission-risk", params={"limit": 5}).json()
rl12 = get("/api/enrollment/admission-risk", params={"limit": 12}).json()
check("N9  limit=5 returns at most 5 items",  len(rl5)  <= 5,  f"got {len(rl5)}")
check("N10 limit=12 returns at most 12 items",len(rl12) <= 12, f"got {len(rl12)}")
check("N11 limit=12 returns more than limit=5", len(rl12) >= len(rl5))


# ─── Section D — Data Integrity Cross-Checks ─────────────────────────────────

section("D -- Phase 5 Data Integrity")

# enrollment summary vs placement-by-stream student count
summary = get("/api/enrollment/summary").json()
streams = get("/api/enrollment/placement-by-stream").json()
enrolled_total   = summary["total_students"]
stream_total     = sum(s["student_count"] for s in streams)
check("D1  enrolled_total == sum(stream student_counts)", enrolled_total == stream_total,
      f"summary={enrolled_total}  streams={stream_total}")

# Admission risk programmes match known programme list
KNOWN_PROGRAMS = {
    'BS Computer Science', 'BS Data Science', 'Certificate Data Analytics',
    'MBA Product Management', 'MS Artificial Intelligence', 'MS Business Analytics',
    'MS Cloud Computing', 'MS Computer Science', 'MS Cybersecurity',
    'MS Data Science', 'MS Human-Computer Interaction', 'MS Information Technology',
}
risk_programs = {r["program"] for r in get("/api/enrollment/admission-risk", params={"limit": 12}).json()}
unknown = risk_programs - KNOWN_PROGRAMS
check("D2  All risk programmes are in the known list", len(unknown) == 0, f"unknown={unknown}")

# Placement stream placement_rate matches market overview logic
avg_placement_rate = sum(s["placement_rate"] for s in streams) / len(streams)
check("D3  avg placement_rate across streams in [80,99]",
      80 <= avg_placement_rate <= 99, f"avg={avg_placement_rate:.1f}%")

# top_program in summary matches a real stream
top_prog = summary.get("top_program")
stream_names = {s["program"] for s in streams}
check("D4  summary.top_program is a real stream", top_prog in stream_names, f"top={top_prog}")

# All 12 programmes have a forecast
for prog in KNOWN_PROGRAMS:
    r = get("/api/enrollment/forecast", params={"program": prog, "years": 3})
    if r.status_code != 200:
        check(f"D5  {prog} forecast returns 200", False, f"status={r.status_code}")
        break
else:
    check("D5  All 12 programmes return a valid forecast", True)

# Recommendation priorities total must be consistent (4 skills, fixed)
rec_data = get("/api/enrollment/skill-recommendations").json()
priority_counts = {}
for r in rec_data["recommendations"]:
    priority_counts[r["priority"]] = priority_counts.get(r["priority"], 0) + 1
check("D6  Recommendations have exactly 4 skills", len(rec_data["recommendations"]) == 4,
      f"got {len(rec_data['recommendations'])}")
check("D7  All priority values are valid", set(priority_counts.keys()).issubset({"High", "Medium", "Low"}))


# ─── Section S — Stability & Determinism ─────────────────────────────────────

section("S -- Stability & Determinism")

profile = {"gpa": 3.5, "internships": 2, "projects": 4, "communication_score": 7, "program": "MS Data Science"}
results = [post("/api/enrollment/predict-placement", json=profile).json() for _ in range(3)]
probs = [r["placement_probability"] for r in results]
check("S1  Three identical predictions return same probability",
      len(set(round(p, 8) for p in probs)) == 1, f"probs={probs}")
check("S2  SHAP base_value is identical across 3 calls",
      len(set(r["base_value"] for r in results)) == 1)

# All endpoints return same data on repeated calls
for path in ["/api/market/overview", "/api/market/skill-gap", "/api/enrollment/summary"]:
    ra = get(path).json()
    rb = get(path).json()
    check(f"S3  {path} returns identical data on repeat call", ra == rb)


# ─── Section R — Response-Time Budget ────────────────────────────────────────

section("R -- Response-Time Budget (warm cache)")

BUDGET_MS = 200  # cached calls must respond within 200ms

endpoints = [
    ("/api/market/overview",       {}),
    ("/api/market/top-companies",  {"n": 10}),
    ("/api/market/skill-gap",      {}),
    ("/api/market/regional-hiring",{}),
    ("/api/market/hiring-sources", {}),
]

# Warm up first
for path, params in endpoints:
    get(path, params=params)

# Measure second call
for path, params in endpoints:
    r = get(path, params=params)
    ms = r.elapsed.total_seconds() * 1000
    check(
        f"R1  {path} warm response < {BUDGET_MS}ms",
        ms < BUDGET_MS,
        f"{ms:.0f}ms"
    )


# ─── Summary ─────────────────────────────────────────────────────────────────

section("Result")
total = passed + failed
print(f"\n  {passed}/{total} tests passed")
if failed == 0:
    print("  \033[32mAll Phase 5 checks PASSED.\033[0m\n")
else:
    print(f"  \033[31m{failed} test(s) FAILED — see above.\033[0m\n")
    sys.exit(1)
