# graduate_outcomes

**Serves:** M1.C7 Lagged employment outcomes by field  
**Collection priority:** 5%  
**Intended source:** MoLS / graduate tracer  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/graduate_outcomes.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `graduate_employment_rate_pct` — Graduate employment rate by field (M1.C7.V1)
- `graduate_unemployment_rate_pct` — Graduate unemployment rate (M1.C7.V2)
- `median_earnings_etb` — Median earnings where available (M1.C7.V3)
- `vacancy_demand_by_field` — Vacancy demand by field (M1.C7.V4)
- `skills_shortage_signal` — Skills shortage signals (M1.C7.V5)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
