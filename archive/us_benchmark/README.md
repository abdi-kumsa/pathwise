# US benchmark archive

The two CSVs in `Assets/` (`job_market_forecasting_data.csv` and
`student_enrollment_forecasting_data.csv`) are a US tech-sector reference
dataset (2020–2025). Wave 1 retired them from the **API request path**.

They stay in `Assets/` rather than being deleted because:

- `backend/startup_seed.py` → `data/load_to_db.py` still loads them into the
  Postgres warehouse tables (`enrollments`, `job_postings`, …), which are not
  served by `/api/*` dashboards.
- The placement XGBoost path still trains and infers against
  `data/processed/features.parquet` derived from that mock pipeline.

Request-path loaders live in `backend/services/_datasets.py` and read
`data/ethiopia/` (simulated Ethiopian structure, 2016–2025). Do not point
those loaders back at `Assets/`.
