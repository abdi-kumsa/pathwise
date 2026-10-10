# enrollment_history

**Serves:** M1.C1 Historical enrollment time series  
**Collection priority:** 25%  
**Intended source:** MoE EMIS  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/enrollment_history.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `enrollment_lag_1y` — Lag-1 enrollment (M1.C1.V1)
- `enrollment_lag_2y` — Lag-2 enrollment (M1.C1.V2)
- `enrollment_rolling_3y_avg` — 3-5 year rolling trend (M1.C1.V3)
- `enrollment_rolling_5y_avg` — additional series for M1.C1.V3
- `enrollment_growth_rate_pct` — Growth/decline rate (M1.C1.V4)
- `program_enrollment_count` — Department/program enrollment (M1.C1.V5)
- `campus_enrollment_count` — Campus and regional enrollment (M1.C1.V6)
- `region_enrollment_count` — additional series for M1.C1.V6

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
