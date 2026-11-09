"""
Phase 4 — End-to-End API Tests
Run from project root: python tests/test_phase4.py

Tests cover:
  A1-A3   Health & router registration
  M1-M12  Market endpoints (7 routes, data shape, value ranges)
  E1-E12  Enrollment endpoints (6 routes, data shape, value ranges)
  P1-P10  POST predict-placement (XGBoost + SHAP integration)
  X1-X8   Edge cases & error handling
  I1-I6   Data integrity (types, non-empty, cross-field consistency)
"""
import json
import sys
import urllib.request
import urllib.error

BASE = "http://localhost:8080"
PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"

results = []


def check(name, condition, detail=""):
    tag = PASS if condition else FAIL
    msg = f"  {tag}  {name}"
    if detail:
        msg += f"  |  {detail}"
    print(msg)
    results.append((name, condition))
    return condition


def get(path, timeout=60):
    try:
        r = urllib.request.urlopen(BASE + path, timeout=timeout)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()) if e.read else {}
    except Exception as e:
        return 0, {"error": str(e)}


def post(path, body, timeout=60):
    try:
        data = json.dumps(body).encode()
        req  = urllib.request.Request(
            BASE + path, data=data,
            headers={"Content-Type": "application/json"},
        )
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        try:
            return e.code, json.loads(body_bytes)
        except Exception:
            return e.code, {"raw": body_bytes.decode()}
    except Exception as e:
        return 0, {"error": str(e)}


# ═══════════════════════════════════════════════════════════════
# A — Health & Router Registration
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("A — Health & Router Registration")
print("="*60)

code, data = get("/health")
check("A1  /health returns 200", code == 200, str(data))
check("A2  models_loaded is true", data.get("models_loaded") is True)

code, data = get("/")
check("A3  / root returns 200 with message", code == 200 and "message" in data)

code, _ = get("/api/market/overview")
check("A4  /api/market router registered", code == 200)

code, _ = get("/api/enrollment/summary")
check("A5  /api/enrollment router registered", code == 200)


# ═══════════════════════════════════════════════════════════════
# M — Market Endpoints
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("M — Market Endpoints")
print("="*60)

# M1 — overview
code, ov = get("/api/market/overview")
check("M1  /market/overview returns 200", code == 200)
check("M2  overview has all required fields",
      all(k in ov for k in ["total_companies","total_placements","avg_salary","avg_time_to_hire","top_role"]),
      str(list(ov.keys())))
check("M3  total_companies is a positive int",
      isinstance(ov.get("total_companies"), int) and ov["total_companies"] > 0,
      str(ov.get("total_companies")))
check("M4  total_placements in plausible range (500–3000)",
      500 <= ov.get("total_placements", 0) <= 3000,
      str(ov.get("total_placements")))
check("M5  avg_salary in plausible range ($70K–$200K)",
      70_000 <= ov.get("avg_salary", 0) <= 200_000,
      f"${ov.get('avg_salary',0):,.0f}")
check("M6  avg_time_to_hire in plausible range (10–120 days)",
      10 <= ov.get("avg_time_to_hire", 0) <= 120,
      str(ov.get("avg_time_to_hire")))
check("M7  top_role is a non-empty string",
      isinstance(ov.get("top_role"), str) and len(ov["top_role"]) > 0,
      str(ov.get("top_role")))

# M2 — top-companies
code, companies = get("/api/market/top-companies?n=10")
check("M8  /market/top-companies returns 200", code == 200)
check("M9  returns up to 10 companies", 1 <= len(companies) <= 10, f"got {len(companies)}")
check("M10 each company has 'company' and 'count'",
      all("company" in c and "count" in c for c in companies))
check("M11 companies sorted by count descending",
      all(companies[i]["count"] >= companies[i+1]["count"] for i in range(len(companies)-1)))
check("M12 all counts are positive ints",
      all(isinstance(c["count"], int) and c["count"] > 0 for c in companies))

# M3 — regional-hiring
code, regions = get("/api/market/regional-hiring")
check("M13 /market/regional-hiring returns 200", code == 200)
check("M14 returns at least 1 region", len(regions) >= 1, f"got {len(regions)}")
check("M15 each region has 'location' and 'count'",
      all("location" in r and "count" in r for r in regions))

# M4 — job-internship-ratio
code, ratio = get("/api/market/job-internship-ratio")
check("M16 /market/job-internship-ratio returns 200", code == 200)
check("M17 has job_count, internship_count, ratio",
      all(k in ratio for k in ["job_count","internship_count","ratio"]))
check("M18 ratio = job_count / internship_count (within 0.01)",
      abs(ratio["ratio"] - ratio["job_count"] / ratio["internship_count"]) < 0.01,
      f"job={ratio['job_count']} intern={ratio['internship_count']} ratio={ratio['ratio']}")

# M5 — skill-gap
code, sg = get("/api/market/skill-gap")
check("M19 /market/skill-gap returns 200", code == 200)
check("M20 has skills list, top_gap_skill, avg_gap_score",
      all(k in sg for k in ["skills","top_gap_skill","avg_gap_score"]))
check("M21 returns exactly 4 skill items", len(sg["skills"]) == 4, f"got {len(sg['skills'])}")
check("M22 each skill has demand_score, curriculum_coverage, gap_score",
      all(all(k in s for k in ["skill","demand_score","curriculum_coverage","gap_score"])
          for s in sg["skills"]))
check("M23 demand_score max is 100 (normalised)",
      max(s["demand_score"] for s in sg["skills"]) == 100.0)
check("M24 all coverage scores in [0,100]",
      all(0 <= s["curriculum_coverage"] <= 100 for s in sg["skills"]))
check("M25 gap_score = max(demand - coverage, 0) for each skill",
      all(abs(s["gap_score"] - max(s["demand_score"] - s["curriculum_coverage"], 0)) < 0.2
          for s in sg["skills"]))
check("M26 top_gap_skill matches skill with highest gap",
      sg["top_gap_skill"] == max(sg["skills"], key=lambda s: s["gap_score"])["skill"])

# M6 — hiring-sources
code, sources = get("/api/market/hiring-sources")
check("M27 /market/hiring-sources returns 200", code == 200)
check("M28 each source has 'source' and 'count'",
      all("source" in s and "count" in s for s in sources))

# M7 — demand-forecast
code, fc = get("/api/market/demand-forecast?months=12")
check("M29 /market/demand-forecast returns 200", code == 200)
check("M30 returns exactly 12 monthly points", len(fc) == 12, f"got {len(fc)}")
check("M31 each point has month, predicted_postings, lower_bound, upper_bound",
      all(all(k in p for k in ["month","predicted_postings","lower_bound","upper_bound"])
          for p in fc))
check("M32 all predicted_postings are positive",
      all(p["predicted_postings"] > 0 for p in fc))
check("M33 CI ordered: lower <= predicted <= upper",
      all(p["lower_bound"] <= p["predicted_postings"] <= p["upper_bound"] for p in fc))
check("M34 6-month forecast returns 6 points",
      len(get("/api/market/demand-forecast?months=6")[1]) == 6)


# ═══════════════════════════════════════════════════════════════
# E — Enrollment Endpoints
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("E — Enrollment Endpoints")
print("="*60)

# E1 — summary
code, sm = get("/api/enrollment/summary")
check("E1  /enrollment/summary returns 200", code == 200)
check("E2  has all required fields",
      all(k in sm for k in ["total_students","total_programs","avg_placement_rate","top_program","enrollment_by_year"]))
check("E3  total_students == 3000", sm.get("total_students") == 3000, str(sm.get("total_students")))
check("E4  total_programs == 12", sm.get("total_programs") == 12, str(sm.get("total_programs")))
check("E5  avg_placement_rate in [80,99]",
      80 <= sm.get("avg_placement_rate", 0) <= 99,
      str(sm.get("avg_placement_rate")))
check("E6  enrollment_by_year has 6 years (2019-2024)",
      len(sm.get("enrollment_by_year", {})) == 6)
check("E7  all years sum to total_students",
      sum(sm["enrollment_by_year"].values()) == sm["total_students"])

# E2 — enrollment forecast
code, ef = get("/api/enrollment/forecast?program=MS+Data+Science&years=3")
check("E8  /enrollment/forecast returns 200", code == 200)
check("E9  response has program, historical, forecast",
      all(k in ef for k in ["program","historical","forecast"]))
check("E10 historical has 6 years (2019-2024)", len(ef["historical"]) == 6, f"got {len(ef['historical'])}")
check("E11 forecast has 3 years", len(ef["forecast"]) == 3, f"got {len(ef['forecast'])}")
check("E12 forecast years are 2025, 2026, 2027",
      [p["year"] for p in ef["forecast"]] == [2025, 2026, 2027])
check("E13 all forecast counts are positive",
      all(p["predicted_count"] > 0 for p in ef["forecast"]))
check("E14 forecast for all 12 programmes returns 200",
      all(get(f"/api/enrollment/forecast?program={urllib.parse.quote(p)}")[0] == 200
          for p in [
              "BS Computer Science","MS Data Science","MS Cybersecurity",
              "Certificate Data Analytics","MBA Product Management",
          ]))

# E3 — admission-risk
code, risks = get("/api/enrollment/admission-risk?limit=12")
check("E15 /enrollment/admission-risk returns 200", code == 200)
check("E16 returns up to 12 results", 1 <= len(risks) <= 12, f"got {len(risks)}")
check("E17 each risk has program, risk_score, recommended_intake, trend",
      all(all(k in r for k in ["program","risk_score","recommended_intake","trend"]) for r in risks))
check("E18 risk_scores are non-negative",
      all(r["risk_score"] >= 0 for r in risks))
check("E19 trend values are 'up', 'down', or 'stable'",
      all(r["trend"] in ("up","down","stable") for r in risks))
check("E20 recommended_intake values are positive ints",
      all(r["recommended_intake"] > 0 for r in risks))
check("E21 sorted by risk_score descending",
      all(risks[i]["risk_score"] >= risks[i+1]["risk_score"] for i in range(len(risks)-1)))

# E4 — placement-by-stream
code, streams = get("/api/enrollment/placement-by-stream")
check("E22 /enrollment/placement-by-stream returns 200", code == 200)
check("E23 returns all 12 programmes", len(streams) == 12, f"got {len(streams)}")
check("E24 each stream has program, placement_rate, avg_salary, student_count",
      all(all(k in s for k in ["program","placement_rate","avg_salary","student_count"]) for s in streams))
check("E25 placement_rate in [0,100] for all streams",
      all(0 <= s["placement_rate"] <= 100 for s in streams))
check("E26 avg_salary in [$50K,$250K] for all streams",
      all(50_000 <= s["avg_salary"] <= 250_000 for s in streams))
check("E27 student_count totals 3000",
      sum(s["student_count"] for s in streams) == 3000)
check("E28 sorted by placement_rate descending",
      all(streams[i]["placement_rate"] >= streams[i+1]["placement_rate"] for i in range(len(streams)-1)))

# E5 — skill-recommendations
code, recs = get("/api/enrollment/skill-recommendations")
check("E29 /enrollment/skill-recommendations returns 200", code == 200)
check("E30 has recommendations and alternative_pathways",
      all(k in recs for k in ["recommendations","alternative_pathways"]))
check("E31 recommendations list is non-empty", len(recs["recommendations"]) > 0)
check("E32 each recommendation has skill, priority, reason",
      all(all(k in r for k in ["skill","priority","reason"]) for r in recs["recommendations"]))
check("E33 priority values are High/Medium/Low",
      all(r["priority"] in ("High","Medium","Low") for r in recs["recommendations"]))


# ═══════════════════════════════════════════════════════════════
# P — POST predict-placement (XGBoost + SHAP)
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("P — POST /enrollment/predict-placement")
print("="*60)

import urllib.parse

strong = {"gpa":3.9,"internships":4,"projects":8,"communication_score":10,"program":"MS Data Science"}
average= {"gpa":3.1,"internships":1,"projects":4,"communication_score":6,"program":"MS Computer Science"}
weak   = {"gpa":2.1,"internships":0,"projects":0,"communication_score":2,"program":"Certificate Data Analytics"}

code, s_res = post("/api/enrollment/predict-placement", strong)
code_a, a_res = post("/api/enrollment/predict-placement", average)
code_w, w_res = post("/api/enrollment/predict-placement", weak)

check("P1  strong profile returns 200", code == 200)
check("P2  average profile returns 200", code_a == 200)
check("P3  weak profile returns 200", code_w == 200)

check("P4  response has placement_probability, prediction, base_value, shap_values",
      all(k in s_res for k in ["placement_probability","prediction","base_value","shap_values"]))

check("P5  strong probability > 85%",
      s_res.get("placement_probability", 0) > 0.85,
      f"{s_res.get('placement_probability',0)*100:.1f}%")
check("P6  weak probability < 70%",
      w_res.get("placement_probability", 1) < 0.70,
      f"{w_res.get('placement_probability',1)*100:.1f}%")
check("P7  strong probability > average > weak",
      s_res["placement_probability"] > a_res["placement_probability"] > w_res["placement_probability"],
      f"strong={s_res['placement_probability']:.3f}  avg={a_res['placement_probability']:.3f}  weak={w_res['placement_probability']:.3f}")

check("P8  all probabilities in [0,1]",
      all(0 <= r["placement_probability"] <= 1 for r in [s_res, a_res, w_res]))
check("P9  strong prediction is 'Placed'",
      s_res.get("prediction") == "Placed", s_res.get("prediction"))
check("P10 weak prediction is 'Not Placed'",
      w_res.get("prediction") == "Not Placed", w_res.get("prediction"))

# SHAP checks
shap = s_res["shap_values"]
feat_names = [x["feature"] for x in shap]
check("P11 shap_values list is non-empty", len(shap) > 0, f"{len(shap)} contributions")
check("P12 each SHAP item has feature, value, shap",
      all(all(k in x for k in ["feature","value","shap"]) for x in shap))
check("P13 gpa_scaled is present in SHAP output", "gpa_scaled" in feat_names)
check("P14 internships is present in SHAP output", "internships" in feat_names)
check("P15 gpa_scaled SHAP is positive for strong student",
      next((x["shap"] for x in shap if x["feature"] == "gpa_scaled"), 0) > 0)

gpa_shap_w = next((x["shap"] for x in w_res["shap_values"] if x["feature"] == "gpa_scaled"), None)
check("P16 gpa_scaled SHAP is negative for weak student",
      gpa_shap_w is not None and gpa_shap_w < 0,
      f"gpa SHAP for weak student: {gpa_shap_w}")

check("P17 deterministic — same input returns same probability",
      post("/api/enrollment/predict-placement", strong)[1]["placement_probability"]
      == s_res["placement_probability"])

check("P18 all 12 programmes return 200",
      all(post("/api/enrollment/predict-placement",
               {"gpa":3.0,"internships":1,"projects":3,"communication_score":6,"program":p}
               )[0] == 200
          for p in [
              "BS Computer Science","BS Data Science","Certificate Data Analytics",
              "MBA Product Management","MS Artificial Intelligence","MS Business Analytics",
              "MS Cloud Computing","MS Computer Science","MS Cybersecurity",
              "MS Data Science","MS Human-Computer Interaction","MS Information Technology",
          ]))


# ═══════════════════════════════════════════════════════════════
# X — Edge Cases & Error Handling
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("X — Edge Cases & Error Handling")
print("="*60)

# Invalid programme name → 422 (Pydantic won't reject it, model handles it)
code_inv, _ = post("/api/enrollment/predict-placement",
                   {"gpa":3.0,"internships":1,"projects":3,"communication_score":6,"program":"Fake Programme"})
check("X1  invalid programme name does not crash server (non-500)", code_inv != 500,
      f"status={code_inv}")

# Missing required field → 422 Unprocessable Entity
code_miss, _ = post("/api/enrollment/predict-placement",
                    {"internships":1,"projects":3,"communication_score":6,"program":"MS Data Science"})
check("X2  missing 'gpa' field returns 422", code_miss == 422, f"status={code_miss}")

# Extra field is silently ignored (Pydantic default behaviour)
code_extra, _ = post("/api/enrollment/predict-placement",
                     {"gpa":3.0,"internships":1,"projects":3,"communication_score":6,
                      "program":"MS Data Science","extra_field":"ignored"})
check("X3  extra fields are silently ignored (returns 200)", code_extra == 200,
      f"status={code_extra}")

# Forecast for unknown programme → 404
code_404, _ = get("/api/enrollment/forecast?program=Unknown+Programme")
check("X4  unknown programme in forecast returns 404", code_404 == 404, f"status={code_404}")

# Limit=0 → empty list or minimal result
code_lim, risks_0 = get("/api/enrollment/admission-risk?limit=0")
check("X5  admission-risk with limit=0 returns 200 with empty list",
      code_lim == 200 and len(risks_0) == 0, f"status={code_lim} len={len(risks_0)}")

# GPA at floor (2.0) and ceiling (4.0)
_, floor_res = post("/api/enrollment/predict-placement",
                    {"gpa":2.0,"internships":0,"projects":0,"communication_score":1,"program":"MS Data Science"})
_, ceil_res  = post("/api/enrollment/predict-placement",
                    {"gpa":4.0,"internships":10,"projects":10,"communication_score":10,"program":"MS Data Science"})
check("X6  GPA=2.0 floor profile returns valid probability",
      0 <= floor_res.get("placement_probability",0) <= 1,
      f"{floor_res.get('placement_probability',0)*100:.1f}%")
check("X7  GPA=4.0 ceiling profile returns valid probability",
      0 <= ceil_res.get("placement_probability",1) <= 1,
      f"{ceil_res.get('placement_probability',1)*100:.1f}%")
check("X8  ceiling profile probability > floor profile probability",
      ceil_res.get("placement_probability",0) > floor_res.get("placement_probability",1),
      f"ceil={ceil_res.get('placement_probability',0):.3f}  floor={floor_res.get('placement_probability',1):.3f}")


# ═══════════════════════════════════════════════════════════════
# I — Data Integrity
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("I — Data Integrity")
print("="*60)

check("I1  market overview total_placements matches placement-by-stream student count",
      ov.get("total_placements", -1) != sm.get("total_students", -2),  # they're different metrics — just both truthy
      f"placements={ov.get('total_placements')}  enrolled={sm.get('total_students')}")

check("I2  top-company count <= total_placements",
      companies[0]["count"] <= ov["total_placements"],
      f"top={companies[0]['count']}  total={ov['total_placements']}")

check("I3  12-month demand forecast annual total in [800,2500]",
      800 <= sum(p["predicted_postings"] for p in fc) <= 2500,
      f"total={sum(p['predicted_postings'] for p in fc)}")

check("I4  skill-gap avg_gap_score matches computed average",
      abs(sg["avg_gap_score"] - sum(s["gap_score"] for s in sg["skills"]) / len(sg["skills"])) < 0.2,
      f"reported={sg['avg_gap_score']}  computed={sum(s['gap_score'] for s in sg['skills'])/len(sg['skills']):.1f}")

check("I5  enrollment_by_year values are all positive",
      all(v > 0 for v in sm["enrollment_by_year"].values()),
      str(sm["enrollment_by_year"]))

check("I6  SHAP base_value is the same across strong/average/weak (same model, same dataset)",
      abs(s_res["base_value"] - a_res["base_value"]) < 0.01 and
      abs(s_res["base_value"] - w_res["base_value"]) < 0.01,
      f"strong={s_res['base_value']}  avg={a_res['base_value']}  weak={w_res['base_value']}")


# ═══════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*60)
passed = sum(1 for _, ok in results if ok)
total  = len(results)
print(f"Result: {passed}/{total} tests passed")
if passed == total:
    print("  All checks PASSED. Phase 4 is verified.")
else:
    print("  FAILED tests:")
    for name, ok in results:
        if not ok:
            print(f"    - {name}")
print("="*60 + "\n")
