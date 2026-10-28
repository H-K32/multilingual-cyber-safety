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
