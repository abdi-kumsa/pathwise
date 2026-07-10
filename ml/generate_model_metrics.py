"""
Task 16: Generate ml/models/model_metrics.json
Collects metrics from all trained models and writes a single JSON summary.
Run AFTER all three models are trained.
"""
import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, mean_squared_error, mean_absolute_error)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

def _project_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


ROOT       = _project_root()
PARQUET    = os.path.join(ROOT, 'data', 'processed', 'features.parquet')
MODEL_DIR  = os.path.join(ROOT, 'ml', 'models')
OUT_PATH   = os.path.join(MODEL_DIR, 'model_metrics.json')


def xgboost_metrics():
    """
    Read placement metrics from the current model_metrics.json rather than
    re-evaluating the pkl, which is sensitive to XGBoost version differences
    between the training environment and the inference environment.
    """
    existing = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as f:
            existing = json.load(f)
    if 'xgboost_placement' in existing:
        return existing['xgboost_placement']

    # Fallback: load and evaluate (only safe when training and inference
    # environments use the exact same XGBoost version)
    with open(os.path.join(MODEL_DIR, 'placement_xgboost.pkl'), 'rb') as f:
        model = pickle.load(f)
    with open(os.path.join(MODEL_DIR, 'placement_feature_names.pkl'), 'rb') as f:
        feature_names = pickle.load(f)

    df = pd.read_parquet(PARQUET)
    X  = df[feature_names]
    y  = df['placed']
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    y_pred = model.predict(X_test)
    fi     = dict(sorted(zip(feature_names, model.feature_importances_),
                         key=lambda x: x[1], reverse=True)[:10])

    return {
        'model': 'XGBoost',
        'task': 'placement_classification',
        'accuracy':   round(float(accuracy_score(y_test, y_pred)),  4),
        'precision':  round(float(precision_score(y_test, y_pred)), 4),
        'recall':     round(float(recall_score(y_test, y_pred)),    4),
        'f1_score':   round(float(f1_score(y_test, y_pred)),        4),
        'top_features': {k: round(float(v), 4) for k, v in fi.items()},
    }


def lstm_metrics():
    from tensorflow.keras.models import load_model as keras_load

    model_path = os.path.join(MODEL_DIR, 'enrollment_lstm.keras')
    if not os.path.exists(model_path):
        return {'model': 'LSTM', 'status': 'not_trained'}

    with open(os.path.join(MODEL_DIR, 'enrollment_scaler.pkl'), 'rb') as f:
        scalers = pickle.load(f)
    with open(os.path.join(MODEL_DIR, 'enrollment_lstm_meta.pkl'), 'rb') as f:
        meta = pickle.load(f)

    keras_model = keras_load(model_path)
    SEQ_LEN = meta['seq_len']

    df = pd.read_parquet(PARQUET)
    prog_cols  = [c for c in df.columns if c.startswith('prog_')]
    df['program'] = df[prog_cols].idxmax(axis=1).str.replace('prog_', '', regex=False)
    enrollment = (df.groupby(['program', 'enrollment_year'])
                    .size().reset_index(name='count')
                    .sort_values(['program', 'enrollment_year']))
    years = sorted(enrollment['enrollment_year'].unique())
    test_year = years[-1]

    rmse_list, mae_list = [], []
    for prog in meta['programs']:
        prog_data = enrollment[enrollment['program'] == prog].sort_values('enrollment_year')
        counts    = prog_data['count'].values.astype(float)
        scaler    = scalers[prog]
        norm      = scaler.transform(counts.reshape(-1, 1)).flatten()

        target_years = np.array(years[SEQ_LEN:])
        test_mask    = target_years == test_year
        if not test_mask.any():
            continue

        X, y = [], []
        for i in range(len(norm) - SEQ_LEN):
            X.append(norm[i:i+SEQ_LEN])
            y.append(norm[i+SEQ_LEN])
        X, y = np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

        y_pred_norm = keras_model.predict(X[test_mask].reshape(-1, SEQ_LEN, 1), verbose=0).flatten()
        y_true = scaler.inverse_transform(y[test_mask].reshape(-1, 1)).flatten()
        y_pred = scaler.inverse_transform(y_pred_norm.reshape(-1, 1)).flatten()

        rmse_list.append(np.sqrt(mean_squared_error(y_true, y_pred)))
        mae_list.append(mean_absolute_error(y_true, y_pred))

    return {
        'model': 'LSTM',
        'task': 'enrollment_forecasting',
        'seq_len': SEQ_LEN,
        'test_year': int(test_year),
        'rmse': round(float(np.mean(rmse_list)), 2),
        'mae':  round(float(np.mean(mae_list)),  2),
    }


def salary_metrics():
    """Read salary metrics from the meta pickle written at training time."""
    meta_path = os.path.join(MODEL_DIR, 'salary_xgboost_meta.pkl')
    if not os.path.exists(meta_path):
        model_path = os.path.join(MODEL_DIR, 'salary_xgboost.pkl')
        if not os.path.exists(model_path):
            return {'model': 'XGBoostRegressor', 'status': 'not_trained'}
        return {'model': 'XGBoostRegressor', 'status': 'meta_missing'}

    with open(meta_path, 'rb') as f:
        meta = pickle.load(f)

    fi = dict(sorted(meta.get('top_features', {}).items(),
                     key=lambda x: x[1], reverse=True)[:10])

    return {
        'model': 'XGBoostRegressor',
        'task':  'salary_prediction',
        'rmse':  round(float(meta['rmse']), 2),
        'mae':   round(float(meta['mae']),  2),
        'r2':    round(float(meta['r2']),   4),
        'top_features': {k: round(float(v), 4) for k, v in fi.items()},
    }


def prophet_metrics():
    prophet_path = os.path.join(MODEL_DIR, 'demand_prophet.pkl')
    if not os.path.exists(prophet_path):
        return {'model': 'Prophet', 'status': 'not_trained'}

    # Preserve existing metrics from the JSON rather than re-evaluating.
    # model.predict() is sensitive to pandas version differences between the
    # environment where the model was pickled and where it is being evaluated.
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as f:
            existing = json.load(f)
        if 'prophet_demand' in existing:
            entry = existing['prophet_demand']
            if entry.get('rmse') is not None:
                return entry

    return {
        'model': 'Prophet',
        'task':  'demand_forecasting',
        'test_period_months': 6,
        'status': 'metrics_unavailable',
    }


if __name__ == '__main__':
    print("Collecting model metrics ...")
    output = {
        'xgboost_placement': xgboost_metrics(),
        'xgboost_salary':    salary_metrics(),
        'lstm_enrollment':   lstm_metrics(),
        'prophet_demand':    prophet_metrics(),
    }

    with open(OUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Saved -> {OUT_PATH}")
    print(json.dumps(output, indent=2))
