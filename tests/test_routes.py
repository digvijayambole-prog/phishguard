import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.mock_server import app

def test_index():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Check a website before you trust it" in response.data

def test_empty_url():
    client = app.test_client()
    response = client.post("/analyze", data={"url": ""})
    assert response.status_code == 400
    assert b"E_EMPTY_URL" in response.data

def test_valid_url():
    client = app.test_client()
    response = client.post("/analyze", data={"url": "https://example.com/login"})
    assert response.status_code == 200
    assert b"Risk score" in response.data
    assert b"Safety recommendation" in response.data

def test_xss_is_escaped():
    client = app.test_client()
    payload = '<script>alert(1)</script>'
    response = client.post("/analyze", data={"url": payload})
    assert b"&lt;script&gt;alert(1)&lt;/script&gt;" in response.data
    assert b"<script>alert(1)</script>" not in response.data
