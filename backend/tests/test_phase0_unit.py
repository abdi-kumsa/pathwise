"""Phase 0 unit tests that need the backend dependencies (FastAPI, PyJWT).

Run inside the backend container, no live server required:

    docker exec pathwise_backend sh -c "cd /app && python -m pytest tests/test_phase0_unit.py -q"
"""
from __future__ import annotations

import importlib
import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
jwt = pytest.importorskip("jwt")

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _auth(monkeypatch, env: str, secret: str | None):
    monkeypatch.setenv("ENV", env)
    if secret is None:
        monkeypatch.delenv("JWT_SECRET", raising=False)
    else:
        monkeypatch.setenv("JWT_SECRET", secret)
    from services import auth_service
    return importlib.reload(auth_service)


STRONG = "x" * 48


@pytest.mark.parametrize("secret", [None, "", "   ", "short", "pathwise-dev-secret-change-me-before-deploying"])
def test_production_refuses_unsafe_secret(monkeypatch, secret):
    a = _auth(monkeypatch, "production", secret)
    with pytest.raises(a.InsecureConfiguration):
        a.check_secret_configuration()


def test_production_accepts_strong_secret(monkeypatch):
    a = _auth(monkeypatch, "production", STRONG)
    a.check_secret_configuration()
    assert a.JWT_SECRET == STRONG


def test_dev_never_signs_with_an_empty_key(monkeypatch):
    a = _auth(monkeypatch, "dev", "")
    a.check_secret_configuration()          # warns, does not raise
    assert a.JWT_SECRET, "an empty JWT_SECRET must fall back, not be used as the key"
    assert len(a.JWT_SECRET.encode()) >= 32


def test_tokens_require_exp_and_sub(monkeypatch):
    a = _auth(monkeypatch, "production", STRONG)
    no_exp = jwt.encode({"sub": "admin", "role": "ADMIN"}, STRONG, algorithm="HS256")
    with pytest.raises(a.JWTError):
        a.decode_token(no_exp)
    good = a.create_access_token("admin", "ADMIN")
    assert a.decode_token(good)["sub"] == "admin"


def test_rate_limiter_blocks_after_limit(monkeypatch):
    from fastapi import HTTPException
    from services import rate_limit
    rate_limit.reset()
    for _ in range(3):
        rate_limit.hit("unit:a", 3, 60)
    with pytest.raises(HTTPException) as exc:
        rate_limit.hit("unit:a", 3, 60)
    assert exc.value.status_code == 429
    assert int(exc.value.headers["Retry-After"]) >= 1
    rate_limit.hit("unit:b", 3, 60)        # independent key unaffected
    rate_limit.reset()


def test_rate_limiter_window_slides(monkeypatch):
    from services import rate_limit
    rate_limit.reset()
    rate_limit.hit("unit:w", 1, 0.2)
    assert rate_limit.is_blocked("unit:w", 1, 0.2) is not None
    time.sleep(0.25)
    assert rate_limit.is_blocked("unit:w", 1, 0.2) is None
    rate_limit.reset()


def test_client_ip_uses_rightmost_forwarded_hop(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY", "1")
    from services import rate_limit
    rl = importlib.reload(rate_limit)

    class Req:
        headers = {"x-forwarded-for": "6.6.6.6, 203.0.113.9"}
        client = type("C", (), {"host": "10.0.0.1"})()

    assert rl.client_ip(Req()) == "203.0.113.9", "left-most entries are client-controlled"
    monkeypatch.setenv("TRUST_PROXY", "0")
    rl = importlib.reload(rate_limit)
    assert rl.client_ip(Req()) == "10.0.0.1"


def test_internal_errors_do_not_leak_detail():
    from fastapi import HTTPException
    from fastapi.testclient import TestClient
    import main

    @main.app.get("/__unit_probe_500")
    def _probe():
        try:
            raise ValueError("/app/services/secret.py column internal_x")
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    try:
        client = TestClient(main.app, raise_server_exceptions=False)
        r = client.get("/__unit_probe_500")
        assert r.status_code == 500
        assert "internal_x" not in r.text
        assert r.json()["ref"]
        # Deliberate 4xx detail is preserved.
        assert client.get("/api/users").status_code == 401
    finally:
        main.app.router.routes[:] = [
            rt for rt in main.app.router.routes if getattr(rt, "path", "") != "/__unit_probe_500"
        ]
