# formal_informal

**Serves:** M2.C3 Formal versus informal sector structure  
**Collection priority:** 15%  
**Intended source:** ESS LFS  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/formal_informal.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `formal_wage_employment` — Formal wage employment (M2.C3.V1)
- `informal_employment` — Informal employment (M2.C3.V2)
- `self_employment` — Self-employment (M2.C3.V3)
- `underemployment` — Underemployment (M2.C3.V4)
- `microenterprise_activity` — Microenterprise activity (M2.C3.V5)
- `sector_absorption_rate` — Sector absorption patterns (M2.C3.V6)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
