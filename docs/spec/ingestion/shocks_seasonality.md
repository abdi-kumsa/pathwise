# shocks_seasonality

**Serves:** M2.C10 Seasonality, commodity and external shocks  
**Collection priority:** 2%  
**Intended source:** derived / NBE commodity  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/shocks_seasonality.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `agricultural_season` — Agricultural cycles (M2.C10.V1)
- `hiring_season_index` — Hiring cycles (M2.C10.V2)
- `commodity_price_index` — Commodity prices (M2.C10.V3)
- `external_shock_flag` — Major external shocks (M2.C10.V4)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
