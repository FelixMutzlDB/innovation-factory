# Innovation Factory — Lessons Learned

> Consolidated technical lessons from building the six accelerators (ViDistrictOne, BSH Remote Assist, MOL ASM Cockpit, AdTech Intelligence, HB Product Center, AECO Hub) plus the shared platform.
> Written for future contributors and for AI agents (Claude, Cursor) working on this codebase.
> Last updated: 2026-05-11.

The first eight sections are distilled from the MOL ASM Cockpit build (commit `dd01f02`) and remain the single most useful reference for wiring new Databricks resources into this repo. Sections 9-26 cover lessons from every major piece of work since. Sections 27-31 are the 5 lessons from the AECO Hub greenfield build (Phases 1-6, shipped 2026-04-29). Sections 32-33 came out of the first monthly revision pass (2026-05-11) — meta-patterns for autonomy handoff and CI hardening. Section 34 came out of the first quarterly revision pass (also 2026-05-11) — the `KNOWN_DEBT` pattern for incremental lint adoption, exercised by clearing the §13 router-discipline debt.

---

## 1. Databricks Lakeview Dashboard API (AI/BI Dashboards)

### Problem
Creating AI/BI dashboards programmatically via the Lakeview API required multiple iterations to get the `serialized_dashboard` JSON structure right. The API returned opaque `"failed to parse serialized dashboard"` errors with no indication of what was wrong.

### Fixes that actually worked

| Attempt | Error | Fix |
|---------|-------|-----|
| 1 | `failed to parse serialized dashboard` | The `query` field inside `datasets` must be a **plain SQL string** (`"query": "SELECT ..."`) — not a nested object (`"query": {"sql": "..."}`) |
| 2 | `validation failed: missing spec or textbox_spec` | `spec` (charts/counters) and `textbox_spec` (text widgets) must be **direct attributes** of each widget object, not inside `overrides` |
| 3 | Silent failures | Empty `"fields": []` arrays in dataset queries can cause issues — omit them entirely |

### Takeaway
The Lakeview `serialized_dashboard` format is **not the same** as the JSON you see in the dashboard UI export. Build up from a minimal single-widget dashboard, inspect, and grow. The Python SDK's `w.lakeview.create(Dashboard(...))` gives clearer errors than the MCP tool.

---

## 2. Multi-Agent Supervisor (MAS) Endpoint Integration

### Problem
Connecting to Agent Bricks MAS endpoints took three rounds to get the request/response shape right.

### The journey
1. SDK `serving_endpoints.query()` with dicts → `AttributeError: 'dict' object has no attribute 'as_dict'`. The SDK expects `ChatMessage` objects.
2. SDK with `ChatMessage` → `Invalid request: 'messages' field is not supported. Please use 'input' field instead.`
3. Raw `requests.post()` with bearer token → `401 Credential was not sent or was of an unsupported type`. The SDK uses OAuth; raw requests doesn't handle auth.

### Solution
Use the SDK's internal HTTP client:

```python
response = ws.api_client.do(
    "POST",
    f"/serving-endpoints/{endpoint_name}/invocations",
    body={"input": [{"role": "user", "content": message}]},
)
```

Response format is non-standard too:

```json
{"output": [{"type": "message", "role": "assistant",
             "content": [{"type": "output_text", "text": "..."}]}]}
```

### Takeaway
MAS/Agent Bricks endpoints do **not** follow the OpenAI-compatible `messages`/`choices` format. Use `ws.api_client.do()` for any endpoint whose wire format isn't covered by the SDK's typed methods. The shared helpers live in `backend/services/databricks_agents.py` — use `query_agent_endpoint()` and `extract_agent_text()` instead of reimplementing this per project.

---

## 3. PGlite (Local Dev Database) Memory Limits

### Problem
Initial seed tried 44 stations × 90 days (~130k records). PGlite crashed during batch INSERTs.

### Symptoms
- Database connection drops during seeding
- `PGlite database initialized` then immediate crash
- All API requests fail with connection errors

### Solution
Keep local seed under ~10k rows. Large datasets live in `seed_uc_tables.py` / `scripts/seed_all_uc_notebook.py` (PySpark, unlimited memory). Use `session.flush()` between batches rather than a single commit.

### Takeaway
PGlite is great for local dev but has hard limits on batch INSERT size. Treat 10k rows as the soft ceiling; anything bigger belongs in a PySpark seed.

---

## 4. Python Type Checker (`ty`) and SQLModel/SQLAlchemy

### Problem
`ty` (used by `apx dev check`) reports many false positives on SQLModel/SQLAlchemy column operations because of metaclass magic.

### Common false positives

| Pattern | `ty` error | Reality |
|---------|-----------|---------|
| `Model.field.desc()` | `unresolved-attribute` | SQLAlchemy column proxy |
| `Model.field >= value` | `unsupported-operator` | SQLAlchemy operator overloading |
| `Model.field.contains(x)` | `unresolved-attribute` on `str` | SQLAlchemy column method |
| `Model.field.in_([...])` | `unresolved-attribute` | SQLAlchemy column method |
| `datetime.utcnow` | `deprecated` | Works; prefer `datetime.now(timezone.utc)` |
| `select(Model)` | `no-matching-overload` | SQLModel dynamic overloads |

### Solution
Two tiers:

1. `pyproject.toml`:
   ```toml
   [tool.ty.src]
   exclude = ["scripts/", "**/seed_uc_tables.py"]
   [tool.ty.rules]
   deprecated = "ignore"
   ```
2. Inline, with the specific rule name:
   ```python
   .order_by(Model.created_at.asc())  # type: ignore[unresolved-attribute]
   ```

### Takeaway
Always name the rule in `# type: ignore[rule]`. Blanket ignores turn into `unused-type-ignore-comment` warnings when `ty` gets smarter. Re-audit after `ty` upgrades.

---

## 5. Environment Variable Configuration Pattern

### Problem
Hardcoded resource IDs (dashboard, Genie, KA, MAS, warehouse) break when moving between workspaces. We paid this cost twice: once when switching from Lakebase Provisioned to Lakebase Autoscaling (`5152f79`), and again when migrating to `fe-sandbox-felix-demo-sandbox` (`8ed7bb8`) and then `fevm-felix-demo` (`6381848`).

### Pattern
Per-project `databricks_config.py` reads `<PREFIX>_*` env vars:

```python
DASHBOARD_ID = os.getenv("MAC_DASHBOARD_ID", "")
MAS_ENDPOINT_NAME = os.getenv("MAC_MAS_ENDPOINT_NAME", "")
```

Shared vars (`WAREHOUSE_ID`, `UC_CATALOG`) are unprefixed and centralized. `.env.example` at repo root documents every knob.

### Takeaway
Never hardcode Databricks resource IDs in router or service files. Read them from env vars, default to empty string, and let the UI render a "not configured" state instead of a broken iframe (introduced in `6381848`).

---

## 6. Project Organization

### Problem
During development, project-specific scripts (dashboard JSON, UC seed scripts, KA documents) piled up in top-level `/scripts/`. Made ownership unclear.

### Correct structure

```
src/innovation_factory/backend/projects/<slug>/
├── databricks_config.py          # env-var config
├── models.py                     # SQLModel models + I/O schemas
├── router.py                     # FastAPI router aggregation
├── routers/                      # individual route files
├── services/                     # business logic
├── seed.py                       # local PGlite seed (~1K rows)
├── seed_uc_tables.py             # Databricks cluster seed (PySpark)
├── create_dashboard.py           # dashboard creation script (if any)
├── dashboard_definition.json     # AI/BI dashboard JSON
└── ka_docs/                      # Knowledge Assistant source docs
```

### Takeaway
Check `git ls-tree` on an existing project before dropping files at the repo root. The top-level `scripts/` directory is reserved for cross-project or platform-wide scripts only.

---

## 7. TanStack Router Route Tree Generation

### Problem
After creating new route files under `routes/projects/<slug>/`, `routeTree.gen.ts` sometimes only partially updates — imports added but `FileRoutesByPath` not.

### Symptoms
- TypeScript errors on route components
- Routes work at runtime but IDE shows red squiggles
- `routeTree.gen.ts` has imports but missing type entries

### Solution
Restart the dev server (`uv run apx dev restart`). For persistent desync, delete `routeTree.gen.ts` and restart.

### Takeaway
Never manually edit auto-generated files (`routeTree.gen.ts`, `ui/lib/api.ts`). Regenerate on conflicts.

---

## 8. Merge Conflict Patterns in Multi-Project Repos

### Observation
When multiple feature branches add new projects, conflicts are always in the same files.

| File | Conflict pattern |
|------|------------------|
| `backend/router.py` | Both branches add `include_router()` at the same location |
| `backend/seed.py` | Both branches add seed imports and project entries |
| `ui/lib/api.ts` | Auto-generated — regenerate after merge |
| `ui/types/routeTree.gen.ts` | Auto-generated — regenerate after merge |

### Takeaway
These are **additive** conflicts. Keep both sides, then regenerate the auto-gen files. A comment marker (`# -- project routers below --`) in `router.py` and `seed.py` makes this trivial.

---

## 9. SQL Injection: UC Statement Execution Doesn't Support Bind Params

### Problem
Unity Catalog's Statement Execution API accepts a plain SQL string — there is no parameterized-query API. Our first HB Product Center queries used f-string interpolation into WHERE clauses, opening a clear SQL injection vector. Fixed in `59286f3`.

### What we built
In `projects/hb_product_center/services/uc_query_service.py`:

- `_validate_column(name)` — regex allowlist (`^[A-Za-z_][A-Za-z0-9_]*$`) enforced before any column name is interpolated.
- `_escape_like(value)` — escapes `'`, `%`, `_`, `\` and adds `ESCAPE '\\'` to the LIKE.
- `_escape_value(value)` — escapes single quotes and disallows null bytes.
- `search_like(ws, table, columns, query, limit, offset)` — the safe entry point for text search.
- `select_all(ws, table, filters={...}, order_by_column=..., ...)` — `filters` is a dict keyed by column name; values escape through `_escape_value()`.

### Known regression risks
Always prefer the `filters=` form. The deprecated `where_raw` / `order_by_raw` params **were removed** in B2 (`2678cb9`) — the public signature no longer accepts raw-SQL kwargs, which eliminates the injection vector by construction. The payload-based regression suite (`tests/projects/hb_product_center/test_uc_query_security.py`) catches any reintroduction.

### Takeaway
Without bind-param support, every SQL string you build must go through an allowlist validator + escaper. Never interpolate user input — not even "numeric" input — without the `filters`/`search_like` helpers. Add a regression test for every escape rule.

---

## 10. Lakebase Autoscaling: OAuth Tokens Expire Every Hour

### Problem
After switching from Lakebase Provisioned to Autoscaling (`5152f79`), long-running apps started failing with auth errors ~60 minutes after startup. The provisioned flavor accepted a static PAT; the autoscaling flavor requires rotating OAuth credentials.

### Solution
In `backend/runtime.py`, install a SQLAlchemy `do_connect` event hook that calls `ws.postgres.generate_database_credential(endpoint=...)` *each time a new DB connection is opened*. The token is injected as the Postgres password; the engine pool recycles connections before tokens expire.

```python
@event.listens_for(engine, "do_connect")
def _before_connect(dialect, conn_rec, cargs, cparams):
    credential = ws.postgres.generate_database_credential(endpoint=endpoint_name)
    cparams["password"] = credential.token
```

Also: an explicit `session.commit()` at the end of the master seed was needed — without it, the seeded projects weren't persisted on cold start.

### Takeaway
For Lakebase Autoscaling: set `pool_recycle` short enough that the engine reopens connections before the 1h token expiry, use `do_connect` to inject a fresh token, and write an integration test that verifies `generate_database_credential` returns a token. Don't assume a seed "worked" until you've done a `session.commit()`.

---

## 11. Agent Bricks REST API: Paths Differ by Workspace Version

### Problem
Deploying agents to `fevm-felix-demo` (April 2026): the paths in our old `migrate_full.py` (`/api/2.0/agent-bricks/agents`, `/api/2.0/agent-bricks/knowledge-assistants`) all returned `ENDPOINT_NOT_FOUND`, even though the Agent Bricks UI at `/ml/agents` loaded fine.

### What we found

| Resource | Old (deprecated) path | Current path on newer workspaces |
|----------|-----------------------|----------------------------------|
| Knowledge Assistants | `/api/2.0/agent-bricks/knowledge-assistants` | `/api/2.1/knowledge-assistants` |
| Multi-Agent Supervisors | `/api/2.0/multi-agent-supervisors` | `/api/2.1/supervisor-agents` |
| Genie spaces | `/api/2.0/genie/spaces` | `/api/2.0/data-rooms/` (create) / `/api/2.0/genie/spaces` (query) |

Also: the public `POST /api/2.0/genie/spaces` now **requires** a full `serialized_space` payload. For programmatic create-from-scratch, use `POST /api/2.0/data-rooms/` with `{display_name, warehouse_id, table_identifiers, run_as_type}`, then add sample questions via `/api/2.0/data-rooms/{id}/curated-questions/batch-actions`.

MAS body must be flat (not nested under `supervisor_agent`). Per-agent config uses `agent_type` (`genie` / `serving_endpoint` / `unity_catalog_function`) with a typed sub-object. The GET response does **not** echo the `agents` field — don't rely on read-after-write to confirm config. Invoke the endpoint to verify routing.

Authoritative paths are in `~/.ai-dev-kit/repo/databricks-tools-core/databricks_tools_core/agent_bricks/manager.py` — consult this rather than guessing.

### Takeaway
Databricks REST API paths evolve. When an API returns `ENDPOINT_NOT_FOUND`, don't try random paths; grep the `databricks-tools-core` source on disk for the real routes. Always verify agent routing by invoking the MAS endpoint with a domain-specific question, not by trusting the GET response.

---

## 12. Shared Streaming + Error Handling for Chat Endpoints

### Problem
Four out of five projects had their own copies of SSE streaming, error handling, and `assert` statements for validation. Errors during a chat stream either disconnected the client or yielded opaque JSON blobs. Fixed in `a960d14` by extracting `backend/services/streaming.py` with `create_chat_stream()`.

### Rules that stuck
- **Never `assert` in request-handling code.** Release builds strip asserts. Use `HTTPException` or explicit `RuntimeError`.
- Every streaming endpoint wraps its generator in a try/except that emits an SSE `event: error` before closing — don't let the stream die silently.
- Use `create_chat_stream(generator, on_complete=persist_messages)` rather than inline `async def event_generator`.

### Normalization (D1, `83bd585`)
All five projects now stream the same way:
- Plain-text chunks (no JSON envelope) + `[DONE]` sentinel.
- Every router uses `create_chat_stream(generator, on_complete=persist)` — no inline `event_generator`.
- Every chat router uses `SessionDep` (not `Annotated[Session, Depends(get_session)]`).
- `tests/common/test_streaming_protocol.py` has a grep-based regression that catches `yield json.dumps({"content": <var>, ...})` reintroductions.

### Takeaway
When you see four copies of a pattern, extract. When a generator can raise, wrap it. When the wrapper is in place, write a grep-based regression test so the next contributor can't accidentally re-open-code it.

---

## 13. Response Model + Operation ID Discipline

### Problem
The OpenAPI → TypeScript client generator silently omits endpoints that lack either `response_model` or `operation_id`. Once, a whole router stopped appearing in the frontend API client with no error — we only noticed when a route 404'd in the UI.

### Rules
- Every `@router.get/post/patch/delete` gets both `response_model=...` and `operation_id="camelCaseName"`.
- Project-specific enums are prefixed (`MacAlertSeverity`, not `AlertSeverity`) to avoid OpenAPI schema collisions.
- I/O schemas follow the 3-model pattern: `Entity` (SQLModel), `EntityIn` (input), `EntityOut` (output) — the output is what `response_model` points at.

### Takeaway
Missing `response_model` or `operation_id` is a silent bug. Consider a pre-commit hook that scans router files for `@router.(get|post|patch|delete)` without both.

---

## 14. Cold-Start Cost: `torch` Is Expensive — Make It Optional

### Problem
`torch>=2.0.0` and `open-clip-torch` live in the top-level `pyproject.toml`. These are ~900MB of wheels, slow `uv pip install`, slow CI, slow cold-start. Only HB Product Center's CLIP recognition uses them.

### Shipped (C4, `fe7a9b3`)
torch + open-clip-torch moved to `[project.optional-dependencies.image-recognition]`. HB services lazy-import and raise `RuntimeError("image-recognition extras not installed")` when the extra is absent. The deploy bundle stays unchanged because `apx build` rewrites `.build/requirements.txt` to append `[image-recognition]` to the wheel reference — prod always installs with the extra, local dev-loops don't have to.

### CI implication
`.github/workflows/ci.yml` (D6, `8aa2e7b`) runs a matrix with and without the extra so both paths are protected: `base` (torch-free, asserts lazy-import error path) and `image-recognition` (torch installed, asserts CLIP module loads).

### Takeaway
Whenever a single project needs a heavy dependency, isolate it behind an extras group. Keep prod unchanged by rewriting the build-time requirements file rather than the public dep list. Add a CI matrix job for the extras-free path so the lazy-import error surface is tested.

---

## 15. Build Artifacts and Committed Dist Files

### Problem
Early commits bundled `src/innovation_factory/__dist__/` (compiled JS) into git. When the build output changed, we got meaningless diffs on every PR. When two branches built concurrently, merge conflicts in `__dist__/assets/index-*.js` (unreadable). The current git status even shows four `__dist__/assets/*.js` files marked for deletion.

### Direction
Only `.build/` should end up in the deploy bundle. `__dist__/` should be `.gitignore`d (and the committed artifacts deleted from git). Same applies to `.playwright-auth-state/` (we have 915 tracked files in there) and `test-*-output/` directories.

### Takeaway
If a file is regenerated by a build, do not commit it. Ever. Use `.gitignore` liberally; add a `.gitattributes` marker `*.gen.ts linguist-generated=true` so review tools collapse them.

---

## 16. Top-Level Debug/Test JS Scripts: Keep Them Out of Main

### Problem
The repo root currently has 17 `test-*.js` / `browser-*.js` / `debug-*.js` / `screenshot-*.js` Playwright ad-hoc scripts plus 7 `*-output/` directories — 971 tracked files and ~33MB of PNG/JSON. These were built during debugging and never cleaned up.

### Direction
- If a script is worth keeping, move it to `scripts/dev/` or wire it as a proper Playwright spec under `tests/e2e/`.
- If not (which is most of them), delete it.
- Add `.gitignore` rules for `*-output/`, `.playwright-auth-state/`, `.playwright-browsers/`, and `debug-*/`.

### Takeaway
Debug scripts live for one debugging session. Either promote them to a tested artifact or delete them the same week you wrote them.

---

## 17. Merging "Done" Bundles Safely

### Observation
The repo's recent history has several ~6-file merge commits that mix unrelated concerns ("new endpoint, chat fixes"). When something broke post-merge, we couldn't bisect cleanly.

### Rule of thumb
One concern per commit, one concern per PR (with exceptions for repo-wide mechanical renames like enum prefixes in `f088a5b`). If you're tempted to write "and" in a commit message, split.

### Takeaway
Branch-and-bundle-everything workflows work until they don't. Favor small, reviewable PRs; use the refinement plan's P0/P1/P2 buckets to decide what ships together.

---

## 18. "Not Configured" Is a First-Class State

### Problem
Early versions of the dashboard/Genie embeds rendered blank iframes when a workspace didn't have the resource ID set, making it look like the app was broken.

### Solution (from `6381848`)
Every embedded-resource endpoint returns a `configured: bool` field. The UI shows a "not configured for this workspace" panel instead of a silent blank. `_resolve_workspace_url()` derives the workspace URL from the runtime when the env var is empty.

### Takeaway
Multi-workspace apps should assume every resource ID might be unset. Return a `configured` boolean and render intent-revealing UI for the unconfigured path.

---

## 19. Cross-project lessons (from civion-safe, where they apply)

Lessons from a parallel project (Go API + Next.js + Neon + mobile) that transfer to innovation-factory despite the stack difference. Kept tight — only the ones that genuinely change how we'd build here.

### 19.1 Sanitize user text at the API boundary, not just at render
Server-side HTML stripping on every user-provided text field (`display_name`, `content`, `search`, free-text chat bodies). React escaping and `rehype-sanitize` close the XSS hole at render time, but a belt-and-suspenders regex `<[^>]+>` strip in the Pydantic validator protects every downstream consumer — database dumps, logs, exports, future clients. **Apply to:** every `*In` Pydantic model with a `str` field that isn't an enum-like slug/UUID.

### 19.2 Test data must use RFC 2606 domains and obviously-fake names
Real-looking names and emails in seed data (`felix.mutzl@databricks.com`, realistic customer names) can be mistaken for production data in screenshots, demos, and shared sessions. Use `@example.test`, `@example.com`, `@example.org` for emails, and names like `Test Customer A` / `Sample Advertiser`. **Apply to:** every `seed.py` and `scripts/seed_*.py` — audit before next demo.

### 19.3 Idempotent upsert + non-idempotent side effect = retry bug waiting to happen
If a handler does a UPSERT (idempotent) AND a side effect (insert-only row, notification, credit — non-idempotent), the client can retry and double-charge the side effect. Fix: read the current state before the side effect, short-circuit if already applied. **Apply to:** any chat / agent endpoint that persists history AND triggers a Databricks billable call. Today none of our endpoints charge credits, but the `ideas` session flow does persist messages AND calls the MAS — a retry would duplicate history without duplicating billing. Add the pre-check when we add idempotency keys.

### 19.4 TODO.md drift — update status in the same commit as the fix
The civion team found 17 items listed as "Planned" that were already shipped because nobody updated the tracker in the same commit. We have the same risk in `docs/TODO.md`. **Rule:** status changes go in the commit that closes the item.

### 19.5 Regression test for every P0/P1 fix
No fix is "done" without an automated test. This bites us today because none of our five accelerators has a regression test for the SQL injection fix or the MAS endpoint path changes we debugged at length. **Rule:** a bug fix PR without a test description is not mergeable.

### 19.6 Build-time vs runtime env vars
Next.js inlines `NEXT_PUBLIC_*` at build time. We have the same pattern in Vite: `__APP_NAME__` and any `import.meta.env.VITE_*` constants are frozen at `apx build` time — setting them on the running app has no effect. We already hit this once (the "Fix `__APP_NAME__` Vite constant in production JS bundle" change in `6381848`). **Rule:** anything the frontend needs at runtime comes over an API endpoint, not from `import.meta.env`.

### 19.7 API response shape consistency across clients
The civion team had a `"completed"` vs `"complete"` enum mismatch between web and iOS that was silently masked by a transform in the web hook. Only iOS broke. **Rule:** the auto-generated TypeScript client is our canonical shape. Don't hand-write transforms that paper over API shape differences — fix the API.

### 19.8 Handler SQL must match the migration that actually ran in production
A handler in civion was written against migration `000020` while production had migration `000003` with a different schema. We have the equivalent risk with UC table schemas defined in `migrate_full.py` / `deploy_to_workspace.py` / `scripts/seed_*` — each defines its own DDL, and drift is possible. **Rule:** one source of truth for each UC table's DDL, referenced by all seeders.

### 19.9 Rate-limit sizing based on realistic user behavior, not fear
Civion started at 5/hour for register and forgot-password and hit false positives immediately (typos, retries, password visibility toggles). They ended up at 15/hr and 10/hr. **Rule for our chat endpoints:** size the limit to a demo-user-clicking-around pace (~30-60/min for chat, ~10/min for recognition), not to theoretical maxima. And plan the test-bypass story upfront (see 19.10).

### 19.10 Rate limiters and E2E tests conflict — plan the test bypass upfront
Every test that hammers a rate-limited endpoint gets 429. Solutions: higher limits in test env, a test-only header that bypasses the limiter, or per-run unique identities. **Rule:** decide the bypass strategy when you add the limiter, not after the first flaky CI run.

### 19.11 Content-Type must be set explicitly on non-200 JSON responses
Civion's rate limiter returned JSON bodies with `Content-Type: text/plain` because `http.Error()` overrides the header. FastAPI's `HTTPException` handles this correctly, but any custom middleware that builds a `Response(content=...)` must set `media_type="application/json"` explicitly. **Apply to:** any future middleware we add for rate limiting, auth failures, or error envelopes.

### 19.12 WebSocket / SSE quota must be checked per-message, not per-connection
If we rate-limit chat only on connect, a user opens one SSE stream and spams it for the whole session. The limiter must fire per user message, not per handshake. **Apply to:** our SSE chat routers in workstream 8.

### 19.13 Partial unique indexes for singleton rows
If we ever add a global-config row (one row with `tenant_id IS NULL`), a regular `UNIQUE(tenant_id)` constraint won't enforce singleton because `NULL != NULL`. Use `CREATE UNIQUE INDEX ... ON config ((true)) WHERE tenant_id IS NULL`. Currently we don't have this case — remember when we do.

### 19.14 Backup/restore procedure must be tested before you need it
Civion built a backup script + runbook before the first customer onboarding. We have Lakebase Autoscaling (managed, auto-backup) and Postgres-level `pg_dump` for disaster recovery, but no documented restore runbook. **Apply:** write a short `docs/runbooks/lakebase-restore.md` that covers (a) Lakebase PITR via the Databricks UI, (b) `pg_dump` export of the innovation-factory DB, (c) a test restore into a branch. Do this before the app carries anything demo-critical.

### 19.15 Docker/package supply chain — pin versions with digests in production paths
Civion got bitten by the LiteLLM PyPI compromise (CVE-2026-33634) because they used `latest`. We don't ship Docker, but we do declare `torch>=2.0.0`, `databricks-sdk>=0.74.0`, etc. in `pyproject.toml`. **Apply:** for production deploys, pin to exact versions and rely on `uv.lock` for reproducibility. Audit once per quarter — a minor-version bump can pull a compromised release.

### 19.16 Accessibility: 16px on inputs, 44×44 touch targets
iOS Safari auto-zooms on focus if input text is <16px. WCAG 2.5.5 requires interactive elements to be at least 44×44 CSS px. Our shadcn/ui defaults are good but custom CSS may break this. **Apply to:** any custom chat input / recognition form / dashboard filter; add an ESLint rule if we grow.

### 19.17 Persona-based UAT finds bugs E2E tests miss
Civion ran 8 conditioned UAT personas (elderly, adversarial, Arabic-RTL, screen-reader, admin, Turkish, etc.) as Claude Code agents. Each persona's conditioning surfaces orthogonal bug classes — accessibility, security, i18n, RBAC. **Apply:** for each accelerator, two personas before the next demo — a "power user poking buttons fast" and an "adversarial security-curious user". Run them as Claude Code + MCP browser sessions.

### 19.18 GitHub Actions OAuth needs `workflow` scope to push workflow files
When we add CI (workstream 11), pushing the first `.github/workflows/*.yml` file requires the token to carry the `workflow` scope. `gh auth refresh -s workflow` solves it; the first-push failure is otherwise confusing.

---

## 20. Belt-and-suspenders XSS: SafeMarkdown + API-boundary sanitization

### Problem
LLM responses render via `react-markdown`. Without `rehype-sanitize`, an assistant-generated `<img src=x onerror=...>` executes. Backend validators also used to accept raw HTML in chat/search/notes fields, which meant DB dumps, logs, and any non-React client inherited the hole.

### Solution (B1 `9d4ba1e` + B3+B4 `7a9487e`)
Two independent layers:

1. **Frontend** — a single `<SafeMarkdown>` wrapper (`ui/components/safe-markdown.tsx`) that pins `rehypePlugins={[rehypeSanitize, ...]}` and exports a typed `PluggableList | undefined` for extension. Every `<ReactMarkdown>` call in the app was migrated to this wrapper.
2. **Backend** — a reusable `sanitize_text` Pydantic `BeforeValidator` (`backend/validation.py`) applied to every free-text field of every `*In` model. Strips `<…>`, null bytes, control chars, and enforces a max length.

### Test design that stuck
- **Unit**: `tests/common/test_input_sanitize.py` parameterizes dozens of payloads (`<script>`, `<img onerror=>`, null bytes, CRLF, oversized inputs).
- **Contract**: a grep-based test rejects any new `<ReactMarkdown` usage outside `SafeMarkdown`.

### Takeaway
Sanitize at both ends and pick the narrowest reusable wrapper. A regression test that greps for the unsafe pattern is often cheaper than a runtime test and harder to silently bypass.

---

## 21. Rate-limit keying on Databricks Apps: `X-Forwarded-User`, not IP

### Problem
`slowapi`'s default `get_remote_address` reads `X-Forwarded-For` / socket IP. On Databricks Apps all traffic arrives from the auth proxy, so IP-keyed limits collapse to one global quota — the first user to hit an endpoint burns everyone's budget.

### Solution (C2 `1b4b105`)
```python
def rate_limit_key(request: Request) -> str:
    user = request.headers.get("X-Forwarded-User")
    if user:
        return f"user:{user}"
    return f"ip:{get_remote_address(request)}"  # local dev fallback
```

Applied per-endpoint (e.g. `@limiter.limit("10/minute")` on `/identify`, `"60/minute"` on chat). Tests set `X-Forwarded-User` explicitly to simulate distinct users and confirm per-user quotas.

### Takeaway
Proxy-fronted apps need identity-based rate-limit keys. If you're about to put `get_remote_address` behind a proxy, stop and reach for the auth header the proxy is already giving you.

---

## 22. Shared `Pagination` dependency over ad-hoc `Query` params

### Problem
Every list endpoint re-declared `limit: int = Query(50, le=200)` + `offset: int = Query(0)`. Inconsistent bounds (some had no `le=`, some used `skip` vs `offset`), and the OpenAPI client emitted a different param shape per route.

### Solution (C3 `0f220ad` + D7 `aa06890`)
`backend/pagination.py` exports a single `Pagination = Annotated[PageParams, Depends(...)]`. Every `GET /list-*` endpoint takes `page: Pagination` and uses `page.limit` / `page.skip`. The dependency caps `limit ≤ 200` centrally.

### Gotcha: default vs non-default ordering
Python rejects `page: Pagination` (no default) after a `Query(None)` default. Put `page` **before** any default-valued params, or Python will refuse to import.

### Takeaway
Shared FastAPI dependencies beat parameter-copy-paste. When migrating, fix the param order once and add the import; a grep regression catches new `limit: int = Query(` additions.

---

## 23. Canonical UC DDL: one `TABLES` dict, many consumers

### Problem
The DDL for each UC table lived in `migrate_full.py`, `deploy_to_workspace.py`, `deploy_agents_fevm.py`, and `scripts/seed_*.py`. Drift was real — some scripts had `product_id INT`, others `BIGINT`; `last_audit_date` was `DATE` in one and `TIMESTAMP` in another. Seeding into a fresh workspace produced schema-mismatched rows.

### Solution (D2 `aefcf6f`)
`scripts/uc_schema.py` is the single source of truth:

```python
TABLES: dict[str, dict] = {
    "hb_product_center.hb_products": {
        "columns": [("id", "BIGINT GENERATED ALWAYS AS IDENTITY"), ...],
        "comment": "Products curated for the HB demo.",
    },
    ...
}

def create_table_sql(catalog: str, schema_table: str) -> str: ...
def tables_for_schema(schema: str) -> list[str]: ...
```

Every deployer/seeder imports `uc_schema` and calls these helpers. The 11-test coverage in `tests/scripts/test_uc_schema.py` locks down column-name safety (regex), identifier column presence, and SQL shape.

### Takeaway
If three scripts each have "their own" DDL, you have two copies of a bug waiting to happen. Extract, add schema tests, and forbid inline DDL via code review.

---

## 24. MAS sub-agent naming: snake_case machine name + "Supervisor" suffix

### Problem
Our first MAS configs mixed sub-agent naming styles — `genie_data_explorer`, `transfer_to_issue_resolution_specialist`, `query_agent`, `call_agent_tool`, `product_identifier_agent`, `query_agent_quality_auth_analyst`. The Agent Bricks UI shows the raw names, so the dashboard looked inconsistent and the LLM's routing was non-deterministic (same capability referenced multiple ways in `instructions`).

### Solution (D3 `5ab16f6`)
Contract now enforced by `tests/scripts/test_mas_naming_convention.py`:

1. Every sub-agent `name` is `^[a-z][a-z0-9_]*$` (snake_case, no prefixes like `transfer_to_` or `_agent`).
2. Every MAS `display_name` ends with `"Supervisor"` (e.g. "AdTech Intelligence Supervisor", "HB Product Center Supervisor").
3. The `instructions` string references every sub-agent by its exact machine name — the test parses each MAS block and fails if a sub-agent name isn't in the instructions it's supposed to be routed by.
4. Phase 7 in `deploy_agents_fevm.py` is stamped with `PHASE_7_VERSION` in `fevm_agents_state.json` + delete-and-recreate (not PATCH) because the Agent Bricks PATCH doesn't update the `agents` array reliably.

### Takeaway
When an LLM does tool-call routing from a string, the string is an API — enforce its shape with tests. For Agent Bricks, prefer delete-and-recreate for sub-agent changes; PATCH-with-update_mask is underspecified on the `agents` array today.

---

## 25. Hybrid migration: DAB for declarative, Python for imperative

### Problem
We kept reinventing the "bootstrap a fresh workspace" story. Databricks Asset Bundles (DAB) handle apps, jobs, warehouses, and (now) some resources declaratively, but don't cover Agent Bricks KAs, MASes, Genie spaces, UC function `identify_product`, KA-doc volume uploads, or the AI/BI embedding allowlist. Terraform was considered and rejected (agent-bricks provider lags).

### Solution (D4 `15a3730`)
Hybrid split documented and automated:

| Layer | Tool | What it creates |
|-------|------|-----------------|
| Declarative | `databricks.yml` + `databricks bundle deploy` | App, Lakebase instance, warehouse binding, DAB resources |
| Imperative (one-off) | `scripts/bootstrap.py --target <profile>` | UC schemas/volumes, KA docs, Agent Bricks KAs/MASes, Genie spaces, dashboard migration (optional), embedding allowlist |
| Declarative (second pass) | `databricks bundle deploy` again | App re-deploys with env vars filled from the state file |

`bootstrap.py` runs phases 1-9 of `deploy_agents_fevm.py` in order, configures the AI/BI embedding allowlist (unblocks iframe dashboards — `aws.databricksapps.com` + `databricksapps.com` must be on it), then prints the env-var block to paste back into `databricks.yml`. Idempotent via `scripts/fevm_agents_state.json`.

### Takeaway
When the declarative tool doesn't cover everything, the hybrid is fine — but write the orchestrator that stitches the two halves together so "fresh workspace in 20 minutes" is true, not aspirational. Make the orchestrator idempotent and its state file gitignored.

---

## 26. CI matrix: Python 3.11 + 3.12, with and without heavy extras

### Problem
A single CI job on one Python version missed: (a) 3.12-only syntax issues, (b) the `image-recognition`-extra-absent lazy-import path, (c) the extra-present import path.

### Solution (D6 `8aa2e7b`)
`.github/workflows/ci.yml` now:
- `lint` job — `ty` + `tsc`, single runner.
- `tests` matrix — `{ python: [3.11, 3.12] } × { extras: [base] }` plus `{ python: 3.11, extras: image-recognition }`. The matrix catches both the "does the lazy-import RuntimeError fire" and the "does CLIP load when available" paths.
- `build` — `uv run apx build` on 3.11 only (prod target).
- `integration` — gated on `workflow_dispatch` + `environment: integration` so Databricks secrets aren't leaked to forks.

### Takeaway
Matrix breadth matters more than matrix size. One axis (Python version) catches syntax/grammar drift; one axis (extras present/absent) catches packaging drift. A third axis is rarely worth the CI minutes.

---

## 27. Server-side `INSERT … SELECT FROM range(N)` for high-volume seeding (AECO Hub)

### Problem
AECO Hub Phase 3 needed ~500K synthetic IoT sensor readings in `aeco_hub.dt_sensor_readings`. Streaming 500K rows of `INSERT VALUES` literals over the SQL API would take many minutes.

### Solution
Generate rows server-side with `range(N)` and `rand()`/`sin()` for shape:

```sql
INSERT INTO ...dt_sensor_readings (sensor_code, sensor_type, ...)
SELECT
    CONCAT('S-', ...),
    'zone_temp',
    ...
    {mid} + {amplitude} * sin(id / 24.0) +
        ({amplitude * 0.2}) * (rand({seed}) - 0.5) AS value,
    'C'
FROM range({rows_per_building})
```

The warehouse runs row generation; the Python client only sends a handful of statements. 499,992 rows landed in under 2 minutes on a 2X-Small warehouse.

### Takeaway
Use server-side `range()` generation any time you need >10K rows of synthetic data into UC. See `scripts/seed_uc_aeco_data.py::_sensor_readings_insert` for the canonical example.

---

## 28. Catalog-parameterize seed scripts so they work across workspaces (AECO Hub)

### Problem
Pre-AECO seed scripts (HB Product Center) hard-coded the catalog name and only worked in one workspace. Switching workspaces meant editing source.

### Solution
Every seed function takes `catalog` as the first argument. `scripts/seed_uc_aeco_data.py::build_sql(catalog=...)` accepts the catalog; `deploy_agents_fevm.py` passes `felix_demo_catalog` for fevm-felix-demo; a standalone run defaults to `innovation_factory_catalog`.

### Takeaway
**Pattern**: every seed/DDL function takes `catalog` as the first argument and uses it in every fully-qualified table reference. No hardcoded `innovation_factory_catalog` outside the default-value assignment.

---

## 29. PGlite + psycopg + NullPool = `DuplicatePreparedStatement` (AECO Hub)

### Problem
`apx dev start` failed with `psycopg.errors.DuplicatePreparedStatement: prepared statement "_pg3_0" already exists` during seed. Root cause: psycopg auto-prepares statements after a few executions and names them `_pg3_<n>` per connection; PGlite leaks prepared-statement state across connection resets while NullPool creates a fresh connection per operation.

### Solution
In `runtime.py`:

```python
if self._is_local_dev:
    engine = create_engine(
        self.engine_url,
        poolclass=NullPool,
        connect_args={"prepare_threshold": None},  # disable for PGlite
    )
```

`prepare_threshold=None` makes psycopg execute statements unprepared. Slower in theory, irrelevant for seed workloads.

### Takeaway
PGlite's connection-reset behavior breaks psycopg's auto-prepare. Set `prepare_threshold=None` in `connect_args` whenever NullPool + PGlite are combined.

---

## 30. Lakeview `serialized_dashboard` live shape ≠ checked-in JSON shape (AECO Hub)

### Problem
Phase 9 in `deploy_agents_fevm.py` migrates dashboards by fetching `serialized_dashboard` from a source workspace and POSTing to target. The shape returned by `GET /api/2.0/lakeview/dashboards/{id}` differs from the older `datasets/pages/widgets` JSON layout that some checked-in files (`dashboard_aq.json`) still use.

### Live shape (use this for new dashboards)
- `datasets`: `[{name, displayName, queryLines: [string]}]` — `queryLines` is an array of SQL strings, not a single `query.sql`
- `pages`: `[{name, displayName, pageType, layout: [...]}]` — pages have `layout`, not `widgets`
- Each `layout` entry: `{widget: {name, queries: [...], spec: {widgetType, ...}}, position: {x, y, width, height}}`

### Takeaway
When authoring new dashboards from scratch, use the live API shape (`queryLines` + `layout`). The legacy checked-in files worked as input to the migration phase, not as templates for fresh creation.

---

## 31. MAS sub-agent block ordering in `deploy_agents_fevm.py` (AECO Hub)

### Problem
Phase 7 of `deploy_agents_fevm.py` builds multiple MAS supervisor configs. The regex parser in `tests/scripts/test_mas_naming_convention.py` scans for `var = []` then the next `_api("post", "/api/2.1/supervisor-agents")` — inserting a new MAS block BETWEEN two existing ones leaks the wrong `instructions` block into the wrong test case and breaks the naming-convention regression.

### Rule
Place new MAS blocks AFTER all previously-defined `_agents = []` blocks in `deploy_agents_fevm.py`, not between them. Supervisor name itself ends in `_supervisor` (`aeco_hub_supervisor`); sub-agents stay snake_case (`project_analytics`, `operations_intelligence`, `standards_compliance`); the `instructions` string MUST reference each sub-agent's machine name in backticks.

### Takeaway
When a regression test parses source by structural position, insertion order matters. Append, don't interleave. The naming convention rule itself is enforced by `tests/scripts/test_mas_naming_convention.py`.

---

## 32. Agent-autonomy testing pipeline for accelerator handoff (`fb43b87`)

### Problem
Handing off a new accelerator to an autonomous coding agent (or a colleague) lacks objective signals about whether the build actually works end-to-end. `apx dev check` (type-check) + `pytest` (unit tests) pass cleanly while the deployed app silently 401s because the service principal lacks `CREATE` on the Lakebase database, or the embedding allowlist doesn't include the workspace, or env vars in `databricks.yml` drifted from the state file.

### Solution
`scripts/check_all.sh` — a 5-stage pipeline that bundles every objective signal we have, run sequentially with fail-fast semantics:

```
1. drift-check  — sync_env_from_state.py --check   # databricks.yml vs fevm_agents_state.json
2. type-check   — apx dev check                    # tsc + ty
3. unit tests   — pytest --ignore=tests/integration
4. preflight    — preflight.py                     # Databricks profile + SP perms + embedding allowlist
5. smoke        — smoke.py against the deployed app
```

Each stage exits non-zero on failure so the script halts at the first broken signal. The preflight stage is the one most often missing — type-check + tests can't see deployment-time auth/allowlist problems.

### Takeaway
Every new accelerator should pass `check_all.sh` before being declared "done." When you build the equivalent for a new repo, copy the structure (especially the preflight stage — its existence is half the value). The agent-autonomy framework also doubles as a CI matrix entry for end-to-end verification when run against a staging environment.

---

## 33. CI cold-cache strategy for apx-bundled monorepos

### Problem
A cluster of 5 separate CI-debug commits in April 2026 (`af422a3`, `8de4587`, `9ee6cd4`, `61cc0ca`, `3505747`, `0822e86`) each fixed a distinct CI gotcha for an apx-bundled FastAPI + React project on a public GitHub runner. None of them were obvious in advance; each cost a CI cycle to discover.

### Gotchas + fixes (the canonical bundle)

| Gotcha | Symptom | Fix |
|---|---|---|
| `bun.lock` references internal `npm-proxy.dev.databricks.com` | `bun install` hangs / times out on public runners | sed-rewrite to `registry.npmjs.org` as the first CI step |
| `apx dev check` cold cost | ~5-7 min for bun install + tsc | Add `actions/cache@v4` on `node_modules`; bump lint job timeout to 25 min |
| `apx`-generated files not present in CI checkout | Tests fail importing `_metadata.py` / `_version.py` / `__dist__/index.html` | Explicit stub block in the test job that writes the known-static values |
| Contract tests assume Databricks env vars | Test asserting "returns populated value" fails on CI | Stub `DATABRICKS_HOST` + relevant `ADTECH_*` IDs in the test job env |
| `try: import torch except ImportError` + stale `# type: ignore` | `ty` flags unused type-ignore after the dep moves to optional | Use `importlib.util.find_spec("torch")` for presence checks; drop the type-ignore comment |
| Lint job needs to see optional extras | `ty` errors on CLIP-using files when extras aren't installed | Include `--extra image-recognition` in the lint job sync, not just the dedicated test row |

### Takeaway
Public-runner CI for apx projects needs both extras-matrix breadth (§26) AND apx-artifact stubbing — neither alone is sufficient. When you stand up CI for the next project, copy this whole table on day one; each row already cost a debug cycle here, you don't need to repay it.

---

## 34. Incremental lint adoption via `KNOWN_DEBT` allowlist

### Problem
When promoting a previously-aspirational convention (e.g. "every route has `response_model` + `operation_id`") to a hard CI lint, the codebase has accumulated violations. Hard-breaking on day one is unacceptable; deferring the lint indefinitely is worse.

### Solution
Land the lint with an explicit `KNOWN_DEBT: set[tuple[str, str]]` allowlist of pre-existing offenders. The lint:

1. **Catches new violations** on every PR (the actual goal of the lint).
2. **Preserves existing ones** by skipping anything in `KNOWN_DEBT`.
3. **Fails when a `KNOWN_DEBT` entry is no longer in violation** — this forces the allowlist to stay accurate. Someone fixes a route, removes their entry from the set, and lands one less line of debt.

```python
# tests/common/test_router_discipline.py (excerpt)
KNOWN_DEBT: set[tuple[str, str]] = {
    ("src/path/to/file.py", "function_name"),
    ...
}

def test_contract():
    all_violations = _collect_violations()
    new_violations = [v for v in all_violations if (v.path, v.fn) not in KNOWN_DEBT]
    cleared = [e for e in KNOWN_DEBT if not any(matches(e, v) for v in all_violations)]
    if cleared:
        pytest.fail("Remove these from KNOWN_DEBT — they no longer violate: ...")
    if new_violations:
        pytest.fail("New violation(s): ...")
```

### Schedule
Clear debt entries in a dedicated quarterly revision pass. Don't chip away ad-hoc — batch the cleanup so the diff tells one story.

### Example
`tests/common/test_router_discipline.py` shipped 2026-05-11 with 10 allowlisted routes for the §13 contract (`response_model` + `operation_id`). The 2026-Q2 revision pass cleared all 10 entries — 5 SSE routes migrated to `@streaming_endpoint`, 5 routes typed via `response_model=dict[...]`. Allowlist is now empty; next violation fails CI immediately.

### Takeaway
Use this pattern for any new convention check that would otherwise produce a wall of failures. Floor goes up incrementally; never break the ceiling. The bi-directional check (catch new AND prune stale) is what makes the allowlist self-maintaining.

---

## Summary

| # | Topic | One-line lesson |
|---|-------|-----------------|
| 1 | Lakeview API | `query` is a plain SQL string; `spec` is a top-level widget attribute |
| 2 | MAS endpoints | Use `input`/`output` via `ws.api_client.do()` — not `messages`/`choices` |
| 3 | PGlite limits | Local seed < 10K rows; full data seeds via PySpark |
| 4 | `ty` + SQLModel | Ignore specific rules by name, re-audit after upgrades |
| 5 | Env-var config | All resource IDs via `databricks_config.py`, default empty, document in `.env.example` |
| 6 | Project layout | Project artifacts live inside the project folder |
| 7 | Route generation | Never hand-edit auto-generated files; regenerate on conflicts |
| 8 | Merge conflicts | Additive conflicts in router.py / seed.py — keep both, regen auto files |
| 9 | SQL injection | No bind params in UC Statement Execution — always use `filters`/`search_like`; remove `where_raw` |
| 10 | Lakebase OAuth | Rotate creds on every connection via SQLAlchemy `do_connect` |
| 11 | Agent Bricks paths | Use `/api/2.1/knowledge-assistants`, `/api/2.1/supervisor-agents`, `/api/2.0/data-rooms/` |
| 12 | Shared streaming | Use `create_chat_stream()`; never `assert` in handlers; emit SSE error events |
| 13 | API discipline | Every route needs `response_model` + `operation_id`; prefix project enums |
| 14 | Heavy deps | Torch + CLIP behind an optional extras group |
| 15 | Build artifacts | Never commit `__dist__/` or built JS; `.gitignore` rigorously |
| 16 | Debug scripts | Promote to tests or delete; don't let them rot at repo root |
| 17 | Commit hygiene | One concern per commit; split mixed commits |
| 18 | Configuration UX | Return `configured: bool`; render a useful empty-state |
| 19.1 | Input sanitization | Strip HTML server-side at API boundary, not just at render |
| 19.2 | Test data | Use `@example.test` domains and obviously-fake names in seeds |
| 19.3 | Idempotency | Upsert + side effect = retry bug; check state before the side effect |
| 19.4 | TODO tracker | Status change goes in the same commit as the fix |
| 19.5 | Regression tests | No P0/P1 fix merges without an automated regression test |
| 19.6 | Build-time vs runtime | Frontend runtime values come via API, not `import.meta.env` |
| 19.7 | API shape | Auto-gen TS client is canonical; never mask API mismatches with transforms |
| 19.8 | Schema drift | One DDL source per UC table; all seeders reference it |
| 19.9 | Rate-limit sizing | Size limits to realistic user pace, not worst-case |
| 19.10 | Limiter-test conflict | Decide the test bypass strategy when you add the limiter |
| 19.11 | Content-Type | Middleware JSON responses must set `media_type="application/json"` |
| 19.12 | Per-message quota | SSE/WebSocket limits fire per user message, not per connect |
| 19.13 | Singleton index | Partial unique index for nullable-singleton rows |
| 19.14 | Backup/restore | Write and test the Lakebase restore runbook before you need it |
| 19.15 | Supply chain | Pin exact versions; audit for known CVEs each quarter |
| 19.16 | Accessibility | 16px min on inputs; 44×44 CSS px touch targets |
| 19.17 | Persona UAT | Two conditioned personas per accelerator before each demo |
| 19.18 | GH workflow scope | `gh auth refresh -s workflow` before pushing first CI file |
| 20 | XSS defense | `SafeMarkdown` wrapper + Pydantic `sanitize_text` BeforeValidator on every free-text field |
| 21 | Rate-limit keying | Key off `X-Forwarded-User` on Databricks Apps; IP keying collapses to one global quota |
| 22 | Shared pagination | One `Pagination` dependency; put it before default-valued params in the signature |
| 23 | Canonical UC DDL | `scripts/uc_schema.py` with a `TABLES` dict; every seeder imports from it |
| 24 | MAS naming contract | snake_case sub-agent names, "Supervisor" suffix, machine names in instructions — enforced by test |
| 25 | Hybrid migration | DAB declarative + `scripts/bootstrap.py` imperative, idempotent via gitignored state file |
| 26 | CI matrix shape | Python 3.11+3.12 × extras-present/absent; integration tests opt-in via `workflow_dispatch` |
| 27 | Server-side seeding | `INSERT … SELECT FROM range(N)` for >10K-row UC seeds — warehouse does the work |
| 28 | Catalog-parameterized seeds | Every seed/DDL function takes `catalog` as first argument; no hardcoded catalog references |
| 29 | PGlite + psycopg | `prepare_threshold=None` in `connect_args` when NullPool + PGlite are combined |
| 30 | Lakeview live shape | New dashboards use `queryLines` + `layout` (live API), not `query` + `widgets` (legacy export) |
| 31 | MAS block ordering | Append new MAS blocks in `deploy_agents_fevm.py`; never interleave — regression regex parses by position |
| 32 | Agent-autonomy pipeline | 5-stage `scripts/check_all.sh` (drift → type-check → tests → preflight → smoke) — preflight catches what types and tests can't |
| 33 | CI cold-cache for apx | Public-runner CI for apx projects needs proxy rewrite + bun cache + apx-artifact stubbing + extras visibility for `ty` — bundle on day one |
| 34 | Incremental lint adoption | New convention lints land with `KNOWN_DEBT` allowlist; test catches new violations AND prunes stale entries; clear in quarterly revision |
