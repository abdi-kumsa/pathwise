# Methodology (DOC1)

DOC1’s recommended procedure is a deliverable, not a preamble. The executable
transcription is `docs/spec/methodology.yaml`. This note is the human reading
of the same seven steps.

Governing sentence (DOC1 line 234): the published percentages are **priorities
for data collection, feature engineering and model design** — not fixed weights
to impose on a learner. The registry field is named `collection_priority`.
Nothing under `ml/` reads it as a training weight.

---

## Step 1 — Define candidate attributes

**Yaml:** `docs/spec/model1_attributes.yaml`, `docs/spec/model2_attributes.yaml`

Twenty categories (ten per model) and every named variable. That registry *is*
the candidate list. Coverage is asserted by `tests/test_spec_coverage.py`.

## Step 2 — Expert validation

**Table:** `expert_validations`  
**Endpoint:** `GET /api/methodology/expert-validations`  
**Page:** admin Methodology

Six named domains: higher education, MoE, labour and skills, statistics,
economics, sector specialist.

## Step 3 — Prioritise Tier 1 and Tier 2 for collection

**Endpoint:** `GET /api/methodology/priority-tiers`  
**Report:** `python scripts/spec_report.py`

Combined collection-priority shares: Model 1 70 / 18 / 12, Model 2 55 / 30 / 15.
These numbers never enter a loss function.

## Step 4 — Train multiple models and compare

**Facade:** `ml/compare_models.py`  
**Report:** [MODEL_COMPARISON.md](MODEL_COMPARISON.md)  
**Endpoint:** `GET /api/methodology/model-comparison`

Rolling-origin backtest: from every origin year from 2019, each candidate
forecasts 1–5 years ahead using only data up to the origin. No random split.
Four candidates per target, two of them naive baselines:

| Target | Candidates |
|---|---|
| M1 applications (unconstrained demand) | `seasonal_naive`, `historical_mean`, `drift`, `pooled_ridge` |
| M2 employment, vacancies, skill-shortage index | same four |

The request path uses the lowest-RMSE candidate at each horizon and records it
on every row. Intervals come from that candidate's backtest residuals, with
coverage measured leave-one-origin-out. Engine: `ml/forecasting.py`. US LSTM
and Prophet are **not-compared**.

## Step 5 — Empirical importance after training

**Artefact:** `ml/explain_predictions.py`  
**Report:** [FEATURE_IMPORTANCE.md](FEATURE_IMPORTANCE.md)  
**Endpoint:** `GET /api/methodology/feature-importance`

Methods: model-based importance, SHAP, permutation. Importance is computed from
fitted models, never asserted in advance.

## Step 6 — Two panels, never one number

Learned importance and collection priority appear in **separate labelled
panels** on the admin methodology page. No endpoint returns a blend. No chart
plots them as one series. Enforced by
`tests/test_spec_coverage.py::test_learned_and_priority_never_merged`.

## Step 7 — AHP only if fixed pre-training weights are required

**Module:** `ml/ahp/`  
**Endpoints:** `POST /api/ahp/weights`, `POST /api/ahp/consistency`

Saaty pairwise matrix → principal eigenvector → consistency ratio. **CR > 0.1
refuses the weights** (`422`, `weights: null`) rather than returning a number
that looks fine. AHP is structurally separate from training. It is displayed
beside SHAP, never blended into it. Enforced by `tests/test_ahp.py`.

---

## Ranking honesty (RANK.R1–R4)

These are client decisions that bind DOC2 “ranked” widgets:

| Id | Rule |
|---|---|
| RANK.R1 | Graduate fit classification enters no ranking. |
| RANK.R2 | Rank on supply–demand gap, labour demand, capacity, eligibility. |
| RANK.R3 | Every composite returns `weights`, `method`, and per-factor rows. |
| RANK.R4 | Severity buckets are quartiles of \|gap\|, not fixed coverage cuts. |

Live checks: `tests/test_honesty_live.py`, `tests/test_spec_coverage.py` honesty
marks.

---

## Pointers

- Compare facade: `ml/compare_models.py`
- SHAP / permutation: `docs/FEATURE_IMPORTANCE.md`
- Two-panel UI: `frontend/src/pages/admin/AdminMethodologyPage.jsx`
- AHP CR gate: `ml/ahp/`, `tests/test_ahp.py`
- Model cards: [ml/MODEL_CARD.md](../ml/MODEL_CARD.md)
