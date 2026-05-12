"""Brand-adjacent theme scaffold regression tests.

Verifies the per-project theming infrastructure introduced in P0 and
hardened in P1:
  - Every project listed in `brand-themes.ts` has a matching CSS file.
  - Every theme CSS file uses the `[data-project-theme="<slug>"]` selector.
  - Every theme overrides `--primary` (no empty stubs) in both light and
    dark mode.
  - Every project's route.tsx wraps with `<ProjectThemeScope slug="...">`.
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


@pytest.mark.parametrize("slug", EXPECTED_SLUGS)
def test_theme_overrides_primary_in_light_and_dark(slug: str) -> None:
    """Every theme must override --primary in both light and dark mode.

    P0 only required this for the vi-home-one pilot; P1 requires it for
    all six themes (no empty stubs left).
    """
    css = (THEMES_DIR / f"{slug}.css").read_text(encoding="utf-8")
    primary_occurrences = re.findall(r"--primary\s*:\s*oklch", css)
    assert len(primary_occurrences) >= 2, (
        f"{slug}.css must override --primary in both light and dark mode "
        f"(found {len(primary_occurrences)} oklch override(s))."
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


@pytest.mark.parametrize("slug", EXPECTED_SLUGS)
def test_route_uses_project_theme_scope(slug: str) -> None:
    """Every project's route.tsx must wrap its layout with <ProjectThemeScope>."""
    route = (
        UI_ROOT / "routes" / "projects" / slug / "route.tsx"
    ).read_text(encoding="utf-8")
    assert "ProjectThemeScope" in route, (
        f"{slug}/route.tsx must import ProjectThemeScope."
    )
    assert f'slug="{slug}"' in route, (
        f'{slug}/route.tsx must use <ProjectThemeScope slug="{slug}">.'
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


# --------------------------------------------------------------------------
# P2 regression tests — wordmark, sidebar slot, chart palette
# --------------------------------------------------------------------------

WORDMARK_PATH = UI_ROOT / "components" / "apx" / "project-wordmark.tsx"
SIDEBAR_LAYOUT_PATH = UI_ROOT / "components" / "apx" / "sidebar-layout.tsx"

_RULE_RE = re.compile(r"(?P<selector>[^{}]+)\{(?P<body>[^{}]+)\}", re.MULTILINE)


def _chart_vars_present(body: str) -> set[str]:
    """Return the set of `--chart-N` variable names defined inside a CSS rule body."""
    return set(re.findall(r"--chart-[1-5]", body))


def _theme_chart_blocks(slug: str) -> dict[str, set[str]]:
    """Aggregate `--chart-*` declarations across all light vs dark rules for a slug.

    Mirrors the parser used by test_brand_theme_contrast.py: any rule whose
    selector mentions the slug + `.dark` lands in `dark`; other slug-bearing
    rules land in `light`. We aggregate the union across rules of the same
    bucket so that themes that split tokens across multiple selectors still
    pass.
    """
    css = (THEMES_DIR / f"{slug}.css").read_text(encoding="utf-8")
    light: set[str] = set()
    dark: set[str] = set()
    for rule in _RULE_RE.finditer(css):
        selector = rule.group("selector")
        if slug not in selector:
            continue
        bucket = dark if ".dark" in selector else light
        bucket |= _chart_vars_present(rule.group("body"))
    return {"light": light, "dark": dark}


_CHART_PAIRS = [(slug, mode) for slug in EXPECTED_SLUGS for mode in ("light", "dark")]


@pytest.mark.parametrize(
    "slug,mode",
    _CHART_PAIRS,
    ids=[f"{s}-{m}" for s, m in _CHART_PAIRS],
)
def test_every_theme_defines_5_chart_vars_in_light_and_dark(
    slug: str, mode: str
) -> None:
    """Each theme must define --chart-1..--chart-5 in BOTH light and dark blocks.

    Without dark-mode chart vars, charts in project routes fall back to the
    global default palette in dark mode — defeating per-project theming.
    """
    expected = {f"--chart-{i}" for i in range(1, 6)}
    found = _theme_chart_blocks(slug)[mode]
    missing = expected - found
    assert not missing, (
        f"{slug}.css {mode} block is missing {sorted(missing)} — "
        f"add full --chart-1..5 to the {mode} rule."
    )


def test_wordmark_component_file_exists_and_exports() -> None:
    """ProjectWordmark must exist and export a component."""
    assert WORDMARK_PATH.is_file(), (
        f"Missing {WORDMARK_PATH.relative_to(REPO_ROOT)}. "
        f"See docs/ci-implementation-plan.md §5 (P2)."
    )
    text = WORDMARK_PATH.read_text(encoding="utf-8")
    assert re.search(r"export\s+function\s+ProjectWordmark\b", text), (
        "project-wordmark.tsx must `export function ProjectWordmark`."
    )
    # Must read the brand registry — proves it's not a stubbed-out shell.
    assert "BRAND_THEMES" in text, (
        "project-wordmark.tsx must look up BRAND_THEMES so the displayName "
        "and theming are slug-driven."
    )
    # Legal rail: no inline SVG / image element. Pure text only.
    assert "<svg" not in text and "<img" not in text, (
        "project-wordmark.tsx must be text-only. See legal rail §2 in "
        "docs/ci-implementation-plan.md — no customer marks."
    )


def test_sidebar_layout_accepts_project_slug_prop() -> None:
    """SidebarLayout must accept an optional projectSlug prop and render the wordmark."""
    text = SIDEBAR_LAYOUT_PATH.read_text(encoding="utf-8")
    assert "projectSlug" in text, (
        "sidebar-layout.tsx must accept a `projectSlug` prop so project "
        "routes can render the brand wordmark in the sidebar header."
    )
    assert "ProjectWordmark" in text, (
        "sidebar-layout.tsx must render <ProjectWordmark /> when projectSlug "
        "is set."
    )


@pytest.mark.parametrize("slug", EXPECTED_SLUGS)
def test_every_project_route_passes_project_slug_to_sidebar(slug: str) -> None:
    """Every project route must wire `projectSlug` into its <SidebarLayout>."""
    route = (
        UI_ROOT / "routes" / "projects" / slug / "route.tsx"
    ).read_text(encoding="utf-8")
    assert f'projectSlug="{slug}"' in route, (
        f'{slug}/route.tsx must pass `projectSlug="{slug}"` to '
        f"<SidebarLayout> so the brand wordmark renders in the sidebar."
    )
