# Innovation Factory — Cleanup & Improvement Plan

> Built from a four-track investigation: repo hygiene, code quality, security, and test coverage.
> Status: **draft for user review — do not implement yet.**
> Author: Felix Mutzl & Claude. Date: 2026-04-23.

Priorities in this order: **operational efficiency** → **security** → **compliance with coding best practices**.
Each workstream below has scope, rationale, test design, and a rollback note. A combined sequencing recommendation is at the bottom.

---

## 0. Summary

| # | Workstream | Priority | Risk | Rough effort | Ships with tests? |
|---|------------|----------|------|--------------|-------------------|
| 1 | Repo cleanup (tracked cruft, `.gitignore`, `__dist__`) | P0 | Low | 2–3h | Smoke + CI |
| 2 | SQL injection regression + deprecated API removal | P0 | Medium | 3–4h | Yes, new security suite |
| 3 | Markdown XSS — add `rehype-sanitize` | P0 | Low | 1h | Yes, unit + E2E |
| 4 | Input length validation on chat/free-text endpoints | P1 | Low | 1h | Yes, unit |
| 5 | Extract shared chat router factory + normalize streaming | P1 | Medium | 4–6h | Yes, unit + integration |
| 6 | Consolidate `databricks_config.py` via a small helper | P1 | Low | 1–2h | Yes, unit |
| 7 | Torch → optional extras (lazy import) | P1 | Medium | 2–3h | Yes, smoke |
| 8 | Rate limiting on expensive endpoints | P2 | Low | 1–2h | Yes, unit |
| 9 | Pagination on list endpoints + page-size guards | P2 | Low | 1–2h | Yes, unit |
| 10 | Foundation test suite (the "first 10 tests") | P1 | Low | 8–10h | Is the tests |
| 11 | CI (GitHub Actions) running tests + type check | P2 | Low | 1–2h | N/A |
| 12 | Obsolete scripts / docs sweep | P2 | Low | 1h | Smoke |

Total effort for everything: ~30–40h. User picks what lands in which sprint.

---

## 1. Repo Cleanup

### Scope
Remove tracked cruft, tighten `.gitignore`, purge committed build artifacts.

### Current state (measured)
- **971 tracked files** and **~33 MB** of debug/test cruft at repo root:
  - **17 ad-hoc Playwright-style JS scripts** at root: `test-*.js`, `browser-*.js`, `debug-*.js`, `screenshot-*.js`
  - **7 output directories** with screenshots/JSON: `browser-login-flow-output/`, `debug-recognition-output/`, `deployed-hb-chat-output/`, `deployed-visual-recognition-output/`, `deployed-visual-recognition-test/`, `test-hb-chat-output/`, `test-recognition-output/`
  - **915 files under `.playwright-auth-state/`** — a full Playwright profile directory, including `Trust Tokens` and `Trust Tokens-journal`. Browser state, not source.
- **Tracked dist artifacts**: 6 files under `src/innovation_factory/__dist__/` (4 JS bundles + `index.html` + `logo.svg`). The `.gitignore` ignores `.mcp.json` inside `__dist__/` but not the dir itself.
- **Random top-level assets**: `hb-product-center-screenshot.png` (67 KB), `shot-home.png`, `file:test_shared` (2.8 MB — name has a colon; likely an accidental `git add "file:test_shared"`), `notebooks backend/` (directory with a space in the name containing a single copy-suffixed `.ipynb`).
- **Tracked browser profile bits**: `.playwright-auth-state/Default/Trust Tokens*` — could contain session state.
- **`.gitignore` gaps**: no rules for `*-output/`, `.playwright-auth-state/`, `.playwright-browsers/`, `src/innovation_factory/__dist__/` (the dir itself), root `test-*.js`, `debug-*.js`, `browser-*.js`, `screenshot-*.js`, `.tanstack/`.

### Action plan

1. **Move-or-delete the 17 root JS scripts**. Proposal:
   - Delete outright (14): one-off debug screenshots of deployed instances.
   - Promote to `tests/e2e/` (3, if still relevant): `test-home-only.js`, `test-kpi-screenshots.js`, `test-hb-product-center-chat.js` — rewrite as proper Playwright `.spec.ts`.
2. **Delete all 7 `*-output/` dirs** — never commit test screenshots.
3. **Delete `.playwright-auth-state/` from git** and add to `.gitignore`. Browser profile state is a credential artifact and should never be in source control.
4. **Untrack `src/innovation_factory/__dist__/`**. Delete its tracked assets; add to `.gitignore`. Build outputs live in `.build/` for deploys, not in source.
5. **Delete the weird files**: `file:test_shared`, `hb-product-center-screenshot.png`, `shot-home.png`, `notebooks backend/`. None are referenced in code, docs, or `package.json` scripts (verify with one grep before deleting).
6. **Expand `.gitignore`**:
   ```
   # Test / debug artifacts
   *-output/
   debug-*/
   test-results/
   test-screenshots/
   .playwright-auth-state/
   .playwright-browsers/
   .tanstack/

   # Build output
   src/innovation_factory/__dist__/

   # Root scratch
   /test-*.js
   /browser-*.js
   /debug-*.js
   /screenshot-*.js
   ```
7. **Add `.gitattributes`**:
   ```
   ui/lib/api.ts linguist-generated=true
   ui/types/routeTree.gen.ts linguist-generated=true
   *.lock linguist-generated=true
   ```

### Test design
- **Smoke**: `uv run apx build` still produces `.build/app.yml` and `.build/*.whl`.
- **Smoke**: `uv run apx dev start` brings up backend + frontend locally.
- **Smoke**: after a `git clean -fdx` to simulate a fresh checkout, `uv sync && uv run apx build && uv run apx dev start` still works.
- **CI**: the forthcoming GitHub Actions workflow (workstream 11) will prevent regressions.

### Rollback
One-shot revert is safe because this touches no runtime code. The deletions should be in their own PR so review is easy.

---

## 2. SQL Injection Regression & Deprecated Query API Removal

### Scope
Close the regression in `projects/hb_product_center/routers/products.py` where user input bypasses the allowlist, then remove the deprecated `where_raw` / `order_by_raw` paths that let this regression happen.

### Evidence
`src/innovation_factory/backend/projects/hb_product_center/routers/products.py:71-84`:

```python
if search:
    escaped = search.replace("'", "''")
    conditions.append(
        f"(LOWER(style_name) LIKE '%{escaped.lower()}%' OR LOWER(sku) LIKE '%{escaped.lower()}%')"
    )
...
rows = select_all(ws, "hb_products", where=where, ...)   # deprecated where_raw path
```

The escape only handles `'` — not the LIKE wildcards `%` and `_`. And `select_all(..., where=...)` triggers the deprecated code path at `services/uc_query_service.py:210`, which interpolates the string raw.

### Action plan
1. Replace the manual WHERE build in `products.py` with `search_like()` (for free-text) + `filters={}` (for enum-style category/collection/season/status) + validated sorts.
2. Audit all `select_all` / `count_rows` / `avg_column` / `sum_column` / `select_one` callers for `where_raw`, `where`, `order_by_raw`, `order_by` kwargs. Migrate each to `filters={}` / `order_by_column=`.
3. **Remove the deprecated params** from the public function signatures. Keep `_build_where()` internal. A warning is not enough when the footgun is in the public API.
4. Similarly audit `scripts/*.py` for raw SQL construction off user input (there should be none — scripts take no user input — but verify).
5. Document in `claude.md` that "No raw SQL interpolation" means *no where_raw either*.

### Test design (new file `tests/projects/hb_product_center/test_uc_query_security.py`)
Unit tests using a mock `WorkspaceClient` that records the SQL actually generated:

```python
@pytest.mark.parametrize("payload", [
    "'; DROP TABLE hb_products; --",
    "' OR '1'='1",
    "a%' OR '1'='1",             # wildcard-bypass regression
    "a_' UNION SELECT *",
    "\\' OR 1=1 --",
    "\x00' OR 1",                # null byte
])
def test_search_like_escapes_injection(mock_ws_recording_sql, payload):
    search_like(mock_ws_recording_sql, "hb_products", ["style_name"], payload, limit=5)
    sql = mock_ws_recording_sql.last_sql
    assert "DROP TABLE" not in sql.upper()
    assert "UNION" not in sql.upper()
    assert "OR '1'='1'" not in sql      # unescaped payload must not survive
    assert " ESCAPE '\\\\'" in sql       # our escape clause present

def test_validate_column_rejects_non_identifiers():
    for bad in ["col; DROP", "col' OR", "1col", "col-name", ""]:
        with pytest.raises(ValueError):
            _validate_column(bad)

def test_select_all_rejects_unknown_filters():
    with pytest.raises(ValueError):
        select_all(mock_ws, "hb_products", filters={"style_name; DROP": "x"})
```

Plus a regression test at the router layer — a real `TestClient` call to `GET /api/projects/hb-product-center/products?search=a%25%27 OR %271%27%3D%271` asserting the returned rows don't leak unfiltered data.

### Rollback
Low risk. If the deprecated params are still referenced somewhere we missed, the PR fails its own new tests before merge.

---

## 3. Markdown XSS — `rehype-sanitize`

### Scope
Sanitize all markdown rendered from untrusted sources (chat responses, docs viewer).

### Evidence
`src/innovation_factory/ui/components/chat/chat-interface.tsx:148-150, 230-250` renders LLM output via `<ReactMarkdown remarkPlugins={[remarkGfm]}>` with no `rehypePlugins`. `react-markdown` does not sanitize raw HTML in markdown by default. An LLM-produced `<img src=x onerror="fetch('/api/...')">` would execute.

### Action plan
1. `uv run apx bun add rehype-sanitize`
2. In every markdown render site, add `rehypePlugins={[rehypeSanitize]}`. Grep first to find them all (`ReactMarkdown` component usage across `ui/`).
3. The docs viewer endpoint (`backend/router.py:73-103`) returns raw markdown for `docs/projects/*.md` — also needs sanitization downstream. Lower risk (content is in the repo) but include it for defense-in-depth.

### Test design
- **Unit (Vitest — new)**: render `<ChatInterface messages={[{role:"assistant", content:'<img src=x onerror=alert(1)>Hi'}]}/>`. Assert no `onerror` attribute in DOM; text "Hi" still shown.
- **E2E (Playwright, `tests/e2e/test_chat_xss.spec.ts`)**: post a chat request whose mocked response includes `<script>window.__pwned=1</script>`, assert `page.evaluate(() => window.__pwned)` is undefined.

### Rollback
Purely additive; one-commit revert is safe.

---

## 4. Input Length Validation

### Scope
Every user-free-text field gets a `max_length`. Today, `HbChatMessageIn.content`, `AtChatMessageIn.content`, and similar have no length bound.

### Action plan
Add `max_length=5000` to chat message bodies, `max_length=500` to descriptions and search fields, `max_length=200` to names/titles. Enforce via Pydantic `Field(..., max_length=...)`.

### Test design
Parametrized Pydantic validation tests in `tests/common/test_input_validation.py`:

```python
@pytest.mark.parametrize("model,field,limit", [
    (HbChatMessageIn, "content", 5000),
    (AtChatMessageIn, "content", 5000),
    (ProductIdentifyRequest, "description", 500),
])
def test_field_length_enforced(model, field, limit):
    with pytest.raises(ValidationError):
        model(**{field: "x" * (limit + 1)})
```

### Rollback
Adjust the bound; revert is trivial.

---

## 5. Shared Chat Router Factory + Streaming Normalization

### Scope
Unify the five chat implementations so they share a router factory, a streaming format, and an error-handling convention.

### Evidence (from the code-quality investigation)
- `vi_home_one/routers/chat.py`: uses `SessionDep`, uses `create_chat_stream()` ✓
- `bsh_home_connect/routers/chat.py`: uses `Annotated[Session, Depends(get_session)]`; yields JSON envelopes `{"content": ..., "done": ...}` (not SSE)
- `mol_asm_cockpit/routers/chat.py`: non-streaming, synchronous response
- `adtech_intelligence/routers/chat.py`: uses `Annotated[...]` instead of `SessionDep`; uses `create_chat_stream()` ✓
- `hb_product_center/routers/chat.py`: inlines an `event_generator` rather than calling `create_chat_stream()`

Only 2/5 projects use the shared `databricks_agents.py` (mol_asm, adtech). VI and BSH have their own mock logic; HB has custom context assembly.

### Action plan
1. Add a `ChatService` protocol in `backend/services/chat_base.py` with `async def stream(query, session_id) -> AsyncIterator[str]` and `def history(session_id) -> list[MessageOut]`.
2. Add `create_chat_router(service, prefix, models)` that returns a ready-mounted `APIRouter` with standard `/chat`, `/chat/history`, `/chat/sessions` routes, all using `SessionDep` and `create_chat_stream()`.
3. Migrate the five projects one at a time. Each migration = a single PR with its own tests.
4. In `create_chat_stream()`, standardize on **plain text chunks + `event: done` sentinel** (drop the JSON envelope). Rev the UI chat client to match.
5. Replace in-service mock generators with a shared `services/mock_chat.py` that takes a per-project question/answer map (used only in local dev when no endpoint configured).

### Test design
- **Unit (`tests/common/test_streaming.py`)**: verify `create_chat_stream` emits chunks, a done event, and an error event when the generator raises.
- **Unit (`tests/common/test_databricks_agents.py`)**: `extract_agent_text()` handles (a) `choices[].message.content` (standard), (b) `output[].content[].output_text` (MAS), (c) mixed lists with `function_call` items.
- **Contract test per project (`tests/projects/<slug>/test_chat_router.py`)**: POST a chat message, assert 200, assert first chunk arrives within 2s, assert `done` sentinel arrives, assert persisted history visible via `/chat/history`.

### Rollback
Migrate one project at a time. A per-project revert is a 1-commit rollback.

---

## 6. `databricks_config.py` Consolidation

### Scope
Collapse the five near-identical `databricks_config.py` files into a single helper.

### Action plan
`backend/projects/_config.py`:
```python
class ProjectResourceConfig:
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.workspace_url = _derive_workspace_url(prefix)
        self.dashboard_id = os.getenv(f"{prefix}_DASHBOARD_ID", "")
        self.genie_space_id = os.getenv(f"{prefix}_GENIE_SPACE_ID", "")
        self.mas_endpoint = os.getenv(f"{prefix}_MAS_ENDPOINT_NAME", "")
        # ...

cfg = ProjectResourceConfig("ADTECH")
```

Each project's `databricks_config.py` becomes ~5 lines re-exporting from the shared loader. The compound projects (HB, AdTech) keep domain-specific additions (VS, multiple Genies).

### Test design
- **Unit (`tests/common/test_project_resource_config.py`)**: monkeypatch env vars, instantiate `ProjectResourceConfig("ADTECH")`, assert fields populate as expected; assert missing env var yields empty string (not None, not KeyError).
- **Smoke**: `uv run apx dev check` passes.

### Rollback
The shared loader is additive; per-project files still work if we leave them. Flip to the shared loader project-by-project.

---

## 7. Torch → Optional Extras (Lazy Import)

### Scope
Stop bundling torch + open-clip-torch for every deploy. Only HB Product Center's CLIP recognition needs them.

### Action plan
1. Move torch, open-clip-torch from `[project.dependencies]` to `[project.optional-dependencies.image-recognition]` in `pyproject.toml`.
2. In `hb_product_center/services/recognition_service.py` (or wherever CLIP is loaded), lazy-import:
   ```python
   def _load_clip():
       try:
           import torch, open_clip
       except ImportError as e:
           raise RuntimeError("image-recognition extras not installed") from e
       ...
   ```
3. The deploy bundle for `fevm-felix-demo` installs with `[image-recognition]` so the prod deploy is unchanged.
4. Document in `claude.md` that local dev without the extras group won't be able to run HB recognition tests — a fair trade for faster dev loop.

### Test design
- **Smoke**: `uv sync` without the extras, then `uv run pytest -x -k "not recognition"` passes.
- **Smoke with extras**: `uv sync --extra image-recognition`, then run HB recognition tests.
- **CI**: two matrix jobs — `base` and `base + extras`.

### Rollback
Revert `pyproject.toml`; torch reappears as a core dep.

---

## 8. Rate Limiting

### Scope
Add per-IP rate limits to the endpoints that hit expensive Databricks resources.

### Endpoints
- `POST /api/projects/hb-product-center/recognition/identify` — UC Statement Execution.
- `POST /api/projects/*/chat` — MAS/KA invocations.
- `POST /api/projects/*/mas-chat` — same.

### Action plan
1. `uv add slowapi`.
2. In `backend/app.py`, mount the SlowAPI middleware with `Limiter(key_func=get_remote_address)`.
3. Decorate the expensive routes: `@limiter.limit("10/minute")` for chat, `@limiter.limit("5/minute")` for recognition.
4. Return 429 with a structured error body.

### Test design
- **Unit (`tests/common/test_rate_limit.py`)**: hit a rate-limited route 11 times in <1s, assert the 11th returns 429 with `Retry-After` header.
- **Edge case**: two different `X-Forwarded-For` clients each get their own quota.

### Rollback
Remove the decorator; middleware tolerates absence.

---

## 9. Pagination on List Endpoints

### Scope
Any `GET /list-stuff` endpoint that today returns "all" or has a hardcoded `.limit(20)`.

### Evidence
`adtech_intelligence/routers/chat.py:72-97` — `list_chat_sessions` has a hardcoded `.limit(20)` with no `offset` / `skip` parameter. Similar patterns live in other routers.

### Action plan
Add `skip: int = 0, limit: int = Query(default=50, le=200)` to every list endpoint; apply `.offset().limit()` uniformly. Update OpenAPI client regeneration to pick up the params.

### Test design
- Hit `GET ...?limit=5` and `?limit=5&skip=5`; assert pages don't overlap and the `limit=201` case returns 422.

### Rollback
Per-endpoint; trivial.

---

## 10. Foundation Test Suite ("first 10 tests")

### Scope
Get from 0 tests to a baseline ~10–12 tests covering the highest-impact paths. Mirrors the test-coverage investigation's quick wins.

### Tests to add (roughly in order)
1. `tests/common/test_databricks_agents.py` — `extract_agent_text()` across 3 response shapes.
2. `tests/common/test_streaming.py` — happy path, early error, late error, consumer abort.
3. `tests/common/test_projects_router.py` — list, get by slug, 404 on unknown slug.
4. `tests/common/test_ideas_router.py` — session CRUD + first chat turn.
5. `tests/common/test_input_validation.py` — Pydantic length bounds on every free-text field.
6. `tests/common/test_project_resource_config.py` — `ProjectResourceConfig` env-var resolution.
7. `tests/projects/hb_product_center/test_uc_query_security.py` — SQL injection payloads (see workstream 2).
8. `tests/projects/hb_product_center/test_recognition.py` — `/identify` happy path + input validation.
9. `tests/projects/mol_asm_cockpit/test_stations.py` — list stations + filter by region.
10. `tests/integration/test_lakebase.py` (`@pytest.mark.integration`) — `generate_database_credential` returns a token (requires live workspace).
11. `tests/e2e/test_gallery.spec.ts` — Playwright: homepage loads all 5 accelerators.
12. `tests/e2e/test_chat_xss.spec.ts` — Playwright: malicious markdown is sanitized.

### Required infrastructure (ship with the first test PR)
- A mock `WorkspaceClient` in `tests/common/fixtures/mock_ws.py` that records SQL, returns canned MAS/KA responses, and implements the subset of `api_client.do()` we actually use.
- A `conftest.py` `client` fixture that mounts the full FastAPI app against an in-memory SQLite.
- Vitest setup (`vitest.config.ts`) + a `bun test` script in `package.json`.
- A Playwright config that uses the built frontend (not the dev server) and a backing FastAPI instance over in-memory SQLite.

### Test design (meta)
These tests are the test design. Each comes with a docstring stating what's being proven. All run under `pytest`, `bun test`, and `bunx playwright test` respectively.

### Rollback
Tests can only add signal. If a test is flaky, mark it `xfail` with a reason and a tracking issue.

---

## 11. CI (GitHub Actions)

### Scope
Gate PRs on `uv run pytest`, `uv run apx dev check`, and `bunx playwright test` (smoke).

### Action plan
`.github/workflows/ci.yml` with:
- Jobs: `lint-backend` (ty), `lint-frontend` (tsc), `test-backend` (pytest without `-m integration`), `build` (`uv run apx build`), `e2e-smoke` (Playwright against the built bundle).
- Matrix: Python 3.11 + 3.12.
- Cache: `uv`, `bun`, Playwright browsers.
- Secrets: none required — integration tests stay opt-in via `-m integration` (run only on demand with a `workflow_dispatch`).

### Test design
The workflow itself. The first run will surface any tests that break under CI's sterilized environment.

### Rollback
Disable the workflow; local dev is unaffected.

---

## 12. Obsolete Scripts & Docs Sweep

### Scope
Prune `scripts/` and `docs/` of superseded content.

### `scripts/` review
- `create_agents.py` — HB-specific one-off, superseded by `deploy_agents_fevm.py`. **Delete.**
- `migrate_full.py` — workspace migration to `fe-sandbox-felix-demo-sandbox` (now obsolete workspace). **Move to `scripts/archive/` or delete** — its agent-bricks paths are wrong on new workspaces anyway.
- `migration_state.json`, `fevm_agents_state.json` — deploy state; never commit. **Untrack, `.gitignore`.**
- `deploy_agents_fevm.py` — keep; it's the current tool.
- `deploy_to_workspace.py` — keep; HB data seeding tool.
- `migrate_uc_data.py` — audit; may be obsolete alongside `migrate_full.py`.
- `seed_all_uc_notebook.py`, `seed_lakebase.py`, `seed_uc_hb_data.py` — keep but verify each is referenced by something.
- `create_dashboards.py` — keep; imported by `migrate_full.py` (which we may delete — if so, this goes too unless `deploy_agents_fevm.py` grows a dashboard phase).
- `setup_vector_search.py` — keep; referenced in docs.

### `docs/` review
- `docs/TODO.md` — keep; active tracker.
- `docs/tasks/refinement.md` — keep; the audit this plan consumes from.
- `docs/development-guide.md` — keep; 12-section reference.
- `docs/projects/*.md` — keep; per-accelerator design docs.
- `docs/projects/aeco-digital-twin-plan.md` — keep; planned 6th accelerator.
- `docs/images/` — audit (not inspected this pass).
- **Add**: `docs/lessons-learned.md` (already written alongside this plan).

### Test design
- **Smoke**: run `git grep` for each script/doc being deleted to prove nothing references it.
- **Smoke**: a fresh `uv run apx build` and `uv run apx dev start` both succeed afterwards.

---

## Recommended sequencing

**Batch A — "safe wins, no app risk" (ship first, one PR per workstream):**
1. Repo cleanup (workstream 1)
2. Obsolete scripts/docs sweep (workstream 12)
3. `docs/lessons-learned.md` + this plan landed
4. CI skeleton that just runs lint + build (workstream 11 minimal)

**Batch B — "security fixes" (the reason to hurry):**
5. Markdown XSS (workstream 3)
6. SQL injection regression + deprecated API removal (workstream 2)
7. Input length validation (workstream 4)
8. Foundation test suite P0 pieces: `test_uc_query_security.py`, `test_chat_xss.spec.ts`, `test_input_validation.py` (subset of workstream 10)

**Batch C — "operational quality" (ship incrementally):**
9. Shared config helper (workstream 6)
10. Rate limiting (workstream 8)
11. Pagination (workstream 9)
12. Torch optional extras (workstream 7)

**Batch D — "bigger refactor" (ship one project at a time):**
13. Shared chat router factory + streaming normalization (workstream 5), one project per PR, starting with the least-coupled (VI Home One).
14. Remaining foundation tests (rest of workstream 10).
15. Full CI matrix (workstream 11 complete).

Batch A + B = ~1–2 days and closes every P0 security / hygiene item.
Batch C + D = ~1 week of partial-time work.

---

## Decisions (2026-04-23)

Answers from the user, locked in:

1. **`migrate_full.py` — keep for future reference.** Archive it under `scripts/archive/` (tracked, so future-you has the 14-phase history), and move `migration_state.json` + `fevm_agents_state.json` out of the committed tree (untracked, regenerated on demand). Workstream 12 adjusted accordingly.
2. **`.playwright-auth-state/` — remove, without breaking Playwright.** This directory stores browser Trust Tokens, cookies, and local storage from an old Playwright auth session. Committing it means any reviewer can grab the logged-in state. Approach:
   - Delete the tracked directory from git.
   - Add `.playwright-auth-state/` to `.gitignore`.
   - If any future E2E test needs pre-authenticated state, use Playwright's `storageState` feature: save to `.playwright-auth-state/session.json` (now gitignored) at the start of the suite, replay it for subsequent tests. The saved file never ships with the repo — each CI run regenerates it via a programmatic login fixture.
   - Smoke test: `bunx playwright test` still passes after the deletion.
3. **Chat refactor scope — all five projects.** BSH's JSON-envelope clients will need rewiring; the frontend chat component is the only consumer and ships with the repo, so breakage is bounded. Per-project migration PRs (one project per PR) so each change is reviewable and revertable. Fix BSH's frontend in the same PR that changes its backend response format.
4. **CI platform — GitHub Actions.** Workstream 11 is go.
5. **Rate-limit keying — see elaboration below.** Short answer: key off `X-Forwarded-User` (set by Databricks Apps), not IP. Fallbacks for local dev and for the rare request without the header.

### Elaboration on #5 — why rate-limit keying needs thought

Rate limiting counts requests against a "key". The stock SlowAPI default is `get_remote_address`, which reads `X-Forwarded-For` or the socket IP. On Databricks Apps that IP is **the auth proxy**, not the end user — so every request from every user comes in with the same IP. Per-IP keying therefore collapses to **one global quota for the whole app**: whoever hits the endpoint first uses up everyone else's budget. Not useful.

The options:

| Option | Key | Behavior on Databricks Apps | Verdict |
|---|---|---|---|
| (a) Per-IP (`get_remote_address`) | proxy IP | Global quota — 10/min for the whole app | ❌ useless |
| (b) Per-forwarded-user header | `X-Forwarded-User` (set by Databricks Apps) | Each authenticated user gets their own quota | ✅ recommended |
| (c) Per-OBO-token subject | decode `X-Forwarded-Access-Token` JWT's `sub` claim | Same outcome as (b), more complex | overkill |
| (d) Per-session cookie | N/A — no cookie auth | — | N/A |

Recommendation: **(b) with fallback chain**:

```python
def rate_limit_key(request: Request) -> str:
    user = request.headers.get("X-Forwarded-User")
    if user:
        return f"user:{user}"
    # Fallback for local dev (no Databricks Apps proxy in front)
    return f"ip:{get_remote_address(request)}"
```

If we ever expose any endpoint anonymously (we don't today — Databricks Apps enforces auth), the IP fallback catches it. Workstream 8's test suite needs a fixture that sets `X-Forwarded-User` to simulate multiple users, so we can confirm quotas are per-user, not global.

---

## New workstreams added from civion-safe lessons

These fold into the existing batches:

### 13. Server-side input sanitization at the API boundary
(Batch B, alongside the XSS fix.) Add `sanitize_text(value: str) -> str` that strips HTML tags via a strict regex (no full HTML parser; we never need HTML inside these fields). Apply via a Pydantic validator on every free-text field in every `*In` model: `content`, `description`, `search`, `title`, `notes`. Belt-and-suspenders alongside `rehype-sanitize` on the frontend — protects logs, DB dumps, exports, and any future non-React consumer. ~1h + unit tests. Lesson 19.1.

### 14. Seed-data hygiene pass
(Batch A.) Audit every `seed.py` and `scripts/seed_*.py`. Replace realistic-looking names and emails with `@example.test` addresses and obviously-fictional names ("Sample Advertiser 1", "Test Station Alpha"). No runtime risk; purely for demos and screenshots not to accidentally look like real customer data. ~45min. Lesson 19.2.

### 15. Regression-test gate
(Batch A — process rule, not code.) Add a one-liner to `claude.md` and the PR template: "No P0 or P1 bug fix merges without a named regression test." Codify what we're already implicitly doing after workstream 2 adds the SQL-injection payload suite. Lesson 19.5.

### 16. Canonical UC DDL
(Batch D, low urgency.) The DDL for each UC table lives in multiple places: `migrate_full.py`, `deploy_to_workspace.py`, `deploy_agents_fevm.py`, and `scripts/seed_*.py`. Drift is possible. Consolidate into a single `scripts/uc_schema.py` with a `TABLES` list; have every seeder/deployer import from it. ~2h. Lesson 19.8.

### 17. Lakebase restore runbook
(Batch C.) Write `docs/runbooks/lakebase-restore.md` covering Lakebase PITR via the Databricks UI, `pg_dump` export of `db-e9w7-uyd0a1xns2`, test restore into a branch database, and the exact `psql` commands to verify row counts after restore. Run the drill once and note the timing. ~2h including the drill. Lesson 19.14.

### 18. Dependency pin audit
(Batch C.) Review `pyproject.toml` and `package.json` for dependencies pinned as `>=X.Y` — pin them to exact versions for production builds. Accept that `uv.lock` / `bun.lock` already handles reproducibility; this audit is about the declared floor, which drives CVE response speed. Document a quarterly re-check. ~1h. Lesson 19.15.

### 19. Per-message rate-limit enforcement on SSE
(Batch C, part of workstream 8.) Don't only limit `POST /chat` per connection — limit per yielded user message within the SSE loop too. Today our streaming endpoints accept one message per HTTP call, so this is moot; if we ever add multi-turn over one connection, the limiter has to move inside the loop. Leave a comment in `services/streaming.py` flagging this. Lesson 19.12.

### 20. Persona-based UAT doc
(Batch D.) Create `docs/uat-personas.md` listing two personas per accelerator — a "demo user clicking around" and an "adversarial security-curious user". Each persona is a prompt for a Claude Code + browser MCP session. Run before each major demo. No code to change; produces repeatable QA. ~1h. Lesson 19.17.

Updated total effort: ~35–45h across all workstreams.

### Updated recommended sequencing

**Batch A (safe wins) — now includes:**
1. Repo cleanup (WS 1)
2. Obsolete scripts/docs sweep (WS 12) — including archiving `migrate_full.py`
3. `.playwright-auth-state/` purge with Playwright storageState refactor (part of WS 1)
4. Seed-data hygiene pass (WS 14)
5. Regression-test process rule in claude.md (WS 15)
6. CI skeleton (WS 11 minimal)

**Batch B (P0 security) — now includes:**
7. Markdown XSS + `rehype-sanitize` (WS 3)
8. SQL injection regression + deprecated API removal (WS 2)
9. Server-side input sanitization at API boundary (WS 13, new)
10. Input length validation (WS 4)
11. Foundation test P0s: SQL-injection payloads, XSS E2E, input validation (subset of WS 10)

**Batch C (ops quality) — now includes:**
12. Shared config helper (WS 6)
13. Rate limiting with per-user keying + per-message enforcement (WS 8 + WS 19)
14. Pagination (WS 9)
15. Torch optional extras (WS 7)
16. Dependency pin audit (WS 18)
17. Lakebase restore runbook + drill (WS 17)

**Batch D (bigger refactor) — now includes:**
18. Shared chat router factory + streaming normalization across all 5 projects including BSH frontend fix (WS 5)
19. Canonical UC DDL (WS 16)
20. Rest of foundation test suite (WS 10)
21. Full CI matrix (WS 11 complete)
22. Persona UAT doc (WS 20)

Batch A + B ≈ 12–16h and closes every P0 hygiene/security item. Batch C + D ≈ 20–25h and gets us to production-grade ops quality.

---

Ready to start when you give the green light. Suggest we go Batch A → B → C → D, with a per-batch review before advancing.
