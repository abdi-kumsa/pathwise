# institution_capacity

**Serves:** M1.C8 Institutional capacity and quality  
**Collection priority:** 3%  
**Intended source:** HERQA / HEI returns  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/institution_capacity.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `faculty_student_ratio` — Faculty-student ratio (M1.C8.V1)
- `laboratory_count` — Laboratories (M1.C8.V2)
- `classroom_count` — Classrooms (M1.C8.V3)
- `accreditation_status` — Accreditation status (M1.C8.V4)
- `program_quality_index` — Program quality indicators (M1.C8.V5)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
