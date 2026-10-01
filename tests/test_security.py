import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app

BROWSER = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}


@pytest.fixture
def client():
    return create_app().test_client()


def _hit(client, n, headers=None):
    r = None
    for _ in range(n):
        r = client.post("/analyze", data={"url": "http://example.com"}, headers=headers)
    return r


def test_rate_limit_allows_ten_then_blocks_json(client):
    assert _hit(client, 10).status_code != 429
    r = _hit(client, 1)
    assert r.status_code == 429
    assert r.get_json()["error"]["code"] == "E_RATE_LIMIT"


def test_rate_limit_shows_friendly_message_in_browser(client):
    r = _hit(client, 11, headers=BROWSER)
    assert r.status_code == 429
    assert "Too many requests" in r.get_data(as_text=True)


def test_security_headers_present(client):
    r = client.get("/")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'self'" in r.headers["Content-Security-Policy"]
