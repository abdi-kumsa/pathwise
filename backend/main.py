import logging
import os

import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup work runs before the first request; nothing to tear down.

    Lifespan replaces @app.on_event("startup"), which Starlette 1.x removed.
    on_startup is synchronous and slow (model loads), so it runs in a worker
    thread rather than blocking the event loop.
    """
    await run_in_threadpool(on_startup)
    yield


from services.auth_service import IS_DEV  # noqa: E402

# Interactive docs and the OpenAPI schema are a map of every route; serve them
# only in development (audit S17).
app = FastAPI(
    title="PathWise API",
    description="Market Demand & Enrollment Intelligence Platform — REST API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if IS_DEV else None,
    redoc_url="/redoc" if IS_DEV else None,
    openapi_url="/openapi.json" if IS_DEV else None,
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


# ── Error bodies ──────────────────────────────────────────────────────────────
# Routers wrap failures as HTTPException(500, detail=str(exc)), which used to
# send internal exception text (file paths, column names, SQL) to the browser.
# Every 500 is now logged in full server-side with a short reference id, and
# the client receives only that id. Other statuses (403, 404, 422, 503...) keep
# their deliberate, user-facing detail.
_GENERIC_500 = "Internal server error. Quote the reference when reporting this."


def _internal_error(request: Request, exc: BaseException) -> JSONResponse:
    ref = uuid.uuid4().hex[:12]
    cause = exc.__cause__ or exc.__context__ or exc
    log.error(
        "500 ref=%s %s %s: %s",
        ref, request.method, request.url.path, getattr(exc, "detail", exc),
        exc_info=(type(cause), cause, cause.__traceback__),
    )
    return JSONResponse(status_code=500, content={"detail": _GENERIC_500, "ref": ref})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 500:
        return _internal_error(request, exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return _internal_error(request, exc)


# ── Security Headers ──────────────────────────────────────────────────────────
# The API returns JSON only, so its CSP allows nothing at all. The dev-only
# Swagger page loads scripts from a CDN and is exempted. HSTS is sent outside
# dev, where the API is served over HTTPS (Render terminates TLS).
_API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
_DOC_PATHS = ("/docs", "/redoc", "/openapi.json")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    # The legacy XSS auditor is removed from browsers and could itself be
    # abused; "0" is the current recommendation.
    response.headers["X-XSS-Protection"] = "0"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if not request.url.path.startswith(_DOC_PATHS):
        response.headers["Content-Security-Policy"] = _API_CSP
    if not IS_DEV:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if request.url.path.startswith("/api/"):
        # Role-scoped data must not sit in shared or browser caches.
        response.headers.setdefault("Cache-Control", "no-store")
    return response


# ── Provenance stamp (Wave 0) ─────────────────────────────────────────────────
# Every successful JSON object under /api/* carries a provenance block so a
# figure cannot be quoted without its source. Auth is excluded: tokens are not
# a dataset. List bodies are left alone so existing array-shaped endpoints do
# not change their contract.
@app.middleware("http")
async def stamp_provenance(request: Request, call_next):
    from starlette.responses import Response
    from services._provenance import attach_default_if_missing

    response = await call_next(request)
    path = request.url.path
    if (
        not path.startswith("/api/")
        or path.startswith("/api/auth")
        or response.status_code >= 400
    ):
        return response
    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return response

    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    body = attach_default_if_missing(b"".join(chunks))
    headers = dict(response.headers)
    headers.pop("content-length", None)
    return Response(
        content=body,
        status_code=response.status_code,
        headers=headers,
        media_type=content_type,
    )

# ── Routers ───────────────────────────────────────────────────────────────────
from services.feature_flags import LEGACY_US_MODELS  # noqa: E402
from routers import (  # noqa: E402
    admin,
    ahp,
    auth,
    careers,
    education,
    institution,
    labour,
    methodology,
    model1,
    model2,
    model3,
    monitoring,
    search,
    student,
    users,
)

# Public
app.include_router(auth.router,             prefix="/api")

# Role-scoped — each router declares its own require_roles dependency
app.include_router(careers.router,          prefix="/api")   # STUDENT
app.include_router(labour.router,           prefix="/api")   # MOL + MOE
app.include_router(education.router,        prefix="/api")   # MOE
app.include_router(institution.router,      prefix="/api")   # UNIVERSITY
app.include_router(model1.router,           prefix="/api")   # MOE + UNIVERSITY
app.include_router(model2.router,           prefix="/api")   # MOL + MOE
app.include_router(model3.router,           prefix="/api")   # MOE + MOL + UNIVERSITY
app.include_router(student.router,          prefix="/api")   # STUDENT
app.include_router(users.router,            prefix="/api")   # ADMIN
app.include_router(admin.router,            prefix="/api")   # ADMIN
app.include_router(methodology.router,      prefix="/api")   # ADMIN
app.include_router(ahp.router,              prefix="/api")   # ADMIN

# Any authenticated role; results are filtered per role inside the router
app.include_router(search.router,           prefix="/api")

app.include_router(monitoring.router,       prefix="/api")   # ADMIN

# Leftover US-model routes (waiver WV.US1). Off unless LEGACY_US_MODELS=1, so
# the default deployment never imports TensorFlow, Prophet or SHAP.
if LEGACY_US_MODELS:
    from routers import enrollment, market, recommendations  # noqa: E402

    app.include_router(market.router,           prefix="/api")
    app.include_router(enrollment.router,       prefix="/api")
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


def _prewarm_forecasts() -> None:
    """Populate ml._memo with the horizons the dashboards request by default."""
    import time
    started = time.monotonic()
    try:
        from ml.model1.layer1_demand import forecast_unconstrained
        from ml.model2.forecast import forecast_employment, forecast_skills, forecast_vacancies
        from ml.model3.supply import graduate_supply
        from services.labour_market_service import workforce_report

        for horizon in (1, 3):
            forecast_unconstrained(horizon=horizon)
            forecast_vacancies(horizon=horizon)
        forecast_employment(3)
        forecast_skills(3)
        graduate_supply(horizon=1)
        workforce_report(3)
        # Backtests behind the accuracy blocks and the drift report.
        from ml.drift import ethiopia_drift
        ethiopia_drift()
        # The admin validation pages re-read all twenty tables.
        from services import admin_service
        admin_service.pipeline_status()
        admin_service.data_quality()
        log.info("Forecast memo warm in %.1f s.", time.monotonic() - started)
    except Exception as exc:
        log.error("Forecast prewarm failed (requests will compute lazily): %s", exc)


def _audit_retention_loop() -> None:
    import time
    from services import admin_service
    while True:
        try:
            result = admin_service.purge_audit_log()
            log.info("Audit retention: removed %d row(s) older than %d days.",
                     result["deleted"], result["retention_days"])
            result = admin_service.purge_scenarios()
            log.info("Scenario retention: removed %d draft/rejected scenario(s) older than %d days.",
                     result["deleted"], result["retention_days"])
        except Exception as exc:
            log.warning("Audit retention run failed: %s", exc)
        time.sleep(24 * 3600)


# ── Startup ───────────────────────────────────────────────────────────────────
def on_startup() -> None:
    """Runs once when uvicorn finishes loading, before accepting requests."""
    log.info("PathWise API starting up ...")

    # 1. Refuse to serve with an unsafe signing key outside dev. Deliberately
    #    not wrapped in try/except: an unsafe key must stop the process.
    from services.auth_service import check_database_configuration, check_secret_configuration
    check_secret_configuration()
    check_database_configuration()

    # 2. Ensure database tables exist and seed if empty
    try:
        from db.database import engine, Base
        import models  # noqa: F401 - registers Student, Enrollment, JobPosting, Placement, User
        Base.metadata.create_all(bind=engine)
        log.info("Database tables verified / created.")
    except Exception as exc:
        log.error("Database table creation failed: %s", exc)

    try:
        from startup_seed import (
            apply_wave5_user_columns,
            patch_demo_student_profile,
            seed_if_empty,
            seed_users_if_empty,
        )
        apply_wave5_user_columns()
        seed_if_empty()
        seed_users_if_empty()
        patch_demo_student_profile()
    except Exception as exc:
        log.error("Startup seed raised an unexpected error: %s", exc)

    # 3. Leftover US artefacts load only when their routes are enabled.
    if LEGACY_US_MODELS:
        _prewarm_models()
    else:
        log.info("LEGACY_US_MODELS is off — US placement/salary/LSTM/Prophet not loaded.")

    # 4. Fill the Ethiopia forecast memo in the background so the first
    #    dashboard visit does not pay for every per-series fit.
    import threading
    threading.Thread(target=_prewarm_forecasts, name="forecast-prewarm", daemon=True).start()

    # 5. Audit-log retention: once at startup, then daily (plan item 3.7).
    threading.Thread(target=_audit_retention_loop, name="audit-retention", daemon=True).start()

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

    if not LEGACY_US_MODELS:
        # The Ethiopia models are computed per request from parquet; there is
        # no artefact to be missing, so nothing can be degraded here.
        return {"status": "ok", "models": {}, "legacy_us_models": False}

    models = ml_service.loaded_status()
    return {
        "status": "ok" if all(models.values()) else "degraded",
        "models": models,
        "legacy_us_models": True,
    }


def _require_admin():
    from services.auth_service import ROLE_ADMIN, require_roles
    return require_roles(ROLE_ADMIN)


@app.post("/health/reload", tags=["Health"], dependencies=[Depends(_require_admin())])
def reload_models():
    """Retry loading any artefact that is not currently resident.

    ADMIN only: it can re-run TensorFlow and Prophet loads, which is expensive
    enough to be a denial-of-service lever if left open (audit S6).

    Recovery path for the case where the process started before its volume
    mounts were ready — the API is up but reports degraded, and previously the
    only fix was restarting the container. Already-loaded models are untouched
    because the loaders no-op on a warm singleton.
    """
    from services import ml_service

    if not LEGACY_US_MODELS:
        return {"status": "ok", "models": {}, "recovered": [], "legacy_us_models": False}

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
