"""
Phase 2 — Step 4
Data quality check: connects to Postgres and prints a summary report for all 4 tables.

Reports per table:
  - Row count
  - Null count per column
  - Numeric columns: min, max, mean
  - Categorical columns: top 5 value frequencies
  - Placements: distribution of placement_status and placed counts

Run from the repo root:
  python data/data_quality_check.py

Or from inside Docker backend container:
  docker compose exec backend python ../data/data_quality_check.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).parent.parent
ENV_FILE = ROOT / ".env"

load_dotenv(ENV_FILE)

# ── Connection (same helper as load_to_db.py) ─────────────────────────────────

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


# ── Report helpers ────────────────────────────────────────────────────────────

def print_separator():
    print("=" * 70)


def report_table(conn, table_name: str) -> None:
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)

    print_separator()
    print(f"TABLE: {table_name} ({len(df)} rows)")
    print_separator()

    # Null counts
    nulls = df.isnull().sum()
    if nulls.sum() > 0:
        print("\nNull counts:")
        for col, count in nulls[nulls > 0].items():
            print(f"  {col:30} {count:5} nulls")
    else:
        print("\nNo null values found.")

    # Numeric columns
    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols) > 0:
        print("\nNumeric columns:")
        for col in numeric_cols:
            vals = df[col].dropna()
            if len(vals) > 0:
                print(f"  {col:30} min={vals.min():.2f}  max={vals.max():.2f}  mean={vals.mean():.2f}")

    # Categorical columns (top 5 frequencies)
    cat_cols = df.select_dtypes(include=["object", "bool"]).columns
    if len(cat_cols) > 0:
        print("\nCategorical columns (top 5):")
        for col in cat_cols:
            top5 = df[col].value_counts().head(5)
            items = ", ".join([f"{k} ({v})" for k, v in top5.items()])
            print(f"  {col:30} {items}")

    # Special handling for placements table
    if table_name == "placements":
        print("\nPlacement distribution:")
        placed_counts = df["placed"].value_counts()
        for val, count in placed_counts.items():
            label = "Placed" if val else "Not Placed"
            pct = count / len(df) * 100
            print(f"  {label:15} {count:5} ({pct:5.1f}%)")

        if "placement_status" in df.columns:
            print("\nPlacement status distribution:")
            status_counts = df["placement_status"].value_counts()
            for status, count in status_counts.items():
                pct = count / len(df) * 100
                print(f"  {str(status):20} {count:5} ({pct:5.1f}%)")

    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\nConnecting to database ...")
    try:
        conn = get_conn()
    except Exception as exc:
        print(f"  ERROR: could not connect — {exc}")
        print("  Make sure Docker is running and the database is up.")
        sys.exit(1)
    print("  Connected.\n")

    tables = ["students", "job_postings", "enrollments", "placements"]

    for table in tables:
        report_table(conn, table)

    conn.close()

    print_separator()
    print("Data quality check complete.")
    print_separator()


if __name__ == "__main__":
    main()
