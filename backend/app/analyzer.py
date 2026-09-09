from detection.rules.security_rules import detect_indicators
from detection.url_analysis.url_analyzer import analyze_urls
from detection.risk_engine.risk_engine import (
    calculate_risk,
    classify_risk,
    determine_threat_type,
)


def detect_language(message: str) -> tuple[str, bool]:
    """
    Very simple baseline language detector.

    Amharic Unicode block:
    U+1200–U+137F

    This will be replaced/improved by the NLP layer.
    """

    has_amharic = any(
        "\u1200" <= char <= "\u137F"
        for char in message
    )

    has_latin = any(
        ("a" <= char.lower() <= "z")
        for char in message
    )

    if has_amharic and has_latin:
        return "MIXED", True

    if has_amharic:
        return "AMHARIC", False

    if has_latin:
        return "ENGLISH", False

    return "UNKNOWN", False


def generate_recommendation(
    classification: str,
    threat_type: str,
) -> str:

    if classification == "HIGH_RISK":
        return (
            "Do not click links or provide credentials, "
            "financial information, OTPs, or passwords. "
            "Verify the message through an official channel."
        )

    if classification == "SUSPICIOUS":
        return (
            "Be cautious. Verify the sender and destination "
            "before clicking links or sharing information."
        )

    return (
        "No major risk indicators were detected. "
        "Continue using normal security precautions."
    )


def analyze_message(message: str) -> dict:

    language, code_switched = detect_language(message)

    security_indicators = detect_indicators(message)

    urls, url_indicators = analyze_urls(message)

    indicators = list(
        dict.fromkeys(
            security_indicators + url_indicators
        )
    )

    risk_score = calculate_risk(indicators)

    classification = classify_risk(risk_score)

    threat_type = determine_threat_type(indicators)

    recommendation = generate_recommendation(
        classification,
        threat_type,
    )

    return {
        "classification": classification,
        "risk_score": risk_score,
        "threat_type": threat_type,
        "language": language,
        "code_switched": code_switched,
        "indicators": indicators,
        "urls": urls,
        "recommendation": recommendation,
    }