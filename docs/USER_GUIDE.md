# PathWise — User Guide

PathWise is a predictive analytics platform that helps academic institutions answer two questions at the same time: what does the job market need right now, and how should we adjust our enrolment and curriculum to match it?

The platform has two dashboard modules. **Module 1 — Market Demand** is for department heads and institutional leaders who need to track hiring trends and skill gaps. **Module 2 — Student Enrollment Intelligence** is for admissions staff and students who need enrolment forecasts, risk signals, and personalised placement advice.

---

## Table of Contents

1. [Getting Around the Dashboard](#1-getting-around-the-dashboard)
2. [Module 1 — Market Demand Dashboard](#2-module-1--market-demand-dashboard)
   - [Overview](#21-overview)
   - [Hiring Analytics](#22-hiring-analytics)
   - [Skill Gap Analysis](#23-skill-gap-analysis)
   - [Demand Forecast](#24-demand-forecast)
3. [Module 2 — Student Enrollment Intelligence Dashboard](#3-module-2--student-enrollment-intelligence-dashboard)
   - [Enrollment Trends](#31-enrollment-trends)
   - [Admission Risk](#32-admission-risk)
   - [Placements by Stream](#33-placements-by-stream)
   - [Student Evaluator](#34-student-evaluator)
4. [How to Use the Student Evaluator — Step by Step](#4-how-to-use-the-student-evaluator--step-by-step)
5. [Interpreting SHAP Feature Contributions](#5-interpreting-shap-feature-contributions)
6. [Interpreting Admission Risk Scores](#6-interpreting-admission-risk-scores)
7. [FAQ](#7-faq)

---

## 1. Getting Around the Dashboard

When you open PathWise at `http://localhost:3000` you land on the Market Overview page. The left-hand sidebar is always visible and is divided into two sections:

**Market Demand** (Module 1)
- Overview
- Hiring analytics
- Skill gap
- Forecast

**Enrollment Intelligence** (Module 2)
- Enrollment trends
- Admission risk
- Placements
- Student evaluator

Click any item to navigate to that view. All data loads automatically when the page opens — you do not need to press a refresh button. If data is still loading, placeholder dashes (—) appear in the KPI cards until the values arrive.

If a page shows a red error banner, the API is temporarily unavailable. Click the **Retry** button that appears inside the banner to try again.

---

## 2. Module 1 — Market Demand Dashboard

### 2.1 Overview

**What it shows:** A snapshot of the entire hiring landscape sourced from the platform's placement and job-posting dataset.

| Card | What it means |
|---|---|
| Total companies | Number of distinct organisations that have hired from this institution |
| Total placements | Number of successful job placements recorded |
| Average salary | Mean starting salary across all placed graduates (USD) |
| Avg time to hire | Mean number of days from graduation to signed offer |
| Top role | The job title appearing most frequently among placed graduates |

**How to use it:** This page is the entry point for any conversation about institutional performance. Share the total placements and average salary figures with prospective students or accreditation bodies as headline indicators.

---

### 2.2 Hiring Analytics

**What it shows:** A deeper breakdown of the hiring picture across four dimensions.

**Top hiring companies bar chart** — the organisations placing the most graduates. Use this to decide which employers deserve a dedicated relationship programme or on-campus recruitment visit.

**Job-to-internship ratio** — the ratio of full-time job placements to internships undertaken. A ratio below 1.0 means the institution produces more intern-ready graduates than job-ready ones; a ratio above 1.0 suggests strong direct-hire outcomes.

**Hiring sources (by industry sector)** — which industry sectors are absorbing graduates. Technology and Finance typically dominate; a large share going to Consulting suggests generalist graduates rather than specialist ones.

**Average time-to-hire KPI** — how long graduates wait for an offer after graduation. Anything above 90 days warrants a review of career services timing and employer outreach.

---

### 2.3 Skill Gap Analysis

**What it shows:** Where employer demand for skills outpaces the institution's current curriculum delivery.

The bar chart compares **Demand Score** (how heavily employers weight this skill, derived from SHAP feature importance on the placement model) against **Curriculum Coverage** (how well current graduates demonstrate the skill, derived from actual student data). The gap between the two bars is the **Gap Score**.

| KPI Card | What it means |
|---|---|
| Top gap skill | The single skill with the largest demand–coverage gap |
| Average gap score | Mean gap across all tracked skills — higher means the curriculum is broadly misaligned |
| Number of skills tracked | Total skills with demand data |

**How to use it:** Sort attention by gap score. A large gap in GPA (academic performance) suggests the intake quality needs attention. A large gap in Industry Experience (internships) suggests the institution needs more mandatory placement years or co-op programmes. A large gap in Communication Skills suggests soft-skills training is under-weighted in the curriculum.

---

### 2.4 Demand Forecast

**What it shows:** A 12-month forward view of hiring demand based on the Prophet time-series model trained on historical job-posting data.

The area chart shows three lines:
- **Predicted postings** — the model's best estimate
- **Upper bound** — 80% confidence interval ceiling
- **Lower bound** — 80% confidence interval floor

The shaded band between upper and lower bounds represents forecast uncertainty. A narrow band means the model is confident; a wide band means external factors (economic cycles, seasonal hiring patterns) are harder to predict.

**KPI Cards:**
- **12-month total** — sum of predicted postings across the entire forecast horizon, useful for capacity planning
- **Peak month** — the month with the highest predicted demand
- **Trend** — whether demand is expected to grow, hold, or contract

**How to use it:** Use peak month data to time career fairs and employer outreach. Use the 12-month total to set enrolment targets — if hiring demand is forecast to contract, intake should be adjusted to avoid a cohort graduating into a tighter market.

---

## 3. Module 2 — Student Enrollment Intelligence Dashboard

### 3.1 Enrollment Trends

**What it shows:** Historical enrolment counts and a 3-year LSTM-powered forecast for any of the 12 programmes.

**Summary KPI cards (top row):**
- **Total students** — total enrolment across all years and programmes in the dataset
- **Programmes** — number of distinct programmes
- **Avg placement rate** — institution-wide mean placement rate across all programmes
- **Top programme** — programme with the highest student count

**Programme selector dropdown** — choosing a programme updates the forecast chart to show that programme's historical trend (solid line) merged into the LSTM forecast (dashed line). The two lines share their last historical data point so the transition is seamless.

**How to use it:** Compare programmes side-by-side by toggling the dropdown. A programme with a flat or declining historical trend and a forecast that continues flat is a candidate for intake reduction or a curriculum refresh to attract more applicants.

---

### 3.2 Admission Risk

**What it shows:** All programmes ranked by **admission risk score** — a measure of how much enrolment declined in the most recent year compared to the year before.

**Risk score:** A positive number means enrolment is falling. Zero means stable or growing. The higher the number, the faster the decline. Risk scores are expressed as percentage-point change (e.g. a score of 24.5 means enrolment fell roughly 24.5% year-on-year).

**Trend badge:**
- **Declining** (red) — enrolment fell more than 2% year-on-year
- **Stable** (amber) — change within ±2%
- **Growing** (green) — enrolment grew more than 2%

**Recommended intake** — a model-suggested target intake for the next year, computed as the programme's two-year average enrolment multiplied by its placement rate. It is a starting point for planning discussions, not a hard directive.

**Limit slider** — drag left or right to show fewer or more programmes in the table. The API is called automatically 500 ms after you release the slider (debounced) so the table does not flicker on every pixel of movement.

**How to use it:** Programmes with high risk scores and a Declining badge need immediate attention — they may need marketing investment, a curriculum update, or an intake reduction to protect placement rates. Programmes with a Growing badge and a reasonable recommended intake can be considered for capacity expansion.

---

### 3.3 Placements by Stream

**What it shows:** Placement rate, average starting salary, and student count for each of the 12 programmes, sorted from highest to lowest placement rate.

| Column | What it means |
|---|---|
| Programme | Degree or certificate name |
| Placement rate | Percentage of that programme's graduates who secured employment |
| Avg salary | Mean starting salary for placed graduates from that programme (USD) |
| Students | Total number of students enrolled in that programme across all years |

**Summary KPI cards:**
- **Overall placement rate** — weighted mean across all programmes
- **Top programme** — programme with the highest individual placement rate
- **Avg salary** — institution-wide mean starting salary

**How to use it:** Cross-reference placement rate against student count. A programme with a very high placement rate but low student count might be under-marketed. A programme with a high student count but low placement rate is where the curriculum or employer relationships need the most work.

---

### 3.4 Student Evaluator

**What it shows:** A personalised XGBoost placement probability score for any hypothetical student profile, along with a SHAP waterfall chart explaining the prediction, skill-building recommendations, and alternative career pathways.

This is the only interactive page in the platform — you adjust the student profile controls and the model runs a real-time prediction.

---

## 4. How to Use the Student Evaluator — Step by Step

**Step 1 — Set the student profile**

Use the sliders on the left panel to set the student's attributes:

| Control | Range | What it represents |
|---|---|---|
| GPA | 2.0 – 4.0 | Cumulative grade point average |
| Internships | 0 – 10 | Number of internship or co-op placements completed |
| Projects | 0 – 10 | Number of independent or academic projects completed |
| Communication score | 1 – 10 | Self-assessed or assessed communication ability (1 = very low, 10 = excellent) |

Use the **Programme** dropdown below the sliders to select the student's current degree programme.

**Step 2 — Click "Predict Placement"**

The button runs the XGBoost model against the profile you set. The button label changes to **Predicting…** while the model computes. This typically takes less than one second.

**Step 3 — Read the probability circle**

The large circle in the results panel shows the placement probability as a percentage:
- **Green (≥ 75%)** — strong likelihood of placement
- **Amber (50–74%)** — moderate likelihood; targeted improvements recommended
- **Red (< 50%)** — low likelihood; significant skill development needed

Below the circle, the **Placed** or **Not Placed** badge shows the model's binary classification (threshold: 50%).

**Step 4 — Study the SHAP waterfall chart**

The horizontal bar chart below the probability circle shows which parts of the student's profile drove the prediction. See §5 for a full explanation of how to read this chart.

**Step 5 — Review Skill Recommendations**

Below the SHAP chart, a **Skill Recommendations** section lists the top skills to develop, each with a **priority badge** (High / Medium / Low) and a one-line reason explaining why that skill matters. These are ordered by how much improving that skill would move the placement probability.

**Step 6 — Review Alternative Pathways**

At the bottom, the **Alternative Pathways** section lists supplementary qualifications (certificates, part-time courses) the student can pursue to increase their employability independent of their main programme.

**Step 7 — Reset and try another profile**

Click **Reset** to clear the results and run a new prediction with a different profile. This is useful for comparing a student's current profile against a target profile (e.g. "what if they did one more internship?").

---

## 5. Interpreting SHAP Feature Contributions

SHAP (SHapley Additive exPlanations) answers the question: *how much did each feature push this prediction higher or lower compared to the average prediction?*

**Reading the chart:**

- Each bar represents one feature (GPA, Internships, Projects, Communication)
- **Bars pointing right (positive SHAP)** — this feature pushed the probability *up*
- **Bars pointing left (negative SHAP)** — this feature pushed the probability *down*
- The longer the bar, the stronger the influence
- The **base value** shown below the circle is the model's average prediction across all students. It is the starting point before any individual features are applied.

**Example interpretation:**

> Base value: 2.04 log-odds (≈ 88% avg probability)
> GPA: +1.29 (long bar right) → high GPA is the biggest driver of this student's strong prediction
> Internships: +0.74 → 3 internships are contributing positively
> Projects: -0.12 → project count is slightly below where the model expects

This tells you that even if this student's GPA dropped slightly, the internships would maintain a strong prediction. Conversely, if they had zero internships, the GPA alone would not be enough.

**What to do with this information:**

- Features with long **negative** bars are the highest-priority improvement areas
- Features already strongly positive confirm what the student is doing well — reinforce those
- The Skill Recommendations section translates SHAP results into plain-language actions so students do not need to understand the underlying math

---

## 6. Interpreting Admission Risk Scores

The admission risk score is computed from year-on-year enrolment change per programme:

```
risk_score = max(0, -(current_year_count - prev_year_count) / prev_year_count × 100)
```

In plain terms: if a programme lost students, the risk score equals the percentage it lost. If it grew or held steady, the risk score is 0.

**Score thresholds (suggested interpretation):**

| Risk score | Interpretation | Suggested action |
|---|---|---|
| 0 – 5 | Normal variation | Monitor quarterly |
| 5 – 15 | Mild decline | Review programme marketing and employer relations |
| 15 – 25 | Significant decline | Curriculum review; consider intake reduction |
| 25+ | Severe decline | Strategic review; programme restructure may be needed |

**Important caveat:** The dataset covers 2019–2024 and includes the pandemic years (2020–2021) which saw unusual enrolment patterns across all programmes. A high risk score for a programme that declined during 2020–2021 but has since recovered should be weighted accordingly.

---

## 7. FAQ

**Q: Does PathWise use real student data?**
A: No. All data in the platform is synthetic — generated using the Python Faker library to simulate realistic student profiles, enrolment patterns, and job placements. No personally identifiable information is stored or processed.

**Q: How often is the data refreshed?**
A: The ML models were trained on the 2019–2024 synthetic dataset. The platform does not pull live data automatically. To update the models with new data, re-run the data generation scripts and then re-train (see the Technical Reference, §7).

**Q: Why does the SHAP chart show log-odds values instead of percentages?**
A: SHAP contributions are additive in log-odds space, which is the internal representation the XGBoost model uses. Converting individual contributions to probabilities would make them non-additive and harder to interpret. The base value and individual bars all operate in log-odds; the circular probability display at the top converts the final sum back to a 0–100% range for readability.

**Q: Can I evaluate a student not in the dataset?**
A: Yes — the Student Evaluator accepts any combination of GPA, internships, projects, communication score, and programme. The model has no memory of individual students from the training data; it only learned the statistical relationship between these features and placement outcomes.

**Q: The prediction is 97% — does that mean this student is guaranteed a job?**
A: No. The probability reflects the statistical likelihood based on historical patterns in a synthetic dataset. Real placement depends on many factors the model does not capture: economic conditions, interview performance, location preferences, and the specific role. The score is a guide for prioritising support, not a guarantee.

**Q: What do the alternative pathways mean?**
A: They are supplementary qualifications (graduate certificates, cloud certifications, MBA modules) that the platform's recommendation engine identifies as high-value additions based on which skills have the largest gap between employer demand and current graduate supply. They are not affiliated with any specific institution.

**Q: The page shows a red error banner — what should I do?**
A: Click **Retry** inside the banner. If the error persists, check that the backend container is running: open `http://localhost:8000/health` in a new browser tab. If it shows an error or does not load, contact your system administrator or consult the Troubleshooting section of the Technical Reference.

**Q: Can I export the charts or data?**
A: The current version does not have a built-in export feature. To extract data, use the API directly — all endpoints are documented at `http://localhost:8000/docs` and return standard JSON that can be copied or piped to a file.
