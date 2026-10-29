"""Tests for the /report and /check-number endpoints and submit_report logic.

Uses the isolated, thread-safe in-memory database mock defined in conftest.py.
No live database is used.
"""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import pytest
from fastapi.testclient import TestClient

from backend.app import phone_reputation
from backend.app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# submit_report unit tests
# ---------------------------------------------------------------------------

def test_valid_report_submission(mock_db_layer):
    """Test valid report submission creates submission and summary rows."""
    result = phone_reputation.submit_report(
        "0911234567", ["scam", "phishing"], "Fake telebirr message received."
    )
    assert result["status"] == "submitted"
    assert "unverified" in result["explanation"]

    # Verify submissions table has 1 record
    assert len(mock_db_layer.submissions) == 1
    sub = mock_db_layer.submissions[0]
    assert sub["phone_e164"] == "+251911234567"
    assert sub["country_code"] == "251"
    assert set(sub["categories"]) == {"scam", "phishing"}
    assert sub["evidence_note"] == "Fake telebirr message received."
    assert sub["verification_status"] == "unverified"

    # Verify summary table has 1 record
    assert len(mock_db_layer.summary) == 1
    summary = mock_db_layer.summary["+251911234567"]
    assert summary["report_count"] == 1
    assert summary["categories"] == ["phishing", "scam"]
    assert summary["verification_status"] == "unverified"


def test_repeated_submissions_for_same_number(mock_db_layer):
    """Repeated submissions update the summary without duplicate summary rows."""
    res1 = phone_reputation.submit_report("0911234567", ["scam"], "First report.")
    assert res1["status"] == "submitted"

    res2 = phone_reputation.submit_report("0911234567", ["phishing"], "Second report.")
    assert res2["status"] == "updated"
    assert "Report count is now 2" in res2["explanation"]

    # Exactly 1 summary row for this number
    assert len(mock_db_layer.summary) == 1
    summary = mock_db_layer.summary["+251911234567"]
    assert summary["report_count"] == 2
    assert summary["categories"] == ["phishing", "scam"]

    # 2 individual submission records
    assert len(mock_db_layer.submissions) == 2


def test_correct_count_and_category_aggregation(mock_db_layer):
    """Multiple submissions aggregate unique categories and increment count."""
    phone_reputation.submit_report("+251911234567", ["scam"], "Note 1")
    phone_reputation.submit_report("0911234567", ["impersonation", "scam"], "Note 2")
    phone_reputation.submit_report("0911234567", ["spam_calls"], "Note 3")

    lookup = phone_reputation.lookup_phone_number("0911234567")
    assert lookup["status"] == "reported"
    assert lookup["report_count"] == 3
    assert lookup["categories"] == ["impersonation", "scam", "spam_calls"]
    assert lookup["verification_status"] == "unverified"


def test_concurrent_submissions_for_same_number(mock_db_layer):
    """Concurrent submissions from multiple threads update the summary safely."""
    num_threads = 10
    phone = "0911234567"

    def submit_task(idx):
        cat = "scam" if idx % 2 == 0 else "phishing"
        return phone_reputation.submit_report(phone, [cat], f"Concurrent report {idx}")

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(submit_task, range(num_threads)))

    assert len(results) == num_threads
    # 1 submitted, 9 updated
    statuses = [r["status"] for r in results]
    assert statuses.count("submitted") == 1
    assert statuses.count("updated") == num_threads - 1

    # Exactly 1 summary row with count == num_threads
    assert len(mock_db_layer.summary) == 1
    summary = mock_db_layer.summary["+251911234567"]
    assert summary["report_count"] == num_threads
    assert summary["categories"] == ["phishing", "scam"]

    # Exactly num_threads individual submission rows
    assert len(mock_db_layer.submissions) == num_threads


def test_database_error_and_transaction_rollback(mock_db_layer):
    """If an error occurs before commit, transaction is rolled back and no partial records remain."""
    mock_db_layer.simulate_upsert_error = True

    with pytest.raises(RuntimeError, match="The phone reputation database is temporarily unavailable."):
        phone_reputation.submit_report("0911234567", ["scam"], "Should fail")

    # Both tables must remain clean (rollback occurred)
    assert len(mock_db_layer.submissions) == 0
    assert len(mock_db_layer.summary) == 0


def test_database_unavailable_error_handling(mock_db_layer):
    """When DB is unavailable, lookup and submit raise a clean RuntimeError without leaking internals."""
    mock_db_layer.simulate_error = True

    with pytest.raises(RuntimeError) as exc_info:
        phone_reputation.lookup_phone_number("0911234567")
    assert "The phone reputation database is temporarily unavailable." in str(exc_info.value)
    # Ensure no credentials or SQL details leaked
    assert "password" not in str(exc_info.value).lower()
    assert "select" not in str(exc_info.value).lower()

    with pytest.raises(RuntimeError) as exc_info2:
        phone_reputation.submit_report("0911234567", ["scam"], "Note")
    assert "The phone reputation database is temporarily unavailable." in str(exc_info2.value)


def test_submit_report_rejects_invalid_numbers():
    assert phone_reputation.submit_report("not-a-number", ["scam"], "")["status"] == "invalid_number"
    assert phone_reputation.submit_report("09112345", ["scam"], "")["status"] == "invalid_number"
    assert phone_reputation.submit_report("+2510911234567", ["scam"], "")["status"] == "invalid_number"
    assert phone_reputation.submit_report("", ["scam"], "")["status"] == "invalid_number"


def test_submit_report_rejects_invalid_categories():
    assert phone_reputation.submit_report("0911234567", [], "")["status"] == "invalid_categories"
    assert phone_reputation.submit_report("0911234567", ["unsupported_category"], "")["status"] == "invalid_categories"


def test_submit_report_normalizes_ethiopian_formats(mock_db_layer):
    phone_reputation.submit_report("0911234567", ["spam_calls"], "Local format.")
    lookup = phone_reputation.lookup_phone_number("+251 91 123 4567")
    assert lookup["status"] == "reported"
    assert lookup["report_count"] == 1


def test_submit_report_truncates_long_evidence_note(mock_db_layer):
    long_note = "x" * 1000
    phone_reputation.submit_report("0911234567", ["scam"], long_note)
    lookup = phone_reputation.lookup_phone_number("0911234567")
    assert len(lookup["evidence_note"]) <= 500


# ---------------------------------------------------------------------------
# /report API endpoint tests
# ---------------------------------------------------------------------------

def test_report_endpoint_accepts_valid_submission(mock_db_layer):
    response = client.post(
        "/report",
        json={
            "phone_number": "0911234567",
            "categories": ["scam"],
            "evidence_note": "Received a fake prize message.",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "submitted"


def test_report_endpoint_rejects_missing_phone():
    response = client.post("/report", json={"categories": ["scam"]})
    assert response.status_code == 400


def test_report_endpoint_rejects_empty_categories():
    response = client.post(
        "/report", json={"phone_number": "0911234567", "categories": []}
    )
    assert response.status_code == 400


def test_report_endpoint_rejects_invalid_number():
    response = client.post(
        "/report", json={"phone_number": "abc", "categories": ["scam"]}
    )
    assert response.status_code == 400


def test_report_endpoint_returns_503_when_database_unavailable(mock_db_layer):
    mock_db_layer.simulate_error = True
    response = client.post(
        "/report",
        json={"phone_number": "0911234567", "categories": ["scam"]},
    )
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]


# ---------------------------------------------------------------------------
# /check-number API endpoint tests
# ---------------------------------------------------------------------------

def test_check_number_returns_no_reports_for_unlisted():
    response = client.post("/check-number", json={"phone_number": "0911234567"})
    assert response.status_code == 200
    assert response.json()["status"] == "no_reports_found"
    assert "does not establish" in response.json()["explanation"]


def test_check_number_returns_report_for_listed(mock_db_layer):
    phone_reputation.submit_report("0911234567", ["phishing"], "Test.")
    response = client.post("/check-number", json={"phone_number": "+251911234567"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "reported"
    assert payload["report_count"] == 1
    assert payload["categories"] == ["phishing"]
    assert payload["verification_status"] == "unverified"


def test_check_number_rejects_missing_phone():
    response = client.post("/check-number", json={})
    assert response.status_code == 400


def test_check_number_returns_invalid_for_bad_number():
    response = client.post("/check-number", json={"phone_number": "not-a-number"})
    assert response.status_code == 200
    assert response.json()["status"] == "invalid_number"


def test_check_number_returns_503_when_database_unavailable(mock_db_layer):
    mock_db_layer.simulate_error = True
    response = client.post("/check-number", json={"phone_number": "0911234567"})
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Legacy CSV import tests
# ---------------------------------------------------------------------------

def test_import_legacy_csv_empty(tmp_path, mock_db_layer):
    from backend.app.import_legacy_csv import import_legacy_reports

    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("phone_number,country_code,report_count,categories,source,first_reported,last_reported,verification_status,evidence_note\n", encoding="utf-8")

    count = import_legacy_reports(empty_csv)
    assert count == 0
    assert len(mock_db_layer.submissions) == 0


def test_import_legacy_csv_with_data(tmp_path, mock_db_layer):
    from backend.app.import_legacy_csv import import_legacy_reports

    data_csv = tmp_path / "data.csv"
    data_csv.write_text(
        "phone_number,country_code,report_count,categories,source,first_reported,last_reported,verification_status,evidence_note\n"
        "0911234567,251,3,scam|phishing,legacy import,2026-01-01,2026-01-02,unverified,Legacy note\n",
        encoding="utf-8",
    )

    count = import_legacy_reports(data_csv)
    assert count == 1
    assert len(mock_db_layer.submissions) == 1
    assert len(mock_db_layer.summary) == 1

    summary = mock_db_layer.summary["+251911234567"]
    assert summary["report_count"] == 3
    assert set(summary["categories"]) == {"phishing", "scam"}



# ---------------------------------------------------------------------------
# Reported Numbers List & Public Feed Tests
# ---------------------------------------------------------------------------

def test_mask_phone_number_formats():
    from backend.app.phone_reputation import mask_phone_number

    assert mask_phone_number("+251911234567") == "+251 9XX XXX XXX"
    assert mask_phone_number("+251711234567") == "+251 7XX XXX XXX"
    assert mask_phone_number("+14155552671") == "+141 XXX XXX"
    assert mask_phone_number("") == ""


def test_derive_risk_status():
    from backend.app.phone_reputation import derive_risk_status

    assert derive_risk_status(12, "unverified", ["scam"]) == ("High Risk", "HIGH_RISK")
    assert derive_risk_status(5, "unverified", ["spam_calls"]) == ("Suspicious", "SUSPICIOUS")
    assert derive_risk_status(1, "unverified", ["other"]) == ("Reported", "REPORTED")
    assert derive_risk_status(1, "verified", ["other"]) == ("High Risk", "HIGH_RISK")


def test_get_reported_numbers_empty(mock_db_layer):
    from backend.app.phone_reputation import get_reported_numbers

    feed = get_reported_numbers()
    assert feed["total"] == 0
    assert feed["items"] == []
    assert feed["has_more"] is False


def test_get_reported_numbers_sorted_and_paginated(mock_db_layer):
    from backend.app.phone_reputation import submit_report, get_reported_numbers

    # Number A: 1 report
    submit_report("0911000001", ["scam"], "Note A")

    # Number B: 3 reports
    for i in range(3):
        submit_report("0911000002", ["phishing"], f"Note B {i}")

    # Number C: 5 reports
    for i in range(5):
        submit_report("0911000003", ["spam_calls"], f"Note C {i}")

    feed = get_reported_numbers(limit=2, offset=0)
    assert feed["total"] == 3
    assert len(feed["items"]) == 2
    assert feed["has_more"] is True

    # Most reported first: Number C (5), then Number B (3)
    assert feed["items"][0]["phone_number"] == "+251911000003"
    assert feed["items"][0]["report_count"] == 5
    assert feed["items"][0]["risk_status"] == "SUSPICIOUS"
    assert feed["items"][0]["masked_phone"] == "+251 9XX XXX XXX"
    assert "evidence_note" not in feed["items"][0]
    assert "source" not in feed["items"][0]

    assert feed["items"][1]["phone_number"] == "+251911000002"
    assert feed["items"][1]["report_count"] == 3

    # Next page
    page2 = get_reported_numbers(limit=2, offset=2)
    assert len(page2["items"]) == 1
    assert page2["items"][0]["phone_number"] == "+251911000001"
    assert page2["has_more"] is False


def test_get_reported_numbers_search_filter(mock_db_layer):
    from backend.app.phone_reputation import submit_report, get_reported_numbers

    submit_report("0911222333", ["scam"], "Scam note")
    submit_report("0977444555", ["impersonation"], "Impersonation note")

    # Filter by operator prefix digits
    res_ethio = get_reported_numbers(query="0911")
    assert res_ethio["total"] == 1
    assert res_ethio["items"][0]["phone_number"] == "+251911222333"

    # Filter by category
    res_cat = get_reported_numbers(query="impersonation")
    assert res_cat["total"] == 1
    assert res_cat["items"][0]["phone_number"] == "+251977444555"


def test_reported_numbers_api_endpoint(mock_db_layer):
    from backend.app.phone_reputation import submit_report

    submit_report("0911234567", ["scam"], "Sensitive user note")

    response = client.get("/reported-numbers?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["phone_number"] == "+251911234567"
    assert item["masked_phone"] == "+251 9XX XXX XXX"
    assert item["report_count"] == 1
    assert item["categories"] == ["scam"]
    assert "evidence_note" not in item  # Privacy protection
    assert "source" not in item


def test_reported_numbers_api_endpoint_503_when_db_down(mock_db_layer):
    mock_db_layer.simulate_error = True
    response = client.get("/reported-numbers")
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]



# ---------------------------------------------------------------------------
# Anti-Abuse Deduplication & Rate Limiting Tests (Phase 1)
# ---------------------------------------------------------------------------

def test_duplicate_submission_does_not_inflate_count(mock_db_layer):
    """Submissions from the same reporter ID within 24h merge categories without incrementing count."""
    # First report from client 1
    res1 = phone_reputation.submit_report(
        "0911234567", ["scam"], "First report", reporter_id="192.168.1.10"
    )
    assert res1["status"] == "submitted"

    # Second report from same client 1 for same number
    res2 = phone_reputation.submit_report(
        "0911234567", ["phishing"], "Duplicate report", reporter_id="192.168.1.10"
    )
    assert res2["status"] == "already_reported"
    assert "was already recorded" in res2["explanation"]

    # Verify summary count is still 1, but categories were merged
    lookup = phone_reputation.lookup_phone_number("0911234567")
    assert lookup["report_count"] == 1
    assert set(lookup["categories"]) == {"scam", "phishing"}

    # Different client reporting the same number increments count to 2
    res3 = phone_reputation.submit_report(
        "0911234567", ["impersonation"], "Third party report", reporter_id="192.168.1.20"
    )
    assert res3["status"] == "updated"
    lookup2 = phone_reputation.lookup_phone_number("0911234567")
    assert lookup2["report_count"] == 2
    assert set(lookup2["categories"]) == {"scam", "phishing", "impersonation"}


def test_report_endpoint_deduplication_via_http(mock_db_layer):
    """Submitting duplicate reports to /report from same IP returns already_reported and keeps count 1."""
    # 1st request from IP
    headers = {"X-Forwarded-For": "203.0.113.195"}
    r1 = client.post(
        "/report",
        json={"phone_number": "0911234567", "categories": ["scam"], "evidence_note": "Scam call"},
        headers=headers,
    )
    assert r1.status_code == 200
    assert r1.json()["status"] == "submitted"

    # 2nd request from same IP
    r2 = client.post(
        "/report",
        json={"phone_number": "0911234567", "categories": ["phishing"]},
        headers=headers,
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "already_reported"

    # Report count is still 1
    chk = client.post("/check-number", json={"phone_number": "0911234567"})
    assert chk.json()["report_count"] == 1


def test_report_endpoint_rate_limiting(mock_db_layer):
    """Submissions exceeding the burst limit (5/min) receive HTTP 429."""
    from backend.app.rate_limiter import report_rate_limiter
    report_rate_limiter.reset()

    headers = {"X-Forwarded-For": "198.51.100.42"}
    # 5 successful submissions
    for i in range(5):
        resp = client.post(
            "/report",
            json={"phone_number": f"091123456{i}", "categories": ["scam"]},
            headers=headers,
        )
        assert resp.status_code == 200

    # 6th submission from same IP is rate limited
    blocked = client.post(
        "/report",
        json={"phone_number": "0911234569", "categories": ["scam"]},
        headers=headers,
    )
    assert blocked.status_code == 429
    assert "Too many reports" in blocked.json()["detail"]
    assert "Retry-After" in blocked.headers

    # Submission from a different IP still succeeds
    other_ip_resp = client.post(
        "/report",
        json={"phone_number": "0911234569", "categories": ["scam"]},
        headers={"X-Forwarded-For": "198.51.100.99"},
    )
    assert other_ip_resp.status_code == 200


def test_report_endpoint_strict_input_validation(mock_db_layer):
    """Verify robust validation of types, lengths, and constraints on /report."""
    # 1. Non-string phone number
    r = client.post("/report", json={"phone_number": 911234567, "categories": ["scam"]})
    assert r.status_code == 400
    assert "phone_number is required and must be a string" in r.json()["detail"]

    # 2. Oversized phone number string
    r = client.post("/report", json={"phone_number": "+251911234567" * 5, "categories": ["scam"]})
    assert r.status_code == 400
    assert "exceeds maximum allowed length" in r.json()["detail"]

    # 3. Categories not a list
    r = client.post("/report", json={"phone_number": "0911234567", "categories": "scam"})
    assert r.status_code == 400
    assert "categories must be a non-empty list" in r.json()["detail"]

    # 4. Categories list with non-string elements
    r = client.post("/report", json={"phone_number": "0911234567", "categories": [123]})
    assert r.status_code == 400
    assert "Each category in categories must be a string" in r.json()["detail"]

    # 5. More than 10 categories
    r = client.post("/report", json={"phone_number": "0911234567", "categories": ["scam"] * 11})
    assert r.status_code == 400
    assert "At most 10 categories" in r.json()["detail"]

    # 6. Non-string evidence note
    r = client.post("/report", json={"phone_number": "0911234567", "categories": ["scam"], "evidence_note": 12345})
    assert r.status_code == 400
    assert "evidence_note must be a string" in r.json()["detail"]

    # 7. Oversized evidence note (> 1000 chars)
    r = client.post("/report", json={"phone_number": "0911234567", "categories": ["scam"], "evidence_note": "A" * 1001})
    assert r.status_code == 400
    assert "evidence_note exceeds maximum allowed length" in r.json()["detail"]


# ---------------------------------------------------------------------------
# Dispute / False-Positive Reporting tests
# ---------------------------------------------------------------------------

def test_submit_dispute_unit_success(mock_db_layer):
    """Unit test: valid dispute submission records record in disputes table."""
    import hashlib
    result = phone_reputation.submit_dispute(
        phone="0911234567",
        explanation="This is an official hospital emergency dispatch number, not a scam.",
        contact_info="security@hospital.et",
        reporter_id="198.51.100.5",
    )
    assert result["status"] == "dispute_recorded"
    assert result["phone_number"] == "+251911234567"
    assert result["review_status"] == "pending"
    assert "queued for moderation review" in result["explanation"]

    assert len(mock_db_layer.disputes) == 1
    d = mock_db_layer.disputes[0]
    assert d["phone_e164"] == "+251911234567"
    assert d["country_code"] == "251"
    assert "hospital emergency" in d["explanation"]
    assert d["contact_info"] == "security@hospital.et"
    assert d["review_status"] == "pending"
    assert d["reporter_hash"] == phone_reputation.compute_reporter_hash("198.51.100.5")


def test_dispute_does_not_clear_or_modify_reports(mock_db_layer):
    """Dispute submission does NOT reset report count or clear reputation."""
    phone_reputation.submit_report("0911234567", ["scam"], "First report")
    phone_reputation.submit_report("0911234567", ["phishing"], "Second report")

    # Verify initial reported status
    chk_before = client.post("/check-number", json={"phone_number": "0911234567"})
    assert chk_before.status_code == 200
    assert chk_before.json()["report_count"] == 2
    assert chk_before.json()["status"] == "reported"

    # Submit dispute
    disp = client.post(
        "/dispute",
        json={
            "phone_number": "0911234567",
            "explanation": "This number was reassigned to our business last month.",
            "contact_info": "owner@business.et",
        },
    )
    assert disp.status_code == 200
    assert disp.json()["status"] == "dispute_recorded"

    # Verify report count remains untouched at 2
    chk_after = client.post("/check-number", json={"phone_number": "0911234567"})
    assert chk_after.status_code == 200
    data = chk_after.json()
    assert data["report_count"] == 2
    assert data["status"] == "reported"

    # Verify contact_info and explanation are NEVER leaked in public responses
    assert "owner@business.et" not in str(data)
    assert "reassigned to our business" not in str(data)

    # Verify reported-numbers list does not leak dispute info
    reported_list = client.get("/reported-numbers").json()
    assert "owner@business.et" not in str(reported_list)
    assert "reassigned to our business" not in str(reported_list)


def test_dispute_endpoint_http_validation(mock_db_layer):
    """Verify validation on POST /dispute."""
    # 1. Non-dict body
    r = client.post("/dispute", json=["not", "a", "dict"])
    assert r.status_code in (400, 422)

    # 2. Missing phone
    r = client.post("/dispute", json={"explanation": "Valid explanation exceeding 10 characters."})
    assert r.status_code == 400
    assert "phone_number is required" in r.json()["detail"]

    # 3. Non-string phone
    r = client.post("/dispute", json={"phone_number": 911234567, "explanation": "Valid explanation."})
    assert r.status_code == 400
    assert "phone_number is required and must be a string" in r.json()["detail"]

    # 4. Oversized phone
    r = client.post("/dispute", json={"phone_number": "+251911234567" * 4, "explanation": "Valid explanation."})
    assert r.status_code == 400
    assert "phone_number exceeds maximum" in r.json()["detail"]

    # 5. Invalid format phone
    r = client.post("/dispute", json={"phone_number": "12345", "explanation": "Valid explanation exceeding 10 characters."})
    assert r.status_code == 400
    assert "could not be validated" in r.json()["detail"]

    # 6. Missing explanation
    r = client.post("/dispute", json={"phone_number": "0911234567"})
    assert r.status_code == 400
    assert "explanation is required" in r.json()["detail"]

    # 7. Explanation too short (< 10 chars)
    r = client.post("/dispute", json={"phone_number": "0911234567", "explanation": "Too short"})
    assert r.status_code == 400
    assert "explanation must be at least 10 characters" in r.json()["detail"]

    # 8. Explanation too long (> 1000 chars)
    r = client.post("/dispute", json={"phone_number": "0911234567", "explanation": "A" * 1001})
    assert r.status_code == 400
    assert "explanation exceeds maximum" in r.json()["detail"]

    # 9. Non-string contact_info
    r = client.post("/dispute", json={"phone_number": "0911234567", "explanation": "Valid explanation text.", "contact_info": 12345})
    assert r.status_code == 400
    assert "contact_info must be a string" in r.json()["detail"]

    # 10. Oversized contact_info (> 254 chars)
    r = client.post("/dispute", json={"phone_number": "0911234567", "explanation": "Valid explanation text.", "contact_info": "c" * 255})
    assert r.status_code == 400
    assert "contact_info exceeds maximum" in r.json()["detail"]


def test_dispute_endpoint_rate_limiting(mock_db_layer):
    """Dispute submissions exceeding 5 per minute from the same IP receive HTTP 429."""
    from backend.app.rate_limiter import dispute_rate_limiter
    dispute_rate_limiter.reset()

    headers = {"X-Forwarded-For": "203.0.113.88"}
    # 5 successful submissions
    for i in range(5):
        resp = client.post(
            "/dispute",
            json={
                "phone_number": f"091123456{i}",
                "explanation": f"Valid dispute explanation number {i} for review.",
            },
            headers=headers,
        )
        assert resp.status_code == 200

    # 6th submission from same IP is rate limited
    blocked = client.post(
        "/dispute",
        json={
            "phone_number": "0911234569",
            "explanation": "Valid dispute explanation number 6 for review.",
        },
        headers=headers,
    )
    assert blocked.status_code == 429
    assert "Too many disputes submitted" in blocked.json()["detail"]
    assert "Retry-After" in blocked.headers

    # Submission from a different IP still succeeds
    other_resp = client.post(
        "/dispute",
        json={
            "phone_number": "0911234569",
            "explanation": "Valid dispute explanation from distinct client.",
        },
        headers={"X-Forwarded-For": "203.0.113.99"},
    )
    assert other_resp.status_code == 200


def test_dispute_endpoint_503_when_database_unavailable(mock_db_layer):
    """Database connection failure during dispute returns HTTP 503."""
    mock_db_layer.simulate_error = True
    resp = client.post(
        "/dispute",
        json={
            "phone_number": "0911234567",
            "explanation": "This number is incorrectly listed as suspicious.",
        },
    )
    assert resp.status_code == 503
    assert "database is temporarily unavailable" in resp.json()["detail"]


def test_reporter_hash_is_salted_and_different_from_plain_sha256():
    """Verify that reporter hashes use server-side salt and cannot be reversed via plain SHA-256."""
    import hashlib
    plain = hashlib.sha256(b"198.51.100.5").hexdigest()
    salted = phone_reputation.compute_reporter_hash("198.51.100.5")
    assert salted != plain
    assert len(salted) == 64


def test_admin_disputes_requires_analyst_auth():
    """Accessing dispute moderation endpoints without analyst token returns HTTP 401."""
    resp = client.get("/admin/disputes")
    assert resp.status_code == 401

    resp_update = client.post("/admin/disputes/1/status", json={"status": "resolved"})
    assert resp_update.status_code == 401


def test_admin_disputes_list_and_status_update(mock_db_layer):
    """Authorized analyst can list disputes and update their review status."""
    analyst_headers = {"Authorization": "Bearer test-analyst-token"}
    # Submit two disputes
    phone_reputation.submit_dispute(
        phone="0911234567",
        explanation="First dispute explanation exceeding ten chars.",
        contact_info="user1@example.com",
    )
    phone_reputation.submit_dispute(
        phone="0922334455",
        explanation="Second dispute explanation exceeding ten chars.",
        contact_info="user2@example.com",
    )

    # List disputes
    resp = client.get("/admin/disputes", headers=analyst_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["review_status"] == "pending"

    # Update status to 'under_review'
    up_resp = client.post(
        "/admin/disputes/1/status",
        headers=analyst_headers,
        json={"status": "under_review"},
    )
    assert up_resp.status_code == 200
    assert up_resp.json()["dispute"]["review_status"] == "under_review"


