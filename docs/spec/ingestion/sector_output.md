# sector_output

**Serves:** M2.C2 Sector-level employment and economic output  
**Collection priority:** 20%  
**Intended source:** ESS national accounts  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/sector_output.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `sector_value_added_etb` — Sector value-added (M2.C2.V1)
- `sector_growth_rate_pct` — Sector growth rate (M2.C2.V2)
- `sector_output_index` — Production/output (M2.C2.V3)
- `business_formation_count` — Business formation (M2.C2.V4)
- `sector_investment_etb` — Investment (M2.C2.V5)
- `employment_intensity` — Employment intensity (M2.C2.V6)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
