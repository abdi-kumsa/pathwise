"""
Train XGBoost model for student placement prediction.

Features: GPA, internships, projects, communication_score, program (one-hot)
Target: placed (binary: 1 = placed, 0 = not placed)
"""
import xgboost as xgb
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import pickle
from load_features import load_placement_features


def train_xgboost_model():
    """Train XGBoost placement prediction model"""
    print("Loading features...")
    X_train, X_test, y_train, y_test = load_placement_features()

    print(f"\nTraining set: {X_train.shape[0]} students")
    print(f"Test set: {X_test.shape[0]} students")
    print(f"Placement rate (train): {y_train.sum() / len(y_train) * 100:.1f}%")
    print(f"Placement rate (test): {y_test.sum() / len(y_test) * 100:.1f}%")

    # Train XGBoost model
    print("\nTraining XGBoost model...")
    # Monotone constraints: +1 = must increase, 0 = unconstrained
    # Enforces that higher GPA / more internships / better comm always help placement
    monotone = {
        'gpa_scaled': 1,
        'internships': 1,
        'projects': 1,
        'communication_score_scaled': 1,
    }
    # All programme dummies get 0 (no ordering between categories)
    for col in X_train.columns:
        if col.startswith('prog_'):
            monotone[col] = 0

    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        objective='binary:logistic',
        random_state=42,
        eval_metric='logloss',
        monotone_constraints=monotone,
    )

    model.fit(X_train, y_train)

    # Evaluate on test set
    print("\nEvaluating model...")
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    print("\n" + "="*50)
    print("XGBOOST PLACEMENT MODEL - PERFORMANCE METRICS")
    print("="*50)
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    print("="*50)

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Not Placed', 'Placed']))

    # Feature importance
    print("\nTop 10 Feature Importances:")
    feature_importance = sorted(
        zip(X_train.columns, model.feature_importances_),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    for feature, importance in feature_importance:
        print(f"  {feature:40s}: {importance:.4f}")

    # Save model
    model_path = 'models/placement_xgboost.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"\n[OK] Model saved to {model_path}")

    # Save feature names for inference
    feature_names_path = 'models/placement_feature_names.pkl'
    with open(feature_names_path, 'wb') as f:
        pickle.dump(X_train.columns.tolist(), f)
    print(f"[OK] Feature names saved to {feature_names_path}")

    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'feature_importance': dict(feature_importance)
    }


if __name__ == '__main__':
    metrics = train_xgboost_model()
