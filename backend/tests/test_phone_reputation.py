import csv

from backend.app import phone_reputation
from backend.app.analyzer import analyze_message


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


def _write_synthetic_report(path, verification_status="unverified"):
    with path.open("w", encoding="utf-8", newline="") as dataset:
        writer = csv.DictWriter(dataset, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerow(
            {
                "phone_number": "+251911234567",
                "country_code": "251",
                "report_count": "2",
                "categories": "spam_calls|phishing",
                "source": "synthetic test fixture only",
                "first_reported": "2026-01-01",
                "last_reported": "2026-01-02",
                "verification_status": verification_status,
                "evidence_note": "Synthetic fixture; not a real report.",
            }
        )


def test_equivalent_ethiopian_mobile_formats_normalize_to_the_same_number():
    expected = ("+251911234567", "251")
    assert phone_reputation.normalize_phone_number("0911234567") == expected
    assert phone_reputation.normalize_phone_number("+251 91 123 4567") == expected
    assert phone_reputation.normalize_phone_number("00251911234567") == expected
    assert phone_reputation.normalize_phone_number("0711234567") == (
        "+251711234567",
        "251",
    )


def test_distinct_and_invalid_numbers_are_not_collapsed():
    assert phone_reputation.normalize_phone_number("0911234568") == (
        "+251911234568",
        "251",
    )
    assert phone_reputation.normalize_phone_number("09112345") == (None, None)
    assert phone_reputation.normalize_phone_number("+2510911234567") == (
        None,
        None,
    )
    assert phone_reputation.normalize_phone_number("+99912345678") == (
        None,
        None,
    )


def test_lookup_skips_missing_and_invalid_numbers(tmp_path, monkeypatch):
    _write_synthetic_report(tmp_path / "reports.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "reports.csv")

    assert phone_reputation.lookup_phone_number(None)["status"] == "not_provided"
    assert phone_reputation.lookup_phone_number("not a number")["status"] == (
        "invalid_number"
    )


def test_matching_local_and_international_numbers_returns_report_evidence(
    tmp_path, monkeypatch
):
    _write_synthetic_report(tmp_path / "reports.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "reports.csv")

    local_result = phone_reputation.lookup_phone_number("0911234567")
    international_result = phone_reputation.lookup_phone_number("+251911234567")

    assert local_result == international_result
    assert local_result["status"] == "reported"
    assert local_result["report_count"] == 2
    assert local_result["categories"] == ["spam_calls", "phishing"]
    assert local_result["verification_status"] == "unverified"
    assert "do not confirm" in local_result["explanation"]


def test_unverified_and_verified_reports_are_distinguished(tmp_path, monkeypatch):
    dataset = tmp_path / "reports.csv"
    _write_synthetic_report(dataset, "unverified")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", dataset)
    assert "unverified community reports" in phone_reputation.lookup_phone_number(
        "+251911234567"
    )["explanation"]

    _write_synthetic_report(dataset, "verified")
    assert "not proof" in phone_reputation.lookup_phone_number("+251911234567")[
        "explanation"
    ]


def test_unlisted_number_is_not_described_as_safe(tmp_path, monkeypatch):
    _write_synthetic_report(tmp_path / "reports.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "reports.csv")

    result = phone_reputation.lookup_phone_number("0911234568")

    assert result["status"] == "no_reports_found"
    assert "does not establish" in result["explanation"]


def test_source_and_phone_reputation_do_not_change_text_risk_score(
    tmp_path, monkeypatch
):
    _write_synthetic_report(tmp_path / "reports.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "reports.csv")
    message = "Let's meet at the university library this afternoon."

    ordinary = analyze_message(message)
    with_context = analyze_message(
        message,
        message_source="WhatsApp",
        sender_phone="0911234567",
    )

    assert with_context["risk_score"] == ordinary["risk_score"]
    assert with_context["classification"] == ordinary["classification"]
    assert with_context["phone_reputation"]["status"] == "reported"
    assert "does not affect" in with_context["explanations"]["context"]


def test_message_source_does_not_change_malicious_message_risk():
    message = "Your account will be suspended. Verify immediately."

    sms_result = analyze_message(message, message_source="SMS")
    email_result = analyze_message(message, message_source="Email")

    assert sms_result["risk_score"] == email_result["risk_score"]
    assert sms_result["classification"] == email_result["classification"]


def test_backward_compatible_analysis_defaults_to_text_without_context():
    result = analyze_message("A plain, ordinary message.")

    assert result["input_method"] == "text"
    assert result["message_source"] is None
    assert result["phone_reputation"]["status"] == "not_provided"


# ── verify_sender_identity ────────────────────────────────────────────────────


def test_sender_identity_match_for_known_shortcode():
    result = phone_reputation.verify_sender_identity("994", "994")
    assert result["status"] == "match"
    assert result["risk_indicator"] is False


def test_sender_identity_mismatch_flags_risk():
    result = phone_reputation.verify_sender_identity("0911234567", "994")
    assert result["status"] == "mismatch"
    assert result["risk_indicator"] is True
    assert "suspicious" in result["explanation"].lower()


def test_sender_identity_unknown_claimed_identity_is_not_flagged():
    result = phone_reputation.verify_sender_identity("0911234567", "unknownorg")
    assert result["status"] == "unknown_identity"
    assert result["risk_indicator"] is False


def test_sender_identity_skipped_when_no_sender():
    result = phone_reputation.verify_sender_identity(None, "994")
    assert result["status"] == "not_checked"
    assert result["risk_indicator"] is False


def test_sender_identity_skipped_when_no_claimed_identity():
    result = phone_reputation.verify_sender_identity("994", None)
    assert result["status"] == "not_checked"
    assert result["risk_indicator"] is False


def test_sender_identity_mismatch_escalates_risk_score():
    # A benign message from a mismatched sender should be escalated to SUSPICIOUS
    result = analyze_message(
        "Your account is active.",
        sender_phone="0911234567",
        claimed_sender="994",
    )
    assert result["sender_verification"]["status"] == "mismatch"
    assert result["classification"] in {"SUSPICIOUS", "HIGH_RISK"}
    assert result["risk_score"] >= 55
    assert "sender_identity_mismatch" in result["indicators"]


def test_sender_identity_match_does_not_inflate_risk():
    result = analyze_message(
        "Your account is active.",
        sender_phone="994",
        claimed_sender="994",
    )
    assert result["sender_verification"]["status"] == "match"
    assert "sender_identity_mismatch" not in result["indicators"]


# ── extract_phone_numbers_from_text ──────────────────────────────────────────


def test_extract_phone_numbers_finds_local_format():
    numbers = phone_reputation.extract_phone_numbers_from_text(
        "Please call 0911234567 for assistance."
    )
    assert "+251911234567" in numbers


def test_extract_phone_numbers_finds_international_format():
    numbers = phone_reputation.extract_phone_numbers_from_text(
        "Contact +251911234567 or +251711234567."
    )
    assert "+251911234567" in numbers
    assert "+251711234567" in numbers


def test_extract_phone_numbers_deduplicates():
    numbers = phone_reputation.extract_phone_numbers_from_text(
        "Call 0911234567 or +251911234567."
    )
    assert numbers.count("+251911234567") == 1


def test_extract_phone_numbers_returns_empty_for_no_numbers():
    numbers = phone_reputation.extract_phone_numbers_from_text(
        "No phone numbers here."
    )
    assert numbers == []


def test_numbers_in_message_included_in_analysis_response(tmp_path, monkeypatch):
    _write_synthetic_report(tmp_path / "reports.csv")
    monkeypatch.setattr(phone_reputation, "DATASET_PATH", tmp_path / "reports.csv")

    result = analyze_message(
        "Suspicious message. Call back: 0911234567.",
    )
    assert any(
        entry["phone_number"] == "+251911234567"
        for entry in result["numbers_in_message"]
    )
