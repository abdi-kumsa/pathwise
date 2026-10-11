# skills_demand

**Serves:** M2.C5 Skills demand and shortage indicators  
**Collection priority:** 10%  
**Intended source:** MoLS skills survey  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/skills_demand.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `technical_skill_demand` — Technical skills (M2.C5.V1)
- `digital_skill_demand` — Digital skills (M2.C5.V2)
- `soft_skill_demand` — Soft skills (M2.C5.V3)
- `emerging_skill_demand` — Emerging skills (M2.C5.V4)
- `skill_shortage_index` — Shortage indicator (M2.C5.V5)
- `skill_oversupply_index` — Oversupply indicator (M2.C5.V6)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
