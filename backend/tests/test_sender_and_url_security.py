# backend/tests/test_sender_and_url_security.py
"""
Automated test suite verifying sender identity, claimed-identity detection,
URL risk scoring, allowlist functionality, and safety overrides.
Covers the 8 core test cases required for Dagu's enhanced scam detection logic.
"""

import os
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.analyzer import analyze_message
from backend.app.phone_reputation import (
    verify_sender_identity,
    is_known_official_sender,
    get_known_official_senders,
    lookup_phone_number,
)
from detection.url_analysis.url_analyzer import (
    analyze_url,
    analyze_urls,
    is_verified_domain,
    get_verified_domains,
)
from detection.rules.security_rules import (
    detect_indicators,
    detect_claimed_identity,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test Case 1: Normal transaction notification from known sender (127 for Telebirr)
# ---------------------------------------------------------------------------

def test_telebirr_127_normal_amharic_transaction_notification_is_safe():
    """A normal Telebirr transaction receipt from shortcode 127 must not be flagged
    as impersonation or assigned an elevated risk score.
    """
    message = (
        "ውድ ደንበኛችን፡ 500.00 ብር ከ አበበ ቢቂላ (251911223344) በቴሌብር ተቀብለዋል። "
        "ቀሪ ሂሳብዎ 1,250.00 ብር ነው። የግብይት ቁጥር፡ TXN123456789።"
    )
    result = analyze_message(
        message,
        sender_phone="127",
    )

    assert "possible_impersonation" not in result["indicators"]
    assert "sender_identity_mismatch" not in result["indicators"]
    assert "financial_request" not in result["indicators"]
    assert result["classification"] == "SAFE"
    assert result["risk_score"] < 35
    assert result["threat_type"] == "BENIGN"
    assert result["sender_verification"]["is_known_sender"] is True


def test_telebirr_127_normal_english_transaction_notification_is_safe():
    """English transaction receipt from 127 must also remain safe without impersonation."""
    message = (
        "Dear customer, you have received 500.00 ETB from Abebe Bikila (0911223344) "
        "via telebirr. Your balance is 1,250.00 ETB. Txn ID: TXN987654."
    )
    result = analyze_message(
        message,
        sender_identifier="127",
    )

    assert "possible_impersonation" not in result["indicators"]
    assert "sender_identity_mismatch" not in result["indicators"]
    assert result["classification"] == "SAFE"
    assert result["risk_score"] < 35
    assert result["threat_type"] == "BENIGN"


# ---------------------------------------------------------------------------
# Test Case 2: Normal message from configured trusted sender
# ---------------------------------------------------------------------------

def test_configured_trusted_sender_994_safe_without_indicators():
    """A normal service message from 994 (Ethio Telecom) must not be assigned high risk."""
    message = "Dear customer, your monthly internet package expires in 3 days. Dial *999# to renew."
    result = analyze_message(
        message,
        sender_phone="994",
    )

    assert result["classification"] == "SAFE"
    assert result["risk_score"] < 35
    assert result["threat_type"] == "BENIGN"
    assert result["sender_verification"]["is_known_sender"] is True


def test_extensible_sender_allowlist_via_env_var(monkeypatch):
    """Verify that KNOWN_OFFICIAL_SENDERS_EXTRA adds new trusted senders dynamically."""
    monkeypatch.setenv(
        "KNOWN_OFFICIAL_SENDERS_EXTRA",
        '{"8112": {"organisation": "National Alert System", "legitimate_ids": ["8112"]}}'
    )
    registry = get_known_official_senders()
    assert "8112" in registry
    assert is_known_official_sender("8112") is True

    result = analyze_message(
        "Weather advisory for Addis Ababa: Expect rainfall this afternoon.",
        sender_phone="8112",
    )
    assert result["classification"] == "SAFE"
    assert result["sender_verification"]["is_known_sender"] is True


# ---------------------------------------------------------------------------
# Test Case 3: Message containing legitimate HTTPS URL
# ---------------------------------------------------------------------------

def test_legitimate_https_url_ethiotelecom_not_marked_high_risk():
    """A message containing an official Ethio Telecom HTTPS URL must not be high risk."""
    message = "Check out our new enterprise fiber services on our official website: https://www.ethiotelecom.et/services"
    result = analyze_message(message)

    assert "https://www.ethiotelecom.et/services" in result["urls"]
    assert result["risk_breakdown"]["url_indicators"] == []
    assert result["classification"] == "SAFE"
    assert result["risk_score"] < 35


def test_legitimate_https_url_cbe_not_marked_high_risk():
    """A message linking to official Commercial Bank of Ethiopia (cbe.com.et) is safe."""
    message = "Check official foreign exchange rates at https://cbe.com.et/en/exchange-rates"
    result = analyze_message(message)

    assert result["classification"] == "SAFE"
    assert result["risk_breakdown"]["url_indicators"] == []
    assert is_verified_domain("cbe.com.et") is True
    assert is_verified_domain("www.cbe.com.et") is True


def test_legitimate_cbe_mobile_receipt_subdomain_is_safe():
    """Verify that official CBE mobile receipt subdomains (mbreciept.cbe.com.et) are recognized as SAFE."""
    url = "https://mbreciept.cbe.com.et/v2-hfHCxNIfePxTiean"
    result = analyze_message(
        f"CBE Birr: Your transaction was completed. Receipt: {url}",
        sender_phone="8397",
    )
    assert result["classification"] == "SAFE"
    assert result["risk_score"] == 0
    assert result["threat_type"] == "BENIGN"
    assert result["risk_breakdown"]["url_indicators"] == []
    assert is_verified_domain("mbreciept.cbe.com.et") is True


def test_extensible_verified_domains_allowlist_via_env(monkeypatch):
    """Verify that VERIFIED_DOMAINS_EXTRA extends the verified domains list."""
    monkeypatch.setenv("VERIFIED_DOMAINS_EXTRA", "official-fintech.et,partner.gov.et")
    domains = get_verified_domains()
    assert "official-fintech.et" in domains
    assert "partner.gov.et" in domains
    assert is_verified_domain("sub.official-fintech.et") is True


# ---------------------------------------------------------------------------
# Test Case 4: Passive bank or telecom mention does not trigger impersonation
# ---------------------------------------------------------------------------

def test_passive_deposit_mention_does_not_trigger_impersonation_english():
    """'Your bank account received a deposit' must not flag possible_impersonation."""
    message = "Your bank account received a deposit of 1,000 ETB. Reference: DEP45678."
    result = analyze_message(message)

    assert "possible_impersonation" not in result["indicators"]
    assert "financial_request" not in result["indicators"]
    assert result["classification"] == "SAFE"


def test_passive_deposit_mention_does_not_trigger_impersonation_amharic():
    """Amharic deposit receipt notification must not trigger possible_impersonation."""
    message = "በንግድ ባንክ ሂሳብዎ 1,000 ብር ገቢ ተደርጓል። ቀሪ ሂሳብዎ 5,000 ብር ነው።"
    result = analyze_message(message)

    assert "possible_impersonation" not in result["indicators"]
    assert "financial_request" not in result["indicators"]
    assert result["classification"] == "SAFE"


def test_explicit_claim_triggers_claimed_identity_detection():
    """Explicit claim of representation triggers detect_claimed_identity."""
    assert detect_claimed_identity("We are Telebirr customer support.") == "telebirr"
    assert detect_claimed_identity("ይህ ከንግድ ባንክ የደንበኞች አገልግሎት የተላከ ነው።") == "cbe"
    assert detect_claimed_identity("Your bank account received a deposit.") is None


# ---------------------------------------------------------------------------
# Test Case 5: Phishing message asking for PIN/OTP remains HIGH_RISK even from known sender
# ---------------------------------------------------------------------------

def test_phishing_asking_for_telebirr_pin_from_127_remains_high_risk():
    """A phishing message demanding a PIN or OTP from sender 127 must remain high risk."""
    message = "Dear customer, send your 6-digit telebirr PIN immediately to avoid account suspension."
    result = analyze_message(
        message,
        sender_phone="127",
    )

    assert "credential_request" in result["indicators"]
    assert result["classification"] == "HIGH_RISK"
    assert result["risk_score"] >= 70
    assert (
        "critical_credential_request_override" in result["risk_breakdown"]["overrides_applied"]
        or "critical_credential_harvesting_override" in result["risk_breakdown"]["overrides_applied"]
    )


def test_phishing_asking_for_otp_in_amharic_remains_high_risk():
    """Amharic OTP request from a claimed or official sender must remain high risk."""
    message = "የይለፍ ቃልዎን ወይም የላክንልዎትን የኦቲፒ (OTP) ቁጥር አሁኑኑ ይላኩ።"
    result = analyze_message(
        message,
        sender_phone="994",
        claimed_sender="ethiotelecom",
    )

    assert "credential_request" in result["indicators"]
    assert result["classification"] == "HIGH_RISK"
    assert result["risk_score"] >= 70


# ---------------------------------------------------------------------------
# Test Case 6: Lookalike domain correctly detected as suspicious or high risk
# ---------------------------------------------------------------------------

def test_lookalike_cbe_top_domain_detected():
    """Lookalike domain cbe-verify.top must trigger lookalike_domain and suspicious_tld."""
    indicators = analyze_url("http://cbe-verify.top/login")
    assert "lookalike_domain" in indicators
    assert "suspicious_tld" in indicators
    assert "credential_path" in indicators
    assert "no_https" in indicators

    result = analyze_message("Notice from bank: Verify account at http://cbe-verify.top/login")
    assert "lookalike_domain" in result["indicators"]
    assert result["classification"] in ("SUSPICIOUS", "HIGH_RISK")


def test_lookalike_telebirr_domain_detected():
    """telebirr-login.com must trigger lookalike_domain."""
    indicators = analyze_url("https://telebirr-login.com/auth")
    assert "lookalike_domain" in indicators
    assert "credential_path" in indicators


# ---------------------------------------------------------------------------
# Test Case 7: Unknown sender or unseen benign URL not treated as malicious
# ---------------------------------------------------------------------------

def test_unseen_benign_url_not_treated_as_malicious():
    """An unfamiliar but clean domain with HTTPS must receive 0 URL penalty points."""
    url = "https://independentblog.org/ethiopian-cuisine"
    indicators = analyze_url(url)
    assert indicators == []

    result = analyze_message(
        f"Check out this interesting article: {url}",
        sender_phone="+251911999888",
    )
    assert result["risk_breakdown"]["url_indicators"] == []
    assert result["classification"] == "SAFE"
    assert result["risk_score"] < 35


# ---------------------------------------------------------------------------
# Test Case 8: Multilingual regression checks (Amharic, English, Mixed)
# ---------------------------------------------------------------------------

def test_multilingual_amharic_scam_detection():
    """Amharic scam with account lock threat and credential demand is HIGH_RISK."""
    message = "የእርስዎ የቴሌብር ሂሳብ ታግዷል። የምስጢር ቁጥርዎን አሁኑኑ ይላኩ"
    result = analyze_message(message)

    assert result["classification"] == "HIGH_RISK"
    assert result["language"] == "AMHARIC"
    assert "credential_request" in result["indicators"]


def test_multilingual_english_prize_scam_detection():
    """English lottery scam with advance fee is PRIZE_SCAM and HIGH_RISK."""
    message = "Congratulations! You won 100,000 Birr cash prize. Send 500 Birr registration fee to claim."
    result = analyze_message(message)

    assert result["classification"] == "HIGH_RISK"
    assert result["threat_type"] == "PRIZE_SCAM"
    assert "reward_bait" in result["indicators"]
    assert "financial_request" in result["indicators"]


def test_multilingual_mixed_language_detection():
    """Code-switched Amharic-English message is detected as MIXED."""
    message = "እንኳን ደስ አለዎት! You won 50,000 ብር."
    result = analyze_message(message)

    assert result["language"] == "MIXED"
    assert result["code_switched"] is True
