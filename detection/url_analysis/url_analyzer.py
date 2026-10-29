import os
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

# Configurable allowlist of verified legitimate organization domains in Ethiopia
VERIFIED_DOMAINS = {
    "combanketh.et",
    "cbe.com.et",
    "ethiotelecom.et",
    "telebirr.et",
    "dashenbanksc.com",
    "awashbank.com",
    "coopbankoromia.com.et",
    "bankofabyssinia.com",
    "wegagenbank.com.et",
    "hibretbank.com.et",
    "nibbanksc.com",
    "zemenbank.com",
    "sinqe.com.et",
    "amharabank.com.et",
}

# Preserved alias for backwards compatibility
LEGITIMATE_DOMAINS = VERIFIED_DOMAINS

LOOKALIKE_PATTERNS = r"(cbe-?|telebirr-?|ethio-?|cbebirr-?|dashen-?|tele-?|awash-?|abyssinia-?)"


def get_verified_domains() -> set[str]:
    """Returns the set of verified legitimate domains, extensible via
    VERIFIED_DOMAINS_EXTRA environment variable (comma-separated).
    """
    domains = set(VERIFIED_DOMAINS)
    extra = os.environ.get("VERIFIED_DOMAINS_EXTRA", "").strip()
    if extra:
        for d in extra.split(","):
            d = d.strip().lower()
            if d:
                domains.add(d)
    return domains


def is_verified_domain(hostname: str | None) -> bool:
    """Checks whether hostname matches or is an authorized subdomain of a verified domain."""
    if not hostname:
        return False
    host = hostname.lower().strip()
    for legit in get_verified_domains():
        if host == legit or host.endswith("." + legit):
            return True
    return False


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
        is_legit = is_verified_domain(hostname)

        # 1. URL Shortener Detection (verified domains are not shorteners)
        if hostname in SHORTENED_DOMAINS:
            indicators.append("url_shortener")

        # 2. IP Address Hostname
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname):
            indicators.append("ip_address_url")

        # 3. Excessive Subdomains (skip if verified legitimate domain)
        # Account for two-part TLDs like .com.et or .co.uk
        has_twopart_tld = any(hostname.endswith(t) for t in (".com.et", ".gov.et", ".org.et", ".edu.et", ".co.uk"))
        max_dots = 3 if has_twopart_tld else 2
        if not is_legit and hostname.count(".") > max_dots:
            indicators.append("excessive_subdomains")

        # 4. Embedded @ symbol credential spoofing
        if "@" in url:
            indicators.append("url_contains_at_symbol")

        # 5. Missing TLS / HTTPS (only flagged on unencrypted http:// links)
        if parsed.scheme != "https":
            indicators.append("no_https")

        # 6. Suspicious / High-Risk TLD (skip if verified domain)
        if not is_legit and any(hostname.endswith(tld) for tld in SUSPICIOUS_TLDS):
            indicators.append("suspicious_tld")

        # 7. Credential / Login Paths (skip on verified official domains)
        if not is_legit and re.search(r"(login|verify|account|update|pin|claim|bank|reset|otp|auth)", path):
            indicators.append("credential_path")

        # 8. Regional Lookalike Domain Spoofing
        if not is_legit and re.search(LOOKALIKE_PATTERNS, hostname):
            indicators.append("lookalike_domain")

        # 9. Punycode or Unicode Obfuscation
        if not is_legit and ("xn--" in hostname or any(ord(char) > 127 for char in hostname)):
            indicators.append("punycode_or_unicode")

    except Exception:
        indicators.append("malformed_url")

    return indicators


def inspect_url(url: str) -> dict:
    """Detailed inspection of a URL returning indicators, hostname, and verification status."""
    indicators = analyze_url(url)
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
    except Exception:
        hostname = ""
    is_legit = is_verified_domain(hostname)
    return {
        "url": url,
        "hostname": hostname,
        "is_verified_domain": is_legit,
        "indicators": indicators,
    }


def analyze_urls(message: str) -> tuple[list[str], list[str]]:
    urls = extract_urls(message)
    indicators = []

    for url in urls:
        indicators.extend(analyze_url(url))

    return urls, list(set(indicators))
