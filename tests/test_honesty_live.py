"""Wave 8 live honesty — provenance, RANK.R3, and copy gates.

Requires the Docker API:

    BASE_URL=http://127.0.0.1:8000 pytest tests/test_honesty_live.py -q
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest

from backend import spec_registry as S

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "pathwise123")
ROOT = Path(__file__).resolve().parent.parent

ROLE_USER = {
    "STUDENT": "student",
    "UNIVERSITY": "university",
    "MOE": "moe",
    "MOL": "mol",
    "ADMIN": "admin",
}

_TOKENS: dict[str, str] = {}

ALLOWED_TIERS = {"simulated", "derived"}
ARRAY_ENDPOINTS = set()

RANKING_PATHS = [
    ("student", "/api/student/alternatives"),
    ("student", "/api/student/field-alignment"),
    ("moe", "/api/model3/policy-priority"),
    ("university", "/api/institution/program-health"),
    ("university", "/api/institution/expansion"),
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


def _get(user: str, path: str) -> httpx.Response:
    return httpx.get(
        f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {_login(user)}"},
        timeout=180,
    )


@pytest.fixture(scope="module")
def api_up():
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=10)
    except Exception as exc:
        pytest.skip(f"API not reachable at {BASE_URL}: {exc}")
    if r.status_code != 200:
        pytest.skip(f"API health {r.status_code}")


def _widget_gets():
    return [
        (w["id"], ROLE_USER[w["role"]], w["satisfied_by"]["endpoint"])
        for w in S.widgets()
    ]


@pytest.mark.parametrize("wid,user,path", _widget_gets())
def test_widget_get_has_simulated_or_derived_provenance(api_up, wid, user, path):
    r = _get(user, path)
    assert r.status_code == 200, (wid, path, r.text)
    body = r.json()
    if path in ARRAY_ENDPOINTS:
        assert isinstance(body, list) and body, (wid, "WV.USERS1: list is unstamped")
        return
    assert isinstance(body, dict), (wid, path, type(body))
    prov = body.get("provenance") or {}
    assert prov.get("tier") in ALLOWED_TIERS, (wid, path, prov)
    assert prov.get("tier") != "official"
    caveat = (prov.get("caveat") or "") + " " + (body.get("note") or "")
    assert "not official" in caveat.lower(), (wid, path, caveat)


@pytest.mark.parametrize("user,path", RANKING_PATHS)
def test_ranking_payloads_declare_weights_and_method(api_up, user, path):
    r = _get(user, path)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("fit_classification_used") is False, path
    assert body.get("method"), path
    assert body.get("weights") is not None, path
    factors = body.get("ranking_factors") or list(body["weights"])
    blob = json.dumps(factors).lower()
    assert "fit_class" not in blob
    rows = body.get("rows") or body.get("programs") or []
    assert rows, path
    sample = json.dumps(rows[0]).lower()
    assert "fit_class" not in sample or "fit_classification_used" in sample


def test_frontend_does_not_claim_official_ethiopia_without_caveat():
    pages = ROOT / "frontend" / "src"
    offenders = []
    for path in pages.rglob("*.jsx"):
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        if "official" not in lower:
            continue
        has_caveat = (
            "not official" in lower
            or "unofficial" in lower
            or "simulated" in lower
            or "official_forecast" in lower
        )
        if not has_caveat:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == [], f"claims official without caveat: {offenders}"


def test_collection_priority_absent_under_ml():
    hits = []
    ml = ROOT / "ml"
    for path in ml.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix in {".pyc", ".pkl", ".keras", ".json", ".png"}:
            continue
        if "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "collection_priority" in text:
            hits.append(str(path.relative_to(ROOT)))
    assert hits == [], f"collection_priority leaked into ml/: {hits}"


def test_mismatch_service_does_not_stamp_ethiopia_label():
    text = (ROOT / "backend" / "services" / "mismatch_service.py").read_text(encoding="utf-8")
    assert "DATASET_LABEL" not in text
    assert "Simulated Ethiopian structure" not in text


def test_student_alignment_uses_jwt_field(api_up):
    r = _get("student", "/api/student/field-alignment")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("field") == "Engineering & Technology"
    own = [row for row in body.get("rows") or [] if row.get("is_own_field")]
    assert own and own[0]["field"] == "Engineering & Technology"


def test_labour_outlook_cell_size(api_up):
    r = _get("student", "/api/student/labour-outlook")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("min_cell_size") == 5
    if body.get("cell_withheld"):
        assert body.get("occupations") == []
