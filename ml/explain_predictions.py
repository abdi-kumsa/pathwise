"""
Tasks 14-15: SHAP Explainability for XGBoost placement model
- Task 14: Generate SHAP values
- Task 15: Provide explain_student() API for individual predictions
Usage:
    python ml/explain_predictions.py
"""
import json
import os
import pickle
import numpy as np
import pandas as pd
try:
    from artifacts import verified_open, verify  # noqa: F401  (ml/ on sys.path)
except ImportError:  # imported as part of the ml package
    from ml.artifacts import verified_open, verify  # noqa: F401

# ── Paths ─────────────────────────────────────────────────────────────────────

def _project_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


ROOT         = _project_root()
PARQUET      = os.path.join(ROOT, 'data', 'processed', 'features.parquet')
MODEL_DIR    = os.path.join(ROOT, 'ml', 'models')
MODEL_PATH   = os.path.join(MODEL_DIR, 'placement_xgboost.pkl')
FEATURE_PATH = os.path.join(MODEL_DIR, 'placement_feature_names.pkl')


def _load_model_and_features():
    with verified_open(MODEL_PATH) as f:
        model = pickle.load(f)
    with verified_open(FEATURE_PATH) as f:
        feature_names = pickle.load(f)
    return model, feature_names


def _load_test_set(feature_names):
    from sklearn.model_selection import train_test_split
    df = pd.read_parquet(PARQUET)
    X  = df[feature_names]
    y  = df['placed']
    _, X_test, _, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    return X_test


# ── Task 14: Generate SHAP values ─────────────────────────────────────────────

def compute_shap_values(n_samples: int = 200):
    """
    Compute SHAP values for a random sample of the test set.
    Returns shap_values array, expected_value, feature_names, X_sample DataFrame.
    """
    import shap

    model, feature_names = _load_model_and_features()
    X_test = _load_test_set(feature_names)

    # Sample for speed (SHAP on XGBoost is fast, but keep it light)
    X_sample = X_test.sample(n=min(n_samples, len(X_test)), random_state=42)

    explainer   = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)   # shape: (n_samples, n_features)

    return shap_values, explainer.expected_value, feature_names, X_sample


# ── Task 15: Per-student explanation ─────────────────────────────────────────

def explain_student(student: dict) -> dict:
    """
    Return SHAP feature contributions for a single student dict.
    Keys must match feature_names (see predict_placement.py for format).
    Returns:
        {
            'placement_prob': float,
            'base_value': float,
            'contributions': [{'feature': str, 'value': float, 'shap': float}, ...]
        }
    """
    import shap

    model, feature_names = _load_model_and_features()

    # Build feature vector (same manual scaling as predict_placement.py)
    gpa_scaled  = (student.get('gpa', 3.0) - 2.0) / (4.0 - 2.0)
    comm_scaled = (student.get('communication_score', 5) - 1) / (10 - 1)

    prog_cols = {col: 0 for col in feature_names if col.startswith('prog_')}
    prog_key  = 'prog_' + student.get('program', '')
    if prog_key in prog_cols:
        prog_cols[prog_key] = 1

    row = {
        'gpa_scaled':                gpa_scaled,
        'internships':               student.get('internships', 0),
        'projects':                  student.get('projects', 0),
        'communication_score_scaled': comm_scaled,
        **prog_cols,
    }
    X = pd.DataFrame([row])[feature_names]

    explainer   = shap.TreeExplainer(model)
    shap_vals   = explainer.shap_values(X)[0]          # (n_features,)
    prob        = float(model.predict_proba(X)[0, 1])

    contributions = sorted(
        [{'feature': f, 'value': float(X[f].iloc[0]), 'shap': round(float(s), 4)}
         for f, s in zip(feature_names, shap_vals)],
        key=lambda x: abs(x['shap']),
        reverse=True,
    )

    return {
        'placement_prob':  round(prob, 4),
        'base_value':      round(float(explainer.expected_value), 4),
        'contributions':   contributions,
    }


# ── Ethiopia importance (M1 / M2) — after training, never a prior ────────────
# Computed on the pooled model the request path actually uses (ml/forecasting),
# trained on target years up to HOLDOUT_FROM - 1 and explained on later years.
# Three methods, all post-training (PROC.S5):
#   model_based  |standardised coefficient|  (coefficient × feature std)
#   shap         mean |coef × (x − mean x)|  — exact SHAP for a linear model
#   permutation  RMSE increase on the holdout when one feature is shuffled
# US LSTM / Prophet are not scored here.

_ETHIOPIA_IMPORTANCE = os.path.join(MODEL_DIR, "ethiopia_feature_importance.json")
HOLDOUT_FROM = 2023


def _pooled_importance(target_id: str) -> dict:
    from sklearn.linear_model import Ridge

    from ml.forecasting import FEATURE_NAMES, TARGETS, pooled_pairs

    pairs = pooled_pairs(target_id, horizon=1)
    if pairs.empty:
        return {"model_based": [], "shap": [], "permutation": []}
    feats = list(FEATURE_NAMES)
    train = pairs[pairs["target_year"] < HOLDOUT_FROM]
    test = pairs[pairs["target_year"] >= HOLDOUT_FROM]
    if len(train) < 20 or len(test) < 10:
        return {"model_based": [], "shap": [], "permutation": []}
    model = Ridge(alpha=1.0).fit(train[feats], train["change"])
    pred = model.predict(test[feats])
    y = test["change"].to_numpy(dtype=float)
    rmse = float(np.sqrt(np.mean((y - pred) ** 2)))
    naive_rmse = float(np.sqrt(np.mean(y ** 2)))       # "no change" baseline
    std = train[feats].std().to_numpy()
    mean = train[feats].mean().to_numpy()

    def ranked(values, method):
        return sorted(
            [{"feature": f, "importance": round(float(v), 6), "method": method}
             for f, v in zip(feats, values)],
            key=lambda r: r["importance"], reverse=True,
        )

    shap_vals = np.abs((test[feats].to_numpy() - mean) * model.coef_).mean(axis=0)
    rng = np.random.default_rng(42)
    perm = []
    for f in feats:
        shuffled = test[feats].copy()
        shuffled[f] = rng.permutation(shuffled[f].to_numpy())
        r = float(np.sqrt(np.mean((y - model.predict(shuffled)) ** 2)))
        perm.append(max(r - rmse, 0.0))
    t = TARGETS[target_id]
    return {
        "target": t.ycol,
        "target_id": target_id,
        "model": "pooled_ridge (horizon 1)",
        "scale": "log change" if t.log else "change",
        "coefficients": {f: round(float(c), 6) for f, c in zip(feats, model.coef_)},
        "intercept": round(float(model.intercept_), 6),
        "model_based": ranked(np.abs(model.coef_) * std, "model_based_importance"),
        "shap": ranked(shap_vals, "shap_linear_exact"),
        "permutation": ranked(perm, "permutation_importance"),
        "holdout_rmse": round(rmse, 6),
        "holdout_rmse_no_change": round(naive_rmse, 6),
        "n_train": int(len(train)),
        "n_holdout": int(len(test)),
        "split": f"train on target years < {HOLDOUT_FROM}, explain on {HOLDOUT_FROM} onwards",
        "features_from": (
            "the target's own history: latest_change = last value − previous value; "
            "distance_from_series_mean = last value − the series' mean so far"
        ),
    }


def ethiopia_feature_importance(persist: bool = True) -> dict:
    """Empirical importance for the Ethiopia M1/M2 pooled estimators.

    Placement SHAP stays in compute_shap_values / explain_student. This function
    does not read collection-priority percentages.
    """
    result = {
        "model1": _pooled_importance("M1.applications"),
        "model2": _pooled_importance("M2.employment_demand"),
        "not_compared": [
            "US LSTM (ml/models/enrollment_lstm.keras)",
            "US Prophet (ml/models/demand_prophet.pkl)",
        ],
    }
    if persist:
        os.makedirs(MODEL_DIR, exist_ok=True)
        with open(_ETHIOPIA_IMPORTANCE, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
    return result


def placement_mean_abs_shap(n_samples: int = 200):
    """Global mean |SHAP| ranking for the placement XGBoost model."""
    shap_values, base_val, feature_names, _X = compute_shap_values(n_samples=n_samples)
    mean_abs = np.abs(shap_values).mean(axis=0)
    ranked = sorted(
        zip(feature_names, mean_abs),
        key=lambda x: x[1],
        reverse=True,
    )
    return {
        "method": "shap",
        "base_value": round(float(np.mean(np.atleast_1d(base_val))), 4),
        "rows": [
            {"feature": name, "importance": round(float(val), 6), "method": "shap"}
            for name, val in ranked
        ],
    }


def load_cached_ethiopia_importance() -> dict | None:
    if not os.path.exists(_ETHIOPIA_IMPORTANCE):
        return None
    with open(_ETHIOPIA_IMPORTANCE, encoding="utf-8") as fh:
        return json.load(fh)


# ── Summary printer ───────────────────────────────────────────────────────────

def print_global_summary(shap_values, feature_names, top_n=10):
    mean_abs = np.abs(shap_values).mean(axis=0)
    ranked   = sorted(zip(feature_names, mean_abs), key=lambda x: x[1], reverse=True)
    print(f"\n  Top {top_n} features by mean |SHAP|:")
    for rank, (feat, val) in enumerate(ranked[:top_n], 1):
        bar = '#' * int(val / ranked[0][1] * 20)
        print(f"    {rank:2}. {feat:<36}  {val:.4f}  {bar}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 56)
    print("PathWise — SHAP Explainability")
    print("=" * 56)

    # Task 14
    print("\n[Task 14] Computing SHAP values on 200-sample test set ...")
    shap_values, base_val, feature_names, X_sample = compute_shap_values(n_samples=200)
    print(f"  SHAP matrix shape: {shap_values.shape}")
    print(f"  Base (expected) value: {base_val:.4f}")
    print_global_summary(shap_values, feature_names)

    # Task 15
    print("\n[Task 15] Per-student explanation demo ...")
    strong_student = {
        'gpa': 3.8,
        'internships': 3,
        'projects': 7,
        'communication_score': 9,
        'program': 'MS Data Science',
    }
    result = explain_student(strong_student)
    print(f"\n  Student: GPA={strong_student['gpa']}, "
          f"Internships={strong_student['internships']}, "
          f"Program={strong_student['program']}")
    print(f"  Placement probability: {result['placement_prob']*100:.1f}%")
    print(f"  Base value: {result['base_value']}")
    print("  Top 5 feature contributions:")
    for c in result['contributions'][:5]:
        direction = '+' if c['shap'] > 0 else '-'
        print(f"    {direction} {c['feature']:<36}  SHAP={c['shap']:+.4f}")

    print("\n[DONE] SHAP explainability complete.")
