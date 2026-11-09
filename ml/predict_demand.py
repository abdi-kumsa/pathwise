"""
Task 12: Prophet demand inference
Predicts monthly job-market demand for n future months.
Usage:
    python ml/predict_demand.py
    python ml/predict_demand.py --months 12
"""
import os
import pickle
import argparse
import warnings
import pandas as pd
try:
    from artifacts import verified_open, verify  # noqa: F401  (ml/ on sys.path)
except ImportError:  # imported as part of the ml package
    from ml.artifacts import verified_open, verify  # noqa: F401

warnings.filterwarnings('ignore')

# ── Paths ─────────────────────────────────────────────────────────────────────

def _project_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


ROOT       = _project_root()
MODEL_DIR  = os.path.join(ROOT, 'ml', 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'demand_prophet.pkl')


def load_model():
    with verified_open(MODEL_PATH) as f:
        return pickle.load(f)


CACHE_PATH = os.path.join(MODEL_DIR, 'demand_forecast_cache.json')


def predict_demand(months_ahead: int = 12) -> pd.DataFrame:
    """
    Return a DataFrame of monthly demand forecasts beyond the training data.

    Tries the pre-computed cache first (avoids Prophet/pandas version issues
    in the inference container where CmdStan is not available for retraining).
    Falls back to live Prophet inference if the cache is missing.
    """
    if os.path.exists(CACHE_PATH):
        import json
        with open(CACHE_PATH) as f:
            rows = json.load(f)
        df = pd.DataFrame(rows)
        df['month'] = pd.to_datetime(df['month'])
        return df.head(months_ahead).reset_index(drop=True)

    # Live inference fallback (requires compatible pandas + Prophet)
    model = load_model()
    future   = model.make_future_dataframe(periods=months_ahead, freq='MS')
    forecast = model.predict(future)

    last_train = model.history['ds'].max()
    future_fc  = forecast[forecast['ds'] > last_train][
        ['ds', 'yhat', 'yhat_lower', 'yhat_upper']
    ].copy()
    future_fc['yhat']       = future_fc['yhat'].clip(lower=0).round().astype(int)
    future_fc['yhat_lower'] = future_fc['yhat_lower'].clip(lower=0).round().astype(int)
    future_fc['yhat_upper'] = future_fc['yhat_upper'].clip(lower=0).round().astype(int)
    future_fc = future_fc.rename(columns={
        'ds': 'month',
        'yhat': 'predicted_postings',
        'yhat_lower': 'lower_bound',
        'yhat_upper': 'upper_bound',
    })

    return future_fc.reset_index(drop=True)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Forecast job-market demand with Prophet')
    parser.add_argument('--months', type=int, default=12,
                        help='Months to forecast beyond training data (default: 12)')
    args = parser.parse_args()

    print(f"\nJob-Market Demand Forecast — next {args.months} months\n" + "=" * 50)
    fc = predict_demand(args.months)
    print(fc.to_string(index=False))
    print(f"\nTotal predicted postings: {fc['predicted_postings'].sum():,}")


if __name__ == '__main__':
    main()
