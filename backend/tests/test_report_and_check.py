"""Tests for the /report and /check-number endpoints and submit_report logic."""

import csv

import pytest
from fastapi.testclient import TestClient

from backend.app import phone_reputation
from backend.app.main import app

client = TestClient(app)

CSV_FIELDS = [
    "phone_number",
    "country_code",
    "report_count",
    "categories",
    "source",
    "first_reported",
    "last_reported",
    "verification_status",
    "evidence_note",
]


def _empty_csv(path):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()


# ── submit_report unit tests ──────────────────────────────────────────────────


def test_submit_report_creates_new_record(tmp_path, monkeypatch):
    _empty_csv(tmp_path / "r.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "r.csv")

    result = phone_reputation.submit_report(
        "0911234567", ["scam", "phishing"], "Fake telebirr message received."
    )
    assert result["status"] == "submitted"
    assert "unverified" in result["explanation"]

    lookup = phone_reputation.lookup_phone_number("0911234567")
    assert lookup["status"] == "reported"
    assert lookup["report_count"] == 1
    assert "scam" in lookup["categories"]
    assert lookup["verification_status"] == "unverified"


def test_submit_report_increments_existing_record(tmp_path, monkeypatch):
    _empty_csv(tmp_path / "r.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "r.csv")

    phone_reputation.submit_report("0911234567", ["scam"], "First report.")
    result = phone_reputation.submit_report("0911234567", ["phishing"], "Second report.")

    assert result["status"] == "updated"
    lookup = phone_reputation.lookup_phone_number("0911234567")
    assert lookup["report_count"] == 2
    assert "scam" in lookup["categories"]
    assert "phishing" in lookup["categories"]


def test_submit_report_rejects_invalid_number(tmp_path, monkeypatch):
    _empty_csv(tmp_path / "r.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "r.csv")

    result = phone_reputation.submit_report("not-a-number", ["scam"], "")
    assert result["status"] == "invalid_number"


def test_submit_report_rejects_unknown_categories(tmp_path, monkeypatch):
    _empty_csv(tmp_path / "r.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "r.csv")

    result = phone_reputation.submit_report("0911234567", ["made_up_category"], "")
    assert result["status"] == "invalid_categories"


def test_submit_report_normalizes_ethiopian_formats(tmp_path, monkeypatch):
    _empty_csv(tmp_path / "r.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "r.csv")

    phone_reputation.submit_report("0911234567", ["spam_calls"], "Local format.")
    lookup = phone_reputation.lookup_phone_number("+251911234567")
    assert lookup["status"] == "reported"


def test_submit_report_truncates_long_evidence_note(tmp_path, monkeypatch):
    _empty_csv(tmp_path / "r.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "r.csv")

    long_note = "x" * 1000
    phone_reputation.submit_report("0911234567", ["scam"], long_note)
    lookup = phone_reputation.lookup_phone_number("0911234567")
    assert len(lookup["evidence_note"]) <= 500


# ── /report API endpoint tests ────────────────────────────────────────────────


def test_report_endpoint_accepts_valid_submission(tmp_path, monkeypatch):
    _empty_csv(tmp_path / "r.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "r.csv")

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


def test_report_endpoint_rejects_missing_phone(tmp_path, monkeypatch):
    _empty_csv(tmp_path / "r.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "r.csv")

    response = client.post("/report", json={"categories": ["scam"]})
    assert response.status_code == 400


def test_report_endpoint_rejects_empty_categories(tmp_path, monkeypatch):
    _empty_csv(tmp_path / "r.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "r.csv")

    response = client.post(
        "/report", json={"phone_number": "0911234567", "categories": []}
    )
    assert response.status_code == 400


def test_report_endpoint_rejects_invalid_number(tmp_path, monkeypatch):
    _empty_csv(tmp_path / "r.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "r.csv")

    response = client.post(
        "/report", json={"phone_number": "abc", "categories": ["scam"]}
    )
    assert response.status_code == 400


# ── /check-number API endpoint tests ─────────────────────────────────────────


def test_check_number_returns_no_reports_for_unlisted(tmp_path, monkeypatch):
    _empty_csv(tmp_path / "r.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "r.csv")

    response = client.post("/check-number", json={"phone_number": "0911234567"})
    assert response.status_code == 200
    assert response.json()["status"] == "no_reports_found"
    assert "does not establish" in response.json()["explanation"]


def test_check_number_returns_report_for_listed(tmp_path, monkeypatch):
    _empty_csv(tmp_path / "r.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "r.csv")

    phone_reputation.submit_report("0911234567", ["phishing"], "Test.")
    response = client.post("/check-number", json={"phone_number": "+251911234567"})
    assert response.status_code == 200
    assert response.json()["status"] == "reported"


def test_check_number_rejects_missing_phone():
    response = client.post("/check-number", json={})
    assert response.status_code == 400


def test_check_number_returns_invalid_for_bad_number(tmp_path, monkeypatch):
    _empty_csv(tmp_path / "r.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "r.csv")

    response = client.post("/check-number", json={"phone_number": "not-a-number"})
    assert response.status_code == 200
    assert response.json()["status"] == "invalid_number"
