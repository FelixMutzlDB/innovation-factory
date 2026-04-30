"""Single source of truth for per-accelerator resource IDs.

After ``scripts/bootstrap.py`` writes ``scripts/fevm_agents_state.json``,
this script regenerates the resource-ID env-var blocks in ``app.yml``,
``databricks.yml``, and ``.env.example``. Phase 6 had three places to
update — easy to miss one — and Phase 7 rebuilds confirmed the bug
(MAS endpoints rebuilt, app.yml still pointed at the old ones).

Each target file has a marked region:

    # AECO_AUTOGEN_BEGIN: resource-ids
    ...generated env vars...
    # AECO_AUTOGEN_END

Lines outside that block are left alone. Run with ``--check`` for a CI
mode that fails non-zero if the generated content would differ from
what's already on disk.

Usage:
    python scripts/sync_env_from_state.py            # write
    python scripts/sync_env_from_state.py --check    # CI: fail if drift
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = REPO_ROOT / "scripts" / "fevm_agents_state.json"

BEGIN = "AECO_AUTOGEN_BEGIN: resource-ids"
END = "AECO_AUTOGEN_END"


# Maps state-file keys → env-var-name prefixes, mirrors emit_env_vars in
# bootstrap.py. Add a new accelerator's state-key entries here.
GENIE_KEYS = {
    "hb_sc": "HB_SC",
    "hb_aq": "HB_AQ",
    "adtech": "ADTECH",
    "aeco_project_analytics": "AECO_PROJECT_ANALYTICS",
    "aeco_operations_intelligence": "AECO_OPERATIONS_INTELLIGENCE",
}
KA_KEYS = {
    "issue_resolution": "ADTECH_ISSUE_RESOLUTION",
    "customer_relations": "ADTECH_CUSTOMER_RELATIONS",
    "aeco_standards_compliance": "AECO_STANDARDS_COMPLIANCE",
}
MAS_KEYS = {"adtech": "ADTECH", "hb": "HB", "aeco": "AECO"}
DASHBOARD_KEYS = {
    "adtech": "ADTECH",
    "hb_sc": "HB_SC",
    "hb_aq": "HB_AQ",
    "aeco_energy": "AECO_ENERGY",
}


def build_env_vars(state: dict) -> list[tuple[str, str]]:
    """Return ``[(name, value), ...]`` derived from state.json — order
    matters because the rendered block is human-read."""
    out: list[tuple[str, str]] = []

    # Dashboards first (consumers want them up-front)
    for sk, prefix in DASHBOARD_KEYS.items():
        v = (state.get("dashboards") or {}).get(sk, "")
        out.append((f"{prefix}_DASHBOARD_ID", v))

    # Genie spaces
    for sk, prefix in GENIE_KEYS.items():
        v = (state.get("genies") or {}).get(sk, "")
        out.append((f"{prefix}_GENIE_SPACE_ID", v))

    # KAs
    for sk, prefix in KA_KEYS.items():
        ka = (state.get("kas") or {}).get(sk, {})
        out.append((f"{prefix}_KA_TILE_ID", ka.get("tile_id", "")))
        out.append((f"{prefix}_KA_ENDPOINT", ka.get("endpoint_name", "")))

    # MASes
    for sk, prefix in MAS_KEYS.items():
        mas = (state.get("mas") or {}).get(sk, {})
        out.append((f"{prefix}_MAS_TILE_ID", mas.get("tile_id", "")))
        out.append((f"{prefix}_MAS_ENDPOINT_NAME", mas.get("endpoint_name", "")))

    return out


def render_dotenv_block(pairs: list[tuple[str, str]]) -> str:
    lines = [f"# {BEGIN}"]
    lines += [f"{k}={v}" for k, v in pairs]
    lines.append(f"# {END}")
    return "\n".join(lines)


def render_yaml_block(pairs: list[tuple[str, str]], indent: str) -> str:
    empty = '""'
    lines = [f"{indent}# {BEGIN}"]
    for k, v in pairs:
        lines.append(f"{indent}- name: {k}")
        lines.append(f"{indent}  value: {v if v else empty}")
    lines.append(f"{indent}# {END}")
    return "\n".join(lines)


class MissingMarkers(RuntimeError):
    """Raised when a target file lacks the autogen begin/end markers.

    We intentionally don't auto-append — the marker placement is a
    structural decision (e.g. inside a YAML ``env:`` block at the right
    indentation) that should be made once by a human, not silently
    fabricated by the script.
    """


def replace_block(text: str, marker_indent: str, new_block: str) -> str:
    """Replace the ``BEGIN/END`` block in *text*.

    Raises :class:`MissingMarkers` if either marker is absent — the
    caller should print a structured message telling the user to add
    them.
    """
    begin_marker = f"{marker_indent}# {BEGIN}"
    end_marker = f"{marker_indent}# {END}"
    start = text.find(begin_marker)
    if start < 0:
        raise MissingMarkers(
            f"missing '{begin_marker}' marker — add a one-time pair of "
            f"# {BEGIN} / # {END} markers around the resource-id env-var "
            f"block; subsequent runs will keep them in sync."
        )
    end = text.find(end_marker, start)
    if end < 0:
        raise MissingMarkers(
            f"found '{begin_marker}' but no matching '{end_marker}'"
        )
    end += len(end_marker)
    return text[:start] + new_block + text[end:]


def sync_file(
    path: Path, mode: str, indent: str = ""
) -> tuple[bool, str | None, str | None]:
    """Apply the autogen block to *path*.

    Returns ``(changed, updated_text, error)``:
    - ``changed=True, updated_text=str, error=None`` — content differs
    - ``changed=False, updated_text=None, error=None`` — already in sync
    - ``changed=False, updated_text=None, error=str`` — markers missing
    """
    if not path.is_file():
        return False, None, f"{path}: not found"
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    pairs = build_env_vars(state)
    if mode == "dotenv":
        new_block = render_dotenv_block(pairs)
    elif mode == "yaml":
        new_block = render_yaml_block(pairs, indent=indent)
    else:
        raise ValueError(f"unknown mode {mode!r}")
    original = path.read_text(encoding="utf-8")
    try:
        updated = replace_block(original, indent, new_block)
    except MissingMarkers as e:
        return False, None, str(e)
    if updated == original:
        return False, None, None
    return True, updated, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="Fail (exit 2) if any file would change. For CI/preflight.",
    )
    args = parser.parse_args()

    if not STATE_FILE.is_file():
        print(f"ERROR: state file not found at {STATE_FILE}", file=sys.stderr)
        return 1

    targets = [
        (REPO_ROOT / ".env.example", "dotenv", ""),
        (REPO_ROOT / "app.yml", "yaml", "  "),
        (REPO_ROOT / "databricks.yml", "yaml", "          "),
    ]
    drift = 0
    missing = 0
    for path, mode, indent in targets:
        rel = path.relative_to(REPO_ROOT)
        changed, payload, error = sync_file(path, mode, indent=indent)
        if error:
            print(f"  [?] {rel}: {error}", file=sys.stderr)
            missing += 1
            continue
        if not changed:
            print(f"  [=] {rel}: in sync")
            continue
        if args.check:
            print(f"  [!] {rel}: would change", file=sys.stderr)
            drift += 1
        else:
            assert payload is not None
            path.write_text(payload, encoding="utf-8")
            print(f"  [+] {rel}: updated")
    if missing:
        print(f"\nFAIL — {missing} file(s) missing autogen markers. "
              f"Add a one-time '# {BEGIN}' / '# {END}' pair around the "
              f"resource-id block in each file.", file=sys.stderr)
        return 3
    if args.check and drift:
        print(f"\nFAIL — {drift} file(s) drift from {STATE_FILE.name}. "
              f"Run: python scripts/sync_env_from_state.py", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
