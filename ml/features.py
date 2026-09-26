import sys
sys.stdout.reconfigure(encoding="utf-8")
"""
Member 1 - Data & Features
Pure feature extraction function for phishing URL detection.

Rules (Section 3.3 of the brief):
- Returns exactly the 12 keys below, all numeric.
- Pure function. No Flask import. No internet. No file reads.
- MUST NEVER RAISE AN EXCEPTION.
"""

from urllib.parse import urlparse
import ipaddress

try:
    import tldextract
except ImportError:
    tldextract = None

SUSPICIOUS_KEYWORDS = [
    "login", "log-in", "signin", "sign-in", "verify", "verification",
    "secure", "security", "account", "update", "confirm", "banking",
    "bank", "password", "credential", "webscr", "paypal", "invoice",
    "billing", "recover",
]

SPECIAL_CHARS = set("@?=&%#~+")

FEATURE_ORDER = [
    "url_length", "hostname_length", "path_length", "num_dots",
    "num_hyphens", "num_digits", "num_special_chars", "num_subdomains",
    "has_https", "has_ip_address", "has_at_symbol", "suspicious_keyword_count",
]


def _empty_features() -> dict:
    return {name: 0 for name in FEATURE_ORDER}


def _is_ip_hostname(hostname: str) -> bool:
    if not hostname:
        return False
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def _count_subdomains(full_url: str, hostname: str) -> int:
    if not hostname:
        return 0
    if tldextract is not None:
        try:
            ext = tldextract.extract(full_url)
            if not ext.subdomain:
                return 0
            return len(ext.subdomain.split("."))
        except Exception:
            pass
    parts = [p for p in hostname.split(".") if p]
    if len(parts) <= 2:
        return 0
    return len(parts) - 2


def extract_features(url: str) -> dict:
    try:
        if url is None:
            return _empty_features()

        url = str(url).strip()
        if url == "":
            return _empty_features()

        parse_target = url if "://" in url else "http://" + url

        try:
            parsed = urlparse(parse_target)
        except Exception:
            return _empty_features()

        hostname = parsed.hostname or ""
        path = parsed.path or ""

        try:
            num_subdomains = _count_subdomains(parse_target, hostname)
        except Exception:
            num_subdomains = 0

        lowered = url.lower()

        features = {
            "url_length": len(url),
            "hostname_length": len(hostname),
            "path_length": len(path),
            "num_dots": url.count("."),
            "num_hyphens": url.count("-"),
            "num_digits": sum(ch.isdigit() for ch in url),
            "num_special_chars": sum(1 for ch in url if ch in SPECIAL_CHARS),
            "num_subdomains": num_subdomains,
            "has_https": 1 if parsed.scheme.lower() == "https" else 0,
            "has_ip_address": 1 if _is_ip_hostname(hostname) else 0,
            "has_at_symbol": 1 if "@" in url else 0,
            "suspicious_keyword_count": sum(
                1 for kw in SUSPICIOUS_KEYWORDS if kw in lowered
            ),
        }

        for k, v in features.items():
            try:
                features[k] = int(v)
            except Exception:
                features[k] = 0

        return features

    except Exception:
        return _empty_features()


if __name__ == "__main__":
    test_urls = [
        "https://google.com",
        "google.com",
        "http://192.168.1.1/login",
        "https://a.b.c.example.co.uk/path",
        "https://example.com:8080/x?y=1#z",
        "https://user@example.com",
        "https://xn--80ak6aa92e.com",
        "https://secure-login-verify.paypal.com.attacker.ru/account",
        "",
        "not a url at all",
        "https://" + "a" * 2000,
        "https://例え.テスト",
    ]
    for u in test_urls:
        result = extract_features(u)
        label = u if len(u) <= 60 else u[:57] + "..."
        line = f"{label!r:65} -> {result}"
        try:
            print(line)
        except UnicodeEncodeError:
            print(line.encode("ascii", errors="backslashreplace").decode("ascii"))