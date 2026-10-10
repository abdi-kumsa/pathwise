# fdi_industrial

**Serves:** M2.C7 FDI and industrial development pipeline  
**Collection priority:** 7%  
**Intended source:** EIC / IPDC  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/fdi_industrial.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `fdi_inflow_usd` — FDI inflows by sector/region (M2.C7.V1)
- `industrial_park` — Industrial parks (M2.C7.V2)
- `industrial_park_operational_flag` — additional series for M2.C7.V2
- `new_investment_project_count` — New investment projects (M2.C7.V3)
- `factory_expansion_count` — Factory expansion (M2.C7.V4)
- `expected_employment` — Expected employment (M2.C7.V5)
- `private_investment_pipeline_etb` — Private investment pipeline (M2.C7.V6)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
