# PathWise ML Model Card

## Overview

Four models power the PathWise intelligence dashboards.  All are trained on
synthetic institutional data (3,000 students, 12 programmes, 2019–2024).

---

## 1. XGBoost — Placement Prediction

| Attribute | Value |
|-----------|-------|
| Task | Binary classification (placed / not placed) |
| Algorithm | XGBoost (`XGBClassifier`) |
| Input features | 16 (GPA, internships, projects, communication score, programme one-hot) |
| Training rows | 2,400 |
| Test rows | 600 |
| Accuracy | 88.17 % |
| Precision | 88.17 % |
| Recall | 100 % |
| F1-score | 93.71 % |

**Top features (by importance)**

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | Certificate Data Analytics | 10.2 % |
| 2 | MS Information Technology | 8.5 % |
| 3 | Projects | 6.5 % |
| 4 | Internships | 6.2 % |

**Artefacts**
- `ml/models/placement_xgboost.pkl` — trained model
- `ml/models/placement_feature_names.pkl` — ordered feature list
- `ml/predict_placement.py` — inference entry point
- `ml/explain_predictions.py` — SHAP explainability

---

## 2. XGBoost — Salary Prediction

| Attribute | Value |
|-----------|-------|
| Task | Regression (expected starting salary, USD) |
| Algorithm | XGBoost (`XGBRegressor`) |
| Input features | Same 16-feature vector as the placement model |
| RMSE | $14,288 |
| MAE | $12,128 |
| R² | **0.36** |

**Top features (by importance)**

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | Certificate Data Analytics | 30.5 % |
| 2 | MS Human-Computer Interaction | 13.8 % |
| 3 | MS Artificial Intelligence | 11.2 % |
| 4 | MBA Product Management | 10.2 % |

> **Interpretation caveat.** An R² of 0.36 means the model explains roughly a
> third of the variance in starting salary; the remaining two-thirds is driven
> by factors absent from the synthetic feature set (employer, negotiation,
> geography, prior experience). Feature importances are dominated by programme
> one-hots, so predictions are best read as *programme-level salary bands* with
> a wide error margin (MAE ≈ $12k) rather than individual salary estimates.
> Do not present a single-point prediction to a student without that band.

**Artefacts**
- `ml/models/salary_xgboost.pkl` — trained model
- `ml/models/salary_xgboost_meta.pkl` — feature list + metadata
- `ml/predict_salary.py` — inference entry point

---

## 3. LSTM — Enrollment Forecasting

| Attribute | Value |
|-----------|-------|
| Task | Regression (monthly/annual enrolment count per programme) |
| Algorithm | LSTM (2-layer, 32→16 units, Keras/TensorFlow) |
| Input | 3-year sliding window per programme (normalised) |
| Programmes | 12 |
| Sequence length | 3 years |
| Test year | 2024 (held-out) |
| Metric | RMSE, MAE (count units) |

**Design notes**

The dataset is small (72 programme×year rows).  Each programme is normalised
independently with its own `MinMaxScaler` so the model learns relative trends.
Rolling-forward inference allows multi-year forecasting (2025, 2026, …).

**Artefacts**
- `ml/models/enrollment_lstm.keras` — trained model
- `ml/models/enrollment_scaler.pkl` — per-programme scalers
- `ml/models/enrollment_lstm_meta.pkl` — programme list + seq_len
- `ml/predict_enrollment.py` — inference entry point

---

## 4. Prophet — Job-Market Demand Forecasting

| Attribute | Value |
|-----------|-------|
| Task | Time-series regression (monthly job postings) |
| Algorithm | Facebook Prophet (additive/multiplicative seasonality) |
| Frequency | Monthly (`MS`) |
| Training period | Jan 2019 – Jun 2024 |
| Test period | Jul–Dec 2024 (6 months) |
| Seasonality | Yearly (multiplicative); peaks Jan–Mar and Aug–Sep |

**Artefacts**
- `ml/models/demand_prophet.pkl` — fitted Prophet model
- `ml/predict_demand.py` — inference entry point

---

## Explainability

SHAP `TreeExplainer` is used for the XGBoost model.  Call
`explain_predictions.explain_student(student_dict)` to receive:
- Overall placement probability
- Per-feature SHAP contributions (ranked by magnitude)
- Base (expected) value

---

## Limitations

- All data is synthetic — performance metrics reflect simulated distributions.
- The salary regressor has low explanatory power (R² = 0.36) and should be surfaced as a band, not a point estimate — see §2.
- The LSTM has a small training set; predictions for programmes with low/volatile enrolment may be unstable.
- Prophet demand series is a proxy derived from student counts; replace with real job-posting data in production.
- No demographic fairness audit has been performed.

---

## Retraining

Re-run the four training scripts in order:

```bash
python ml/train_xgboost.py
python ml/train_salary_xgboost.py
python ml/train_lstm.py
python ml/train_prophet.py
python ml/generate_model_metrics.py   # refresh metrics JSON
```

Or run all of them in one step:

```bash
python ml/retrain_all.py
```
