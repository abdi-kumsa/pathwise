# capacity_quota

**Serves:** M1.C4 Program capacity and quota policy  
**Collection priority:** 15%  
**Intended source:** MoE intake circulars  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/capacity_quota.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `approved_intake_quota` — Approved intake quota (M1.C4.V1)
- `available_seats` — Available seats (M1.C4.V2)
- `program_capacity` — Program capacity (M1.C4.V3)
- `program_expansion_flag` — New program expansion (M1.C4.V4)
- `program_suspension_flag` — Program suspension/closure (M1.C4.V5)
- `strategic_priority_flag` — Strategic priority field (M1.C4.V6)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
