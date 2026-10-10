# labour_history

**Serves:** M2.C1 Historical employment and unemployment trends  
**Collection priority:** 20%  
**Intended source:** ESS LFS / UEUS  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/labour_history.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `employment_level` — Employment level (M2.C1.V1)
- `unemployment_rate_pct` — Unemployment rate (M2.C1.V2)
- `youth_unemployment_rate_pct` — Youth unemployment (M2.C1.V3)
- `sector_employment` — Sector employment (M2.C1.V4)
- `employment_growth_pct` — Employment growth (M2.C1.V5)
- `job_creation_count` — Job creation (M2.C1.V6)
- `labour_force_participation_pct` — Labor-force participation (M2.C1.V7)
- `employment_lag_1y` — Lagged employment (M2.C1.V8)
- `employment_lag_2y` — additional series for M2.C1.V8

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
