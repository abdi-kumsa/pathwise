"""
Concurrent load test for every DOC2 widget endpoint (plan items 3.1–3.3).

Each simulated user signs in as the role that owns a widget and requests it;
USERS such users run at once, each making ROUNDS passes over the widget list.
Reports p50 / p95 / max latency per endpoint and fails when any p95 exceeds
the target.

    python scripts/load_test.py                       # 5 users x 3 rounds, target 5 s
    python scripts/load_test.py --users 10 --rounds 2 --target 5
    BASE_URL=https://api.example.org python scripts/load_test.py

Uses only the standard library plus httpx (already a backend dependency).
Rate limits apply per user; run against a stack with RATE_LIMIT_SCALE raised
if you push past the defaults.
"""
from __future__ import annotations

import argparse
import os
import statistics
import sys
import threading
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
PASSWORD = os.getenv("DEMO_PASSWORD", "pathwise123")
ROLE_USER = {"STUDENT": "student", "UNIVERSITY": "university", "MOE": "moe",
             "MOL": "mol", "ADMIN": "admin"}


_PREFIX_ROLE = {"W.STU": "STUDENT", "W.UNI": "UNIVERSITY", "W.MOE": "MOE",
                "W.MOL": "MOL", "W.ADM": "ADMIN"}


def widget_endpoints() -> list[tuple[str, str]]:
    """(demo user, endpoint) for every DOC2 widget, from docs/spec/widgets.yaml."""
    from backend import spec_registry as S
    out = set()
    for w in S.widgets():
        ep = (w.get("satisfied_by") or {}).get("endpoint")
        role = _PREFIX_ROLE.get(w["id"][:5])
        if ep and role and "{" not in ep:
            out.add((ROLE_USER[role], ep))
    return sorted(out)


def login(user: str) -> str:
    r = httpx.post(f"{BASE_URL}/api/auth/login",
                   data={"username": user, "password": PASSWORD}, timeout=60)
    r.raise_for_status()
    return r.json()["access_token"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=5)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--target", type=float, default=5.0, help="p95 target in seconds")
    args = ap.parse_args()

    endpoints = widget_endpoints()
    tokens = {u: login(u) for u in {u for u, _ in endpoints}}
    timings: dict[str, list[float]] = {ep: [] for _, ep in endpoints}
    errors: dict[str, int] = {ep: 0 for _, ep in endpoints}
    limited: dict[str, int] = {ep: 0 for _, ep in endpoints}
    lock = threading.Lock()

    def worker(offset: int) -> None:
        with httpx.Client(base_url=BASE_URL, timeout=120) as c:
            for _round in range(args.rounds):
                order = endpoints[offset % len(endpoints):] + endpoints[:offset % len(endpoints)]
                for user, ep in order:
                    t0 = time.perf_counter()
                    resp = c.get(ep, headers={"Authorization": f"Bearer {tokens[user]}"})
                    dt = time.perf_counter() - t0
                    with lock:
                        timings[ep].append(dt)
                        # Simulated users share one demo account per role, so
                        # per-user rate limits trip by design; counted apart.
                        if resp.status_code == 429:
                            limited[ep] += 1
                        elif resp.status_code != 200:
                            errors[ep] += 1

    started = time.perf_counter()
    threads = [threading.Thread(target=worker, args=(i * 7,)) for i in range(args.users)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    wall = time.perf_counter() - started

    print(f"{args.users} concurrent users x {args.rounds} rounds over {len(endpoints)} widget endpoints "
          f"in {wall:.1f} s against {BASE_URL}\n")
    print(f"{'endpoint':52s} {'p50':>7s} {'p95':>7s} {'max':>7s} {'err':>4s} {'429':>4s}")
    worst = 0.0
    failed = []
    for _, ep in endpoints:
        ts = sorted(timings[ep])
        p50 = statistics.median(ts)
        p95 = ts[min(len(ts) - 1, int(round(0.95 * (len(ts) - 1))))]
        worst = max(worst, p95)
        flag = " <-- over target" if p95 > args.target else ""
        if p95 > args.target or errors[ep]:
            failed.append(ep)
        print(f"{ep:52s} {p50:7.2f} {p95:7.2f} {max(ts):7.2f} {errors[ep]:4d} {limited[ep]:4d}{flag}")
    print(f"\nworst p95 {worst:.2f} s (target {args.target:.1f} s); "
          f"{'PASS' if not failed else 'FAIL: ' + ', '.join(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
