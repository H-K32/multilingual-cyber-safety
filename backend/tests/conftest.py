# backend/tests/conftest.py
"""Shared pytest fixtures and in-memory transactional database for tests.

Provides an isolated, concurrent-safe in-memory database mock so tests never
modify or require a live production database.
"""

import threading
from contextlib import contextmanager
from datetime import date, datetime, timezone
from typing import Generator, List, Dict, Any

import pytest

from backend.app import db, phone_reputation, security_feed, main
from backend.app.rate_limiter import report_rate_limiter, dispute_rate_limiter


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
        self.uncommitted_disputes: List[Dict[str, Any]] = []
        self.in_transaction = True

    def execute(self, sql: str, params: tuple = ()) -> FakeCursor:
        if self.db.simulate_error:
            raise RuntimeError("Simulated database connection error.")

        sql_stripped = " ".join(sql.split()).upper()

        # ── INSERT INTO phone_number_disputes ─────────────────────────────
        if "INSERT INTO PHONE_NUMBER_DISPUTES" in sql_stripped:
            phone_e164, country_code, explanation, contact_info = params[:4]
            reporter_hash = params[4] if len(params) > 4 else None
            self.uncommitted_disputes.append({
                "phone_e164": phone_e164,
                "country_code": country_code,
                "explanation": explanation,
                "contact_info": contact_info,
                "review_status": "pending",
                "reporter_hash": reporter_hash,
                "submitted_at": date.today().isoformat(),
            })
            return FakeCursor([])

        # ── SELECT FROM phone_report_submissions (deduplication check) ───
        if "SELECT" in sql_stripped and "PHONE_REPORT_SUBMISSIONS" in sql_stripped and "REPORTER_HASH = %S" in sql_stripped:
            phone_e164 = params[0]
            reporter_hash = params[1]
            with self.db.lock:
                matches = [
                    s for s in self.db.submissions
                    if s.get("phone_e164") == phone_e164
                    and s.get("reporter_hash") == reporter_hash
                    and reporter_hash is not None
                ]
                if matches:
                    return FakeCursor([(1,)])
                return FakeCursor([])

        # ── INSERT INTO phone_report_submissions ──────────────────────────
        if "INSERT INTO PHONE_REPORT_SUBMISSIONS" in sql_stripped:
            phone_e164, country_code, categories, evidence_note = params[:4]
            # Handle reporter_hash at end of params or source/status
            reporter_hash = None
            source = "community submission"
            v_status = "unverified"
            if len(params) == 5:
                reporter_hash = params[4]
            elif len(params) > 5:
                source = params[4]
                v_status = params[5]
                reporter_hash = params[6] if len(params) > 6 else None

            self.uncommitted_submissions.append({
                "phone_e164": phone_e164,
                "country_code": country_code,
                "categories": list(categories),
                "evidence_note": evidence_note,
                "source": source,
                "verification_status": v_status,
                "reporter_hash": reporter_hash,
                "submitted_at": date.today().isoformat(),
            })
            return FakeCursor([])

        # ── UPDATE phone_number_summary (deduplicated category merge) ─────
        if "UPDATE PHONE_NUMBER_SUMMARY" in sql_stripped:
            clean_cats, safe_note, phone_e164 = params[0], params[1], params[2]
            with self.db.lock:
                existing = self.db.summary.get(phone_e164)
                if existing is not None:
                    merged = sorted(set(existing["categories"]) | set(clean_cats))
                    existing["categories"] = merged
                    existing["last_reported"] = date.today()
                    if safe_note:
                        existing["evidence_note"] = safe_note
                    return FakeCursor([(existing["report_count"],)])
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
            with self.db.lock:
                # Signal sync: cross-category threats (>= 3 categories)
                if "ARRAY_LENGTH" in sql_stripped:
                    rows = [
                        (x["phone_e164"], x["country_code"], x["report_count"], x["categories"])
                        for x in self.db.summary.values()
                        if len(x.get("categories", [])) >= 3
                    ]
                    return FakeCursor(rows)

                # Signal sync: high report volume (>= 5 or verified)
                if "REPORT_COUNT >= 5" in sql_stripped:
                    rows = [
                        (x["phone_e164"], x["country_code"], x["report_count"], x["categories"], x.get("verification_status", "unverified"))
                        for x in self.db.summary.values()
                        if x.get("report_count", 0) >= 5 or x.get("verification_status") == "verified"
                    ]
                    return FakeCursor(rows)

                # 1. Count query
                if "COUNT(*)" in sql_stripped:
                    items = list(self.db.summary.values())
                    if params:
                        search_pat = params[0].strip("%").lower()
                        alt_pat = params[1].strip("%").lower() if len(params) > 1 else search_pat
                        items = [
                            x for x in items
                            if search_pat in x["phone_e164"].lower()
                            or alt_pat in x["phone_e164"].lower()
                            or any(search_pat in c.lower() for c in x["categories"])
                        ]
                    return FakeCursor([(len(items),)])

                # 2. List / Paginated query
                if "ORDER BY REPORT_COUNT" in sql_stripped or "LIMIT" in sql_stripped:
                    items = list(self.db.summary.values())
                    if len(params) >= 3 and "%" in str(params[0]):
                        search_pat = params[0].strip("%").lower()
                        alt_pat = params[1].strip("%").lower() if len(params) > 1 else search_pat
                        items = [
                            x for x in items
                            if search_pat in x["phone_e164"].lower()
                            or alt_pat in x["phone_e164"].lower()
                            or any(search_pat in c.lower() for c in x["categories"])
                        ]
                        limit = params[-2]
                        offset = params[-1]
                    else:
                        limit = params[0]
                        offset = params[1]

                    # Sort by report_count DESC, phone_e164 ASC
                    items.sort(key=lambda x: (-x["report_count"], x["phone_e164"]))
                    page = items[offset: offset + limit]

                    rows = [
                        (
                            x["phone_e164"],
                            x["country_code"],
                            x["report_count"],
                            x["categories"],
                            x["first_reported"],
                            x["last_reported"],
                            x["verification_status"],
                        )
                        for x in page
                    ]
                    return FakeCursor(rows)

                # 3. Single number lookup
                if params:
                    phone_e164 = params[0]
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

        # ── SELECT 24h spike FROM phone_report_submissions ────────────────
        if "COUNT(DISTINCT S.REPORTER_HASH)" in sql_stripped and "PHONE_REPORT_SUBMISSIONS" in sql_stripped:
            with self.db.lock:
                by_phone: Dict[str, List[Dict[str, Any]]] = {}
                for s in self.db.submissions:
                    p = s.get("phone_e164")
                    if p:
                        by_phone.setdefault(p, []).append(s)
                rows = []
                for p, subs in by_phone.items():
                    distinct_hashes = {s["reporter_hash"] for s in subs if s.get("reporter_hash")}
                    if len(distinct_hashes) >= 3:
                        all_cats = sorted({c for s in subs for c in s.get("categories", [])})
                        c_code = subs[0].get("country_code", "251")
                        rows.append((p, c_code, len(distinct_hashes), all_cats))
                return FakeCursor(rows)

        # ── SELECT disputed threats (summary JOIN disputes) ───────────────
        if "PHONE_NUMBER_DISPUTES" in sql_stripped and "PHONE_NUMBER_SUMMARY" in sql_stripped and "JOIN" in sql_stripped:
            with self.db.lock:
                disputed_phones = {
                    d["phone_e164"] for d in self.db.disputes
                    if d.get("review_status") == "pending"
                }
                rows = []
                for p in disputed_phones:
                    s = self.db.summary.get(p)
                    if s:
                        rows.append((s["phone_e164"], s["country_code"], s["report_count"], s["categories"]))
                return FakeCursor(rows)

        # ── COUNT(*) FROM phone_number_disputes ───────────────────────────
        if "COUNT(*)" in sql_stripped and "PHONE_NUMBER_DISPUTES" in sql_stripped and "JOIN" not in sql_stripped:
            with self.db.lock:
                status_filter = params[0] if params else None
                matched = [
                    d for d in self.db.disputes
                    if not status_filter or d.get("review_status") == status_filter
                ]
                return FakeCursor([(len(matched),)])

        # ── SELECT ... FROM phone_number_disputes (admin list) ────────────
        if "FROM PHONE_NUMBER_DISPUTES" in sql_stripped and "JOIN" not in sql_stripped:
            with self.db.lock:
                status_filter = params[0] if (len(params) == 3 and not isinstance(params[0], int)) else None
                matched = [
                    d for d in self.db.disputes
                    if not status_filter or d.get("review_status") == status_filter
                ]
                rows = []
                for idx, d in enumerate(matched, start=1):
                    rows.append((
                        d.get("id", idx),
                        d.get("phone_e164"),
                        d.get("country_code", "251"),
                        d.get("explanation"),
                        d.get("contact_info"),
                        d.get("review_status", "pending"),
                        d.get("submitted_at", datetime.now(timezone.utc)),
                    ))
                return FakeCursor(rows)

        # ── UPDATE phone_number_disputes (admin status update) ────────────
        if "UPDATE PHONE_NUMBER_DISPUTES" in sql_stripped:
            new_status, dispute_id = params[:2]
            with self.db.lock:
                for idx, d in enumerate(self.db.disputes, start=1):
                    if d.get("id", idx) == dispute_id or idx == dispute_id:
                        d["review_status"] = new_status
                        return FakeCursor([(dispute_id, d.get("phone_e164"), new_status)])
                return FakeCursor([])

        # ── INSERT INTO security_feed_events (upsert) ─────────────────────
        if "INSERT INTO SECURITY_FEED_EVENTS" in sql_stripped:
            ev_id, ev_type, prio, phone, c_code, r_count, cats, r_24h, reason, ev_src, conf_qual = params[:11]
            with self.db.lock:
                existing = self.db.feed_events.get(ev_id)
                now_str = datetime.now(timezone.utc).isoformat()
                if existing is None:
                    self.db.feed_events[ev_id] = {
                        "event_id": ev_id,
                        "event_type": ev_type,
                        "priority": prio,
                        "phone_e164": phone,
                        "country_code": c_code,
                        "report_count": r_count,
                        "categories": list(cats),
                        "recent_reports_24h": r_24h,
                        "reason": reason,
                        "evidence_source": ev_src,
                        "confidence_qualification": conf_qual,
                        "review_status": "new",
                        "acknowledged_by": None,
                        "acknowledged_at": None,
                        "notes": None,
                        "first_detected": now_str,
                        "last_updated": now_str,
                    }
                else:
                    existing["report_count"] = r_count
                    existing["categories"] = list(cats)
                    existing["recent_reports_24h"] = r_24h
                    existing["priority"] = prio
                    existing["reason"] = reason
                    existing["evidence_source"] = ev_src
                    existing["confidence_qualification"] = conf_qual
                    existing["last_updated"] = now_str
            return FakeCursor([])

        # ── SELECT FROM security_feed_events ──────────────────────────────
        if "SECURITY_FEED_EVENTS" in sql_stripped and "SELECT" in sql_stripped:
            with self.db.lock:
                # 1. Count query
                if "COUNT(*)" in sql_stripped:
                    events = list(self.db.feed_events.values())
                    idx = 0
                    if "EVENT_TYPE = %S" in sql_stripped and idx < len(params):
                        events = [e for e in events if e["event_type"] == params[idx]]
                        idx += 1
                    if "PRIORITY = %S" in sql_stripped and idx < len(params):
                        events = [e for e in events if e["priority"] == params[idx]]
                        idx += 1
                    if "REVIEW_STATUS = %S" in sql_stripped and idx < len(params):
                        events = [e for e in events if e["review_status"] == params[idx]]
                        idx += 1
                    return FakeCursor([(len(events),)])

                # 2. Single event lookup by event_id
                if "WHERE EVENT_ID = %S" in sql_stripped:
                    ev_id = params[0]
                    ev = self.db.feed_events.get(ev_id)
                    if ev is None:
                        return FakeCursor([])
                    return FakeCursor([(
                        ev["event_id"], ev["event_type"], ev["priority"], ev["phone_e164"],
                        ev["country_code"], ev["report_count"], ev["categories"],
                        ev["recent_reports_24h"], ev["reason"], ev["evidence_source"],
                        ev["confidence_qualification"], ev["review_status"],
                        ev["acknowledged_by"], ev["acknowledged_at"], ev["notes"],
                        ev["first_detected"], ev["last_updated"],
                    )])

                # 3. Paginated list query
                events = list(self.db.feed_events.values())
                filter_params = list(params[:-2]) if len(params) >= 2 else []
                limit = params[-2] if len(params) >= 2 else 20
                offset = params[-1] if len(params) >= 2 else 0

                idx = 0
                if "EVENT_TYPE = %S" in sql_stripped and idx < len(filter_params):
                    events = [e for e in events if e["event_type"] == filter_params[idx]]
                    idx += 1
                if "PRIORITY = %S" in sql_stripped and idx < len(filter_params):
                    events = [e for e in events if e["priority"] == filter_params[idx]]
                    idx += 1
                if "REVIEW_STATUS = %S" in sql_stripped and idx < len(filter_params):
                    events = [e for e in events if e["review_status"] == filter_params[idx]]
                    idx += 1

                prio_order = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}
                events.sort(key=lambda x: (prio_order.get(x["priority"], 5), str(x["last_updated"])))

                page = events[offset: offset + limit]
                rows = [
                    (
                        ev["event_id"], ev["event_type"], ev["priority"], ev["phone_e164"],
                        ev["country_code"], ev["report_count"], ev["categories"],
                        ev["recent_reports_24h"], ev["reason"], ev["evidence_source"],
                        ev["confidence_qualification"], ev["review_status"],
                        ev["acknowledged_by"], ev["acknowledged_at"], ev["notes"],
                        ev["first_detected"], ev["last_updated"],
                    )
                    for ev in page
                ]
                return FakeCursor(rows)

        # ── UPDATE security_feed_events SET review_status ─────────────────
        if "UPDATE SECURITY_FEED_EVENTS" in sql_stripped:
            clean_status, ack_by, notes, ev_id = params[0], params[1], params[2], params[3]
            with self.db.lock:
                ev = self.db.feed_events.get(ev_id)
                if ev is not None:
                    ev["review_status"] = clean_status
                    ev["acknowledged_by"] = ack_by
                    ev["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
                    if notes:
                        ev["notes"] = notes
                    ev["last_updated"] = datetime.now(timezone.utc).isoformat()
                    return FakeCursor([(ev_id,)])
                return FakeCursor([])

        return FakeCursor([])

    def commit(self):
        with self.db.lock:
            self.db.submissions.extend(self.uncommitted_submissions)
            self.uncommitted_submissions.clear()

            self.db.disputes.extend(self.uncommitted_disputes)
            self.uncommitted_disputes.clear()

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
        self.uncommitted_disputes.clear()

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
        self.disputes: List[Dict[str, Any]] = []
        self.feed_events: Dict[str, Dict[str, Any]] = {}
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
    report_rate_limiter.reset()
    dispute_rate_limiter.reset()

    # Configure test security feed analyst credentials
    test_keys = (
        '{"test-analyst-token": {"analyst_id": "cbe-soc-01", "organization": "Commercial Bank of Ethiopia", "role": "analyst"}, '
        '"test-admin-token": {"analyst_id": "dagu-admin-01", "organization": "Dagu Security SOC", "role": "admin"}, '
        '"test-viewer-token": {"analyst_id": "guest-01", "organization": "Guest Auditor", "role": "viewer"}}'
    )
    monkeypatch.setenv("DAGU_SECURITY_FEED_API_KEYS", test_keys)

    @contextmanager
    def fake_get_connection():
        with fake_db.connection() as conn:
            yield conn

    # Preserve unmocked get_connection reference for testing db module directly
    if not hasattr(db, "_original_get_connection"):
        db._original_get_connection = db.get_connection

    # Patch get_connection across modules
    monkeypatch.setattr(phone_reputation, "get_connection", fake_get_connection)
    monkeypatch.setattr(security_feed, "get_connection", fake_get_connection)
    monkeypatch.setattr(db, "get_connection", fake_get_connection)

    # Patch startup/shutdown in main
    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setattr(main, "close_db", lambda: None)

    return fake_db
