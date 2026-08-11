# Innovation Factory

> Last updated: 2026-05-18 | Owner: Felix Mutzl | FEIP: [FEIP-5472](https://databricks.atlassian.net/browse/FEIP-5472)
> Platform: Multi-accelerator showcase for Databricks Apps (FastAPI + React)
> Stage: 7 accelerators live (yard-pro P0 + P1 + most of P2 shipped on `feature/yard-pro`)
> Tracking: [TODO.md](docs/TODO.md) | Refinement: [docs/tasks/refinement.md](docs/tasks/refinement.md) | Revision: [docs/revision-checklist.md](docs/revision-checklist.md)

## Current State

> Volatile status — the accelerator roster, deploy IDs, workspace, and branch state — lives in **[docs/TODO.md](docs/TODO.md)** (see the dated *Current State snapshot* near the top). It's kept out of this always-loaded file so a stale, time-stamped status block can't drown the behavioral rules below (the article's #1 CLAUDE.md failure mode).

## Codebase Tree

```
src/innovation_factory/
  backend/
    app.py                          # FastAPI app + lifespan (DB init, seeding)
    router.py                       # Route aggregator (platform + per-project)
    config.py                       # Pydantic settings (DB, app config)
    runtime.py                      # DB engine, Lakebase OAuth rotation, WorkspaceClient
    dependencies.py                 # FastAPI DI: SessionDep, ConfigDep, get_obo_ws()
    models.py                       # Platform models: Project, IdeaSession, IdeaMessage
    seed.py                         # Master seed orchestrator (idempotent)
    services/
      databricks_agents.py          # Shared MAS/KA query + response extraction
      streaming.py                  # Shared SSE chat streaming utility
    routers/
      projects.py                   # GET /api/projects, /api/projects/{slug}
      ideas.py                      # Idea builder chat sessions
    projects/                       # One folder per accelerator (see layout below)
      vi_home_one/                  # Smart Energy (neighborhood monitoring)
      bsh_home_connect/             # Remote Assist (device troubleshooting)
      mol_asm_cockpit/              # Fuel & Retail (station KPIs, anomalies)
      adtech_intelligence/          # Advertising (campaigns, Genie, MAS)
      hb_product_center/            # Fashion (CLIP recognition, quality, supply chain)
      aeco_hub/                     # AECO digital twin (BIM, IoT, energy, MAS, KA, graph)
      yard_pro/                     # AI gardening companion (KA, vision, telemetry,
                                    # Art. 22 review-and-confirm rail, dealer panel)
  ui/
    main.tsx                        # React entry (Router, QueryClient)
    routes/                         # TanStack Router file-based routes
    components/
      ui/                           # shadcn/ui primitives
      apx/                          # App framework (navbar, sidebar, theme)
      chat/                         # Shared chat interface
    lib/
      api.ts                        # AUTO-GENERATED OpenAPI client (never edit)
      selector.ts                   # Data selector utility
tests/                              # pytest: common/, projects/, integration/
scripts/                            # Databricks setup (agents, dashboards, vector search, migration)
docs/
  lessons-learned.md                # 31-section technical reference & lessons learned (canonical)
  new-project.md                    # 4-phase methodology for spinning up a new accelerator
  tasks/refinement.md               # Full audit findings with prioritized fixes
  projects/                         # Per-accelerator design docs
  TODO.md                           # Outstanding work tracker (status + timestamps)
```

### Standard Accelerator Layout

```
projects/<slug>/
  router.py                         # FastAPI router aggregation
  models.py                         # SQLModel tables + Pydantic I/O schemas
  databricks_config.py              # Env-var config (dashboard IDs, endpoints)
  routers/                          # Feature sub-routers (domain pages)
  services/                         # Business logic (chat, anomaly detection, etc.)
  seed.py                           # PGlite-safe local seed (~1K rows)
  ka_docs/                          # Optional: Knowledge Assistant source docs
```

## Working mode (read before every non-trivial task)

For anything larger than a one-line fix, follow this loop:

1. **Investigate** — read the relevant code, git history, logs, and prior docs before forming an opinion. Use Explore agents in parallel for wide codebase sweeps.
2. **Plan** — write out the plan *including the test design* (unit, integration, and where relevant UI/E2E). Hand it to the user for review before touching implementation.
3. **Implement** — smallest viable change; keep commits focused.
4. **Test thoroughly** — run the designed tests, exercise the golden path and edge cases, and for UI changes actually open a browser.
5. **Iterate** — fix issues surfaced by testing until the feature works well under realistic conditions. Don't declare done on the first green run.

Throughout, prioritize in this order: **operational efficiency** (readability, simplicity, maintainability, dev-loop speed), **security** (OWASP top 10, input validation, secrets handling, least-privilege resource access), and **compliance with coding best practices** (the Do's and Don'ts below, plus the constraints). Only skip the investigate/plan step for truly trivial edits, and only skip review with the user when they've explicitly said "just do it".

**Regression-test rule:** no P0 or P1 bug fix is considered done without a named, automated regression test. The test title should reference the bug symptom (not just the fix). For SQL-safety, XSS, auth, and other security fixes, this rule is non-negotiable.

**Pre-PR review rule:** before `git push` / opening a PR, run `/review` (Isaac Review — Databricks' recommended code + doc review pipeline) as the adversarial review step. It reviews the diff in a fresh context, so it catches gaps the implementing session is blind to. Treat correctness/requirement findings as blocking; treat style-only findings as optional (don't over-engineer to clear them).

## Constraints (read before every task)

- **Never edit auto-generated files** — `ui/lib/api.ts` and `ui/types/routeTree.gen.ts` regenerate on save when dev servers run
- **No raw SQL interpolation** — UC Statement Execution doesn't support params; use the allowlist-based `_validate_column()` / `_escape_like()` in `uc_query_service.py`
- **All API routes need** `response_model` and `operation_id` — required for TypeScript client generation
- **Prefix project-specific enums** — e.g. `MacAlertSeverity` not `AlertSeverity`, to avoid OpenAPI schema collisions
- **PGlite limit** — keep seed data under ~10K rows; large datasets go to `seed_uc_tables.py` (PySpark)
- **Lakebase OAuth tokens expire in 1 hour** — `runtime.py` handles rotation via SQLAlchemy `do_connect` event
- **torch is 900MB+** — it's bundled for CLIP (HB Product Center only); making it optional is a tracked TODO

## Do's and Don'ts

- OpenAPI client auto-regenerates on code changes when dev servers are running — don't manually regenerate.
- Prefer running apx related commands via MCP server if it's available.
- Use the apx MCP `search_registry_components` and `add_component` tools to find and add shadcn/ui components.
- When using the API calls on the frontend, use error boundaries to handle errors.
- Run `apx dev check` command (via CLI or MCP) to check for errors in the project code after making changes.
- If agent has access to native browser tool, use it to verify changes on the frontend. If such tool is not present or is not working, use playwright MCP to automate browser actions (e.g. screenshots, clicks, etc.).
- **Databricks SDK:** Use the apx MCP `docs` tool to search Databricks SDK documentation instead of guessing or hallucinating API signatures.

## Package Management
- **Frontend:** Bun might not be present on user's $PATH. It's recommended to use prebundled bun (e.g., `uv run apx bun install` or `uv run apx bun add <dependency>`), unless user explicitly stated otherwise.
- **Python:** Always use `uv` (never `pip`)

## Component Management
- **Finding components:** Use MCP `search_registry_components` to search for available shadcn/ui components
- **Adding components:** Use MCP `add_component` or CLI `uv run apx components add <component> --yes` to add components
- **Component location:** If component was added to a wrong location (e.g. stored into `src/components` instead of `src/innovation-factory/ui/components`), move it to the proper folder
- **Component organization:** Prefer grouping components by functionality rather than by file type (e.g. `src/innovation-factory/ui/components/chat/`)

## Models & API
- **3-model pattern:** `Entity` (DB/SQLModel), `EntityIn` (input/Pydantic), `EntityOut` (output/Pydantic)
- **API routes must have:** `response_model` and `operation_id` for client generation
- **MAS/KA endpoints:** Use `ws.api_client.do()` with `input` field, not `messages` — see `services/databricks_agents.py`

## Frontend Rules
- **Routing:** `@tanstack/react-router` (file-based routes in `src/innovation_factory/ui/routes/`)
- **Data fetching:** Always use `useXSuspense` hooks with `Suspense` and `Skeleton` components
- **Pattern:** Render static elements immediately, fetch API data with suspense
- **Components:** Use shadcn/ui, add to `src/innovation_factory/ui/components/`
- **Data access:** Use `selector()` function for clean destructuring (e.g., `const {data: profile} = useProfileSuspense(selector())`)

## Development Commands

```bash
uv run apx dev start               # Start backend + frontend + OpenAPI watcher
uv run apx dev status              # Show running servers and ports
uv run apx dev check               # TypeScript + Python linting
uv run apx dev logs                # Recent logs (default: last 10m)
uv run apx dev logs -f             # Follow/stream logs live
uv run apx dev stop                # Stop all servers
uv run apx build                   # Production build
pytest                             # Run tests (add -m integration for live Databricks tests)
```

## Key Reference Files

| What | Where |
|------|-------|
| App deployment config | `app.yml` (resources, env vars) |
| Bundle deployment | `databricks.yml` |
| Python deps & apx metadata | `pyproject.toml` |
| Technical reference (31 topics) | `docs/lessons-learned.md` |
| New project methodology | `docs/new-project.md` |
| Audit & refinement plan | `docs/tasks/refinement.md` |
| Outstanding work | `docs/TODO.md` |
| Per-accelerator design docs | `docs/projects/*.md` |
| Databricks setup scripts | `scripts/` |

## MCP Tools Reference

When the apx MCP server is available, use these tools:

| Tool | Description |
|------|-------------|
| `start` | Start development server and return the URL |
| `stop` | Stop the development server |
| `restart` | Restart the development server (preserves port if possible) |
| `logs` | Fetch recent dev server logs |
| `check` | Check project code for errors (runs tsc and ty checks in parallel) |
| `refresh_openapi` | Regenerate OpenAPI schema and API client |
| `search_registry_components` | Search shadcn registry components using semantic search |
| `add_component` | Add a component to the project |
| `docs` | Search Databricks SDK documentation for code examples and API references |
| `databricks_apps_logs` | Fetch logs from deployed Databricks app using Databricks CLI |
| `get_route_info` | Get code example for using a specific API route |
