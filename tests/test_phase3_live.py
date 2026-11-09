"""Phase 3 live regression tests: sessions, headers, audit hygiene.

    BASE_URL=http://127.0.0.1:8000 pytest tests/test_phase3_live.py -q
"""
from __future__ import annotations

import os
import uuid

import httpx
import pytest

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "pathwise123")


def _up() -> bool:
    try:
        return httpx.get(f"{BASE_URL}/health", timeout=5).status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = [pytest.mark.live, pytest.mark.skipif(not _up(), reason="API not reachable")]


def _login(user: str, password: str = DEMO_PASSWORD) -> str:
    r = httpx.post(f"{BASE_URL}/api/auth/login", data={"username": user, "password": password}, timeout=60)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def scratch_user():
    admin = _login("admin")
    name = f"t_sess_{uuid.uuid4().hex[:6]}"
    password = "Session-Test-77"
    r = httpx.post(f"{BASE_URL}/api/users", headers=_h(admin), timeout=30, json={
        "username": name, "password": password, "role": "MOE", "display_name": "Scratch"})
    assert r.status_code == 201, r.text
    yield name, password, admin
    httpx.delete(f"{BASE_URL}/api/users/{name}/permanent", headers=_h(admin), timeout=30)


def test_demotion_ends_the_old_session_immediately(scratch_user):
    name, password, admin = scratch_user
    token = _login(name, password)
    assert httpx.get(f"{BASE_URL}/api/education/overview", headers=_h(token), timeout=60).status_code == 200
    assert httpx.patch(f"{BASE_URL}/api/users/{name}", headers=_h(admin), timeout=30,
                       json={"role": "MOL"}).status_code == 200
    r = httpx.get(f"{BASE_URL}/api/education/overview", headers=_h(token), timeout=60)
    assert r.status_code == 401
    assert "sign in again" in r.json()["detail"].lower()


def test_refresh_carries_the_current_role(scratch_user):
    name, password, _ = scratch_user
    token = _login(name, password)
    r = httpx.post(f"{BASE_URL}/api/auth/refresh", headers=_h(token), timeout=30)
    assert r.status_code == 200
    assert r.json()["user"]["role"] == "MOE"
    assert httpx.get(f"{BASE_URL}/api/auth/me", headers=_h(r.json()["access_token"]), timeout=30).status_code == 200


def test_admin_password_reset_ends_existing_sessions(scratch_user):
    name, password, admin = scratch_user
    token = _login(name, password)
    assert httpx.post(f"{BASE_URL}/api/users/{name}/password", headers=_h(admin), timeout=30,
                      json={"new_password": "Session-Test-99"}).status_code == 200
    assert httpx.get(f"{BASE_URL}/api/auth/me", headers=_h(token), timeout=30).status_code == 401


def test_api_responses_carry_security_headers():
    r = httpx.get(f"{BASE_URL}/api/auth/roles", timeout=30)
    assert r.headers["content-security-policy"].startswith("default-src 'none'")
    assert r.headers["cache-control"] == "no-store"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"


def test_page_view_only_stores_known_routes():
    admin = _login("admin")
    unknown = httpx.post(f"{BASE_URL}/api/auth/page-view", headers=_h(admin), timeout=30,
                         json={"path": "/" + "A" * 60})
    body = unknown.json()
    assert body["logged"] is False and body["reason"] == "unknown_route"
    known = httpx.post(f"{BASE_URL}/api/auth/page-view", headers=_h(admin), timeout=30,
                       json={"path": "/moe/simulator"})
    assert known.json()["logged"] is True


def test_audit_filters_treat_wildcards_literally_and_report_a_total():
    admin = _login("admin")
    every = httpx.get(f"{BASE_URL}/api/admin/audit-log", headers=_h(admin), timeout=30,
                      params={"limit": 1}).json()
    assert every["n"] == 1 and every["total"] >= 1
    wild = httpx.get(f"{BASE_URL}/api/admin/audit-log", headers=_h(admin), timeout=30,
                     params={"actor": "%", "limit": 1}).json()
    assert wild["total"] == 0, "'%' must match a literal percent sign, not everything"


def test_retention_purge_is_audited():
    admin = _login("admin")
    r = httpx.post(f"{BASE_URL}/api/admin/audit-log/purge", headers=_h(admin), timeout=60,
                   params={"retention_days": 3650})
    assert r.status_code == 200
    rows = httpx.get(f"{BASE_URL}/api/admin/audit-log", headers=_h(admin), timeout=30,
                     params={"action": "audit_retention", "limit": 1}).json()["rows"]
    assert rows and rows[0]["payload"]["retention_days"] == 3650


def test_retention_refuses_less_than_thirty_days():
    admin = _login("admin")
    r = httpx.post(f"{BASE_URL}/api/admin/audit-log/purge", headers=_h(admin), timeout=30,
                   params={"retention_days": 1})
    assert r.status_code == 422
