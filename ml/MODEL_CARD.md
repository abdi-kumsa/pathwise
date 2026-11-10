# PathWise ML Model Card

Ethiopia Models 1–3 are the request-path scores. Placement XGBoost remains on
the leftover student tools. AHP is a **separate** methodology and does not
train anything. US LSTM and Prophet are appendix-only: **not compared**.

Figures are simulated Ethiopian structure (2016–2025) until official files
replace the parquets.

---

## 1. Model 1 — Student education demand

| Attribute | Value |
|-----------|-------|
| Task | Layer 1: forecast applications (unconstrained demand) per HEI × campus × programme × year. Layer 2: turn demand into enrolment |
| Request-path estimator | Lowest backtest RMSE per horizon among `seasonal_naive`, `historical_mean`, `drift`, `pooled_ridge` (`ml/forecasting.py`) |
| Validation | Rolling-origin backtest, origins 2019–2024, horizons 1–5 |
| Intervals | 90%, empirical residual quantiles; coverage measured leave-one-origin-out |
| Constraint layer | Exam eligibility, placement rules, intake quotas, priority fields, capacity (`ml/model1/layer2_constraints.py`) |
| Collection-priority yaml | `docs/spec/model1_attributes.yaml` (not used as weights) |

Layer 1 forecasts *applications* because observed enrolment has already
passed every real constraint; forecasting it and then constraining again (as
earlier waves did) applied the rules twice. Backtest errors and skill against
the naive baselines are in [docs/MODEL_COMPARISON.md](../docs/MODEL_COMPARISON.md).
They are measured on simulated data (WV.SIM1).

**Artefacts**
- `ml/model1/layer1_demand.py` — unconstrained forecast
- `ml/model1/layer2_constraints.py` — constrained enrolment
- `ml/model1/compare.py` — holdout comparison
- `backend/services/constraint_service.py` — API wrapper

AHP and DOC1 collection priorities do not enter training.

---

## 2. Model 2 — Labour-market demand

| Attribute | Value |
|-----------|-------|
| Task | Forecast employment (region × sector), vacancies (region × occupation) and the skill-shortage index (field); growth and occupational demand are derived |
| Request-path estimator | Same engine and selection rule as Model 1 |
| Validation | Rolling-origin backtest |
| Monitoring | Input PSI and error drift per target (`ml/drift.py`, `/api/monitoring/drift`) |
| Collection-priority yaml | `docs/spec/model2_attributes.yaml` |

**Artefacts**
- `ml/model2/forecast.py`
- `ml/model2/compare.py`
- `backend/services/model2_service.py` / `labour_market_service.py`

---

## 3. Model 3 — Alignment and scenarios

| Attribute | Value |
|-----------|-------|
| Task | Graduate supply vs labour demand; student / policy / institution actions |
| Method | Explicit weighted scores after min-max normalisation |
| Fit classification | `fit_classification_used: false` on every ranking payload |
| What-if | Scenario runner; persisted runs stay `official_forecast: false` |

Student alternatives, field alignment and MoE policy-priority return `weights`,
`method` and per-factor rows (RANK.R3). Programme health ranks on the sign of
labour minus expected graduates; severity is a quartile of \|gap\| (RANK.R4).

**Artefacts**
- `ml/model3/gap.py`, `recommend.py`, `pathways.py`, `scenario.py`, `supply.py`
- `backend/services/alignment_service.py`

---

## 4. Placement XGBoost (leftover US tools)

| Attribute | Value |
|-----------|-------|
| Task | Binary classification (placed / not placed) |
| Algorithm | XGBoost (`XGBClassifier`) |
| Training rows | 2,400 synthetic US-style students |
| Accuracy / F1 | 88.17 % / 93.71 % |

Used by `/student/evaluator` and career-explorer odds when a full profile is
filled. **Not** an Ethiopia Model 1 or Model 2 score (WV.US1).

Salary XGBoost (`XGBRegressor`, RMSE ≈ $14k, R² 0.36) remains on
`/student/salary`. Read as a programme-level USD band, not an ETB forecast.

**Artefacts**
- `ml/models/placement_xgboost.pkl`, `salary_xgboost.pkl`
- `ml/predict_placement.py`, `ml/predict_salary.py`
- `ml/explain_predictions.py` — SHAP for this model

---

## 5. AHP — separate methodology

Saaty pairwise comparison → principal eigenvector weights → consistency
ratio. CR > 0.1 **refuses** the matrix (`weights: null`). Output is shown next
to SHAP on the admin methodology page. It does not reweight training samples
or enter a loss.

**Artefacts:** `ml/ahp/`, `GET|POST /api/ahp/weights`, `POST /api/ahp/consistency`

---

## Appendix — US LSTM / Prophet (not compared)

These artefacts stay on disk, served only when the API runs with
`LEGACY_US_MODELS=1` (and installed only from `backend/requirements-legacy.txt`).
They are **not** scored as Ethiopia models and do not appear in `ml/models/ethiopia_comparison.json`
except under `not_compared`.

### LSTM — enrolment (US programmes)

| Attribute | Value |
|-----------|-------|
| Task | Programme enrolment count |
| Algorithm | 2-layer LSTM 32→16 (Keras/TensorFlow) |
| Route | `/university/enrollment` |
| Artefacts | `ml/models/enrollment_lstm.keras`, `enrollment_scaler.pkl` |

### Prophet — job-market postings (US)

| Attribute | Value |
|-----------|-------|
| Task | Monthly job postings |
| Algorithm | Prophet, yearly multiplicative seasonality |
| Route | leftover `/api/market/demand-forecast` |
| Artefacts | `ml/models/demand_prophet.pkl` |

Do not mix these RMSE figures with Ethiopia M1/M2 comparison tables.

---

## Explainability rule

SHAP and permutation importance are **learned**, after training.
DOC1 collection priorities are **expert / data-collection**. Two panels. Never one
blended number. See [docs/FEATURE_IMPORTANCE.md](../docs/FEATURE_IMPORTANCE.md).
