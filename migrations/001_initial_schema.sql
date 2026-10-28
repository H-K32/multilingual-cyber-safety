-- migrations/001_initial_schema.sql
--
-- Idempotent schema for phone-number reporting.
-- Safe to run multiple times (all statements use IF NOT EXISTS).
-- Run this once against your Neon database before starting the backend.
--
-- Usage:
--   psql "$DATABASE_URL" -f migrations/001_initial_schema.sql
--
-- The application also runs this DDL automatically on startup via db.init_db(),
-- so manual execution is only required if you need to inspect or seed the
-- schema before the first deployment.

-- ── Individual submission log ─────────────────────────────────────────────────
-- One row per community report submission.  Never deleted or overwritten.

CREATE TABLE IF NOT EXISTS phone_report_submissions (
    id                  SERIAL PRIMARY KEY,
    phone_e164          TEXT        NOT NULL,
    country_code        TEXT        NOT NULL,
    categories          TEXT[]      NOT NULL,
    evidence_note       TEXT,
    source              TEXT        NOT NULL DEFAULT 'community submission',
    verification_status TEXT        NOT NULL DEFAULT 'unverified'
                            CHECK (verification_status IN ('verified', 'unverified')),
    submitted_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_submissions_phone
    ON phone_report_submissions (phone_e164);

-- ── Aggregated summary ────────────────────────────────────────────────────────
-- One row per normalised phone number.  Updated atomically on each new report
-- via ON CONFLICT DO UPDATE (upsert) inside a transaction.

CREATE TABLE IF NOT EXISTS phone_number_summary (
    phone_e164          TEXT        PRIMARY KEY,
    country_code        TEXT        NOT NULL,
    report_count        INTEGER     NOT NULL DEFAULT 1 CHECK (report_count >= 1),
    categories          TEXT[]      NOT NULL,
    source              TEXT        NOT NULL DEFAULT 'community submission',
    first_reported      DATE        NOT NULL,
    last_reported       DATE        NOT NULL,
    verification_status TEXT        NOT NULL DEFAULT 'unverified'
                            CHECK (verification_status IN ('verified', 'unverified')),
    evidence_note       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
