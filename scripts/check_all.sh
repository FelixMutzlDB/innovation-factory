#!/usr/bin/env bash
# Single-entry-point pipeline for "is the repo + deployed app healthy?"
# Designed for the agent (or CI) to run end-to-end. Each stage is
# independently runnable and exits non-zero on failure.
#
# Stages:
#   1. drift-check  — `sync_env_from_state.py --check`
#   2. type-check   — `apx dev check` (tsc + ty)
#   3. unit tests   — `pytest --ignore=tests/integration`
#   4. preflight    — `preflight.py` (Databricks profile, SP perms, embedding)
#   5. smoke        — `smoke.py` against the deployed app (needs DATABRICKS_TOKEN)
#
# Usage:
#   scripts/check_all.sh                             # run everything
#   scripts/check_all.sh --skip-deploy               # skip 4+5 (no Databricks calls)
#   scripts/check_all.sh --skip-permissions          # skip the slow Lakebase check
#   PROFILE=fevm-felix-demo scripts/check_all.sh
#   APP_URL=https://... scripts/check_all.sh
set -euo pipefail

cd "$(dirname "$0")/.."

PROFILE="${PROFILE:-fevm-felix-demo}"
APP_URL="${APP_URL:-https://innovation-factory-7474658643170817.aws.databricksapps.com}"
SKIP_DEPLOY=false
SKIP_PERMS=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-deploy) SKIP_DEPLOY=true; shift ;;
        --skip-permissions) SKIP_PERMS=true; shift ;;
        *) echo "Unknown arg: $1"; exit 2 ;;
    esac
done

bold() { printf "\n\033[1m=== %s ===\033[0m\n" "$1"; }
ok() { printf "\033[32m✓\033[0m %s\n" "$1"; }
fail() { printf "\033[31m✗\033[0m %s\n" "$1"; exit 1; }

# Stage 1 — env-file drift
bold "1. drift-check"
uv run python scripts/sync_env_from_state.py --check || fail "env files drift from fevm_agents_state.json"
ok "env files in sync"

# Stage 2 — type check
bold "2. type-check (tsc + ty)"
uv run apx dev check 2>&1 | tee /tmp/check_all_typecheck.log
grep -q "✅ \[tsc\] TypeScript compilation succeeded" /tmp/check_all_typecheck.log \
    || fail "tsc failed"
grep -q "✅ \[ty\] Python type check succeeded" /tmp/check_all_typecheck.log \
    || fail "ty failed"
ok "tsc + ty pass"

# Stage 3 — unit tests
bold "3. unit tests"
uv run pytest tests/ -q --ignore=tests/integration || fail "unit tests failed"
ok "unit tests pass"

if $SKIP_DEPLOY; then
    bold "DONE — local stages green (preflight + smoke skipped)"
    exit 0
fi

# Stage 4 — preflight
bold "4. preflight (Databricks profile + perms + embedding)"
preflight_args=("--profile" "$PROFILE")
if $SKIP_PERMS; then preflight_args+=("--skip-permissions"); fi
uv run python scripts/preflight.py "${preflight_args[@]}" || fail "preflight failed"
ok "preflight green"

# Stage 5 — smoke against deployed app
bold "5. smoke test against $APP_URL"
if [[ -z "${DATABRICKS_TOKEN:-}" ]]; then
    DATABRICKS_TOKEN="$(databricks auth token --profile "$PROFILE" \
        | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"
    export DATABRICKS_TOKEN
fi
uv run python scripts/smoke.py --base "$APP_URL" || fail "smoke failed"
ok "smoke green"

bold "DONE — all stages green ✓"
