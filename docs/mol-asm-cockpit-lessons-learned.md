# MOL ASM Cockpit — Lessons Learned

Development log and technical lessons from building the MOL ASM Cockpit project,
a full-stack Area Sales Manager dashboard built with FastAPI + React on Databricks Apps.

---

## 1. Databricks Lakeview Dashboard API (AI/BI Dashboards)

### Problem
Creating AI/BI dashboards programmatically via the Lakeview API required multiple
iterations to get the `serialized_dashboard` JSON structure right. The API returned
opaque `"failed to parse serialized dashboard"` errors with no indication of what
was wrong.

### Root Causes & Fixes

| Attempt | Error | Fix |
|---------|-------|-----|
| 1 | `failed to parse serialized dashboard` | The `query` field inside `datasets` must be a **plain SQL string** (`"query": "SELECT ..."`) — not a nested object (`"query": {"sql": "..."}`) |
| 2 | `validation failed: missing spec or textbox_spec` | `spec` (for charts/counters) and `textbox_spec` (for text widgets) must be **direct attributes** of each widget object, not inside `overrides` |
| 3 | Various silent failures | Empty `"fields": []` arrays in dataset queries can cause issues — omit them entirely |

### Key Takeaway
The Lakeview `serialized_dashboard` format is **not the same** as the JSON you see
in the dashboard UI export. When in doubt, create a minimal single-widget dashboard
via the SDK, inspect the result, and build up from there. The Python SDK's
`w.lakeview.create(Dashboard(...))` is more reliable than the MCP tool for debugging
because you get exact error messages.

---

## 2. Multi-Agent Supervisor (MAS) Endpoint Integration

### Problem
Connecting to a Databricks Agent Bricks MAS serving endpoint required three rounds
of debugging to get the request/response format right.

### The Journey

1. **SDK `serving_endpoints.query()` with dicts** → `AttributeError: 'dict' object has no attribute 'as_dict'`
   - The SDK expects `ChatMessage` objects, not raw Python dicts.

2. **SDK `serving_endpoints.query()` with `ChatMessage` objects** → `Invalid request: 'messages' field is not supported. Please use 'input' field instead.`
   - MAS endpoints use a **non-standard request format**: `{"input": [...]}` instead of `{"messages": [...]}`.

3. **Direct `requests.post()` with bearer token** → `401 Credential was not sent or was of an unsupported type`
   - The SDK uses OAuth (not PAT tokens) under the hood. Raw `requests` doesn't handle the auth flow.

### Solution
Use the SDK's internal HTTP client for raw REST calls:

```python
response = ws.api_client.do(
    "POST",
    f"/serving-endpoints/{endpoint_name}/invocations",
    body={"input": [{"role": "user", "content": message}]},
)
```

The response format is also non-standard:

```json
{
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": [{"type": "output_text", "text": "..."}]
    }
  ]
}
```

### Key Takeaway
MAS/Agent Bricks endpoints do **not** follow the standard OpenAI-compatible
`messages`/`choices` format. Always use `ws.api_client.do()` for raw calls
when the SDK's typed methods don't support the endpoint's wire format.

---

## 3. PGlite (Local Dev Database) Memory Limits

### Problem
The initial seed script tried to generate data for 44 stations × 90 days,
producing ~130,000 records. PGlite's WebAssembly-based in-memory database
crashed with large batch INSERTs.

### Symptoms
- Database connection drops during seeding
- `PGlite database initialized` followed by immediate crash
- All subsequent API requests fail with connection errors

### Solution
Reduced seed data to **10 stations × 14 days** for local development. This keeps
the data realistic enough for UI testing while staying well within PGlite's limits.
The full 44-station / 365-day dataset lives in `seed_uc_tables.py` and runs on a
Databricks cluster with PySpark (unlimited memory).

### Key Takeaway
PGlite is great for local dev but has hard limits on batch INSERT size. Keep local
seed data small (~1,000s of rows, not ~100,000s). Use `session.flush()` between
batches rather than committing everything at once.

---

## 4. Python Type Checker (`ty`) and SQLModel/SQLAlchemy

### Problem
The `ty` type checker (used by `apx dev check`) reports many false positives with
SQLModel and SQLAlchemy code because these libraries use metaclass magic for column
operations that `ty` can't understand.

### Common False Positives

| Pattern | `ty` Error | Reality |
|---------|-----------|---------|
| `Model.field.desc()` | `unresolved-attribute` on `datetime` | SQLAlchemy column proxy, works fine |
| `Model.field >= value` | `unsupported-operator` | SQLAlchemy operator overloading |
| `Model.field.contains(x)` | `unresolved-attribute` on `str` | SQLAlchemy column method |
| `Model.field.in_([...])` | `unresolved-attribute` | SQLAlchemy column method |
| `datetime.utcnow` | `deprecated` | Works fine, just deprecated in Python 3.12+ |
| `select(Model)` | `no-matching-overload` | SQLModel dynamic overloads |

### Solution
Two-tier approach:

1. **`pyproject.toml` config** for codebase-wide suppressions:
   ```toml
   [tool.ty.src]
   exclude = ["scripts/", "**/seed_uc_tables.py", "**/create_dashboard.py"]

   [tool.ty.rules]
   deprecated = "ignore"
   ```

2. **Inline `# type: ignore[rule]`** for specific false positives:
   ```python
   .order_by(Model.created_at.asc())  # type: ignore[unresolved-attribute]
   ```

### Key Takeaway
Use **specific rule names** in type-ignore comments (e.g., `[unresolved-attribute]`),
not blanket `# type: ignore`. Blanket ignores will later become `unused-type-ignore-comment`
warnings when `ty` updates and resolves some of these issues. Also, `ty` ignores can
become stale between versions — re-check after `ty` upgrades.

---

## 5. Environment Variable Configuration Pattern

### Problem
Hardcoded Databricks resource IDs (dashboard IDs, endpoint names, warehouse IDs)
break when deploying to different workspaces or environments.

### Pattern (from AdTech project)
Each project gets a `databricks_config.py` that reads `PROJECTPREFIX_*` env vars:

```python
# databricks_config.py
import os

DASHBOARD_ID = os.getenv("MAC_DASHBOARD_ID", "")
MAS_ENDPOINT_NAME = os.getenv("MAC_MAS_ENDPOINT_NAME", "")
WAREHOUSE_ID = os.getenv("MAC_WAREHOUSE_ID", "")
```

With a corresponding `.env.example` at the repo root:
```
MAC_DASHBOARD_ID=<dashboard-id>
MAC_MAS_ENDPOINT_NAME=<mas-endpoint-name>
MAC_WAREHOUSE_ID=<warehouse-id>
```

### Key Takeaway
Never hardcode Databricks resource IDs in router files. Centralize them in a
config module, read from env vars, and provide empty defaults. The `.env.example`
file serves as documentation for required configuration.

---

## 6. Project Organization

### Problem
During development, scripts and artifacts (dashboard JSON, UC seed scripts,
knowledge base documents) were created in a top-level `/scripts/` directory.
This made it unclear which project they belonged to.

### Correct Structure
All project-specific artifacts belong under the project folder:

```
src/innovation_factory/backend/projects/mol_asm_cockpit/
├── __init__.py
├── databricks_config.py          # env var config
├── models.py                     # SQLModel models
├── router.py                     # FastAPI router aggregation
├── routers/                      # individual route files
├── seed.py                       # local dev seeding (PGlite)
├── seed_uc_tables.py             # Databricks cluster seeding (PySpark)
├── create_dashboard.py           # dashboard creation script
├── dashboard_definition.json     # AI/BI dashboard JSON
└── ka_docs/                      # knowledge assistant documents
    ├── issue_resolution/
    └── customer_relations/
```

### Key Takeaway
Follow the pattern set by existing projects in the repo. Check `git ls-tree` on
the reference branch to see how sibling projects organize their files before
creating new directories at the repo root.

---

## 7. TanStack Router Route Tree Generation

### Problem
After creating new route files under `routes/projects/mol-asm-cockpit/`, the
auto-generated `routeTree.gen.ts` sometimes only partially updates — adding
imports and tree structure but not the `FileRoutesByPath` type mapping.

### Symptoms
- TypeScript errors on route components (types not found)
- Routes work at runtime but IDE shows red squiggles
- `routeTree.gen.ts` has the imports but is missing type entries

### Solution
Restart the dev server (`uv run apx dev restart`). The OpenAPI client and route
tree are regenerated on startup. If that doesn't work, delete `routeTree.gen.ts`
and restart — it will be fully regenerated from scratch.

### Key Takeaway
Auto-generated files (`routeTree.gen.ts`, `api.ts`) should never be manually
edited. When they're out of sync, regenerate them. After merge conflicts on these
files, always regenerate rather than trying to manually resolve the conflicts.

---

## 8. Merge Conflict Patterns in Multi-Project Repos

### Observation
When multiple feature branches add new projects to the same repo simultaneously,
the conflicts are predictable and always in the same files:

| File | Conflict Pattern |
|------|-----------------|
| `backend/router.py` | Both branches add `include_router()` at the same location |
| `backend/seed.py` | Both branches add seed imports and project entries |
| `ui/lib/api.ts` | Auto-generated — regenerate after merge |
| `ui/types/routeTree.gen.ts` | Auto-generated — regenerate after merge |

### Key Takeaway
These are always **additive conflicts** (both sides add, neither deletes). Resolution
is straightforward: keep both additions. For auto-generated files, just regenerate
after merging. Consider adding a comment marker in `router.py` and `seed.py` like
`# -- project routers below --` to make conflict resolution even more obvious.

---

## Summary

| # | Topic | One-Line Lesson |
|---|-------|----------------|
| 1 | Lakeview API | Dashboard `query` is a plain SQL string, not `{"sql": "..."}` |
| 2 | MAS Endpoints | Use `input`/`output` format via `ws.api_client.do()`, not `messages`/`choices` |
| 3 | PGlite Limits | Keep local seed data under ~10K rows; use PySpark for full datasets |
| 4 | `ty` + SQLModel | Use specific `# type: ignore[rule]` comments, not blanket ignores |
| 5 | Config Pattern | Read all resource IDs from env vars via `databricks_config.py` |
| 6 | Project Layout | Keep all project artifacts inside the project folder, not at repo root |
| 7 | Route Generation | Never manually edit auto-generated files; regenerate on conflicts |
| 8 | Merge Conflicts | Multi-project repos have predictable additive conflicts; regenerate auto-gen files |
