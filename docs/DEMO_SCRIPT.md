# PathWise — Demo Script

A 10–12 minute walkthrough for client presentations or project submission. Rehearse twice before going live.

---

## Setup (5 minutes before the demo)

1. `docker compose up -d` — start the stack
2. Wait for the backend log line: `PathWise API ready.`
3. Open two browser tabs:
   - Tab 1: `http://localhost:3000` (the dashboard)
   - Tab 2: `http://localhost:8000/docs` (API reference — useful if the client asks a technical question)
4. Pre-load the Student Evaluator with the **dramatic profile** below so you are not typing live

---

## Opening (1 min)

> "PathWise answers two questions at once: what does the market need right now, and how should we adjust our enrolment and curriculum to match it? I'll show you both modules in about ten minutes."

Start on the **Market Overview** page (it loads by default).

---

## Module 1 — Market Demand (4 min)

### 1. Overview page

Point out the five KPI cards:
- **Total placements** — confirms the dataset covers real hiring activity
- **Average salary** — anchors the conversation around ROI for students
- **Top role** — usually *Full Stack Developer* or similar; good hook for "is this what students should be aiming for?"

> "Everything on this page is computed live from the database — no hard-coded numbers."

---

### 2. Hiring Analytics page

Show the **top companies** bar chart and name the top 3.

Point to the **job-to-internship ratio** card:
> "A ratio above 1.0 means we're producing more job-ready graduates than intern-ready ones — that's the direction we want."

Show the **hiring sources** breakdown and call out the dominant sector.

---

### 3. Skill Gap page

This is usually the most impactful slide.

> "The blue bar is what employers are looking for. The green bar is what our current graduates actually bring. The gap between them is the opportunity."

Point to **the skill with the largest gap** (shown in the Top Gap Skill KPI card).
> "This is where a curriculum update would have the most direct impact on placement rates."

---

### 4. Demand Forecast page

Show the 12-month forecast area chart.

> "This is a Prophet time-series model trained on historical job-posting data. The shaded band is the 80% confidence interval — narrow means confident, wide means more uncertainty. The peak month tells us when to run our next employer outreach campaign."

---

## Module 2 — Student Enrollment Intelligence (5 min)

Switch to the Enrollment Intelligence section in the sidebar.

### 5. Enrollment Trends page

Select **MS Data Science** in the dropdown (it has the clearest upward trend in the dataset).

> "The solid line is historical enrolment. The dashed line is the LSTM neural network's 3-year forecast. The two lines share the last historical data point so the handoff is seamless."

---

### 6. Admission Risk page

> "Every programme gets a risk score based on year-on-year enrolment change. Red badge means declining, green means growing. The recommended intake column gives us a data-driven starting point for next year's targets."

Point to the **highest-risk programme** at the top of the table.

---

### 7. Placements by Stream page

> "This cross-references placement rate against student count. High placement rate but low student count — under-marketed. High count but low rate — curriculum or employer relationships need work."

---

### 8. Student Evaluator — the dramatic moment (2 min)

This is the highlight. Use this profile for the most impressive result:

| Field | Value |
|---|---|
| GPA | 3.9 |
| Internships | 4 |
| Projects | 5 |
| Communication score | 9 |
| Programme | MS Data Science |

Click **Predict Placement**.

Expected result: **~95% probability**, predicted **Placed**, large positive SHAP bars for GPA and Internships.

> "The model is telling us that GPA and internship count are doing most of the heavy lifting for this student. The SHAP chart makes that visible — the longer the bar to the right, the more that feature is pushing the probability up."

Then dial down to a contrasting profile to show the model works in both directions:

| Field | Value |
|---|---|
| GPA | 2.3 |
| Internships | 0 |
| Projects | 1 |
| Communication score | 3 |
| Programme | Certificate Data Analytics |

Expected result: **< 40% probability**, predicted **Not Placed**, negative SHAP bars.

> "And here the model flags this student as at risk. The skill recommendations below tell us exactly what to address — no guesswork needed."

---

## Closing (1 min)

> "Everything you just saw is running on a three-container Docker stack — Postgres, a FastAPI backend with three ML models, and a React frontend. All you need to run it yourself is Docker Desktop and one command: `docker compose up`."

Point to the two docs in the repo:
- `docs/TECHNICAL.md` — for anyone setting it up or retraining the models
- `docs/USER_GUIDE.md` — for anyone using the dashboard day-to-day

> "The models are production-ready. Accuracy is 88.2% on the placement model, RMSE of 4.7 on demand forecasting. Retraining takes one command whenever new data arrives."

---

## If Asked About Model Accuracy

> "The XGBoost placement model achieves 88.2% accuracy and an F1-score of 0.94 on the held-out test set. The Prophet demand forecast has an MAPE of 3.4% — within 3–4% of actual job posting counts on the test period. Full metrics are in `ml/models/model_metrics.json`."

---

## If Asked How to Update With New Data

> "Load the new data into Postgres — the same ETL scripts handle that. Then run `bash scripts/retrain.sh` (or the Docker version). The retraining pipeline runs in under ten minutes and the backend reloads the new models automatically."

---

## Backup: Quick API Tour (if client is technical)

Open `http://localhost:8000/docs` in Tab 2.

Show the `/api/enrollment/predict-placement` endpoint — click **Try it out**, paste the strong student profile, hit **Execute**, and show the raw JSON response with SHAP values.

> "Every chart in the dashboard is backed by an API endpoint. You can query these directly, pipe them into your own BI tools, or build on top of them."
