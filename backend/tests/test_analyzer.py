from fastapi.testclient import TestClient

from backend.app.analyzer import analyze_message
from backend.app.main import app


client = TestClient(app)


def test_benign_message():
    result = analyze_message(
        "Hi, I will meet you at the university library at 3 PM."
    )

    assert result["classification"] == "SAFE"
    assert result["threat_type"] == "BENIGN"


def test_prize_scam():
    result = analyze_message(
        "Congratulations! You won 50,000 ETB. "
        "Click here: http://bit.ly/claim"
    )

    assert "reward_bait" in result["indicators"]
    assert "url_shortener" in result["indicators"]
    assert "reward_bait" in result["indicators"]


def test_mixed_language():
    result = analyze_message(
        "እንኳን ደስ አለዎት! You won 50,000 ብር."
    )

    assert result["language"] == "MIXED"
    assert result["code_switched"] is True


def test_suspicious_url():
    result = analyze_message(
        "Verify your account: http://bit.ly/verify"
    )

    assert "url_shortener" in result["indicators"]


def test_empty_input_api_rejected():
    response = client.post("/analyze", json={"message": "  "})
    assert response.status_code == 400


def test_api_response_contains_expected_fields():
    response = client.post(
        "/analyze",
        json={"message": "Your account will be suspended today. Verify immediately. http://bit.ly/verify"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(
        {
            "classification",
            "risk_score",
            "threat_type",
            "language",
            "code_switched",
            "confidence",
            "indicators",
            "urls",
            "recommendation",
            "explanation",
        }
    ).issubset(payload.keys())


def test_api_response_includes_new_fields():
    response = client.post(
        "/analyze",
        json={
            "message": "Your account will be suspended. Verify now.",
            "sender_phone": "0911234567",
            "claimed_sender": "994",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "sender_verification" in payload
    assert "numbers_in_message" in payload
    assert payload["sender_verification"]["status"] == "mismatch"
    assert "sender_identity_mismatch" in payload["indicators"]


def test_api_claimed_sender_match_does_not_add_mismatch_indicator():
    response = client.post(
        "/analyze",
        json={
            "message": "Your account is active.",
            "sender_phone": "994",
            "claimed_sender": "994",
        },
    )
    assert response.status_code == 200
    assert "sender_identity_mismatch" not in response.json()["indicators"]
