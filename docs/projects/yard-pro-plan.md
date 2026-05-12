# yard-pro — Project Plan

> yard-pro is an AI gardening companion that turns connected-tool telemetry and yard imagery into a season-by-season care plan for homeowners.
> Industry: consumer outdoor power equipment / connected products.
> What the prototype demonstrates: _(to be locked at end of Phase 1)_.
>
> **Customer inspiration (obfuscated CI — internal only):** Stihl. Per `docs/ci-implementation-plan.md` §2, the runtime UI and customer-facing artifacts MUST NOT name Stihl. Branding is brand-*adjacent*, fonts are open-source Google Fonts, wordmark = `yard-pro` only.

---

## 1. Vision & Problem

- **Problem statement:** Martin's last season *is* the problem statement. He **(a) missed the apple-tree winter pruning window by 3 weeks**, **(b) over-fertilized the lawn in May** because the almanac said so and his local weather didn't agree, and **(c) let a leaf-spot fungus spread for 10 days** before he diagnosed it from a Reddit thread. Each failure is independently observable; together they reveal that his yard runs on stale memory and mistimed generic advice. The current alternative is a stack of brand-specific apps + paper notebook + Reddit + occasional pro visits — fragmented enough that no single source ever closes the loop between *what's happening in the yard*, *what should be done next*, and *which tool/consumable Martin already owns to do it*.

- **Primary persona — "Martin, 52":** Enthusiast gardener. Lives outside Stuttgart. 900 m² yard: 400 m² lawn, a 30 m beech hedge, 4 fruit trees (2 apple, 1 cherry, 1 plum), perennial border. Owns a cordless trimmer + hedge cutter + robotic mower (2021 model), plus one petrol chainsaw he uses ~4× a year. Two battery families across the cordless tools. Logs nothing — everything is in his head and a paper notebook in the shed. Knows plant names; doesn't know optimal pruning windows for *his* fruit varieties in *his* microclimate. Comfortable with smartphones, allergic to fragmented logins. Aesthetically cares — his yard is a hobby, not a chore.

- **Secondary persona — "Klaus, 38, dealer technician":** Stuttgart-area dealer (Stihl-adjacent in real life; "yard-pro authorized dealer" in the UI). Sells, services, and stocks consumables for ~200 active customers in a 30 km radius. Wants to (a) know which customers have aging connected tools likely to need service, (b) up-sell battery upgrades / robotic-mower service contracts, (c) see seasonal demand spikes a week ahead. Today's stack: SAP back-office + walk-ins; zero visibility into the actual yards his customers run. The dealer-side workflow is a P2 use case for yard-pro and the anchor for Genie.

- **Industry context:** Consumer outdoor power equipment is a ~€20B EU market with strong family-owned German brand presence. The category is shifting from petrol → battery and from passive tools → connected products (battery-pack telemetry, robotic mowers, app-pairing). Regulatory exposure is moderate: **GDPR is the binding rail** (yard imagery is personal data; geolocation likewise; voice/chat history bound to a household; aggregated-to-dealer flows require separate explicit consent). No safety-of-life regulation, but a strong consumer-trust bar (dealer relationships are sticky, brand promise = "premium German engineering"). Demand is highly **seasonal and weather-coupled** — peak engagement March-Oct, near-zero Dec-Feb.

## 2. Scope & Use Cases

| # | Use Case | In scope | Why / Why not |
|---|----------|----------|---------------|
| 1 | **State-of-the-yard cockpit** — one screen: connected-tool readiness (battery %, blade hours, oil, attachments) + plant inventory + last-actions log + weather-aware "today's window" | **Yes (P0)** | Closes the fragmentation pain; is the demo's anchor screen |
| 2 | **Personalized seasonal coach** — dynamic care calendar that adapts to local weather, Martin's plant list, and what he marked done. Chat-style "what should I do this weekend?" | **Yes (P0)** | Closes the timing pain; is the AI-moment headline |
| 3 | **Snap-and-diagnose** — Martin photographs a problem (yellow patch, fungus, weird insect, stunted growth). CV + KA returns diagnosis with confidence + next-step recommendation tied to the tools/products he already owns | **Yes (P0)** | Closes the diagnostics pain; visceral AI-moment; OEM hook (recommends product within Stihl-adjacent ecosystem) |
| 4 | **Tool-readiness nudges** — proactive: "battery hasn't been charged in 3 weeks", "trimmer blade past 40h since last sharpening", "robotic mower stuck in zone 3 — 35 min" | Yes (P1, simulated telemetry) | Demonstrates connected-product value; real telemetry deferred to integration phase |
| 5 | **Inventory & consumables** — knows what tools/products Martin has; suggests reorder timing (oil, lubricant, fertilizer, blade) | Yes (P1, lightweight) | Round-trips the OEM business model; can be a thin pass in v1 |
| 6 | **Dealer "talk to your data" Genie space** — Klaus opens a Genie space and asks "which of my customers have a robotic mower past 4 years old that hasn't been serviced this season?" Aggregated, anonymized customer telemetry feeds it. | Yes (P2, OEM-side anchor) | Anchors a B2B2C narrative without bloating the consumer P0; Genie load-bearing here, not in the consumer app |
| 7 | Multi-user / household sharing (Martin's spouse adds an entry) | No (deferred) | Adds auth/permissions; out of scope for single-persona demo |
| 8 | Direct dealer-network booking (pro service for the chainsaw) | No (deferred) | Real B2B2C integration; future phase |
| 9 | Voice-first ("Hey yard-pro, did it rain enough this week?") | No (deferred) | Cool but not load-bearing for the core pain |

- **Success criteria (each is observable in a ≤5-minute demo):**
  1. Open the app on a simulated Saturday morning. Cockpit first paint <1s on cold load. The "Apple tree fungus check overdue 4 days" string renders from a seeded action-log row dated 2026-05-08 — pass = inspect the seeded row and confirm the rendered string matches.
  2. Ask the coach "what should I do this weekend?" → personalized answer in <5s referencing Martin's plant list, the 7-day weather, and what he marked done last week.
  3. Snap a photo of a yellowing lawn patch → diagnosis returned within 15s with ≥1 confident finding ("fusarium blight, 82% confidence") and an action ("apply X-fertilizer — you have 2.5kg in inventory; switch off the robotic mower for zone 3 for 14 days").
  4. Mark "mowed lawn" → at least 2 named calendar entries in the next 28 days shift by ≥1 day, visible in the UI diff within 2s. Pass = before/after screenshot shows the deltas.
  5. Robotic-mower telemetry alert ("stuck in zone 3") appears in cockpit within 30s of simulated event.
  6. *(P2, dealer-side)* Klaus opens his Genie space, types "which customers have a robotic mower 4+ years old and no service this season" → SQL is generated, runs, returns ≥3 anonymized customer rows in <10s.

> **Phase 1 dissent (open for Phase 4 re-test):** The Skeptical PM sub-agent proposed cutting UC1 (cockpit) as a primary surface and folding it into UC2 as a sidebar — arguing two surfaces (coach + snap-diagnose) tell the full story and UC1 alone is just a dashboard. Founder kept UC1 as P0 on the grounds that the OEM-aligned narrative needs a "state of your yard" anchor screen where telemetry, plant inventory, and the action log converge. Phase 4 (pragmatic-EM sub-agent) is the right place to re-evaluate this call after architecture and effort cost are concrete.

- **Non-negotiables:**
  - **Privacy (GDPR).** Yard photos, location, household chat history are personal data. Data minimization, explicit consent, deletion endpoint, EU-region storage.
  - **Dealer data-sharing is opt-in and irreversibly anonymized.** Aggregation to the dealer Genie space is opt-in per household; anonymization is irreversible at ingest; Klaus never sees identifiable Martin data unless Martin separately opts in for a specific service event.
  - **Diagnostic honesty.** No high-confidence answers from a low-confidence model. If the CV model isn't sure, the UI says so and recommends a pro consultation — *advisory, not authoritative*.
  - **Brand-adjacency only.** Per `docs/ci-implementation-plan.md` §2: yard-pro wordmark + open-source Google Font + brand-adjacent palette. No Stihl marks, no licensed fonts, no lifted photography.
  - **Seasonal-load tolerance.** System must scale 100× from Jan to July without burning idle cost — Lakebase Autoscaling scale-to-zero is load-bearing for the cost story.

## 3. Why Databricks (Differentiators)

- **Foundation Model API + Knowledge Assistant (KA)** — the seasonal coach (UC 2) needs current, grounded answers (plant species × region × season × weather). KA over a curated gardening corpus + FM API for natural-language chat is exactly the Databricks shape. Equivalent on a competitor stack = build/host an embedding pipeline + RAG infra + chat orchestrator separately.
- **Mosaic AI Model Serving with vision model** (UC 3 snap-and-diagnose) — plant disease / lawn / pest classification served as a versioned endpoint, callable from the same workspace that owns the data. Equivalent elsewhere = SageMaker + custom inference + cross-account IAM headaches.
- **Lakebase Autoscaling (scale-to-zero)** — UC 1/4 OLTP state (tool inventory, plant list, action log, telemetry events). Consumer-app load is 100× seasonal swing; scale-to-zero is the cost story. Equivalent elsewhere = RDS provisioned + aggressive autoscaler tuning, never truly to zero.
- **Genie (dealer-side, UC 6)** — Klaus's "talk to your data" surface for the dealer panel. Aggregated, anonymized customer telemetry feeds a Genie space the dealer queries in natural language to drive service + up-sell. Anchors the B2B2C story and is the only place Genie appears (deliberately scoped — not a consumer feature).

- **First-principles check:**
  - **If we removed the AI:** A state-of-the-yard cockpit + a manual seasonal log is still mildly useful — but the coach (UC 2) and snap-and-diagnose (UC 3) collapse to nothing, and 2 of 3 demo moments die. The AI is load-bearing, not decorative.
  - **If we removed the cloud:** Minimal core = a phone app with a local SQLite of tools + plants + a static almanac. Loses the weather-coupling, the CV model, the chat coach, the cross-device sync, and the entire dealer flow. Workable for a single power user; not a product.
  - **Smallest demoable version:** One screen. Upload a yard photo → KA-grounded coach returns a 3-bullet "what to do this weekend" answer that names a plant in the photo, the local 7-day weather, and one specific action. No cockpit, no calendar, no telemetry, no second screen, no dealer. If that single interaction doesn't make a customer lean in, the bigger plan won't either.

---

## 4. System Architecture

Three layers in P1-P3 — Presentation, Application, Data. A fourth "Edge" layer is introduced in P4 only; until then, telemetry is generated in-process and persisted directly, with no separate runtime boundary. Dealer flow (P5) reuses the same layers and adds a small admin sub-surface plus an anonymization pipeline.

```
+---------------------------------------------------------------+
|  Presentation (React + TanStack Router)                       |
|  /projects/yard-pro                                           |
|    ├── index.tsx           cockpit (UC1)                      |
|    ├── coach.tsx           coach chat (UC2)                   |
|    ├── diagnose.tsx        snap-and-diagnose (UC3)            |
|    ├── calendar.tsx        personalized calendar (UC2)        |
|    ├── inventory.tsx       tools + consumables (UC4, UC5)     |
|    └── dealer/             dealer panel (UC6, P5)             |
+---------------------------------------------------------------+
                              │ HTTPS (OAuth, X-Forwarded-User)
                              ▼
+---------------------------------------------------------------+
|  Application (FastAPI, src/innovation_factory/backend/        |
|               projects/yard_pro/)                             |
|    routers/  yards · plants · tools · inventory · actions     |
|              coach · diagnose · dealer (P5)                   |
|    services/ yard_context_service  ← typed YardContext        |
|                                      (plants + tools + log    |
|                                      tail + weather window)   |
|                                      consumed by coach + cal  |
|              coach_service         ← KA + FM API              |
|              diagnose_service      ← Mosaic AI Vision client  |
|              calendar_service      ← regenerate-on-write      |
|              telemetry_service     ← P1-P3: in-process        |
|                                      synthesizer writing      |
|                                      yp_tool_readiness        |
|                                      P4: swap to Zerobus      |
|                                      gRPC client              |
|              aggregation_service   ← anonymize → Gold (P5)    |
+---------------------------------------------------------------+
              │ SQLAlchemy             │ REST          │ REST
              ▼                        ▼               ▼
+--------------------+   +-----------------+   +-----------------+
| Lakebase Autoscale |   | Mosaic AI Vision|   | KA over Vector  |
| OLTP — yp_*        |   | endpoint        |   | Search index    |
| (scale-to-zero)    |   | (plant/lawn CV) |   | (gardening KB)  |
+--------------------+   +-----------------+   +-----------------+
              │
              │ Lakehouse Sync (Lakebase → Delta)
              ▼
+---------------------------------------------------------------+
|  Data (Unity Catalog)                                         |
|    Delta Bronze   raw telemetry, photo refs, coach transcripts|
|    Delta Silver   cleaned + plant/region joins                |
|    Delta Gold     anonymized aggregates → Genie space (P5)    |
+---------------------------------------------------------------+

[Edge layer — P4 only, not present in P1-P3]
  Robotic mower / battery telemetry → Zerobus gRPC → Delta Bronze
  Until P4, all telemetry is generated inside the Application layer.
```

**Responsibilities per layer:**
- **Presentation** — Render-only; never holds business logic. Suspense + Skeleton everywhere (per CLAUDE.md frontend rules). Theming via `<ProjectThemeScope slug="yard-pro">`.
- **Application** — FastAPI routers thin; logic lives in `services/`. Every route has `response_model` + `operation_id` (lessons §13). Coach + diagnose stream SSE via shared `services/streaming.py` (lessons §12). `yard_context_service` is the single source of truth for what the AI sees about Martin's yard — both `coach_service` and `calendar_service` consume the same typed `YardContext` object so they can't drift.
- **Data** — OLTP in Lakebase (consumer reads/writes; small, snapshot-shaped tables), analytical in Delta (telemetry-at-volume + dealer aggregates). Unidirectional Lakebase → Delta via Lakehouse Sync; never the other way. Vector Search hosts the gardening knowledge base for KA.
- **Edge (P4 only)** — Documentation, not architecture, until P4. The "Edge" box deliberately sits outside the main diagram in P1-P3 to make this honest. P4 swaps the in-process synthesizer for a Zerobus gRPC ingestion client; real devices (or a SIM) emit events that land directly in Delta Bronze, bypassing Lakebase.

## 5. Data Model

### OLTP (Lakebase) — table prefix `yp_*`

| Table | Purpose | Notable columns |
|-------|---------|-----------------|
| `yp_yards` | One per household | `id`, `display_name`, `region_code`, `lat`, `lng`, `size_m2`, `metadata` JSONB |
| `yp_plants` | Plant inventory per yard | `id`, `yard_id`, `species`, `variety`, `planted_at`, `notes` |
| `yp_tools` | Tools owned per household | `id`, `yard_id`, `kind` (trimmer/hedge/mower/chainsaw/blower), `model_year`, `battery_family`, `last_serviced_at` |
| `yp_consumables` | Consumables stock | `id`, `yard_id`, `kind`, `quantity`, `unit`, `last_restock_at` |
| `yp_action_log` | Append-only events | `id`, `yard_id`, `action_type`, `target_plant_id?`, `tool_id?`, `consumable_id?`, `occurred_at`, `notes` |
| `yp_diagnoses` | CV diagnostic results | `id`, `yard_id`, `photo_uri`, `model_version`, `predictions` JSONB, `top_confidence`, `accepted_label?`, `status` |
| `yp_calendar_entries` | Coach-generated plan | `id`, `yard_id`, `title`, `scheduled_at`, `target_plant_id?`, `tool_id?`, `status`, `generated_by_run_id` |
| `yp_tool_readiness` | Latest readiness snapshot per tool (one row per `yp_tools.id`, upserted) | `tool_id` PK, `battery_pct`, `blade_hours_since_sharpening`, `last_session_at`, `last_event_type`, `last_event_at`, `payload` JSONB |
| `yp_dealer_relationships` | Household ↔ dealer + consent | `yard_id`, `dealer_id`, `consent_state`, `consent_at`, `revoked_at?` (P5) |

**Telemetry at volume lives in Delta, not Lakebase.** The raw event stream (potentially millions of rows by P4) is written to `yard_pro_bronze.telemetry_events` only. Lakebase holds *only* the upserted readiness snapshot per tool (`yp_tool_readiness`) which the cockpit and nudges service read on every page load. This split aligns with lessons §3 (PGlite < 10K) and §27 (`INSERT … SELECT FROM range(N)` writes into UC for high-volume seeding).

**Status enums (VARCHAR + CHECK, prefixed to avoid OpenAPI collisions — lessons §13):**
- `YardProActionType`: `mow` · `fertilize` · `prune` · `water` · `spray` · `plant` · `diagnose` · `other`
- `YardProDiagnosisStatus`: `pending` · `reviewed` · `acted_upon` · `dismissed`
- `YardProCalendarStatus`: `planned` · `done` · `snoozed` · `skipped`
- `YardProTelemetryEventType`: `battery_low` · `maintenance_due` · `stuck` · `session_started` · `session_ended`
- `YardProConsentState`: `none` · `pending` · `granted` · `revoked`

**Composite indexes — read paths first, then a write path:**
- `yp_action_log(yard_id, occurred_at DESC)` — cockpit "last actions" feed (read)
- `yp_calendar_entries(yard_id, status, scheduled_at)` — "what's next?" + "what's overdue?" (read)
- `yp_calendar_entries(yard_id, generated_by_run_id)` — calendar regeneration deletes-and-rewrites N entries with the same run_id; without this index the AI-write path full-scans (write)
- `yp_diagnoses(yard_id, created_at DESC)` — diagnose history (read)
- `yp_dealer_relationships(dealer_id, consent_state)` — dealer-side filtering (read)
- Primary key on `yp_tool_readiness(tool_id)` covers the per-tool snapshot upsert; no secondary index needed.
- **JSONB columns intentionally have no GIN index** — `yp_yards.metadata` and `yp_diagnoses.predictions` are written and read by `id`, not queried inside. Add GIN only when a query needs it.

### Analytical (Delta) — UC catalog `yard_pro`

- **Bronze:** `yard_pro_bronze.telemetry_events`, `yard_pro_bronze.diagnoses_raw`, `yard_pro_bronze.coach_transcripts` (PII bound to consent flag)
- **Silver:** `yard_pro_silver.tool_health` (telemetry rolled to per-tool daily KPIs), `yard_pro_silver.yard_state` (combined yard + plant + action snapshot)
- **Gold (dealer-facing, anonymized):** `yard_pro_gold.dealer_customer_summary` — yard size bucket + region bucket + tool inventory hash; never raw lat/lng or names. Feeds the Genie space.

### Vector Search — `yard_pro_gardening_kb`

Storage-optimized endpoint. Sources in `ka_docs/`:
- Plant-care manuals (per species)
- Regional almanac fragments (Stuttgart-area; expanded later)
- Consumables spec sheets (fertilizer N-P-K, oil grades, blade specs)
- Diagnostic playbooks (fungus → action; pest → tool; deficiency → consumable)

## 6. Implementation Phases

| Phase | Scope | Demoable on its own? | Dependencies |
|-------|-------|----------------------|--------------|
| **P1 — Foundation** | Lakebase schema (`yp_*`), seed (Martin's Stuttgart yard, 5 tools, 12 plants, 30-day action log), CRUD APIs, backend router registered under `/api/projects/yard-pro` | Yes — `apx dev start` shows seeded data via API docs | None |
| **P2 — Consumer UI surfaces (mocked AI)** | Cockpit (UC1) showing tools+plants+action log+telemetry; coach chat UI shell (UC2, fixed-string responses); snap-and-diagnose UI with seeded fixed responses (UC3) | **Internal only.** Clickable prototype for UX validation; the three AI moments return seeded fixed responses. Do NOT show P2 to a customer cold — P3 is the first customer-grade demo. | P1 |
| **P3 — AI live** | KA over gardening corpus (FM API + KA endpoint); vision endpoint (Mosaic AI Serving) wired to UC3; coach prompts include yard context + weather; calendar regeneration (UC2) on action-log writes | Yes — the headline AI moments now work end-to-end. **This is the first phase you'd put in front of a customer.** | P1, P2 |
| **P4 — Connected telemetry & nudges** | Telemetry synthesizer producing battery/blade/usage events into `yp_tool_readiness` + `yard_pro_bronze.telemetry_events`; readiness nudges (UC4); consumables suggestions (UC5); cockpit shows live tool state | Yes — completes the consumer demo loop | P1-P3 |
| **P5 — Dealer panel (UC6, P2 priority)** | Dealer-relationship table, consent endpoint, anonymization pipeline (Lakebase → Delta Bronze → Silver → Gold), Genie space deployed against `yard_pro_gold.dealer_customer_summary`, dealer admin route | Yes — adds the B2B2C narrative for OEM customer conversations. **Depends on P4 specifically because** `yard_pro_gold.dealer_customer_summary` rolls up real-shape telemetry; if P4 ships only a synthesizer the rollup still works, but the Klaus demo's credibility hinges on the rollup looking like a real fleet would produce. | P1-P4 |

Each phase has a one-line demo script that should land cold to a new viewer. The full demo script for the finished prototype is in §11 (Phase 4 will write that).

## 7. File Layout & Lessons Applied

```
src/innovation_factory/backend/projects/yard_pro/
  router.py                         # aggregates routers/, registered in backend/router.py
  models.py                         # SQLModel + Pydantic (3-model pattern; YardPro* enum prefix)
  databricks_config.py              # env-var endpoint IDs (KA, vision, Genie space); default ""
  seed.py                           # PGlite-safe: ~150 rows total (1 yard, 12 plants, 5 tools,
                                    # 8 consumables, 30 action-log entries, 5 calendar entries,
                                    # 3 telemetry events, 2 diagnoses)
  routers/
    yards.py                        # GET /yards/{id} cockpit data (UC1)
    plants.py                       # plant CRUD
    tools.py                        # tool CRUD + telemetry rollups (UC4)
    inventory.py                    # consumables CRUD (UC5)
    actions.py                      # action log: POST mark-done, GET history (UC1, UC2)
    coach.py                        # SSE streaming coach chat (UC2)
    diagnose.py                     # POST /diagnose (multipart photo upload, UC3)
    dealer.py                       # dealer endpoints (P5)
  services/
    yard_context_service.py         # typed YardContext shared by coach + calendar
    coach_service.py                # KA query + FM API response synthesis
    diagnose_service.py             # Mosaic AI Vision endpoint client + label mapping
    calendar_service.py             # personalized regenerate-on-write
    telemetry_service.py            # in-process synthesizer (P1-P3) writing yp_tool_readiness;
                                    # P4 swaps for Zerobus gRPC client writing Delta Bronze
    aggregation_service.py          # anonymize + project to yard_pro_gold.* (P5)
  ka_docs/                          # Knowledge Assistant source corpus — SINGLE corpus,
                                    # ingested into one Vector Search index yard_pro_gardening_kb.
                                    # Subdirectories below are organizational only; each chunk
                                    # carries a doc_type tag (plant_care | almanac | consumables
                                    # | playbook) used for filtered retrieval.
    plant_care/
    regional_almanac/
    consumables/
    diagnostic_playbooks/
  seed_uc_tables.py                 # per-project UC seed (mirrors mol_asm_cockpit pattern;
                                    # see TODO.md for follow-up to refactor aeco/hb the same way)

src/innovation_factory/ui/
  routes/projects/yard-pro/
    route.tsx                       # layout: <ProjectThemeScope slug="yard-pro">
    index.tsx                       # cockpit (UC1)
    coach.tsx                       # UC2 chat
    diagnose.tsx                    # UC3 photo upload + result card
    calendar.tsx                    # UC2 calendar
    inventory.tsx                   # UC5
    dealer/                         # P5
      route.tsx
      index.tsx
  styles/themes/
    yard-pro.css                    # NEW — Stihl-adjacent token overrides (light + dark)
  lib/
    brand-themes.ts                 # MOD — register slug "yard-pro"

scripts/
  yard_pro/
    deploy_ka.py                    # KA endpoint + Vector Search index
    deploy_vision.py                # Mosaic AI Vision endpoint
    deploy_genie_space.py           # Genie over yard_pro_gold.* (P5)
                                    # (UC seed lives in projects/yard_pro/seed_uc_tables.py,
                                    # NOT in scripts/, per the per-project pattern decision.)

tests/projects/yard_pro/
  test_models.py                    # 3-model pattern
  test_router_discipline.py         # response_model + operation_id (lessons §13)
  test_seed.py                      # PGlite seed under 10K rows (lessons §3)
  test_coach_sse.py                 # streaming protocol (lessons §12)
  test_diagnose_endpoint.py         # endpoint contract + "not configured" path (lessons §18)
  test_klaus_cannot_see_revoked_household_data.py  # P5 consent regression
                                    # (test name refers to the symptom, not the fix)
tests/ui/theme/
  test_no_customer_ref_in_dom.tsx   # NEW — renders ProjectThemeScope for every slug,
                                    # asserts no customerRef value (Stihl, Viessmann, etc.)
                                    # appears in document.body.innerHTML. Closes the
                                    # build-time-vs-runtime obfuscation gap.
```

### Lessons applied (cite ≥5 — methodology requirement)

| Lesson | Where it applies in yard-pro |
|--------|------------------------------|
| **§3 PGlite memory limits** | `seed.py` keeps total seeded rows < 200; high-volume telemetry seeded only in `seed_uc_tables.py` (Delta side) |
| **§5 Env var config** | `databricks_config.py` defaults all endpoint IDs to `""`; `databricks_config_for_local()` returns sentinels; production reads from `databricks.yml` resource bindings |
| **§9 SQL injection / UC Statement allowlist** | Dealer admin queries that bypass Genie (rare) use `_validate_column()` + `_escape_like()`; Genie itself owns the NL→SQL layer |
| **§10 Lakebase OAuth rotation** | Inherited from `runtime.py`; load-bearing for the cost story in §3 |
| **§12 Shared streaming + error handling** | `coach.py` and `diagnose.py` use `services/streaming.py` for SSE + uniform 4xx/5xx surfaces |
| **§13 Response model + operation_id discipline** | Every router function in `routers/` has both; regression test `test_router_discipline.py` enforces |
| **§14 torch optionality** | Vision served via Mosaic AI Serving endpoint — backend calls the endpoint, never `pip install torch` |
| **§18 "Not configured" first-class** | Missing `YARD_PRO_VISION_ENDPOINT` renders a "Snap-and-diagnose requires configuration" card, not a 500 |
| **§20 XSS SafeMarkdown** | Coach's markdown responses rendered through SafeMarkdown; user-supplied yard notes sanitized at the API boundary |
| **§21 Rate-limit keying** | `/diagnose` (file upload) + `/coach/chat` (streaming) rate-limited per `X-Forwarded-User`, not IP |
| **§22 Shared `Pagination` dependency** | `actions.py` history endpoint uses the shared pagination dep |
| **§23 Canonical UC DDL** | `yard_pro_*` Delta tables defined in one `TABLES` dict consumed by `seed_uc_tables.py` and `deploy_*.py` scripts |
| **§27 INSERT…SELECT FROM range(N)** | Telemetry seeded server-side: ~100k rows in seconds for the cockpit live-load demo |
| **§28 Catalog-parameterize** | All `deploy_*.py` scripts read `--catalog` so the same scripts run in `fevm-felix-demo` and any other workspace |
| **§29 PGlite + psycopg + NullPool** | Already handled by `runtime.py` — no per-project pool config |
| **§32 `scripts/check_all.sh` per-phase gate** | Every phase's acceptance criterion includes `scripts/check_all.sh` exiting 0 against yard-pro routes (drift → type-check → tests → preflight → smoke). Without this, phases can each pass locally while the deployed app silently 401s. |
| **§34 KNOWN_DEBT allowlist** | `test_router_discipline.py` lands with `KNOWN_DEBT=set()` from day 1 — this is greenfield, no debt to grandfather in. Allowlist stays empty by policy. |

### Risk callout — KA corpus quality is risk #1

**The vision endpoint (UC3) is the visible AI moment, but the KA corpus (UC2) is the risk.** A Mosaic AI Vision endpoint either exists and serves predictions or it doesn't — well-trodden ground (lessons §14 covers the dependency story). The KA corpus is different: "apply X-fertilizer because Martin has 2.5 kg in inventory and his apple-variety + Stuttgart microclimate + 7-day forecast align" requires curated, region-tagged, season-tagged, plant-variety-tagged source documents that don't exist as a public dataset. A generic gardening corpus retrieves generic answers and the demo dies in the first chat turn.

**Derisking action (must complete before P3 wiring):**
1. Hand-author **20 seed answers** covering the demo's expected questions — weekend tasks, fungus diagnosis, fertilizer timing, pruning windows for apple/cherry/plum in Stuttgart, robotic-mower readiness, hedge maintenance.
2. Validate that KA retrieval over the curated `ka_docs/` corpus surfaces the right chunks for each.
3. If retrieval is wrong on more than 3 of 20, the corpus isn't ready — invest a week in curation before wiring FM API.

**Second-riskiest path: GDPR + dealer-aggregation consent surface (P5/UC6).** "Irreversibly anonymized at ingest" + "opt-in per household" + "Klaus never sees Martin unless Martin opts in for a specific service event" is three independent consent states and one anonymization pipeline. Building it inside P5 alone is tight. Derisking action: ship `yp_dealer_relationships` + the consent endpoint + a no-op `aggregation_service.anonymize()` function in **P1**, not P5, so the consent state machine is exercised by tests from day one. P5 then just plugs the real anonymizer into the existing pipe.

## 7.5 Customer CI Spec

### Customer CI Spec

| Aspect | Value |
|--------|-------|
| **Real customer (internal only)** | Stihl |
| **Obfuscated project name** | yard-pro |
| **Primary color (brand-adjacent)** | `#D9541F` — a deeper, red-shifted orange. Stihl's signature is `#F46717` (RAL 2004); ours sits ~6° lower in hue (toward red-brown) and ~12% lower in chroma in oklch space, reading as "industrial outdoor orange" without approximating the *registered* orange+grey combination mark. The bigger shift is deliberate: yard-pro is the only Innovation Factory accelerator whose reference brand owns a registered combination mark, so the visual delta has to be the largest of the six, not the smallest. |
| **Secondary / accent** | `#2B2F33` — graphite/anthracite near Stihl's housing grey but intentionally cooler/bluer than RAL 7016, to avoid the protected orange+grey pairing |
| **Tertiary (optional)** | `#F5F2EC` — warm off-white (not Stihl's RAL 9010); adds "premium German engineering" paper-feel without copying the pure-white logo background |
| **Typography (UI body)** | **Inter**, 400-600 — neutral, dashboard-practical; evokes the precise, engineering-minded character without imitating their proprietary wordmark. Already loaded for 3 other projects, so bundle stays small |
| **Typography (display / wordmark)** | **Saira Condensed**, 600-700 — bold, condensed, slight industrial flair; echoes Stihl's italicized condensed sans wordmark feel. Fallbacks: Oswald, Bebas Neue. Never set "YARD-PRO" at Stihl's specific ~12° italic lean |
| **Tone notes** | Warm industrial, German engineering, outdoor-professional. Premium-but-approachable: confident block headings, calm body copy, imagery cues of work/craft over consumer-glossy |
| **Sources** | • [Wikipedia — Stihl](https://en.wikipedia.org/wiki/Stihl) (history, positioning) <br>• [encycolorpedia — Stihl](https://encycolorpedia.com/companies/germany/stihl) (`#F46717` orange) <br>• [Fire & Saw — Stihl paint codes](https://fireandsaw.com/stihl-paint-colors/) (RAL 2004 / 9010 / 7016) <br>• [1000logos — Stihl](https://1000logos.net/stihl-logo/) (italic condensed sans wordmark character) <br>• [Lexology — Stihl trademark](https://www.lexology.com/commentary/intellectual-property/china/wan-hui-da-law-firm-intellectual-property-agency/stihl-obtains-registration-of-famous-orange-and-grey-colour-combination-mark) (orange+grey is a **registered combination mark** — explicit reason to shift and break the pairing) |

**Do NOT copy from Stihl's actual brand (hard rails on top of `ci-implementation-plan.md` §2):**
- Do not pair our primary orange with a warm grey at Stihl's RAL 7016 hue — that orange+grey combination is a **registered trademark** in multiple jurisdictions. Always break the pairing with the off-white `#F5F2EC` or a deep neutral.
- No italicized condensed all-caps wordmarks angled at Stihl's specific ~12° lean. No reproductions of their chainsaw/hedge-trimmer hero photography style. No "STIHL"-shaped five-letter horizontal lockup proportions.
- No forest/forestry-worker photography. No orange-on-grey machinery close-ups. Use abstract turf/yard motifs or schematic line art instead.

**Implementation hook:** add `yard-pro` entry to `src/innovation_factory/ui/lib/brand-themes.ts` (`customerRef: "Stihl"`, `fontUi: "Inter"`, `fontDisplay: "Saira Condensed"`, primary `#D9541F`, secondary `#2B2F33`). Create `src/innovation_factory/ui/styles/themes/yard-pro.css` with light + dark token overrides per the pattern in `ci-implementation-plan.md` §4.2. Wrap `routes/projects/yard-pro/route.tsx` with `<ProjectThemeScope slug="yard-pro">`. Add Saira Condensed `<link>` to `index.html` (Inter is already loaded).

**Build-time vs runtime obfuscation guard.** `customerRef: "Stihl"` is a TypeScript string consumed only by internal tooling and tests; it must never reach the DOM. Enforced by `tests/ui/theme/test_no_customer_ref_in_dom.tsx` (see §7 test list) — mounts `<ProjectThemeScope slug={slug}>` for every slug and asserts no `customerRef` value (Stihl, Viessmann, BSH Hausgeräte, MOL Group, Ströer SE, HB, Nemetschek Group) appears in `document.body.innerHTML`. Lands in P0.

---

<!-- Phase 3 (§8-10 Security/Resilience/Red team) and Phase 4 (§11-12 Use-case map/Final ordering) appear below as they're drafted. -->
