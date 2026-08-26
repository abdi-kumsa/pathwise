-- Migration 003: Add is_active to users, for admin user management
-- Run with: psql $DATABASE_URL -f backend/db/migrations/003_add_user_is_active.sql
-- Safe to re-run.
--
-- schema.sql already includes this column, but that file only executes on a
-- first-ever container start (empty data volume). Existing deployments need
-- this migration. The definition here must stay in sync with the `users`
-- block in schema.sql.
--
-- Accounts are DEACTIVATED rather than deleted so the record that an account
-- existed survives. Existing rows default to active, so applying this
-- migration changes nobody's access.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

-- The admin user list filters and sorts on this, and get_current_user reads it
-- (behind a short TTL cache) on every authenticated request.
CREATE INDEX IF NOT EXISTS idx_users_is_active
    ON users (is_active);
