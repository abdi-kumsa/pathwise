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

def _prewarm_models() -> None:
    """Load all four ML artefacts eagerly at startup.

    Without pre-warming the first HTTP request to any ML endpoint blocks for
    8–12 s while TensorFlow initialises.  Loading here means every subsequent
    request hits the already-warm module-level singletons in ml_service.

    Each model is loaded independently — a failure in one (e.g. missing .keras
    file) does not prevent the others from loading.

    Loaders are idempotent (they no-op when the singleton is already set), so
    this is safe to re-run to retry whatever failed last time.
    """
    from services import ml_service

    log.info("Pre-warming ML models ...")

    loaders = [
        ("XGBoost placement model", ml_service.get_xgboost),
        ("XGBoost salary model",    ml_service.get_salary_model),
        ("LSTM enrollment model",   ml_service.get_lstm),
        ("Prophet demand model",    ml_service.get_prophet),
        ("SHAP value cache",        ml_service.get_shap_cache),
    ]

    for label, loader in loaders:
        try:
            loader()
            log.info("  [ok] %s", label)
        except Exception as exc:
            log.error("  [fail] %s: %s", label, exc)

    loaded = sum(ml_service.loaded_status().values())
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
    """Returns per-model load status, read live from the ml_service singletons.

    docker-compose uses this endpoint to decide when the backend service is
    healthy.  The frontend container will not start until this returns 200.
    A model that failed to load shows False — the API still starts, but
    endpoints that depend on that model will return 500.

    This reflects current state, not a snapshot taken at startup: a model that
    loads later (lazily, or via POST /health/reload) is reported immediately.
    """
    from services import ml_service

    models = ml_service.loaded_status()
    return {
        "status": "ok" if all(models.values()) else "degraded",
        "models": models,
    }


@app.post("/health/reload", tags=["Health"])
def reload_models():
    """Retry loading any artefact that is not currently resident.

    Recovery path for the case where the process started before its volume
    mounts were ready — the API is up but reports degraded, and previously the
    only fix was restarting the container. Already-loaded models are untouched
    because the loaders no-op on a warm singleton.
    """
    from services import ml_service

    before = ml_service.loaded_status()
    _prewarm_models()
    after = ml_service.loaded_status()

    return {
        "status":   "ok" if all(after.values()) else "degraded",
        "models":   after,
        "recovered": [k for k, v in after.items() if v and not before[k]],
    }


@app.get("/", tags=["Health"])
def root():
    return {"message": "PathWise API is running. Visit /docs for the API reference."}
