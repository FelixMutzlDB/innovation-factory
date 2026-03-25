# Innovation Factory — Refinement Plan

Comprehensive code review and enhancement plan based on a full audit of the codebase,
lessons-learned from the Cursor/Opus build process, and the migration to
`fe-sandbox-felix-demo-sandbox`.

---

## Audit Summary

| Area | Finding |
|---|---|
| **Security** | 2 critical SQL injection paths, 1 medium XSS risk |
| **Code Quality** | Chat streaming duplicated 4x, 99 `type: ignore` comments, dead code in HB chat |
| **Error Handling** | Streaming endpoints lack try/except, `assert` used for validation |
| **Architecture** | Strong patterns overall; UC query layer is the weak link |
| **Config** | Clean env-var pattern; migration exposed wrong `OLD_CATALOG` default |
| **Tests** | Structure exists but coverage is thin; no security-focused tests |
| **Frontend** | Solid Suspense/Skeleton pattern; markdown rendering lacks sanitization |
| **Dependencies** | All current; `torch` adds 1 GB+ to deploy (only needed for CLIP) |

---

## P0 — Security (fix before any demo)

### S1. SQL Injection in `uc_query_service.py`

**File:** `src/innovation_factory/backend/projects/hb_product_center/services/uc_query_service.py`

**Problem:** `select_all()`, `count_rows()`, `avg_column()`, `sum_column()` accept raw
`where` and `order_by` strings that are interpolated directly into SQL. Any caller
passing user input creates an injection vector.

**Fix:** Replace string interpolation with a safe query builder. The UC Statement
Execution API doesn't support parameterized queries, so we need allowlist-based
sanitization:

```python
import re

_SAFE_COLUMN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_SAFE_ORDER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*(\s+(ASC|DESC))?$", re.I)

def _validate_column(name: str) -> str:
    if not _SAFE_COLUMN.match(name):
        raise ValueError(f"Invalid column name: {name}")
    return name

def _escape_like(value: str) -> str:
    """Escape LIKE wildcards and single quotes."""
    return (
        value.replace("'", "''")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )

def select_all(
    ws, table, *,
    filters: dict[str, str] | None = None,
    order_by_column: str = "",
    order_desc: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    fqn = get_table_name(table)
    sql = f"SELECT * FROM {fqn}"

    if filters:
        clauses = []
        for col, val in filters.items():
            _validate_column(col)
            escaped = val.replace("'", "''")
            clauses.append(f"{col} = '{escaped}'")
        sql += " WHERE " + " AND ".join(clauses)

    if order_by_column:
        _validate_column(order_by_column)
        sql += f" ORDER BY {order_by_column}" + (" DESC" if order_desc else "")

    sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"
    ...
```

Add a `search_like()` function for LIKE queries with proper escaping:

```python
def search_like(ws, table, columns: list[str], term: str, limit: int = 5):
    for col in columns:
        _validate_column(col)
    escaped = _escape_like(term.lower())
    clauses = [f"LOWER({c}) LIKE '%{escaped}%' ESCAPE '\\'" for c in columns]
    where = " OR ".join(clauses)
    ...
```

**Affected callers to update:**
- `recognition.py` — `identify_product()` (lines 90-98, 107-113)
- `recognition.py` — `list_recognition_jobs()` (line 166, `status` query param)
- `recognition.py` — `get_recognition_image()` (line 294, `image_id`)
- Any other router calling `select_all(where=...)` with user input

### S2. SQL Injection in `recognition.py` LIKE clauses

**File:** `src/innovation_factory/backend/projects/hb_product_center/routers/recognition.py`

**Problem:** Lines 90-98 build a WHERE clause from `request.description` with only
single-quote escaping. SQL comments (`--`), LIKE wildcards, and boolean injection
are all possible.

**Fix:** Use the `search_like()` function from S1 above:

```python
# Before (vulnerable)
escaped_desc = desc.replace("'", "''")
where_clause = f"LOWER(style_name) LIKE '%{escaped_desc}%' ..."
db_matches = select_all(ws, "hb_products", where=where_clause, limit=5)

# After (safe)
db_matches = search_like(
    ws, "hb_products",
    columns=["style_name", "category", "color", "material", "collection"],
    term=desc,
    limit=5,
)
```

### S3. Input length validation

**File:** `recognition.py`

**Problem:** No limit on `request.description` length — an attacker could send a
multi-MB string to create expensive LIKE queries.

**Fix:** Add Pydantic field validation:

```python
class ProductIdentifyRequest(BaseModel):
    description: str = Field(..., min_length=2, max_length=500)
```

### S4. Markdown XSS in frontend

**Files:** Any component rendering `react-markdown` with LLM/user-generated content.

**Fix:** Add `rehype-sanitize`:

```bash
uv run apx bun add rehype-sanitize
```

```tsx
import rehypeSanitize from "rehype-sanitize";
<ReactMarkdown rehypePlugins={[rehypeSanitize]}>{content}</ReactMarkdown>
```

---

## P1 — Error Handling & Robustness

### E1. Streaming chat error handling

**Files:** All `routers/chat.py` files (vi_home_one, bsh_home_connect, adtech, hb, mol_asm)

**Problem:** `event_generator()` async generators don't wrap the streaming loop in
try/except. If the LLM endpoint fails mid-stream, the client gets an abrupt
disconnection with no error event.

**Fix:** Wrap in try/except and emit an error SSE event:

```python
async def event_generator():
    full_response = ""
    try:
        async for chunk in chat_service.stream_response(...):
            full_response += chunk
            yield f"data: {json.dumps({'content': chunk})}\n\n"
    except Exception as e:
        logger.error(f"Stream error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    # ... save message, yield DONE
```

### E2. Replace `assert` with HTTPException

**Files:**
- `adtech_intelligence/routers/chat.py` (lines 91, 122)
- `adtech_intelligence/services/chat_service.py` (lines 43, 81)
- `hb_product_center/services/chat_service.py` (line 51)

**Problem:** `assert obj.id is not None` is optimized away with `python -O`. In
production, the code silently passes `None` downstream.

**Fix:** Replace each with:

```python
if not session or session.id is None:
    raise HTTPException(status_code=404, detail="Session not found")
```

### E3. Missing 404 on invalid query params

**File:** `mol_asm_cockpit/routers/stations.py`

**Problem:** Invalid `region_id` or `station_type` values return an empty list
instead of a 400 error.

**Fix:** Validate enum values against the model before querying.

---

## P2 — Code Quality & DRY

### Q1. Extract shared chat streaming utility

**Problem:** The SSE streaming pattern is copy-pasted across 4-5 projects with ~90%
identical code (event generator, message storage, DONE sentinel).

**Fix:** Create `src/innovation_factory/backend/platform/services/streaming.py`:

```python
from fastapi.responses import StreamingResponse

async def create_chat_stream(
    stream_fn,           # async generator yielding chunks
    on_complete,         # callback(full_response) to persist
    on_error=None,       # optional error callback
) -> StreamingResponse:
    async def event_generator():
        full = ""
        try:
            async for chunk in stream_fn():
                full += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            if on_error:
                on_error(e)
            return
        on_complete(full)
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

Each project's chat router reduces to ~10 lines calling this utility.

### Q2. Remove dead chat code in HB Product Center

**File:** `hb_product_center/routers/chat.py`

**Problem:** Session-based chat endpoints reference tables that don't exist in UC.
Only the MAS streaming endpoint works.

**Fix:** Remove dead session CRUD endpoints. Keep only the MAS streaming endpoint.
Add a comment explaining why UC-based chat sessions aren't used.

### Q3. Deduplicate `databricks_config.py` patterns

**Problem:** Each project's `databricks_config.py` repeats the same `os.getenv()`
pattern with slightly different prefixes. The shared `WAREHOUSE_ID` and `UC_CATALOG`
are defined in every file.

**Fix:** Create a shared base in `platform/config.py`:

```python
# platform/config.py
import os

UC_CATALOG = os.getenv("UC_CATALOG", "innovation_factory_catalog")
WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "8af6100313039ba2")
WORKSPACE_URL = os.getenv("WORKSPACE_URL", "fe-sandbox-felix-demo-sandbox.cloud.databricks.com")
```

Each project imports shared values and only defines project-specific ones.

### Q4. Reduce `type: ignore` comments

**Problem:** 99 `type: ignore` comments, many with blanket suppression.

**Fix:**
1. Update `pyproject.toml` `[tool.ty.rules]` to suppress known SQLModel false positives globally
2. Replace blanket `# type: ignore` with specific rules: `# type: ignore[unresolved-attribute]`
3. For ~10 remaining, add inline docs explaining why the ignore is needed

---

## P3 — Architecture Improvements

### A1. Make `torch`/`open-clip` optional

**Problem:** `torch` (915 MB) and `open-clip-torch` are only used by the image
similarity service in HB Product Center. Every deploy downloads them.

**Fix:**
1. Move CLIP deps to an optional group in `pyproject.toml`:
   ```toml
   [project.optional-dependencies]
   clip = ["torch>=2.0.0", "open-clip-torch>=2.24.0", "Pillow>=10.0.0"]
   ```
2. In `image_similarity_service.py`, lazy-import with graceful fallback:
   ```python
   def compute_embedding(image_bytes):
       try:
           import open_clip
           import torch
       except ImportError:
           raise HTTPException(503, "Image similarity not available (torch not installed)")
       ...
   ```
3. For production deploys where CLIP is needed, install with `pip install .[clip]`

**Impact:** Deploy time drops from ~4 min to ~1 min; package size drops ~900 MB.

### A2. App resource configuration for Lakebase

**Lesson from migration:** The app's SP needs explicit Lakebase access via app
resources. The correct format is:

```yaml
resources:
  - name: lakebase-db
    postgres:
      branch: projects/innovation-factory/branches/production
      database: projects/innovation-factory/branches/production/databases/<db-id>
      permission: CAN_CONNECT_AND_CREATE
```

**Action:** Document this in `development-guide.md` Section 5 (Lakebase Connection)
and ensure `app.yml` + `databricks.yml` always include the `resources` block.
Also document that after adding the resource, you must grant schema-level
permissions:

```sql
GRANT ALL ON SCHEMA public TO "<sp-uuid>";
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT ALL PRIVILEGES ON TABLES TO "<sp-uuid>";
```

### A3. Rate limiting on public-facing endpoints

**Problem:** No rate limiting on any endpoint. The `/identify` endpoint (which
queries UC) could be abused to generate expensive SQL warehouse load.

**Fix:** Add `slowapi` middleware:

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/identify")
@limiter.limit("10/minute")
async def identify_product(...):
    ...
```

### A4. Request logging middleware

**Problem:** No structured request logging for security auditing.

**Fix:** Add a middleware that logs: endpoint, method, user identity (from OBO
token), response status, and latency. Use the existing `logger` module.

---

## P4 — Testing

### T1. Security-focused tests

**Add to `tests/projects/test_hb_security.py`:**

```python
def test_sql_injection_in_identify(client):
    """Verify SQL injection attempts are safely handled."""
    payloads = [
        "'; DROP TABLE hb_products; --",
        "' OR '1'='1",
        "test%' UNION SELECT * FROM hb_products WHERE '1'='1",
    ]
    for payload in payloads:
        resp = client.post("/api/projects/hb-product-center/recognition/identify",
                          json={"description": payload})
        assert resp.status_code in (200, 400)  # Never 500

def test_description_length_limit(client):
    resp = client.post("/api/projects/hb-product-center/recognition/identify",
                      json={"description": "x" * 10000})
    assert resp.status_code == 422  # Pydantic validation error
```

### T2. Chat streaming tests

**Add to `tests/common/test_streaming.py`:**

Test the shared streaming utility (Q1) with mock generators that:
- Complete normally
- Raise mid-stream
- Yield empty content

### T3. API contract tests

**Add to `tests/common/test_api_contracts.py`:**

Ensure all routers return proper response codes (404 for missing resources,
422 for invalid input, never raw 500s with stack traces).

### T4. Integration test for Lakebase connection

**Add to `tests/integration/test_lakebase.py`:**

```python
@pytest.mark.integration
def test_lakebase_credential_rotation():
    """Verify Lakebase OAuth token rotation works."""
    ws = WorkspaceClient()
    cred = ws.postgres.generate_database_credential(endpoint=ENDPOINT_NAME)
    assert cred.token
    assert len(cred.token) > 100
```

---

## P5 — Documentation & DevEx

### D1. Update `development-guide.md`

Add new sections:

- **Section 13: App Resources** — Lakebase, SQL warehouse, serving endpoint
  resource configuration for `app.yml`. Include the `postgres` field names
  discovered during migration (`branch`, `database` with full path, `CAN_CONNECT_AND_CREATE`).
- **Section 14: Migration Playbook** — Reference `scripts/migrate_full.py` and
  the lesson about `OLD_CATALOG` vs actual catalog name on source workspace.
- **Section 15: Security Checklist** — SQL injection prevention, input validation,
  markdown sanitization.

### D2. Add `.env.example`

Create a documented `.env.example` with all required variables:

```bash
# Shared
UC_CATALOG=innovation_factory_catalog
WAREHOUSE_ID=8af6100313039ba2

# Lakebase
PGHOST=ep-xxx.database.us-west-2.cloud.databricks.com
PGDATABASE=databricks_postgres
PGUSER=<sp-client-id>
PGPORT=5432
PGSSLMODE=require
ENDPOINT_NAME=projects/innovation-factory/branches/production/endpoints/primary

# AdTech Intelligence
ADTECH_DASHBOARD_ID=
ADTECH_GENIE_SPACE_ID=
ADTECH_ISSUE_RESOLUTION_KA_TILE_ID=
...
```

### D3. Update README with current accelerator list

The README only lists 3 accelerators (ViDistrictOne, BSH, AdTech). Add MOL ASM
Cockpit and HB Product Center.

---

## P6 — Migration Cleanup

### M1. Fix `migrate_full.py` OLD_CATALOG

The migration script had `OLD_CATALOG = "felix_demo_sandbox_catalog"` but the
actual data was in `innovation_factory_catalog` on the old workspace. Update the
script's default and add a CLI flag to override:

```python
parser.add_argument("--old-catalog", default="innovation_factory_catalog")
```

### M2. Clean up `__dist__` from git

The git status shows ~130 untracked `__dist__` asset files. These are build
artifacts that should be in `.gitignore`.

**Fix:** Add `src/innovation_factory/__dist__/` to `.gitignore` and remove tracked
dist files.

### M3. Remove `scripts/migrate_uc_data.py`

This was the old partial migration script, superseded by `migrate_full.py`.
Keep only `migrate_full.py` to avoid confusion.

---

## Implementation Order

| Priority | Tasks | Effort | Impact |
|---|---|---|---|
| **Week 1** | S1, S2, S3, S4 (SQL injection + XSS) | 4h | Critical security fixes |
| **Week 1** | E1, E2 (streaming errors + assert) | 2h | Robustness |
| **Week 2** | Q1 (shared streaming utility) | 3h | DRY, maintainability |
| **Week 2** | Q2, Q3 (dead code, config dedup) | 2h | Cleanliness |
| **Week 2** | T1, T2 (security + streaming tests) | 3h | Confidence |
| **Week 3** | A1 (optional torch) | 2h | Deploy speed |
| **Week 3** | A2, D1 (Lakebase docs) | 1h | DevEx |
| **Week 3** | D2, D3 (env example, README) | 1h | Onboarding |
| **Ongoing** | Q4 (type ignore cleanup) | 2h | Code quality |
| **Ongoing** | A3, A4 (rate limiting, logging) | 3h | Production hardening |
| **Cleanup** | M1, M2, M3 (migration artifacts) | 1h | Repo hygiene |

---

## Lessons Learned from the Build Process

### What Cursor/Opus did well
- Consistent project structure across all 5 accelerators
- Clean dependency injection via FastAPI Depends
- Proper OBO token handling for multi-tenant auth
- Good separation between PGlite dev and Lakebase production paths
- Solid frontend patterns (Suspense + Skeleton + auto-generated API client)

### What to watch for with AI-assisted coding
1. **SQL construction** — AI models tend to use string interpolation for SQL.
   Always review generated code that touches SQL/queries for injection risks.
2. **Copy-paste drift** — When the AI creates a new project by copying an existing
   one, subtle differences accumulate. The chat streaming pattern is identical
   across 4 projects but none call a shared utility.
3. **Assert vs. raise** — AI models often use `assert` for null checks because
   it's shorter. These get optimized away in production Python.
4. **Dead code accumulation** — When features evolve (e.g., HB chat moving from
   session-based to MAS-only), the AI doesn't always clean up the old path.
5. **Type suppression** — AI models add `# type: ignore` to make the checker
   pass rather than fixing the underlying type issue.
6. **Missing input validation** — AI-generated endpoints often skip length limits,
   allowed-value checks, and rate limiting.

### Migration-specific lessons
- Always verify catalog names on source workspace before scripting exports
- Lakebase Autoscale roles must have `auth_method: LAKEBASE_OAUTH_V1` — manually
  created Postgres roles get `NO_LOGIN` which breaks OAuth token auth
- App resources with `postgres` type require the full database path
  (`projects/.../databases/<db-id>`), not just the database name
- The `CAN_CONNECT_AND_CREATE` permission is the correct value for app SPs
  (not `CAN_USE`, `READ_WRITE`, or any other variant)
