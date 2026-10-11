# vacancies

**Serves:** M2.C4 Job vacancy and recruitment signals  
**Collection priority:** 10%  
**Intended source:** MoLS / job boards  
**Refresh cadence:** quarterly  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/vacancies.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `vacancy_count` — Vacancy count (M2.C4.V1)
- `occupation` — Job title/occupation (M2.C4.V2)
- `occupation_frequency` — additional series for M2.C4.V2
- `required_education` — Required education (M2.C4.V3)
- `required_experience_years` — Required experience (M2.C4.V4)
- `hiring_trend_pct` — Hiring trends (M2.C4.V5)
- `time_to_fill_days` — additional series for M2.C4.V5

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
