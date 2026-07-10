"""
Train XGBoost model for early-career salary prediction.

Features: GPA, internships, projects, communication_score, program (one-hot)
Target:   salary (USD, annual) — placed students only
"""
import os
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split


def _project_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


FEATURE_COLS = [
    'gpa_scaled', 'internships', 'projects', 'communication_score_scaled',
    'prog_BS Computer Science', 'prog_BS Data Science',
    'prog_Certificate Data Analytics', 'prog_MBA Product Management',
    'prog_MS Artificial Intelligence', 'prog_MS Business Analytics',
    'prog_MS Cloud Computing', 'prog_MS Computer Science',
    'prog_MS Cybersecurity', 'prog_MS Data Science',
    'prog_MS Human-Computer Interaction', 'prog_MS Information Technology',
]


def train_salary_model():
    ROOT = _project_root()
    parquet_path = os.path.join(ROOT, 'data', 'processed', 'features.parquet')

    print("Loading features...")
    df = pd.read_parquet(parquet_path)

    # Salary only exists for placed students
    df = df[df['placed'] == 1].dropna(subset=['salary']).copy()
    print(f"Placed students with salary data: {len(df)}")
    print(f"Salary range: ${df['salary'].min():,.0f} – ${df['salary'].max():,.0f}")
    print(f"Salary mean:  ${df['salary'].mean():,.0f}")

    X = df[FEATURE_COLS]
    y = df['salary']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"\nTraining set: {len(X_train)} students")
    print(f"Test set:     {len(X_test)} students")

    print("\nTraining XGBoost salary regression model...")
    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective='reg:squarederror',
        random_state=42,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_pred = model.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae  = float(mean_absolute_error(y_test, y_pred))
    r2   = float(r2_score(y_test, y_pred))

    print("\n" + "=" * 50)
    print("XGBOOST SALARY MODEL — PERFORMANCE METRICS")
    print("=" * 50)
    print(f"RMSE: ${rmse:,.2f}")
    print(f"MAE:  ${mae:,.2f}")
    print(f"R²:   {r2:.4f}")
    print("=" * 50)

    print("\nTop 10 Feature Importances:")
    feature_importance = sorted(
        zip(FEATURE_COLS, model.feature_importances_),
        key=lambda x: x[1], reverse=True
    )[:10]
    for feat, imp in feature_importance:
        print(f"  {feat:40s}: {imp:.4f}")

    MODEL_DIR  = os.path.join(ROOT, 'ml', 'models')
    model_path = os.path.join(MODEL_DIR, 'salary_xgboost.pkl')
    meta_path  = os.path.join(MODEL_DIR, 'salary_xgboost_meta.pkl')

    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"\n[OK] Model saved   -> {model_path}")

    meta = {
        'feature_names': FEATURE_COLS,
        'rmse': rmse,
        'mae':  mae,
        'r2':   r2,
        'top_features': dict(feature_importance),
    }
    with open(meta_path, 'wb') as f:
        pickle.dump(meta, f)
    print(f"[OK] Meta saved    -> {meta_path}")

    return meta


if __name__ == '__main__':
    train_salary_model()
