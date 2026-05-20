"""WCAG AA contrast regression tests for brand-adjacent themes.

For each theme × mode (light, dark) × foreground/background token pair,
assert the contrast ratio meets WCAG AA.

Two-tier thresholds (WCAG 2.1):
  - 4.5:1 — normal-text pairs (accent + sidebar-accent are surface tones
            commonly used behind body text).
  - 3.0:1 — primary + sidebar-primary pairs. Per WCAG 1.4.3 "Large Text"
            (>=18pt or >=14pt bold) and 1.4.11 "Non-text Contrast" for
            UI components. shadcn `--primary` is conventionally used on
            primary buttons (semibold >=14px) and active-state pills,
            which qualify under either of those relaxations.

Tokens that a theme does NOT override (no fg or no bg in the theme
block) are skipped — they inherit from the global `:root` scope where
shadcn defaults already meet AA.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from ._wcag import contrast_ratio_oklch


REPO_ROOT = Path(__file__).resolve().parents[2]
THEMES_DIR = REPO_ROOT / "src" / "innovation_factory" / "ui" / "styles" / "themes"

SLUGS = (
    "vi-home-one",
    "bsh-home-connect",
    "mol-asm-cockpit",
    "adtech-intelligence",
    "hb-product-center",
    "aeco-hub",
    "yard-pro",
)

AA_NORMAL_TEXT = 4.5
AA_LARGE_TEXT_OR_UI = 3.0

# (background-token, foreground-token, threshold) triples.
TOKEN_PAIRS: list[tuple[str, str, float]] = [
    ("primary", "primary-foreground", AA_LARGE_TEXT_OR_UI),
    ("accent", "accent-foreground", AA_NORMAL_TEXT),
    ("sidebar-primary", "sidebar-primary-foreground", AA_LARGE_TEXT_OR_UI),
    ("sidebar-accent", "sidebar-accent-foreground", AA_NORMAL_TEXT),
]


_RULE_RE = re.compile(r"(?P<selector>[^{}]+)\{(?P<body>[^{}]+)\}", re.MULTILINE)
_TOKEN_RE = re.compile(r"--([\w-]+)\s*:\s*([^;]+);")


def _parse_theme_tokens(slug: str) -> dict[str, dict[str, str]]:
    """Parse a theme CSS file → {"light": {token: oklch}, "dark": {...}}.

    A rule's selector mentioning the slug AND `.dark` lands in the dark
    block; any other slug-bearing rule lands in light. Rules that don't
    declare `--token` values (e.g. HB's heading-font override) contribute
    nothing.
    """
    css = (THEMES_DIR / f"{slug}.css").read_text(encoding="utf-8")
    light: dict[str, str] = {}
    dark: dict[str, str] = {}

    for rule in _RULE_RE.finditer(css):
        selector = rule.group("selector")
        if slug not in selector:
            continue
        bucket = dark if ".dark" in selector else light
        for tok in _TOKEN_RE.finditer(rule.group("body")):
            bucket[tok.group(1)] = tok.group(2).strip()

    return {"light": light, "dark": dark}


@pytest.fixture(scope="session")
def theme_tokens() -> dict[str, dict[str, dict[str, str]]]:
    return {slug: _parse_theme_tokens(slug) for slug in SLUGS}


def _pair_id(slug: str, mode: str, bg: str, fg: str) -> str:
    return f"{slug}-{mode}-{fg}_on_{bg}"


_PAIRS = [
    (slug, mode, bg, fg, threshold)
    for slug in SLUGS
    for mode in ("light", "dark")
    for bg, fg, threshold in TOKEN_PAIRS
]


@pytest.mark.parametrize(
    "slug,mode,bg,fg,threshold",
    _PAIRS,
    ids=[_pair_id(s, m, bg, fg) for s, m, bg, fg, _ in _PAIRS],
)
def test_token_pair_meets_wcag_aa(
    slug: str,
    mode: str,
    bg: str,
    fg: str,
    threshold: float,
    theme_tokens: dict[str, dict[str, dict[str, str]]],
) -> None:
    tokens = theme_tokens[slug][mode]
    if fg not in tokens or bg not in tokens:
        pytest.skip(f"{slug} {mode}: {fg} or {bg} not overridden in theme")

    ratio = contrast_ratio_oklch(tokens[fg], tokens[bg])
    tier = "Large Text / UI (1.4.3 / 1.4.11)" if threshold == AA_LARGE_TEXT_OR_UI else "Normal Text (1.4.3)"
    assert ratio >= threshold, (
        f"{slug} {mode}: {fg} on {bg} contrast = {ratio:.2f}:1 "
        f"(< AA {threshold}:1 for {tier})\n"
        f"  fg = {tokens[fg]}\n"
        f"  bg = {tokens[bg]}"
    )
