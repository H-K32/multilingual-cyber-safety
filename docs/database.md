# Database Architecture & Deployment Guide (Neon PostgreSQL)

## Overview

The phone number reputation and reporting module has migrated from static CSV storage to **Neon PostgreSQL**. This provides high-concurrency safety, transaction guarantees, and persistent storage of community reports and aggregated reputation summaries.

---

## Database Schema

The database uses two normalized tables:

### 1. `phone_report_submissions`
Maintains an append-only audit trail of every report submitted by users. Individual reports are never deleted or overwritten.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | `SERIAL` | `PRIMARY KEY` | Unique submission identifier |
| `phone_e164` | `TEXT` | `NOT NULL` | E.164 normalized phone number (e.g. `+251911234567`) |
| `country_code` | `TEXT` | `NOT NULL` | Country calling code (e.g. `251`) |
| `categories` | `TEXT[]` | `NOT NULL` | Reported categories (e.g. `{"scam", "phishing"}`) |
| `evidence_note` | `TEXT` | | User-submitted evidence note (sanitized, truncated to 500 chars) |
| `source` | `TEXT` | `NOT NULL DEFAULT 'community submission'` | Source identifier |
| `verification_status` | `TEXT` | `NOT NULL DEFAULT 'unverified'` | `'verified'` or `'unverified'` |
| `submitted_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Submission timestamp |

An index `idx_submissions_phone` is maintained on `phone_e164`.

### 2. `phone_number_summary`
Maintains an aggregated, deduplicated summary for each reported phone number.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `phone_e164` | `TEXT` | `PRIMARY KEY` | E.164 normalized phone number |
| `country_code` | `TEXT` | `NOT NULL` | Country calling code |
| `report_count` | `INTEGER` | `NOT NULL DEFAULT 1 CHECK (report_count >= 1)` | Total report count |
| `categories` | `TEXT[]` | `NOT NULL` | Distinct combined categories across all reports |
| `source` | `TEXT` | `NOT NULL DEFAULT 'community submission'` | Source summary |
| `first_reported` | `DATE` | `NOT NULL` | Date of earliest report |
| `last_reported` | `DATE` | `NOT NULL` | Date of most recent report |
| `verification_status` | `TEXT` | `NOT NULL DEFAULT 'unverified'` | `'verified'` or `'unverified'` |
| `evidence_note` | `TEXT` | | Most recent evidence note |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Last update timestamp |

---

## Concurrency and Atomic Upserts

Concurrent submissions for the same phone number are handled safely at the database engine level via PostgreSQL `ON CONFLICT (phone_e164) DO UPDATE` in a single transaction:

```sql
INSERT INTO phone_number_summary
    (phone_e164, country_code, report_count, categories,
     source, first_reported, last_reported,
     verification_status, evidence_note)
VALUES (%s, %s, 1, %s, 'community submission', CURRENT_DATE, CURRENT_DATE, 'unverified', %s)
ON CONFLICT (phone_e164) DO UPDATE SET
    report_count  = phone_number_summary.report_count + 1,
    categories    = (
        SELECT array_agg(DISTINCT c ORDER BY c)
        FROM unnest(phone_number_summary.categories || EXCLUDED.categories) AS c
    ),
    last_reported = CURRENT_DATE,
    evidence_note = COALESCE(EXCLUDED.evidence_note, phone_number_summary.evidence_note),
    updated_at    = now()
RETURNING
    report_count,
    (xmax::text = '0') AS is_insert;
```

This prevents lost updates, duplicate summary rows, and read-modify-write race conditions.

---

## Configuration

### Environment Variable
The backend reads the database connection string from the `DATABASE_URL` environment variable:
```
DATABASE_URL=postgresql://<username>:<password>@<ep-xxxx>.<region>.aws.neon.tech/<dbname>?sslmode=require
```

### SSL Requirement
Neon requires SSL connections. If `sslmode=` is omitted from `DATABASE_URL`, the application automatically appends `sslmode=require`.

### Startup & Failure Behavior
- If `DATABASE_URL` is missing at startup, `init_db()` raises a clear `RuntimeError`, halting startup.
- The application **never** silently falls back to CSV storage in production.
- If the database is temporarily unreachable during API requests (`/report` or `/check-number`), the backend returns an HTTP 503 error without leaking SQL errors or credentials.

---

## Deployment on Render

### Automated Initialization
During deployment on Render, FastAPI runs the `lifespan` context manager, which calls `backend.app.db.init_db()`.
`init_db()` executes idempotent DDL (`CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`).
Therefore:
1. Render automatically initializes or verifies the schema on every deployment.
2. No manual database modification is required.
3. Existing reports and summaries are preserved.

### Manual Migration Option
If you prefer to initialize the database before deploying:
```bash
psql "$DATABASE_URL" -f migrations/001_initial_schema.sql
```

---

## Legacy CSV Migration

The legacy dataset at `backend/data/reported_phone_numbers.csv` is preserved as an optional import or seeding source.

To import legacy records from the CSV file into your PostgreSQL database:
```bash
python -m backend.app.import_legacy_csv
```
This utility:
- Normalizes and validates numbers.
- Populates `phone_report_submissions`.
- Upserts `phone_number_summary`.
- Is idempotent and safe to run multiple times.

---

## Local Testing Without Exposing Credentials

Automated tests **never** connect to or modify the production Neon database.

1. **In-Memory Mock Database:**
   The test suite in `backend/tests/` uses `conftest.py` with `InMemoryTransactionalDB`. This fixture provides thread-safe transaction and rollback support locally without needing external network access.
2. **Running Tests:**
   ```bash
   pytest backend/tests
   ```
   No `DATABASE_URL` environment variable is required to run the test suite.
3. **Local Development with a Real Database (Optional):**
   If testing against a local development PostgreSQL instance:
   ```bash
   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/testdb"
   python -m uvicorn backend.app.main:app --reload
   ```
   Never commit `.env` files or credentials to Git.

