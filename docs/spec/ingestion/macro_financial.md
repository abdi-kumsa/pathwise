# macro_financial

**Serves:** M2.C8 Macroeconomic and financial conditions  
**Collection priority:** 4%  
**Intended source:** NBE  
**Refresh cadence:** monthly/annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/macro_financial.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `gdp_growth_rate_pct` — GDP growth (M2.C8.V1)
- `cpi_index` — Inflation / CPI (M2.C8.V2)
- `inflation_rate_pct` — additional series for M2.C8.V2
- `exchange_rate_etb_usd` — Exchange rate (M2.C8.V3)
- `forex_reserve_months` — Forex availability (M2.C8.V4)
- `gross_investment_etb` — Investment levels (M2.C8.V5)
- `interest_rate_pct` — Interest conditions (M2.C8.V6)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
