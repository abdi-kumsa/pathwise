"""
Phase 2 — Step 3
Pulls data from Postgres, engineers features, and saves two parquet files:

  data/processed/features.parquet
      Student + placement data — ML-ready rows for XGBoost placement model.
      3 000 rows x N columns. Target column: `placed` (0/1).

  data/processed/enrollment_features.parquet
      Enrollment time series per program with lag and rolling-average features.
      Used by LSTM and Prophet models in Phase 3.

  data/processed/scaler.pkl
      Fitted MinMaxScaler (gpa + communication_score) — saved so inference
      can apply the exact same transform without re-fitting.

Run from the repo root:
  python ml/feature_engineering.py
"""

import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).parent.parent
ENV_FILE  = ROOT / ".env"
OUT_DIR   = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURES_OUT    = OUT_DIR / "features.parquet"
ENROLLMENT_OUT  = OUT_DIR / "enrollment_features.parquet"
SCALER_OUT      = OUT_DIR / "scaler.pkl"

# ── DB connection (same helper as load_to_db.py) ──────────────────────────────
load_dotenv(ENV_FILE)

def _build_dsn() -> str:
    url = os.getenv("DATABASE_URL", "")
    if url:
        return url
    user   = os.getenv("DB_USER",     "pathwise_user")
    pwd    = os.getenv("DB_PASSWORD", "pathwise_pass")
    host   = os.getenv("DB_HOST",     "db")
    port   = os.getenv("DB_PORT",     "5432")
    dbname = os.getenv("DB_NAME",     "pathwise_db")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{dbname}"


def get_conn():
    return psycopg2.connect(_build_dsn())


# ── Pull data from DB ─────────────────────────────────────────────────────────

def pull_students(conn) -> pd.DataFrame:
    return pd.read_sql(
        "SELECT id AS student_id, gpa, internships, projects, "
        "       communication_score, program, enrollment_year "
        "FROM   students ORDER BY id",
        conn,
    )


def pull_placements(conn) -> pd.DataFrame:
    return pd.read_sql(
        "SELECT student_id, placed, placement_status, salary, time_to_hire "
        "FROM   placements ORDER BY student_id",
        conn,
    )


def pull_enrollments(conn) -> pd.DataFrame:
    return pd.read_sql(
        "SELECT program, year, count "
        "FROM   enrollments ORDER BY program, year",
        conn,
    )


# ── Enrollment features ───────────────────────────────────────────────────────

STATUS_ENCODE = {"Matched": 2, "Overeducated": 1, "Undereducated": 0}

def build_enrollment_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add lag-1y, lag-2y, and 3-year rolling average within each program group.
    NaN values in lag/rolling columns are expected for the earliest years.
    """
    df = df.sort_values(["program", "year"]).copy()

    df["lag_1y"]          = df.groupby("program")["count"].shift(1)
    df["lag_2y"]          = df.groupby("program")["count"].shift(2)
    df["rolling_3y_avg"]  = (
        df.groupby("program")["count"]
        .transform(lambda s: s.rolling(window=3, min_periods=1).mean())
    )

    # Label-encode program so LSTM can receive a numeric identifier
    programs = sorted(df["program"].unique())
    prog_map = {p: i for i, p in enumerate(programs)}
    df["program_encoded"] = df["program"].map(prog_map)

    return df


# ── Student + placement features ──────────────────────────────────────────────

def build_student_features(
    students: pd.DataFrame,
    placements: pd.DataFrame,
) -> tuple[pd.DataFrame, MinMaxScaler]:
    """
    Returns:
      - ML-ready DataFrame (student rows merged with placement outcomes)
      - Fitted MinMaxScaler (persisted for inference)
    """
    # ── 1. Merge ──
    df = students.merge(placements, on="student_id", how="left")

    # ── 2. Target: placed → 0/1 integer ──
    df["placed"] = df["placed"].fillna(False).astype(int)

    # ── 3. Encode placement_status ──
    df["placement_status_encoded"] = (
        df["placement_status"]
        .map(STATUS_ENCODE)
        .fillna(-1)          # -1 = not placed / unknown
        .astype(int)
    )

    # ── 4. Scale gpa and communication_score to [0, 1] ──
    scaler = MinMaxScaler()
    df[["gpa_scaled", "communication_score_scaled"]] = scaler.fit_transform(
        df[["gpa", "communication_score"]]
    )

    # ── 5. One-hot encode program (12 columns, prefix "prog_") ──
    dummies = pd.get_dummies(df["program"], prefix="prog").astype(int)
    df = pd.concat([df, dummies], axis=1)

    # ── 6. Keep only ML-relevant columns ──
    feature_cols = (
        ["student_id", "enrollment_year",
         "gpa", "gpa_scaled",
         "internships", "projects",
         "communication_score", "communication_score_scaled",
         "placed", "placement_status_encoded",
         "salary", "time_to_hire"]
        + list(dummies.columns)
    )
    df = df[feature_cols]

    return df, scaler


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Connecting to database ...")
    try:
        conn = get_conn()
    except Exception as exc:
        print(f"  ERROR: could not connect — {exc}")
        print("  Make sure Docker is running and `docker compose up -d db` has been executed.")
        sys.exit(1)
    print("  Connected.")

    # ── Pull ──
    print("\nPulling data from Postgres ...")
    students    = pull_students(conn)
    placements  = pull_placements(conn)
    enrollments = pull_enrollments(conn)
    conn.close()
    print(f"  students:    {len(students)} rows")
    print(f"  placements:  {len(placements)} rows")
    print(f"  enrollments: {len(enrollments)} rows")

    # ── Enrollment features ──
    print("\nBuilding enrollment features ...")
    enroll_feat = build_enrollment_features(enrollments)
    enroll_feat.to_parquet(ENROLLMENT_OUT, index=False)
    print(f"  OK enrollment_features.parquet saved — {len(enroll_feat)} rows x {enroll_feat.shape[1]} columns")

    # ── Student features ──
    print("\nBuilding student features ...")
    student_feat, scaler = build_student_features(students, placements)
    student_feat.to_parquet(FEATURES_OUT, index=False)
    joblib.dump(scaler, SCALER_OUT)
    print(f"  OK features.parquet saved            — {len(student_feat)} rows x {student_feat.shape[1]} columns")
    print(f"  OK scaler.pkl saved")

    # ── Quick sanity ──
    placed_count = student_feat["placed"].sum()
    print(f"\nSanity check:")
    print(f"  placed=1 : {placed_count} ({placed_count/len(student_feat)*100:.1f}%)")
    print(f"  placed=0 : {len(student_feat)-placed_count}")
    print(f"  prog columns: {[c for c in student_feat.columns if c.startswith('prog_')]}")
    print(f"  enrollment lag_1y nulls: {enroll_feat['lag_1y'].isna().sum()} (expected — first year per program)")

    print("\nDone.")


if __name__ == "__main__":
    main()
