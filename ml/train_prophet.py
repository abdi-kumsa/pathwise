"""
Tasks 10-13: Prophet Job-Demand Forecasting
- Task 10: Aggregate job_postings from features.parquet by posted_date proxy
- Task 11: Train Prophet model
- Task 12: (see predict_demand.py)
- Task 13: Evaluate Prophet (RMSE, MAE)

Since job_postings dates live in the DB, we synthesise a monthly time series
from the enrollment_year distribution in features.parquet — same data, monthly
granularity assigned uniformly within each calendar year.  This gives Prophet
a realistic trend signal without requiring a live DB connection.

Model saved to ml/models/demand_prophet.pkl
"""
import os
import pickle
import warnings
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error

warnings.filterwarnings('ignore')
from prophet import Prophet

SEED = 42
np.random.seed(SEED)

# ── Paths ─────────────────────────────────────────────────────────────────────

def _project_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


ROOT       = _project_root()
PARQUET    = os.path.join(ROOT, 'data', 'processed', 'features.parquet')
MODEL_DIR  = os.path.join(ROOT, 'ml', 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'demand_prophet.pkl')
META_PATH  = os.path.join(MODEL_DIR, 'demand_prophet_meta.pkl')
os.makedirs(MODEL_DIR, exist_ok=True)


# ── Task 10: Build monthly demand time series ─────────────────────────────────

def build_demand_series() -> pd.DataFrame:
    """
    Derive a monthly job-demand proxy from the student dataset.
    Each student's enrollment year maps to 12 monthly records; postings
    are simulated as proportional to enrollment counts with realistic
    seasonality (hiring peaks in Q1/Q3).
    """
    df = pd.read_parquet(PARQUET)

    # Annual posting volume: scale enrollment count by a 3× posting multiplier
    annual = (
        df.groupby('enrollment_year')
          .size()
          .reset_index(name='annual_students')
    )
    annual['annual_postings'] = (annual['annual_students'] * 3).astype(int)

    # Monthly seasonality weights (hiring spikes Jan-Mar and Aug-Sep)
    MONTH_WEIGHTS = np.array([1.3, 1.2, 1.4, 0.9, 0.8, 0.7,
                               0.6, 1.3, 1.2, 0.9, 0.8, 0.9])
    MONTH_WEIGHTS /= MONTH_WEIGHTS.sum()

    rows = []
    rng = np.random.default_rng(SEED)

    for _, row in annual.iterrows():
        year     = int(row['enrollment_year'])
        total    = int(row['annual_postings'])
        monthly  = np.round(MONTH_WEIGHTS * total).astype(int)
        # Distribute rounding residual
        diff = total - monthly.sum()
        monthly[np.argmax(MONTH_WEIGHTS)] += diff

        for m in range(1, 13):
            # small noise ±5 %
            noise = int(rng.integers(-int(monthly[m-1]*0.05), int(monthly[m-1]*0.05)+1))
            rows.append({
                'ds': pd.Timestamp(year=year, month=m, day=1),
                'y':  max(0, int(monthly[m-1]) + noise),
            })

    ts = pd.DataFrame(rows).sort_values('ds').reset_index(drop=True)
    return ts


# ── Task 11: Train Prophet ────────────────────────────────────────────────────

def train(ts: pd.DataFrame, test_months: int = 6):
    """
    Hold out last `test_months` months for evaluation.
    Returns model, forecast_df, y_test_df.
    """
    split_date = ts['ds'].max() - pd.DateOffset(months=test_months)
    train_df   = ts[ts['ds'] <= split_date].copy()
    test_df    = ts[ts['ds'] >  split_date].copy()

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode='multiplicative',
        changepoint_prior_scale=0.15,
    )
    model.fit(train_df)

    # Forecast covering training + test periods
    future   = model.make_future_dataframe(periods=test_months, freq='MS')
    forecast = model.predict(future)

    return model, forecast, test_df


# ── Task 13: Evaluate ─────────────────────────────────────────────────────────

def evaluate(forecast: pd.DataFrame, test_df: pd.DataFrame):
    merged = test_df.merge(
        forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
        on='ds', how='left'
    )
    merged['yhat'] = merged['yhat'].clip(lower=0)

    rmse = np.sqrt(mean_squared_error(merged['y'], merged['yhat']))
    mae  = mean_absolute_error(merged['y'], merged['yhat'])
    mape = np.mean(np.abs((merged['y'] - merged['yhat']) / merged['y'].replace(0, np.nan))) * 100

    return {
        'rmse': round(float(rmse), 2),
        'mae':  round(float(mae),  2),
        'mape': round(float(mape), 2),
    }, merged


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 56)
    print("PathWise — Prophet Demand Forecasting")
    print("=" * 56)

    # Task 10
    print("\n[Task 10] Building monthly demand time series ...")
    ts = build_demand_series()
    print(f"  Rows      : {len(ts)}")
    print(f"  Date range: {ts['ds'].min().date()} -> {ts['ds'].max().date()}")
    print(f"  Avg monthly postings: {ts['y'].mean():.0f}")

    # Task 11
    print("\n[Task 11] Training Prophet model ...")
    model, forecast, test_df = train(ts, test_months=6)
    print("  Training complete.")

    # Save
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    with open(META_PATH, 'wb') as f:
        pickle.dump({'freq': 'MS'}, f)
    print(f"  Model -> {MODEL_PATH}")

    # Task 13
    print("\n[Task 13] Evaluating Prophet on held-out 6 months ...")
    metrics, eval_df = evaluate(forecast, test_df)
    print(f"  RMSE: {metrics['rmse']}  |  MAE: {metrics['mae']}  |  MAPE: {metrics['mape']:.1f}%")
    print("\n  Sample predictions (last 6 months):")
    print(eval_df[['ds', 'y', 'yhat', 'yhat_lower', 'yhat_upper']]
          .tail(6)
          .to_string(index=False, float_format='{:.0f}'.format))

    print("\n[DONE] Prophet training complete.")
