"""
Model 5 — SHAP Explainability Tests (S1–S9)
Run from project root: python tests/test_shap.py
"""
import os
import sys
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split

ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR    = os.path.join(ROOT, 'ml', 'models')
MODEL_PATH   = os.path.join(MODEL_DIR, 'placement_xgboost.pkl')
FEATURE_PATH = os.path.join(MODEL_DIR, 'placement_feature_names.pkl')
PARQUET      = os.path.join(ROOT, 'data', 'processed', 'features.parquet')

sys.path.insert(0, os.path.join(ROOT, 'ml'))
from explain_predictions import compute_shap_values, explain_student

PASS   = "[PASS]"
FAIL   = "[FAIL]"
INFO   = "[INFO]"
MANUAL = "[MANUAL]"

results = []

def check(name, condition, detail=""):
    tag = PASS if condition else FAIL
    msg = f"  {tag}  {name}"
    if detail:
        msg += f"  |  {detail}"
    print(msg)
    results.append((name, condition))
    return condition


# ── Shared fixtures ───────────────────────────────────────────────────────────
print("\n" + "="*60)
print("Model 5 — SHAP Explainability")
print("="*60)
print("\n--- Automated Tests ---\n")

import shap

with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)
with open(FEATURE_PATH, 'rb') as f:
    feature_names = pickle.load(f)

df = pd.read_parquet(PARQUET)
X  = df[feature_names]
y  = df['placed']
_, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


# ── S1: SHAP values compute without error ────────────────────────────────────
try:
    shap_values, base_val, feat_names, X_sample = compute_shap_values(n_samples=200)
    s1_ok = True
except Exception as e:
    print(f"  {FAIL}  S1  compute_shap_values raised: {e}")
    sys.exit(1)

check("S1  SHAP values compute without error", s1_ok,
      f"shape={shap_values.shape}")


# ── S2: SHAP matrix shape is (200, 16) ───────────────────────────────────────
expected_shape = (200, len(feature_names))
check("S2  SHAP matrix shape is (200, n_features)",
      shap_values.shape == expected_shape,
      f"got {shap_values.shape}  expected {expected_shape}")


# ── S3: Additivity — base + sum(shap) ≈ model raw score (within 1e-2) ────────
# TreeExplainer SHAP values are in log-odds space for XGBoost classifiers.
# base_value + sum(shap_i) should equal the model's margin output per sample.
raw_scores  = model.get_booster().predict(
    xgb.DMatrix(X_sample, feature_names=feature_names), output_margin=True
)
shap_sums   = shap_values.sum(axis=1) + base_val
max_delta   = float(np.abs(raw_scores - shap_sums).max())
additive_ok = max_delta < 1e-2

check("S3  SHAP additivity: base + sum(shap) = model raw score (tol 1e-2)",
      additive_ok,
      f"max delta={max_delta:.2e}  across {len(X_sample)} samples")


# ── S4: gpa_scaled is in top-3 by mean |SHAP| ────────────────────────────────
mean_abs   = np.abs(shap_values).mean(axis=0)
ranked     = sorted(zip(feature_names, mean_abs), key=lambda x: x[1], reverse=True)
top3_names = [name for name, _ in ranked[:3]]

check("S4  gpa_scaled is in top-3 features by mean |SHAP|",
      'gpa_scaled' in top3_names,
      f"top-3: {top3_names}")


# ── S5: gpa_scaled SHAP direction — mean SHAP is positive ───────────────────
# With monotone constraint (GPA must help), mean gpa SHAP should be positive
# across the sample (students above the baseline GPA pull probability up).
gpa_idx      = list(feature_names).index('gpa_scaled')
mean_gpa_shap = float(shap_values[:, gpa_idx].mean())

check("S5  Mean SHAP of gpa_scaled is positive (higher GPA helps placement)",
      mean_gpa_shap > 0,
      f"mean SHAP gpa_scaled = {mean_gpa_shap:+.4f}")


# ── S6: Strong student probability > 85% via explain_student() ───────────────
strong = {
    'gpa': 3.9, 'internships': 4, 'projects': 8,
    'communication_score': 10, 'program': 'MS Data Science'
}
strong_result = explain_student(strong)
strong_prob   = strong_result['placement_prob']

check("S6  explain_student(): strong candidate probability > 85%",
      strong_prob > 0.85,
      f"prob={strong_prob*100:.1f}%")


# ── S7: Weak student — gpa_scaled and internships both have negative SHAP ─────
weak = {
    'gpa': 2.1, 'internships': 0, 'projects': 0,
    'communication_score': 2, 'program': 'Certificate Data Analytics'
}
weak_result = explain_student(weak)
weak_prob   = weak_result['placement_prob']

weak_contribs = {c['feature']: c['shap'] for c in weak_result['contributions']}
gpa_shap_weak     = weak_contribs.get('gpa_scaled', 0)
intern_shap_weak  = weak_contribs.get('internships', 0)
comm_shap_weak    = weak_contribs.get('communication_score_scaled', 0)

gpa_negative    = gpa_shap_weak < 0
intern_negative = intern_shap_weak <= 0
comm_negative   = comm_shap_weak < 0

check("S7a Weak student: gpa_scaled SHAP is negative",
      gpa_negative,
      f"gpa SHAP={gpa_shap_weak:+.4f}  prob={weak_prob*100:.1f}%")

check("S7b Weak student: internships SHAP is non-positive",
      intern_negative,
      f"internships SHAP={intern_shap_weak:+.4f}")

check("S7c Weak student: communication_score SHAP is negative",
      comm_negative,
      f"comm SHAP={comm_shap_weak:+.4f}")


# ── S8: All 16 features present in SHAP output ───────────────────────────────
n_features_shap = shap_values.shape[1]
n_features_model = len(feature_names)
check("S8  All 16 features have SHAP values (no missing columns)",
      n_features_shap == n_features_model,
      f"shap cols={n_features_shap}  expected={n_features_model}")


# ── Manual inspection ─────────────────────────────────────────────────────────
print(f"\n--- Manual Inspection ---\n")

print(f"  {MANUAL}  S9  Top-5 SHAP contributors — do explanations make intuitive sense?\n")

profiles = [
    ("Strong",  {'gpa': 3.9, 'internships': 4, 'projects': 8,  'communication_score': 10, 'program': 'MS Data Science'}),
    ("Average", {'gpa': 3.1, 'internships': 1, 'projects': 4,  'communication_score': 6,  'program': 'MS Computer Science'}),
    ("Weak",    {'gpa': 2.1, 'internships': 0, 'projects': 0,  'communication_score': 2,  'program': 'Certificate Data Analytics'}),
]

for label, prof in profiles:
    res = explain_student(prof)
    prob = res['placement_prob']
    base = res['base_value']
    print(f"  [{label}] GPA={prof['gpa']}  Int={prof['internships']}  "
          f"Comm={prof['communication_score']}  Program={prof['program']}")
    print(f"  Placement prob: {prob*100:.1f}%  |  Base value: {base}")
    print(f"  {'Feature':<36}  {'Raw value':>9}  {'SHAP':>8}  Direction")
    print(f"  {'-'*36}  {'-'*9}  {'-'*8}  {'-'*9}")
    for c in res['contributions'][:5]:
        arrow = "(+) helps" if c['shap'] > 0 else "(-) hurts"
        print(f"  {c['feature']:<36}  {c['value']:>9.3f}  {c['shap']:>+8.4f}  {arrow}")
    print()

print(f"  {INFO}  Global feature ranking by mean |SHAP| across 200 test samples:\n")
print(f"  {'Rank':<5}  {'Feature':<36}  {'Mean |SHAP|':>11}  {'Bar'}")
print(f"  {'-'*5}  {'-'*36}  {'-'*11}  {'-'*20}")
for rank, (feat, val) in enumerate(ranked, 1):
    bar = '|' * int(val / ranked[0][1] * 20)
    category = "individual" if feat in ('gpa_scaled','internships','projects',
                                        'communication_score_scaled') else "programme"
    print(f"  {rank:<5}  {feat:<36}  {val:>11.4f}  {bar}  [{category}]")

print(f"\n  {INFO}  SHAP base value (expected log-odds): {base_val:.4f}")
print(f"  {INFO}  Corresponds to base placement prob: "
      f"{1/(1+np.exp(-base_val))*100:.1f}%")


# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "="*60)
passed = sum(1 for _, ok in results if ok)
total  = len(results)
print(f"Result: {passed}/{total} automated tests passed")
if passed == total:
    print("  All automated checks PASSED.")
else:
    failed = [name for name, ok in results if not ok]
    print("  FAILED tests:")
    for f in failed:
        print(f"    - {f}")
print("="*60 + "\n")
