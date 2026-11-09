"""Test classification for the root suite.

Two markers are applied here so every module does not have to repeat them:

* ``live``   — needs the running API at BASE_URL (docker compose up).
* ``legacy`` — exercises the leftover US model artefacts (placement / salary
  XGBoost, LSTM, Prophet, SHAP; waiver WV.US1) and needs TensorFlow, Prophet,
  XGBoost and SHAP installed.

The default CI job runs ``pytest -m "not live and not legacy"``: no Docker, no
heavy ML packages, a few minutes. A second job brings the stack up and runs
``-m live``. See .github/workflows/ci.yml.
"""
from __future__ import annotations

import pytest

LIVE_MODULES = {"test_scopes", "test_honesty_live"}
# Root modules that need the US artefacts. Empty since Phase 1 moved the
# script-style artefact checks to archive/legacy_tests/; kept so a new legacy
# test is classified in one place.
LEGACY_MODULES: set[str] = set()


def pytest_collection_modifyitems(config, items):
    for item in items:
        module = item.module.__name__.rsplit(".", 1)[-1]
        if module in LIVE_MODULES or item.name.startswith("test_live"):
            item.add_marker(pytest.mark.live)
        if module in LEGACY_MODULES:
            item.add_marker(pytest.mark.legacy)
