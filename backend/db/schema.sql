-- ============================================================
-- PathWise — PostgreSQL Database Schema
-- Run: psql -U <user> -d <db> -f schema.sql
-- ============================================================

-- ── Extensions ────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Drop tables in dependency order (safe re-run) ─────────
DROP TABLE IF EXISTS expert_validations CASCADE;
DROP TABLE IF EXISTS ahp_matrices CASCADE;
DROP TABLE IF EXISTS scenarios CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS placements CASCADE;
DROP TABLE IF EXISTS job_postings CASCADE;
DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS users CASCADE;


-- ── users ─────────────────────────────────────────────────
-- Authentication and role-based access control.
--
-- NOTE: `users` plus the four governance tables at the bottom of this file
-- (audit_log, scenarios, ahp_matrices, expert_validations) are on the API
-- request path. The warehouse tables (students, enrollments, job_postings,
-- placements) remain an ETL sink — every /api/* dashboard endpoint still
-- reads parquet/CSV, not those four. See docs/TECHNICAL.md §4.
--
-- institution_name scopes a UNIVERSITY user to their own institution's rows.
-- It is read from the JWT, never from a query parameter, so one university
-- cannot request another's data.
-- is_active: accounts are deactivated rather than deleted, so the record that
-- an account existed survives. An inactive user cannot log in, and their
-- existing token stops working within the status-cache TTL (see
-- services/auth_service.py).
CREATE TABLE users (
    id               SERIAL PRIMARY KEY,
    username         VARCHAR(64)     NOT NULL UNIQUE,
    password_hash    VARCHAR(255)    NOT NULL,
    role             VARCHAR(16)     NOT NULL
                     CHECK (role IN ('ADMIN', 'STUDENT', 'MOE', 'MOL', 'UNIVERSITY')),
    display_name     VARCHAR(120)    NOT NULL,
    institution_name VARCHAR(120),   -- required for UNIVERSITY, NULL otherwise
    is_active        BOOLEAN         NOT NULL DEFAULT TRUE,
    cross_institution BOOLEAN        NOT NULL DEFAULT FALSE,
    program          VARCHAR(120),
    field            VARCHAR(120),
    enrollment_year  SMALLINT,
    created_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CHECK (role <> 'UNIVERSITY' OR institution_name IS NOT NULL)
);


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

-- Users
-- username already has a UNIQUE index from the constraint; role is indexed
-- because every authenticated request filters on it.
CREATE INDEX idx_users_role               ON users (role);

-- ── audit_log / scenarios / ahp_matrices / expert_validations ──
-- Wave 1.5 governance tables. Intentionally on the request path (Wave 7
-- widgets W.ADM.05–08 and DOC1 procedure steps 2 and 7). Dashboard analytics
-- still read parquet/CSV.
CREATE TABLE audit_log (
    id          SERIAL PRIMARY KEY,
    actor       VARCHAR(64)     NOT NULL,
    role        VARCHAR(16),
    action      VARCHAR(64)     NOT NULL,
    resource    VARCHAR(255),
    payload     JSONB,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_log_actor       ON audit_log (actor);
CREATE INDEX idx_audit_log_created_at  ON audit_log (created_at);

CREATE TABLE scenarios (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(120)    NOT NULL,
    owner         VARCHAR(64)     NOT NULL,
    assumptions   JSONB           NOT NULL,
    status        VARCHAR(24)     NOT NULL DEFAULT 'draft'
                  CHECK (status IN ('draft', 'submitted', 'approved', 'rejected', 'archived')),
    created_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_scenarios_owner  ON scenarios (owner);
CREATE INDEX idx_scenarios_status ON scenarios (status);

CREATE TABLE ahp_matrices (
    id                    SERIAL PRIMARY KEY,
    model                 VARCHAR(8)      NOT NULL
                          CHECK (model IN ('M1', 'M2', 'M3')),
    matrix                JSONB           NOT NULL,
    consistency_ratio     NUMERIC(8, 4),
    created_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TABLE expert_validations (
    id            SERIAL PRIMARY KEY,
    spec_id       VARCHAR(32)     NOT NULL,
    expert_role   VARCHAR(64)     NOT NULL,
    verdict       VARCHAR(24)     NOT NULL
                  CHECK (verdict IN ('accepted', 'revision', 'rejected')),
    notes         TEXT,
    created_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_expert_validations_spec ON expert_validations (spec_id);

