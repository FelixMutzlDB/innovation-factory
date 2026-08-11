#!/usr/bin/env bash
# Stop hook: block turn-end until `uv run apx dev check` is clean.
#
# OPT-IN. Not active until wired into .claude/settings.json under hooks.Stop.
# Purpose: let auto-mode / unattended sessions self-verify (tsc + ty) instead of
# handing back a red build. Deliberately runs ONLY when there are uncommitted
# source changes, so pure Q&A turns aren't taxed. pytest is intentionally NOT
# here (too slow for a per-turn gate) — keep that in the prompt or a /goal.
set -uo pipefail

INPUT="$(cat)"

# Avoid loops: if we're already inside a stop-hook continuation, let the turn end.
if printf '%s' "$INPUT" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true'; then
  exit 0
fi

# .claude/hooks -> gallery repo root
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)" || exit 0
cd "$REPO_DIR" || exit 0

# Only run the (heavier) check when src/ has uncommitted changes worth checking.
if git diff --quiet -- src/ 2>/dev/null && git diff --cached --quiet -- src/ 2>/dev/null; then
  exit 0
fi

# NOTE: invoked via `python -m apx` (not `uv run apx`) because the .venv/bin/apx
# shebang points at a stale parent .venv and exits 126 — see docs/TODO.md.
OUT="$(uv run python -m apx dev check 2>&1)"
STATUS=$?
if [ "$STATUS" -ne 0 ]; then
  OUT="$OUT" python3 - <<'PY'
import json, os
out = os.environ.get("OUT", "")
reason = "apx dev check failed — fix these before ending the turn:\n" + out
print(json.dumps({"decision": "block", "reason": reason}))
PY
fi
exit 0
