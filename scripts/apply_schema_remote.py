"""
Apply a schema file to a remote Postgres over psycopg2 — a stand-in for
`psql -f` on machines without the psql client installed.

Usage:
    python scripts/apply_schema_remote.py "<external-database-url>"

    # non-default schema file
    python scripts/apply_schema_remote.py "<url>" backend/db/schema.sql

Defaults to backend/db/schema_shared_instance.sql, which confines every
statement to a dedicated `pathwise` schema. Use that one when the database
is shared with another project: plain schema.sql opens with
DROP TABLE IF EXISTS users CASCADE, and `users` is a name another project
may well be using.

Pass the EXTERNAL connection string (from Render's Connect panel) — the
internal one only resolves from inside Render's network.
"""
import sys
from pathlib import Path

import psycopg2

_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_SCHEMA = _ROOT / "backend" / "db" / "schema_shared_instance.sql"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    dsn = sys.argv[1]
    schema_path = Path(sys.argv[2]) if len(sys.argv) > 2 else _DEFAULT_SCHEMA

    if not schema_path.is_absolute():
        schema_path = _ROOT / schema_path

    if not schema_path.exists():
        print(f"[fail] schema file not found: {schema_path}")
        return 1

    sql = schema_path.read_text(encoding="utf-8")
    print(f"Applying {schema_path.name} ({len(sql):,} bytes)")

    # Warn rather than block: dropping unqualified table names against a
    # database you share is how another project loses its `users` table.
    if "schema_shared_instance" not in schema_path.name:
        print(
            "[warn] This file may DROP unqualified table names. Only continue "
            "if PathWise owns this database exclusively."
        )

    conn = None
    try:
        conn = psycopg2.connect(dsn)
        # One transaction: a failure halfway leaves nothing behind.
        with conn, conn.cursor() as cur:
            cur.execute(sql)
        print("[ok] Schema applied.")

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_name IN
                    ('users','students','enrollments','job_postings','placements')
                ORDER BY table_schema, table_name
                """
            )
            rows = cur.fetchall()

        if rows:
            print(f"\nPathWise tables now present ({len(rows)}):")
            for schema, table in rows:
                print(f"  {schema}.{table}")
        else:
            print("[warn] No PathWise tables found after apply — check the output above.")

        return 0

    except psycopg2.Error as exc:
        print(f"[fail] {exc}")
        return 1
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
