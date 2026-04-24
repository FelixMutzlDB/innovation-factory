"""Policy regression: only `components/safe-markdown.tsx` is allowed to
import `react-markdown` directly. Every other UI file must use the
``SafeMarkdown`` wrapper, which bakes in rehype-sanitize so LLM-produced
or doc-authored markdown can't smuggle in <script>, onerror=, or
javascript: URLs.

If this test fails, either:
  (a) you legitimately need to extend the sanitize policy — do it in
      components/safe-markdown.tsx and add test coverage there, or
  (b) you're inadvertently reintroducing an XSS vector. Import
      SafeMarkdown instead of ReactMarkdown.

Background: https://github.com/remarkjs/react-markdown#security
"""
from __future__ import annotations

import pathlib
import re
import subprocess


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
UI_ROOT = REPO_ROOT / "src" / "innovation_factory" / "ui"
SAFE_WRAPPER_REL = "src/innovation_factory/ui/components/safe-markdown.tsx"

IMPORT_PATTERN = re.compile(
    r'^\s*import\s+[^"\']+from\s+[\'"]react-markdown[\'"]', re.M
)


def _tracked_files() -> list[pathlib.Path]:
    """Return all tracked files under ui/ (skips node_modules, build)."""
    r = subprocess.run(
        ["git", "ls-files", "src/innovation_factory/ui/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [REPO_ROOT / p for p in r.stdout.splitlines()]


def test_only_safe_wrapper_imports_react_markdown():
    violations: list[tuple[str, int, str]] = []
    for path in _tracked_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel == SAFE_WRAPPER_REL:
            continue
        if path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if IMPORT_PATTERN.match(line):
                violations.append((rel, lineno, line.strip()))

    if violations:
        detail = "\n".join(f"  {p}:{ln}: {content}" for p, ln, content in violations)
        raise AssertionError(
            "Found direct `react-markdown` imports outside the SafeMarkdown "
            f"wrapper ({SAFE_WRAPPER_REL}). Replace with:\n"
            "    import SafeMarkdown from \"@/components/safe-markdown\";\n\n"
            "Violations:\n"
            f"{detail}"
        )


def test_safe_wrapper_applies_rehype_sanitize():
    """The wrapper must actually plug rehype-sanitize into every render,
    not just import it."""
    text = (REPO_ROOT / SAFE_WRAPPER_REL).read_text(encoding="utf-8")
    assert "rehype-sanitize" in text, "SafeMarkdown must import rehype-sanitize"
    assert "rehypeSanitize" in text, "SafeMarkdown must reference rehypeSanitize symbol"
    # The wrapper hard-codes rehypeSanitize as the first rehype plugin —
    # callers can only append additional plugins, they cannot remove it.
    assert re.search(
        r"rehypePlugins=\{\[rehypeSanitize", text
    ), "SafeMarkdown must pass rehypeSanitize as the first rehype plugin"
