"""Stylesheet checks from the UI requirements: tokens only, dark mode, reduced motion, contrast."""
import re
from pathlib import Path

import pytest

CSS = (Path(__file__).resolve().parents[1] / "static" / "style.css").read_text(encoding="utf-8")
ROOT_BLOCKS = re.findall(r":root\s*\{([^}]*)\}", CSS)


def _vars(block):
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})\s*;", block))


LIGHT = _vars(ROOT_BLOCKS[0])
DARK = {**LIGHT, **_vars(ROOT_BLOCKS[1])}


def _luminance(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(a, b):
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


TEXT_PAIRS = [("text", "bg"), ("text", "surface"), ("text", "surface-2"), ("muted", "bg"),
              ("muted", "surface"), ("muted", "surface-2"), ("primary", "surface"),
              ("on-primary", "primary"), ("danger", "surface"), ("safe", "surface"),
              ("danger", "danger-bg"), ("safe", "safe-bg"), ("warning", "warning-bg")]
UI_PAIRS = [("input-border", "surface"), ("focus", "surface"), ("focus", "bg")]


def test_two_token_blocks_exist():
    assert len(ROOT_BLOCKS) == 2 and "prefers-color-scheme: dark" in CSS


def test_reduced_motion_supported():
    assert "prefers-reduced-motion: reduce" in CSS


def test_no_hardcoded_hex_outside_token_blocks():
    outside = re.sub(r":root\s*\{[^}]*\}", "", CSS)
    assert re.findall(r"#[0-9a-fA-F]{3,8}\b", outside) == []


@pytest.mark.parametrize("mode,palette", [("light", LIGHT), ("dark", DARK)])
@pytest.mark.parametrize("fg,bg", TEXT_PAIRS)
def test_text_contrast_at_least_4_5(mode, palette, fg, bg):
    assert ratio(palette[fg], palette[bg]) >= 4.5, (mode, fg, bg)


@pytest.mark.parametrize("mode,palette", [("light", LIGHT), ("dark", DARK)])
@pytest.mark.parametrize("fg,bg", UI_PAIRS)
def test_ui_component_contrast_at_least_3(mode, palette, fg, bg):
    assert ratio(palette[fg], palette[bg]) >= 3.0, (mode, fg, bg)
