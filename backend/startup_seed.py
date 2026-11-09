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


# ── Demo users ────────────────────────────────────────────────────────────────
# One account per role so the platform is demonstrable immediately after
# `docker compose up`. Passwords are read from DEMO_PASSWORD and hashed with
# bcrypt at seed time — no credential is stored in source control.
#
# These are DEMO accounts. Rotate DEMO_PASSWORD and re-seed before exposing
# this deployment to anyone.
_DEMO_USERS = [
    # (username,     role,          display_name,             institution)
    ("admin",        "ADMIN",       "Platform Administrator",  None),
    ("student",      "STUDENT",     "Demo Student",            "Addis Ababa University"),
    ("moe",          "MOE",         "Ministry of Education",   None),
    ("mol",          "MOL",         "Ministry of Labour",      None),
    ("university",   "UNIVERSITY",  "Addis Ababa University",  "Addis Ababa University"),
]


def seed_users_if_empty() -> None:
    """Create the five demo accounts if the users table is empty.

    Idempotent: exits silently once any user exists, so a password changed
    through the app is never overwritten on restart.
    """
    from services.auth_service import IS_DEV, hash_password

    # The well-known fallback is for local development only. A real deployment
    # with no DEMO_PASSWORD gets no demo accounts rather than five accounts
    # (one of them ADMIN) behind a password published in the README.
    password = (os.getenv("DEMO_PASSWORD") or "").strip()
    if not password:
        if not IS_DEV:
            log.error(
                "User seed skipped — DEMO_PASSWORD is not set and ENV is not dev. "
                "Set DEMO_PASSWORD to create the first administrator."
            )
            return
        password = "pathwise123"
    elif not IS_DEV and password == "pathwise123":
        log.error(
            "User seed skipped — DEMO_PASSWORD is the published demo value. "
            "Choose a private password for a non-dev deployment."
        )
        return

    try:
        from db.database import SessionLocal
        from models.user import User
    except Exception as exc:
        log.error("User seed skipped — could not import the ORM layer: %s", exc)
        return

    session = None
    try:
        session = SessionLocal()
        existing = session.query(User).count()

        if existing > 0:
            log.info("User seed skipped — %d account(s) already present.", existing)
            return

        log.info("Users table is empty — creating %d demo accounts ...", len(_DEMO_USERS))
        for username, role, display_name, institution in _DEMO_USERS:
            kwargs = dict(
                username         = username,
                password_hash    = hash_password(password),
                role             = role,
                display_name     = display_name,
                institution_name = institution,
            )
            if username == "student":
                kwargs.update(
                    program="BSc Civil Engineering",
                    field="Engineering & Technology",
                    enrollment_year=2023,
                    cross_institution=False,
                )
            session.add(User(**kwargs))
        session.commit()

        log.info(
            "Demo accounts created: %s (password from DEMO_PASSWORD)",
            ", ".join(u[0] for u in _DEMO_USERS),
        )

    except Exception as exc:
        # Non-fatal at startup, but login will not work until this succeeds.
        if session is not None:
            session.rollback()
        log.error("User seed failed — login will be unavailable: %s", exc)
    finally:
        if session is not None:
            session.close()


def apply_wave5_user_columns() -> None:
    """Add scope columns on an existing volume (schema.sql only runs once)."""
    from sqlalchemy import text
    from db.database import engine

    stmts = (
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS cross_institution BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS program VARCHAR(120)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS field VARCHAR(120)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS enrollment_year SMALLINT",
        # Phase 3.6 — session revocation.
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0",
        # Phase 4.1 — expert validation provenance.
        "ALTER TABLE expert_validations ADD COLUMN IF NOT EXISTS expert_name VARCHAR(120)",
        "ALTER TABLE expert_validations ADD COLUMN IF NOT EXISTS organisation VARCHAR(160)",
        "ALTER TABLE expert_validations ADD COLUMN IF NOT EXISTS recorded_by VARCHAR(64)",
        "ALTER TABLE expert_validations ADD COLUMN IF NOT EXISTS source VARCHAR(16) NOT NULL DEFAULT 'recorded'",
        # Rows created by the earlier seeder carry one of its fixed notes.
        "UPDATE expert_validations SET source = 'seeded' WHERE notes IN ("
        "'Enrolment history is the right demand spine.', "
        "'Quota tables match placement practice.', "
        "'Formal/informal split needs a ministry refresh.', "
        "'Labour history grain is usable for a simulated series.', "
        "'Macro-regional context is a collection priority, not a weight.', "
        "'FDI parks are leading indicators, displayed separately.')",
    )
    try:
        with engine.begin() as conn:
            for stmt in stmts:
                conn.execute(text(stmt))
        log.info("Wave 5 user-scope columns are present.")
    except Exception as exc:
        log.error("Wave 5 user-scope migration failed: %s", exc)


def patch_demo_student_profile() -> None:
    """Keep the demo student on the Ethiopia join backbone even if the row
    was seeded before Wave 5. Does not reset passwords or other accounts."""
    try:
        from db.database import SessionLocal
        from models.user import User
    except Exception as exc:
        log.error("Demo student patch skipped: %s", exc)
        return

    session = SessionLocal()
    try:
        row = session.query(User).filter(User.username == "student").first()
        if row is None:
            return
        row.institution_name = "Addis Ababa University"
        row.program = "BSc Civil Engineering"
        row.field = "Engineering & Technology"
        row.enrollment_year = 2023
        if getattr(row, "cross_institution", None) is None:
            row.cross_institution = False
        session.commit()
        log.info("Demo student profile: AAU · BSc Civil Engineering.")
    except Exception as exc:
        session.rollback()
        log.error("Demo student patch failed: %s", exc)
    finally:
        session.close()
