# Innovation Factory — Development Guide & Lessons Learned

Technical reference and lessons learned from building the Innovation Factory platform,
a multi-project full-stack application built with FastAPI + React on Databricks Apps.

---

## 1. Databricks Lakeview Dashboard API (AI/BI Dashboards)

### Problem
Creating and embedding AI/BI dashboards programmatically via the Lakeview API required
multiple iterations to get the `serialized_dashboard` JSON structure right.

### Key Findings

| Issue | Fix |
|-------|-----|
| `failed to parse serialized dashboard` | The `query` field inside `datasets` must be a **plain SQL string** (`"query": "SELECT ..."`) — not a nested object |
| `validation failed: missing spec or textbox_spec` | `spec` (for charts/counters) and `textbox_spec` (for text widgets) must be **direct attributes** of each widget object |
| Empty `"fields": []` arrays cause silent failures | Omit empty field arrays entirely |

### Dashboard Embedding
To embed a dashboard in a React frontend, use an `<iframe>` pointing to the published
dashboard URL with `?embed` appended. The backend must expose the `workspace_url` and
`dashboard_id` so the frontend can construct the embed URL:

```
https://{workspace_url}/embed/dashboardsv3/{dashboard_id}?embed
```

### Takeaway
The Lakeview `serialized_dashboard` format differs from the dashboard UI export JSON.
Create minimal single-widget dashboards via the SDK for debugging. Keep dashboard creation
scripts inside the project folder (e.g., `create_dashboard.py` + `dashboard_definition.json`).

---

## 2. Multi-Agent Supervisor (MAS) & Knowledge Assistant (KA) Integration

### Problem
Connecting to Databricks Agent Bricks serving endpoints (MAS and KA) required
understanding a non-standard request/response format.

### Request Format
Agent Bricks endpoints do **not** support the standard `messages` field.
Use the `input` field instead:

```python
response = ws.api_client.do(
    "POST",
    f"/serving-endpoints/{endpoint_name}/invocations",
    body={"input": [{"role": "user", "content": message}]},
)
```

### Response Parsing
The response uses a nested structure with content arrays:

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

Responses may also contain internal tool-call metadata. Implement a recursive
`_extract_text()` helper to walk the nested structure and filter out non-text content
before saving to the database.

### Auth Approach
- **Do not** use raw `requests.post()` with PAT tokens — OAuth handling is complex.
- **Do** use `ws.api_client.do()` which inherits the SDK's auth context automatically.

### Shared Utilities Module
The platform provides `backend/services/databricks_agents.py` with reusable helpers:
- **`query_agent_endpoint(ws, endpoint_name, messages)`** — Calls MAS/KA endpoints using the correct `input` payload format
- **`extract_agent_text(response)`** — Recursively extracts plain text from nested Agent Bricks responses, filtering out tool-call metadata

Projects (AdTech Intelligence, MOL ASM Cockpit) import these instead of reimplementing. Use them when adding new MAS/KA integrations.

### Takeaway
Always use `ws.api_client.do()` for MAS/KA endpoints. The SDK's typed
`serving_endpoints.query()` method does not support the Agent Bricks wire format.
Prefer the shared `databricks_agents` module over custom implementations.

---

## 3. PGlite (Local Dev Database) Memory Limits

### Problem
PGlite's WebAssembly-based in-memory database crashes with large batch INSERTs.

### Symptoms
- Database connection drops during seeding
- `PGlite process exited early with status: ExitStatus(unix_wait_status(256))`
- All subsequent API requests fail

### Solution
- Keep local seed data small: ~10 stations, ~14 days, ~1,000s of rows
- Use `session.flush()` between batches rather than one large commit
- Reduce `batch_size` (e.g., from 200 to 30) for INSERT-heavy seeds
- Full datasets belong in `seed_uc_tables.py` scripts that run on Databricks clusters

### Takeaway
PGlite is great for local dev but has hard limits on batch INSERT size (~10K rows max).
Always provide both a lightweight `seed.py` (for PGlite) and an optional
`seed_uc_tables.py` (for production/cluster seeding with PySpark).

---

## 4. Python Type Checker (`ty`) and SQLModel/SQLAlchemy

### Problem
The `ty` type checker reports false positives with SQLModel/SQLAlchemy metaclass magic.

### Common False Positives

| Pattern | `ty` Error | Reality |
|---------|-----------|---------|
| `Model.field.desc()` | `unresolved-attribute` on `datetime` | SQLAlchemy column proxy |
| `Model.field.in_([...])` | `unresolved-attribute` | SQLAlchemy column method |
| `Model.field.contains(x)` | `unresolved-attribute` on `str` | SQLAlchemy column method |
| `Model.field >= value` | `unsupported-operator` | SQLAlchemy operator overloading |
| FastAPI `Depends()` with `=None` | `invalid-parameter-default` | Valid FastAPI pattern |
| `select(Model)` | `no-matching-overload` | SQLModel dynamic overloads |
| `Optional[int]` ID usage | `invalid-argument-type` | Need explicit `assert id is not None` |

### Solution

1. **`pyproject.toml`** for codebase-wide suppressions:
   ```toml
   [tool.ty.src]
   exclude = ["scripts/", "**/seed_uc_tables.py", "**/create_dashboard.py"]

   [tool.ty.rules]
   deprecated = "ignore"
   ```

2. **Inline** with specific rule names:
   ```python
   .order_by(Model.created_at.asc())  # type: ignore[unresolved-attribute]
   ```

3. **Type narrowing** for optional IDs:
   ```python
   assert obj.id is not None
   ```

### Additional Typing Notes
- Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` throughout
- Use `from collections.abc import Sequence` instead of `list` for read-only parameters
- Add `# type: ignore[assignment]` for FastAPI dependency defaults like `db: Session = None`

### Takeaway
Use **specific rule names** in type-ignore comments, not blanket `# type: ignore`.
Blanket ignores become `unused-type-ignore-comment` warnings when `ty` updates.

---

## 5. Lakebase (Managed PostgreSQL) Connection

### Problem
Connecting to Lakebase Autoscaling from local dev and deployed apps requires
OAuth token rotation and careful URL handling.

### Credential Rotation Pattern
Lakebase uses OAuth tokens that expire after one hour. Use SQLAlchemy's `do_connect`
event to inject fresh credentials before each connection:

```python
@event.listens_for(engine, "do_connect")
def before_connect(dialect, conn_rec, cargs, cparams):
    credential = ws.postgres.generate_database_credential(endpoint=endpoint_name)
    cparams["password"] = credential.token
```

### URL Encoding Gotcha
- **In SQLAlchemy engine URLs**: URL-encode the username (e.g., `felix.mutzl%40databricks.com`)
- **In psycopg.connect()**: Do **not** URL-encode — psycopg handles this internally

### Service Principal Access
After seeding, grant the service principal access:
```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "<sp-uuid>";
GRANT USAGE ON SCHEMA public TO "<sp-uuid>";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "<sp-uuid>";
```

### Discovering Endpoint Names
Use the Databricks SDK to list projects, branches, and endpoints:
```python
for project in ws.postgres.list_projects():
    for branch in ws.postgres.list_branches(parent=project.name):
        for ep in ws.postgres.list_endpoints(parent=branch.name):
            print(ep.name)  # Full endpoint path for credential generation
```

### Takeaway
Always use `ENDPOINT_NAME` env var for credential generation. The runtime should
detect whether to use PGlite (local dev), Lakebase (deployment), or a direct
`DATABASE_URL` override, following a priority chain.

---

## 6. Environment Variable Configuration Pattern

### Problem
Hardcoded Databricks resource IDs break when deploying to different environments.

### Pattern
Each project gets a `databricks_config.py` that reads `PROJECTPREFIX_*` env vars:

```python
import os

DASHBOARD_ID = os.getenv("MAC_DASHBOARD_ID", "")
MAS_ENDPOINT_NAME = os.getenv("MAC_MAS_ENDPOINT_NAME", "")
WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "")
```

Provide `.env.example` at the repo root with placeholders for all required variables.

### `.gitignore` for `.env`
The `.gitignore` pattern `.env*` will block `.env.example`. Add an exception:
```gitignore
.env*
!.env.example
```

### Takeaway
Never hardcode resource IDs in router files. Centralize in config modules, read
from env vars, and document all variables in `.env.example`.

---

## 7. Project Organization & Structure

### Standard Project Layout
```
src/innovation_factory/backend/projects/<project_slug>/
├── __init__.py
├── databricks_config.py          # env var config for Databricks resources
├── models.py                     # SQLModel table definitions + Pydantic schemas
├── router.py                     # FastAPI router aggregation
├── routers/                      # individual route files by domain
├── seed.py                       # local dev seeding (PGlite-safe)
├── seed_uc_tables.py             # optional: Databricks cluster seeding (PySpark)
├── create_dashboard.py           # optional: dashboard creation script
├── dashboard_definition.json     # optional: AI/BI dashboard JSON
├── services/                     # optional: business logic (chat, anomaly detection)
└── ka_docs/                      # optional: knowledge assistant source documents
```

### Frontend Routes
```
src/innovation_factory/ui/routes/
├── _sidebar/
│   ├── route.tsx                 # main layout with Profile + Documentation nav
│   └── documentation.tsx         # /documentation — project docs viewer (fetches from /api/docs/projects)
└── projects/<project-slug>/
    ├── route.tsx                 # layout with sidebar navigation
    ├── index.tsx                 # redirect to default sub-route
    ├── home.tsx                  # main dashboard/overview
    ├── agent.tsx                 # AI chat agent
    ├── explorer.tsx               # Genie space / data exploration
    ├── anomalies/index.tsx       # anomaly monitoring
    └── <domain>/                 # domain-specific pages
```

### Takeaway
Follow the pattern set by existing projects. All project-specific artifacts belong
inside the project folder, not at the repo root. Check sibling projects before
creating new directory structures.

---

## 8. Test Infrastructure

### Structure
```
tests/
├── conftest.py                   # Shared fixtures: engine, session, client (in-memory SQLite)
├── common/                       # Platform-level tests
│   ├── test_api_health.py
│   ├── test_databricks_agents.py  # Unit tests for databricks_agents module
│   ├── test_models.py
│   └── test_project_routes.py
├── projects/                     # Project-specific tests
│   ├── test_vi_home.py
│   ├── test_bsh.py
│   ├── test_adtech.py
│   └── test_mol_asm.py
└── integration/                  # Integration tests (may require Databricks)
    └── test_databricks.py
```

### Running Tests
Use `pytest` with the shared in-memory SQLite database. The `conftest.py` sets
`DATABASE_URL=sqlite:///file:test_shared?mode=memory&cache=shared` and imports
all project models so the schema is created before tests run.

### Takeaway
Add project tests under `tests/projects/test_<project>.py`. Use the shared
`client` fixture for API tests. Unit-test shared utilities (e.g. `databricks_agents`)
in `tests/common/` without live Databricks connections.

---

## 9. Frontend Data Fetching & Routing

### Pattern: Suspense + Skeleton
Always use `useXSuspense` hooks with React `Suspense` boundaries:

```tsx
function MyPage() {
  return (
    <Suspense fallback={<Skeleton className="h-64" />}>
      <MyContent />
    </Suspense>
  );
}

function MyContent() {
  const { data } = useGetItemsSuspense(selector());
  return <div>{/* render data */}</div>;
}
```

### Auto-Generated Files
- `ui/lib/api.ts` — OpenAPI client, regenerated on backend changes
- `ui/types/routeTree.gen.ts` — TanStack Router route tree

**Never manually edit these files.** When they're out of sync after merges,
restart the dev server to regenerate.

### Takeaway
Render static layout elements immediately, fetch API data with suspense.
Auto-generated files should be regenerated, never manually resolved.

---

## 10. Merge Conflicts in Multi-Project Repos

### Predictable Conflict Points

| File | Conflict Pattern | Resolution |
|------|-----------------|------------|
| `backend/router.py` | Both branches add `include_router()` | Keep both additions |
| `backend/seed.py` | Both branches add seed imports and project entries | Keep both additions |
| `ui/lib/api.ts` | Auto-generated | Regenerate after merge |
| `ui/types/routeTree.gen.ts` | Auto-generated | Regenerate after merge |

### Takeaway
These are always **additive conflicts** — both sides add, neither deletes.
For auto-generated files, just regenerate after merging.

---

## 11. Seeding Strategy

### Two-Tier Seeding
1. **`seed.py`** — lightweight, PGlite-safe (~1K rows), runs on every `apx dev start`
2. **`seed_uc_tables.py`** — full-scale, runs on Databricks clusters with PySpark
3. **`scripts/seed_lakebase.py`** — standalone script to seed the Lakebase PostgreSQL
   instance using the Databricks SDK for credential management

### Lakebase Seeding Notes
- Lakebase does not support `CREATE TYPE` — disable native PostgreSQL enums:
  ```python
  for table in SQLModel.metadata.tables.values():
      for column in table.columns:
          if isinstance(column.type, SAEnum):
              column.type.native_enum = False
  ```
- Use `SQLModel.metadata.drop_all()` + `create_all()` for clean re-seeds
- Always run `GRANT` statements after seeding for service principal access

---

## 12. Enum Naming — Avoiding OpenAPI Schema Collisions

### Problem
When two projects define enums with the same class name (e.g., both `adtech_intelligence` and `mol_asm_cockpit` define `IssueStatus`), FastAPI's OpenAPI schema generation creates ambiguous names like `IssueStatus-Input`, which are invalid TypeScript identifiers.

### Solution
**Always prefix project-specific enums with the project abbreviation:**
- `MacAlertSeverity` instead of `AlertSeverity`
- `MacIssueStatus` instead of `IssueStatus`
- BSH already does this correctly: `BshTicketStatus`, `BshChatRole`

### Rule
If an enum is specific to one project, prefix it with the project's short name. Only use unprefixed names for truly shared/platform-level enums.

---

## Summary

| # | Topic | Key Lesson |
|---|-------|-----------|
| 1 | Lakeview API | Dashboard `query` is a plain SQL string; embed via `<iframe>` with `?embed` |
| 2 | MAS/KA Endpoints | Use `input`/`output` format via `ws.api_client.do()`, not `messages`/`choices` |
| 3 | PGlite Limits | Keep local seed data under ~10K rows; use PySpark for full datasets |
| 4 | `ty` + SQLModel | Use specific `# type: ignore[rule]` comments; narrow Optional types with asserts |
| 5 | Lakebase Connection | OAuth token rotation via `do_connect` event; don't URL-encode in psycopg |
| 6 | Config Pattern | Read all resource IDs from env vars via `databricks_config.py` |
| 7 | Project Layout | Keep all project artifacts inside the project folder |
| 8 | Test Infrastructure | Shared conftest fixtures; add project tests under tests/projects/ |
| 9 | Frontend Patterns | Suspense + Skeleton for data fetching; never edit auto-generated files |
| 10 | Merge Conflicts | Multi-project repos have predictable additive conflicts |
| 11 | Seeding Strategy | Two-tier: lightweight PGlite seeds + full-scale cluster/Lakebase seeds |
| 12 | Enum Naming | Prefix project enums to avoid OpenAPI schema collisions (e.g., `MacAlertSeverity` not `AlertSeverity`) |
