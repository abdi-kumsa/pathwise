"""
In-process sliding-window rate limiting.

Audit finding S4: no endpoint was rate limited, so a single account could
brute-force the login form or pin the CPU with expensive reports. This module
adds per-key limits without a new dependency.

Scope and limits of the design:

* State lives in this process. That is correct for the current deployment
  (one uvicorn worker locally and on Render). With several workers each one
  keeps its own counters, so the effective limit multiplies by the worker
  count; move the store to Redis before scaling out (plan item 3.3).
* Client identity behind a proxy. On Render every request reaches uvicorn from
  the proxy's address, which would put all users in one bucket. With
  TRUST_PROXY=1 the right-most X-Forwarded-For entry is used: that is the hop
  the trusted proxy appended, so a client cannot spoof it by sending its own
  header (it can only add entries to the left).
* RATE_LIMIT_SCALE multiplies every limit (e.g. 10 for a load test) and
  RATE_LIMIT_ENABLED=0 disables limiting entirely.
"""
from __future__ import annotations

import os
import threading
import time
from collections import deque

from fastapi import Depends, HTTPException, Request, status

_ENABLED = (os.getenv("RATE_LIMIT_ENABLED") or "1").strip() not in ("0", "false", "no")
_SCALE = max(float(os.getenv("RATE_LIMIT_SCALE") or "1"), 0.01)
_TRUST_PROXY = (os.getenv("TRUST_PROXY") or "0").strip() in ("1", "true", "yes")

_hits: dict[str, deque] = {}
_guard = threading.Lock()
_last_sweep = time.monotonic()
_SWEEP_EVERY = 300.0


def client_ip(request: Request) -> str:
    if _TRUST_PROXY:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


def _sweep(now: float) -> None:
    """Drop idle keys so the dict cannot grow without bound."""
    global _last_sweep
    if now - _last_sweep < _SWEEP_EVERY:
        return
    _last_sweep = now
    for key in [k for k, q in _hits.items() if not q or now - q[-1] > 3600]:
        _hits.pop(key, None)


def _limit(limit: int) -> int:
    return max(1, int(round(limit * _SCALE)))


def hit(key: str, limit: int, window: float) -> None:
    """Record one hit; raise 429 if `key` already used `limit` in `window` s."""
    if not _ENABLED:
        return
    limit = _limit(limit)
    now = time.monotonic()
    with _guard:
        _sweep(now)
        q = _hits.setdefault(key, deque())
        while q and now - q[0] >= window:
            q.popleft()
        if len(q) >= limit:
            retry = max(1, int(window - (now - q[0])) + 1)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please wait and try again.",
                headers={"Retry-After": str(retry)},
            )
        q.append(now)


def is_blocked(key: str, limit: int, window: float) -> int | None:
    """Seconds until `key` may try again, or None if it is under the limit."""
    if not _ENABLED:
        return None
    limit = _limit(limit)
    now = time.monotonic()
    with _guard:
        q = _hits.get(key)
        if not q:
            return None
        while q and now - q[0] >= window:
            q.popleft()
        if len(q) < limit:
            return None
        return max(1, int(window - (now - q[0])) + 1)


def record(key: str) -> None:
    """Record a hit without checking (used for failed-login counting)."""
    if not _ENABLED:
        return
    with _guard:
        _hits.setdefault(key, deque()).append(time.monotonic())


def forget_account(username: str) -> None:
    """Clear failed-attempt counters for one account, from every IP.

    Called when an administrator reactivates an account or resets its
    password: the intervention is the unlock, so the user is not left locked
    out by attempts made while the account was disabled or forgotten.
    """
    suffix = f":{username.strip().lower()}"
    with _guard:
        for key in [k for k in _hits if k.startswith("login-fail:") and k.endswith(suffix)]:
            _hits.pop(key, None)
        _hits.pop(f"change-password-fail{suffix}", None)


def reset() -> None:
    """Clear every counter. Used by tests."""
    with _guard:
        _hits.clear()


def per_ip(name: str, limit: int, window: float):
    """Dependency: `limit` requests per `window` seconds per client IP."""
    def _dep(request: Request) -> None:
        hit(f"{name}:ip:{client_ip(request)}", limit, window)
    return _dep


def per_user(name: str, limit: int, window: float):
    """Dependency: `limit` requests per `window` seconds per signed-in user."""
    from services.auth_service import get_current_user

    def _dep(user: dict = Depends(get_current_user)) -> dict:
        hit(f"{name}:user:{user['username']}", limit, window)
        return user
    return _dep
