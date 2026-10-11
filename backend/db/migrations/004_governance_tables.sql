-- Migration 004: governance tables that are on the API request path.
-- Run with: psql $DATABASE_URL -f backend/db/migrations/004_governance_tables.sql
-- Safe to re-run.
--
-- Wave 1.5. Until now `users` was the only Postgres table the API read.
-- These four tables are an intentional exception, documented in
-- docs/TECHNICAL.md §4 and schema.sql: audit_log, scenarios, ahp_matrices,
-- expert_validations. Dashboard parquet/CSV reads are unchanged.
--
-- schema.sql includes the same definitions for a first-ever container start.

CREATE TABLE IF NOT EXISTS audit_log (
    id          SERIAL PRIMARY KEY,
    actor       VARCHAR(64)     NOT NULL,
    role        VARCHAR(16),
    action      VARCHAR(64)     NOT NULL,
    resource    VARCHAR(255),
    payload     JSONB,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor ON audit_log (actor);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log (created_at);

CREATE TABLE IF NOT EXISTS scenarios (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(120)    NOT NULL,
    owner         VARCHAR(64)     NOT NULL,
    assumptions   JSONB           NOT NULL,
    status        VARCHAR(24)     NOT NULL DEFAULT 'draft',
    created_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CHECK (status IN ('draft', 'submitted', 'approved', 'rejected', 'archived'))
);
CREATE INDEX IF NOT EXISTS idx_scenarios_owner ON scenarios (owner);
CREATE INDEX IF NOT EXISTS idx_scenarios_status ON scenarios (status);

CREATE TABLE IF NOT EXISTS ahp_matrices (
    id                    SERIAL PRIMARY KEY,
    model                 VARCHAR(8)      NOT NULL,
    matrix                JSONB           NOT NULL,
    consistency_ratio     NUMERIC(8, 4),
    created_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CHECK (model IN ('M1', 'M2', 'M3'))
);

CREATE TABLE IF NOT EXISTS expert_validations (
    id            SERIAL PRIMARY KEY,
    spec_id       VARCHAR(32)     NOT NULL,
    expert_role   VARCHAR(64)     NOT NULL,
    verdict       VARCHAR(24)     NOT NULL,
    notes         TEXT,
    created_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CHECK (verdict IN ('accepted', 'revision', 'rejected'))
);
CREATE INDEX IF NOT EXISTS idx_expert_validations_spec ON expert_validations (spec_id);
