"""
Model 4 — Prophet Demand Forecasting Tests (P1–P8)
Run from project root: python tests/test_prophet.py
"""
import os
import sys
import pickle
import warnings
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error

warnings.filterwarnings('ignore')

ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR  = os.path.join(ROOT, 'ml', 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'demand_prophet.pkl')

sys.path.insert(0, os.path.join(ROOT, 'ml'))
from train_prophet import build_demand_series, evaluate
from predict_demand import predict_demand

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


# ── Load fixtures once ────────────────────────────────────────────────────────
print("\n" + "="*60)
print("Model 4 — Prophet Demand Forecasting")
print("="*60)
print("\n--- Automated Tests ---\n")

try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    model_loaded = True
except Exception as e:
    print(f"  {FAIL}  P1  Model failed to load: {e}")
    sys.exit(1)


# ── P1: Model loads ───────────────────────────────────────────────────────────
check("P1  Model file loads without error",
      model_loaded, type(model).__name__)


# ── Rebuild time series and generate forecast for evaluation ──────────────────
ts           = build_demand_series()
split_date   = ts['ds'].max() - pd.DateOffset(months=6)
test_df      = ts[ts['ds'] > split_date].copy()

future   = model.make_future_dataframe(periods=6, freq='MS')
forecast = model.predict(future)


# ── P2: MAPE < 10% on holdout ────────────────────────────────────────────────
metrics, eval_df = evaluate(forecast, test_df)
check("P2  MAPE on 6-month holdout < 10%",
      metrics['mape'] < 10,
      f"MAPE={metrics['mape']:.2f}%")


# ── P3: RMSE < 20 on holdout ─────────────────────────────────────────────────
check("P3  RMSE on 6-month holdout < 20",
      metrics['rmse'] < 20,
      f"RMSE={metrics['rmse']:.2f}  MAE={metrics['mae']:.2f}")


# ── P4: All 12-month forecast predictions are positive ───────────────────────
fc_12 = predict_demand(months_ahead=12)
neg_rows = fc_12[fc_12['predicted_postings'] <= 0]
check("P4  All 12-month forecast predictions are positive",
      len(neg_rows) == 0,
      f"min={fc_12['predicted_postings'].min()}  max={fc_12['predicted_postings'].max()}")


# ── P5: Confidence intervals are ordered (lower <= yhat <= upper) ─────────────
# Check both on the holdout forecast and on the 12-month raw forecast
raw_fc_12 = model.predict(
    model.make_future_dataframe(periods=12, freq='MS')
)
future_only = raw_fc_12[raw_fc_12['ds'] > model.history['ds'].max()]

ci_ok = (
    (future_only['yhat_lower'] <= future_only['yhat']).all() and
    (future_only['yhat']       <= future_only['yhat_upper']).all()
)
violations = int((future_only['yhat_lower'] > future_only['yhat']).sum() +
                 (future_only['yhat'] > future_only['yhat_upper']).sum())
check("P5  Confidence intervals ordered (lower <= yhat <= upper) in all 12 months",
      ci_ok,
      f"violations={violations}")


# ── P6: Seasonality — August predicted postings > June ───────────────────────
# Use a 24-month forecast so we get a full Jan-Dec 2025 cycle
raw_fc_24 = model.predict(
    model.make_future_dataframe(periods=24, freq='MS')
)
future_24 = raw_fc_24[raw_fc_24['ds'] > model.history['ds'].max()].copy()
future_24['month_num'] = future_24['ds'].dt.month

aug_postings  = future_24[future_24['month_num'] == 8]['yhat'].mean()
jun_postings  = future_24[future_24['month_num'] == 6]['yhat'].mean()
mar_postings  = future_24[future_24['month_num'] == 3]['yhat'].mean()

check("P6  Seasonality captured: August forecast > June forecast",
      aug_postings > jun_postings,
      f"Aug={aug_postings:.1f}  Jun={jun_postings:.1f}  Mar={mar_postings:.1f}")


# ── P7: 12-month annual total in plausible range (800–2000) ──────────────────
annual_total = int(fc_12['predicted_postings'].sum())
check("P7  12-month forecast total between 800 and 2,000 postings",
      800 <= annual_total <= 2000,
      f"total={annual_total:,}")


# ── Manual inspection ─────────────────────────────────────────────────────────
print(f"\n--- Manual Inspection ---\n")

print(f"  {MANUAL}  P8  Seasonal curve — do peaks appear in Jan-Mar and Aug-Sep?\n")

# Monthly averages across the full training history
history_df = model.history.copy()
history_df['month_num'] = history_df['ds'].dt.month
monthly_avg = history_df.groupby('month_num')['y'].mean()

MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun',
               'Jul','Aug','Sep','Oct','Nov','Dec']

print(f"  {'Month':<5}  {'Hist avg':>8}  {'Forecast':>9}  {'Bar'}")
print(f"  {'-'*5}  {'-'*8}  {'-'*9}  {'-'*20}")

future_24['month_num'] = future_24['ds'].dt.month
fc_monthly = future_24.groupby('month_num')['yhat'].mean()

max_val = max(monthly_avg.max(), fc_monthly.max())
for m in range(1, 13):
    hist_v = monthly_avg.get(m, 0)
    fc_v   = fc_monthly.get(m, 0)
    bar    = '|' * int(fc_v / max_val * 25)
    peak   = " <-- peak" if m in (1, 2, 3, 8, 9) else ""
    print(f"  {MONTH_NAMES[m-1]:<5}  {hist_v:>8.1f}  {fc_v:>9.1f}  {bar}{peak}")

print(f"\n  {INFO}  6-month holdout: actual vs predicted\n")
print(f"  {'Month':<12}  {'Actual':>6}  {'Forecast':>8}  {'Lower':>6}  {'Upper':>6}  {'Error%':>7}")
print(f"  {'-'*12}  {'-'*6}  {'-'*8}  {'-'*6}  {'-'*6}  {'-'*7}")
for _, row in eval_df.iterrows():
    err_pct = abs(row['y'] - row['yhat']) / row['y'] * 100 if row['y'] != 0 else 0
    flag = " *" if err_pct > 10 else ""
    print(f"  {str(row['ds'].date()):<12}  {int(row['y']):>6}  {row['yhat']:>8.1f}  "
          f"{row['yhat_lower']:>6.0f}  {row['yhat_upper']:>6.0f}  {err_pct:>6.1f}%{flag}")

print(f"\n  {INFO}  12-month demand forecast (full output):\n")
print(f"  {'Month':<12}  {'Predicted':>9}  {'Lower':>6}  {'Upper':>6}")
print(f"  {'-'*12}  {'-'*9}  {'-'*6}  {'-'*6}")
for _, row in fc_12.iterrows():
    print(f"  {str(row['month'].date()):<12}  {row['predicted_postings']:>9,}  "
          f"{row['lower_bound']:>6,}  {row['upper_bound']:>6,}")
print(f"\n  Annual total: {annual_total:,} predicted postings")


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
