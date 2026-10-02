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


import re




def test_result_page_uses_svg_icons_not_emoji(client):
    html = analyze(client, "http://192.168.1.1/login").get_data(as_text=True)
    assert "<svg" in html
    assert "\U0001F6E1" not in html and "\u26A0" not in html


def test_input_errors_render_inline_and_keep_the_url(client):
    r = analyze(client, "ftp://example.com/a")
    html = r.get_data(as_text=True)
    assert r.status_code == 400
    assert 'id="analyzeForm"' in html
    assert "Only http and https addresses can be analysed." in html
    assert 'data-error-code="E_UNSUPPORTED_SCHEME"' in html
    assert 'value="ftp://example.com/a"' in html


def test_whitespace_only_gets_the_servers_message(client):
    r = analyze(client, "   ")
    assert r.status_code == 400
    assert "Please enter a website URL." in r.get_data(as_text=True)


def test_inline_error_echo_is_escaped(client):
    r = analyze(client, '"><img src=x onerror=alert(1)>;')
    html = r.get_data(as_text=True)
    assert r.status_code == 400
    assert "<img src=x" not in html and "&lt;img" in html


def test_script_has_no_own_error_copy_and_form_defers_to_server(client):
    js = (ROOT / "static" / "script.js").read_text(encoding="utf-8")
    assert "Please enter" not in js
    assert "novalidate" in client.get("/", headers=BROWSER).get_data(as_text=True)


def test_home_page_has_no_emoji_icons(client):
    html = client.get("/", headers=BROWSER).get_data(as_text=True)
    for emoji in ("\U0001F50E", "\U0001F9E0", "\U0001F6E1"):
        assert emoji not in html


def test_input_errors_render_inline_and_keep_the_url(client):
    r = analyze(client, "ftp://example.com/a")
    html = r.get_data(as_text=True)
    assert r.status_code == 400
    assert 'id="analyzeForm"' in html
    assert "Only http and https addresses can be analysed." in html
    assert 'data-error-code="E_UNSUPPORTED_SCHEME"' in html
    assert 'value="ftp://example.com/a"' in html


def test_whitespace_only_gets_the_servers_message(client):
    r = analyze(client, "   ")
    assert r.status_code == 400
    assert "Please enter a website URL." in r.get_data(as_text=True)


def test_inline_error_echo_is_escaped(client):
    r = analyze(client, '"><img src=x onerror=alert(1)>;')
    html = r.get_data(as_text=True)
    assert r.status_code == 400
    assert "<img src=x" not in html and "&lt;img" in html


def test_script_has_no_own_error_copy_and_form_defers_to_server(client):
    js = (ROOT / "static" / "script.js").read_text(encoding="utf-8")
    assert "Please enter" not in js
    assert "novalidate" in client.get("/", headers=BROWSER).get_data(as_text=True)


def test_home_page_has_no_emoji_icons(client):
    html = client.get("/", headers=BROWSER).get_data(as_text=True)
    for emoji in ("\U0001F50E", "\U0001F9E0", "\U0001F6E1"):
        assert emoji not in html


def test_oversized_request_body_is_rejected_with_frozen_shape(client):
    r = client.post("/analyze", data={"url": "a" * 40000}, headers={"Accept": "*/*"})
    assert r.status_code == 413
    assert r.get_json()["error"]["code"] == "E_INTERNAL"
    assert "Traceback" not in r.get_data(as_text=True)


def test_gauge_arc_is_set_by_attribute_not_inline_style(client):
    html = analyze(client, "https://example.com/login").get_data(as_text=True)
    assert re.search(r'stroke-dasharray="\d+ 100"', html)


def test_no_inline_style_attributes_so_csp_can_stay_strict(client):
    pages = [client.get("/", headers=BROWSER).get_data(as_text=True),
             analyze(client, "https://example.com/login").get_data(as_text=True),
             analyze(client, "ftp://example.com").get_data(as_text=True)]
    for html in pages:
        assert ' style="' not in html


def test_gauge_arc_is_set_by_attribute_not_inline_style(client):
    html = analyze(client, "https://example.com/login").get_data(as_text=True)
    assert re.search(r'stroke-dasharray="\d+ 100"', html)


def test_no_inline_style_attributes_so_csp_can_stay_strict(client):
    pages = [client.get("/", headers=BROWSER).get_data(as_text=True),
             analyze(client, "https://example.com/login").get_data(as_text=True),
             analyze(client, "ftp://example.com").get_data(as_text=True)]
    for html in pages:
        assert ' style="' not in html
