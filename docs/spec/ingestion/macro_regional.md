# macro_regional

**Serves:** M1.C10 Macroeconomic and regional socio-economic conditions  
**Collection priority:** 2%  
**Intended source:** NBE / ESS  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/macro_regional.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `inflation_rate_pct` — Inflation (M1.C10.V1)
- `household_income_proxy_etb` — Household-income proxies (M1.C10.V2)
- `youth_unemployment_rate_pct` — Youth unemployment (M1.C10.V3)
- `regional_socioeconomic_index` — Regional socio-economic indicators (M1.C10.V4)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
