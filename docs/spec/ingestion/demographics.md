# demographics

**Serves:** M1.C5 Demographic pipeline  
**Collection priority:** 10%  
**Intended source:** ESS / CSA  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/demographics.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `grade12_completers_count` — High-school completers / exam candidates (M1.C5.V1)
- `university_age_population` — University-age population (M1.C5.V2)
- `regional_youth_population` — Regional youth population (M1.C5.V3)
- `net_internal_migration` — Migration patterns (M1.C5.V4)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
