-- Migration 005: student profile columns and CROSS_INSTITUTION grant.
-- Safe to re-run. Wave 5.0.
--
-- Demo student profile is patched at startup (startup_seed.py). The grant
-- defaults to false; the demo university account stays own-institution only.

ALTER TABLE users ADD COLUMN IF NOT EXISTS cross_institution BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS program VARCHAR(120);
ALTER TABLE users ADD COLUMN IF NOT EXISTS field VARCHAR(120);
ALTER TABLE users ADD COLUMN IF NOT EXISTS enrollment_year SMALLINT;
