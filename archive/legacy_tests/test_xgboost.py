"""
Model 2 — XGBoost Placement Prediction Tests (X1–X12)
Run from project root: python tests/test_xgboost.py
"""
import os
import sys
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score

ROOT         = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH   = os.path.join(ROOT, 'ml', 'models', 'placement_xgboost.pkl')
FEATURE_PATH = os.path.join(ROOT, 'ml', 'models', 'placement_feature_names.pkl')
PARQUET      = os.path.join(ROOT, 'data', 'processed', 'features.parquet')

sys.path.insert(0, os.path.join(ROOT, 'ml'))
from predict_placement import predict_placement

PASS   = "[PASS]"
FAIL   = "[FAIL]"
INFO   = "[INFO]"
MANUAL = "[MANUAL]"

PROGRAMS = [
    'BS Computer Science', 'BS Data Science', 'Certificate Data Analytics',
    'MBA Product Management', 'MS Artificial Intelligence', 'MS Business Analytics',
    'MS Cloud Computing', 'MS Computer Science', 'MS Cybersecurity',
    'MS Data Science', 'MS Human-Computer Interaction', 'MS Information Technology',
]

results = []

def check(name, condition, detail=""):
    tag = PASS if condition else FAIL
    msg = f"  {tag}  {name}"
    if detail:
        msg += f"  |  {detail}"
    print(msg)
    results.append((name, condition))
    return condition


# ── Load shared fixtures once ─────────────────────────────────────────────────
print("\n" + "="*60)
print("Model 2 — XGBoost Placement Prediction")
print("="*60)
print("\n--- Automated Tests ---\n")

with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)
with open(FEATURE_PATH, 'rb') as f:
    feature_names = pickle.load(f)

df = pd.read_parquet(PARQUET)
X  = df[feature_names]
y  = df['placed']
_, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

y_pred       = model.predict(X_test)
y_proba      = model.predict_proba(X_test)[:, 1]


# ── X1: Model loads with correct type ────────────────────────────────────────
import xgboost as xgb
check("X1  Model file loads, correct type",
      isinstance(model, xgb.XGBClassifier),
      type(model).__name__)


# ── X2: Accuracy >= 85% ───────────────────────────────────────────────────────
acc = accuracy_score(y_test, y_pred)
check("X2  Accuracy >= 85% on test set",
      acc >= 0.85,
      f"{acc*100:.2f}%")


# ── X3: Precision >= 85% ──────────────────────────────────────────────────────
prec = precision_score(y_test, y_pred)
check("X3  Precision >= 85% on test set",
      prec >= 0.85,
      f"{prec*100:.2f}%")


# ── X4: Recall >= 90% ─────────────────────────────────────────────────────────
rec = recall_score(y_test, y_pred)
check("X4  Recall >= 90% on test set",
      rec >= 0.90,
      f"{rec*100:.2f}%")


# ── X5: All probabilities in [0, 1] ──────────────────────────────────────────
prob_ok = (y_proba >= 0.0).all() and (y_proba <= 1.0).all()
check("X5  All output probabilities in [0.0, 1.0]",
      prob_ok,
      f"min={y_proba.min():.4f}  max={y_proba.max():.4f}")


# ── X6: Strong candidate scores higher than weak ─────────────────────────────
strong = predict_placement({'gpa': 3.9, 'internships': 4, 'projects': 8,
                            'communication_score': 10, 'program': 'MS Data Science'})
weak   = predict_placement({'gpa': 2.1, 'internships': 0, 'projects': 0,
                            'communication_score': 2, 'program': 'Certificate Data Analytics'})
check("X6  Strong candidate probability > weak candidate",
      strong['placed_probability'] > weak['placed_probability'],
      f"strong={strong['placed_probability']:.4f}  weak={weak['placed_probability']:.4f}")


# ── X7: GPA monotonicity (increasing GPA -> non-decreasing probability) ───────
base = {'internships': 2, 'projects': 4, 'communication_score': 7,
        'program': 'MS Computer Science'}
gpa_steps   = [2.0, 2.5, 3.0, 3.5, 4.0]
gpa_probs   = [predict_placement({**base, 'gpa': g})['placed_probability']
               for g in gpa_steps]
# Allow one small dip (trees aren't strictly monotonic), majority must be non-decreasing
violations  = sum(1 for i in range(len(gpa_probs)-1) if gpa_probs[i] > gpa_probs[i+1] + 0.01)
check("X7  GPA monotonicity: prob rises as GPA increases (max 1 dip allowed)",
      violations <= 1,
      "  ".join(f"GPA{g}={p:.3f}" for g, p in zip(gpa_steps, gpa_probs)))


# ── X8: Internship monotonicity ───────────────────────────────────────────────
base2 = {'gpa': 3.2, 'projects': 4, 'communication_score': 7,
         'program': 'MS Computer Science'}
intern_steps = [0, 1, 2, 3, 4]
intern_probs = [predict_placement({**base2, 'internships': i})['placed_probability']
                for i in intern_steps]
violations2  = sum(1 for i in range(len(intern_probs)-1)
                   if intern_probs[i] > intern_probs[i+1] + 0.01)
check("X8  Internship monotonicity: prob rises with more internships (max 1 dip allowed)",
      violations2 <= 1,
      "  ".join(f"I{i}={p:.3f}" for i, p in zip(intern_steps, intern_probs)))


# ── X9: All 12 programs return valid predictions ─────────────────────────────
base3 = {'gpa': 3.0, 'internships': 1, 'projects': 3, 'communication_score': 6}
prog_results = {}
prog_errors  = []
for prog in PROGRAMS:
    try:
        r = predict_placement({**base3, 'program': prog})
        p = r['placed_probability']
        assert 0.0 <= p <= 1.0, f"probability out of range: {p}"
        prog_results[prog] = p
    except Exception as e:
        prog_errors.append(f"{prog}: {e}")

check("X9  All 12 programmes return valid predictions",
      len(prog_errors) == 0,
      f"{len(prog_results)}/12 OK" + (f"  ERRORS: {prog_errors}" if prog_errors else ""))


# ── X10: Deterministic — same input yields same output ───────────────────────
sample = {'gpa': 3.5, 'internships': 2, 'projects': 5,
          'communication_score': 8, 'program': 'MS Cybersecurity'}
run1 = predict_placement(sample)['placed_probability']
run2 = predict_placement(sample)['placed_probability']
run3 = predict_placement(sample)['placed_probability']
check("X10 Deterministic: 3 identical runs return same probability",
      run1 == run2 == run3,
      f"run1={run1:.6f}  run2={run2:.6f}  run3={run3:.6f}")


# ── X11: Feature importance sums to ~1.0 ─────────────────────────────────────
importance_sum = float(model.feature_importances_.sum())
check("X11 Feature importances sum to ~1.0",
      abs(importance_sum - 1.0) < 0.01,
      f"sum={importance_sum:.6f}")


# ── X12: Manual spot-check ───────────────────────────────────────────────────
print(f"\n--- Manual Inspection ---\n")

profiles = [
    ("Strong",  {'gpa': 3.9, 'internships': 4, 'projects': 8,  'communication_score': 10, 'program': 'MS Data Science'}),
    ("Average", {'gpa': 3.1, 'internships': 1, 'projects': 4,  'communication_score': 6,  'program': 'MS Computer Science'}),
    ("Weak",    {'gpa': 2.2, 'internships': 0, 'projects': 1,  'communication_score': 3,  'program': 'Certificate Data Analytics'}),
]

print(f"  {MANUAL}  X12  Three candidate profiles:\n")
print(f"  {'Profile':<10}  {'GPA':>4}  {'Int':>3}  {'Proj':>4}  {'Comm':>4}  {'Program':<32}  {'Prob':>6}  {'Class'}")
print(f"  {'-'*10}  {'-'*4}  {'-'*3}  {'-'*4}  {'-'*4}  {'-'*32}  {'-'*6}  {'-'*10}")
for label, prof in profiles:
    r = predict_placement(prof)
    print(f"  {label:<10}  {prof['gpa']:>4.1f}  {prof['internships']:>3}  "
          f"{prof['projects']:>4}  {prof['communication_score']:>4}  "
          f"{prof['program']:<32}  {r['placed_probability']:>5.1%}  {r['predicted_class']}")

print(f"\n  {INFO}  Per-programme probabilities (baseline student: GPA 3.0, 1 int, 3 proj, comm 6):")
print(f"\n  {'Programme':<36}  {'Probability':>11}  {'Class'}")
print(f"  {'-'*36}  {'-'*11}  {'-'*10}")
for prog, prob in sorted(prog_results.items(), key=lambda x: x[1], reverse=True):
    bar = '|' * int(prob * 20)
    print(f"  {prog:<36}  {prob:>10.1%}  {bar}")

print(f"\n  {INFO}  GPA sensitivity (internships=2, projects=4, comm=7, MS Computer Science):")
for g, p in zip(gpa_steps, gpa_probs):
    bar = '|' * int(p * 20)
    print(f"  GPA {g:.1f}  ->  {p:.1%}  {bar}")

print(f"\n  {INFO}  Internship sensitivity (GPA=3.2, projects=4, comm=7, MS Computer Science):")
for i, p in zip(intern_steps, intern_probs):
    bar = '|' * int(p * 20)
    print(f"  Internships {i}  ->  {p:.1%}  {bar}")


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
