"""Brand-adjacent theme scaffold regression tests.

Verifies the per-project theming infrastructure introduced in P0:
  - Every project listed in `brand-themes.ts` has a matching CSS file.
  - Every theme CSS file uses the `[data-project-theme="<slug>"]` selector.
  - The pilot project (vi-home-one) has actual token overrides (--primary),
    not just an empty stub.
  - The pilot project's route file wraps with `<ProjectThemeScope>`.
  - The customer-inspiration callout is still present in each project plan
    (obfuscation regression guard).

See docs/ci-implementation-plan.md for the full plan.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
UI_ROOT = REPO_ROOT / "src" / "innovation_factory" / "ui"
THEMES_DIR = UI_ROOT / "styles" / "themes"
REGISTRY = UI_ROOT / "lib" / "brand-themes.ts"
DOCS_PROJECTS = REPO_ROOT / "docs" / "projects"

# Slugs that should have a brand theme. Source of truth: BRAND_THEMES registry.
EXPECTED_SLUGS = (
    "vi-home-one",
    "bsh-home-connect",
    "mol-asm-cockpit",
    "adtech-intelligence",
    "hb-product-center",
    "aeco-hub",
)

# Per-project plan doc names (under docs/projects/).
PROJECT_DOCS = {
    "vi-home-one": "vi-home-one.md",
    "bsh-home-connect": "bsh-home-connect.md",
    "mol-asm-cockpit": "mol-asm-cockpit.md",
    "adtech-intelligence": "adtech-intelligence.md",
    "hb-product-center": "hb-product-center.md",
    "aeco-hub": "aeco-hub-plan.md",
}


def _registry_text() -> str:
    return REGISTRY.read_text(encoding="utf-8")


@pytest.mark.parametrize("slug", EXPECTED_SLUGS)
def test_registry_contains_slug(slug: str) -> None:
    """brand-themes.ts must declare an entry for every expected slug."""
    text = _registry_text()
    assert f'"{slug}"' in text, (
        f"brand-themes.ts missing entry for slug '{slug}'. "
        f"Add a BRAND_THEMES['{slug}'] record."
    )


@pytest.mark.parametrize("slug", EXPECTED_SLUGS)
def test_theme_css_file_exists(slug: str) -> None:
    """Each slug must have a CSS file under styles/themes/."""
    path = THEMES_DIR / f"{slug}.css"
    assert path.is_file(), (
        f"Missing theme file {path.relative_to(REPO_ROOT)}. "
        f"Stub it (see hb-product-center.css for shape)."
    )


@pytest.mark.parametrize("slug", EXPECTED_SLUGS)
def test_theme_css_has_attribute_selector(slug: str) -> None:
    """Each theme file must scope tokens via the data-project-theme selector."""
    css = (THEMES_DIR / f"{slug}.css").read_text(encoding="utf-8")
    selector = f'[data-project-theme="{slug}"]'
    assert selector in css, (
        f"Theme {slug}.css must use selector {selector!r} so "
        f"ProjectThemeScope can scope its tokens."
    )


def test_pilot_theme_has_primary_token() -> None:
    """vi-home-one is the P0 pilot — it must actually override --primary."""
    css = (THEMES_DIR / "vi-home-one.css").read_text(encoding="utf-8")
    assert re.search(r"--primary\s*:\s*oklch", css), (
        "vi-home-one.css must override --primary with an oklch value "
        "(the Vitorange-adjacent palette). Other projects are P1 stubs."
    )


def test_globals_imports_all_themes() -> None:
    """globals.css must @import every per-project theme file."""
    css = (UI_ROOT / "styles" / "globals.css").read_text(encoding="utf-8")
    for slug in EXPECTED_SLUGS:
        marker = f'@import "./themes/{slug}.css"'
        assert marker in css, (
            f"globals.css missing import for {slug} theme. "
            f"Add: {marker};"
        )


def test_pilot_route_uses_project_theme_scope() -> None:
    """vi-home-one route must wrap its layout with <ProjectThemeScope>."""
    route = (
        UI_ROOT / "routes" / "projects" / "vi-home-one" / "route.tsx"
    ).read_text(encoding="utf-8")
    assert "ProjectThemeScope" in route, (
        "vi-home-one route.tsx must import ProjectThemeScope."
    )
    assert 'slug="vi-home-one"' in route, (
        "vi-home-one route.tsx must use <ProjectThemeScope slug=\"vi-home-one\">."
    )


@pytest.mark.parametrize("slug,filename", PROJECT_DOCS.items())
def test_project_plan_has_customer_inspiration_callout(
    slug: str, filename: str
) -> None:
    """Each project plan must declare its (obfuscated) customer inspiration.

    Regression guard against accidentally removing the mapping that drives
    the CI work. The line shape is:
        > **Customer inspiration (obfuscated CI):** <name> — ...
    """
    path = DOCS_PROJECTS / filename
    assert path.is_file(), f"Project plan missing: {path}"
    text = path.read_text(encoding="utf-8")
    assert "Customer inspiration" in text, (
        f"{filename} missing 'Customer inspiration' callout. "
        f"Add the standard blockquote near the top — see "
        f"docs/ci-implementation-plan.md."
    )
