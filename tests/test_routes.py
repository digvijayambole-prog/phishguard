import json
import sys
from pathlib import Path

import pytest
from flask import render_template

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, predictor

BROWSER = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}


@pytest.fixture
def client():
    return create_app().test_client()


def analyze(client, url):
    return client.post("/analyze", data={"url": url}, headers=BROWSER)


def test_index(client):
    response = client.get("/", headers=BROWSER)
    assert response.status_code == 200
    assert b"Check a website before you trust it" in response.data


def test_empty_url(client):
    response = analyze(client, "")
    assert response.status_code == 400
    assert b"E_EMPTY_URL" in response.data


def test_valid_url(client):
    response = analyze(client, "https://example.com/login")
    assert response.status_code == 200
    assert b"Risk score" in response.data
    assert b"Safety recommendation" in response.data


def test_xss_is_escaped(client):
    response = analyze(client, "<script>alert(1)</script>")
    assert b"&lt;script&gt;alert(1)&lt;/script&gt;" in response.data
    assert b"<script>alert(1)</script>" not in response.data


@pytest.mark.parametrize("payload", [
    "<script>alert(1)</script>",
    '"><img src=x onerror=alert(1)>',
    "javascript:alert(document.cookie)",
    "https://example.com/<svg onload=alert(1)>",
])
def test_xss_payloads_never_render_as_markup(client, payload):
    response = analyze(client, payload)
    assert response.status_code in (200, 400)
    body = response.get_data(as_text=True)
    for raw in ["<script>alert(1)", "<img src=x", "<svg onload", "Traceback"]:
        assert raw not in body


def test_information_hierarchy_order(client):
    html = analyze(client, "https://example.com/login").get_data(as_text=True)
    labels = ["1. Analysed URL", "2. Prediction", "3. Risk score", "4. Risk level",
              "5. Key indicators", "6. Plain-language explanation",
              "7. Safety recommendation", "8. Technical details"]
    positions = [html.find(label) for label in labels]
    assert all(p >= 0 for p in positions)
    assert positions == sorted(positions)


def test_results_region_is_aria_live(client):
    html = analyze(client, "https://example.com/login").get_data(as_text=True)
    assert 'aria-live="polite"' in html


def test_model_unavailable_shows_message_page(client, monkeypatch):
    monkeypatch.setattr(predictor, "model", None)
    response = analyze(client, "https://example.com")
    assert response.status_code == 503
    assert b"Analysis is unavailable right now." in response.data
    assert b"Traceback" not in response.data


@pytest.mark.parametrize("name", ["result_high", "result_medium", "result_low", "result_no_explain"])
def test_result_template_renders_every_fixture(name):
    data = json.loads((ROOT / "fixtures" / f"{name}.json").read_text(encoding="utf-8"))
    with create_app().test_request_context():
        html = render_template("result.html", **data)
    assert "Risk score" in html and "Safety recommendation" in html
