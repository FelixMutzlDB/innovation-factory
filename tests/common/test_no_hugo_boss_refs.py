"""Regression: the full "Hugo Boss" brand name must not appear anywhere
in the tracked codebase except explicitly allowed locations.

The user asked for all "Hugo Boss" mentions to be removed from the app,
MAS/KA/Genie text, dashboards, and seed data. "HB" is the approved
substitute. This test prevents future copy-paste regressions.

Allowed exceptions (things that legitimately keep the history):
  - scripts/archive/migrate_full.py — historical reference, not run
  - docs/lessons-learned.md — describes past decisions including old names
  - .claude/, .git/, .venv/, node_modules/ — not source
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_PATH_PREFIXES = (
    "scripts/archive/",
    "docs/lessons-learned.md",
    ".claude/",
    ".git/",
    ".venv/",
    ".apx/",
    "node_modules/",
    ".playwright-browsers/",
    ".pytest_cache/",
    ".build/",
    "src/innovation_factory/__dist__/",
    "tests/common/test_no_hugo_boss_refs.py",  # this file mentions the pattern
)
PATTERN = re.compile(r"Hugo Boss|HUGO BOSS|hugoboss", re.IGNORECASE)


def _should_check(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT).as_posix()
    return not any(rel.startswith(p) for p in ALLOWED_PATH_PREFIXES)


def test_no_hugo_boss_outside_allowed_paths():
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    hits: list[tuple[str, int, str]] = []
    for rel in result.stdout.splitlines():
        path = REPO_ROOT / rel
        if not _should_check(path) or not path.is_file():
            continue
        # skip obvious binaries
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf",
                                     ".whl", ".ico", ".svg", ".lock"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if PATTERN.search(line):
                hits.append((rel, lineno, line.rstrip()))

    if hits:
        msg = "\n".join(f"  {p}:{ln}: {content}" for p, ln, content in hits[:20])
        raise AssertionError(
            f"Found {len(hits)} Hugo-Boss reference(s) outside allowed paths.\n"
            f"Rename to 'HB'. First matches:\n{msg}"
        )
