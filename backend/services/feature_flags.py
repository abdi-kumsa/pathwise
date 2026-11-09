"""
Deployment feature flags, read once from the environment.

LEGACY_US_MODELS (default off)
    The four US-trained artefacts — placement XGBoost, salary XGBoost,
    enrollment LSTM and Prophet demand — and the routes that serve them
    (/api/market, /api/enrollment, /api/recommendations). They are not Ethiopia
    Model 1 or Model 2 (waiver WV.US1), and the 2026-11-07 audit found all four
    lose to trivial baselines. Off, the API does not import TensorFlow, Prophet
    or SHAP at startup, the routes are not registered, and nothing on the
    Ethiopia request path calls the US placement model.

    Set LEGACY_US_MODELS=1 (and VITE_LEGACY_US_MODELS=true for the frontend
    build) to bring them back for a side-by-side demonstration.
"""
from __future__ import annotations

import os


def _flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


LEGACY_US_MODELS = _flag("LEGACY_US_MODELS")
