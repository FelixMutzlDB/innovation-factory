# Innovation Factory — Outstanding Work

> FEIP: [FEIP-5472](https://databricks.atlassian.net/browse/FEIP-5472)
> Last reviewed: 2026-05-18
> Source: [docs/tasks/refinement.md](tasks/refinement.md) (full audit details)
> Batch plan (now shipped): [docs/cleanup-and-improvement-plan.md](cleanup-and-improvement-plan.md)

Legend: `[ ]` open | `[x]` done | `[~]` partial | `[-]` won't do

---

## Current State snapshot (2026-05-18)

> Relocated here from `CLAUDE.md` so it doesn't bloat the always-loaded file. Refresh the date when you update it.

| Area | Status |
|------|--------|
| **Accelerators** | 7 (ViDistrictOne, BSH Remote Assist, MOL ASM Cockpit, AdTech Intelligence, HB Product Center, AECO Hub, **yard-pro** — 7th, P0 + most of P1 + most of P2 shipped on `feature/yard-pro`) |
| **AECO Hub plan** | [projects/aeco-hub-plan.md](projects/aeco-hub-plan.md) — Phases 1-6 shipped 2026-04-29 |
| **yard-pro plan** | [projects/yard-pro-plan.md](projects/yard-pro-plan.md) — P0 + P1 + P2 dealer/compliance bundles shipped. Live on fevm-felix-demo at `innovation-factory-7474658643170817.aws.databricksapps.com`. Coach KA endpoint `ka-7598e04d-endpoint` + dealer Genie `01f152e6ba76129887a955cf08dd5c92` + dealer Lakeview dashboard `01f152f10628135caf9d41eed16c8b50` (published with `embed_credentials=true`) all live. Vision endpoint `yard-pro-vision-v1` still DEPLOYMENT_FAILED; `YARD_PRO_VISION_ENDPOINT` omitted from app config so diagnose modal renders the lessons §18 "not configured" card (pre-recorded session is served from the seeded `yp_diagnoses` rows for the demo). |
| **Brand themes** | [ci-implementation-plan.md](ci-implementation-plan.md) — P0–P3 shipped 2026-05-11/12: `BRAND_THEMES` registry (`ui/lib/brand-themes.ts`), `<ProjectThemeScope>` + 7 theme CSS files (yard-pro included), `<ProjectWordmark>` in sidebar, per-project light+dark chart palettes. WCAG AA contrast suite + Playwright visual regression at 0.5% effective tolerance gate the system. |
| **Database** | Lakebase Autoscaling (production), PGlite (local dev) |
| **Workspace** | `fevm-felix-demo` (migrated from `fe-sandbox-felix-demo-sandbox` → `fe-shared-demo`) |
| **Security** | SQL injection (§9), XSS (§20), rate limiting (§21) shipped; router-discipline lint added (D6); yard-pro adds GDPR Art. 22 review-and-confirm rail + Art. 17 cascade delete + EU AI Act Art. 50 advisory chip + RT-016 cross-tenant regression test |
| **Tests** | Security tests in place (input sanitize, markdown XSS policy, rate limit, streaming protocol, router discipline); yard-pro adds 144+ unit/integration tests + Playwright browser smoke; broader coverage on the 6 older accelerators still thin |
| **Branch** | `feature/yard-pro` (P2 mostly shipped — dealer panel UI + dashboard + Genie space + compliance; remaining: UC row-level filter for multi-dealer scope, Y28 cold-start benchmark, vision endpoint provisioning) |

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
| Q2 | Remove dead chat code in HB Product Center | `[x]` | 2026-05-11 | Q1 codebase grooming pass: dropped `HbChatSessionOut`, `HbChatMessageOut`, `HbChatSessionCreate` from `models.py`. Routes themselves were already removed earlier (HB chat router only exposes the MAS streaming endpoint). |
| Q3 | Deduplicate `databricks_config.py` shared values | `[x]` | 2026-04-23 | Commit `eaea634` (C1). `ProjectResourceConfig` collapses the five configs |
| Q4 | Reduce blanket `type: ignore` comments (~99 total) | `[ ]` | — | Replace with specific rule names; update `pyproject.toml` suppressions |
| Q5 | Normalize chat streaming across all 5 projects | `[x]` | 2026-04-23 | Commit `83bd585` (D1). Plain-text SSE + `[DONE]` sentinel + `SessionDep` everywhere |
| Q6 | Canonical UC DDL (single source of truth for table shapes) | `[x]` | 2026-04-23 | Commit `aefcf6f` (D2). `scripts/uc_schema.py` |
| Q7 | MAS sub-agent naming contract (snake_case + "Supervisor" suffix) | `[x]` | 2026-04-23 | Commit `5ab16f6` (D3). Regression test in `tests/scripts/test_mas_naming_convention.py` |

## P3 — Architecture Improvements

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| A1 | Make `torch`/`open-clip` optional dependency | `[x]` | 2026-04-23 | Commit `fe7a9b3` (C4). `[image-recognition]` extras group; build-time requirements rewrite keeps prod deploy unchanged |
| A2 | Document Lakebase app resource configuration | `[~]` | 2026-03-28 | `app.yml` has resources; App Resources section still owed in `docs/lessons-learned.md` (alongside §5 + §10) |
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
| D1 | Distribute App Resources / Migration Playbook / Security Checklist into `docs/lessons-learned.md` | `[~]` | 2026-05-11 | Migration Playbook covered in §25 (hybrid DAB + Python); Security Checklist partially covered in §9, §20, §21; App Resources section still owed |
| D2 | Add `.env.example` with all required variables | `[x]` | 2026-05-11 | `.env.example` tracked at repo root; M1.8 of 2026-05 revision added the 4 HB vector-search vars. New env vars must be added when new accelerators land (caught by M1 env-diff check). |
| D3 | Update README with current 6-accelerator list | `[x]` | 2026-05-11 | M1.6 of 2026-05 revision: added AECO Hub row. Future accelerators auto-flagged by M1 consistency-auditor. |
| D4 | Persona-based UAT playbook | `[x]` | 2026-04-23 | Commit `20a3a6d` (D5). `docs/uat-personas.md` — 10 personas, 2 per accelerator |
| D5 | PR template + per-PR revision checks | `[x]` | 2026-05-11 | `.github/PULL_REQUEST_TEMPLATE.md`; 5-item checklist from `docs/revision-checklist.md` |
| D6 | Router discipline CI lint + clear KNOWN_DEBT allowlist | `[x]` | 2026-05-11 | `tests/common/test_router_discipline.py` decorator-aware (skips `@streaming_endpoint`). All 10 originally-seeded debt entries cleared in the 2026-Q2 revision pass: 5 SSE chat routes migrated to `@streaming_endpoint`; 1 idea-chat + 3 file-upload + 1 anomaly-counts route typed via `response_model=dict[...]`. `KNOWN_DEBT` set is now empty; next violation fails CI immediately. |

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

**P2 — quality of life:**
- Q4 — replace blanket `# type: ignore` comments with named rules
- A4 — structured request-logging middleware
- T3 — full 4xx/5xx contract-test sweep
- T4 — Lakebase credential-rotation integration test

**P3 — documentation debt:**
- D1 — App Resources section owed in `docs/lessons-learned.md` (Migration Playbook → §25; Security Checklist → §9 + §20 + §21 — App Resources still open)

**P5 — backlog (post-AECO Hub):**
- B1 — delete unused Lakebase dev branch `dev-aeco-hub` on `fevm-felix-demo` (uid `br-dark-sun-d7t7sgls`). **READY TO DELETE** (Phase 6 merged to master 2026-05-11 via PR #5). Run: `databricks auth login --profile fevm-felix-demo && databricks postgres delete-branch projects/innovation-factory/branches/dev-aeco-hub -p fevm-felix-demo`.
- B2 — `tests/conftest.py` `DATABASE_URL` is missing `?uri=true` so SQLite treats `file:test_shared` as a literal filename, leaking a real `file:test_shared` into the repo root on each `pytest` run. Found Phase 2; deleted the stale file but didn't fix the root cause.
- B3 — Refactor `aeco_hub` + `hb_product_center` UC seed scripts to per-project pattern (mirror `mol_asm_cockpit/seed_uc_tables.py`). Today aeco/hb keep their UC seed in top-level `scripts/seed_uc_aeco_data.py` + `scripts/seed_uc_hb_data.py`; mol_asm and the new yard-pro accelerator use a per-project `projects/<slug>/seed_uc_tables.py`. Standardize on the per-project pattern so each project folder is self-contained. Decision logged 2026-05-12 during yard-pro Phase 2 planning.

**P4 — lifts the ceiling, not the floor:**
- A2 — Lakebase app-resource config section owed in `docs/lessons-learned.md`
- T-future — Playwright E2E smoke for each accelerator's golden path

**P6 — Q3 operational-drift follow-ups (2026-05-11 quarterly revision):**
- O1 — Verify no other orphan Lakebase branches: `databricks postgres list-branches projects/innovation-factory -p fevm-felix-demo`.
- O2 — Diff live UC tables vs `scripts/uc_schema.py::TABLES` (32 canonical). Drop orphan tables, add missing-schema tables. See `docs/revision-checklist.md` Q3 for the diff one-liner.
- O3 — Confirm deployed app `source_code_path` revision matches `master` HEAD. `databricks apps list -p fevm-felix-demo` and inspect.
- O4 — Audit `scripts/fevm_agents_state.json` (dashboards / genies / kas / mas) against live Databricks workspace IDs — any that 404 are orphans on disk.
- O5 — Run `uv tool run --from pip-audit pip-audit --skip-editable` from a network-enabled shell (this session couldn't reach PyPI). Capture any High/Critical findings as a separate P0 issue.

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

## New Accelerator — yard-pro (7th — Stihl-shaped AI gardening companion)

Plan: [docs/projects/yard-pro-plan.md](projects/yard-pro-plan.md). Tracked in PR #14 on `feature/yard-pro`.

### P0 — first customer-grade demo

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| Y1 | 4-phase plan via `/new-innovation-factory-project` | `[x]` | 2026-05-12 | Commits `0f41c80`-`4ad4758` (squash-merged to master as `e6af221`) |
| Y2 | Phase A foundation: 12 yp_* tables + seed (Martin's Stuttgart yard) | `[x]` | 2026-05-12 | Commit `565c1c2` |
| Y3 | Phase B1: CRUD routers + Art. 22 rail + RT-016 isolation | `[x]` | 2026-05-12 | Commit `0abd90c` — 39 regression tests |
| Y4 | Phase B2: AI surfaces (coach SSE + diagnose + calendar regen + provenance) | `[x]` | 2026-05-12 | Commit `02ce50e` — citation-required fallback for ungrounded recs |
| Y5 | Phase B3: cockpit + coach + Stihl-adjacent theme + AdvisoryChip + MarkAsDone | `[x]` | 2026-05-12 | Commit `6a576ff` — WCAG AA contrast pass for yard-pro |
| Y6 | Phase B4: UC schema + 22-doc KA corpus + deploy scripts | `[x]` | 2026-05-12 | Commit `97a422b` |
| Y7 | Deploy KA + Vision + UC tables to fevm-felix-demo | `[~]` | 2026-05-13 | KA `ka-7598e04d-endpoint` READY (retrieval verified on 3 sample prompts). UC tables seeded. Vision endpoint provisioning blocked — `YARD_PRO_VISION_ENDPOINT` temporarily blank so diagnose modal renders "not configured" card per lessons §18 |

### P1 — next sprint (extends to plan-phase P4)

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| Y8 | Playwright browser smoke + first-paint timing | `[x]` | 2026-05-12 | Commit `bb88865` — FCP 224-248ms |
| Y9 | Idempotency-Key 24h cache-replay on actions + diagnose | `[x]` | 2026-05-12 | Commit `22d122c` |
| Y10 | GDPR Art. 17 happy-path delete cascade (RT-025 regression) | `[x]` | 2026-05-12 | Commit `adaf5ff` — full-metadata enumeration so future yp_* tables are auto-covered |
| Y11 | Deployment runbook + app.yml/databricks.yml env wiring | `[x]` | 2026-05-12 | Commit `0267d9a` — `scripts/yard_pro/RUNBOOK.md` |
| Y12 | UC4 telemetry synthesizer + nudges (notifications-only, Art. 22 compliant) | `[x]` | 2026-05-12 | Commit `c3d3244` |
| Y13 | `yp_coach_feedback` UI + stats endpoint (5% auto-flag rule) | `[x]` | 2026-05-12 | Commit `e5536ff` |
| Y14 | Consumables reorder hints (UC5 polish) | `[x]` | 2026-05-13 | Commit `dca1009` |
| Y15 | Ensemble plausibility check on `confidence ≥ 0.8` (RT-002 follow-on) | `[x]` | 2026-05-13 | Commit `1b52cd5` (vision-resilience bundle) |
| Y16 | Per-dependency circuit-breaker thresholds | `[ ]` | — | Tune once we have real failure latency data |
| Y17 | Tier-2 diagnose-queue degradation path | `[x]` | 2026-05-13 | Commit `1b52cd5` (vision-resilience bundle) |
| Y18 | Log-canary CI test (`test_log_pipeline_no_pii.py`) | `[ ]` | — | RT-024 production hardening |
| Y19 | KA-extraction canary nightly job + verbatim cap (RT-008) | `[x]` | 2026-05-13 | Commit `01f60d9` — canary script + tests; nightly job-scheduler wiring still open |
| Y20 | `canary_cold_start.py` Lakebase Saturday-surge benchmark | `[ ]` | — | Closes plan Q2 |

### P2 — production hardening / dealer (extends to plan-phase P5)

| ID | Task | Status | Done | Notes |
|----|------|--------|------|-------|
| Y21 | Dealer panel UI (`/projects/yard-pro/dealer/*`) — UC6 | `[x]` | 2026-05-18 | Commits `90aa079` (initial) + `ef39152` (curated Genie questions) + `a9bd101` (dashboard embed) |
| Y22 | Consent state machine (`yp_dealer_relationships`) end-to-end | `[x]` | 2026-05-13 | Commit `90aa079` — endpoints + tests; live demo seed `3c93608` exercises pending→granted on Felix's yard |
| Y23 | Genie space over `yard_pro_gold.dealer_customer_summary` | `[x]` | 2026-05-18 | Commit `508906a` — space `01f152e6ba76129887a955cf08dd5c92` deployed via `scripts/yard_pro/deploy_genie_space.py` with 6 curated sample questions |
| Y24 | Anonymization pipeline (Lakebase → Delta Silver → Gold) production-grade | `[~]` | 2026-05-13 | Commit `90aa079` — aggregation_service + HMAC ingest wired; production-grade Spark job (replace in-process aggregation) still open |
| Y25 | GDPR Art. 15 (access) + Art. 20 (portability) export endpoints | `[x]` | 2026-05-13 | Commit `b9a0bfd` |
| Y26 | Log PII regex post-filter + canary CI | `[x]` | 2026-05-13 | Commit `b9a0bfd` — runtime filter shipped; canary CI test still pending (covers Y18) |
| Y27 | Retention/partition jobs for `yp_action_log` + Delta tables | `[x]` | 2026-05-13 | Commit `b9a0bfd` — `scripts/yard_pro/retention_jobs.py` |
| Y28 | Lakebase connection-pool sizing + `canary_cold_start.py` results applied | `[ ]` | — | Closes plan Q2 |
| Y29 | Saira Condensed self-host fallback | `[x]` | 2026-05-13 | Commit `1dd53bb` |
| Y30 | AI/BI dealer dashboard + Genie link + embed in dealer panel | `[x]` | 2026-05-18 | Commit `a9bd101` — `dashboard_dealer.json` published with `embed_credentials=true`; ID `01f152f10628135caf9d41eed16c8b50`; 48 anonymized rows in gold table for chart density |
| Y31 | UC row-level filter on `dealer_customer_summary` (RT-022 enforcement) | `[ ]` | — | Genie + dashboard still show all rows. Runbook §11 covers the `dealer_code = current_user_dealer()` filter; ship before exposing to a second dealer |

### P3 — deferred / depends on real customer

`[ ]` Real Edge / Zerobus integration · `[ ]` Multi-user / household sharing · `[ ]` Voice-first · `[ ]` Direct dealer-network booking · `[ ]` Batched-inference path for 100× scale · `[ ]` US launch (CCPA / state privacy) · `[ ]` Premium-tier real-time vision at 100× · `[ ]` Photo retention user-override

---

## Summary

| Priority | Total | Done | Open / Partial |
|----------|-------|------|----------------|
| P0 Security | 6 | 6 | 0 |
| P1 Error Handling | 3 | 2 | 1 |
| P2 Code Quality | 7 | 6 | 1 (Q4 type:ignore audit) |
| P3 Architecture | 6 | 4 | 1 open + 1 partial |
| P4 Testing | 6 | 4 | 1 open + 1 partial |
| P5 Documentation | 6 | 5 | 1 (D1 App Resources section) |
| P6 Cleanup | 3 | 3 | 0 |
| AECO Hub | 7 | 7 | 0 |
| **yard-pro P0** | 7 | 6 | 1 (Y7 vision endpoint partial) |
| **yard-pro P1** | 13 | 10 | 3 |
| **yard-pro P2** | 11 | 8 | 2 open + 1 partial |
| **Total** | **75** | **61** | **14** |
