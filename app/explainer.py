"""Rule catalogue (one rule per feature). Explainer functions are added in Phase 3."""

RULES = [
    {"feature": "hostname_length", "triggers_when": lambda v: v >= 27,
     "label": "Unusually long domain name",
     "why": "Long domain names are sometimes used to imitate a trusted brand or to bury the part that identifies the real site."},
    {"feature": "num_dots", "triggers_when": lambda v: v >= 3,
     "label": "Many dots in the address",
     "why": "A lot of dots often means several sections are stacked before the real domain, which can make a fake address look genuine."},
    {"feature": "num_subdomains", "triggers_when": lambda v: v >= 2,
     "label": "Several sub-domains",
     "why": "Extra sections before the main domain can be used to make an address appear to belong to a trusted company."},
    {"feature": "suspicious_keyword_count", "triggers_when": lambda v: v >= 1,
     "label": "Sensitive words in the address",
     "why": "Words like 'login', 'verify' or 'account' in an address are often associated with pages trying to look like real sign-in pages."},
    {"feature": "has_https", "triggers_when": lambda v: v == 0,
     "label": "Connection is not encrypted (no HTTPS)",
     "why": "Genuine sign-in pages almost always use an encrypted connection, so its absence is unusual for a page asking for personal details."},
    {"feature": "has_ip_address", "triggers_when": lambda v: v == 1,
     "label": "Address uses a raw IP instead of a domain name",
     "why": "Genuine services almost always use a domain name. A bare IP address is unusual for a login page."},
    {"feature": "has_at_symbol", "triggers_when": lambda v: v == 1,
     "label": "Address contains an @ symbol",
     "why": "Browsers ignore the text before an @ symbol in an address, which can be used to disguise the real destination."},
]

TOTAL_RULES = len(RULES)


# ---------------------------------------------------------------------------
# Phase 3: ranked indicators, summary and recommendation
# ---------------------------------------------------------------------------
import json

from app import config
from app.errors import AppError

# Fallback ranking (used when feature_importance.json is missing or invalid).
FALLBACK_WEIGHTS = {
    "has_ip_address": 12, "has_at_symbol": 11, "suspicious_keyword_count": 10,
    "has_https": 9, "num_subdomains": 8, "url_length": 7, "hostname_length": 6,
    "num_hyphens": 5, "num_special_chars": 4, "num_dots": 3, "num_digits": 2,
    "path_length": 1,
}

RECOMMENDATIONS = {
    "Low": "No strong warning signs were found. Normal caution still applies "
           "- check the address bar before signing in anywhere.",
    "Medium": "Some characteristics of this address are unusual. Do not enter "
              "passwords or payment details unless you are certain the site is genuine.",
    "High": "This address shows several characteristics commonly seen in phishing "
            "pages. Avoid entering passwords or payment information on this site.",
}


def _load_importance():
    """Loaded ONCE at import. Returns {feature: number} or None if absent/invalid."""
    try:
        with open(config.IMPORTANCE_PATH, encoding="utf-8") as fh:
            data = json.load(fh)["importances"]
        for rule in RULES:
            if not isinstance(data[rule["feature"]], (int, float)):
                return None
        return data
    except Exception:
        return None


_IMPORTANCE = _load_importance()


def _rank_key(feature):
    importance = _IMPORTANCE[feature] if _IMPORTANCE else 0
    return (-importance, -FALLBACK_WEIGHTS[feature])


def build_indicators(features):
    """Return ONLY the rules that actually triggered, most important first."""
    try:
        triggered = [r for r in RULES if r["triggers_when"](features[r["feature"]])]
        triggered.sort(key=lambda r: _rank_key(r["feature"]))
        return [{"feature": r["feature"], "value": features[r["feature"]],
                 "label": r["label"], "why": r["why"]} for r in triggered]
    except Exception:
        raise AppError("E_EXPLANATION_FAILURE")


def summarize(level, indicators):
    """One short paragraph built only from indicators that triggered."""
    n = len(indicators)
    if n == 0:
        if level == "Low":
            return "No common warning signs were found in the structure of this web address."
        return ("The automated check rates this address as risky, but no single clear "
                "warning sign can be pointed out.")
    top = "; ".join(i["label"] for i in indicators[:3])
    noun = "characteristic" if n == 1 else "characteristics"
    return (f"This address shows {n} {noun} commonly associated with phishing pages. "
            f"The most notable: {top}.")
