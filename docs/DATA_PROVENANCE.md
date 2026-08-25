# Data Provenance

What the numbers in PathWise are, where they come from, and what they cannot
support. Read this before quoting a figure from the dashboards.

---

## 1. The datasets

| File | Rows × cols | Period | Feeds |
|---|---|---|---|
| `Assets/job_market_forecasting_data.csv` | 3000 × 35 | 2020–2025, monthly | Labour demand (MoL), career explorer, investment matrix |
| `Assets/student_enrollment_forecasting_data.csv` | 2000 × 41 | 2020–2025, by term | Education supply (MoE), institution views (University) |
| `data/mock/students.csv` | 3000 | — | ML feature store |
| `data/mock/placements.csv` | 3000 | — | Graduate outcomes, fit classification |
| `data/processed/features.parquet` | 3000 × 24 | — | All ML inference |

Both `Assets/` files were only read by `data/load_to_db.py` before the
role-based work — nothing queried the resulting tables, so 76 columns of
demand, supply, cost and outcome data sat unused. They are now the backbone
of every role dashboard.

---

## 2. Geographic framing — read this first

**This is a US-benchmarked reference dataset.** US metro areas (CBSA names),
US states, USD salaries, US SOC occupation codes, US institution types.

PathWise is presented to Ethiopian stakeholders (MoE, MoL), and the two do not
match. The decision taken was to **keep the data as it is and label it
honestly** rather than relabel regions or convert currency, because:

- the *methodology* transfers unchanged — a demand-vs-supply growth matrix works
  on any country's data
- relabelling US figures as Ethiopian would produce numbers nobody could defend
  in a viva or to a ministry

Every dashboard therefore carries the chip **“US benchmark dataset · 2020–2025”**
in the top bar, and every API response includes a `dataset_label` field saying
the same. To localise, replace the two `Assets/` CSVs with equivalents using the
same column names — no service code changes.

---

## 3. The join backbone

```
job_title  ──►  job_family  ═══  field_of_study  ──►  program_name
  (33)            (9)          identical vocabulary       (12)
```

`job_family` in the jobs data and `field_of_study` in the enrollment data share
the **same nine values exactly** — verified, no mapping table needed. This is
what lets a student name a target job and be told which department to join, and
what lets MoE compare labour demand against graduate supply per field.

Implemented in `backend/services/_datasets.py`.

### The one gap

`data/mock/placements.csv` records outcomes against `role`, drawn from the same
33-title vocabulary, but only **28 of 33 overlap**. The five placement-only
titles are mapped explicitly in `_datasets._PLACEMENT_ROLE_FAMILY`:

| Placement role | Assigned family |
|---|---|
| QA Engineer | Software Engineering |
| Release Manager | DevOps |
| Scrum Master | Product Management |
| Solutions Architect | Cloud Infrastructure |
| UX Researcher | UX Design |

Without this map, 371 of 2649 placed rows (14%) drop silently out of every
family aggregate.

---

## 4. Known limitations

### 4.1 Graduate fit classification is not comparable across fields

`/api/labour/mismatch` returns Matched / Overeducated / Undereducated. The
system-wide figure is sound: **87% of placed graduates hold a role that does not
match their credential level.**

The per-field and per-programme breakdowns are **not** a ranking. The
distribution is near-identical everywhere — roughly 80% Undereducated, 13%
Matched, 5% Overeducated — with an observed spread of **5.3 percentage points**
across all nine fields. `data/mock/placements.csv` is synthetic and its
generator encoded no between-group signal.

Consequences, enforced in code:

- every mismatch response carries `comparable: false` and a `caveat` string
- `SkillsMismatchPage.jsx` renders one system-wide bar, lists the breakdown
  **alphabetically rather than by match rate**, and shows the caveat in a
  cautionary banner above the table
- the observed spread is printed on the page so a reader can judge for themselves

**For a mismatch signal with real variance, use the supply–demand gap**
(`/api/labour/supply-demand`), which ranges across an order of magnitude
between fields.

### 4.2 Supply–demand severity is a relative rank

Coverage (supply ÷ demand) sits between 90% and 93% for every field, so any
fixed coverage threshold would bucket all nine identically. Severity is
therefore a **quartile rank of the absolute unfilled-headcount gap**, which does
separate them. The response says so in `severity_basis`.

### 4.3 Scores are relative, not absolute

The career recommender, investment priority and expansion scores all min-max
normalise each factor **across the current cohort** before weighting. A score of
70 means "high within these twelve programmes", not "70% good". Every response
returns its `weights` and a `method` string, and every score is shown decomposed
into per-factor contributions so the ranking can be audited.

### 4.4 Quadrant boundaries are medians

The MoE investment matrix splits at the median of each axis, so the four
quadrants always partition the nine fields. Membership is relative to this
cohort. A field in "Review" has slow growth on both axes — it is not necessarily
small, so check total openings before acting.

### 4.5 Mock vs. real

`data/mock/*.csv` are generated (`data/generate_mock_data.py`). The two
`Assets/` files are the substantive datasets. Model metrics in
`ml/MODEL_CARD.md` are computed against the mock-derived feature store and
should be read as pipeline validation, not as claims about real-world accuracy.

---

## 5. What is *not* on the request path

All `/api/*` dashboard endpoints read parquet and CSV. **Postgres serves exactly
one table on the request path: `users`, for authentication.** The other four
tables are an ETL sink. See `docs/TECHNICAL.md` §4.
