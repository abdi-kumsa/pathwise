"""
Model 1 — Feature Engineering Pipeline Tests (F1–F9)
Run from project root: python tests/test_feature_pipeline.py
"""
import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# ── Resolve project root ──────────────────────────────────────────────────────
ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET = os.path.join(ROOT, 'data', 'processed', 'features.parquet')

PASS  = "[PASS]"
FAIL  = "[FAIL]"
INFO  = "[INFO]"
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


# ── Load once ─────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("Model 1 — Feature Engineering Pipeline")
print("="*60)

try:
    df = pd.read_parquet(PARQUET)
    load_ok = True
except Exception as e:
    print(f"  {FAIL}  Could not load parquet: {e}")
    sys.exit(1)

PROG_COLS = [c for c in df.columns if c.startswith('prog_')]
FEATURE_COLS = ['gpa', 'gpa_scaled', 'internships', 'projects',
                'communication_score', 'communication_score_scaled']


# ── Automated tests ───────────────────────────────────────────────────────────
print("\n--- Automated Tests ---\n")

# F1: parquet loads
check("F1  Parquet loads without error", load_ok)

# F2: shape
expected_rows, expected_cols = 3000, 24
actual_rows, actual_cols = df.shape
check("F2  Shape is 3,000 rows × 24 cols",
      actual_rows == expected_rows and actual_cols == expected_cols,
      f"got ({actual_rows} x {actual_cols})")

# F3: no nulls in core feature columns
null_counts = df[FEATURE_COLS].isnull().sum()
has_nulls = (null_counts > 0).any()
check("F3  No nulls in core feature columns",
      not has_nulls,
      "null counts: " + null_counts[null_counts > 0].to_dict().__str__() if has_nulls else "all clean")

# F4: gpa_scaled bounded [0, 1]
gpa_min = df['gpa_scaled'].min()
gpa_max = df['gpa_scaled'].max()
check("F4  gpa_scaled bounded in [0.0, 1.0]",
      gpa_min >= 0.0 and gpa_max <= 1.0,
      f"range: [{gpa_min:.4f}, {gpa_max:.4f}]")

# F5: communication_score_scaled bounded [0, 1]
cs_min = df['communication_score_scaled'].min()
cs_max = df['communication_score_scaled'].max()
check("F5  communication_score_scaled bounded in [0.0, 1.0]",
      cs_min >= 0.0 and cs_max <= 1.0,
      f"range: [{cs_min:.4f}, {cs_max:.4f}]")

# F6: program one-hots are mutually exclusive (each row sums to exactly 1)
row_sums = df[PROG_COLS].sum(axis=1)
all_ones = (row_sums == 1).all()
check("F6  Programme one-hots are mutually exclusive (row sum = 1)",
      all_ones,
      f"unique row sums: {sorted(row_sums.unique().tolist())}")

# F7: enrollment_year range 2019–2024 only
years = sorted(df['enrollment_year'].unique())
expected_years = [2019, 2020, 2021, 2022, 2023, 2024]
check("F7  enrollment_year only contains 2019–2024",
      years == expected_years,
      f"got: {years}")

# F9: stratified split preserves placement rate (delta < 1%)
X = df.drop(columns=['placed'])
y = df['placed']
_, _, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
train_rate = y_train.mean()
test_rate  = y_test.mean()
delta      = abs(train_rate - test_rate)
check("F9  Stratified split: placement rate delta < 1%",
      delta < 0.01,
      f"train={train_rate:.4f}  test={test_rate:.4f}  delta={delta:.4f}")


# ── Manual inspection section ─────────────────────────────────────────────────
print("\n--- Manual Inspection ---\n")

placement_rate = df['placed'].mean()
print(f"  {MANUAL}  F8  Placement rate: {placement_rate*100:.2f}%")
print(f"           Expected range: 80–95%")
print(f"           -> {'LOOKS OK' if 0.80 <= placement_rate <= 0.95 else 'OUT OF RANGE'}")

print()
print(f"  {INFO}  Programme distribution (one-hot counts):")
prog_counts = df[PROG_COLS].sum().sort_values(ascending=False)
for col, cnt in prog_counts.items():
    name = col.replace('prog_', '')
    bar  = '|' * int(cnt / prog_counts.max() * 20)
    print(f"           {name:<36}  {cnt:4d}  {bar}")

print()
print(f"  {INFO}  Enrollment year distribution:")
year_counts = df['enrollment_year'].value_counts().sort_index()
for yr, cnt in year_counts.items():
    bar = '|' * int(cnt / year_counts.max() * 20)
    print(f"           {yr}  {cnt:4d}  {bar}")

print()
print(f"  {INFO}  Scaled feature distributions:")
print(f"           gpa_scaled              mean={df['gpa_scaled'].mean():.3f}  std={df['gpa_scaled'].std():.3f}")
print(f"           comm_score_scaled       mean={df['communication_score_scaled'].mean():.3f}  std={df['communication_score_scaled'].std():.3f}")
print(f"           internships             mean={df['internships'].mean():.2f}   min={df['internships'].min()}  max={df['internships'].max()}")
print(f"           projects                mean={df['projects'].mean():.2f}   min={df['projects'].min()}  max={df['projects'].max()}")


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
