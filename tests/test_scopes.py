"""SCOPE.STU / SCOPE.UNI — live 200/403 matrix for widget endpoints.

Requires the Docker API:

    BASE_URL=http://127.0.0.1:8000 pytest tests/test_scopes.py -q
"""
from __future__ import annotations

import json
import os

import httpx
import pytest

from backend import spec_registry as S

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "pathwise123")

_TOKENS: dict[str, str] = {}
ALL_USERS = ("student", "university", "moe", "mol", "admin")
ARRAY_ENDPOINTS = set()

ADMIN_PATHS = [
    "/api/admin/platform-health",
    "/api/admin/pipeline-status",
    "/api/admin/data-quality",
    "/api/admin/scenarios",
    "/api/admin/audit-log",
    "/api/methodology/feature-importance",
    "/api/methodology/priority-tiers",
    "/api/methodology/model-comparison",
    "/api/methodology/expert-validations",
    "/api/ahp/weights",
    "/api/ahp/consistency",
    "/api/users",
    "/api/monitoring/drift",
]

STUDENT_PATHS = [
    "/api/student/profile",
    "/api/student/labour-outlook",
    "/api/student/demand-comparison",
    "/api/student/field-alignment",
    "/api/student/supply-demand-gap",
    "/api/student/alternatives",
    "/api/student/skill-gaps",
    "/api/student/pathways",
    "/api/student/opportunities",
]
UNI_PATHS = [
    "/api/institution/me",
    "/api/institution/program-health",
    "/api/institution/demand-vs-labour",
    "/api/institution/funnel",
    "/api/institution/cohort-progression",
    "/api/institution/graduate-outcomes",
    "/api/institution/resource-planning",
    "/api/institution/curriculum-alignment",
]
MOE_PATHS = [
    "/api/education/overview",
    "/api/education/demand-constrained-comparison",
    "/api/education/supply-demand-gap",
    "/api/education/policy-simulator",
    "/api/education/institution-comparison",
    "/api/education/policy-impact",
    "/api/education/regional-alignment",
    "/api/education/investment-priority",
    "/api/model3/policy-priority",
]
MOL_PATHS = [
    "/api/labour/overview",
    "/api/labour/graduate-absorption",
    "/api/labour/workforce-report",
    "/api/model2/formal-informal",
    "/api/model2/forecast",
    "/api/model2/skills-shortage",
    "/api/model2/public-pipeline",
    "/api/model2/fdi-pipeline",
    "/api/model2/migration",
]


def _login(username: str) -> str:
    if username not in _TOKENS:
        r = httpx.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": username, "password": DEMO_PASSWORD},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        _TOKENS[username] = r.json()["access_token"]
    return _TOKENS[username]


def _get(user: str, path: str, **params) -> httpx.Response:
    return httpx.get(
        f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {_login(user)}"},
        params=params,
        timeout=180,
    )


def _allowed_users(path: str) -> set[str]:
    if path.startswith("/api/student"):
        return {"student", "admin"}
    if path.startswith("/api/institution"):
        return {"university", "admin"}
    if path.startswith("/api/education"):
        return {"moe", "admin"}
    if path.startswith("/api/labour") or path.startswith("/api/model2"):
        return {"mol", "moe", "admin"}
    if path.startswith("/api/model1"):
        return {"moe", "university", "admin"}
    if path.startswith("/api/model3"):
        return {"moe", "mol", "university", "admin"}
    return {"admin"}


def _widget_endpoints():
    return [
        (w["id"], w["satisfied_by"]["endpoint"])
        for w in S.widgets()
    ]


@pytest.fixture(scope="module")
def api_up():
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=10)
    except Exception as exc:
        pytest.skip(f"API not reachable at {BASE_URL}: {exc}")
    if r.status_code != 200:
        pytest.skip(f"API health {r.status_code}")


@pytest.mark.parametrize("path", STUDENT_PATHS)
def test_student_paths_allow_student_and_admin(api_up, path):
    assert _get("student", path).status_code == 200
    assert _get("admin", path).status_code == 200


@pytest.mark.parametrize("path", STUDENT_PATHS)
@pytest.mark.parametrize("user", ["moe", "mol", "university"])
def test_student_paths_forbid_other_roles(api_up, path, user):
    assert _get(user, path).status_code == 403


@pytest.mark.parametrize("path", UNI_PATHS)
def test_university_paths_allow_university_and_admin(api_up, path):
    assert _get("university", path).status_code == 200
    assert _get("admin", path).status_code == 200


@pytest.mark.parametrize("path", UNI_PATHS)
@pytest.mark.parametrize("user", ["student", "moe", "mol"])
def test_university_paths_forbid_other_roles(api_up, path, user):
    assert _get(user, path).status_code == 403


def test_student_profile_ignores_forged_username(api_up):
    r = _get("student", "/api/student/profile", username="admin", student_id="999")
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "student"
    assert body["program"] == "BSc Civil Engineering"
    assert body["field"] == "Engineering & Technology"


def test_university_forged_institution_is_403_without_grant(api_up):
    r = _get("university", "/api/institution/me", institution="Hawassa University")
    assert r.status_code == 403
    assert "grant" in r.json()["detail"].lower()


def test_university_own_institution_still_aau(api_up):
    r = _get("university", "/api/institution/me")
    assert r.status_code == 200
    assert r.json()["institution"] == "Addis Ababa University"


@pytest.mark.parametrize("path", MOE_PATHS)
def test_moe_paths_allow_moe_and_admin(api_up, path):
    assert _get("moe", path).status_code == 200
    assert _get("admin", path).status_code == 200


@pytest.mark.parametrize("path", [p for p in MOE_PATHS if p.startswith("/api/education/")])
@pytest.mark.parametrize("user", ["student", "university", "mol"])
def test_moe_education_paths_forbid_other_roles(api_up, path, user):
    assert _get(user, path).status_code == 403


@pytest.mark.parametrize("path", MOL_PATHS)
def test_mol_paths_allow_mol_and_admin(api_up, path):
    assert _get("mol", path).status_code == 200
    assert _get("admin", path).status_code == 200


@pytest.mark.parametrize("path", MOL_PATHS)
def test_mol_paths_allow_moe_labour_read(api_up, path):
    assert _get("moe", path).status_code == 200


@pytest.mark.parametrize("path", MOL_PATHS)
@pytest.mark.parametrize("user", ["student", "university"])
def test_mol_paths_forbid_student_and_university(api_up, path, user):
    assert _get(user, path).status_code == 403


def test_student_forbidden_on_education_overview(api_up):
    assert _get("student", "/api/education/overview").status_code == 403


def test_mol_forbidden_on_institution_me(api_up):
    assert _get("mol", "/api/institution/me").status_code == 403


def test_student_forbidden_on_model1_and_model2(api_up):
    assert _get("student", "/api/model1/demand/unconstrained").status_code == 403
    assert _get("student", "/api/model2/forecast").status_code == 403


@pytest.mark.parametrize("path", ADMIN_PATHS)
def test_admin_paths_allow_admin(api_up, path):
    r = _get("admin", path)
    assert r.status_code == 200, r.text
    body = r.json()
    if path in ARRAY_ENDPOINTS:
        assert isinstance(body, list) and body, "empty 200 is forbidden for admin ops"
    else:
        assert isinstance(body, dict)
        assert body, "empty 200 is forbidden for admin ops"


@pytest.mark.parametrize("path", ADMIN_PATHS)
@pytest.mark.parametrize("user", ["student", "university", "moe", "mol"])
def test_admin_paths_forbid_other_roles(api_up, path, user):
    assert _get(user, path).status_code == 403


def test_pipeline_has_twenty_feeds(api_up):
    r = _get("admin", "/api/admin/pipeline-status")
    assert r.status_code == 200
    body = r.json()
    assert body["n"] == 20
    assert len(body["feeds"]) == 20
    families = {f["family"] for f in body["feeds"]}
    assert families == {"education", "labor", "policy", "investment"}


def test_admin_audit_log_is_searchable(api_up):
    r = _get("admin", "/api/admin/audit-log", action="report_export")
    assert r.status_code == 200
    body = r.json()
    assert "rows" in body
    for row in body["rows"]:
        assert "report_export" in row.get("action", "")


def test_student_forbidden_on_audit_log(api_up):
    assert _get("student", "/api/admin/audit-log").status_code == 403


def test_widget_endpoints_match_yaml_forty_four():
    paths = [p for _, p in _widget_endpoints()]
    assert len(paths) == 44
    assert len(set(paths)) == 44


@pytest.mark.parametrize("wid,path", _widget_endpoints())
@pytest.mark.parametrize("user", ALL_USERS)
def test_widget_endpoint_rbac(api_up, wid, path, user):
    r = _get(user, path)
    if user in _allowed_users(path):
        assert r.status_code == 200, (wid, path, user, r.text)
        body = r.json()
        if path in ARRAY_ENDPOINTS:
            assert isinstance(body, list) and body, (wid, path)
        else:
            assert body, (wid, path, "empty 200 is forbidden")
    else:
        assert r.status_code == 403, (wid, path, user, r.status_code)


def test_student_alternatives_do_not_leak_other_accounts(api_up):
    r = _get("student", "/api/student/alternatives")
    assert r.status_code == 200, r.text
    blob = json.dumps(r.json()).lower()
    for other in ("admin", "moe", "mol", "university"):
        assert f'"username": "{other}"' not in blob
        assert f'"student_id": "{other}"' not in blob


def test_student_opportunities_do_not_leak_other_accounts(api_up):
    r = _get("student", "/api/student/opportunities")
    assert r.status_code == 200, r.text
    blob = json.dumps(r.json()).lower()
    for other in ("admin", "moe", "mol", "university"):
        assert f'"username": "{other}"' not in blob
        assert f'"student_id": "{other}"' not in blob
