# backend/app/db.py
"""
Database connection pool and schema initialisation for Neon PostgreSQL.

The module reads DATABASE_URL from the environment.  If the variable is absent
the application raises a clear error at startup rather than silently falling
back to CSV storage.

Usage
-----
Call `init_db()` once at application startup (FastAPI lifespan).
Use `get_connection()` as a context manager to borrow a connection from the
pool for a single logical operation.

    from backend.app.db import get_connection

    with get_connection() as conn:
        conn.execute("SELECT 1")

The pool is module-level so it is shared across all requests in the same
worker process.  psycopg3 ConnectionPool is thread-safe.
"""

import os
from contextlib import contextmanager
from typing import Generator

import psycopg
from psycopg_pool import ConnectionPool

_pool: ConnectionPool | None = None

# DDL is idempotent: safe to run on every startup.
_SCHEMA_SQL = """
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
"""


def _get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Configure it with your Neon PostgreSQL connection string before starting the server."
        )
    # Neon requires SSL; enforce it unless the caller already specified sslmode.
    if "sslmode=" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}sslmode=require"
    return url


def init_db() -> None:
    """Create the connection pool and initialise the schema.

    Called once from the FastAPI lifespan handler.  Raises RuntimeError if
    DATABASE_URL is missing or the database is unreachable.
    """
    global _pool
    url = _get_database_url()
    try:
        _pool = ConnectionPool(
            conninfo=url,
            min_size=1,
            max_size=10,
            open=True,
        )
        # Run idempotent DDL to ensure tables exist.
        with _pool.connection() as conn:
            conn.execute(_SCHEMA_SQL)
            conn.commit()
    except Exception as exc:
        if _pool is not None:
            try:
                _pool.close()
            except Exception:
                pass
        _pool = None
        raise RuntimeError(
            "Failed to connect to the database or initialise the schema."
        ) from exc


def close_db() -> None:
    """Close the connection pool gracefully on application shutdown."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    """Yield a connection from the pool.

    Automatically returns the connection to the pool when the block exits.
    Rolls back any open transaction on exception so the connection is clean.
    """
    if _pool is None:
        raise RuntimeError(
            "The database connection pool is not initialised. "
            "Ensure DATABASE_URL is set and the server started correctly."
        )
    with _pool.connection() as conn:
        try:
            yield conn
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
