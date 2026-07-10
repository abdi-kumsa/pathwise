"""
Inference script for XGBoost placement prediction.
Used by backend API to predict student placement probability.
"""
import pickle
import numpy as np
import pandas as pd


def predict_placement(student_profile):
    """
    Predict placement probability for a student.

    Args:
        student_profile (dict): Student features
            {
                'gpa': float (0.0-4.0),
                'internships': int (0-10),
                'projects': int (0-10),
                'communication_score': int (1-10),
                'program': str (one of the 12 programs)
            }

    Returns:
        dict: {
            'placed_probability': float,
            'predicted_class': str ('Placed' or 'Not Placed'),
            'confidence': float
        }
    """
    import os
    from pathlib import Path

    # Get paths relative to script location
    script_dir = Path(__file__).parent
    model_path = script_dir / 'models' / 'placement_xgboost.pkl'
    feature_names_path = script_dir / 'models' / 'placement_feature_names.pkl'
    scaler_path = script_dir / '..' / 'data' / 'processed' / 'scaler.pkl'

    # Load model and feature names
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    with open(feature_names_path, 'rb') as f:
        feature_names = pickle.load(f)

    # Manual scaling (MinMaxScaler equivalent)
    # GPA range: 2.0-4.0, Comm score range: 1-10
    gpa_scaled = (student_profile['gpa'] - 2.0) / (4.0 - 2.0)
    comm_scaled = (student_profile['communication_score'] - 1) / (10 - 1)

    # Create feature vector matching training format
    feature_dict = {
        'gpa_scaled': gpa_scaled,
        'internships': student_profile['internships'],
        'projects': student_profile['projects'],
        'communication_score_scaled': comm_scaled
    }

    # Add program one-hot encoding (all zeros except selected program)
    programs = [
        'BS Computer Science', 'BS Data Science', 'Certificate Data Analytics',
        'MBA Product Management', 'MS Artificial Intelligence', 'MS Business Analytics',
        'MS Cloud Computing', 'MS Computer Science', 'MS Cybersecurity',
        'MS Data Science', 'MS Human-Computer Interaction', 'MS Information Technology'
    ]

    for prog in programs:
        prog_key = f'prog_{prog}'
        feature_dict[prog_key] = 1 if student_profile['program'] == prog else 0

    # Create DataFrame in correct column order
    X = pd.DataFrame([feature_dict])[feature_names]

    # Predict
    probability = model.predict_proba(X)[0][1]  # Probability of class 1 (Placed)
    predicted_class = 'Placed' if probability >= 0.5 else 'Not Placed'
    confidence = max(probability, 1 - probability)

    return {
        'placed_probability': float(probability),
        'predicted_class': predicted_class,
        'confidence': float(confidence)
    }


if __name__ == '__main__':
    # Test cases
    print("Testing XGBoost Placement Predictor\n" + "="*50)

    # Test Case 1: Strong candidate
    student1 = {
        'gpa': 3.8,
        'internships': 3,
        'projects': 5,
        'communication_score': 9,
        'program': 'MS Data Science'
    }
    result1 = predict_placement(student1)
    print("\n[Test 1] Strong Candidate (MS Data Science, GPA 3.8, 3 internships)")
    print(f"  Prediction: {result1['predicted_class']}")
    print(f"  Probability: {result1['placed_probability']:.2%}")
    print(f"  Confidence: {result1['confidence']:.2%}")

    # Test Case 2: Weak candidate
    student2 = {
        'gpa': 2.5,
        'internships': 0,
        'projects': 1,
        'communication_score': 4,
        'program': 'Certificate Data Analytics'
    }
    result2 = predict_placement(student2)
    print("\n[Test 2] Weak Candidate (Certificate, GPA 2.5, 0 internships)")
    print(f"  Prediction: {result2['predicted_class']}")
    print(f"  Probability: {result2['placed_probability']:.2%}")
    print(f"  Confidence: {result2['confidence']:.2%}")

    # Test Case 3: Average candidate
    student3 = {
        'gpa': 3.2,
        'internships': 1,
        'projects': 3,
        'communication_score': 7,
        'program': 'MS Computer Science'
    }
    result3 = predict_placement(student3)
    print("\n[Test 3] Average Candidate (MS CS, GPA 3.2, 1 internship)")
    print(f"  Prediction: {result3['predicted_class']}")
    print(f"  Probability: {result3['placed_probability']:.2%}")
    print(f"  Confidence: {result3['confidence']:.2%}")
