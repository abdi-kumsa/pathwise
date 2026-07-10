"""
Task 8: LSTM enrollment inference
Predicts enrollment count for a given program and future year.
Usage:
    python ml/predict_enrollment.py
    python ml/predict_enrollment.py --program "MS Data Science" --years 2
"""
import os
import pickle
import argparse
import numpy as np
import pandas as pd

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
from tensorflow.keras.models import load_model

# ── Paths ─────────────────────────────────────────────────────────────────────

def _project_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


ROOT        = _project_root()
PARQUET     = os.path.join(ROOT, 'data', 'processed', 'features.parquet')
MODEL_DIR   = os.path.join(ROOT, 'ml', 'models')
MODEL_PATH  = os.path.join(MODEL_DIR, 'enrollment_lstm.keras')
SCALER_PATH = os.path.join(MODEL_DIR, 'enrollment_scaler.pkl')
META_PATH   = os.path.join(MODEL_DIR, 'enrollment_lstm_meta.pkl')


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_artifacts():
    model   = load_model(MODEL_PATH)
    with open(SCALER_PATH, 'rb') as f:
        scalers = pickle.load(f)
    with open(META_PATH, 'rb') as f:
        meta = pickle.load(f)
    return model, scalers, meta


def load_history(program: str) -> np.ndarray:
    """Return historical enrollment counts (sorted by year) for a program."""
    df = pd.read_parquet(PARQUET)
    prog_cols = [c for c in df.columns if c.startswith('prog_')]
    df['program'] = df[prog_cols].idxmax(axis=1).str.replace('prog_', '', regex=False)
    prog_df = (
        df[df['program'] == program]
          .groupby('enrollment_year')
          .size()
          .reset_index(name='count')
          .sort_values('enrollment_year')
    )
    if prog_df.empty:
        raise ValueError(f"Program not found: '{program}'")
    return prog_df['enrollment_year'].values, prog_df['count'].values.astype(float)


def predict_next_years(program: str, n_years: int = 2):
    """
    Predict enrollment for the next n_years beyond the last known year.
    Uses a rolling forecast: each predicted value feeds the next window.
    """
    model, scalers, meta = load_artifacts()
    seq_len = meta['seq_len']

    if program not in scalers:
        raise ValueError(f"No scaler for '{program}'. Valid programs: {list(scalers.keys())}")

    years, counts = load_history(program)
    scaler = scalers[program]

    norm = scaler.transform(counts.reshape(-1, 1)).flatten()

    # Seed the rolling window from the last seq_len known values
    window = list(norm[-seq_len:])
    predictions = []
    last_year = int(years[-1])

    for step in range(n_years):
        x = np.array(window[-seq_len:], dtype=np.float32).reshape(1, seq_len, 1)
        pred_norm = model.predict(x, verbose=0)[0, 0]
        pred_count = float(scaler.inverse_transform([[pred_norm]])[0, 0])
        pred_year  = last_year + step + 1
        predictions.append({'year': pred_year, 'predicted_enrollment': round(pred_count)})
        window.append(pred_norm)

    return predictions


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Predict enrollment with LSTM')
    parser.add_argument('--program', type=str, default=None,
                        help='Program name (default: run all programs)')
    parser.add_argument('--years', type=int, default=2,
                        help='Number of future years to forecast (default: 2)')
    args = parser.parse_args()

    _, scalers, _ = load_artifacts()
    programs = [args.program] if args.program else list(scalers.keys())

    print(f"\nEnrollment Forecasts (next {args.years} year(s))\n" + "=" * 58)
    for prog in programs:
        try:
            preds = predict_next_years(prog, n_years=args.years)
            print(f"\n  {prog}")
            for p in preds:
                print(f"    {p['year']}: {p['predicted_enrollment']} students")
        except ValueError as e:
            print(f"  [ERROR] {e}")


if __name__ == '__main__':
    main()
