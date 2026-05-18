# Innovation Factory — New Project Methodology

> A first-principles, 4-phase process for taking a new accelerator from raw idea to
> implementation-ready plan. Driven by the `new-innovation-factory-project` skill.

## Why this exists

Every accelerator in this repo (ViDistrictOne → AECO Hub) was built faster and
better than the one before because we got smarter about *planning* before we got
smarter about *building*. The AI-native MES plan
([`ai-native-mes/plan.md`](../../ai-native-mes/plan.md)) is the current
high-water mark — it carried the project from idea to a working prototype in days,
not weeks, and surfaced the red-team threats *before* they became live bugs.

This document generalizes that approach. The thesis is simple:

> **A good plan makes a good project.** Cheap iterations on a `plan.md` cost
> nothing; cheap iterations on running code cost a lot.

The methodology has four phases. Each phase has one job, one output artifact,
and one **fresh sub-agent** that critiques the artifact from a specific role —
fresh because we want the critic to come at the plan without the founder's
attachment to it.

## Phases at a glance

| Phase | Job | Output (in `plan.md`) | Sub-agent role |
|---|---|---|---|
| **1. Structure** | Make the idea defensible | §1-3: Problem, Persona, Use Cases, Success Criteria, Why Databricks, Non-negotiables | Skeptical PM / customer voice |
| **2. Plan** | Make the path concrete | §4-7: Architecture, Data Model, Phase breakdown, File layout, Lessons applied | Senior engineer doing design review |
| **3. Harden** | Find what breaks before users do | §8-10: Security, Resilience, Red Team summary, Edge cases, Scale assumptions | Red team / threat modeler |
| **4. Optimize** | Cut what isn't earning its place | §11-12: Use case coverage map (in/out/deferred), Open questions, Final P0/P1/P2 ordering | Pragmatic engineering manager |

The skill drives one phase at a time. After each phase, the user can iterate
with the sub-agent's critique or move on. Phase 5 ("Implementation") is out of
scope for this skill — the plan handoff to implementation is what success looks
like.

---

## Phase 1 — Structure a solid idea

**Goal:** Establish that there's a real problem worth solving, with a defensible
scope and an obvious "why Databricks."

### Required output (`plan.md` §1-3)

```markdown
# <Project Name> — Project Plan

> One-sentence pitch. Industry. What the prototype demonstrates.

## 1. Vision & Problem

- **Problem statement:** Who hurts, how, and why is the current alternative bad?
- **Target persona(s):** Who uses this day-to-day? (Operator, analyst, ops manager, etc.)
- **Industry context:** What's the regulatory / scale / data-shape backdrop?

## 2. Scope & Use Cases

| # | Use Case | In scope | Why / Why not |
|---|----------|----------|---------------|
| 1 | ...     | Yes      | Core demo loop |
| 2 | ...     | No (deferred) | Needs CMMS integration; future phase |

- **Success criteria:** Concrete, demoable. ("Operator sees live OEE drop within
  5s of a PLC anomaly", not "performant dashboard.")
- **Non-negotiables:** Stability, security, scale, regulatory bar.

## 3. Why Databricks (Differentiators)

- What is impossible / hard on a competitor stack that this build makes trivial?
- Which Databricks-native primitives (Lakebase, Lakeview, Agent Bricks, Genie,
  Foundation Models, Mosaic AI, Zerobus) are load-bearing — not just decorative?
- **First-principles check:** If you removed the AI, would this still be useful?
  If you removed the cloud, what's the minimal core?
```

### Phase 1 checklist (before moving on)

- [ ] One-sentence pitch written and re-readable a week later
- [ ] At least one persona is concrete enough to name (not "the analyst")
- [ ] In-scope use cases ≤ 5 for a prototype; deferred items are listed, not ignored
- [ ] Success criteria are observable, not aspirational
- [ ] "Why Databricks" cites ≥ 2 specific primitives, not just "the Lakehouse"
- [ ] At least one non-negotiable is named (it's almost always one of: stability,
      security, scale, compliance)

### Phase 1 sub-agent — Skeptical PM

After Phase 1 drafts §1-3, spawn a fresh agent (no chat history) with this brief:

> You're a skeptical product manager reading a draft project plan for the first
> time. You have not seen the prior conversation. Read `plan.md` and critique
> §1-3 only. Specifically:
> 1. Is the problem statement specific enough that I'd know who to interview
>    next, or is it generic SaaS noise?
> 2. Is the persona named and grounded? (Not "users" or "operators in general".)
> 3. Are the in-scope use cases minimal and tightly coupled to the core demo
>    loop, or is this trying to be five products at once?
> 4. Are success criteria observable in a demo? Rewrite any that aren't.
> 5. Does "why Databricks" name specific primitives, or does it just say
>    "Lakehouse / Unity Catalog"?
> 6. First-principles: what's the smallest thing this could be and still be
>    interesting?
>
> Return: numbered critique + concrete suggested edits to `plan.md` §1-3.
> Be specific. Quote the existing text and write the replacement. Cap at 800 words.

---

## Phase 2 — Create an actionable plan

**Goal:** Turn the idea into a buildable system. Architecture, data model, file
layout, phase breakdown.

### Required output (`plan.md` §4-7)

```markdown
## 4. System Architecture

A layer diagram (Presentation → Application → Data → Edge if applicable → Shop
Floor / Source if applicable). Each layer lists components and their
responsibilities. Show data-flow direction.

If the system has an edge / IoT / external-source component, use a 5-layer
Purdue-style diagram. If it's purely cloud-native, 3 layers is enough.

## 5. Data Model

- **OLTP (Lakebase):** Tables, prefix convention (`<slug>_*` or `dt_*`),
  status enums (`VARCHAR + CHECK`, not `CREATE TYPE`).
- **Analytical (Delta):** Bronze / Silver / Gold; what lives where.
- **Naming:** Project enum prefix to avoid OpenAPI collisions (see
  lessons-learned §13).
- **Indexes:** Composite indexes for the primary query patterns. GIN on JSONB.

## 6. Implementation Phases

| Phase | Scope | Key endpoints / pages | Dependencies |
|---|---|---|---|
| **P1** | Foundation: schema, CRUD APIs, seed data | ... | None |
| **P2** | UI: cockpit pages + streaming pipeline | ... | P1 |
| **P3** | AI: predictions, assistant, agents | ... | P1, P2 |
| **P4** | Integration: ERP / external system, multi-tenant | ... | P1-P3 |

Each phase is independently demoable. P1 alone should already show *something*.

## 7. File Layout & Lessons Applied

```
backend/projects/<slug>/
  models.py                # 3-model pattern (Entity / EntityIn / EntityOut)
  router.py + routers/     # response_model + operation_id on every route
  databricks_config.py     # env-var resource IDs, default empty
  seed.py                  # PGlite-safe (<10K rows)
  ka_docs/ (optional)      # KA source docs
ui/routes/projects/<slug>/
  route.tsx + sub-pages    # Suspense + Skeleton everywhere
```

Reference table: which sections of `docs/lessons-learned.md` we'll lean on
(e.g. §2 MAS endpoints, §5 Lakebase OAuth rotation, §10 idempotency).

## 7.5 Customer CI Research (required)

Innovation Factory accelerators are obfuscated proxies for real customers. Phase 2
includes a small CI (corporate identity) research pass so the prototype can be
themed to *evoke* its target customer without using protected marks.

**Research step:** Visit the customer's corporate site (and brand-aggregator
fallbacks like encycolorpedia.com, logotyp.us, brandcolorcode.com, 1000logos.net).
Capture in `plan.md`:

```markdown
### Customer CI Spec

| Aspect | Value |
|--------|-------|
| **Real customer (internal only)** | <Name> |
| **Obfuscated project name** | <slug / display name> |
| **Primary color (brand-adjacent)** | `#RRGGBB` — source link |
| **Secondary / accent** | `#RRGGBB` — source link |
| **Typography (UI)** | <Google Font, brand-adjacent>  — open-source only |
| **Typography (display, optional)** | <Google Font> |
| **Tone notes** | 1–2 sentences (e.g. "warm industrial / German engineering", "fashion-editorial monochrome") |
| **Sources** | bulleted links |
```

**Hard rails (non-negotiable, see `docs/ci-implementation-plan.md` §2):**
- Brand-*adjacent*, not pixel-perfect. Never embed protected logos or licensed fonts.
- Wordmark = obfuscated project name only, in chosen brand font.
- Photography = generic stock / AI-generated; never lifted from customer marketing.
- The real customer name is for internal docs only; runtime UI and customer-facing
  artifacts must not name them.

Implementation pattern (theme tokens, font loading, route wrapping, tests) lives
in `docs/ci-implementation-plan.md`. Reference it from `plan.md` rather than
duplicating.

```

### Phase 2 checklist

- [ ] Architecture diagram exists (ASCII is fine) and labels every layer
- [ ] Each layer's components have one-line responsibilities
- [ ] Lakebase schema enumerated with prefix convention chosen
- [ ] Enum-prefix decided (lessons-learned §13)
- [ ] At least one composite index per primary query pattern
- [ ] Phase breakdown has clear demoable milestones (P1 alone is interesting)
- [ ] File layout mirrors the standard accelerator layout in `CLAUDE.md`
- [ ] Lessons-applied table cites ≥ 5 specific lessons from `lessons-learned.md`
- [ ] **Customer CI Spec (§7.5) filled in** — palette, fonts, sources cited; obfuscation rails read and accepted

### Phase 2 sub-agent — Senior engineer (design review)

> You're a senior engineer doing a design review on a project plan. You have not
> seen the prior conversation. Read `plan.md` and critique §4-7 only.
>
> 1. Are the layer responsibilities tight, or are concerns leaking across?
> 2. Is the data model correctly normalized for OLTP, or is it pre-optimized
>    for analytics (which belongs in Delta, not Lakebase)?
> 3. Does each phase produce a demoable artifact independently? Mark phases
>    that don't.
> 4. Are there obvious pitfalls from `docs/lessons-learned.md` that the plan
>    has *not* called out? Cite section numbers.
> 5. Is the file layout consistent with existing accelerators in
>    `src/innovation_factory/backend/projects/`? Spot any drift.
> 6. What's the riskiest engineering path here — what could push the build
>    from "1 week" to "1 month" if it goes sideways?
> 7. CI spec (§7.5): are the chosen colors brand-*adjacent* (not pixel-perfect)?
>    Are the fonts open-source Google Fonts (not licensed brand fonts)? Is the
>    real customer name confined to internal docs, not the runtime UI?
>
> Return: numbered critique + concrete suggested edits to `plan.md` §4-7.5. Cite
> specific files/sections. Cap at 1000 words.

---

## Phase 3 — Harden the plan

**Goal:** Surface failure modes, security threats, scale assumptions, and edge
cases *before* code exists. This is the cheapest red team you'll ever run.

### Required output (`plan.md` §8-10)

```markdown
## 8. Security Architecture

| Layer | Measure | Threat addressed |
|-------|---------|------------------|
| **API Gateway** | OAuth + JWT + rate limiting + CSP/HSTS headers | API abuse, XSS |
| **Service-to-service** | mTLS / Zerobus gRPC TLS + cert pinning | MITM, lateral movement |
| **Data at rest** | Lakebase/Delta AES-256; column encryption for sensitive | Disk-level exfil |
| **Data in transit** | TLS 1.3; Lakebase `sslmode=verify-full` | MITM |
| **Access control** | UC RBAC + Lakebase RLS by tenant | Cross-tenant leak |
| **Secrets** | Databricks Secrets; no hardcoded IDs (lessons §5) | Key exposure |
| **Audit** | `<slug>_events` append-only + tamper-protected (lessons §X) | Repudiation |
| **AI security** | Prompt-injection detection; trust-separated RAG; canaries | Prompt injection, model inversion |

(Adapt this table to the project's threat surface — IoT projects need edge
hardening, AI-heavy projects need ML-specific controls, etc.)

## 9. Resilience Design Principles

- **Idempotency** — every write accepts an `idempotency_key`; dedup via event log
- **Circuit breaker** — external calls (Lakebase, Model Serving, ERP) wrapped
- **Graceful degradation** — what works if cloud is offline? what tier serves
  reads from cache? (See AI-native MES plan §"Graceful Degradation Tiers")
- **CQRS** — writes to Lakebase (OLTP), analytical reads from Delta (OLAP),
  unidirectional Lakebase → Delta via Lakehouse Sync
- **Event sourcing** — append-only event table for audit + state reconstruction
- **Optimistic concurrency** — version-based updates, no row locks

## 10. Red Team Summary

| ID | Threat | Severity | Mitigation |
|----|--------|----------|------------|
| RT-001 | ... | Critical | ... |

Full assessment table — 10-30 findings is typical for a prototype. For each
finding, cite the §8 row that mitigates it, or mark "Open — Phase 4B".
```

### Phase 3 checklist

- [ ] Security table covers every layer of the architecture diagram in §4
- [ ] Every "in scope" use case from §2 has been threat-modeled
- [ ] Resilience principles match the non-negotiables in §2
  (no resilience claims without a non-negotiable backing them)
- [ ] Red team table has ≥ 10 findings; ≥ 70% are mitigated, not "open"
- [ ] At least one assumption about scale is concretely stated ("15 plants × 200
      machines × 1 update/sec = 3000 writes/s") rather than handwaved
- [ ] Edge cases (offline, partial failure, conflicting writes) explicitly listed

### Phase 3 sub-agent — Red team / threat modeler

> You're a senior security architect / red teamer reviewing a project plan
> before any code is written. You have not seen the prior conversation. Read
> `plan.md` and critique §8-10 only.
>
> 1. For each layer in the architecture (§4), enumerate the top 3 threats and
>    check whether §8 mitigates each. List unmitigated threats.
> 2. Is the resilience story (§9) backed by named patterns, or is it "we'll
>    handle errors"? Specifically: idempotency, circuit breaker, graceful
>    degradation tiers, CQRS.
> 3. Scale: what fails at 10× the stated load? At 100×? Specifically check
>    Lakebase row-lock contention, connection pool exhaustion, event log
>    unbounded growth.
> 4. AI/ML-specific (if applicable): prompt injection, model poisoning, data
>    leakage via inference, advisory trust erosion.
> 5. Supply chain: any dep that's a single-vendor SPOF (`torch`, a specific
>    SDK pinned to a version)?
> 6. Compliance: what does this plan need (GDPR, GxP, FDA 21 CFR Part 11,
>    IEC 62443, SOC 2) that it doesn't yet have?
>
> Return: numbered red-team findings (severity Critical/High/Medium) + concrete
> additions to §8-10. Be ruthless. Cap at 1500 words.

---

## Phase 4 — Optimize the plan

**Goal:** Cut overdesign. Decide what to defer. Lock the implementation
ordering. Surface remaining open questions.

### Required output (`plan.md` §11-12)

```markdown
## 11. Use Case Coverage Map

| # | Use case from §2 | Plan phase | Status |
|---|------------------|-----------|--------|
| 1 | ... | P1 | In scope, complete |
| 2 | ... | P3 | Simplified (advisory only; full version is future) |
| 3 | ... | — | **Deferred** — needs CMMS integration |

Explicit deferred list with reason. No silent omissions.

## 12. Open Questions & Final Ordering

### Open questions / decisions needed
1. Which Foundation Model API? (Claude via External Models, DBRX, Llama 3)
2. Single Lakebase with RLS vs per-tenant instances?
3. Regulatory bar — is this regulated workload or not?

### Implementation ordering (P0 → P3)

**P0 (must-have for first demo):**
- ...

**P1 (next sprint):**
- ...

**P2 (production hardening):**
- ...

**P3 (deferred — depends on real customer):**
- ...
```

### Phase 4 checklist

- [ ] Every §2 use case is mapped in §11 — in scope, simplified, or deferred
- [ ] No silent omissions — if it's not in §11, it's not in scope (period)
- [ ] Each P0 item directly serves a §2 success criterion
- [ ] P0 list has been pruned: each item, ask "what if we cut this?" — keep only
      the ones where the answer is "the demo dies"
- [ ] Open questions are *decisions*, not platitudes ("Foundation Model API
      choice" not "AI strategy")
- [ ] The plan would survive being handed to a fresh engineer without you

### Phase 4 sub-agent — Pragmatic engineering manager

> You're a pragmatic engineering manager looking at a plan and deciding what
> ships in the next two weeks. You have not seen the prior conversation. Read
> `plan.md` and critique §11-12 only, but also pull from §4-10 to challenge
> scope.
>
> 1. P0 list: for each item, can you justify it in one sentence tied to a §2
>    success criterion? If not, propose cutting or deferring.
> 2. What in §4-6 (architecture, data model, phases) looks over-engineered for
>    a prototype? Specifically: monolith-vs-microservices, premature CQRS,
>    premature observability stack, "future-proofing" abstractions.
> 3. Are there §8-10 controls that are essential vs nice-to-have for a *demo*?
>    (Production needs all of them. The first demo probably doesn't.)
> 4. Are open questions in §12 actually decisions someone can make this week,
>    or are they research projects in disguise? Flag the latter.
> 5. What's the smallest version of this plan that proves the core thesis
>    (§3 first-principles check)? Sketch it.
>
> Return: numbered cut/defer recommendations + a final "smallest demo" sketch.
> Cap at 1000 words.

---

## Sub-agent invocation contract

Every sub-agent is spawned with:
- **No conversation memory.** It sees only `plan.md` and the role prompt.
- **A scoped read of `plan.md`** — only the sections relevant to its phase
  (§1-3 for Phase 1, §4-7 for Phase 2, etc.).
- **Optional context:** `docs/lessons-learned.md` for Phase 2; existing
  `docs/projects/*.md` as comparable accelerators for any phase.
- **A bounded word count** — 800-1500 words depending on phase. Long enough to
  be specific; short enough that you can act on it.

After the sub-agent returns:
1. Skim the critique with the user.
2. User decides which suggestions to accept (this is the irreplaceable step —
   you, not the agent, have the founder's judgment).
3. Apply accepted edits to `plan.md`.
4. (Optional) Re-run the sub-agent on the edited section once. Stop after one
   re-run; further loops are usually polishing, not learning.

## Hand-off to implementation

When all four phases are complete and `plan.md` clears every checklist:

- Save `plan.md` to `docs/projects/<slug>-plan.md` (matching existing accelerators).
- Open a feature branch `feature/<slug>` from `master`.
- The first commit on the branch is just the plan, so the implementation history
  starts from a planned baseline.
- Implementation work follows the **working mode** in `CLAUDE.md`:
  Investigate → Plan → Implement → Test → Iterate.

### Overview-page registration checklist (don't ship without these)

A new accelerator only renders on `/` (the gallery) when **all** of these wires
are in place. AECO Hub Phase 6 and yard-pro both shipped commits where the
backend was live but the project tile silently didn't appear — the root causes
were (a) the `seed_<slug>_data` raising and rolling back the platform Project
row in a single big transaction (fixed by `_safe_seed` in `backend/seed.py`,
do **not** revert), and (b) the brand icon missing from the frontend `iconMap`
so the tile fell back to a generic Box.

Before declaring "deployed":

1. **Platform Project row** — add an entry to `_seed_projects.projects_data`
   in `src/innovation_factory/backend/seed.py` with `slug`, `name`,
   `description`, `company`, `icon`, `color`.
2. **Per-project seed** — add `(label, seed_<slug>_data)` to `_PROJECT_SEEDS`
   in the same file. Each seed is wrapped by `_safe_seed`, so a data-seed
   failure no longer rolls back the platform row — but the project's own
   data still won't appear until the seed succeeds.
3. **Icon registration** — the `icon` string you set in step 1 must exist in
   `src/innovation_factory/ui/routes/index.tsx`'s `iconMap`. Import the
   lucide-react icon and add it to the map. Without this the tile renders
   with a fallback Box icon (functional but visually wrong).
4. **Brand theme** — register the slug in `src/innovation_factory/ui/lib/brand-themes.ts`
   and create `src/innovation_factory/ui/styles/themes/<slug>.css` so the
   `<ProjectThemeScope>` wrapper applies the right CSS variables on the
   project's own routes. The gallery tile picks up the `color` from the DB
   row directly, but the project's sub-pages need the theme registered.
5. **Idempotency** — re-run `uv run apx dev start` against a clean PGlite
   and confirm the seed is a no-op the second time. Master seed runs on
   every app start; non-idempotent seeds will silently slow startup or
   raise.
6. **Smoke** — after `databricks bundle deploy`, hit
   `GET /api/projects` on the deployed app and confirm the new slug is in
   the response. If not, check the app logs for `Seed for <label> failed`
   from `_safe_seed`'s exception handler.

## When to skip a phase

- **Skip Phase 1** if you're extending an existing accelerator with a known
  problem statement — start at Phase 2.
- **Skip Phase 3** only if the project is a throwaway / 1-day spike. Otherwise
  this phase has the best cost-to-value ratio.
- **Never skip Phase 4.** Cuts compound; the plan you ship is always smaller
  than the plan you drafted.

## Anti-patterns to avoid

- **Plan-as-todo-list.** A plan is a *design*, not a backlog. Backlogs live in
  TODO.md, the plan lives in `docs/projects/`.
- **Adding sections without removing any.** Optimize means cut. If §11 grows
  during Phase 4, something else should shrink.
- **Skipping the sub-agent because "I already know what they'll say."** You
  don't. Every project we've run this on has surfaced a finding the founder
  missed.
- **Re-running sub-agents to convergence.** After one or two passes the agent
  starts polishing prose, not finding issues. Stop and move on.
- **Letting the plan grow past ~700 lines.** AI-native MES landed at 725
  lines and was at the edge of readable. Past that, split: keep `plan.md` as
  index + first-principles; move detail to sibling docs.
