# PathWise — User Guide

PathWise is a role-based education–employment alignment platform for Ethiopia.
It forecasts student demand (Model 1), labour demand (Model 2) and the gap
between them (Model 3), then shows each audience only the pages it is allowed
to see.

The numbers are **simulated Ethiopian structure, 2016–2025**, not official MoE,
MoLS or ESS statistics. The chip in the top bar says so. So does the amber
note on each widget page.

---

## Signing in

Open PathWise at `http://localhost:3001`.

All demo accounts use the password **`pathwise123`**.

| Sign in as | Role | You land on |
|---|---|---|
| `student` | Student | Profile & eligibility |
| `university` | University (Addis Ababa University) | Institution overview |
| `moe` | Ministry of Education | National snapshot |
| `mol` | Ministry of Labour | Labour pulse |
| `admin` | Administrator | Platform overview |

You only see pages your role can open. Hitting another role’s URL returns you
to your home page — the API enforces this, not just the menu.

Click your name in the sidebar footer for **Your account** (password change).
Sign out with the arrow beside it.

---

## Layout

- **Sidebar** — your role’s pages, grouped as in the lists below. On a phone,
  tap ☰.
- **Search (`Ctrl K` / `Cmd K`)** — occupations, fields and programmes your
  role may open.
- **Provenance chip** — source and vintage. Hover for the caveat.

If a page shows a red error banner, the API is down. Click **Retry**.

---

## What a ranking is (and is not)

- **Fit classification is not a ranking.** Matched / overeducated /
  undereducated is near-uniform across fields. Alternative paths, field
  priority and programme health do **not** use it.
- **What-if is not circular.** A saved MoE simulator run is a draft
  (`official_forecast: false`). It does not become next year’s baseline.
- **Scores are relative.** A 70 means high among the rows on screen, not
  “70% good”. Open the factor breakdown.

Leftover pages come in two kinds, and neither is Ethiopia Model 1 or Model 2:

- **US-model tools** (placement odds, salary, job market, enrolment LSTM) are
  switched off. Their pages and routes exist only when the platform runs with
  `LEGACY_US_MODELS=1`.
- **Older dashboard pages** (career explorer, expansion, peer benchmark, field
  explorer, investment matrix, emerging occupations, supply–demand, regional
  demand) read the Ethiopia tables. They are hidden from role nav but open from
  search results and bookmarks.

---

## 1. Student

Sidebar follows `navConfig.js`.

### Your programme

1. **Profile & eligibility** — your signed-in identity. Query-string
   `username` / `student_id` are ignored.
2. **Labour outlook** — 3- and 5-year vacancy outlook for your field.
   Occupation cells smaller than 5 are withheld.
3. **Demand comparison** — student demand vs labour demand.
4. **Field opportunity** — alignment score with published weights.
5. **Supply–demand gap** — expected graduates vs vacancies.

### Explore options

6. **Alternative paths** — ranked on labour demand, supply, eligibility and
   skills. Fit classification does not enter.
7. **Skill roadmap** — technical / digital / soft / emerging demand.
8. **Pathways** — programme graph for your field.
9. **Opportunities** — scholarships, internships, training, hiring windows.
   Lists do not include other students’ accounts.

---

## 2. University (Addis Ababa University)

The token carries the institution. You cannot pass `?institution=` for another
HEI without a `CROSS_INSTITUTION` grant.

### My institution

1. **Overview** — this HEI only.
2. **Programme health** — expand / maintain / review / consolidate from the
   labour–graduate gap. Not fit class.
3. **Unconstrained demand** — Model 1 layer 1.
4. **Constrained enrolment** — Model 1 after exam, quota, priority and
   capacity.
5. **Demand vs labour** — three series: student demand, expected graduates,
   labour demand.

### Progression

6. **Admissions funnel**
7. **Cohort progression**
8. **Graduate outcomes**
9. **Curriculum heatmap**
10. **Resource planning** — unofficial what-if; `official_forecast` stays false.

---

## 3. Ministry of Education

### Education supply

1. **National snapshot**
2. **Demand vs capacity** — unconstrained vs constrained.
3. **National field gap**
4. **Policy simulator** — quota, priority field, placement rule, capacity.
   Persist writes a **draft**. It is not an official circular.

### Investment planning

5. **Field priority** — reads `/api/model3/policy-priority` (labour shortage,
   national priority, student demand, feasibility). The yaml investment
   ranker stays on `/api/education/investment-priority` and is not swapped
   into this page.
6. **Regional alignment**
7. **Institution comparison**
8. **Policy impact** — unofficial; `official_forecast: false`.

---

## 4. Ministry of Labour

### Labour market

1. **Labour pulse**
2. **Formal vs informal**
3. **Sector forecast** — Model 2, using whichever of four estimators had the lowest error on past years, with a 90% range.
4. **Skills heatmap** — fit classification is listed alphabetically with a
   caveat; it is not a league table.

### Pipelines

5. **Public hiring**
6. **FDI and parks**
7. **Graduate absorption**
8. **Migration**
9. **Workforce report** — download writes a `report_export` audit row.
   `official_forecast` stays false.

---

## 5. Administrator

### Platform

1. **Overview** — API health and account counts.
2. **Data pipeline** — all **20** Ethiopia feeds (education, labor, policy,
   investment).
3. **Data quality** — validation failures from `_validate.py`.
4. **Model monitoring** — backtest error of each forecast's chosen model, input drift and error drift.
   Leftover US placement drift (baseline 0.88) is secondary.
5. **Accounts** — create, role, reset password, deactivate. Never deletes
   from the UI. Last-admin and self-lockout guards are server-side.

### Governance

6. **Scenarios** — persisted what-ifs. Approval does not set
   `official_forecast`.
7. **Audit log** — searchable by action (try `report_export`).

### Methodology

8. **Importance & AHP** — two panels: learned importance (SHAP /
   permutation) and collection-priority tiers. They are never blended.
   AHP pairwise weights: consistency ratio **> 0.1 is refused** (422,
   `weights: null`). AHP does not train Models 1–3.

Admin can also open ministry, institution and student views from the
sidebar. The API still requires the right role for writes; admin is allowed
to read.

---

## FAQ

**Can I quote these figures in a ministry circular?** No. They are simulated
until an official parquet replaces the generator file. See
[DATA_PROVENANCE.md](DATA_PROVENANCE.md).

**Why do leftover US pages still exist?** The four US-model tools are kept for
side-by-side demonstration only and are off by default (`LEGACY_US_MODELS`).
The older dashboard pages still open from search and bookmarks. Ethiopia
scores live on the Model 1–3 widget pages.

**Why did AHP return 422?** The pairwise matrix is inconsistent (CR > 0.1).
Fix the judgements; do not paste those weights into a learner.
