from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="PathWise API",
    description="Market Demand & Enrollment Intelligence Platform — REST API",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers (uncomment as each is built) ──────────────────────────────────────
# from routers import market, enrollment, recommendations
# app.include_router(market.router, prefix="/api")
# app.include_router(enrollment.router, prefix="/api")
# app.include_router(recommendations.router, prefix="/api")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "models_loaded": False}


@app.get("/", tags=["Health"])
def root():
    return {"message": "PathWise API is running. Visit /docs for the API reference."}
