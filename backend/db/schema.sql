-- ============================================================
-- PathWise — PostgreSQL Database Schema
-- Run: psql -U <user> -d <db> -f schema.sql
-- ============================================================

-- ── Extensions ────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Drop tables in dependency order (safe re-run) ─────────
DROP TABLE IF EXISTS placements CASCADE;
DROP TABLE IF EXISTS job_postings CASCADE;
DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS students CASCADE;


-- ── students ──────────────────────────────────────────────
-- One row per student. Core profile used by XGBoost placement model.
CREATE TABLE students (
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
CREATE TABLE enrollments (
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
CREATE TABLE job_postings (
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
CREATE TABLE placements (
    id                  SERIAL PRIMARY KEY,
    student_id          INTEGER         NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    company             VARCHAR(120),
    role                VARCHAR(150),
    salary              NUMERIC(10, 2)  CHECK (salary >= 0),
    time_to_hire        SMALLINT        CHECK (time_to_hire >= 0),   -- days from graduation to offer
    placed              BOOLEAN         NOT NULL DEFAULT FALSE,
    placement_status    VARCHAR(20)     CHECK (placement_status IN ('Matched', 'Overeducated', 'Undereducated')),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);


-- ── Indexes ───────────────────────────────────────────────
-- Students
CREATE INDEX idx_students_program         ON students (program);
CREATE INDEX idx_students_enrollment_year ON students (enrollment_year);

-- Enrollments
CREATE INDEX idx_enrollments_program      ON enrollments (program);
CREATE INDEX idx_enrollments_year         ON enrollments (year);

-- Job postings
CREATE INDEX idx_job_postings_location    ON job_postings (location);
CREATE INDEX idx_job_postings_posted_date ON job_postings (posted_date);
CREATE INDEX idx_job_postings_company     ON job_postings (company);
CREATE INDEX idx_job_postings_internship  ON job_postings (is_internship);

-- Placements
CREATE INDEX idx_placements_student_id    ON placements (student_id);
CREATE INDEX idx_placements_placed        ON placements (placed);
CREATE INDEX idx_placements_status        ON placements (placement_status);
