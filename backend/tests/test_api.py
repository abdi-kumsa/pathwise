"""
PathWise — Backend API Test Suite (pytest + httpx)

Tests every API endpoint: status codes, response schemas, parameter forwarding,
error handling, data consistency, and directional ML correctness.

Run (backend must be reachable):
    pytest backend/tests/test_api.py -v

Override the base URL:
    BASE_URL=http://127.0.0.1:8000 pytest backend/tests/test_api.py -v

Run inside Docker:
    docker exec pathwise_backend pytest /app/tests/test_api.py -v
"""

import os
import pytest
import httpx

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

# ── Shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=30) as c:
        yield c


STRONG_STUDENT = {
    "gpa": 3.9,
    "internships": 4,
    "projects": 5,
    "communication_score": 9,
    "program": "MS Data Science",
}

WEAK_STUDENT = {
    "gpa": 2.3,
    "internships": 0,
    "projects": 1,
    "communication_score": 3,
    "program": "Certificate Data Analytics",
}

KNOWN_PROGRAMS = {
    "BS Computer Science", "BS Data Science", "Certificate Data Analytics",
    "MBA Product Management", "MS Artificial Intelligence", "MS Business Analytics",
    "MS Cloud Computing", "MS Computer Science", "MS Cybersecurity",
    "MS Data Science", "MS Human-Computer Interaction", "MS Information Technology",
}


# =============================================================================
# Health
# =============================================================================

class TestHealth:

    def test_health_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_models_loaded(self, client):
        body = client.get("/health").json()
        assert body.get("models_loaded") is True or all(body.get("models", {}).values()), \
            f"Not all models loaded: {body}"

    def test_health_status_ok(self, client):
        body = client.get("/health").json()
        assert body.get("status") == "ok", f"Got status={body.get('status')}"

    def test_root_liveness(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "PathWise" in r.json().get("message", "")


# =============================================================================
# Market Demand
# =============================================================================

class TestMarketOverview:

    def test_overview_200(self, client):
        r = client.get("/api/market/overview")
        assert r.status_code == 200

    def test_overview_schema(self, client):
        body = client.get("/api/market/overview").json()
        assert isinstance(body["total_companies"],  int)
        assert isinstance(body["total_placements"], int)
        assert isinstance(body["avg_salary"],       (int, float))
        assert isinstance(body["avg_time_to_hire"], (int, float))
        assert isinstance(body["top_role"],         str)

    def test_overview_realistic_values(self, client):
        body = client.get("/api/market/overview").json()
        assert body["total_companies"]  > 0
        assert body["total_placements"] > 0
        assert body["avg_salary"]       > 0


class TestTopCompanies:

    def test_top_companies_200(self, client):
        r = client.get("/api/market/top-companies")
        assert r.status_code == 200

    def test_top_companies_returns_at_least_5(self, client):
        body = client.get("/api/market/top-companies").json()
        assert isinstance(body, list) and len(body) >= 5

    def test_top_companies_item_schema(self, client):
        body = client.get("/api/market/top-companies").json()
        item = body[0]
        assert isinstance(item["company"], str)
        assert isinstance(item["count"],   int)

    def test_top_companies_n_param(self, client):
        r3  = client.get("/api/market/top-companies", params={"n": 3}).json()
        r10 = client.get("/api/market/top-companies", params={"n": 10}).json()
        assert len(r3)  <= 3
        assert len(r10) <= 10
        assert len(r10) > len(r3)


class TestMarketOther:

    def test_regional_hiring_200(self, client):
        assert client.get("/api/market/regional-hiring").status_code == 200

    def test_job_internship_ratio_schema(self, client):
        body = client.get("/api/market/job-internship-ratio").json()
        assert isinstance(body["job_count"],        int)
        assert isinstance(body["internship_count"], int)
        assert isinstance(body["ratio"],            (int, float))

    def test_skill_gap_top_field(self, client):
        body = client.get("/api/market/skill-gap").json()
        assert isinstance(body["top_gap_skill"], str)
        assert len(body["skills"]) > 0

    def test_hiring_sources_list(self, client):
        body = client.get("/api/market/hiring-sources").json()
        assert isinstance(body, list) and len(body) > 0


class TestDemandForecast:

    def test_forecast_200(self, client):
        assert client.get("/api/market/demand-forecast").status_code == 200

    def test_forecast_returns_12_points(self, client):
        body = client.get("/api/market/demand-forecast").json()
        assert len(body) == 12

    def test_forecast_months_param(self, client):
        for months in (3, 6, 9, 12):
            body = client.get("/api/market/demand-forecast", params={"months": months}).json()
            assert len(body) == months, f"Expected {months} points, got {len(body)}"

    def test_forecast_bounds_order(self, client):
        body = client.get("/api/market/demand-forecast").json()
        for pt in body:
            assert pt["lower_bound"] <= pt["predicted_postings"] <= pt["upper_bound"], \
                f"Bounds violated: {pt}"

    def test_forecast_non_negative(self, client):
        body = client.get("/api/market/demand-forecast").json()
        for pt in body:
            assert pt["lower_bound"] >= 0
            assert pt["predicted_postings"] > 0


# =============================================================================
# Enrollment Intelligence
# =============================================================================

class TestEnrollmentSummary:

    def test_summary_200(self, client):
        assert client.get("/api/enrollment/summary").status_code == 200

    def test_summary_schema(self, client):
        body = client.get("/api/enrollment/summary").json()
        assert isinstance(body["total_students"],     int)
        assert isinstance(body["total_programs"],     int)
        assert isinstance(body["avg_placement_rate"], (int, float))
        assert isinstance(body["top_program"],        str)
        assert isinstance(body["enrollment_by_year"], dict)

    def test_summary_total_programs_12(self, client):
        body = client.get("/api/enrollment/summary").json()
        assert body["total_programs"] == 12

    def test_summary_placement_rate_realistic(self, client):
        body = client.get("/api/enrollment/summary").json()
        rate = body["avg_placement_rate"]
        assert 50 <= rate <= 100, f"Unrealistic placement rate: {rate}"


class TestEnrollmentForecast:

    def test_forecast_200(self, client):
        r = client.get("/api/enrollment/forecast", params={"program": "MS Data Science"})
        assert r.status_code == 200

    def test_forecast_schema(self, client):
        body = client.get("/api/enrollment/forecast",
                          params={"program": "MS Data Science", "years": 3}).json()
        assert isinstance(body["program"],    str)
        assert isinstance(body["historical"], list)
        assert isinstance(body["forecast"],   list)
        assert len(body["forecast"]) == 3

    def test_forecast_years_param(self, client):
        for years in (2, 3, 5):
            body = client.get("/api/enrollment/forecast",
                              params={"program": "MS Data Science", "years": years}).json()
            assert len(body["forecast"]) == years

    def test_forecast_all_12_programs(self, client):
        for prog in KNOWN_PROGRAMS:
            r = client.get("/api/enrollment/forecast", params={"program": prog})
            assert r.status_code == 200, f"Failed for program: {prog}"


class TestAdmissionRisk:

    def test_admission_risk_200(self, client):
        assert client.get("/api/enrollment/admission-risk").status_code == 200

    def test_admission_risk_schema(self, client):
        body = client.get("/api/enrollment/admission-risk").json()
        assert isinstance(body, list) and len(body) > 0
        item = body[0]
        assert isinstance(item["program"],            str)
        assert isinstance(item["risk_score"],         (int, float))
        assert isinstance(item["trend"],              str)
        assert isinstance(item["recommended_intake"], int)

    def test_admission_risk_scores_non_negative(self, client):
        body = client.get("/api/enrollment/admission-risk").json()
        for item in body:
            assert item["risk_score"] >= 0

    def test_admission_risk_trend_valid(self, client):
        body = client.get("/api/enrollment/admission-risk").json()
        valid = {"up", "down", "stable"}
        for item in body:
            assert item["trend"] in valid, f"Invalid trend: {item['trend']}"

    def test_admission_risk_limit_param(self, client):
        r5  = client.get("/api/enrollment/admission-risk", params={"limit": 5}).json()
        r12 = client.get("/api/enrollment/admission-risk", params={"limit": 12}).json()
        assert len(r5)  <= 5
        assert len(r12) <= 12
        assert len(r12) > len(r5)


class TestPlacementByStream:

    def test_placement_by_stream_200(self, client):
        assert client.get("/api/enrollment/placement-by-stream").status_code == 200

    def test_placement_by_stream_12_programs(self, client):
        body = client.get("/api/enrollment/placement-by-stream").json()
        assert len(body) == 12

    def test_placement_by_stream_program_names(self, client):
        body = client.get("/api/enrollment/placement-by-stream").json()
        names = {item["program"] for item in body}
        assert names.issubset(KNOWN_PROGRAMS), f"Unexpected programs: {names - KNOWN_PROGRAMS}"

    def test_placement_by_stream_schema(self, client):
        body = client.get("/api/enrollment/placement-by-stream").json()
        item = body[0]
        assert isinstance(item["placement_rate"], (int, float))
        assert isinstance(item["avg_salary"],     (int, float))
        assert isinstance(item["student_count"],  int)


# =============================================================================
# Placement Prediction (XGBoost + SHAP)
# =============================================================================

class TestPredictPlacement:

    def test_predict_placement_200(self, client):
        r = client.post("/api/enrollment/predict-placement", json=STRONG_STUDENT)
        assert r.status_code == 200

    def test_predict_placement_probability_0_to_1(self, client):
        body = client.post("/api/enrollment/predict-placement", json=STRONG_STUDENT).json()
        prob = body["placement_probability"]
        assert isinstance(prob, float)
        assert 0.0 <= prob <= 1.0, f"Probability out of range: {prob}"

    def test_predict_placement_schema(self, client):
        body = client.post("/api/enrollment/predict-placement", json=STRONG_STUDENT).json()
        assert isinstance(body["prediction"],  str)
        assert isinstance(body["base_value"],  (int, float))
        assert isinstance(body["shap_values"], list)
        assert len(body["shap_values"]) > 0

    def test_predict_placement_shap_schema(self, client):
        body = client.post("/api/enrollment/predict-placement", json=STRONG_STUDENT).json()
        sv = body["shap_values"][0]
        assert isinstance(sv["feature"], str)
        assert isinstance(sv["value"],   (int, float))
        assert isinstance(sv["shap"],    (int, float))

    def test_strong_student_placed(self, client):
        body = client.post("/api/enrollment/predict-placement", json=STRONG_STUDENT).json()
        assert body["prediction"] == "Placed"
        assert body["placement_probability"] > 0.5

    def test_directional_ordering(self, client):
        strong = client.post("/api/enrollment/predict-placement", json=STRONG_STUDENT).json()
        weak   = client.post("/api/enrollment/predict-placement", json=WEAK_STUDENT).json()
        assert weak["placement_probability"] < strong["placement_probability"], \
            f"weak {weak['placement_probability']:.3f} should be < strong {strong['placement_probability']:.3f}"

    def test_predict_missing_program_422(self, client):
        body = {k: v for k, v in STRONG_STUDENT.items() if k != "program"}
        r = client.post("/api/enrollment/predict-placement", json=body)
        assert r.status_code == 422

    def test_predict_invalid_gpa_422(self, client):
        body = {**STRONG_STUDENT, "gpa": 9.9}
        r = client.post("/api/enrollment/predict-placement", json=body)
        assert r.status_code == 422


class TestSkillRecommendations:

    def test_skill_recommendations_200(self, client):
        assert client.get("/api/enrollment/skill-recommendations").status_code == 200

    def test_skill_recommendations_schema(self, client):
        body = client.get("/api/enrollment/skill-recommendations").json()
        assert isinstance(body["recommendations"],      list)
        assert isinstance(body["alternative_pathways"], list)
        assert len(body["recommendations"]) > 0

    def test_skill_priority_valid(self, client):
        body = client.get("/api/enrollment/skill-recommendations").json()
        valid = {"High", "Medium", "Low"}
        for rec in body["recommendations"]:
            assert rec["priority"] in valid, f"Invalid priority: {rec['priority']}"


# =============================================================================
# Monitoring
# =============================================================================

class TestMonitoring:

    def test_drift_200(self, client):
        assert client.get("/api/monitoring/drift").status_code == 200

    def test_drift_schema(self, client):
        body = client.get("/api/monitoring/drift").json()
        assert isinstance(body["total_logged"],     int)
        assert isinstance(body["baseline"],         (int, float))
        assert isinstance(body["drift"],            (int, float))
        assert isinstance(body["alert"],            bool)
        assert isinstance(body["recommendation"],   str)

    def test_predictions_log_200(self, client):
        assert client.get("/api/monitoring/predictions").status_code == 200

    def test_predictions_log_list(self, client):
        body = client.get("/api/monitoring/predictions").json()
        assert isinstance(body, list)

    def test_predictions_n_param(self, client):
        r1  = client.get("/api/monitoring/predictions", params={"n": 1}).json()
        r10 = client.get("/api/monitoring/predictions", params={"n": 10}).json()
        assert len(r1) <= 1
        assert len(r10) <= 10


# =============================================================================
# Cross-Endpoint Consistency
# =============================================================================

class TestDataConsistency:

    def test_student_count_matches_streams(self, client):
        summary = client.get("/api/enrollment/summary").json()
        streams = client.get("/api/enrollment/placement-by-stream").json()
        stream_total = sum(s["student_count"] for s in streams)
        assert summary["total_students"] == stream_total, \
            f"summary total {summary['total_students']} != stream total {stream_total}"

    def test_top_program_in_known_list(self, client):
        body = client.get("/api/enrollment/summary").json()
        assert body["top_program"] in KNOWN_PROGRAMS
