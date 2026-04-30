"""Visual-regression diff for the agent-driven UI verification loop.

The agent walks the deployed app via chrome-devtools MCP, dumps each
page's accessibility-tree snapshot to a file, and runs this script to
compare it against a checked-in baseline under
``tests/visual/baselines/<page>.md``. The diff is line-based, with
volatile fields (UIDs, timestamps, dynamic counts) normalized away so a
clean run is a deterministic byte match against the baseline.

Usage:
    # Compare a captured snapshot against a baseline
    python scripts/snapshot_diff.py \\
        --baseline tests/visual/baselines/aeco-hub-portfolio.md \\
        --current  /tmp/portfolio-snapshot.md

    # Update the baseline (e.g. after intentional UI change)
    python scripts/snapshot_diff.py \\
        --baseline tests/visual/baselines/aeco-hub-portfolio.md \\
        --current  /tmp/portfolio-snapshot.md \\
        --update

    # Just normalize stdin and emit to stdout (useful in shell pipes)
    python scripts/snapshot_diff.py --normalize < snapshot.md > normalized.md

Exit codes:
    0 — clean (or --update succeeded)
    1 — drift detected
    2 — invalid arguments / missing files
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path


# Regex set that strips volatile UI bits a reasonable diff shouldn't fail on.
NORMALIZERS: list[tuple[re.Pattern[str], str]] = [
    # uid="N_M" — chrome-devtools assigns these per-snapshot
    (re.compile(r'uid=\d+_\d+'), 'uid=<UID>'),
    # Live IoT chart values — change every poll
    (re.compile(r'(StaticText\s+")(\d+\.\d+)"'), r'\1<NUM>"'),
    # ISO timestamps in any reasonable format
    (re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?'),
     '<TIMESTAMP>'),
    # Dates that drift (today/relative)
    (re.compile(r'"(20\d{2}-\d{2}-\d{2})"'), '"<DATE>"'),
    # Recharts axis tick labels for dates ("Mar 31", "Apr 12")
    (re.compile(r'StaticText "(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2}"'),
     'StaticText "<MONTH-DAY>"'),
    # Random sensor codes that change with seed timestamps
    (re.compile(r'"S-\d{3}-\d{4}"'), '"<SENSOR-CODE>"'),
]


def normalize(text: str) -> str:
    """Strip volatile fields (UIDs, timestamps, live readings) so the
    diff focuses on layout + copy, not noise."""
    for pat, repl in NORMALIZERS:
        text = pat.sub(repl, text)
    # Trailing whitespace eats false positives in markdown snapshots.
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"


def diff_snapshots(baseline: Path, current: Path) -> list[str]:
    base_text = normalize(baseline.read_text(encoding="utf-8"))
    cur_text = normalize(current.read_text(encoding="utf-8"))
    if base_text == cur_text:
        return []
    return list(difflib.unified_diff(
        base_text.splitlines(keepends=True),
        cur_text.splitlines(keepends=True),
        fromfile=str(baseline),
        tofile=str(current),
        n=3,
    ))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--current", type=Path)
    parser.add_argument(
        "--update", action="store_true",
        help="Replace the baseline with the current snapshot (after an intentional UI change).",
    )
    parser.add_argument(
        "--normalize", action="store_true",
        help="Read snapshot from stdin, write normalized output to stdout. "
             "Useful for `chrome-devtools-snapshot | tee /tmp/x.md`.",
    )
    args = parser.parse_args()

    if args.normalize:
        sys.stdout.write(normalize(sys.stdin.read()))
        return 0

    if not args.baseline or not args.current:
        parser.print_usage()
        return 2

    if not args.current.is_file():
        print(f"ERROR: current snapshot not found: {args.current}", file=sys.stderr)
        return 2
    if args.update:
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        normalized = normalize(args.current.read_text(encoding="utf-8"))
        args.baseline.write_text(normalized, encoding="utf-8")
        print(f"Wrote normalized baseline → {args.baseline}")
        return 0
    if not args.baseline.is_file():
        print(f"ERROR: baseline not found: {args.baseline}", file=sys.stderr)
        print("       Run with --update to create it from the current snapshot.",
              file=sys.stderr)
        return 2

    diff = diff_snapshots(args.baseline, args.current)
    if not diff:
        print(f"PASS — {args.baseline.name} matches current snapshot.")
        return 0
    sys.stdout.writelines(diff)
    print(f"\nFAIL — {len(diff)} diff line(s). Either fix the UI or run --update "
          f"if the change was intentional.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
