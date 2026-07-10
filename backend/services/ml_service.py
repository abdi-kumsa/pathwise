"""
ML model service — single place that loads all trained models.
Models are loaded lazily on first call and held in module-level singletons
so uvicorn workers never re-load them per request.
"""
import sys
import os
import pickle
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

# ── Resolve project root and add ml/ to sys.path ─────────────────────────────
# backend/services/ml_service.py -> backend/services/ -> backend/ -> project root
_ROOT = Path(__file__).resolve().parent.parent.parent
_ML_DIR = _ROOT / 'ml'
_MODEL_DIR = _ML_DIR / 'models'
_PARQUET = _ROOT / 'data' / 'processed' / 'features.parquet'

if str(_ML_DIR) not in sys.path:
    sys.path.insert(0, str(_ML_DIR))

# ── Module-level singletons ───────────────────────────────────────────────────
_xgboost_model = None
_feature_names = None
_salary_model  = None
_salary_meta   = None
_lstm_model = None
_lstm_scalers = None
_lstm_meta = None
_prophet_model = None
_shap_cache = None   # (shap_values, base_val, feature_names, X_sample)


# ── Loaders ───────────────────────────────────────────────────────────────────

def get_xgboost():
    global _xgboost_model, _feature_names
    if _xgboost_model is None:
        with open(_MODEL_DIR / 'placement_xgboost.pkl', 'rb') as f:
            _xgboost_model = pickle.load(f)
        with open(_MODEL_DIR / 'placement_feature_names.pkl', 'rb') as f:
            _feature_names = pickle.load(f)
    return _xgboost_model, _feature_names


def get_salary_model():
    global _salary_model, _salary_meta
    if _salary_model is None:
        with open(_MODEL_DIR / 'salary_xgboost.pkl', 'rb') as f:
            _salary_model = pickle.load(f)
        with open(_MODEL_DIR / 'salary_xgboost_meta.pkl', 'rb') as f:
            _salary_meta = pickle.load(f)
    return _salary_model, _salary_meta


def get_lstm():
    global _lstm_model, _lstm_scalers, _lstm_meta
    if _lstm_model is None:
        os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
        from tensorflow.keras.models import load_model
        _lstm_model = load_model(str(_MODEL_DIR / 'enrollment_lstm.keras'))
        with open(_MODEL_DIR / 'enrollment_scaler.pkl', 'rb') as f:
            _lstm_scalers = pickle.load(f)
        with open(_MODEL_DIR / 'enrollment_lstm_meta.pkl', 'rb') as f:
            _lstm_meta = pickle.load(f)
    return _lstm_model, _lstm_scalers, _lstm_meta


def get_prophet():
    global _prophet_model
    if _prophet_model is None:
        with open(_MODEL_DIR / 'demand_prophet.pkl', 'rb') as f:
            _prophet_model = pickle.load(f)
    return _prophet_model


def get_shap_cache():
    """Compute SHAP values on 200 test samples once and cache the result."""
    global _shap_cache
    if _shap_cache is None:
        from explain_predictions import compute_shap_values
        _shap_cache = compute_shap_values(n_samples=200)
    return _shap_cache


# ── Inference wrappers ────────────────────────────────────────────────────────

def predict_placement(student_dict: dict) -> dict:
    from predict_placement import predict_placement as _fn
    return _fn(student_dict)


def predict_salary(student_dict: dict) -> dict:
    from predict_salary import predict_salary as _fn
    return _fn(student_dict)


def explain_student(student_dict: dict) -> dict:
    from explain_predictions import explain_student as _fn
    return _fn(student_dict)


def forecast_enrollment(program: str, n_years: int = 3) -> list:
    from predict_enrollment import predict_next_years
    return predict_next_years(program, n_years=n_years)


def forecast_demand(months_ahead: int = 12):
    """Returns a pandas DataFrame with columns: month, predicted_postings, lower_bound, upper_bound."""
    from predict_demand import predict_demand
    return predict_demand(months_ahead)
