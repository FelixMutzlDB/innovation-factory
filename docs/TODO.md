# Innovation Factory — Outstanding Work

> FEIP: [FEIP-5472](https://databricks.atlassian.net/browse/FEIP-5472)
> Last reviewed: 2026-04-13
> Source: [docs/tasks/refinement.md](tasks/refinement.md) (full audit details)

Legend: `[ ]` open | `[x]` done | `[~]` partial | `[-]` won't do

---

## P0 — Security

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| S1 | SQL injection fix in `uc_query_service.py` (allowlist sanitization) | `[x]` | 2026-03-28 | Commit `59286f3`. Added `_validate_column`, `_escape_like`, `search_like` |
| S2 | SQL injection fix in `recognition.py` LIKE clauses | `[x]` | 2026-03-28 | Commit `59286f3`. Callers updated to use safe query builder |
| S3 | Input length validation on `ProductIdentifyRequest` | `[x]` | 2026-03-28 | Commit `59286f3`. Pydantic `Field(max_length=500)` |
| S4 | Markdown XSS — add `rehype-sanitize` to frontend | `[ ]` | — | Any component rendering `react-markdown` with LLM content needs this |

## P1 — Error Handling & Robustness

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| E1 | Streaming chat error handling (try/except in SSE generators) | `[x]` | 2026-03-28 | Commit `a960d14`. Shared streaming utility handles this |
| E2 | Replace `assert` with `HTTPException` in chat routers | `[ ]` | — | Files: `adtech/chat.py`, `adtech/chat_service.py`, `hb/chat_service.py` |
| E3 | Missing 404 on invalid query params in `mol_asm/stations.py` | `[ ]` | — | Invalid `region_id`/`station_type` returns empty list instead of 400 |

## P2 — Code Quality & DRY

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| Q1 | Extract shared chat streaming utility | `[x]` | 2026-03-28 | Commit `a960d14`. `backend/services/streaming.py` created |
| Q2 | Remove dead chat code in HB Product Center | `[ ]` | — | Session-based CRUD endpoints reference non-existent UC tables |
| Q3 | Deduplicate `databricks_config.py` shared values | `[ ]` | — | `WAREHOUSE_ID`, `UC_CATALOG` repeated in every project config |
| Q4 | Reduce blanket `type: ignore` comments (~99 total) | `[ ]` | — | Replace with specific rule names; update `pyproject.toml` suppressions |

## P3 — Architecture Improvements

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| A1 | Make `torch`/`open-clip` optional dependency | `[ ]` | — | 900MB+ added to every deploy; only used by HB Product Center CLIP |
| A2 | Document Lakebase app resource configuration | `[~]` | 2026-03-28 | `app.yml` has resources; `development-guide.md` needs Section 13 |
| A3 | Add rate limiting (`slowapi`) on public endpoints | `[ ]` | — | `/identify` endpoint could generate expensive SQL warehouse load |
| A4 | Add request logging middleware | `[ ]` | — | Structured logging: endpoint, method, user identity, status, latency |

## P4 — Testing

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| T1 | Security-focused tests (SQL injection payloads) | `[ ]` | — | `tests/projects/test_hb_security.py` |
| T2 | Chat streaming tests (shared utility) | `[ ]` | — | `tests/common/test_streaming.py` |
| T3 | API contract tests (proper status codes) | `[ ]` | — | `tests/common/test_api_contracts.py` |
| T4 | Integration test for Lakebase credential rotation | `[ ]` | — | `tests/integration/test_lakebase.py` |

## P5 — Documentation & DevEx

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| D1 | Update `development-guide.md` (Sections 13-15) | `[ ]` | — | App Resources, Migration Playbook, Security Checklist |
| D2 | Add `.env.example` with all required variables | `[ ]` | — | Currently only `.env` exists (gitignored) |
| D3 | Update README with current 5-accelerator list | `[ ]` | — | README only lists 3 accelerators |

## P6 — Migration Cleanup

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| M1 | Fix `migrate_full.py` OLD_CATALOG default | `[~]` | 2026-03-28 | Migration done but script default still wrong |
| M2 | Clean `__dist__` build artifacts from git | `[ ]` | — | ~130 tracked files that should be in `.gitignore` |
| M3 | Remove superseded `scripts/migrate_uc_data.py` | `[ ]` | — | Replaced by `migrate_full.py` |

---

## New Accelerator — AECO Digital Twin [Phase: Planned]

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| N1 | Finalize data model & Nemetschek brand mapping | `[ ]` | — | Plan: `docs/projects/aeco-digital-twin-plan.md` |
| N2 | Backend: project scaffolding + seed data | `[ ]` | — | Follow standard layout in `projects/` |
| N3 | Frontend: routes + dashboard pages | `[ ]` | — | — |
| N4 | Databricks integration (dashboards, agents) | `[ ]` | — | — |

---

## Summary

| Priority | Total | Done | Open |
|----------|-------|------|------|
| P0 Security | 4 | 3 | 1 |
| P1 Error Handling | 3 | 1 | 2 |
| P2 Code Quality | 4 | 1 | 3 |
| P3 Architecture | 4 | 0 | 4 |
| P4 Testing | 4 | 0 | 4 |
| P5 Documentation | 3 | 0 | 3 |
| P6 Cleanup | 3 | 0 | 3 |
| New (AECO) | 4 | 0 | 4 |
| **Total** | **29** | **5** | **24** |
