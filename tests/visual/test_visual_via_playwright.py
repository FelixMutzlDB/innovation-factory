"""Pytest wrapper for the Playwright visual-regression suite.

The actual assertions live in `tests/visual/brand-themes.spec.ts`. This
module is a thin shim so the visual suite can be invoked through the
same `pytest` entrypoint the rest of the project uses, while staying
opt-in (marked `visual`, deselected by default).

Run with:
    pytest -m visual

The wrapper:
- requires the apx dev server reachable on http://localhost:9001
  (Playwright's `webServer` config will start one with
  `uv run apx dev start` if it's not already up — see
  `playwright.config.ts`),
- shells out to `uv run apx bun playwright test`,
- streams Playwright's reporter output to stdout so the pytest log
  matches what you'd see running the spec directly.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.visual
def test_brand_themes_visual_regression() -> None:
    """Run the Playwright visual-regression spec end-to-end.

    Fails if Playwright exits non-zero (i.e. at least one screenshot
    differs from its baseline beyond the configured tolerance).
    """
    if shutil.which("uv") is None:
        pytest.skip("uv is not on PATH; cannot launch playwright via apx")

    result = subprocess.run(
        ["uv", "run", "apx", "bun", "playwright", "test", "--reporter=list"],
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0, (
        "Playwright visual-regression suite failed. "
        "Inspect diffs under `test-results/` and, after intentional UI "
        "changes, refresh baselines with "
        "`uv run apx bun run test:visual:update`."
    )
