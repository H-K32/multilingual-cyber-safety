# backend/tests/test_security_feed.py
"""Tests for the Bank Security Operations Feed and Authorization Mechanism.

Covers:
- Threat signal aggregation and synchronization (spikes, high volume, cross-category, disputes)
- Alert stability and duplicate alert prevention
- Authentication: Bearer token and X-API-Key handling
- Role-based authorization: analyst, admin, and viewer permissions
- Privacy safeguards: verifying reporter hashes and dispute contact info are never leaked
- Pagination, filtering, and phone number masking
- Acknowledgment and review status transition workflow
- Safe database error handling (HTTP 503)
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app import phone_reputation

client = TestClient(app)

ANALYST_HEADERS = {"Authorization": "Bearer test-analyst-token"}
ADMIN_HEADERS = {"Authorization": "Bearer test-admin-token"}
VIEWER_HEADERS = {"Authorization": "Bearer test-viewer-token"}


# ---------------------------------------------------------------------------
# Authentication & Authorization Tests
# ---------------------------------------------------------------------------

def test_security_feed_requires_authentication():
    """Unauthenticated requests to /security-feed receive HTTP 401."""
    resp = client.get("/security-feed")
    assert resp.status_code == 401
    assert "Missing security operations authentication credentials" in resp.json()["detail"]


def test_security_feed_rejects_invalid_token():
    """Requests with unknown or malformed tokens receive HTTP 401."""
    resp = client.get("/security-feed", headers={"Authorization": "Bearer invalid-fake-token"})
    assert resp.status_code == 401
    assert "Invalid or expired" in resp.json()["detail"]


def test_security_feed_accepts_x_api_key_header():
    """Requests providing credentials via X-API-Key header succeed."""
    resp = client.get("/security-feed", headers={"X-API-Key": "test-analyst-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["organization"] == "Commercial Bank of Ethiopia"
    assert data["caller_role"] == "analyst"


def test_security_feed_503_when_no_server_keys_configured(monkeypatch):
    """When DAGU_SECURITY_FEED_API_KEYS is unset, feed access safely returns HTTP 503."""
    monkeypatch.delenv("DAGU_SECURITY_FEED_API_KEYS", raising=False)
    resp = client.get("/security-feed", headers=ANALYST_HEADERS)
    assert resp.status_code == 503
    assert "not configured on this server" in resp.json()["detail"]


def test_server_derives_organization_and_role_server_side():
    """Client cannot spoof organization or role via query parameters or body."""
    # Attempt to claim admin role and different org via query params
    resp = client.get(
        "/security-feed?role=admin&organization=HackedBank",
        headers=ANALYST_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Derivation must come strictly from server token
    assert data["organization"] == "Commercial Bank of Ethiopia"
    assert data["caller_role"] == "analyst"
    assert data["analyst_id"] == "cbe-soc-01"


# ---------------------------------------------------------------------------
# Threat Signal Aggregation Tests
# ---------------------------------------------------------------------------

def test_high_report_volume_signal_generation(mock_db_layer):
    """Numbers with >= 5 reports generate high_report_volume security feed alerts."""
    phone = "0911223344"
    # Submit 5 reports
    for i in range(5):
        phone_reputation.submit_report(phone, ["phishing"], f"Report {i}", reporter_id=f"reporter-{i}")

    resp = client.get("/security-feed?event_type=high_report_volume", headers=ANALYST_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1

    event = next(e for e in data["items"] if e["phone_number"] == "+251911223344")
    assert event["event_type"] == "high_report_volume"
    assert event["priority"] == "HIGH"
    assert event["report_count"] == 5
    assert "phishing" in event["categories"]
    assert "Accumulated 5 independent reports" in event["reason"]
    assert "Does not constitute definitive proof" in event["confidence_qualification"]
    assert event["review_status"] == "new"


def test_cross_category_threat_signal_generation(mock_db_layer):
    """Numbers reported across >= 3 distinct categories generate cross_category_threat alerts."""
    phone = "0922334455"
    # Submit reports covering 3 distinct categories
    phone_reputation.submit_report(phone, ["scam", "phishing", "impersonation"], "Multi-vector fraud", reporter_id="rep-1")

    resp = client.get("/security-feed?event_type=cross_category_threat", headers=ANALYST_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1

    event = data["items"][0]
    assert event["event_type"] == "cross_category_threat"
    assert event["priority"] == "HIGH"
    assert set(event["categories"]) == {"impersonation", "phishing", "scam"}
    assert "Multi-vector scam pattern" in event["reason"]


def test_reputation_spike_24h_window_signal(mock_db_layer):
    """Numbers with >= 3 distinct reporters in 24 hours generate a reputation_spike alert."""
    phone = "0933445566"
    for i in range(4):
        phone_reputation.submit_report(phone, ["scam"], f"Spike note {i}", reporter_id=f"distinct-client-{i}")

    resp = client.get("/security-feed?event_type=reputation_spike", headers=ANALYST_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1

    event = next(e for e in data["items"] if e["phone_number"] == "+251933445566")
    assert event["event_type"] == "reputation_spike"
    assert event["priority"] in ("HIGH", "CRITICAL")
    assert event["recent_reports_24h"] == 4
    assert "Rapid surge of 4 independent reports" in event["reason"]


def test_disputed_threat_signal_generation(mock_db_layer):
    """Numbers with active reports and a pending dispute generate a disputed_threat alert."""
    phone = "0944556677"
    # 1. Active community report
    phone_reputation.submit_report(phone, ["scam"], "Scam call received", reporter_id="rep-1")
    # 2. Dispute submitted
    phone_reputation.submit_dispute(phone, "This is our verified customer care hotline.", "care@service.et")

    resp = client.get("/security-feed?event_type=disputed_threat", headers=ANALYST_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1

    event = next(e for e in data["items"] if e["phone_number"] == "+251944556677")
    assert event["event_type"] == "disputed_threat"
    assert event["priority"] == "MEDIUM"
    assert "Contested reputation" in event["reason"]
    assert "pending dispute under review" in event["reason"]
    assert "Do not apply automated blocking" in event["confidence_qualification"]


# ---------------------------------------------------------------------------
# Duplicate Prevention & Alert Stability Tests
# ---------------------------------------------------------------------------

def test_duplicate_event_prevention_on_repeated_sync(mock_db_layer):
    """Repeated calls to the feed do not create duplicate event entries for the same number."""
    phone = "0911556677"
    for i in range(6):
        phone_reputation.submit_report(phone, ["scam"], f"Report {i}", reporter_id=f"rep-{i}")

    # First feed query triggers sync
    resp1 = client.get("/security-feed", headers=ANALYST_HEADERS)
    assert resp1.status_code == 200
    total1 = resp1.json()["total"]

    # Second feed query triggers another sync
    resp2 = client.get("/security-feed", headers=ANALYST_HEADERS)
    assert resp2.status_code == 200
    total2 = resp2.json()["total"]

    # Exactly the same number of events (no duplicate inflation)
    assert total1 == total2
    matching = [e for e in resp2.json()["items"] if e["phone_number"] == "+251911556677"]
    # Only 1 volume event and/or spike event, each with unique deterministic event_id
    event_ids = [e["event_id"] for e in matching]
    assert len(event_ids) == len(set(event_ids))


# ---------------------------------------------------------------------------
# Privacy Safeguards Tests
# ---------------------------------------------------------------------------

def test_security_feed_never_leaks_reporter_hashes_or_dispute_contact(mock_db_layer):
    """Verify that private reporter hashes, dispute explanations, and contact info are NEVER returned."""
    phone = "0955667788"
    phone_reputation.submit_report(phone, ["scam"], "Secret private note", reporter_id="198.51.100.99")
    phone_reputation.submit_dispute(
        phone,
        "Secret explanation containing private details.",
        contact_info="confidential_officer@bank.et",
        reporter_id="198.51.100.77",
    )

    resp = client.get("/security-feed", headers=ANALYST_HEADERS)
    assert resp.status_code == 200
    raw_response = resp.text

    assert "confidential_officer@bank.et" not in raw_response
    assert "Secret explanation containing private details" not in raw_response
    assert "198.51.100.99" not in raw_response
    assert "198.51.100.77" not in raw_response


def test_security_feed_phone_masking_option(mock_db_layer):
    """When mask_phone=true is passed, phone numbers are masked in feed items."""
    phone = "0911998877"
    for i in range(5):
        phone_reputation.submit_report(phone, ["phishing"], "Note", reporter_id=f"r-{i}")

    resp = client.get("/security-feed?mask_phone=true", headers=ANALYST_HEADERS)
    assert resp.status_code == 200
    item = next(e for e in resp.json()["items"] if "0911998877" in e["masked_phone"] or "+251 9XX XXX XXX" in e["phone_number"])
    assert item["phone_number"] == "+251 9XX XXX XXX"


# ---------------------------------------------------------------------------
# Pagination & Filter Tests
# ---------------------------------------------------------------------------

def test_security_feed_filtering_and_pagination(mock_db_layer):
    """Test pagination (limit, offset) and priority filtering."""
    # Create multiple numbers with varying counts
    for i in range(5):
        phone = f"091100000{i}"
        for r in range(5 + i):
            phone_reputation.submit_report(phone, ["scam"], "Note", reporter_id=f"r-{i}-{r}")

    # Query with limit=2, offset=0
    p1 = client.get("/security-feed?limit=2&offset=0", headers=ANALYST_HEADERS)
    assert p1.status_code == 200
    d1 = p1.json()
    assert d1["limit"] == 2
    assert d1["offset"] == 0
    assert len(d1["items"]) == 2
    assert d1["has_more"] is True

    # Query page 2
    p2 = client.get("/security-feed?limit=2&offset=2", headers=ANALYST_HEADERS)
    assert p2.status_code == 200
    d2 = p2.json()
    assert len(d2["items"]) == 2
    # Ensure distinct items
    ids_p1 = {x["event_id"] for x in d1["items"]}
    ids_p2 = {x["event_id"] for x in d2["items"]}
    assert ids_p1.isdisjoint(ids_p2)


def test_security_feed_invalid_filter_validation(mock_db_layer):
    """Invalid query filter parameters return HTTP 400."""
    r1 = client.get("/security-feed?event_type=invalid_type", headers=ANALYST_HEADERS)
    assert r1.status_code == 400
    assert "Invalid event_type" in r1.json()["detail"]

    r2 = client.get("/security-feed?priority=ULTRA_HIGH", headers=ANALYST_HEADERS)
    assert r2.status_code == 400
    assert "Invalid priority" in r2.json()["detail"]

    r3 = client.get("/security-feed?review_status=invalid_status", headers=ANALYST_HEADERS)
    assert r3.status_code == 400
    assert "Invalid review_status" in r3.json()["detail"]


# ---------------------------------------------------------------------------
# Event Detail & Acknowledgment / Review Workflow Tests
# ---------------------------------------------------------------------------

def test_security_feed_get_single_event(mock_db_layer):
    """GET /security-feed/{event_id} returns details of an existing event."""
    phone = "0911778899"
    for i in range(5):
        phone_reputation.submit_report(phone, ["scam"], "Note", reporter_id=f"r-{i}")

    feed_resp = client.get("/security-feed", headers=ANALYST_HEADERS)
    event_id = feed_resp.json()["items"][0]["event_id"]

    detail_resp = client.get(f"/security-feed/{event_id}", headers=ANALYST_HEADERS)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["event"]["event_id"] == event_id
    assert detail["organization"] == "Commercial Bank of Ethiopia"

    # Non-existent event returns 404
    missing_resp = client.get("/security-feed/EVT-NONEXISTENT", headers=ANALYST_HEADERS)
    assert missing_resp.status_code == 404


def test_acknowledge_and_review_status_transition(mock_db_layer):
    """Analyst can acknowledge an alert and update review status."""
    phone = "0911443322"
    for i in range(5):
        phone_reputation.submit_report(phone, ["phishing"], "Note", reporter_id=f"r-{i}")

    feed_resp = client.get("/security-feed", headers=ANALYST_HEADERS)
    event_id = feed_resp.json()["items"][0]["event_id"]

    # 1. Acknowledge the alert
    ack_resp = client.post(
        f"/security-feed/{event_id}/acknowledge",
        json={"review_status": "under_review", "notes": "Initiated customer outreach and SIM verification."},
        headers=ANALYST_HEADERS,
    )
    assert ack_resp.status_code == 200
    ack_data = ack_resp.json()
    assert ack_data["acknowledged_by"] == "cbe-soc-01"
    assert ack_data["event"]["review_status"] == "under_review"
    assert "Initiated customer outreach" in ack_data["event"]["notes"]

    # 2. Verify subsequent feed query preserves the updated status
    feed_after = client.get("/security-feed", headers=ANALYST_HEADERS)
    ev = next(e for e in feed_after.json()["items"] if e["event_id"] == event_id)
    assert ev["review_status"] == "under_review"
    assert ev["acknowledged_by"] == "cbe-soc-01"

    # 3. Viewer role cannot acknowledge or update status (HTTP 403)
    viewer_ack = client.post(
        f"/security-feed/{event_id}/acknowledge",
        json={"review_status": "resolved"},
        headers=VIEWER_HEADERS,
    )
    assert viewer_ack.status_code == 403
    assert "Insufficient permissions" in viewer_ack.json()["detail"]


def test_security_feed_database_error_handling(mock_db_layer):
    """Simulated database failures safely return HTTP 503 without leaking internals."""
    mock_db_layer.simulate_error = True
    resp = client.get("/security-feed", headers=ANALYST_HEADERS)
    assert resp.status_code == 503
    assert "temporarily unavailable" in resp.json()["detail"]
