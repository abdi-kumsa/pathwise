"""
Model 3 — LSTM Enrollment Forecasting Tests (L1–L9)
Run from project root: python tests/test_lstm.py
"""
import os
import sys
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'   # silence TF startup noise

ROOT        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR   = os.path.join(ROOT, 'ml', 'models')
MODEL_PATH  = os.path.join(MODEL_DIR, 'enrollment_lstm.keras')
SCALER_PATH = os.path.join(MODEL_DIR, 'enrollment_scaler.pkl')
META_PATH   = os.path.join(MODEL_DIR, 'enrollment_lstm_meta.pkl')
PARQUET     = os.path.join(ROOT, 'data', 'processed', 'features.parquet')

sys.path.insert(0, os.path.join(ROOT, 'ml'))
from predict_enrollment import predict_next_years, load_artifacts

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
print("Model 3 — LSTM Enrollment Forecasting")
print("="*60)
print("\n--- Automated Tests ---\n")

# ── L1: Model loads ───────────────────────────────────────────────────────────
try:
    from tensorflow.keras.models import load_model as keras_load
    keras_model = keras_load(MODEL_PATH)
    model_loaded = True
except Exception as e:
    print(f"  {FAIL}  L1  Model failed to load: {e}")
    sys.exit(1)

with open(SCALER_PATH, 'rb') as f:
    scalers = pickle.load(f)
with open(META_PATH, 'rb') as f:
    meta = pickle.load(f)

check("L1  Model file loads without error", model_loaded,
      type(keras_model).__name__)


# ── L2: All 12 programmes have a scaler ──────────────────────────────────────
n_scalers = len(scalers)
check("L2  All 12 programmes have a scaler",
      n_scalers == 12,
      f"found {n_scalers} scalers: {sorted(scalers.keys())[:3]} ...")


# ── L3: seq_len in meta matches model input shape ────────────────────────────
seq_len_meta  = meta['seq_len']
seq_len_model = keras_model.input_shape[1]   # (batch, seq_len, features)
check("L3  Meta seq_len matches model input dimension",
      seq_len_meta == seq_len_model,
      f"meta={seq_len_meta}  model.input_shape={keras_model.input_shape}")


# ── L4: RMSE on 2024 holdout < 15 students ───────────────────────────────────
df = pd.read_parquet(PARQUET)
prog_cols = [c for c in df.columns if c.startswith('prog_')]
df['program'] = df[prog_cols].idxmax(axis=1).str.replace('prog_', '', regex=False)

enrollment = (
    df.groupby(['program', 'enrollment_year'])
      .size().reset_index(name='count')
      .sort_values(['program', 'enrollment_year'])
)
years     = sorted(enrollment['enrollment_year'].unique())
SEQ_LEN   = meta['seq_len']
test_year = years[-1]
programs  = meta['programs']

rmse_list, mae_list = [], []
per_prog_eval = {}

for prog in programs:
    prog_data    = enrollment[enrollment['program'] == prog].sort_values('enrollment_year')
    counts       = prog_data['count'].values.astype(float)
    scaler       = scalers[prog]
    norm         = scaler.transform(counts.reshape(-1, 1)).flatten()

    X_all, y_all = [], []
    for i in range(len(norm) - SEQ_LEN):
        X_all.append(norm[i:i+SEQ_LEN])
        y_all.append(norm[i+SEQ_LEN])
    X_all = np.array(X_all, dtype=np.float32)
    y_all = np.array(y_all, dtype=np.float32)

    target_years = np.array(years[SEQ_LEN:])
    test_mask    = target_years == test_year
    if not test_mask.any():
        continue

    X_t = X_all[test_mask].reshape(-1, SEQ_LEN, 1)
    y_t = y_all[test_mask]

    y_pred_norm  = keras_model.predict(X_t, verbose=0).flatten()
    y_true_count = scaler.inverse_transform(y_t.reshape(-1, 1)).flatten()
    y_pred_count = scaler.inverse_transform(y_pred_norm.reshape(-1, 1)).flatten()

    rmse = float(np.sqrt(mean_squared_error(y_true_count, y_pred_count)))
    mae  = float(mean_absolute_error(y_true_count, y_pred_count))
    rmse_list.append(rmse)
    mae_list.append(mae)
    per_prog_eval[prog] = {
        'actual': round(float(y_true_count[0])),
        'pred':   round(float(y_pred_count[0])),
        'rmse':   round(rmse, 1),
        'mae':    round(mae, 1),
    }

overall_rmse = float(np.mean(rmse_list))
overall_mae  = float(np.mean(mae_list))
check("L4  Overall RMSE on held-out 2024 < 15 students",
      overall_rmse < 15,
      f"RMSE={overall_rmse:.2f}  MAE={overall_mae:.2f}")


# ── L5 & L6: All 2025 predictions positive and in plausible range ─────────────
forecasts_2yr = {}
errors_5 = []
errors_6 = []

for prog in programs:
    try:
        preds = predict_next_years(prog, n_years=2)
        forecasts_2yr[prog] = preds
        for p in preds:
            cnt = p['predicted_enrollment']
            if cnt <= 0:
                errors_5.append(f"{prog} {p['year']}: {cnt}")
            if not (10 <= cnt <= 200):
                errors_6.append(f"{prog} {p['year']}: {cnt}")
    except Exception as e:
        errors_5.append(f"{prog}: {e}")
        errors_6.append(f"{prog}: {e}")

check("L5  All 2025/2026 predicted counts are positive (> 0)",
      len(errors_5) == 0,
      "all OK" if not errors_5 else str(errors_5))

check("L6  All 2025/2026 counts in plausible range [10, 200]",
      len(errors_6) == 0,
      "all OK" if not errors_6 else str(errors_6))


# ── L7: 2025 and 2026 both return values for all programs ────────────────────
l7_ok = all(
    len(preds) == 2 and preds[0]['year'] == 2025 and preds[1]['year'] == 2026
    for preds in forecasts_2yr.values()
)
check("L7  Rolling forecast returns 2025 and 2026 for all 12 programmes",
      l7_ok and len(forecasts_2yr) == 12,
      f"{len(forecasts_2yr)}/12 programmes OK")


# ── L8: 5-year forecast doesn't explode (all counts < 500) ───────────────────
explode_errors = []
forecasts_5yr  = {}

for prog in programs:
    try:
        preds = predict_next_years(prog, n_years=5)
        forecasts_5yr[prog] = preds
        for p in preds:
            if p['predicted_enrollment'] >= 500:
                explode_errors.append(f"{prog} {p['year']}: {p['predicted_enrollment']}")
    except Exception as e:
        explode_errors.append(f"{prog}: {e}")

check("L8  5-year rolling forecast stays below 500 students (no explosion)",
      len(explode_errors) == 0,
      "all OK" if not explode_errors else str(explode_errors))


# ── Manual section ────────────────────────────────────────────────────────────
print(f"\n--- Manual Inspection ---\n")

print(f"  {MANUAL}  L9  Per-programme: 2024 actual vs model + 2025/2026 forecast\n")
print(f"  {'Programme':<36}  {'2024 act':>8}  {'2024 pred':>9}  {'RMSE':>5}  {'2025':>6}  {'2026':>6}  {'Trend'}")
print(f"  {'-'*36}  {'-'*8}  {'-'*9}  {'-'*5}  {'-'*6}  {'-'*6}  {'-'*7}")

for prog in sorted(programs):
    e   = per_prog_eval.get(prog, {})
    f2  = forecasts_2yr.get(prog, [{},{}])
    act = e.get('actual', '?')
    prd = e.get('pred', '?')
    rmse_v = e.get('rmse', '?')
    y25 = f2[0].get('predicted_enrollment', '?') if len(f2) > 0 else '?'
    y26 = f2[1].get('predicted_enrollment', '?') if len(f2) > 1 else '?'

    if isinstance(y26, int) and isinstance(y25, int):
        trend = "up" if y26 > y25 else ("dn" if y26 < y25 else "flat")
    else:
        trend = "?"

    print(f"  {prog:<36}  {act:>8}  {prd:>9}  {rmse_v:>5}  {y25:>6}  {y26:>6}  {trend:>7}")

print(f"\n  {INFO}  5-year rolling forecast (2025-2029) — check for drift/explosion:")
print(f"\n  {'Programme':<36}  {'2025':>6}  {'2026':>6}  {'2027':>6}  {'2028':>6}  {'2029':>6}")
print(f"  {'-'*36}  {'-'*6}  {'-'*6}  {'-'*6}  {'-'*6}  {'-'*6}")

for prog in sorted(programs):
    row = forecasts_5yr.get(prog, [])
    vals = [str(p.get('predicted_enrollment', '?')) for p in row]
    while len(vals) < 5:
        vals.append('?')
    print(f"  {prog:<36}  {'  '.join(f'{v:>6}' for v in vals)}")


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
