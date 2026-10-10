# admissions_funnel

**Serves:** M1.C2 Admissions funnel data  
**Collection priority:** 15%  
**Intended source:** MoE EMIS / HEI registrar  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/admissions_funnel.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `applications_count` — Applications (M1.C2.V1)
- `offers_count` — Offers/admissions (M1.C2.V2)
- `accepted_offers_count` — Accepted offers (M1.C2.V3)
- `yield_rate_pct` — Yield rate (M1.C2.V4)
- `applicants_per_seat` — Applicants per seat (M1.C2.V5)
- `first_choice_demand_count` — First-choice program demand (M1.C2.V6)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
