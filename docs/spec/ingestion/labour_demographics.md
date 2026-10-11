# labour_demographics

**Serves:** M2.C9 Labor-force demographics, migration and regional variation  
**Collection priority:** 2%  
**Intended source:** ESS  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/labour_demographics.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `working_age_population` — Working-age population (M2.C9.V1)
- `education_level_distribution` — Education level (M2.C9.V2)
- `skilled_emigration_count` — Migration / brain drain (M2.C9.V3)
- `return_migration_count` — Return migration (M2.C9.V4)
- `regional_absorption_rate` — Regional labor absorption (M2.C9.V5)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
