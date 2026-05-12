"""WCAG contrast helper — oklch to relative luminance, no external deps.

Used by test_brand_theme_contrast.py to assert that every brand-theme
token pair meets WCAG AA contrast thresholds (4.5:1 for normal text,
3:1 for large text / UI components).

References:
  - oklab/oklch ↔ linear sRGB: https://bottosson.github.io/posts/oklab/
  - WCAG 2.1 contrast formula: https://www.w3.org/TR/WCAG21/#dfn-contrast-ratio
  - WCAG 2.1 contrast minimum: https://www.w3.org/TR/WCAG21/#contrast-minimum
"""
from __future__ import annotations

import math
import re


_OKLCH_RE = re.compile(
    r"oklch\(\s*"
    r"(?P<L>[0-9.]+)\s+"
    r"(?P<C>[0-9.]+)\s+"
    r"(?P<h>[0-9.]+)"
    r"(?:\s*/\s*(?P<alpha>[0-9.]+))?"
    r"\s*\)"
)


def parse_oklch(value: str) -> tuple[float, float, float]:
    """Parse `oklch(L C h [/alpha])` → (L, C, h_deg). Alpha is ignored."""
    m = _OKLCH_RE.search(value.strip())
    if not m:
        raise ValueError(f"Could not parse oklch from {value!r}")
    return float(m["L"]), float(m["C"]), float(m["h"])


def oklch_to_linear_rgb(
    L: float, C: float, h_deg: float
) -> tuple[float, float, float]:
    """Convert oklch (L 0-1, C 0-~0.4, h in degrees) → linear-light sRGB.

    Channel values are clamped to [0, 1] to handle out-of-gamut colors.
    """
    h_rad = math.radians(h_deg)
    a = C * math.cos(h_rad)
    b = C * math.sin(h_rad)

    # oklab → linear sRGB (Björn Ottosson)
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b

    l = l_**3
    m = m_**3
    s = s_**3

    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b_rgb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

    return (
        max(0.0, min(1.0, r)),
        max(0.0, min(1.0, g)),
        max(0.0, min(1.0, b_rgb)),
    )


def relative_luminance(linear_rgb: tuple[float, float, float]) -> float:
    """WCAG relative luminance from linear-light sRGB.

    The input is already linear-light (the gamma-encoded sRGB step is
    skipped by the caller); WCAG's formula operates on linear values.
    """
    r, g, b = linear_rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio_oklch(color_a: str, color_b: str) -> float:
    """WCAG contrast ratio between two oklch(...) color strings."""
    y_a = relative_luminance(oklch_to_linear_rgb(*parse_oklch(color_a)))
    y_b = relative_luminance(oklch_to_linear_rgb(*parse_oklch(color_b)))
    lighter = max(y_a, y_b) + 0.05
    darker = min(y_a, y_b) + 0.05
    return lighter / darker
