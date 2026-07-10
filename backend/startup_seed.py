"""
Idempotent startup seeder.
Called from main.py on FastAPI startup.

Checks whether the students table is empty and, if so, seeds all 4 tables
from the CSV files in data/. Safe to call on every restart — exits silently
when data already exists.

Inside Docker the volume mounts are:
  ./backend  -> /app      (this file lives here)
  ./data     -> /data     (CSV sources)
  ./Assets   -> /Assets   (raw enrollment + job CSV files)
"""
import logging
import os
import sys
from pathlib import Path

log = logging.getLogger(__name__)

# /app is backend; parent is project root inside Docker
_ROOT = Path(__file__).resolve().parent.parent


def _student_count() -> int:
    """Return the row count in students, or -1 if the table is unreachable."""
    import psycopg2

    dsn = os.getenv("DATABASE_URL") or (
        "postgresql://"
        f"{os.getenv('DB_USER', 'pathwise_user')}:"
        f"{os.getenv('DB_PASSWORD', 'pathwise_pass')}@"
        f"{os.getenv('DB_HOST', 'db')}:"
        f"{os.getenv('DB_PORT', '5432')}/"
        f"{os.getenv('DB_NAME', 'pathwise_db')}"
    )
    try:
        conn = psycopg2.connect(dsn)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM students")
            count = cur.fetchone()[0]
        conn.close()
        return int(count)
    except Exception as exc:
        log.warning("Seed check — could not query students table: %s", exc)
        return -1


def seed_if_empty() -> None:
    """Seed all 4 database tables from CSVs if the database is empty."""
    count = _student_count()

    if count < 0:
        log.warning("Startup seed skipped — database unreachable.")
        return

    if count > 0:
        log.info("Startup seed skipped — database already contains %d students.", count)
        return

    log.info("Students table is empty — seeding from CSV files ...")

    # load_to_db.py lives in data/ which Docker mounts at /data
    data_dir = str(_ROOT / "data")
    if data_dir not in sys.path:
        sys.path.insert(0, data_dir)

    try:
        from load_to_db import (  # noqa: PLC0415
            get_conn,
            load_enrollments,
            load_job_postings,
            load_students,
            load_placements,
        )

        conn = get_conn()
        n = load_enrollments(conn);  log.info("  enrollments  : %d rows", n)
        n = load_job_postings(conn); log.info("  job_postings : %d rows", n)
        n = load_students(conn);     log.info("  students     : %d rows", n)
        n = load_placements(conn);   log.info("  placements   : %d rows", n)
        conn.close()
        log.info("Startup seed complete — all 4 tables populated.")

    except Exception as exc:
        # Non-fatal: parquet-backed ML endpoints work without Postgres data.
        log.error("Startup seed failed: %s", exc)
