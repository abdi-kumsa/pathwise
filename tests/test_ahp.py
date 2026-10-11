"""PROC.S7 — AHP is a separate methodology, never a learner hook."""
from __future__ import annotations

from pathlib import Path

import pytest

from ml.ahp import AhpRefused, consistency_ratio, weigh

ROOT = Path(__file__).resolve().parent.parent
CONSISTENT_3 = [
    [1.0, 2.0, 4.0],
    [0.5, 1.0, 2.0],
    [0.25, 0.5, 1.0],
]
INCONSISTENT_3 = [
    [1.0, 9.0, 1.0],
    [1.0 / 9.0, 1.0, 9.0],
    [1.0, 1.0 / 9.0, 1.0],
]


def test_consistent_3x3_weights_sum_to_one():
    out = weigh(CONSISTENT_3, ["a", "b", "c"])
    assert out["refused"] is False
    assert out["consistency_ratio"] <= 0.1
    assert pytest.approx(out["sum"], abs=1e-6) == 1.0
    assert pytest.approx(sum(out["weights"].values()), abs=1e-6) == 1.0


def test_inconsistent_matrix_is_refused():
    report = consistency_ratio(INCONSISTENT_3)
    assert report["consistency_ratio"] > 0.1
    assert report["usable"] is False
    assert report["weights"] is None
    with pytest.raises(AhpRefused) as exc:
        weigh(INCONSISTENT_3, ["a", "b", "c"])
    assert exc.value.detail["weights"] is None
    assert exc.value.detail["refused"] is True


def test_ahp_not_imported_by_learners():
    """AHP must not enter model1/model2 or a training script."""
    ml = ROOT / "ml"
    offenders = []
    for folder in (ml / "model1", ml / "model2"):
        for path in folder.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "ml.ahp" in text or "from ahp" in text or "import ahp" in text:
                offenders.append(str(path.relative_to(ROOT)))
    for path in ml.rglob("*.py"):
        if "ahp" in path.parts:
            continue
        name = path.name.lower()
        if "train" not in name and "fit" not in name:
            continue
        text = path.read_text(encoding="utf-8")
        if "ml.ahp" in text or "from ahp" in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == [], f"AHP imported from a learner: {offenders}"


def test_live_inconsistent_ahp_returns_422():
    """POST CR>0.1 as admin → 422, weights null. Skip if Docker API is down."""
    import os

    import httpx

    base = os.getenv("BASE_URL", "http://127.0.0.1:8000")
    password = os.getenv("DEMO_PASSWORD", "pathwise123")
    try:
        health = httpx.get(f"{base}/health", timeout=10)
    except Exception as exc:
        pytest.skip(f"API not reachable at {base}: {exc}")
    if health.status_code != 200:
        pytest.skip(f"API health {health.status_code}")
    login = httpx.post(
        f"{base}/api/auth/login",
        data={"username": "admin", "password": password},
        timeout=30,
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    r = httpx.post(
        f"{base}/api/ahp/weights",
        headers={"Authorization": f"Bearer {token}"},
        json={"matrix": INCONSISTENT_3, "labels": ["a", "b", "c"], "model": "M1"},
        timeout=30,
    )
    assert r.status_code == 422, r.text
    detail = r.json().get("detail")
    assert isinstance(detail, dict), detail
    assert detail.get("weights") is None
    assert detail.get("refused") is True
