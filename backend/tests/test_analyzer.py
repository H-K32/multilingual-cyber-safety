from backend.app.analyzer import analyze_message


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