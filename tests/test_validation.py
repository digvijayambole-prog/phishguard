import re
import pytest
from urllib.parse import urlparse

VALID = [
    "https://example.com",
    "http://example.com",
    "https://example.com:8080/path",
    "https://example.com/path?q=1",
    "https://example.com/path#section",
    "https://xn--bcher-kva.example/",
    "https://b\u00fccher.example/",
]

INVALID = [
    "",
    "   ",
    "example.com",
    "https//example.com",
    "https://",
    "ftp://example.com",
    "https://example",
    "https://example.com/\nnext",
    "https://example.com:99999",
]

FORBIDDEN = re.compile(r"[<>\"'`\\|;$\s\x00-\x1f\x7f]")


def is_valid_url(value):
    value = value.strip()
    if not value or len(value) > 2048:
        return False
    if FORBIDDEN.search(value):
        return False
    try:
        parsed = urlparse(value)
        host = parsed.hostname
        parsed.port  # raises ValueError for an out-of-range port
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"} or not host:
        return False
    return "." in host


@pytest.mark.parametrize("url", VALID)
def test_valid_urls(url):
    assert is_valid_url(url)


@pytest.mark.parametrize("url", INVALID)
def test_invalid_urls(url):
    assert not is_valid_url(url)


def test_long_input_rejected():
    assert not is_valid_url("https://" + "a" * 10000 + ".com")


@pytest.mark.parametrize("payload", [
    '<script>alert(1)</script>',
    '"><img src=x onerror=alert(1)>',
    'javascript:alert(document.cookie)',
    'https://example.com/<svg onload=alert(1)>',
    "'; | & $ `",
    "%3Cscript%3E",
])
def test_security_payloads_are_not_valid(payload):
    assert not is_valid_url(payload)
