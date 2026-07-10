"""
Feature loading utility for PathWise ML models.
Loads and splits features.parquet for training and testing.
"""
import pandas as pd
from sklearn.model_selection import train_test_split


def load_placement_features(test_size=0.2, random_state=42):
    """
    Load features for XGBoost placement prediction model.

    Returns:
        X_train, X_test, y_train, y_test
    """
    import os

    # Use absolute path from current working directory
    parquet_path = os.path.join(os.getcwd(), 'data', 'processed', 'features.parquet')

    # If running from ml/ directory, adjust path
    if not os.path.exists(parquet_path):
        parquet_path = os.path.join(os.path.dirname(os.getcwd()), 'data', 'processed', 'features.parquet')

    df = pd.read_parquet(parquet_path)

    # Features for placement prediction
    feature_cols = [
        'gpa_scaled',
        'internships',
        'projects',
        'communication_score_scaled',
        'prog_BS Computer Science',
        'prog_BS Data Science',
        'prog_Certificate Data Analytics',
        'prog_MBA Product Management',
        'prog_MS Artificial Intelligence',
        'prog_MS Business Analytics',
        'prog_MS Cloud Computing',
        'prog_MS Computer Science',
        'prog_MS Cybersecurity',
        'prog_MS Data Science',
        'prog_MS Human-Computer Interaction',
        'prog_MS Information Technology'
    ]

    X = df[feature_cols]
    y = df['placed']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    return X_train, X_test, y_train, y_test


def load_enrollment_data():
    """
    Load enrollment time series data for LSTM forecasting.

    Returns:
        DataFrame with enrollment data from database
    """
    import psycopg2
    import os
    from dotenv import load_dotenv

    load_dotenv()

    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

    query = """
        SELECT program, year, count
        FROM enrollments
        ORDER BY program, year
    """

    df = pd.read_sql(query, conn)
    conn.close()

    return df


def load_job_postings_data():
    """
    Load job postings time series data for Prophet forecasting.

    Returns:
        DataFrame with job posting counts aggregated by date
    """
    import psycopg2
    import os
    from dotenv import load_dotenv

    load_dotenv()

    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

    query = """
        SELECT posted_date, COUNT(*) as postings
        FROM job_postings
        GROUP BY posted_date
        ORDER BY posted_date
    """

    df = pd.read_sql(query, conn)
    conn.close()

    return df


if __name__ == '__main__':
    # Test loading
    print("Testing placement features loading...")
    X_train, X_test, y_train, y_test = load_placement_features()
    print(f"[OK] X_train shape: {X_train.shape}")
    print(f"[OK] X_test shape: {X_test.shape}")
    print(f"[OK] y_train distribution: {y_train.value_counts().to_dict()}")
    print(f"[OK] y_test distribution: {y_test.value_counts().to_dict()}")

    print("\nTesting enrollment data loading...")
    enrollment_df = load_enrollment_data()
    print(f"[OK] Enrollment data shape: {enrollment_df.shape}")
    print(f"[OK] Programs: {enrollment_df['program'].nunique()}")
    print(f"[OK] Year range: {enrollment_df['year'].min()} - {enrollment_df['year'].max()}")

    print("\nTesting job postings data loading...")
    postings_df = load_job_postings_data()
    print(f"[OK] Job postings data shape: {postings_df.shape}")
    print(f"[OK] Date range: {postings_df['posted_date'].min()} to {postings_df['posted_date'].max()}")
