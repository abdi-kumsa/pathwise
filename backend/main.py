import logging
import os

from fastapi import FastAPI, Request
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
# Defaults include standard dev ports and automatically strips trailing slashes.
_raw_origins = os.getenv(
    "FRONTEND_URL",
    "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001",
)
_origins = []
for origin in _raw_origins.split(","):
    clean = origin.strip().rstrip("/")
    if clean and clean not in _origins:
        _origins.append(clean)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Security Headers ──────────────────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# ── Routers ───────────────────────────────────────────────────────────────────
from routers import (  # noqa: E402
    auth,
    careers,
    education,
    enrollment,
    institution,
    labour,
    market,
    monitoring,
    recommendations,
    search,
    users,
)

# Public
app.include_router(auth.router,             prefix="/api")

# Role-scoped — each router declares its own require_roles dependency
app.include_router(careers.router,          prefix="/api")   # STUDENT
app.include_router(labour.router,           prefix="/api")   # MOL + MOE
app.include_router(education.router,        prefix="/api")   # MOE
app.include_router(institution.router,      prefix="/api")   # UNIVERSITY
app.include_router(users.router,            prefix="/api")   # ADMIN

# Any authenticated role; results are filtered per role inside the router
app.include_router(search.router,           prefix="/api")

# Original dashboards — now authenticated
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

    # 1. Warn loudly if the JWT signing key is still the built-in default
    try:
        from services.auth_service import warn_if_insecure
        warn_if_insecure()
    except Exception as exc:
        log.error("Auth configuration check failed: %s", exc)

    # 2. Seed the database on first-ever start (idempotent)
    try:
        from startup_seed import seed_if_empty, seed_users_if_empty
        seed_if_empty()
        seed_users_if_empty()
    except Exception as exc:
        log.error("Startup seed raised an unexpected error: %s", exc)

    # 3. Load all ML models into memory now so requests are instant
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
