# Data Provenance

What the numbers in PathWise are, where they come from, and what they cannot
support. Read this before quoting a figure from the dashboards.

---

## 1. The request-path dataset

**PathWise serves a simulated Ethiopian structure for 2016–2025.** Real region
names, HEI names and MoE programme bands. Generated values. Not official CSA,
MoE or ESS statistics.

Every `/api/*` JSON **object** carries a `provenance` block:

```json
{
  "source": "Simulated Ethiopian structure",
  "tier": "simulated",
  "as_of": "2016–2025",
  "method": "seeded generator in data/ethiopia/generate.py",
  "caveat": "Simulated Ethiopian structure (real regions, HEIs, MoE bands). Not official MoE, MoLS or ESS statistics."
}
```

`tier` is `simulated` until an official file replaces a parquet in place. It may
be `derived` for ranks, ratios and forecasts computed from stamped series. It is
never `official` in this build.

The shell chip (`ProvenanceBadge`) shows the same stamp. Widget pages add a
page-level `DataNote`.

Waiver **WV.SIM1** records this until official files exist.

---

## 2. Twenty fact tables

All live under `data/ethiopia/`. One table per DOC1 category. CSV beside parquet
for inspection. Reference dimensions in `data/ethiopia/reference/`
(`regions.csv`, `heis.csv`, `fields.csv`, `industrial_parks.csv`).

| Table | Family | Intended official source |
|---|---|---|
| `enrollment_history` | education | MoE EMIS |
| `admissions_funnel` | education | MoE / HEI SIS |
| `exam_placement` | policy | MoE placement |
| `demographics` | education | CSA / MoE |
| `capacity_quota` | policy | MoE quotas |
| `institution_capacity` | education | HEI / MoE |
| `graduate_outcomes` | education | HEI tracer / ESS |
| `finance_support` | education | MoE / MoF |
| `cohort_progression` | education | HEI SIS |
| `labour_history` | labor | ESS / MoLS |
| `vacancies` | labor | MoLS / job boards |
| `skills_demand` | labor | MoLS |
| `labour_demographics` | labor | ESS |
| `formal_informal` | labor | ESS |
| `sector_output` | labor | CSA / NBE |
| `public_hiring` | policy | CSC / MoLS |
| `fdi_industrial` | investment | EIC / industrial parks |
| `macro_regional` | investment | CSA / regional bureaux |
| `macro_financial` | investment | NBE |
| `shocks_seasonality` | investment | CSA / disaster agencies |

Join backbone:

```
field  ──►  programme / department
 HEI   ──►  campus  ──►  region
occupation / sector  ──►  region
academic year 2016–2025
```

`backend/services/_datasets.py` is the reader. Models 1–3 join on field, HEI
and region — not on US metro or SOC codes.

---

## 3. How to replace a parquet with an official file

1. Open the contract for that table under `docs/spec/ingestion/<table>.md`.
2. Keep the grain, keys and column names. Extra columns are ignored; missing
   required columns fail `backend/services/_validate.py`.
3. Drop the file in place as `data/ethiopia/<table>.parquet` (CSV optional).
4. Restamp `provenance` on those rows to `official` with the real `source` and
   vintage. `_validate.py` accepts official rows that declare a source; it does
   not fail them for not being all-`simulated`. Until an official file lands,
   the API stamp stays `simulated`.
5. Restart the backend (`docker compose restart backend` on Windows).

Do not relabel US metros as Ethiopian regions. The US CSVs are **retired from
the request path**. They live in `archive/us_benchmark/` and on leftover tool
routes only (waiver **WV.US1**).

---

## 4. What is not on the Ethiopia request path

| Source | Role today |
|---|---|
| `data/ethiopia/*.parquet` | Models 1–3, five role dashboards, admin pipeline |
| `data/processed/features.parquet` | Leftover US placement / salary XGBoost |
| `data/mock/placements.csv` | Leftover US placement tools |
| `ml/models/enrollment_lstm.keras` | Leftover university LSTM page |
| `ml/models/demand_prophet.pkl` | Leftover US demand tool |
| Postgres `users`, `audit_log`, `scenarios`, `ahp_matrices`, `expert_validations` | Auth and Wave 7 governance |

Postgres is not the analytics store. A database outage blocks sign-in; dashboard
reads still come from parquet.

---

## 5. Known limitations (honesty)

### 5.1 Graduate fit classification is not a ranking

Fit class (matched / overeducated / undereducated) is near-uniform across
fields. It must not enter any score, league table or alternative-path rank
(RANK.R1). Rankings use labour demand, expected supply, eligibility and
capacity. Every scoring payload returns `fit_classification_used: false`.

### 5.2 Scores are relative

Composite scores min-max normalise across the current comparison set. A score of
70 means “high among these rows”, not “70% good”. Payloads return `weights`,
`method` and per-factor rows (RANK.R3).

### 5.3 `ols_lags` holdout is not ministry accuracy

On the simulated lag construction, chronological holdout RMSE for `ols_lags` is
near-zero. Comparison still includes seasonal-naive and historical-mean. The
monitoring headline uses seasonal-naive. Waiver **WV.OLS1**.

### 5.4 GET `/api/users` is a stamped object

The accounts list returns `{ n, rows }` so provenance middleware can stamp it.
The page still carries a DataNote.

### 5.5 W.MOE.05 uses Model 3 policy-priority

Yaml `satisfied_by.endpoint` is `/api/model3/policy-priority`, matching the MoE
priority page. `education_service.get_investment_priority` remains on
`/api/education/investment-priority` and is not swapped into the widget.

### 5.6 Official ingest is unblocked, not present

The contract validator accepts `provenance: official` when `source` is set.
No official CSA / MoE / ESS file is in this build. Waiver **WV.SIM1**.

---

## 6. Related documents

- [METHODOLOGY.md](METHODOLOGY.md) — DOC1 steps 1–7
- [TECHNICAL.md](TECHNICAL.md) — routers, ports, tests
- [USER_GUIDE.md](USER_GUIDE.md) — five role walkthroughs
- [ml/MODEL_CARD.md](../ml/MODEL_CARD.md) — Ethiopia M1/M2/M3 and leftover US models
- [spec/waivers.yaml](spec/waivers.yaml) — residual caveats
