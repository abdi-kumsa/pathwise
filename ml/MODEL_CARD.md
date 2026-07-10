# PathWise ML Model Card

## Overview

Three models power the PathWise intelligence dashboards.  All are trained on
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

## 2. LSTM — Enrollment Forecasting

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

## 3. Prophet — Job-Market Demand Forecasting

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
- The LSTM has a small training set; predictions for programmes with low/volatile enrolment may be unstable.
- Prophet demand series is a proxy derived from student counts; replace with real job-posting data in production.
- No demographic fairness audit has been performed.

---

## Retraining

Re-run the three training scripts in order:

```bash
python ml/train_xgboost.py
python ml/train_lstm.py
python ml/train_prophet.py
python ml/generate_model_metrics.py   # refresh metrics JSON
```
