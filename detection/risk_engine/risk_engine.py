INDICATOR_SCORES = {
    "urgency": 15,
    "financial_reward": 25,
    "credential_request": 25,
    "financial_request": 25,
    "possible_impersonation": 20,
    "url_shortener": 15,
    "ip_address_url": 30,
    "excessive_subdomains": 15,
    "url_contains_at_symbol": 25,
    "no_https": 10,
    "malformed_url": 20,
}


def calculate_risk(indicators: list[str]) -> int:
    score = sum(
        INDICATOR_SCORES.get(indicator, 0)
        for indicator in indicators
    )

    return min(score, 100)


def classify_risk(score: int) -> str:
    if score >= 70:
        return "HIGH_RISK"

    if score >= 35:
        return "SUSPICIOUS"

    return "SAFE"


def determine_threat_type(indicators: list[str]) -> str:
    if "credential_request" in indicators:
        return "CREDENTIAL_PHISHING"

    if "financial_request" in indicators:
        return "FINANCIAL_SCAM"

    if "financial_reward" in indicators:
        return "PRIZE_SCAM"

    if "possible_impersonation" in indicators:
        return "IMPERSONATION"

    if any(
        indicator in indicators
        for indicator in [
            "url_shortener",
            "ip_address_url",
            "excessive_subdomains",
            "url_contains_at_symbol",
            "malformed_url",
        ]
    ):
        return "SUSPICIOUS_LINK"

    if "urgency" in indicators:
        return "SOCIAL_ENGINEERING"

    return "BENIGN"