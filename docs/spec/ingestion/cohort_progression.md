# cohort_progression

**Serves:** M1.C6 Cohort progression and retention  
**Collection priority:** 8%  
**Intended source:** MoE EMIS  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/cohort_progression.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `retention_rate_pct` — Retention rate (M1.C6.V1)
- `dropout_rate_pct` — Dropout rate (M1.C6.V2)
- `transfer_rate_pct` — Transfer rate (M1.C6.V3)
- `completion_rate_pct` — Completion rate (M1.C6.V4)
- `time_to_graduation_years` — Time to graduation (M1.C6.V5)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
