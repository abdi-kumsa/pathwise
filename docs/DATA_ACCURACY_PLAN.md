# Data accuracy plan (Phase 5)

The scoping document for the data-accuracy discussion, which was parked in the
[2026-11-07 improvement plan](audit/2026-11-07-improvement-plan.md). Every
figure in PathWise is still simulated (waiver WV.SIM1). This plan sets out what
is needed to replace the simulation, in what order, and what is already in
place to receive it.

## What can only come from you

The software cannot supply these. They decide when accuracy becomes real.

1. **Data-sharing agreements** with MoE (EMIS, placement, quotas), MoLS, the
   Ethiopian Statistics Service (labour force survey), CSA / NBE (output,
   macro), the Civil Service Commission and EIC. Each table below names its
   intended source.
2. **The files themselves**, at the grain and with the columns in
   `docs/spec/ingestion/<table>.md`.
3. **Expert reviewers** for the six DOC1 domains (PROC.S2), named so their
   verdicts can be recorded in Admin → Methodology.
4. **Decisions on gaps**: what to do where a ministry has no series for a
   column (drop it from the contract, proxy it, or keep it simulated and
   labelled).

## Order of work

Collect Tier 1 tables first: DOC1 gives them 70% (Model 1) and 55% (Model 2) of
the collection priority, and the forecasts depend on them directly. Within a
tier, higher priority first.

| Order | Table | DOC1 category | Priority | Tier | Intended source | Required columns |
|---|---|---|---|---|---|---|
| 1 | `enrollment_history` | M1.C1 Historical enrolment | 25% | M1 T1 | MoE EMIS | 8 |
| 2 | `labour_history` | M2.C1 Employment and unemployment trends | 20% | M2 T1 | ESS / MoLS | 9 |
| 3 | `sector_output` | M2.C2 Sector employment and output | 20% | M2 T1 | CSA / NBE | 6 |
| 4 | `admissions_funnel` | M1.C2 Admissions funnel | 15% | M1 T1 | MoE / HEI SIS | 6 |
| 5 | `exam_placement` | M1.C3 Entrance exam and placement | 15% | M1 T1 | MoE placement (ESSLCE) | 12 |
| 6 | `capacity_quota` | M1.C4 Capacity and quota policy | 15% | M1 T1 | MoE quotas | 6 |
| 7 | `formal_informal` | M2.C3 Formal vs informal structure | 15% | M2 T1 | ESS LFS | 6 |
| 8 | `demographics` | M1.C5 Demographic pipeline | 10% | M1 T2 | CSA / MoE | 4 |
| 9 | `vacancies` | M2.C4 Vacancies and recruitment | 10% | M2 T2 | MoLS / job boards | 7 |
| 10 | `skills_demand` | M2.C5 Skills demand and shortage | 10% | M2 T2 | MoLS | 6 |
| 11 | `public_hiring` | M2.C6 Public hiring and projects | 10% | M2 T2 | CSC / MoLS | 4 |
| 12 | `cohort_progression` | M1.C6 Cohort progression | 8% | M1 T2 | HEI SIS | 5 |
| 13 | `fdi_industrial` | M2.C7 FDI and industrial pipeline | 7% | M2 T3 | EIC / industrial parks | 7 |
| 14 | `graduate_outcomes` | M1.C7 Graduate employment outcomes | 5% | M1 T3 | HEI tracer / ESS | 5 |
| 15 | `macro_financial` | M2.C8 Macro and financial | 4% | M2 T3 | NBE | 7 |
| 16 | `institution_capacity` | M1.C8 Institutional capacity | 3% | M1 T3 | HEI / MoE | 5 |
| 17 | `finance_support` | M1.C9 Tuition and support | 2% | M1 T3 | MoE / MoF | 4 |
| 18 | `macro_regional` | M1.C10 Regional socio-economic | 2% | M1 T3 | CSA / regional bureaux | 4 |
| 19 | `labour_demographics` | M2.C9 Labour demographics and migration | 2% | M2 T3 | ESS | 5 |
| 20 | `shocks_seasonality` | M2.C10 Seasonality and shocks | 2% | M2 T3 | CSA / disaster agencies | 4 |

The forecasts read four of these directly: `admissions_funnel` (Model 1
demand), `capacity_quota` and `exam_placement` (Layer 2), and `labour_history`,
`vacancies`, `skills_demand` (Model 2). Replacing those first changes the
forecasts soonest.

## What is in place to receive a file

| Step | Tool | What it does |
|---|---|---|
| Contract | `docs/spec/ingestion/<table>.md`, `backend/services/_validate.py` | Required columns, keys, tiers; official rows must name a source |
| Ingestion | `scripts/ingest_official.py TABLE FILE --source … --vintage …` | Dry run by default; `--apply` backs up the simulated file, writes the official one, logs it, re-runs the backtest |
| Key checks | same script | Institutions, regions and fields must exist in `data/ethiopia/reference/`; no duplicate keys; whole-number years |
| Consistency | `ml/consistency.py` (13 rules) | Funnel order, cohort rates ≤ 100%, seats ≤ quota ≤ capacity, placed ≤ passed, true lag and prior-year rolling columns, rate bounds. Critical and high failures block ingestion |
| Reconciliation | same script | Rows, years and median % difference per column between the official file and the simulation it replaces |
| Provenance | Admin → Pipeline | Each feed shows its own tier, source and vintage, read from the file |
| Accuracy | `scripts/model_report.py`, `/api/monitoring/drift` | The same rolling-origin backtest and drift checks run on whatever data is loaded |

## How accuracy will be judged

Once a Tier 1 table is official:

1. Re-run `python scripts/model_report.py`. The backtest now measures real
   forecasting error for that target.
2. Compare the selected model's skill against the naive baselines. A model that
   cannot beat "last year's value" on official data should not be the one
   served, and the selection rule already enforces that.
3. Check interval coverage. On official data the 90% bands must still cover
   roughly 90% of held-out years; if not, the residual distribution has changed
   and the intervals need recalibrating.
4. Re-score the rubric in the audit report. Data integrity cannot pass
   "realistic dependence structure" on simulated data; official data replaces
   that criterion with the reconciliation results.

## Open questions for the discussion

- Which ministries can share at HEI × programme × year grain, and which only
  at national or regional level? Lower grain means the HEI-level widgets fall
  back to aggregates.
- How far back do official series go? The backtest needs at least four years
  before its first origin; with fewer, only the naive baselines are eligible.
- Should simulated years be kept before the first official year (back-casting),
  or should series simply start later? Mixing them would blur the accuracy
  figures, so the current tooling replaces whole tables.
- Who owns refreshes, and how often? Vintage tracking is in place; a schedule
  is not.
