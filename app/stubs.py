"""Stand-ins for Member 1's extractor and Member 2's model.
DELETED on Day 11."""

SUSPICIOUS_KEYWORDS = ["login", "log-in", "signin", "sign-in", "verify", "verification",
    "secure", "security", "account", "update", "confirm", "banking", "bank", "password",
    "credential", "webscr", "paypal", "invoice", "billing", "recover"]

FEATURE_ORDER = ["url_length", "hostname_length", "path_length", "num_dots",
    "num_hyphens", "num_digits", "num_special_chars", "num_subdomains",
    "has_https", "has_ip_address", "has_at_symbol", "suspicious_keyword_count"]


def stub_extract_features(url: str) -> dict:
    u = url.lower()
    host = url.split("/")[2] if "//" in url else url
    return {
        "url_length": len(url),
        "hostname_length": len(host),
        "path_length": max(0, len(url) - len(host) - 8),
        "num_dots": url.count("."),
        "num_hyphens": url.count("-"),
        "num_digits": sum(c.isdigit() for c in url),
        "num_special_chars": sum(url.count(c) for c in "@?=&%#~+"),
        "num_subdomains": max(0, host.count(".") - 1),
        "has_https": 1 if url.startswith("https://") else 0,
        "has_ip_address": 0,
        "has_at_symbol": 1 if "@" in url else 0,
        "suspicious_keyword_count": sum(k in u for k in SUSPICIOUS_KEYWORDS),
    }


class StubModel:
    name = "StubModel"

    def predict_proba(self, X):
        f = X[0]
        p = min(0.95, 0.20 + f[0] / 400 + f[11] * 0.12)  # longer + more keywords = riskier
        return [[1 - p, p]]

    def predict(self, X):
        return [1 if self.predict_proba(X)[0][1] >= 0.5 else 0]
