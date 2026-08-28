-- ============================================================
-- PathWise — schema-scoped bootstrap for a SHARED Postgres instance
--
-- Use this instead of schema.sql when PathWise does not own the database.
-- Render's free tier allows one Postgres instance per account, so a shared
-- deployment puts every PathWise table inside a dedicated `pathwise` schema
-- rather than `public`.
--
-- Why this file exists: schema.sql opens with
--   DROP TABLE IF EXISTS placements, job_postings, enrollments, students, users CASCADE;
-- Those are generic names. Run it against a database another project owns and
-- a collision on `users` destroys their table and everything referencing it.
-- This file never drops anything outside the pathwise schema.
--
-- Table definitions are kept identical to schema.sql — only the schema
-- qualification differs. If you change one file, change both.
--
-- Run:  psql "<external-connection-string>" -f schema_shared_instance.sql
-- ============================================================

CREATE SCHEMA IF NOT EXISTS pathwise;

SET search_path TO pathwise;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Scoped to this schema only — cannot reach another project's tables.
DROP TABLE IF EXISTS pathwise.placements   CASCADE;
DROP TABLE IF EXISTS pathwise.job_postings CASCADE;
DROP TABLE IF EXISTS pathwise.enrollments  CASCADE;
DROP TABLE IF EXISTS pathwise.students     CASCADE;
DROP TABLE IF EXISTS pathwise.users        CASCADE;


-- ── users ─────────────────────────────────────────────────
-- Authentication and role-based access control.
--
-- NOTE: this is the ONLY table on the API request path. The other four are an
-- ETL/warehouse sink — every /api/* dashboard endpoint reads parquet/CSV, not
-- Postgres. Consequence: the database being down blocks login outright.
CREATE TABLE pathwise.users (
    id               SERIAL PRIMARY KEY,
    username         VARCHAR(64)     NOT NULL UNIQUE,
    password_hash    VARCHAR(255)    NOT NULL,
    role             VARCHAR(16)     NOT NULL
                     CHECK (role IN ('ADMIN', 'STUDENT', 'MOE', 'MOL', 'UNIVERSITY')),
    display_name     VARCHAR(120)    NOT NULL,
    institution_name VARCHAR(120),   -- required for UNIVERSITY, NULL otherwise
    is_active        BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CHECK (role <> 'UNIVERSITY' OR institution_name IS NOT NULL)
);


-- ── students ──────────────────────────────────────────────
-- One row per student. Core profile used by XGBoost placement model.
CREATE TABLE pathwise.students (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(120)        NOT NULL,
    gpa                 NUMERIC(3, 2)       NOT NULL CHECK (gpa >= 0.0 AND gpa <= 4.0),
    internships         SMALLINT            NOT NULL DEFAULT 0 CHECK (internships >= 0),
    projects            SMALLINT            NOT NULL DEFAULT 0 CHECK (projects >= 0),
    communication_score SMALLINT            NOT NULL CHECK (communication_score >= 1 AND communication_score <= 10),
    program             VARCHAR(80)         NOT NULL,
    enrollment_year     SMALLINT            NOT NULL,
    created_at          TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);


-- ── enrollments ───────────────────────────────────────────
-- Aggregate enrollment counts per program per year.
-- Feeds Prophet and LSTM forecasting models.
CREATE TABLE pathwise.enrollments (
    id          SERIAL PRIMARY KEY,
    program     VARCHAR(80)     NOT NULL,
    year        SMALLINT        NOT NULL,
    count       INTEGER         NOT NULL CHECK (count >= 0),
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    UNIQUE (program, year)
);


-- ── job_postings ──────────────────────────────────────────
-- One row per job or internship posting from the labour market.
-- skills_required stored as a Postgres text array (e.g. ARRAY['Python','SQL']).
CREATE TABLE pathwise.job_postings (
    id              SERIAL PRIMARY KEY,
    company         VARCHAR(120)    NOT NULL,
    title           VARCHAR(150)    NOT NULL,
    location        VARCHAR(100)    NOT NULL,
    skills_required TEXT[]          NOT NULL DEFAULT '{}',
    salary_min      NUMERIC(10, 2)  CHECK (salary_min >= 0),
    salary_max      NUMERIC(10, 2)  CHECK (salary_max >= 0),
    source          VARCHAR(80),
    posted_date     DATE            NOT NULL,
    is_internship   BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CHECK (salary_max IS NULL OR salary_min IS NULL OR salary_max >= salary_min)
);


-- ── placements ────────────────────────────────────────────
-- Outcome record for each student after graduation.
-- placement_status: 'Matched' | 'Overeducated' | 'Undereducated'
CREATE TABLE pathwise.placements (
    id                  SERIAL PRIMARY KEY,
    student_id          INTEGER         NOT NULL REFERENCES pathwise.students(id) ON DELETE CASCADE,
    company             VARCHAR(120),
    role                VARCHAR(150),
    salary              NUMERIC(10, 2)  CHECK (salary >= 0),
    time_to_hire        SMALLINT        CHECK (time_to_hire >= 0),   -- days from graduation to offer
    placed              BOOLEAN         NOT NULL DEFAULT FALSE,
    placement_status    VARCHAR(20)     CHECK (placement_status IN ('Matched', 'Overeducated', 'Undereducated')),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);


-- ── Indexes ───────────────────────────────────────────────
CREATE INDEX idx_students_program         ON pathwise.students (program);
CREATE INDEX idx_students_enrollment_year ON pathwise.students (enrollment_year);

CREATE INDEX idx_enrollments_program      ON pathwise.enrollments (program);
CREATE INDEX idx_enrollments_year         ON pathwise.enrollments (year);

CREATE INDEX idx_job_postings_location    ON pathwise.job_postings (location);
CREATE INDEX idx_job_postings_posted_date ON pathwise.job_postings (posted_date);
CREATE INDEX idx_job_postings_company     ON pathwise.job_postings (company);
CREATE INDEX idx_job_postings_internship  ON pathwise.job_postings (is_internship);

CREATE INDEX idx_placements_student_id    ON pathwise.placements (student_id);
CREATE INDEX idx_placements_placed        ON pathwise.placements (placed);
CREATE INDEX idx_placements_status        ON pathwise.placements (placement_status);

CREATE INDEX idx_users_role               ON pathwise.users (role);
