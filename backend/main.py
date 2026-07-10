import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

app = FastAPI(
    title="PathWise API",
    description="Market Demand & Enrollment Intelligence Platform — REST API",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Reads FRONTEND_URL from .env so the allowed origin is never hard-coded.
# Multiple origins can be separated by commas:
#   FRONTEND_URL=http://localhost:3000,https://pathwise.example.com
_origins = [
    o.strip()
    for o in os.getenv("FRONTEND_URL", "http://localhost:3000").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from routers import market, enrollment, monitoring, recommendations  # noqa: E402

app.include_router(market.router,           prefix="/api")
app.include_router(enrollment.router,       prefix="/api")
app.include_router(monitoring.router,       prefix="/api")
app.include_router(recommendations.router,  prefix="/api")

# ── Model status — updated in _prewarm_models() ───────────────────────────────
# Kept at module level so /health can read it without re-importing ml_service.
_model_status: dict = {
    "xgboost": False,
    "salary":  False,
    "lstm":    False,
    "prophet": False,
    "shap":    False,
}


def _prewarm_models() -> None:
    """Load all four ML artefacts eagerly at startup.

    Without pre-warming the first HTTP request to any ML endpoint blocks for
    8–12 s while TensorFlow initialises.  Loading here means every subsequent
    request hits the already-warm module-level singletons in ml_service.

    Each model is loaded independently — a failure in one (e.g. missing .keras
    file) does not prevent the others from loading.
    """
    from services import ml_service

    log.info("Pre-warming ML models ...")

    try:
        ml_service.get_xgboost()
        _model_status["xgboost"] = True
        log.info("  [ok] XGBoost placement model")
    except Exception as exc:
        log.error("  [fail] XGBoost: %s", exc)

    try:
        ml_service.get_salary_model()
        _model_status["salary"] = True
        log.info("  [ok] XGBoost salary model")
    except Exception as exc:
        log.error("  [fail] Salary model: %s", exc)

    try:
        ml_service.get_lstm()
        _model_status["lstm"] = True
        log.info("  [ok] LSTM enrollment model")
    except Exception as exc:
        log.error("  [fail] LSTM: %s", exc)

    try:
        ml_service.get_prophet()
        _model_status["prophet"] = True
        log.info("  [ok] Prophet demand model")
    except Exception as exc:
        log.error("  [fail] Prophet: %s", exc)

    try:
        ml_service.get_shap_cache()
        _model_status["shap"] = True
        log.info("  [ok] SHAP value cache")
    except Exception as exc:
        log.error("  [fail] SHAP cache: %s", exc)

    loaded = sum(_model_status.values())
    log.info("Model pre-warm complete — %d/5 loaded.", loaded)


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup() -> None:
    """Runs once when uvicorn finishes loading, before accepting requests."""
    log.info("PathWise API starting up ...")

    # 1. Seed the database on first-ever start (idempotent)
    try:
        from startup_seed import seed_if_empty
        seed_if_empty()
    except Exception as exc:
        log.error("Startup seed raised an unexpected error: %s", exc)

    # 2. Load all ML models into memory now so requests are instant
    _prewarm_models()

    log.info("PathWise API ready.")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health_check():
    """Returns per-model load status.

    docker-compose uses this endpoint to decide when the backend service is
    healthy.  The frontend container will not start until this returns 200.
    A model that failed to load shows False — the API still starts, but
    endpoints that depend on that model will return 500.
    """
    all_loaded = all(_model_status.values())
    return {
        "status": "ok" if all_loaded else "degraded",
        "models": _model_status,
    }


@app.get("/", tags=["Health"])
def root():
    return {"message": "PathWise API is running. Visit /docs for the API reference."}
