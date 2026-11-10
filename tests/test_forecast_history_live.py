"""Forecast endpoints carry the observed history their charts draw (live API).

    BASE_URL=http://127.0.0.1:8000 pytest tests/test_forecast_history_live.py -q
"""
from __future__ import annotations

import os

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


def _get(user: str, path: str, **params) -> dict:
    r = httpx.post(f"{BASE_URL}/api/auth/login",
                   data={"username": user, "password": DEMO_PASSWORD}, timeout=60)
    assert r.status_code == 200, r.text
    tok = r.json()["access_token"]
    r = httpx.get(f"{BASE_URL}{path}", params=params,
                  headers={"Authorization": f"Bearer {tok}"}, timeout=120)
    assert r.status_code == 200, r.text
    return r.json()


def test_university_demand_history_is_scoped_to_the_callers_institution():
    me = _get("university", "/api/institution/me")
    inst = me.get("institution") or me.get("profile", {}).get("institution")
    for path in ("/api/model1/demand/unconstrained", "/api/model1/demand/constrained"):
        body = _get("university", path, horizon=3, group_by="program,academic_year")
        hist = body["history"]
        assert hist, path
        assert {"academic_year", "applications", "enrollment"} <= set(hist[0])
        if inst:
            assert {h["institution"] for h in hist} == {inst}
        first_forecast = min(r["academic_year"] for r in body["rows"])
        assert max(h["academic_year"] for h in hist) == first_forecast - 1


def test_model2_history_matches_the_grain():
    sector = _get("mol", "/api/model2/forecast", horizon=3, group_by="sector,period")
    assert sector["history"] and "employment_demand" in sector["history"][0]
    assert {"employment_demand_low", "employment_demand_high"} <= set(sector["rows"][0])

    occ = _get("mol", "/api/model2/forecast", horizon=3, group_by="occupation,period")
    assert occ["history"] and "vacancies" in occ["history"][0]
    # Employment has no occupation series, so none is invented for the grain.
    assert "employment_demand" not in occ["history"][0]
