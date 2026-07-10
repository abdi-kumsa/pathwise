"""
Phase 2 — Step 2
Idempotent ETL loader: truncates all 4 tables then reloads from source files.

Load order (respects FK constraints):
  1. enrollments   <- Assets/student_enrollment_forecasting_data.csv
  2. job_postings  <- Assets/job_market_forecasting_data.csv
  3. students      <- data/mock/students.csv
  4. placements    <- data/mock/placements.csv

Run from the repo root:
  python data/load_to_db.py

If running outside Docker, DB_HOST='db' is auto-swapped to 'localhost'.
"""

import os
import random
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

random.seed(42)

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
ENV_FILE   = ROOT / ".env"
ASSETS     = ROOT / "Assets"
MOCK       = ROOT / "data" / "mock"

ENROLLMENT_CSV  = ASSETS / "student_enrollment_forecasting_data.csv"
JOB_CSV         = ASSETS / "job_market_forecasting_data.csv"
STUDENTS_CSV    = MOCK   / "students.csv"
PLACEMENTS_CSV  = MOCK   / "placements.csv"

# ── Connection ─────────────────────────────────────────────────────────────────
load_dotenv(ENV_FILE)

def _build_dsn() -> str:
    """Return a DSN that works both inside and outside Docker."""
    url = os.getenv("DATABASE_URL", "")
    if url:
        # Use as-is — Docker sets it correctly for the container environment
        return url
    # Fallback: build from individual vars
    user   = os.getenv("DB_USER",     "pathwise_user")
    pwd    = os.getenv("DB_PASSWORD", "pathwise_pass")
    host   = os.getenv("DB_HOST",     "db")
    port   = os.getenv("DB_PORT",     "5432")
    dbname = os.getenv("DB_NAME",     "pathwise_db")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{dbname}"


def get_conn():
    dsn = _build_dsn()
    return psycopg2.connect(dsn)


# ── Lookup tables ──────────────────────────────────────────────────────────────

SKILL_MAP = {
    "Software Engineering":  ["Python", "JavaScript", "Git", "REST APIs", "SQL"],
    "AI":                    ["Python", "TensorFlow", "PyTorch", "SHAP", "Pandas"],
    "Data & Analytics":      ["SQL", "Python", "Tableau", "Excel", "dbt"],
    "Cloud Infrastructure":  ["AWS", "Azure", "Kubernetes", "Terraform", "Docker"],
    "DevOps":                ["Docker", "Kubernetes", "CI/CD", "Linux", "Terraform"],
    "Business Intelligence": ["Power BI", "SQL", "Tableau", "Excel", "DAX"],
    "Cybersecurity":         ["SIEM", "Penetration Testing", "Network Security", "Python", "Compliance"],
    "Product Management":    ["Agile", "JIRA", "Roadmapping", "SQL", "Stakeholder Management"],
    "UX Design":             ["Figma", "User Research", "Prototyping", "Accessibility", "Design Systems"],
}

COMPANY_MAP = {
    "Technology":    ["Google", "Microsoft", "Apple", "Meta", "Salesforce"],
    "Finance":       ["JPMorgan Chase", "Goldman Sachs", "Morgan Stanley", "Visa", "Stripe"],
    "Healthcare":    ["Johnson & Johnson", "UnitedHealth Group", "Epic Systems", "Medtronic", "Abbott"],
    "Consulting":    ["McKinsey & Company", "Deloitte", "Accenture", "PwC", "KPMG"],
    "Manufacturing": ["Intel", "Bosch", "Honeywell", "General Electric", "Caterpillar"],
    "Education":     ["Coursera", "Pearson", "McGraw-Hill", "Cengage", "Chegg"],
    "Energy":        ["Chevron", "ExxonMobil", "Shell", "BP", "NextEra Energy"],
    "Retail":        ["Amazon", "Walmart", "Target", "Best Buy", "Costco"],
    "Government":    ["Booz Allen Hamilton", "Leidos", "SAIC", "Raytheon Technologies", "Lockheed Martin"],
}


# ── Step 0 — Truncate ─────────────────────────────────────────────────────────

def truncate_all(conn) -> None:
    """Truncate in reverse FK order so constraints are not violated."""
    with conn.cursor() as cur:
        cur.execute("""
            TRUNCATE TABLE placements, students, job_postings, enrollments
            RESTART IDENTITY CASCADE;
        """)
    conn.commit()
    print("  Truncated all 4 tables (RESTART IDENTITY CASCADE).")


# ── Step 1 — Enrollments ──────────────────────────────────────────────────────

def load_enrollments(conn) -> int:
    df = pd.read_csv(ENROLLMENT_CSV, usecols=["program_name", "year", "enrollment_count"])
    df = df.rename(columns={"program_name": "program", "enrollment_count": "count"})

    # Deduplicate: if same (program, year) appears multiple times, take the mean
    df = (
        df.groupby(["program", "year"], as_index=False)["count"]
        .mean()
        .assign(count=lambda x: x["count"].round().astype(int))
    )

    rows = list(df.itertuples(index=False, name=None))   # (program, year, count)

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO enrollments (program, year, count)
            VALUES %s
            ON CONFLICT (program, year) DO UPDATE
                SET count = EXCLUDED.count
            """,
            rows,
        )
    conn.commit()
    return len(rows)


# ── Step 2 — Job Postings ─────────────────────────────────────────────────────

def load_job_postings(conn) -> int:
    df = pd.read_csv(JOB_CSV, usecols=[
        "job_title", "skill_cluster", "posting_industry",
        "metro_area", "avg_salary_usd", "time_to_fill_days", "date",
    ])

    rows = []
    for _, r in df.iterrows():
        cluster  = str(r["skill_cluster"]).strip()
        industry = str(r["posting_industry"]).strip()
        skills   = SKILL_MAP.get(cluster, ["Communication", "Problem Solving"])
        company  = random.choice(COMPANY_MAP.get(industry, ["General Corp"]))
        sal      = float(r["avg_salary_usd"])
        sal_min  = round(sal * 0.85, 2)
        sal_max  = round(sal * 1.15, 2)

        # Convert YYYY-MM to YYYY-MM-01 for DATE type
        date_str = str(r["date"]).strip()
        if len(date_str) == 7:  # "2024-04"
            date_str += "-01"

        rows.append((
            company,                          # company
            str(r["job_title"]).strip(),      # title
            str(r["metro_area"]).strip(),     # location
            skills,                           # skills_required (list → psycopg2 array)
            sal_min,                          # salary_min
            sal_max,                          # salary_max
            "Job Board",                      # source
            date_str,                         # posted_date
            False,                            # is_internship
        ))

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO job_postings
              (company, title, location, skills_required,
               salary_min, salary_max, source, posted_date, is_internship)
            VALUES %s
            """,
            rows,
        )
    conn.commit()
    return len(rows)


# ── Step 3 — Students ─────────────────────────────────────────────────────────

def load_students(conn) -> int:
    df = pd.read_csv(STUDENTS_CSV)
    rows = [
        (
            str(r["name"]),
            float(r["gpa"]),
            int(r["internships"]),
            int(r["projects"]),
            int(r["communication_score"]),
            str(r["program"]),
            int(r["enrollment_year"]),
        )
        for _, r in df.iterrows()
    ]

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO students
              (name, gpa, internships, projects,
               communication_score, program, enrollment_year)
            VALUES %s
            """,
            rows,
        )
    conn.commit()
    return len(rows)


# ── Step 4 — Placements ───────────────────────────────────────────────────────

def _none_if_blank(val):
    """Return None for empty/NaN values so psycopg2 writes NULL."""
    if val is None:
        return None
    s = str(val).strip()
    return None if s == "" or s.lower() == "nan" else s


def load_placements(conn) -> int:
    df = pd.read_csv(PLACEMENTS_CSV, dtype=str)

    rows = []
    for _, r in df.iterrows():
        placed = r["placed"].strip().lower() == "true"
        rows.append((
            int(r["student_id"]),
            placed,
            _none_if_blank(r["placement_status"]),
            _none_if_blank(r["company"]),
            _none_if_blank(r["role"]),
            float(r["salary"]) if _none_if_blank(r["salary"]) else None,
            int(r["time_to_hire"]) if _none_if_blank(r["time_to_hire"]) else None,
        ))

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO placements
              (student_id, placed, placement_status,
               company, role, salary, time_to_hire)
            VALUES %s
            """,
            rows,
        )
    conn.commit()
    return len(rows)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Connecting to database ...")
    conn = get_conn()
    print("  Connected.")

    print("\nTruncating existing data ...")
    truncate_all(conn)

    print("\nLoading enrollments ...")
    n = load_enrollments(conn)
    print(f"  OK enrollments  loaded: {n} rows")

    print("\nLoading job_postings ...")
    n = load_job_postings(conn)
    print(f"  OK job_postings loaded: {n} rows")

    print("\nLoading students ...")
    n = load_students(conn)
    print(f"  OK students     loaded: {n} rows")

    print("\nLoading placements ...")
    n = load_placements(conn)
    print(f"  OK placements   loaded: {n} rows")

    conn.close()
    print("\nDone. All 4 tables loaded successfully.")


if __name__ == "__main__":
    main()
