import re
from urllib.parse import urlparse

URL_PATTERN = r"https?://[^\s]+"

SHORTENED_DOMAINS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "is.gd",
    "cutt.ly",
    "shorturl.at",
    "rb.gy",
    "ow.ly",
    "tiny.cc",
}

SUSPICIOUS_TLDS = {
    ".top", ".xyz", ".club", ".online", ".work", ".site",
    ".tk", ".ml", ".ga", ".cf", ".gq", ".vip", ".cc"
}

LEGITIMATE_DOMAINS = {
    "combanketh.et", "ethiotelecom.et", "telebirr.et",
    "dashenbanksc.com", "awashbank.com", "coopbankoromia.com.et"
}

LOOKALIKE_PATTERNS = r"(cbe-?|telebirr-?|ethio-?|cbebirr-?|dashen-?|tele-?)"


def extract_urls(message: str) -> list[str]:
    return re.findall(URL_PATTERN, message)


def analyze_url(url: str) -> list[str]:
    indicators = []

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        path = (parsed.path or "").lower()

        if not hostname:
            return ["malformed_url"]

        hostname = hostname.lower()

        # 1. URL Shortener Detection
        if hostname in SHORTENED_DOMAINS:
            indicators.append("url_shortener")

        # 2. IP Address Hostname
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname):
            indicators.append("ip_address_url")

        # 3. Excessive Subdomains
        if hostname.count(".") >= 3:
            indicators.append("excessive_subdomains")

        # 4. Embedded @ symbol credential spoofing
        if "@" in url:
            indicators.append("url_contains_at_symbol")

        # 5. Missing TLS / HTTPS
        if parsed.scheme != "https":
            indicators.append("no_https")

        # 6. Suspicious / High-Risk TLD
        if any(hostname.endswith(tld) for tld in SUSPICIOUS_TLDS):
            indicators.append("suspicious_tld")

        # 7. Credential / Login Paths
        if re.search(r"(login|verify|account|update|pin|claim|bank|reset|otp|auth)", path):
            indicators.append("credential_path")

        # 8. Regional Lookalike Domain Spoofing
        is_legit = any(hostname.endswith(legit) for legit in LEGITIMATE_DOMAINS)
        if not is_legit and re.search(LOOKALIKE_PATTERNS, hostname):
            indicators.append("lookalike_domain")

        # 9. Punycode or Unicode Obfuscation
        if "xn--" in hostname or any(ord(char) > 127 for char in hostname):
            indicators.append("punycode_or_unicode")

    except Exception:
        indicators.append("malformed_url")

    return indicators


def analyze_urls(message: str) -> tuple[list[str], list[str]]:
    urls = extract_urls(message)
    indicators = []

    for url in urls:
        indicators.extend(analyze_url(url))

    return urls, list(set(indicators))