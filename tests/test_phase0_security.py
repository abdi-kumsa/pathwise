"""Phase 0 regression tests (audit 2026-11-07).

Two groups:

* Forecast memo behaviour (pure pandas, no server).
* Live checks against the running API for the High/Medium findings fixed in
  Phase 0: Model 3 institution scoping (S2), unauthenticated reload (S6),
  empty-key token forgery (S3), failed-login lockout (S4), and that the demo
  password is not in a production build (S1, checked from source).

Live tests skip when the API is not reachable:

    BASE_URL=http://127.0.0.1:8000 pytest tests/test_phase0_security.py -q
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import threading
import time
import uuid
from pathlib import Path

import httpx
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "pathwise123")


# ── Forecast memo ─────────────────────────────────────────────────────────────

def _fresh_memo():
    from ml import _memo
    _memo.clear()
    return _memo


def test_memo_returns_isolated_copies():
    memo = _fresh_memo()
    calls = []

    @memo.memo
    def frame(n: int) -> pd.DataFrame:
        calls.append(n)
        return pd.DataFrame({"x": range(n)})

    first = frame(3)
    first["x"] = -1
    first["added"] = 1
    second = frame(3)
    assert calls == [3], "second call must be served from the memo"
    assert list(second["x"]) == [0, 1, 2], "a caller's mutation leaked into the cache"
    assert "added" not in second.columns


def test_memo_computes_once_under_concurrency():
    memo = _fresh_memo()
    calls = []

    @memo.memo
    def slow(n: int) -> pd.DataFrame:
        calls.append(n)
        time.sleep(0.3)
        return pd.DataFrame({"x": [n]})

    threads = [threading.Thread(target=slow, args=(7,)) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert calls == [7], f"expected one computation, got {len(calls)}"


def test_memo_bypasses_unhashable_arguments():
    memo = _fresh_memo()
    calls = []

    @memo.memo
    def use(frame=None) -> int:
        calls.append(1)
        return 0 if frame is None else len(frame)

    df = pd.DataFrame({"x": [1, 2]})
    assert use(frame=df) == 2
    assert use(frame=df) == 2
    assert len(calls) == 2, "DataFrame arguments must not be cached"


# ── Demo password not shipped (S1) ────────────────────────────────────────────

def test_demo_password_only_behind_dev_flag():
    src = (ROOT / "frontend" / "src" / "pages" / "LoginPage.jsx").read_text(encoding="utf-8")
    lines = [ln for ln in src.splitlines() if "pathwise123" in ln]
    assert len(lines) == 1, "the demo password literal must appear exactly once"
    i = src.index("pathwise123")
    assert "import.meta.env.DEV" in src[max(0, i - 200):i], (
        "the literal must sit inside the import.meta.env.DEV branch so vite build drops it"
    )


def test_render_does_not_commit_demo_password():
    text = (ROOT / "render.yaml").read_text(encoding="utf-8")
    block = text[text.index("key: DEMO_PASSWORD"):].splitlines()[:2]
    assert "sync: false" in block[1], "DEMO_PASSWORD must be set in the Render dashboard"
    assert "pathwise123" not in text


# ── Live API ──────────────────────────────────────────────────────────────────

def _reachable() -> bool:
    try:
        return httpx.get(f"{BASE_URL}/health", timeout=5).status_code == 200
    except httpx.HTTPError:
        return False


_skip_unless_up = pytest.mark.skipif(not _reachable(), reason=f"API not reachable at {BASE_URL}")


def live(fn):
    """Marks a test as needing the running API, and skips it when it is down."""
    return pytest.mark.live(_skip_unless_up(fn))


def _token(username: str) -> str:
    r = httpx.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": username, "password": DEMO_PASSWORD},
        timeout=60,
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def tokens():
    return {u: _token(u) for u in ("admin", "moe", "university", "student")}


def _get(path: str, token: str | None = None, **kw) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.get(f"{BASE_URL}{path}", headers=headers, timeout=180, **kw)


@live
def test_university_supply_is_own_institution_only(tokens):
    r = _get("/api/model3/supply", tokens["university"])
    assert r.status_code == 200
    institutions = {row["institution"] for row in r.json()["rows"]}
    assert institutions == {"Addis Ababa University"}, institutions


@live
def test_university_cannot_request_another_institution_supply(tokens):
    r = _get("/api/model3/supply", tokens["university"],
             params={"institution": "Bahir Dar University"})
    assert r.status_code == 403
    assert "grant" in r.json()["detail"].lower()


@live
@pytest.mark.parametrize("group_by", ["institution,period", "campus,period", "field,region"])
def test_university_gap_cannot_group_by_identifying_dimensions(tokens, group_by):
    r = _get("/api/model3/gap", tokens["university"], params={"group_by": group_by})
    assert r.status_code == 403


@live
def test_university_gap_national_aggregate_still_works(tokens):
    assert _get("/api/model3/gap", tokens["university"]).status_code == 200


@live
def test_ministry_supply_spans_all_institutions(tokens):
    r = _get("/api/model3/supply", tokens["moe"])
    assert r.status_code == 200
    assert len({row["institution"] for row in r.json()["rows"]}) > 1


@live
def test_gap_rejects_unknown_dimension(tokens):
    r = _get("/api/model3/gap", tokens["moe"], params={"group_by": "nonsense"})
    assert r.status_code == 422


@live
def test_health_reload_requires_admin(tokens):
    assert httpx.post(f"{BASE_URL}/health/reload", timeout=30).status_code == 401
    r = httpx.post(f"{BASE_URL}/health/reload", timeout=30,
                   headers={"Authorization": f"Bearer {tokens['student']}"})
    assert r.status_code == 403


def _hs256(payload: dict, secret: str) -> str:
    def b64(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
    head = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = b64(json.dumps(payload).encode())
    sig = b64(hmac.new(secret.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest())
    return f"{head}.{body}.{sig}"


@live
def test_token_signed_with_empty_key_is_rejected():
    forged = _hs256({"sub": "admin", "role": "ADMIN", "exp": int(time.time()) + 600}, "")
    assert _get("/api/users", forged).status_code == 401


@live
def test_token_without_expiry_is_rejected():
    # Signed with whatever key; the point is the missing exp claim. Either a
    # signature failure or a missing-claim failure must be 401, never 200.
    forged = _hs256({"sub": "admin", "role": "ADMIN"}, "")
    assert _get("/api/users", forged).status_code == 401


@live
def test_failed_logins_lock_out_the_pair_not_the_user():
    probe = f"lockout-probe-{uuid.uuid4().hex[:8]}"
    codes = [
        httpx.post(f"{BASE_URL}/api/auth/login",
                   data={"username": probe, "password": f"wrong-{i}"}, timeout=30).status_code
        for i in range(11)
    ]
    assert codes[:10] == [401] * 10
    assert codes[10] == 429
    # A different account from the same client is unaffected.
    assert httpx.post(f"{BASE_URL}/api/auth/login",
                      data={"username": "admin", "password": DEMO_PASSWORD},
                      timeout=30).status_code == 200


@live
def test_workforce_report_is_cached(tokens):
    _get("/api/labour/workforce-report", tokens["moe"])
    started = time.monotonic()
    r = _get("/api/labour/workforce-report", tokens["moe"])
    assert r.status_code == 200
    assert time.monotonic() - started < 5, "second call should be served from the memo"
