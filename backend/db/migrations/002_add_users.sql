-- Migration 002: Add the users table for role-based access control
-- Run with: psql $DATABASE_URL -f backend/db/migrations/002_add_users.sql
-- All statements use IF NOT EXISTS so re-running is safe.
--
-- schema.sql already creates this table, but that file only runs on a
-- first-ever container start (empty data volume). Existing deployments need
-- this migration instead. The definition here must stay in sync with the
-- `users` block in schema.sql.
--
-- Rows are seeded separately by backend/startup_seed.py::seed_users_if_empty,
-- which hashes DEMO_PASSWORD with bcrypt. This file creates structure only —
-- no credentials are committed.

CREATE TABLE IF NOT EXISTS users (
    id               SERIAL PRIMARY KEY,
    username         VARCHAR(64)     NOT NULL UNIQUE,
    password_hash    VARCHAR(255)    NOT NULL,
    role             VARCHAR(16)     NOT NULL
                     CHECK (role IN ('ADMIN', 'STUDENT', 'MOE', 'MOL', 'UNIVERSITY')),
    display_name     VARCHAR(120)    NOT NULL,
    institution_name VARCHAR(120),
    created_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- A UNIVERSITY user must be scoped to an institution, or row-level
    -- scoping in institution_service has nothing to filter on.
    CHECK (role <> 'UNIVERSITY' OR institution_name IS NOT NULL)
);

-- Every authenticated request resolves the caller's role.
CREATE INDEX IF NOT EXISTS idx_users_role
    ON users (role);
