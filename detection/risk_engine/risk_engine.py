from typing import Dict, List, Any

# Map specific threat categories to human-friendly explanations and recommendations
THREAT_DESCRIPTIONS = {
    "TELEBIRR_SCAM": {
        "explanation": "Detected unauthorized telebirr PIN/OTP or account lock demand designed to compromise mobile wallet funds.",
        "recommendation": "Never share your 6-digit telebirr PIN or OTP code with anyone. Official telebirr staff will never ask for your credentials."
    },
    "BANK_PHISHING": {
        "explanation": "Detected bank brand impersonation combined with urgent verification prompts or deceptive link redirection.",
        "recommendation": "Do not open any links or provide personal credentials. Contact your bank directly through official phone numbers or visit a local branch."
    },
    "CREDENTIAL_PHISHING": {
        "explanation": "Detected deceptive attempt to capture account passcodes, passwords, or login details.",
        "recommendation": "Do not enter your credentials on unverified websites. Change your password immediately if entered."
    },
    "PRIZE_SCAM": {
        "explanation": "Detected suspicious lottery or prize bait requiring advance fees, link clicks, or personal details.",
        "recommendation": "Ignore messages claiming unexpected rewards. Legitimate organizations do not require upfront payments to claim prizes."
    },
    "JOB_SCAM": {
        "explanation": "Detected work-from-home or recruitment scam requesting registration fees or personal details.",
        "recommendation": "Never pay money to secure a job opportunity. Verify employment offers through official corporate channels."
    },
    "DELIVERY_SCAM": {
        "explanation": "Detected fake parcel delivery notification demanding fee payment or personal details.",
        "recommendation": "Do not pay delivery fees via untrusted links. Check shipment status directly on the provider's official portal."
    },
    "ACCOUNT_TAKEOVER_ALERT": {
        "explanation": "Detected intimidation language threatening immediate account deactivation or legal consequences.",
        "recommendation": "Remain calm and verify your account status directly in your official banking or telecom application."
    },
    "SUSPICIOUS_LINK": {
        "explanation": "Detected high-risk URL indicators such as IP address hostname, lookalike domain, or suspicious extension.",
        "recommendation": "Avoid clicking on unfamiliar links sent via SMS, social media, or email messages."
    },
    "SOCIAL_ENGINEERING": {
        "explanation": "Detected multiple social-engineering tactics including urgency, fear, or psychological pressure.",
        "recommendation": "Exercise caution. Verify the sender identity before taking any requested action."
    },
    "BENIGN": {
        "explanation": "No known threat vectors or suspicious indicators were identified in this message.",
        "recommendation": "Message appears safe, but always maintain standard digital security awareness."
    }
}

INDICATOR_SCORES = {
    # Social Engineering Signals
    "urgency": 15,
    "fear_or_threat": 20,
    "reward_bait": 25,
    "financial_reward": 25,
    "credential_request": 25,
    "financial_request": 25,
    "possible_impersonation": 20,
    "account_verification_request": 15,
    "job_scam_indicator": 20,
    "delivery_scam_indicator": 20,
    
    # URL Intelligence Signals
    "url_shortener": 15,
    "ip_address_url": 30,
    "excessive_subdomains": 15,
    "url_contains_at_symbol": 25,
    "no_https": 10,
    "malformed_url": 20,
    "suspicious_tld": 15,
    "credential_path": 20,
    "lookalike_domain": 30,
    "punycode_or_unicode": 15,
}


def calculate_risk(indicators: List[str]) -> int:
    """Computes bounded raw score from combined rule and URL indicators."""
    score = sum(INDICATOR_SCORES.get(indicator, 0) for indicator in indicators)
    return min(score, 100)


def classify_risk(score: int) -> str:
    """Classifies numerical risk score into high-level category."""
    if score >= 70:
        return "HIGH_RISK"
    if score >= 35:
        return "SUSPICIOUS"
    return "SAFE"


def determine_threat_type(indicators: List[str], message: str = "") -> str:
    """Maps indicator sets and message keywords to threat categories."""
    msg_lower = message.lower()
    is_telebirr = "telebirr" in msg_lower or "ቴሌብር" in msg_lower
    is_cbe = "cbe" in msg_lower or "ንግድ ባንክ" in msg_lower or "commercial bank" in msg_lower

    if is_telebirr and ("credential_request" in indicators or "fear_or_threat" in indicators or "account_verification_request" in indicators):
        return "TELEBIRR_SCAM"

    if is_cbe and ("credential_request" in indicators or "fear_or_threat" in indicators or "lookalike_domain" in indicators or "suspicious_tld" in indicators):
        return "BANK_PHISHING"

    if "credential_request" in indicators:
        return "CREDENTIAL_PHISHING"

    if "financial_request" in indicators:
        return "FINANCIAL_SCAM"

    if "reward_bait" in indicators or "financial_reward" in indicators:
        return "PRIZE_SCAM"

    if "job_scam_indicator" in indicators:
        return "JOB_SCAM"

    if "delivery_scam_indicator" in indicators:
        return "DELIVERY_SCAM"

    if "possible_impersonation" in indicators:
        return "IMPERSONATION"

    if any(
        ind in indicators
        for ind in [
            "url_shortener",
            "ip_address_url",
            "excessive_subdomains",
            "url_contains_at_symbol",
            "malformed_url",
            "suspicious_tld",
            "lookalike_domain",
            "credential_path",
        ]
    ):
        return "SUSPICIOUS_LINK"

    if "urgency" in indicators or "fear_or_threat" in indicators:
        return "SOCIAL_ENGINEERING"

    return "BENIGN"


def evaluate_message_security(
    indicators: List[str],
    ml_probability: float = 0.0,
    message: str = ""
) -> Dict[str, Any]:
    """
    Main Risk Engine evaluation API combining indicators, ML probability,
    threat mapping, and explanation generation.
    """
    rule_score = calculate_risk(indicators)
    ml_score = int(ml_probability * 40)
    
    # Additive composite score capped at 100
    total_score = min(rule_score + ml_score, 100)

    # High-severity override for critical vector combinations
    if ("credential_request" in indicators or "otp_request" in indicators) and ("lookalike_domain" in indicators or "ip_address_url" in indicators):
        total_score = max(total_score, 85)

    classification = classify_risk(total_score)
    threat_type = determine_threat_type(indicators, message)
    threat_meta = THREAT_DESCRIPTIONS.get(threat_type, THREAT_DESCRIPTIONS["BENIGN"])

    return {
        "risk_score": total_score,
        "classification": classification,
        "threat_type": threat_type,
        "is_statistically_calibrated": False,
        "explanation": threat_meta["explanation"],
        "recommendation": threat_meta["recommendation"]
    }