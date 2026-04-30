# Testing framework — agent-autonomy edition

Building a new accelerator (AECO Hub Phase 1-6) surfaced ~14 places where
the loop required user intervention or magic-number debugging. This
framework pulls those into one cohesive pipeline so a future agent can
build → deploy → verify a new accelerator without you in the loop.

## Five stages, one entry point

```bash
scripts/check_all.sh
```

| Stage | Command | Catches |
|---|---|---|
| 1. Drift check | `python scripts/sync_env_from_state.py --check` | Resource ID drift between `.env.example`, `app.yml`, `databricks.yml`, and `fevm_agents_state.json` |
| 2. Type check | `uv run apx dev check` | TypeScript + Python type errors |
| 3. Unit tests | `uv run pytest --ignore=tests/integration` | Contract regressions (incl. the AST-based MAS naming test, the streaming-route marker, the conftest leak) |
| 4. Preflight | `python scripts/preflight.py` | Stale env, profile not reachable, app SP missing CREATE on `public`, dashboard embed not allowed |
| 5. Smoke | `python scripts/smoke.py --base <url>` | `/api/_health` warnings, missing accelerator rows, 5xx on portfolio endpoints |

Run flags:
- `--skip-deploy` — stages 1-3 only (no Databricks calls)
- `--skip-permissions` — skip the slow Lakebase permission round-trip in stage 4

## What each tool replaces

### `scripts/preflight.py` — "is this workspace ready to deploy?"
Runs a structured set of checks before `databricks bundle deploy`. Each
check is `Ok | Warn | Err` with a JSON-serializable detail blob; non-zero
exit on any `Err`.

What it catches that bit Phase 1-6:
- **Stale `.env`** pointing at a deleted workspace (Phase 1)
- **App SP missing `CREATE ON SCHEMA public`** — the silent
  `permission denied` that ate Phase 6 deploy (`runtime.initialize_models`
  swallows it as "concurrent worker race")
- **Resource ID drift** between env files (Phase 7 left `app.yml`
  pointing at the old MAS endpoint name after the rebuild)
- **Dashboard embedding not allowed** — iframe shows "embedding not
  allowed in this workspace" if `aibi-dashboard-embedding-approved-domains`
  isn't set

### `scripts/sync_env_from_state.py` — single source of truth for resource IDs
Each target file (`.env.example`, `app.yml`, `databricks.yml`) has a
marker pair:

```yaml
# AECO_AUTOGEN_BEGIN: resource-ids
- name: ADTECH_DASHBOARD_ID
  value: 01f13f258d20183894ba2b942833b50e
...
# AECO_AUTOGEN_END
```

Lines outside the markers are left alone. After
`scripts/bootstrap.py` writes `fevm_agents_state.json`, run
`scripts/sync_env_from_state.py` once to refresh all three files. CI
runs it with `--check` to fail fast on drift.

The script intentionally **refuses to silently append** — if the
markers aren't there, it tells you to add them once. That's a
structural decision (correct YAML indentation, right place in the
file) that should be made by a human, not fabricated by the script.

### `scripts/smoke.py` — post-deploy verification
Hits `/api/_health` and one portfolio-shaped endpoint per accelerator;
asserts 2xx + non-empty payload. Uses `DATABRICKS_TOKEN` so it works in
CI without an SSO browser.

What it catches:
- Missing platform Project rows (e.g. AECO Hub didn't show on landing
  page Phase 6)
- Empty per-accelerator tables (silent ` create_all` failure)
- `startup_warnings` from the `/api/_health` endpoint surface latent
  permission errors

### `scripts/dump_openapi.py` — break the dependency cycle
Backend lifespan crashes block frontend compile because `ui/lib/api.ts`
only regenerates when `apx dev start` boots successfully. This script
imports the FastAPI app *without* its lifespan and dumps `openapi.json`
to `.build/`. The codegen step picks it up.

Recovery move: `python scripts/dump_openapi.py && uv run apx frontend build`.

### `scripts/snapshot_diff.py` + `tests/visual/baselines/` — visual regression
The agent walks the deployed app via chrome-devtools MCP, dumps each
page's accessibility-tree snapshot, and runs:

```bash
python scripts/snapshot_diff.py \
    --baseline tests/visual/baselines/<page>.md \
    --current  /tmp/<page>.md
```

`scripts/snapshot_diff.NORMALIZERS` strips volatile fields (`uid=N_M`,
live IoT readings, ISO timestamps, recharts axis ticks, synthetic sensor
codes) so a clean run is a deterministic byte match against the
checked-in baseline. After an intentional UI change, regenerate with
`--update`.

Catches the class of UI drift bugs we saw in Phase 6 visual verification:
- "Qa Qc" instead of "QA / QC" (capitalize-words on raw enum value)
- Stale page subtitle still referencing "Phase 5 ships later"
- MAS chat showing the supervisor's `<execute_tool>` block

### `scripts/grant_lakebase_app_permissions.py`
Already there — wired into `bootstrap.py` after `configure_embedding`.
Idempotent. Makes future fresh workspaces self-grant the app SP CREATE
permission so deploys don't silently lose new tables.

## Code-level test infra additions

### `streaming_endpoint` decorator
`from innovation_factory.backend.services.streaming import streaming_endpoint`

Marks a FastAPI route as SSE so the contract regression test
(`response_model + operation_id`) skips it. Replaces the brittle
`STREAMING_PATHS = {"/chat", "/ka-chat"}` allowlist that broke every
time a new chat endpoint shipped.

### AST-based MAS naming test
`tests/scripts/test_mas_naming_convention.py` no longer parses
`scripts/deploy_agents_fevm.py` with regexes — it walks the AST. Block
order (`adtech_agents` → `aeco_agents` → `hb_agents`) doesn't break the
test anymore.

## How a future build runs end-to-end

```bash
# 0. Make sure repo is clean
scripts/check_all.sh --skip-deploy

# 1. Bootstrap a fresh workspace (one-time)
python scripts/bootstrap.py --target <profile>

# 2. Sync all env files from state
python scripts/sync_env_from_state.py

# 3. Deploy
databricks bundle deploy -t dev -p <profile>
databricks bundle run innovation-factory-app -t dev -p <profile>

# 4. Full verification
scripts/check_all.sh

# 5. Visual regression (chrome-devtools MCP)
#    For each page: capture snapshot, diff against baseline.
```

If anything in stages 1-5 fails, the structured exit code + JSON output
tells the agent exactly what to fix. The user only steps in for the
one-time SSO ceremony in step 5 (until the cookie-reuse work in the
backlog lands).
