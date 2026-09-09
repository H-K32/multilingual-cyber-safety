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
}


def extract_urls(message: str) -> list[str]:
    return re.findall(URL_PATTERN, message)


def analyze_url(url: str) -> list[str]:
    indicators = []

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return ["malformed_url"]

        hostname = hostname.lower()

        if hostname in SHORTENED_DOMAINS:
            indicators.append("url_shortener")

        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname):
            indicators.append("ip_address_url")

        if hostname.count(".") >= 3:
            indicators.append("excessive_subdomains")

        if "@" in url:
            indicators.append("url_contains_at_symbol")

        if parsed.scheme != "https":
            indicators.append("no_https")

    except Exception:
        indicators.append("malformed_url")

    return indicators


def analyze_urls(message: str) -> tuple[list[str], list[str]]:
    urls = extract_urls(message)

    indicators = []

    for url in urls:
        indicators.extend(analyze_url(url))

    return urls, list(set(indicators))