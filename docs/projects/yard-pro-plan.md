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

<!-- Phases 2-4 sections appear below as they're drafted. -->
