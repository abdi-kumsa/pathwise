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
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    with open(FEATURE_PATH, 'rb') as f:
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


# ── Ethiopia OLS importance (M1 / M2) — after training, never a prior ─────────
# Model-based |coefficient| and permutation ΔRMSE on a chronological holdout.
# US LSTM / Prophet are not scored here.

_ETHIOPIA_IMPORTANCE = os.path.join(MODEL_DIR, "ethiopia_feature_importance.json")


def _permutation_delta(model, X_test, y_test, baseline_rmse, rng):
    """Increase in RMSE when each column is shuffled independently."""
    out = []
    y = np.asarray(y_test, dtype=float)
    for name in list(X_test.columns):
        shuffled = X_test.copy()
        shuffled[name] = rng.permutation(shuffled[name].to_numpy())
        pred = model.predict(shuffled)
        rmse = float(np.sqrt(np.mean((y - pred) ** 2)))
        out.append({
            "feature": name,
            "importance": round(max(rmse - baseline_rmse, 0.0), 6),
            "method": "permutation_importance",
        })
    out.sort(key=lambda r: r["importance"], reverse=True)
    return out


def _ols_holdout_importance(frame, ycol, feature_cols, group_keys):
    """Pooled OLS on a last-2-year chronological holdout of one Ethiopia panel."""
    work = frame.dropna(subset=[ycol, *feature_cols]).copy()
    if work.empty:
        return {"model_based": [], "permutation": []}
    hold_idx = []
    train_idx = []
    for _, series in work.groupby(group_keys, sort=False):
        if len(series) < 6:
            continue
        train_idx.extend(series.index[:-2].tolist())
        hold_idx.extend(series.index[-2:].tolist())
    if len(hold_idx) < 4 or len(train_idx) < 8:
        return {"model_based": [], "permutation": []}
    train = work.loc[train_idx]
    test = work.loc[hold_idx]
    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model.fit(train[feature_cols], train[ycol])
    pred = model.predict(test[feature_cols])
    y_test = test[ycol].to_numpy(dtype=float)
    baseline_rmse = float(np.sqrt(np.mean((y_test - pred) ** 2)))
    model_based = sorted(
        [
            {
                "feature": name,
                "importance": round(float(abs(coef)), 6),
                "method": "model_based_importance",
            }
            for name, coef in zip(feature_cols, model.coef_)
        ],
        key=lambda r: r["importance"],
        reverse=True,
    )
    rng = np.random.default_rng(42)
    permutation = _permutation_delta(
        model, test[feature_cols], y_test, baseline_rmse, rng,
    )
    return {
        "model_based": model_based,
        "permutation": permutation,
        "holdout_rmse": round(baseline_rmse, 4),
        "n_holdout": int(len(test)),
        "split": "chronological last-2-years per series",
    }


def ethiopia_feature_importance(persist: bool = True) -> dict:
    """Empirical importance for Ethiopia M1/M2 OLS estimators.

    Placement SHAP stays in compute_shap_values / explain_student. This function
    does not read collection-priority percentages.
    """
    from ml.features.model1.assemble import assemble_panel
    from ml.features.model2 import c1_labour

    m1_lags = (
        "enrollment_lag_1y",
        "enrollment_lag_2y",
        "enrollment_rolling_3y_avg",
        "applications_count",
    )
    m2_lags = ("employment_lag_1y", "employment_lag_2y")
    result = {
        "model1": {
            "target": "program_enrollment_count",
            **_ols_holdout_importance(
                assemble_panel(),
                "program_enrollment_count",
                list(m1_lags),
                ["institution", "campus", "program"],
            ),
        },
        "model2": {
            "target": "employment_level",
            **_ols_holdout_importance(
                c1_labour.frame(),
                "employment_level",
                list(m2_lags),
                ["region", "sector"],
            ),
        },
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
