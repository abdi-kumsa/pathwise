# Model comparison (DOC1 step 4)

PathWise compares **Ethiopia** estimators on a **grouped chronological holdout**
(the last two observed years of each series). A random train/test split is not
used. Each target has at least three named candidates, including a seasonal-naive
baseline, so any gain is measured against something.

The facade is `ml/compare_models.py`. It calls `ml/model1/compare.py` and
`ml/model2/compare.py`; it does not train a third Ethiopia learner.

## Candidates

| Target | Candidates | Split |
|---|---|---|
| M1 `program_enrollment_count` | `seasonal_naive`, `historical_mean`, `ols_lags` | last two years per HEI × campus × programme |
| M2 `employment_level` | `seasonal_naive`, `historical_mean`, `ols_lags` | last two years per region × sector |
| M2 `employment_growth_pct` | `seasonal_naive`, `historical_mean`, `ols_lags` | last two years per region × sector |
| M2 `vacancy_count` | `seasonal_naive`, `historical_mean`, `ols_lags` | last two years per region × occupation |
| M2 `occupational_demand` | `seasonal_naive`, `historical_mean`, `ols_lags` | vacancy × occupation share of the region's vacancy mix — not a copy of the vacancy point |
| M2 `skill_shortage_index` | `seasonal_naive`, `historical_mean`, `ols_lags` | last two years per field |

`employment_growth_pct` is derived from the employment series. It is still
scored so PROC.S4 is not silently one-target.

The request path still selects `ols_lags` when a series has four or more history
years, otherwise `seasonal_naive`. `historical_mean` is a comparison baseline
only.

Ethiopia OLS is not explained with SHAP. Learned importance for M1/M2 is
coefficient and permutation on the lag columns actually used. Other DOC1
columns are listed as `unused_by_learner`. Placement SHAP remains a leftover
US artefact.

## What is not compared

US artefacts remain on the old enrollment / labour-demand path and are **not**
scored as Ethiopia models:

- `ml/models/enrollment_lstm.keras`
- `ml/models/demand_prophet.pkl`

They appear in API payloads under `us_models_not_compared` / `not_compared`.

Holdout RMSE on generated lags can be near-zero (WV.OLS1). That is not
ministry-grade accuracy.

## How to run

```text
python -m ml.compare_models
```

Scores are written to `ml/models/ethiopia_comparison.json` and
`ml/models/model2_comparison.json`, and served at
`GET /api/methodology/model-comparison` (ADMIN).
