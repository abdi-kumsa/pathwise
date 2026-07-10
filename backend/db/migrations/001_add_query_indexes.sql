-- Migration 001: Add indexes on commonly queried columns
-- Run with: psql $DATABASE_URL -f backend/db/migrations/001_add_query_indexes.sql
-- All statements use IF NOT EXISTS so re-running is safe.

-- job_postings: filter/group by location (regional hiring endpoint)
CREATE INDEX IF NOT EXISTS idx_job_postings_location
    ON job_postings (location);

-- job_postings: range queries and sorting by date (demand forecast endpoint)
CREATE INDEX IF NOT EXISTS idx_job_postings_posted_date
    ON job_postings (posted_date);

-- students: filter by program (enrollment forecast, placement-by-stream endpoints)
CREATE INDEX IF NOT EXISTS idx_students_program
    ON students (program);

-- placements: join back to students (placement prediction, placement-by-stream endpoints)
-- PostgreSQL does NOT automatically index foreign key columns.
CREATE INDEX IF NOT EXISTS idx_placements_student_id
    ON placements (student_id);
