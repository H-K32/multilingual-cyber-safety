# backend/tests/conftest.py
"""Shared pytest fixtures and in-memory transactional database for tests.

Provides an isolated, concurrent-safe in-memory database mock so tests never
modify or require a live production database.
"""

import threading
from contextlib import contextmanager
from datetime import date
from typing import Generator, List, Dict, Any

import pytest

from backend.app import db, phone_reputation, main


class FakeCursor:
    """Cursor returned by FakeConnection.execute()."""

    def __init__(self, rows: list):
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows


class FakeConnection:
    """Connection with transaction management and rollback capability."""

    def __init__(self, fake_db: "InMemoryTransactionalDB"):
        self.db = fake_db
        self.uncommitted_submissions: List[Dict[str, Any]] = []
        self.uncommitted_summary_ops: List[Dict[str, Any]] = []
        self.in_transaction = True

    def execute(self, sql: str, params: tuple = ()) -> FakeCursor:
        if self.db.simulate_error:
            raise RuntimeError("Simulated database connection error.")

        sql_stripped = " ".join(sql.split()).upper()

        # ── INSERT INTO phone_report_submissions ──────────────────────────
        if "INSERT INTO PHONE_REPORT_SUBMISSIONS" in sql_stripped:
            phone_e164, country_code, categories, evidence_note = params[:4]
            source = params[4] if len(params) > 4 else "community submission"
            v_status = params[5] if len(params) > 5 else "unverified"
            self.uncommitted_submissions.append({
                "phone_e164": phone_e164,
                "country_code": country_code,
                "categories": list(categories),
                "evidence_note": evidence_note,
                "source": source,
                "verification_status": v_status,
                "submitted_at": date.today().isoformat(),
            })
            return FakeCursor([])

        # ── INSERT INTO phone_number_summary (upsert) ─────────────────────
        if "INSERT INTO PHONE_NUMBER_SUMMARY" in sql_stripped:
            if self.db.simulate_upsert_error:
                raise RuntimeError("Simulated database error during summary upsert.")

            phone_e164, country_code = params[0], params[1]
            if isinstance(params[2], int):
                report_count_param = params[2]
                categories = list(params[3])
                evidence_note = params[8] if len(params) > 8 else None
            else:
                report_count_param = 1
                categories = list(params[2])
                evidence_note = params[3]

            self.uncommitted_summary_ops.append({
                "phone_e164": phone_e164,
                "country_code": country_code,
                "report_count": report_count_param,
                "categories": categories,
                "evidence_note": evidence_note,
            })

            with self.db.lock:
                existing = self.db.summary.get(phone_e164)
                if existing is None:
                    return FakeCursor([(1, True)])
                else:
                    new_count = existing["report_count"] + report_count_param
                    return FakeCursor([(new_count, False)])

        # ── SELECT FROM phone_number_summary ──────────────────────────────
        if "SELECT" in sql_stripped and "PHONE_NUMBER_SUMMARY" in sql_stripped:
            (phone_e164,) = params
            with self.db.lock:
                rec = self.db.summary.get(phone_e164)
                if rec is None:
                    return FakeCursor([])
                return FakeCursor([(
                    rec["report_count"],
                    rec["categories"],
                    rec["source"],
                    rec["first_reported"],
                    rec["last_reported"],
                    rec["verification_status"],
                    rec["evidence_note"],
                )])

        return FakeCursor([])

    def commit(self):
        with self.db.lock:
            self.db.submissions.extend(self.uncommitted_submissions)
            self.uncommitted_submissions.clear()

            for op in self.uncommitted_summary_ops:
                phone_e164 = op["phone_e164"]
                existing = self.db.summary.get(phone_e164)
                if existing is None:
                    self.db.summary[phone_e164] = {
                        "phone_e164": phone_e164,
                        "country_code": op["country_code"],
                        "report_count": op["report_count"],
                        "categories": sorted(set(op["categories"])),
                        "source": "community submission",
                        "first_reported": date.today(),
                        "last_reported": date.today(),
                        "verification_status": "unverified",
                        "evidence_note": op["evidence_note"],
                    }
                else:
                    existing["report_count"] += op["report_count"]
                    merged = sorted(set(existing["categories"]) | set(op["categories"]))
                    existing["categories"] = merged
                    existing["last_reported"] = date.today()
                    if op["evidence_note"]:
                        existing["evidence_note"] = op["evidence_note"]
            self.uncommitted_summary_ops.clear()

    def rollback(self):
        self.uncommitted_submissions.clear()
        self.uncommitted_summary_ops.clear()

    @contextmanager
    def transaction(self):
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise


class InMemoryTransactionalDB:
    """Thread-safe in-memory database."""

    def __init__(self):
        self.lock = threading.Lock()
        self.submissions: List[Dict[str, Any]] = []
        self.summary: Dict[str, Dict[str, Any]] = {}
        self.simulate_error = False
        self.simulate_upsert_error = False

    @contextmanager
    def connection(self) -> Generator[FakeConnection, None, None]:
        conn = FakeConnection(self)
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise


@pytest.fixture(autouse=True)
def mock_db_layer(monkeypatch):
    """Autouse fixture that protects tests from contacting a live database.

    Provides a clean in-memory database instance for each test.
    """
    fake_db = InMemoryTransactionalDB()

    @contextmanager
    def fake_get_connection():
        with fake_db.connection() as conn:
            yield conn

    # Preserve unmocked get_connection reference for testing db module directly
    if not hasattr(db, "_original_get_connection"):
        db._original_get_connection = db.get_connection

    # Patch get_connection across modules
    monkeypatch.setattr(phone_reputation, "get_connection", fake_get_connection)
    monkeypatch.setattr(db, "get_connection", fake_get_connection)

    # Patch startup/shutdown in main
    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setattr(main, "close_db", lambda: None)

    return fake_db
