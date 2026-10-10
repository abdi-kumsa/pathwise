# public_hiring

**Serves:** M2.C6 Public-sector hiring and government project pipeline  
**Collection priority:** 10%  
**Intended source:** Civil Service Commission  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/public_hiring.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `civil_service_hiring_plan` — Civil-service hiring plans (M2.C6.V1)
- `hiring_policy_state` — Hiring freezes/expansions (M2.C6.V2)
- `public_project_count` — Public projects (M2.C6.V3)
- `megaproject_staffing_demand` — Mega-project staffing demand (M2.C6.V4)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
