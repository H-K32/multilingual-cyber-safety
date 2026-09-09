"""
security_rules.py

Rule-Based Security Detection Layer for the Multilingual Cyber-Safety Assistant.
Supports English, Amharic (አማርኛ), and English-Amharic code-switched messaging.

This module extracts deterministic security indicators (threat vectors) from digital
communications (SMS, Telegram, Email, WhatsApp, etc.) without making final risk
classifications or executing external network calls.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Pattern, Set


# ==============================================================================
# TEXT NORMALIZATION HELPERS
# ==============================================================================

def normalize_text(text: str) -> str:
    """
    Safely normalizes incoming text while strictly preserving Amharic Unicode characters,
    URLs, numbers, and security-relevant punctuation.

    Args:
        text: Raw input message string.

    Returns:
        Normalized string suitable for regex matching.
    """
    if not text:
        return ""

    # 1. Unicode Normalization (NFC preserves combined characters cleanly)
    normalized = unicodedata.normalize("NFC", text)

    # 2. Convert standard Latin characters to lowercase (leaves Ethiopic untouched)
    normalized = normalized.lower()

    # 3. Strip zero-width and invisible control characters used in evasion
    normalized = re.sub(r"[\u200B-\u200D\uFEFF]", "", normalized)

    # 4. Collapse excessive internal spacing/tabs without stripping newlines
    normalized = re.sub(r"[ \t]+", " ", normalized)

    return normalized.strip()


# ==============================================================================
# PATTERN GROUPS & REGEX REGISTRY
# ==============================================================================

# 1. Urgency & Time-Pressure Language
_URGENCY_PATTERNS: List[str] = [
    r"\b(immediately|urgent|urgently|right\s+now|asap|at\s+once|within\s+\d+\s*(hours?|hrs?|mins?|minutes?))\b",
    r"(አሁኑኑ|በፍጥነት|አሁንም|አሁኑን|በ\d+\s*(ሰዓት|ደቂቃ)\s*ውስጥ|ሳይዘገዩ|አጣዳፊ|በአስቸኳይ)",
    r"\b(act\s+now|limited\s+time|expires?\s+soon|due\s+today)\b",
]

# 2. Threat, Fear & Penalization Language
_FEAR_PATTERNS: List[str] = [
    r"\b(will\s+be\s+(suspended|blocked|terminated|closed|deactivated|frozen|restricted|deleted))\b",
    r"\b(legal\s+action|police|arrest|lawsuit|prosecution|penalty|fine)\b",
    r"(ይዘጋል|ይገደባል|ይ ታገዳል|ይሰረዛል|እርምጃ\s*ይወሰዳል|ወደ\s*ህግ|ፖሊስ|እስራት|ክስ)",
    r"\b(suspicious\s+activity|unauthorized\s+access|security\s+breach|account\s+compromised)\b",
    r"(ያልተፈቀደ\s*ግቤት|የደህንነት\s*ስጋት|ተጠርጣሪ\s*እንቅስቃሴ|ስጋት\s*ተገኝቷል)",
]

# 3. Financial Bait, Prize & Lottery Scams
_REWARD_PATTERNS: List[str] = [
    r"\b(congratulations?|you\s+won|winner|claim\s+your|jackpot|cash\s+prize|selected\s+for)\b",
    r"(እንኳን\s+ደስ\s+አለዎት|እድለኛ|አሸንፈዋል|ሽልማት|ተሸላሚ|እጣዎ|የገንዘብ\s*ሽልማት)",
    r"\b(\d+[\d,]*\s*(birr|ብር|usd|\$|etb|dollars?))\b.*?\b(won|prize|reward|grant|bonus|gift)\b",
    r"\b(won|prize|reward|grant|bonus|gift)\b.*?\b(\d+[\d,]*\s*(birr|ብር|usd|\$|etb|dollars?))\b",
    r"(ነፃ\s*ስጦታ|ነፃ\s*ካርድ|ነፃ\s*ቦነስ|100%\s*ትርፍ)",
]

# 4. Credential & Authentication Requests (Passwords, PINs, OTPs)
_CREDENTIAL_PATTERNS: List[str] = [
    r"\b(one[- ]time\s+passcode|otp|verification\s+code|security\s+code|pin|password|secret\s+key)\b",
    r"(የምስጢር\s*ቁጥር|ኦቲፒ|የማረጋገጫ\s*ኮድ|ፓስወርድ|ፒን\s*ቁጥር|ይለፍ\s*ቃል)",
    r"\b(send|share|provide|enter|reply\s+with|forward)\b.*?\b(otp|code|pin|password)\b",
    r"(ላክልኝ|ላክ|ስጠኝ|አስገባ|ግለጽ)\b.*?\b(ኦቲፒ|የምስጢር\s*ቁጥር|ኮድ|ፓስወርድ|ፒን)",
    r"\b(otp|code|pin|password)\b.*?(ላክልኝ|ላክ|ስጠኝ|አስገባ)",
]

# 5. Financial Requests, Transfers & Payment Demands
_FINANCIAL_PATTERNS: List[str] = [
    r"\b(send|transfer|deposit|pay|wire|recharge)\b.*?\b(money|funds|cash|birr|ብር|etb|\$|usd|airtime|balance)\b",
    r"(ገንዘብ\s*ላክ|ብር\s*ክፈል|ገንዘብ\b.*?\bክፈል|አስገባ|አየር\s*ሰዓት|ካርድ\s*ላክ|ሞላ|ቴሌብር|telebirr)",
    r"\b(processing\b.*?\bfee|activation\b.*?\bfee|advance\b.*?\bpayment|tax\b.*?\bpayment)\b",
    r"(የአገልግሎት\s*ክፍያ|የማስኬጃ|ቅድመ\s*ክፍያ|ታክስ\s*ክፈል)",
]

# 6. Impersonation of Banks, Telecoms & Official Bodies
_IMPERSONATION_PATTERNS: List[str] = [
    r"\b(cbe|commercial\s+bank|bank\s+of\s+ethiopia|telebirr|ethio\s*telecom|boa|awash\s+bank|dashen\s+bank|cbe\s*birr)\b",
    r"(ንግድ\s*ባንክ|ኢትዮ\s*ቴሌኮም|ቴሌብር|አዋሽ\s*ባንክ|ዳሽን\s*ባንክ|አቢሲንያ\s*ባንክ)",
    r"\b(customer\s+support|security\s+team|helpdesk|admin|official\s+notice|system\s+administrator)\b",
    r"(የደንበኞች\s*አገልግሎት|የደህንነት\s*ክፍል|ኦፊሴላዊ\s*መልእክት|የስርዓት\s*አስተዳዳሪ)",
    r"\b(fbi|revenue\s+authority|customs|ethiopian\s+government|ministry)\b",
    r"(የገቢዎች\s*ሚኒስቴር|ጉሙሩክ|መንግስታዊ|የኢትዮጵያ\s*ንግድ\s*ባንክ)",
]

# 7. Account Verification & Login Phishing
_VERIFICATION_PATTERNS: List[str] = [
    r"\b(verify|confirm|validate|update|reactivate)\b.*?\b(account|identity|details|profile|wallet|information)\b",
    r"(መለያዎን?\s*ያረጋግጡ|መረጃዎን?\s*ያዘምኑ|አካውንትዎን?\s*ያረጋግጡ|ያረጋግጡ|ማረጋገጫ)",
    r"\b(click\s+here\s+to\s+(verify|login|log\s+in|confirm|update))\b",
    r"\b(login\s+to\s+(your\s+)?account|sign\s+in\s+here)\b",
    r"(ለመግባት\s*እዚህ\s*ይጫኑ|ወደ\s*መለያዎ\s*ይግቡ|መለያዎን?\s*ለማደስ)",
]

# 8. Suspicious Calls to Action & Link Indicators
_CTA_PATTERNS: List[str] = [
    r"\b(click\s+(on\s+)?(this|the)?\s*link|open\s+(this|the)?\s*link|visit\s+(our)?\s*website|tap\s+here)\b",
    r"(እዚህ\s*ይጫኑ|ሊንኩን\s*ይክፈቱ|ተጫን|ይጎብኙ|እዚህ\0*ይግቡ)",
    r"(https?://|www\.|bit\.ly|t\.me|tinyurl\.com|cutt\.ly|ngrok\.io|serveo\.net)",
    r"\b(fill\s+out\s+(this|the)\s+form|download\s+attachment|install\s+this\s+app)\b",
    r"(ፎርሙን\s*ይምሉ|አፕሊኬሽኑን\s*ያወርዱ|አፕ\s*ጭን)",
]

# 9. Fake Job, Recruitment & Task Scams
_JOB_SCAM_PATTERNS: List[str] = [
    r"\b(work\s+from\s+home|online\s+job|daily\s+income|earn\s+\d+\s*(birr|\$|usd)\s*per\s*day|part[- ]time\s+job)\b",
    r"(የቤት\s*ውስጥ\s*ስራ|የኦንላይን\s*ስራ|በቀን\s*\d+\s*ብር\s*ያግኙ|ትርፍ\s*ሰዓት\s*ስራ|ቀሊል\s*ስራ)",
    r"\b(no\s+experience\s+needed|hiring\s+immediately|guaranteed\s+income)\b",
    r"(ያለ\s*ልምድ|አሁኑኑ\s*የሚቀጠር|የተረጋገጠ\s*ገቢ)",
]

# 10. Fake Delivery & Package Scams
_DELIVERY_SCAM_PATTERNS: List[str] = [
    r"\b(package\s+(delivery|pending|held|failed)|parcel\s+(arrived|stopped)|shipment\s+delayed)\b",
    r"(እቃዎ\s*ደርሷል|ፓኬጅ|ፖስታ\s*ታግዷል|የስጦታ\s*እቃ|ትራንስፖርት\s*ክፍያ)",
    r"\b(update\s+(your\s+)?address\s+for\s+delivery|pay\s+delivery\s+fee)\b",
]

# 11. Investment & Crypto Scams
_INVESTMENT_SCAM_PATTERNS: List[str] = [
    r"\b(crypto\s*investment|forex\s*trading|double\s+your\s+(money|investment)|guaranteed\s+profit|return\s+on\s+investment|roi)\b",
    r"(ክሪፕቶ|ፎሬክስ|ገንዘብዎን\s*እጥፍ\s*ያድርጉ|የተረጋገጠ\s*ትርፍ|አስተማማኝ\s*ኢንቨስትመንት)",
    r"\b(invest\s+\d+.*?\bget\s+\d+)\b",
]


# Compile regex patterns for efficient execution
def _compile_group(patterns: List[str]) -> List[Pattern[str]]:
    return [re.compile(p, re.IGNORECASE | re.UNICODE) for p in patterns]


_COMPILED_RULES: Dict[str, List[Pattern[str]]] = {
    "urgency": _compile_group(_URGENCY_PATTERNS),
    "fear_or_threat": _compile_group(_FEAR_PATTERNS),
    "reward_bait": _compile_group(_REWARD_PATTERNS),
    "credential_request": _compile_group(_CREDENTIAL_PATTERNS),
    "financial_request": _compile_group(_FINANCIAL_PATTERNS),
    "possible_impersonation": _compile_group(_IMPERSONATION_PATTERNS),
    "account_verification_request": _compile_group(_VERIFICATION_PATTERNS),
    "suspicious_call_to_action": _compile_group(_CTA_PATTERNS),
    "job_scam_indicator": _compile_group(_JOB_SCAM_PATTERNS),
    "delivery_scam_indicator": _compile_group(_DELIVERY_SCAM_PATTERNS),
    "investment_scam_indicator": _compile_group(_INVESTMENT_SCAM_PATTERNS),
}


# ==============================================================================
# MAIN PUBLIC API
# ==============================================================================

def detect_indicators(message: str) -> List[str]:
    """
    Analyzes an input message and returns a deterministic list of security indicators.

    Does NOT decide overall risk level (e.g., BENIGN or MALICIOUS). Returns unique,
    sorted indicator tags triggered by rule matches.

    Args:
        message: Raw message text (English, Amharic, or Code-switched).

    Returns:
        Sorted list of unique string indicator identifiers.
    """
    if not message or not isinstance(message, str):
        return []

    normalized = normalize_text(message)
    triggered_indicators: Set[str] = set()

    for indicator_name, compiled_patterns in _COMPILED_RULES.items():
        for pattern in compiled_patterns:
            if pattern.search(normalized):
                triggered_indicators.add(indicator_name)
                break  # Single hit per category is sufficient

    # Compound Security Logic: Synthesize compound threats based on rule combinations
    if "possible_impersonation" in triggered_indicators and (
        "fear_or_threat" in triggered_indicators or "account_verification_request" in triggered_indicators
    ):
        triggered_indicators.add("fake_account_suspension_warning")

    if "credential_request" in triggered_indicators and "possible_impersonation" in triggered_indicators:
        triggered_indicators.add("credential_theft_attempt")

    if "reward_bait" in triggered_indicators and "financial_request" in triggered_indicators:
        triggered_indicators.add("advance_fee_scam_indicator")

    return sorted(list(triggered_indicators))