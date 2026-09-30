"""URL input hardening. Analyses the string only: never fetches or resolves it."""
import re
from urllib.parse import urlparse

from app import config
from app.errors import AppError

SUPPORTED_SCHEMES = {"http", "https"}
BANNED_CHARS = set(";|&$`")
_SCHEME_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.\-]*)://")
_OPAQUE_SCHEMES = ("javascript:", "data:", "file:", "mailto:", "tel:", "vbscript:")


def validate_url(raw):
    """Return a normalised URL string, or raise AppError."""
    if raw is None or not isinstance(raw, str) or not raw.strip():
        raise AppError("E_EMPTY_URL")

    if any(ord(c) < 32 or ord(c) == 127 for c in raw):
        raise AppError("E_INVALID_URL")

    url = raw.strip()

    if len(url) > config.MAX_URL_LENGTH:
        raise AppError("E_URL_TOO_LONG")

    match = _SCHEME_RE.match(url)
    if match:
        if match.group(1).lower() not in SUPPORTED_SCHEMES:
            raise AppError("E_UNSUPPORTED_SCHEME")
    elif url.lower().startswith(_OPAQUE_SCHEMES):
        raise AppError("E_UNSUPPORTED_SCHEME")
    else:
        url = "https://" + url

    if any(c in BANNED_CHARS for c in url) or any(c.isspace() for c in url):
        raise AppError("E_INVALID_URL")

    try:
        parsed = urlparse(url)
        _ = parsed.port  # raises ValueError on a bad port
    except ValueError:
        raise AppError("E_INVALID_URL")

    if not parsed.hostname:
        raise AppError("E_INVALID_URL")

    return url
