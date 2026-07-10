"""
Tasks 6-9: LSTM Enrollment Forecasting
- Task 6: Prepare enrollment time series sequences from features.parquet
- Task 7: Build and train LSTM model
- Task 9: Evaluate LSTM (RMSE, MAE)
Model saved to ml/models/enrollment_lstm.keras
"""
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'   # suppress TF info logs
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Input
from tensorflow.keras.callbacks import EarlyStopping

SEED = 42
tf.random.set_seed(SEED)
np.random.seed(SEED)

SEQ_LEN = 3   # look at 3 years -> predict next year

# ── Paths ─────────────────────────────────────────────────────────────────────

def _project_root():
    here = os.path.dirname(os.path.abspath(__file__))
    # ml/ is one level below project root
    return os.path.dirname(here)


ROOT = _project_root()
PARQUET = os.path.join(ROOT, 'data', 'processed', 'features.parquet')
MODEL_DIR = os.path.join(ROOT, 'ml', 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH  = os.path.join(MODEL_DIR, 'enrollment_lstm.keras')
SCALER_PATH = os.path.join(MODEL_DIR, 'enrollment_scaler.pkl')
META_PATH   = os.path.join(MODEL_DIR, 'enrollment_lstm_meta.pkl')


# ── Task 6: Data preparation ──────────────────────────────────────────────────

def load_enrollment_series():
    """Aggregate features.parquet into enrollment counts by program × year."""
    df = pd.read_parquet(PARQUET)

    # Reconstruct program name from one-hot columns (prog_<Name>)
    prog_cols = [c for c in df.columns if c.startswith('prog_')]
    df['program'] = df[prog_cols].idxmax(axis=1).str.replace('prog_', '', regex=False)

    enrollment = (
        df.groupby(['program', 'enrollment_year'])
          .size()
          .reset_index(name='count')
          .sort_values(['program', 'enrollment_year'])
    )
    return enrollment


def make_sequences(counts: np.ndarray, seq_len: int = SEQ_LEN):
    """Sliding-window sequences from a 1-D normalized count array."""
    X, y = [], []
    for i in range(len(counts) - seq_len):
        X.append(counts[i : i + seq_len])
        y.append(counts[i + seq_len])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def prepare_data(enrollment: pd.DataFrame):
    """
    Build X/y arrays across all programs.
    Each program is normalised with its own MinMaxScaler so the model
    learns relative trends rather than absolute headcounts.
    Returns X_train, y_train, X_test, y_test, scalers dict, program list.
    """
    programs = enrollment['program'].unique()
    years    = sorted(enrollment['enrollment_year'].unique())

    # Hold last year out for testing (per program)
    test_year  = years[-1]    # 2024
    train_years = years[:-1]  # 2019-2023

    scalers   = {}
    X_train_all, y_train_all = [], []
    X_test_all,  y_test_all  = [], []

    for prog in programs:
        prog_data = enrollment[enrollment['program'] == prog].sort_values('enrollment_year')
        counts    = prog_data['count'].values.astype(float)

        # Fit scaler on training years only
        train_mask  = prog_data['enrollment_year'].isin(train_years)
        train_counts = counts[train_mask.values]

        scaler = MinMaxScaler()
        scaler.fit(train_counts.reshape(-1, 1))
        scalers[prog] = scaler

        norm_counts = scaler.transform(counts.reshape(-1, 1)).flatten()

        # Sequences from full series (train uses first 5, test uses last window)
        X, y = make_sequences(norm_counts, SEQ_LEN)

        # Last sequence uses [2022, 2023, 2024] -> but we only have up to 2024
        # Split: sequences whose target is NOT the test year go to train
        target_years = np.array(years[SEQ_LEN:])   # year for each y value
        train_mask_seq = target_years < test_year
        test_mask_seq  = target_years == test_year

        if train_mask_seq.any():
            X_train_all.append(X[train_mask_seq])
            y_train_all.append(y[train_mask_seq])
        if test_mask_seq.any():
            X_test_all.append(X[test_mask_seq])
            y_test_all.append(y[test_mask_seq])

    X_train = np.concatenate(X_train_all).reshape(-1, SEQ_LEN, 1)
    y_train = np.concatenate(y_train_all)
    X_test  = np.concatenate(X_test_all).reshape(-1, SEQ_LEN, 1)
    y_test  = np.concatenate(y_test_all)

    return X_train, y_train, X_test, y_test, scalers, list(programs)


# ── Task 7: Build & train LSTM ────────────────────────────────────────────────

def build_model(seq_len: int = SEQ_LEN) -> Sequential:
    model = Sequential([
        Input(shape=(seq_len, 1)),
        LSTM(32, return_sequences=True),
        LSTM(16),
        Dense(1),
    ])
    model.compile(optimizer='adam', loss='mse')
    return model


def train(X_train, y_train, epochs=200, batch_size=8):
    model = build_model()
    early_stop = EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True)
    history = model.fit(
        X_train, y_train,
        validation_split=0.2,
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[early_stop],
        verbose=0,
    )
    return model, history


# ── Task 9: Evaluate ──────────────────────────────────────────────────────────

def evaluate(model, X_test, y_test, enrollment, scalers, programs):
    """Compute RMSE and MAE in original (count) units per program."""
    years = sorted(enrollment['enrollment_year'].unique())
    test_year = years[-1]

    preds_norm = model.predict(X_test, verbose=0).flatten()

    rmse_list, mae_list = [], []
    per_program = {}

    for i, prog in enumerate(programs):
        prog_data = enrollment[enrollment['program'] == prog].sort_values('enrollment_year')
        target_years = np.array(years[SEQ_LEN:])
        test_mask = target_years == test_year

        if not test_mask.any():
            continue

        y_true_norm  = y_test[i : i + 1]
        y_pred_norm  = preds_norm[i : i + 1]

        scaler = scalers[prog]
        y_true = scaler.inverse_transform(y_true_norm.reshape(-1, 1)).flatten()
        y_pred = scaler.inverse_transform(y_pred_norm.reshape(-1, 1)).flatten()

        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae  = mean_absolute_error(y_true, y_pred)
        rmse_list.append(rmse)
        mae_list.append(mae)
        per_program[prog] = {'y_true': float(y_true[0]), 'y_pred': float(y_pred[0]),
                             'rmse': round(float(rmse), 2), 'mae': round(float(mae), 2)}

    overall = {
        'rmse': round(float(np.mean(rmse_list)), 2),
        'mae':  round(float(np.mean(mae_list)),  2),
    }
    return overall, per_program


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 56)
    print("PathWise — LSTM Enrollment Forecasting")
    print("=" * 56)

    # Task 6
    print("\n[Task 6] Loading & preparing enrollment sequences ...")
    enrollment = load_enrollment_series()
    print(f"  Programs : {enrollment['program'].nunique()}")
    print(f"  Year range: {enrollment['enrollment_year'].min()} – {enrollment['enrollment_year'].max()}")
    print(f"  Total rows: {len(enrollment)}")

    X_train, y_train, X_test, y_test, scalers, programs = prepare_data(enrollment)
    print(f"  X_train: {X_train.shape}  y_train: {y_train.shape}")
    print(f"  X_test : {X_test.shape}   y_test : {y_test.shape}")

    # Task 7
    print("\n[Task 7] Building and training LSTM ...")
    model, history = train(X_train, y_train)
    epochs_run = len(history.history['loss'])
    final_loss  = history.history['val_loss'][-1]
    print(f"  Stopped at epoch {epochs_run}  |  val_loss: {final_loss:.6f}")
    model.summary()

    # Save model + scalers
    model.save(MODEL_PATH)
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scalers, f)
    with open(META_PATH, 'wb') as f:
        pickle.dump({'programs': programs, 'seq_len': SEQ_LEN}, f)
    print(f"\n  Model  -> {MODEL_PATH}")
    print(f"  Scaler -> {SCALER_PATH}")

    # Task 9
    print("\n[Task 9] Evaluating LSTM on held-out year (2024) ...")
    overall, per_prog = evaluate(model, X_test, y_test, enrollment, scalers, programs)
    print(f"\n  Overall  RMSE: {overall['rmse']}  |  MAE: {overall['mae']}")
    print("\n  Per-program results (actual vs. predicted):")
    for prog, m in per_prog.items():
        print(f"    {prog:<36}  actual={m['y_true']:.0f}  pred={m['y_pred']:.0f}"
              f"  RMSE={m['rmse']:.1f}  MAE={m['mae']:.1f}")

    print("\n[DONE] LSTM training complete.")
