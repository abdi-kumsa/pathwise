# PathWise — Market Demand & Enrollment Intelligence Platform

A full-stack predictive analytics platform built around two interconnected dashboards:
- **Module 1 — Market Demand Forecast Dashboard**: Hiring analytics, skill gap analysis, salary forecasting, and feature importance visualisations for institutional leaders.
- **Module 2 — Student Enrollment Intelligence Dashboard**: Enrollment forecasting, admission risk modelling, and a student-facing placement probability evaluator with personalised skill recommendations.

---

## Repository Structure

```
pathwise/
├── backend/      # FastAPI REST API — serves ML model inference, data queries, and recommendation logic
├── frontend/     # React + Vite dashboard UI — both Module 1 and Module 2 interfaces
├── ml/           # Machine learning — model training scripts, saved models, feature engineering, evaluation
├── data/         # Raw and processed data — mock data generators, ETL loaders, CSV outputs, parquet files
├── docker/       # Docker configuration files — Dockerfiles for backend and frontend services
├── docs/         # Project documentation — technical setup guide, API reference, user guide
└── docker-compose.yml  # Orchestrates all services: Postgres, FastAPI backend, React frontend
```

---

## Folder Details

### `/backend`
FastAPI Python application. Handles all REST API routes, database access via SQLAlchemy, and wraps trained ML models into real-time inference endpoints. Structured as:
- `/routers` — route handlers for market demand, enrollment, and recommendations
- `/models` — SQLAlchemy ORM table definitions
- `/services` — ML inference service and recommendation logic
- `/db` — database connection and session management

### `/frontend`
React + Vite single-page application. Renders both dashboard modules with interactive charts (Recharts), responsive layouts (Tailwind CSS), and live API integration (Axios).
- `/pages` — one file per dashboard view
- `/components` — reusable UI components (StatCard, charts, forms)
- `/hooks` — custom React hooks (useFetch, etc.)
- `/api` — Axios service functions per module

### `/ml`
All machine learning work lives here:
- Training scripts for XGBoost (placement prediction), Prophet (enrollment forecasting), and LSTM (temporal demand)
- SHAP explainability outputs
- Saved model files (`/models/`)
- Feature engineering pipeline
- Model evaluation and monitoring scripts

### `/data`
Data layer for the platform:
- `generate_mock_data.py` — Faker-based synthetic data generator (students, job postings, enrollments, placements)
- `load_to_db.py` — ETL script to ingest CSVs into PostgreSQL
- `data_quality_check.py` — summary report for validating loaded data
- `/mock/` — generated CSV files
- `/processed/` — feature-engineered parquet files ready for ML training

### `/docker`
Dockerfiles for individual services (backend and frontend). The root `docker-compose.yml` references these to spin up the full stack with a single command.

### `/docs`
- `TECHNICAL.md` — setup guide, environment variables, API reference, how to retrain models
- `USER_GUIDE.md` — plain-language guide to navigating the dashboards

---

## Quick Start

```bash
# 1. Copy environment config
cp .env.example .env

# 2. Start all services
docker compose up

# 3. Open the app
#    Frontend:  http://localhost:3000
#    API docs:  http://localhost:8000/docs
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python) |
| Database | PostgreSQL |
| ML Models | XGBoost · Prophet · Keras LSTM |
| Explainability | SHAP |
| Frontend | React + Vite · Tailwind CSS · Recharts |
| Infrastructure | Docker Compose |
| Mock Data | Python Faker |
