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
  - **Privacy (GDPR).** Yard photos, location, household chat history are personal data. Data minimization, explicit consent, deletion endpoint, EU-region storage. (Art. 15/17/20 endpoints; see §8 for the implementation rows.)
  - **GDPR Art. 22 — review-and-confirm rail (added Phase 3 finding #11).** No solely-automated decisions with significant effect. Every coach recommendation and every UC4 telemetry nudge is advisory; the action is taken only when Martin clicks "Mark as done". Backend enforces this via the `human_confirmed_at` requirement on any `yp_action_log` write whose `source != 'user'`. **No "do it for me" affordance is permitted anywhere in the consumer app — this is a UI design invariant, not a configuration option.**
  - **EU AI Act — limited-risk classification (added Phase 3 finding #12).** Coach responses render an "AI-generated, advisory only" chip (Art. 50 transparency). Re-evaluate classification if scope ever expands to high-risk (professional/agricultural advice with economic-loss exposure).
  - **Dealer data-sharing is opt-in and irreversibly anonymized.** Aggregation to the dealer Genie space is opt-in per household; anonymization is irreversible at ingest; Klaus never sees identifiable Martin data unless Martin separately opts in for a specific service event.
  - **Diagnostic honesty.** No high-confidence answers from a low-confidence model. If the CV model isn't sure, the UI says so and recommends a pro consultation — *advisory, not authoritative*. Enforced at the response-shape level via mandatory citations on recommendation turns (§8) and an ensemble plausibility check on high-confidence vision outputs (§8).
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
| `yp_action_log` | Append-only events | `id`, `yard_id`, `action_type`, `target_plant_id?`, `tool_id?`, `consumable_id?`, `occurred_at`, `notes`, `idempotency_key?`, `source` ∈ {`user`, `coach_recommendation`, `telemetry_nudge`}, `human_confirmed_at?` (required when `source != 'user'` — Art. 22 invariant) |
| `yp_coach_feedback` | Per-response feedback for advisory feedback loop | `id`, `response_id`, `model_version`, `signal` ∈ {`thumbs_up`, `thumbs_down`}, `notes?`, `created_at` |
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
- `yp_action_log(yard_id, idempotency_key) WHERE idempotency_key IS NOT NULL` — UNIQUE partial; idempotency enforcement (write). Duplicate `Idempotency-Key` within 24h returns the original 2xx response from the cached row.
- `yp_calendar_entries(yard_id, status, scheduled_at)` — "what's next?" + "what's overdue?" (read)
- `yp_calendar_entries(yard_id, generated_by_run_id)` — calendar regeneration deletes-and-rewrites N entries with the same run_id; without this index the AI-write path full-scans (write)
- `yp_diagnoses(yard_id, created_at DESC)` — diagnose history (read)
- `yp_diagnoses(yard_id, idempotency_key) WHERE idempotency_key IS NOT NULL` — UNIQUE partial; same idempotency semantics for the diagnose write.
- `yp_dealer_relationships(dealer_id, consent_state)` — dealer-side filtering (read)
- Primary key on `yp_tool_readiness(tool_id)` covers the per-tool snapshot upsert; no secondary index needed.
- **JSONB columns intentionally have no GIN index** — `yp_yards.metadata` and `yp_diagnoses.predictions` are written and read by `id`, not queried inside. Add GIN only when a query needs it.

**Partitioning & retention** (append-only tables would grow unbounded at 100× × 5y ≈ 2.6B rows):
- `yp_action_log` — RANGE partitioned quarterly on `occurred_at`. Partitions > 24 months pruned to Delta cold storage.
- `yard_pro_bronze.coach_transcripts` — Delta partitioned by `date(created_at)`. `consent_flag=false` rows hard-deleted at 30 days; `consent_flag=true` rows aggregated and deleted at 13 months (GDPR purpose limitation).
- `yard_pro_bronze.telemetry_events` — Delta partitioned by `date(occurred_at)`. Raw retention 90 days; rollups in Silver/Gold are permanent.
- UC Volume photos — 180-day rolling delete per yard (documented in privacy notice; RT-019 promoted into this row).

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
| **P2 — Consumer UI surfaces (mocked AI)** | **Two routes only.** Cockpit (UC1) consolidates calendar (UC2) + inventory (UC5) + diagnose-result (UC3) as cards within the same route; coach chat (UC2) is the second route with fixed-string responses. Diagnose photo upload opens as a modal from the cockpit, no separate URL. | **Internal only.** Clickable prototype for UX validation; the three AI moments return seeded fixed responses. Do NOT show P2 to a customer cold — P3 is the first customer-grade demo. | P1 |
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
    index.tsx                       # cockpit (UC1) — consolidates UC2 calendar +
                                    # UC3 diagnose-result + UC5 inventory as cards
    coach.tsx                       # UC2 chat (the only second route)
    dealer/                         # P5 — separate route subtree
      route.tsx
      index.tsx
  components/yard-pro/              # NEW — cockpit's child cards
    calendar-card.tsx               # UC2 personalized calendar
    inventory-card.tsx              # UC5 tools + consumables
    diagnose-modal.tsx              # UC3 — opened from cockpit "Snap a photo" button
    advisory-chip.tsx               # "AI-generated, advisory only" chip (Art. 50, EU AI Act)
    mark-as-done.tsx                # human_confirmed_at affordance (Art. 22 invariant)
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

## 8. Security Architecture

yard-pro's threat surface is shaped by three things the other accelerators don't have to the same degree: **personal data at scale** (yard photos + geolocation + household chat history), **a cross-tenant data flow** (consumer → anonymized → dealer Genie), and **GDPR as the binding rail** rather than an aspirational checklist.

| Layer | Measure | Threat addressed |
|-------|---------|------------------|
| **API Gateway** | OAuth (Databricks Apps) + JWT + rate limiting keyed on `X-Forwarded-User` (lessons §21) + CSP/HSTS headers | API abuse, brute-force, XSS-via-header |
| **API Gateway** | Multipart upload limited to 10 MB; allowlist `image/jpeg` + `image/png` + `image/heic`; reject unknown MIME | Malicious file upload (RT-005) |
| **API Gateway** | EXIF strip on photo ingest; no GPS coordinates leave the upload pipeline | Geolocation leak via photo metadata (RT-005) |
| **Service-to-service** | Lakebase: `sslmode=verify-full`, OAuth token rotation via SQLAlchemy `do_connect` (lessons §10); Mosaic AI Vision + KA endpoints: workspace-scoped service principal | MITM, token theft, lateral movement |
| **Service-to-service** | Idempotency keys on `POST /actions` and `POST /diagnose` (write paths); deduplicated via `yp_action_log` | Replay attacks, double-fire on retry |
| **Data at rest** | Lakebase AES-256 (managed); Delta AES-256; photos stored in UC Volume with per-tenant prefix `yard_pro/photos/<yard_id>/...` | Disk-level exfil |
| **Data at rest** | Coach transcripts in `yard_pro_bronze.coach_transcripts` carry a `consent_flag` column; rows with `consent_flag=false` are excluded from any analytical query | Repurposing consumer chat for analytics without consent |
| **Data in transit** | TLS 1.3 end-to-end; HSTS preload | MITM |
| **Access control — consumer** | Lakebase Row-Level Security by `yard_id` derived from `X-Forwarded-User → yp_user_yards`; no cross-household reads or writes possible at the SQL layer | Cross-tenant leak (RT-016) |
| **Access control — dealer** | Klaus's Genie space sees only `yard_pro_gold.dealer_customer_summary`, which is the anonymized aggregate view. UC grants exclude all `yp_*` and all `yard_pro_bronze.*` / `yard_pro_silver.*` tables from Klaus's service principal | Dealer-side PII exposure (RT-003) |
| **Consent state machine** | `yp_dealer_relationships.consent_state` is the single gate; aggregation pipeline (`aggregation_service.anonymize`) reads it on every batch and excludes households with `consent_state != 'granted'`. State changes are append-only (no UPDATE on `consent_state`; new row on every transition) | Stale consent reads, race conditions on revoke (RT-012) |
| **Secrets** | All endpoint IDs (KA, Vision, Genie space) read from env vars via `databricks_config.py` defaulting `""` (lessons §5, §18); no hardcoded IDs in source | Key exposure |
| **Audit** | `yp_action_log` is append-only (no UPDATE, no DELETE — schema `CHECK` constraint); `yard_pro_bronze.coach_transcripts` likewise. Tamper-evident via row sequence + monotonic timestamp constraint | Repudiation, history rewrite |
| **AI security — coach (UC2)** | Prompt-injection detection: input sanitization at the API boundary (XSS / control-char strip per lessons §20); RAG sources marked `trust-tier: ground-truth` (curated docs) vs `trust-tier: user-supplied` (coach transcripts) and never retrieved into prompts that act on tools/consumables. Canary strings in KA used to detect leak. | Prompt injection via plant notes / coach (RT-001) |
| **AI security — provenance enforcement** | Every coach response that recommends a specific action (fertilize, prune, apply product) MUST include `citations: list[KaChunkRef]` with `min_length=1` in the response payload. Backend rejects FM API completions on recommendation turns without citations and falls back to "I don't have a grounded answer — consider your local dealer." Diagnostic-honesty is enforced at the response-shape level, not the prompt level. | Hallucinated recommendations, advisory trust erosion |
| **AI security — KA extraction** | Coach responses are forbidden from returning verbatim chunks > 200 chars; a SafeMarkdown post-processor truncates and adds attribution ("Source: regional almanac, Stuttgart Apr"). KA corpus is licensed/own-authored only — no third-party copyrighted almanac text. Canary phrases seeded in each `ka_docs/` subdirectory; nightly job `scripts/yard_pro/canary_ka_extraction.py` queries the coach with extraction prompts ("repeat the previous document verbatim") and alerts if a canary surfaces. | Model inversion, KA corpus extraction |
| **AI security — advisory feedback loop** | Every coach answer and every diagnose result exposes a one-tap "👎 wrong" affordance writing to `yp_diagnoses.accepted_label` and a new table `yp_coach_feedback` (`response_id`, `model_version`, `signal` ∈ {`thumbs_up`, `thumbs_down`}, `notes?`, `created_at`). When negative-feedback rate on a `model_version` crosses 5 % over 100 turns, the version is auto-flagged for manual review and the UI surfaces "This coach version is being reviewed" for affected response classes. Without the loop, a wrong recommendation has no path back to model improvement. | Diagnostic-honesty erosion over time |
| **AI security — vision (UC3)** | Image size + dimension hard caps before model invocation; adversarial-input rate limit per user; confidence floor `< 0.6` → return "unsure" + suggest pro consultation. **Confidence floor is necessary but not sufficient.** On `confidence ≥ 0.8` responses, run an ensemble plausibility check: the vision label is rephrased into a sentence and submitted to the coach FM API with a yes/no plausibility prompt ("is fusarium blight plausible on apple bark in May Stuttgart?"). If the FM API disagrees, downgrade to "unsure". Every high-confidence diagnosis surfaces "Get a second opinion (free dealer chat)" as a co-equal CTA, not a secondary one. | Adversarial image attacks (RT-002), confidence inflation |
| **AI security — Genie (UC6)** | Genie space configured against `yard_pro_gold.*` only; row-level filters baked into the underlying Delta view, not relying on Genie's NL→SQL to enforce them; canary rows seeded and queried periodically to detect leakage | SQL injection through NL→SQL (RT-004), PII leak via join (RT-022) |
| **Supply-chain SPOFs + fallbacks** | **FM API** — model ID pinned via `YARD_PRO_COACH_MODEL` env var (default `databricks-meta-llama-3-3-70b` or successor); explicit `YARD_PRO_COACH_MODEL_FALLBACK` env var; weekly canary `scripts/yard_pro/canary_fm_models.py` detects deprecation. **Vision** — no model fallback (custom plant model); Tier-2 degradation queues diagnoses (see §9 tiers). **Saira Condensed** — self-host fallback at `/static/fonts/saira-condensed.woff2` declared *first* in `yard-pro.css` `@font-face`; Google Fonts CDN is the secondary, not primary (customers behind corporate proxies routinely block `fonts.googleapis.com`). **`torch`** — confirmed not bundled; CI test `tests/projects/yard_pro/test_no_torch_import.py` asserts. **Lakebase scale-to-zero cold start** — documented budget p95 30 s, tested by `scripts/yard_pro/canary_cold_start.py`. | Vendor lock-in, deprecation, CDN block, dependency bloat |
| **DoS protection** | Vision endpoint: cost cap per service principal per day; coach SSE per-user concurrent connection cap; photo upload size-rate-limit | Vision endpoint cost runaway (RT-018), photo storage abuse (RT-019) |
| **GDPR Art. 15 (right of access)** | `GET /api/projects/yard-pro/yards/{id}/export` enqueues an async job that produces a signed-URL ZIP of all rows referencing `yard_id` across `yp_*`, all coach transcripts (consent permitting), all photos, all calendar history. SLA 30 days. | Subject Access Request fulfillment |
| **GDPR Art. 17 (right to be forgotten)** | `DELETE /api/projects/yard-pro/yards/{id}` cascades: Lakebase `yp_*` rows by `yard_id`; UC Volume `yard_pro/photos/<yard_id>/` prefix; Delta Bronze/Silver/Gold rows by `yard_id_hash` (anonymized rows are matchable by the hash but contain no PII); revokes `yp_dealer_relationships.consent_state` to `revoked`. Integration test asserts no row referencing the deleted `yard_id` survives. (Was RT-025.) | GDPR Art. 17 |
| **GDPR Art. 20 (data portability)** | Art. 15 export, but in a machine-readable JSON Schema documented in `docs/projects/yard-pro-data-export-schema.md`. Same async-job flow. | Data portability |
| **GDPR Art. 22 (no solely-automated decisions)** | **Load-bearing invariant.** The coach's "apply X-fertilizer" recommendation is advisory-only. The UI shows a "You are reviewing an AI suggestion" chip on every recommendation; the action is taken only when Martin clicks "Mark as done". Backend enforces this by requiring an explicit `human_confirmed_at` timestamp before any `yp_action_log` write whose `source='coach_recommendation'`. UC4 telemetry nudges are notifications, not auto-actions; every nudge needs the same Mark-as-done click. No "do it for me" affordance is permitted anywhere in the consumer app. | Solely-automated decisions, regulatory exposure |
| **EU AI Act (Art. 50, "limited risk")** | yard-pro is classified **limited risk** under the EU AI Act (in force in 2026 EU market): AI system interacting with natural persons. Transparency obligations: (a) every coach response renders an "AI-generated, advisory only" chip; (b) AI-generated images, if any, would be watermarked (N/A — none generated). **Not high-risk** — yard-pro does not make decisions about employment, credit, education, essential services, biometric ID, or critical infrastructure. **Re-evaluate** if scope expands to professional/agricultural advice with economic-loss exposure (e.g. commercial crop guidance). | EU AI Act compliance |
| **ePrivacy Directive** | Coach transcripts and yard photos are "communications content / terminal-equipment data" under ePrivacy. Single, granular opt-in at first login: "I consent to yard-pro processing my photos, chat, and tool telemetry for advisory features" — separately recorded from the dealer-aggregation consent in `yp_dealer_relationships`. Strictly-necessary cookies only; no third-party tracking; no analytics beacons to non-EU regions. | ePrivacy compliance |
| **CCPA / US state privacy** | **Out of scope.** yard-pro v1 is EU-only (Stuttgart pilot). A US launch would require separate review (CCPA, CPRA, state-by-state). Flagged in `docs/TODO.md` as a future scope item; not implemented in P0-P5. | Regulatory scope clarity |

## 9. Resilience Design Principles

- **Idempotency** — `Idempotency-Key` header is **required** on `POST /actions`, `POST /diagnose`, and `POST /coach/chat`. Enforced by the UNIQUE partial indexes in §5 (`yp_action_log` and `yp_diagnoses`). Absent or duplicate within 24 h returns the original 2xx response from the cached row. Coach SSE chunks are idempotent at the chunk level (re-streamable from `run_id`); `idempotency_key` gates the initial turn write only.
- **Circuit breaker — per dependency, not uniform.** External calls are wrapped via `services/circuit_breaker.py` with different thresholds:
  - **Vision (UC3)** — 3 `5xx` OR p95 latency > 8 s within a 60 s window → open 60 s, half-open with 1 probe.
  - **KA + FM API (UC2)** — 5 `5xx` within 30 s → open 30 s, half-open with 1 probe.
  - **Lakebase write** — **never** circuit-break; degrade to `503 Service Unavailable` with `Retry-After`. Breaking Lakebase writes silently corrupts the event-sourcing invariant.
  - **Genie (UC6)** — not wrapped; dealer panel tolerates direct failures (non-load-bearing demo surface).
- **Graceful degradation — explicit tiers.** Each tier names what works and what doesn't:

  | Tier | Failure | What still works | What's degraded |
  |------|---------|------------------|-----------------|
  | **0 (full)** | Nothing down | Everything | — |
  | **1 (KA / FM API down)** | Coach unreachable | Cockpit, calendar, diagnose | Coach chat returns "Coach offline — using cached weekly digest" from yesterday's last-good summary cached in `yp_coach_cache` |
  | **2 (Vision down)** | Diagnose endpoint unreachable | Cockpit, calendar, coach | `/diagnose` accepts upload, queues to `yp_diagnoses` with `status='queued'`; UI says "Diagnosis pending — we'll notify when back" |
  | **3 (Lakebase down)** | OLTP unreachable | Static cockpit from IndexedDB cache | All writes `503`; no AI features |
  | **4 (everything down)** | Cloud unreachable | Static brand page | No API |

  Dealer Genie space sits outside the tier table — its failure mode is "provisioning placeholder," never a `500`.
- **CQRS** — consumer writes go to Lakebase (OLTP); analytical reads (dealer Genie, internal observability) go to Delta; unidirectional `Lakehouse Sync` keeps Delta up to date. Never read consumer-facing queries from Delta.
- **Event sourcing** — `yp_action_log` is the audit + state-reconstruction source. Calendar regeneration reads it; coach context-builder reads it; dealer aggregation reads it. A new event always produces a new row; nothing is mutated in place.
- **Optimistic concurrency** — `yp_calendar_entries` carries an `etag` column; the regenerate-on-write path runs `DELETE … WHERE etag = ?` and writes the new run atomically. Conflicting writes lose loudly (409 with explanation), not silently.
- **Cold-path defenses** — KA reload is the cold-start risk (a several-second VS index warm-up on the first query of the day). Mitigation: a cron-warmed dummy query at 06:00 local time so Martin's Saturday-morning first query hits a warm index.

## 10. Red Team Summary

Findings below are intentional pre-build threat model; each cites the §8 row that mitigates it. "Open" entries are deliberately deferred to a later phase.

| ID | Threat | Severity | Mitigation |
|----|--------|----------|------------|
| RT-001 | Prompt injection via plant notes (`yp_plants.notes` field rendered to coach prompt) | High | §8 "AI security — coach": trust-tiered retrieval, control-char strip at API boundary, canary detection. Regression test: `test_plant_note_with_injection_payload_does_not_leak_to_coach`. |
| RT-002 | Adversarial image fooling the vision model into a high-confidence wrong diagnosis | **Critical** (re-rated 2026-05-12: confidence floor alone is insufficient — a 0.85-confidence wrong answer is the actual failure mode) | §8 "AI security — vision": confidence floor < 0.6 → "unsure"; **ensemble plausibility check on `confidence ≥ 0.8`** (vision label rephrased and sent to FM API for yes/no plausibility); per-user rate limit on diagnose endpoint; "Get a second opinion (free dealer chat)" surfaced as a co-equal CTA on every high-confidence diagnosis; advisory feedback loop (§8) closes the correction path. Diagnostic-honesty non-negotiable is the policy backstop. |
| RT-003 | Klaus sees raw Martin data via dealer Genie space | **Critical** | §8 "Access control — dealer": UC grants exclude all `yp_*` and `yard_pro_bronze/silver` from dealer SP; only `yard_pro_gold.dealer_customer_summary` is queryable. Regression test: `test_klaus_cannot_see_revoked_household_data` + a P5 integration test that asserts a row deleted from Lakebase no longer appears in Klaus's Genie results within sync latency. |
| RT-004 | SQL injection through Genie NL→SQL | High | §8 "AI security — Genie": row-level filter baked into the underlying Delta view; Genie's NL→SQL is sandboxed by UC permissions. |
| RT-005 | Photo upload — malicious filetype, EXIF GPS leak, oversize DoS | Medium | §8 "API Gateway": 10 MB cap, MIME allowlist, EXIF strip on ingest. |
| RT-006 | Rate limit bypass via header spoofing | Medium | §8 "API Gateway": `X-Forwarded-User` is set by the Databricks Apps proxy and not user-settable. Lessons §21 explicitly chose this over IP-based keying. |
| RT-007 | Lakebase OAuth token theft via process dump | Medium | §8 "Service-to-service": token rotated hourly per lessons §10; short window of usefulness. |
| RT-008 | Vision endpoint DoS via large image batch | Medium | §8 "DoS protection": cost cap per SP per day; per-user rate limit on `/diagnose`. |
| RT-009 | KA corpus poisoning (attacker contributes malicious docs) | Low (today) | KA corpus is curated, single-author at P3; no user-contributed sources. Promotion to High when/if community-contributed plant guides are added. **Open — re-evaluate before any user-contributed corpus.** |
| RT-010 | Calendar regen DoS via action-log spam | Medium | Per-user rate limit on `POST /actions`; regen is debounced (one regen per `yard_id` per 5 s). |
| RT-011 | Telemetry replay (replay an old "stuck" event to trigger a false alert) | Low | Telemetry events carry monotonic `occurred_at` and `tool_id`-scoped sequence numbers; replays rejected at ingest. P4 concern. |
| RT-012 | Stale dealer consent state — Klaus's query returns a household that revoked after query started | Medium | §8 "Consent state machine": append-only consent log; aggregation reads consent at every batch start; analytical query latency to revoke is bounded by sync interval (≤ 5 min documented SLA in the consent UI). |
| RT-013 | `customerRef` "Stihl" leaks into rendered DOM | Medium | §7.5 implementation note + regression test `test_no_customer_ref_in_dom.tsx`. |
| RT-014 | XSS in user-supplied notes rendered in coach output or cockpit | High | §8 "AI security — coach": SafeMarkdown (lessons §20); API-boundary sanitization for all user-supplied text fields. |
| RT-015 | CSRF on `POST /actions/mark-done` | Medium | Databricks Apps OAuth flow + same-origin + `SameSite=Strict` cookie. |
| RT-016 | Cross-tenant leak via `yard_id` from another household | **Critical** | §8 "Access control — consumer": Lakebase RLS by `yard_id` from `X-Forwarded-User`. Regression test `tests/projects/yard_pro/test_cross_household_isolation.py`: (a) seeds yard_A (user_A) and yard_B (user_B); (b) calls every `yp_*` endpoint with `X-Forwarded-User=user_A` AND `yard_id=yard_B` in path, body, and query — asserts `403` or empty result; (c) repeats for PATCH and DELETE; (d) attempts JSON-body `yard_id` override on `POST /actions` where the path doesn't include `yard_id` — asserts RLS wins over the body field. Lessons §9 SQL-injection allowlist pattern applies if any endpoint accepts `yard_id` as a literal in a constructed query. |
| RT-017 | KA cold-start latency erodes the "5s coach answer" success criterion | Medium | §9 "Cold-path defenses": cron-warmed dummy query at 06:00 local. |
| RT-018 | Vision endpoint cost runaway from one abusive user | Medium | §8 "DoS protection": cost cap per SP per day. |
| RT-019 | Photo-storage cost runaway / volume abuse | Medium | UC Volume size-quota alert; per-yard photo retention policy (180-day rolling delete) documented in the privacy notice. |
| RT-020 | Lakebase OAuth refresh failure cascade — all in-flight requests fail | Medium | Lessons §10 handles single-token rotation; additional retry-once on `do_connect` with exponential backoff. |
| RT-021 | Edge synthesizer (P1-P3) feedback loop — telemetry triggers nudge triggers action triggers more telemetry | Low | Synthesizer is one-way; the action-log → telemetry path is explicitly absent. P3 acceptance gate: `scripts/yard_pro/check_no_telemetry_feedback.py` static-analysis grep asserts `action_log` writers are not invoked from `telemetry_service.py` code path. Test fails CI if a future change wires the loop. |
| RT-022 | Genie SQL leaks PII through an unintended JOIN to a non-anonymized table | **Critical** | §8 "Access control — dealer": Klaus's SP has UC `SELECT` only on `yard_pro_gold.*`; cannot reach `yard_pro_bronze/silver` even if Genie's NL→SQL tried. |
| RT-023 | Dealer brute-forces consent state by probing for which households appear | Medium | Anonymization at ingest means dealer never sees `yard_id` — only `yard_id_hash` (HMAC with rotating secret). Brute-force search of the hash space is computationally infeasible. |
| RT-024 | Logs leak yard photos or coach transcripts | **Critical** (re-rated 2026-05-12: GDPR Art. 32 "security of processing" violation = up to €20M / 4 % global turnover; geotagged yard images = PII, coach transcripts may reveal health-of-household details) | Belt-and-suspenders: (a) name-based field exclusion in structured logger (`photo_uri`, `predictions`, `coach_transcript_chunk`, etc.); (b) regex post-filter on log emission for base64 image data, UUID-shaped photo refs, and multi-line text blocks >500 chars; (c) **log-pipeline assertion test** `tests/projects/yard_pro/test_log_pipeline_no_pii.py` runs the diagnose + coach happy paths and greps the emitted log stream for a known canary photo URI and a known canary transcript phrase — fails CI if either appears. |
| RT-025 | GDPR delete endpoint misses a table — orphan rows survive | High | §8 "GDPR right-to-be-forgotten": integration test enumerates all tables in `scripts/uc_schema.py::TABLES` + Lakebase `yp_*` + UC Volume prefix; asserts zero rows referencing the deleted `yard_id` after the delete. Lessons §23 (canonical UC DDL) makes the enumeration tractable. |

### Phase 3 scale assumptions

- **Per-household, peak season:** ~50 coach turns/week, ~10 photos/week, ~30 calendar entries active, ~5 tools generating ~100 telemetry events/week (P4). At 1k households → 50k coach turns/wk, 10k photos/wk, ~300k telemetry events/wk.
- **Dealer side:** 1 dealer queries ~10× per business day, mostly aggregate counts. Negligible.
- **At 10× — Saturday-morning peak is the real stress test.** Sustained averages don't capture March-Oct, 09:00-11:00 local: coach turns spike **8-12× the weekly average → ~8-12 turns/sec sustained for 2 hours**. Each turn writes to `yp_action_log` (event-sourcing rail in §9) and into `yard_pro_bronze.coach_transcripts` via Lakehouse Sync. The UNIQUE partial index on `(yard_id, idempotency_key)` plus the `(yard_id, occurred_at DESC)` BTree must be benchmarked at **50 writes/sec/yard worst case** (concurrent diagnose + action + coach). Lakebase connection pool default of 10 per app instance is insufficient; size to `(max_concurrent_app_workers × 2)`. **Open question: does Lakebase scale-to-zero handle the 09:00 surge, or does the first user eat a 30-60 s wake?** P4 acceptance includes `scripts/yard_pro/canary_cold_start.py` and a synthetic-load test against the partial index.
- **At 100× (100k households):** real-time vision economics break — ~$0.02/inference × 10k photos/hour at peak ≈ $200/hr. **This is a re-scope, not a free optimization.** Batched path: photos enqueue to `yard_pro_bronze.diagnose_queue`; vision inference runs every 60 s on batches of 32-128; latency budget shifts from <15 s (UC3 success criterion #3) to <2 min — **explicitly breaking UC3's success criterion**. Premium tier could keep real-time. Out of P0-P5 scope; flagged for the OEM business-model conversation, not the technical phase plan.

### Edge cases explicitly enumerated

- **Offline:** Consumer app caches the cockpit's last `/yards/{id}` payload in IndexedDB; coach degrades to "available offline soon" message; photo upload queues locally.
- **Partial failure:** Vision endpoint down but KA up → `/diagnose` returns "diagnosis unavailable, here's a general care reminder from KA". Coach down but cockpit up → cockpit still loads; chat button shows "Coach is offline".
- **Conflicting writes:** Two devices simultaneously mark the same calendar entry done → optimistic concurrency (§9) returns 409 to the loser; UI shows "Already marked done from another device".
- **GDPR delete during analytical sync:** Delete may take up to one Lakehouse-Sync interval to propagate to Delta Bronze/Silver/Gold; documented in privacy notice. Dealer query result therefore lags real-time consent revoke by ≤ 5 min.

---

## 11. Use Case Coverage Map

Every use case from §2 mapped here. No silent omissions.

| # | Use case from §2 | Plan phase | Status | Simplification / deferral notes |
|---|------------------|-----------|--------|---------------------------------|
| 1 | State-of-the-yard cockpit | P1 (data) + P2 (UI) | **In scope, complete — consolidates calendar (UC2) + inventory (UC5) + diagnose-result (UC3) as cards within the same route** | First customer-grade demo lands when P3 ships. Phase 1 dissent resolved by consolidation, not by cutting (see below). |
| 2 | Personalized seasonal coach | P3 (AI live) | **In scope, complete** | Requires the 20 hand-authored seed answers from §7 KA-risk callout *before* P3 wiring |
| 3 | Snap-and-diagnose | P3 (AI live) | **In scope, complete — opens as a modal from the cockpit, not a separate route** | Confidence floor + co-equal "second opinion" CTA in P0; ensemble plausibility deferred to P1 (demo photo is seeded — ensemble is over-engineering for a controlled demo) |
| 4 | Tool-readiness nudges | P4 | **In scope, simplified — notifications only** | **Reshaped by Phase 3 Art. 22 invariant.** Nudges are notifications with a Mark-as-done click, never auto-actions. The "we silently maintained your tools for you" framing is out. |
| 5 | Inventory & consumables | P1 (data) + P2 (cockpit card) | **In scope, complete** | Lightweight; surfaces as a cockpit card, not a separate route |
| 6 | Dealer "talk to your data" Genie space | P5 | **In scope, P2 priority** | Anonymization pipeline + consent state machine + Genie space. Requires P4 telemetry shape. Note: founder chose to keep the Bronze/Silver/Gold Delta scaffolding in P0 so the analytical-pipeline story is *visible* during a P3 customer demo even before Klaus's screen exists. |
| 7 | Multi-user / household sharing | — | **Deferred** | Adds auth/permissions; out of P0-P5 scope |
| 8 | Direct dealer-network booking | — | **Deferred** | Real B2B2C integration; future phase |
| 9 | Voice-first ("Hey yard-pro …") | — | **Deferred** | Cool but not load-bearing for the core pain |
| — | **US launch (CCPA / state-level US privacy)** | — | **Deferred** | yard-pro v1 is EU-only (Stuttgart pilot per §8). Future scope item logged in `docs/TODO.md` |
| — | **Real Edge / Zerobus integration** | — | **Deferred** | P4 ships the in-process synthesizer; real Zerobus gRPC client deferred until a SIM customer is in the loop |
| — | **Batched-inference 100× scale path** | — | **Deferred** | Re-scope conversation, not a Phase 5 item. UC3 success criterion (<15 s) is the SLA at P0-P5; 100× breaks it (Phase 3 §10) |

### Phase 1 UC1 dissent — Phase 4 verdict

**Phase 1's Skeptical PM proposed cutting UC1 as a primary surface and folding the cockpit into the coach screen as a sidebar.** Phase 4 EM re-tested and recommended a different resolution: **keep UC1 as the anchor, but consolidate calendar + inventory + diagnose-result *into* it as cards rather than as sibling routes.** Both critiques were right:
- The Skeptical PM was right that four sibling pages (cockpit, calendar, diagnose, inventory) is overscoped.
- The founder was right that the "state of your yard" anchor screen is load-bearing for the OEM narrative.

Consolidation wins both arguments. The yard-pro consumer app ships **two** routes only: cockpit (the anchor) and coach (the chat). Diagnose is a modal opened from the cockpit's "Snap a photo" button.

## 12. Open Questions & Final Ordering

### Open questions / decisions

The Phase 4 EM sub-agent reclassified the original 9 questions; most were decisions or punts disguised as research. Final list:

| # | Question | Class | Status |
|---|----------|-------|--------|
| Q1 | Foundation Model API default + fallback model IDs | **Decision** | Default `databricks-meta-llama-3-3-70b`, fallback `databricks-claude-sonnet-4`. Confirmed P0. |
| Q2 | Lakebase scale-to-zero Saturday-morning surge — does the 09:00 wake fit UC2 <5 s coach-answer SLA? | **Research** | **Punt for P0** (demo isn't Saturday 09:00 in production). Build the `canary_cold_start.py` script as a deliverable, run it at P4 acceptance. |
| Q3 | KA corpus total size beyond the 20 seed answers | **Decision** | P0 floor: 20 hand-authored seed answers. Beyond 20 is P1 work, scoped after retrieval validation. |
| Q4 | Photo retention default (180 days) | **Punt** | 180 days for v1 privacy notice. User-override deferred to P3 backlog. |
| Q5 | Single Lakebase + RLS vs per-tenant instances | **Punt** | Stays as documented "revisit at scale". |
| Q6 | Same Databricks Apps deployment for consumer + dealer, or separate | **Decision** | Same deployment, sub-route `/dealer/*`, separate service-principal UC grants for Klaus. |
| Q7 | Saira Condensed self-host vs CDN | **Decision** | CDN (Google Fonts) for P0; self-host fallback deferred to P1. |
| Q8 | Vision endpoint no fallback — comfortable? | **Decision** | Yes. Tier-2 diagnose queue deferred to P1 (demo never sees Vision down). |
| Q9 | Genie space provisioning timing — fallback if a customer demo needs the dealer angle before P5 lands | **Decision** | Static screenshot. No engineered fallback. |

**True open at P0 start:** Q2 alone, and it's a benchmark — not a blocker.

### Implementation ordering (P0 → P3)

**P0 — must-have for first customer-grade demo (end of plan-phase P3):**

| Item | Source non-negotiable / use case | Cost |
|------|----------------------------------|------|
| Lakebase schema (`yp_*`) + UC catalog DDL (`yard_pro_bronze/silver/gold` skeleton) seeded with Martin's Stuttgart yard | UC1, UC5; §5 | M |
| Lakehouse Sync configured Lakebase → Delta Bronze + visible Bronze/Silver/Gold layers seeded (~10k synthetic telemetry rows for a believable "analytical pipeline" story during demo) | OEM differentiator narrative §3; founder's call to keep | M |
| Backend routers (yards, plants, tools, inventory, actions, coach, diagnose) with `response_model` + `operation_id` | All P0 UCs; §13 discipline | M |
| `yard_context_service` typed `YardContext` | UC2/UC3 share state; §4 | S |
| Cockpit route (UC1) with `<ProjectThemeScope slug="yard-pro">` + calendar/inventory/diagnose-result child cards | UC1 + UC2 + UC5 + brand-adjacency NN | M |
| Coach route (UC2) — SSE streaming + provenance enforcement (citations required on recommendation turns) + "AI-generated, advisory only" chip | UC2 + diagnostic-honesty NN + EU AI Act NN | M |
| Snap-and-diagnose endpoint + confidence floor < 0.6 → "unsure" + co-equal "second opinion" CTA (NO ensemble plausibility yet — that's P1) + "advisory only" chip | UC3 + diagnostic-honesty NN | M |
| Calendar regeneration on action-log write | UC2 success criterion #4 | S |
| KA corpus (20 hand-authored seed answers minimum) + Vector Search index `yard_pro_gardening_kb` | UC2 + #11 risk callout | L |
| GDPR Art. 22 invariant: `human_confirmed_at` enforced on all `source != 'user'` writes; `<MarkAsDone>` component is the only path | Art. 22 NN | S |
| GDPR Art. 17 delete — happy-path only (delete one yard's `yp_*` rows + photo prefix + cascade to Delta within sync interval) | GDPR NN | S |
| Brand-adjacent theme (`yard-pro.css` + `brand-themes.ts` entry) + `test_no_customer_ref_in_dom.tsx` | Brand-adjacency NN | S |
| Cross-household isolation test (`test_cross_household_isolation.py`) — full enumeration | RT-016 Critical | S |
| Lakebase RLS by `yard_id` derived from `X-Forwarded-User` | RT-016 Critical | S |
| Structured-logger field exclusion (no log-canary CI test yet — that's P1) | RT-024 partial mitigation | S |
| `scripts/check_all.sh` per-phase gate (lessons §32) | Cross-phase | S |
| Single default circuit breaker (per-dependency tuning is P1 work) | §9 simplified | S |
| Idempotency-Key column + UNIQUE partial index (schema only; 24h cache-replay logic is P1) | §8 + §9 simplified | S |

**P1 — next sprint (extends to plan-phase P4):**

| Item | Notes |
|------|-------|
| Telemetry synthesizer + `yp_tool_readiness` upsert flow | UC4 backend; in-process at P1, real Zerobus deferred |
| Tool-readiness nudges as notifications (UC4) | Notifications-only per Art. 22 invariant |
| Consumables reorder hints (UC5 polish) | Surface in cockpit + dealer panel |
| Advisory feedback loop (`yp_coach_feedback`) | Closes diagnostic-honesty rail; auto-flag at 5 % thumbs-down / 100 |
| **Ensemble plausibility check on `confidence ≥ 0.8`** | Deferred from P0 — demo photo is seeded, real users motivate this |
| **Idempotency-Key 24h cache-replay enforcement** | Deferred from P0 — schema in place, logic activated when first double-fire is observed |
| **Per-dependency circuit-breaker thresholds** | Deferred from P0 — tune once we have real failure latency data |
| **Tier-2 diagnose-queue degradation path** | Deferred from P0 — demo never sees Vision down |
| **Log-canary CI test (`test_log_pipeline_no_pii.py`)** | Deferred from P0 — demo has no real PII; promote before any real-user rollout |
| KA-extraction canary nightly job + verbatim cap | RT-008 + §8 AI security |
| `canary_cold_start.py` benchmark (closes Q2) | Lakebase scale-to-zero Saturday-surge research |

**P2 — production hardening / dealer (extends to plan-phase P5):**

| Item | Notes |
|------|-------|
| Dealer panel UI (`/projects/yard-pro/dealer/*`) | UC6 |
| Anonymization pipeline (Lakebase → Delta Silver → Gold) production-grade | UC6 + dealer-consent NN. (Bronze layer already exists from P0 founder-keep call.) |
| Consent state machine (`yp_dealer_relationships`) end-to-end | UC6 |
| Genie space over `yard_pro_gold.dealer_customer_summary` | UC6 |
| **GDPR Art. 15 (access) + Art. 20 (portability) export endpoints** | Deferred from P0 — a SAR isn't exercised during demo; production-launch necessity |
| **Log PII regex post-filter + canary CI** | RT-024 production hardening |
| Retention/partition jobs for `yp_action_log` + Delta tables | §5 retention rules; demo dataset is 30 rows |
| Lakebase connection-pool sizing + `canary_cold_start.py` results applied | Open Q2 closed |
| **Saira Condensed self-host fallback** | Deferred from P0 — CDN works for demo; self-host is production-quality |

**P3 — deferred / depends on real customer:**

| Item | Notes |
|------|-------|
| Real Edge / Zerobus integration | Replaces the synthesizer |
| Multi-user / household sharing | UC #7 deferred |
| Voice-first | UC #9 deferred |
| Direct dealer-network booking | UC #8 deferred |
| Batched-inference path for 100× scale | Re-scope conversation, not engineering |
| US launch (CCPA / state-level privacy) | Out of EU-only v1 scope |
| Premium-tier real-time vision at 100× | Business-model conversation |
| Photo retention user-override | Q4 graduated from punt to backlog |

### Demo script — the 5-minute version that ships at end of P0

1. Open the cockpit (UC1). One screen with calendar / inventory / diagnose cards. "Hedge cutting today: 1.5 h, battery topped up, blade fine. Apple tree fungus check overdue 4 days." rendered from the seeded 2026-05-08 row. **< 1 s first paint.**
2. Click coach. Type "what should I do this weekend?" Personalized answer streams in, **< 5 s end-to-end**, with the "AI-generated, advisory only" chip and inline citations from `ka_docs/regional_almanac/stuttgart_may.md`.
3. Back to cockpit. Tap "Snap a photo" — modal opens. Upload the seeded yellowing-lawn-patch photo. Diagnosis returns in **< 15 s**: "Fusarium blight, 0.82 confidence" + a co-equal "Get a second opinion (free dealer chat)" CTA.
4. Tap "Mark as done" on a queued coach recommendation (Art. 22 affordance). Cockpit recomputes; **≥ 2 calendar entries shift by ≥ 1 day**; the `human_confirmed_at` write happens.
5. *(architecture tour, not a screen)* Open Databricks workspace, show `yard_pro_bronze.coach_transcripts` and `yard_pro_silver.tool_health` populated. "This is where the OEM analytical layer lives. When the dealer panel ships in P5, Klaus's Genie space reads from `yard_pro_gold.dealer_customer_summary` — same lakehouse, different audience."
6. *(optional, if P5 is live)* Switch to the dealer panel. Klaus types "which customers have a robotic mower 4+ years old and no service this season?" Genie returns **≥ 3 anonymized rows in < 10 s**. No `yard_id` visible; only `yard_id_hash`.

Anything that isn't in that demo script and isn't blocking a non-negotiable is a candidate for cut before P0 lands.
