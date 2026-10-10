# finance_support

**Serves:** M1.C9 Tuition, financial support and scholarships  
**Collection priority:** 2%  
**Intended source:** MoE / HEI finance  
**Refresh cadence:** annual  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/finance_support.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

- `tuition_fee_etb` — Fees (M1.C9.V1)
- `stipend_etb` — Stipends (M1.C9.V2)
- `scholarship_availability` — Scholarships (M1.C9.V3)
- `cost_sharing_loan_etb` — Loans and other financial incentives (M1.C9.V4)

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
