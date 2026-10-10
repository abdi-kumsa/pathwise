# Feature importance (DOC1 steps 5–6)

Empirical feature rankings are computed **after training**. They are reported
**separately** from DOC1’s data-collection priorities. The two must never be
combined into a single number or plotted as one series (W.ADM.04,
`never_merged: true`).

## Learned importance

| Model | Method | Source |
|---|---|---|
| Placement XGBoost | SHAP (`mean \|SHAP\|`) | `ml/explain_predictions.py` |
| M1 OLS-on-lags | model-based \|coefficient\| and permutation ΔRMSE | `ethiopia_feature_importance()` |
| M2 OLS-on-lags | model-based \|coefficient\| and permutation ΔRMSE | `ethiopia_feature_importance()` |

US LSTM / Prophet are not mixed into Ethiopia scores.

## Collection priority

The percentages in `docs/spec/model1_attributes.yaml` and
`docs/spec/model2_attributes.yaml` are **priorities for data collection**, not
model weights. `backend/spec_registry.py` exposes them as
`collection_priority()` — there is deliberately no `weight()` helper.

They appear only in the `collection_priority` panel of
`GET /api/methodology/feature-importance` and on the admin methodology page.
They do not appear under `ml/`.

## AHP

If fixed pre-training weights are required, DOC1 step 7 routes that through
`ml/ahp/` as a **separate** methodology. AHP ranks may be shown beside SHAP
ranks; they are never blended, and they never enter a learner’s loss or sample
weights. Consistency ratio above 0.1 is refused.

## How to read the API

```json
{
  "panels": ["learned_importance", "collection_priority"],
  "never_merged": true,
  "learned_importance": { "placement": {}, "model1": {}, "model2": {} },
  "collection_priority": [ { "id": "M1.C1", "collection_priority": 12 } ]
}
```

There is no blended score field.
