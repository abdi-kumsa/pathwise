# exam_placement

**Serves:** M1.C3 National entrance exam and placement data  
**Collection priority:** 15%  
**Intended source:** EAES / MoE placement  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/exam_placement.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `exam_candidates_count` — Entrance exam participation (M1.C3.V1)
- `exam_pass_rate_pct` — Pass rate (M1.C3.V2)
- `exam_score_mean` — Score distribution (M1.C3.V3)
- `exam_score_sd` — additional series for M1.C3.V3
- `exam_score_p25` — additional series for M1.C3.V3
- `exam_score_p50` — additional series for M1.C3.V3
- `exam_score_p75` — additional series for M1.C3.V3
- `program_cutoff_score` — Program cutoff (M1.C3.V4)
- `placed_count` — Placement decision (M1.C3.V5)
- `placement_rate_pct` — additional series for M1.C3.V5
- `field_allocation_count` — Field allocation (M1.C3.V6)
- `band_allocation_ratio` — additional series for M1.C3.V6

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
