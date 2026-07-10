"""
Inference script for XGBoost salary prediction.
Used by backend API to estimate early-career salary from a student profile.
"""
import pickle
import numpy as np
import pandas as pd
from pathlib import Path


PROGRAMS = [
    'BS Computer Science', 'BS Data Science', 'Certificate Data Analytics',
    'MBA Product Management', 'MS Artificial Intelligence', 'MS Business Analytics',
    'MS Cloud Computing', 'MS Computer Science', 'MS Cybersecurity',
    'MS Data Science', 'MS Human-Computer Interaction', 'MS Information Technology',
]


def predict_salary(student_profile: dict) -> dict:
    """
    Predict expected early-career annual salary for a student.

    Args:
        student_profile: {
            'gpa': float (0.0–4.0),
            'internships': int,
            'projects': int,
            'communication_score': int (1–10),
            'program': str (one of the 12 programs)
        }

    Returns:
        {
            'predicted_salary': float,
            'confidence_low': float,   # 80 % lower bound
            'confidence_high': float,  # 80 % upper bound
        }
    """
    script_dir = Path(__file__).parent
    model_path = script_dir / 'models' / 'salary_xgboost.pkl'
    meta_path  = script_dir / 'models' / 'salary_xgboost_meta.pkl'

    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    with open(meta_path, 'rb') as f:
        meta = pickle.load(f)

    feature_names = meta['feature_names']
    rmse = meta['rmse']

    # Same scaling as training (MinMaxScaler equivalent)
    gpa_scaled  = (student_profile['gpa'] - 2.0) / (4.0 - 2.0)
    comm_scaled = (student_profile['communication_score'] - 1) / (10 - 1)

    feature_dict: dict = {
        'gpa_scaled':                 gpa_scaled,
        'internships':                student_profile['internships'],
        'projects':                   student_profile['projects'],
        'communication_score_scaled': comm_scaled,
    }
    for prog in PROGRAMS:
        feature_dict[f'prog_{prog}'] = 1 if student_profile['program'] == prog else 0

    X = pd.DataFrame([feature_dict])[feature_names]
    predicted = float(model.predict(X)[0])

    # 80 % confidence interval: predicted ± 1.28 × RMSE
    margin = 1.28 * rmse
    return {
        'predicted_salary': round(predicted, 2),
        'confidence_low':   round(max(0.0, predicted - margin), 2),
        'confidence_high':  round(predicted + margin, 2),
    }


if __name__ == '__main__':
    print("Testing XGBoost Salary Predictor\n" + "=" * 50)

    profiles = [
        ('Strong  (MS Data Science, GPA 3.9, 4 internships)',
         {'gpa': 3.9, 'internships': 4, 'projects': 5, 'communication_score': 9,
          'program': 'MS Data Science'}),
        ('Weak    (Certificate, GPA 2.3, 0 internships)',
         {'gpa': 2.3, 'internships': 0, 'projects': 1, 'communication_score': 3,
          'program': 'Certificate Data Analytics'}),
        ('Average (MS CS, GPA 3.2, 2 internships)',
         {'gpa': 3.2, 'internships': 2, 'projects': 3, 'communication_score': 7,
          'program': 'MS Computer Science'}),
    ]

    for label, profile in profiles:
        result = predict_salary(profile)
        print(f"\n[{label}]")
        print(f"  Predicted salary : ${result['predicted_salary']:>10,.0f}")
        print(f"  80% range        : ${result['confidence_low']:>10,.0f} – ${result['confidence_high']:,.0f}")
