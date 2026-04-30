# Innovation Factory — Outstanding Work

> FEIP: [FEIP-5472](https://databricks.atlassian.net/browse/FEIP-5472)
> Last reviewed: 2026-04-24
> Source: [docs/tasks/refinement.md](tasks/refinement.md) (full audit details)
> Batch plan (now shipped): [docs/cleanup-and-improvement-plan.md](cleanup-and-improvement-plan.md)

Legend: `[ ]` open | `[x]` done | `[~]` partial | `[-]` won't do

---

## Batch status (2026-04-24)

| Batch | Scope | Status |
|-------|-------|--------|
| A | Repo cleanup, seed hygiene, CI skeleton, lessons-learned, plan doc | `[x]` shipped `96c7d93` |
| B | XSS sanitization, SQL-injection path removal, input sanitize + length bounds | `[x]` shipped `9d4ba1e` `2678cb9` `7a9487e` |
| C | Shared project-resource config, per-user rate limiting, shared pagination, torch optional | `[x]` shipped `eaea634` `1b4b105` `0f220ad` `fe7a9b3` |
| D | Streaming normalization, canonical UC DDL, MAS naming, hybrid migration, UAT personas, CI matrix, pagination sweep | `[x]` shipped `83bd585` `aefcf6f` `5ab16f6` `15a3730` `20a3a6d` `8aa2e7b` `aa06890` |

---

## P0 — Security

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| S1 | SQL injection fix in `uc_query_service.py` (allowlist sanitization) | `[x]` | 2026-03-28 | Commit `59286f3`. Added `_validate_column`, `_escape_like`, `search_like` |
| S2 | SQL injection fix in `recognition.py` LIKE clauses | `[x]` | 2026-03-28 | Commit `59286f3`. Callers updated to use safe query builder |
| S3 | Input length validation on `ProductIdentifyRequest` | `[x]` | 2026-03-28 | Commit `59286f3`. Pydantic `Field(max_length=500)` |
| S4 | Markdown XSS — add `rehype-sanitize` to frontend | `[x]` | 2026-04-23 | Commit `9d4ba1e` (B1). `SafeMarkdown` wrapper with `rehype-sanitize` applied repo-wide |
| S5 | Remove deprecated `where_raw` / `order_by_raw` SQL paths | `[x]` | 2026-04-23 | Commit `2678cb9` (B2). Public APIs no longer accept raw-SQL kwargs |
| S6 | Server-side sanitize + length-bound every free-text input | `[x]` | 2026-04-23 | Commit `7a9487e` (B3+B4). Pydantic `BeforeValidator` + `max_length` on every `*In` model |

## P1 — Error Handling & Robustness

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| E1 | Streaming chat error handling (try/except in SSE generators) | `[x]` | 2026-03-28 | Commit `a960d14`. Shared streaming utility handles this |
| E2 | Replace `assert` with `HTTPException` in chat routers | `[x]` | 2026-04-23 | Resolved during D1 streaming normalization (`83bd585`); no `assert` remains in request-handling code |
| E3 | Missing 404 on invalid query params in `mol_asm/stations.py` | `[ ]` | — | Invalid `region_id`/`station_type` returns empty list instead of 400 |

## P2 — Code Quality & DRY

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| Q1 | Extract shared chat streaming utility | `[x]` | 2026-03-28 | Commit `a960d14`. `backend/services/streaming.py` created |
| Q2 | Remove dead chat code in HB Product Center | `[ ]` | — | Session-based CRUD endpoints reference non-existent UC tables |
| Q3 | Deduplicate `databricks_config.py` shared values | `[x]` | 2026-04-23 | Commit `eaea634` (C1). `ProjectResourceConfig` collapses the five configs |
| Q4 | Reduce blanket `type: ignore` comments (~99 total) | `[ ]` | — | Replace with specific rule names; update `pyproject.toml` suppressions |
| Q5 | Normalize chat streaming across all 5 projects | `[x]` | 2026-04-23 | Commit `83bd585` (D1). Plain-text SSE + `[DONE]` sentinel + `SessionDep` everywhere |
| Q6 | Canonical UC DDL (single source of truth for table shapes) | `[x]` | 2026-04-23 | Commit `aefcf6f` (D2). `scripts/uc_schema.py` |
| Q7 | MAS sub-agent naming contract (snake_case + "Supervisor" suffix) | `[x]` | 2026-04-23 | Commit `5ab16f6` (D3). Regression test in `tests/scripts/test_mas_naming_convention.py` |

## P3 — Architecture Improvements

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| A1 | Make `torch`/`open-clip` optional dependency | `[x]` | 2026-04-23 | Commit `fe7a9b3` (C4). `[image-recognition]` extras group; build-time requirements rewrite keeps prod deploy unchanged |
| A2 | Document Lakebase app resource configuration | `[~]` | 2026-03-28 | `app.yml` has resources; `development-guide.md` needs Section 13 |
| A3 | Add rate limiting (`slowapi`) on expensive endpoints | `[x]` | 2026-04-23 | Commit `1b4b105` (C2). Per-user keying via `X-Forwarded-User`, IP fallback for local dev |
| A4 | Add request logging middleware | `[ ]` | — | Structured logging: endpoint, method, user identity, status, latency |
| A5 | Shared pagination dependency on list endpoints | `[x]` | 2026-04-23 | Commits `0f220ad` (C3) + `aa06890` (D7). All HB list endpoints now take `Pagination` |
| A6 | Hybrid DAB + Python workspace bootstrap | `[x]` | 2026-04-24 | Commit `15a3730` (D4). `scripts/bootstrap.py` orchestrates phases 1-9 + embedding-allowlist config |

## P4 — Testing

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| T1 | Security-focused tests (SQL injection payloads) | `[x]` | 2026-04-23 | Added alongside B2 (`2678cb9`). `tests/projects/hb_product_center/test_uc_query_security.py` |
| T2 | Chat streaming tests (shared utility) | `[x]` | 2026-04-23 | Commit `83bd585` (D1). `tests/common/test_streaming_protocol.py` |
| T3 | API contract tests (proper status codes) | `[~]` | — | Pagination contract covered in D7; 4xx/5xx contract sweep still open |
| T4 | Integration test for Lakebase credential rotation | `[ ]` | — | `tests/integration/test_lakebase.py` |
| T5 | MAS naming-convention regression test | `[x]` | 2026-04-23 | Commit `5ab16f6` (D3). `tests/scripts/test_mas_naming_convention.py` |
| T6 | CI matrix (Python 3.11 + 3.12, with/without `image-recognition`) | `[x]` | 2026-04-23 | Commit `8aa2e7b` (D6). `.github/workflows/ci.yml` |

## P5 — Documentation & DevEx

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| D1 | Update `development-guide.md` (Sections 13-15) | `[ ]` | — | App Resources, Migration Playbook, Security Checklist |
| D2 | Add `.env.example` with all required variables | `[ ]` | — | Currently only `.env` exists (gitignored) |
| D3 | Update README with current 5-accelerator list | `[ ]` | — | README only lists 3 accelerators |
| D4 | Persona-based UAT playbook | `[x]` | 2026-04-23 | Commit `20a3a6d` (D5). `docs/uat-personas.md` — 10 personas, 2 per accelerator |

## P6 — Migration Cleanup

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| M1 | Archive / replace `migrate_full.py` | `[x]` | 2026-04-23 | Moved to `scripts/archive/migrate_full.py` in `9489f11`; superseded by `bootstrap.py` + `deploy_agents_fevm.py` |
| M2 | Clean `__dist__` build artifacts from git | `[x]` | 2026-04-23 | Commit `9489f11`. Untracked and `.gitignore`'d |
| M3 | Remove superseded `scripts/migrate_uc_data.py` | `[x]` | 2026-04-23 | Removed in `9489f11` |

---

## Remaining work (by priority)

**P1 — nice to close next:**
- E3 — mol_asm/stations.py: return 400 on invalid `region_id`/`station_type`
- Q2 — delete dead HB chat CRUD endpoints referencing non-existent UC tables

**P2 — quality of life:**
- Q4 — replace blanket `# type: ignore` comments with named rules
- A4 — structured request-logging middleware
- T3 — full 4xx/5xx contract-test sweep
- T4 — Lakebase credential-rotation integration test

**P3 — documentation debt:**
- D1 — development-guide.md Sections 13 (App Resources), 14 (Migration Playbook), 15 (Security Checklist)
- D2 — `.env.example`
- D3 — README refresh to list all 5 accelerators

**P5 — backlog (post-AECO Hub):**
- B1 — delete unused Lakebase dev branch `dev-aeco-hub` on `fevm-felix-demo` (uid `br-dark-sun-d7t7sgls`). Created Phase 1 for schema iteration but the app reads/writes via PGlite locally and Lakebase production; the dev branch never got wired in. Keep until Phase 6 deploy is verified, then drop with `databricks postgres delete-branch projects/innovation-factory/branches/dev-aeco-hub -p fevm-felix-demo`.
- B2 — `tests/conftest.py` `DATABASE_URL` is missing `?uri=true` so SQLite treats `file:test_shared` as a literal filename, leaking a real `file:test_shared` into the repo root on each `pytest` run. Found Phase 2; deleted the stale file but didn't fix the root cause.

**P4 — lifts the ceiling, not the floor:**
- A2 — Lakebase config section in development-guide.md
- T-future — Playwright E2E smoke for each accelerator's golden path

---

## New Accelerator — AECO Hub [Phase: Shipped 2026-04-29]

All six phases from `docs/projects/aeco-hub-plan.md` complete:

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| N1 | Finalize data model & AECO tooling-ecosystem mapping | `[x]` | 2026-04-27 | Plan: `docs/projects/aeco-hub-plan.md` |
| N2 | Backend: project scaffolding + seed data (Phase 1) | `[x]` | 2026-04-27 | 27 tables, 23 enums, 1.3K-row Lakebase seed |
| N3 | Backend: lifecycle routers (Phase 2) | `[x]` | 2026-04-27 | 5 routers (issues / docs / design / build / operate) + 25 endpoints |
| N4 | UC tables + 500K sensor seed + 2 Genies + AI/BI dashboard (Phase 3) | `[x]` | 2026-04-27 | felix_demo_catalog.aeco_hub schema |
| N5 | KA + MAS supervisor + Tools / Marketplace / Agent UI (Phase 4) | `[x]` | 2026-04-28 | aeco_hub_supervisor (mas-7a265c24-endpoint) |
| N6 | Relationship graph + force-directed view + phase stepper (Phase 5) | `[x]` | 2026-04-28 | react-force-graph-2d, 227-edge seed |
| N7 | Deploy bundle to fevm-felix-demo + docs (Phase 6) | `[x]` | 2026-04-29 | App RUNNING at innovation-factory-7474658643170817.aws.databricksapps.com |

---

## Summary

| Priority | Total | Done | Open / Partial |
|----------|-------|------|----------------|
| P0 Security | 6 | 6 | 0 |
| P1 Error Handling | 3 | 2 | 1 |
| P2 Code Quality | 7 | 5 | 2 |
| P3 Architecture | 6 | 4 | 1 open + 1 partial |
| P4 Testing | 6 | 4 | 1 open + 1 partial |
| P5 Documentation | 4 | 1 | 3 |
| P6 Cleanup | 3 | 3 | 0 |
| AECO Hub | 7 | 7 | 0 |
| **Total** | **42** | **32** | **10** |
