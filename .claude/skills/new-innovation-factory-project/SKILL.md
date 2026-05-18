---
name: new-innovation-factory-project
description: Drives the 4-phase methodology in docs/new-project.md to take a new Innovation Factory accelerator from raw idea to implementation-ready plan. Each phase spawns a fresh sub-agent (no conversation memory) to critique the artifact from a specific role — skeptical PM, senior engineer, threat modeler, pragmatic EM. Use when the user wants to start a new accelerator, draft a plan.md for a new project, or formalize an idea before coding.
---

# new-innovation-factory-project

Drives the methodology in `docs/new-project.md`. Single output: a `plan.md`
saved to `docs/projects/<slug>-plan.md`, ready for implementation.

## Operating principles

1. **Read the methodology first.** Before doing anything, read
   `docs/new-project.md` end-to-end. It is the source of truth — this skill
   just runs it.
2. **One phase at a time.** Drive Phase 1 → 2 → 3 → 4 in order. Never start
   Phase 2 until Phase 1's checklist is satisfied.
3. **Sub-agents have no memory.** Each phase critique is done by a fresh agent
   that sees only `plan.md` (the relevant sections) and the role prompt from
   `docs/new-project.md`. Never pass conversation history to the sub-agent.
4. **The user owns acceptance.** Sub-agents propose; the user decides. The
   skill never auto-applies sub-agent suggestions — it summarizes them and
   asks the user which to accept.
5. **First-principles bias.** When the user wavers between scope options,
   default to the smaller one. Phase 4 will cut anyway; Phase 1 is the time
   to be honest about what's load-bearing.

## Initial setup

When the skill starts:

1. **Read `docs/new-project.md`** for the canonical methodology (you'll
   reference its sub-agent prompts verbatim).
2. **Read `docs/lessons-learned.md`** (or at least skim the summary table) so
   you can cite specific lessons when drafting §7 in Phase 2.
3. **Scan `docs/projects/`** for prior accelerator plans (AECO Hub, MOL ASM
   Cockpit, etc.) as structural references.
4. **Ask the user:**
   - Project slug (kebab-case, used for folder + file naming)
   - One-sentence pitch (becomes the doc's lead-in)
   - Whether to start at Phase 1 (new idea) or jump in mid-flow (extending
     an existing draft)
5. **Create `docs/projects/<slug>-plan.md`** with the boilerplate header from
   `docs/new-project.md` Phase 1 template. This is the artifact you'll grow
   across phases.

## Per-phase loop

For each of Phases 1 → 4:

### Step 1 — Draft

Use the Phase N template in `docs/new-project.md` to ask the user the right
questions. Write the answers into the corresponding `plan.md` sections. Don't
fish for completeness on the first pass — get a credible draft, then improve.

Tips:
- For Phase 1: ask about persona before product features. "Who hurts?" before
  "what's the feature?"
- For Phase 2: cite specific lessons from `docs/lessons-learned.md` in §7
  ("we'll lean on §5 Lakebase OAuth rotation, §2 MAS endpoints, §10
  idempotency").
- For Phase 3: refuse to write platitudes. "We'll handle errors" is rejected;
  "circuit-break Lakebase calls at 5 consecutive 5xx with 30s open state" is
  accepted.
- For Phase 4: list every §2 use case in §11 explicitly. Silent omissions are
  a smell.

### Step 2 — Self-check checklist

Run the Phase N checklist from `docs/new-project.md` against the draft. If
items are unchecked, decide:
- **Block the phase** — go back to Step 1 (e.g. missing success criteria).
- **Accept and note** — proceed with a TODO entry (e.g. "open question 3
  pending: Foundation Model API choice").

### Step 3 — Spawn the sub-agent

Use the Agent tool with `subagent_type=general-purpose`. The prompt must:

1. Quote the **exact role prompt** from `docs/new-project.md` for this phase.
2. Provide the file path to `plan.md` and the section range to read
   (§1-3 for Phase 1, §4-7 for Phase 2, etc.).
3. **Not include any conversation history.** This is the cleared-memory
   guarantee. The agent reads the artifact, not the chat.
4. State the word cap (800-1500 depending on phase, per the methodology).
5. Request output in this format:

   ```
   ## Critique
   1. <finding> — <severity if Phase 3>
      Current: "<quote from plan.md>"
      Suggested: "<replacement>"
   ...

   ## Top 3 to accept
   <which findings, in priority order, the user should likely apply>
   ```

Example invocation pattern (Phase 3):

```
Agent({
  description: "Phase 3 red team critique",
  subagent_type: "general-purpose",
  prompt: `You're a senior security architect / red teamer reviewing a project
plan before any code is written. You have not seen the prior conversation.

Read /Users/felix.mutzl/Databricks Git/innovation-factory/docs/projects/<slug>-plan.md
sections 8-10 only. Also read docs/lessons-learned.md sections 9 (SQL injection),
10 (Lakebase OAuth), 19.x (cross-project), 20 (XSS) for prior art.

<paste the exact Phase 3 role prompt from docs/new-project.md here>

Return your critique in this format:
## Critique
1. <finding> — Critical/High/Medium
   Current: "<quote>"
   Suggested: "<replacement>"

## Top 3 to accept
<which findings the user should likely apply, in priority order>

Cap at 1500 words.`
})
```

### Step 4 — Summarize for the user

After the sub-agent returns:
1. Show the user the **Top 3 to accept** with a one-line preview of each.
2. Ask which to apply: "all", "top 3", "1 and 3", or specific items.
3. Apply only what the user accepts — edit `plan.md` directly.
4. Offer **one** optional re-run of the sub-agent on the edited sections.
   After one re-run, move on — further loops are polish, not learning.

### Step 5 — Phase gate

Confirm with the user: "Phase N complete. Move to Phase N+1?" Wait for
explicit go-ahead. The user may want to sleep on it, share with a colleague,
or refine further before advancing.

## Output

When Phase 4 closes:

1. Final `docs/projects/<slug>-plan.md` is committed-ready.
2. Suggest the user:
   - Open feature branch: `git checkout -b feature/<slug>`
   - Make the first commit just the plan
   - Then start implementation work following the `CLAUDE.md` working mode
3. Save a memory entry (project-type) noting that the accelerator exists and
   when the plan was finalized, so future sessions can find it.
4. **Surface the overview-page registration checklist** from
   `docs/new-project.md` § "Hand-off to implementation". Both AECO Hub
   (2026-04) and yard-pro (2026-05) shipped commits where the backend was
   live but the gallery tile at `/` silently didn't render — root causes
   were the master seed rolling back the platform Project row on a per-project
   seed failure (fixed by `_safe_seed` in `backend/seed.py`) and the brand
   icon missing from the frontend `iconMap`. The checklist names the four
   wires every new accelerator needs (platform Project row, per-project
   seed registration, `iconMap` entry, brand theme + CSS). Repeat it
   verbatim from `docs/new-project.md` so the implementer doesn't have
   to hunt for it.

## What this skill does NOT do

- **Implementation.** This skill stops at a finished `plan.md`. Implementation
  is a separate workflow.
- **Resource provisioning.** No Lakebase creation, no UC catalog creation, no
  Databricks App deployment — those happen during implementation.
- **Convergence loops.** Each sub-agent runs at most twice. The user makes
  judgment calls, not the agent.

## Failure modes & how to recover

- **User pushes ahead without finishing a phase.** Note the unchecked items
  as open questions in §12 and continue. Don't block.
- **Sub-agent returns generic critique.** Refeed the prompt with a stronger
  cap on word count and an explicit "be specific, quote the plan, propose
  exact replacements." If still generic, skip and move on — the founder's
  judgment is more reliable than a generic critique.
- **Plan grows past 700 lines.** Per `docs/new-project.md` anti-patterns,
  split: keep `plan.md` as index + first-principles, move detail to sibling
  docs (`<slug>-security.md`, `<slug>-architecture.md`).
- **User wants to fork the methodology.** Encourage editing
  `docs/new-project.md` directly — the skill is thin on purpose so the
  methodology stays in plain markdown that the team can iterate on.

## Reference files

- `docs/new-project.md` — the canonical methodology (read first, every time)
- `docs/lessons-learned.md` — 31 lessons to cite in Phase 2 §7
- `docs/projects/aeco-hub-plan.md` — most recent accelerator plan (good
  structural reference)
- `/Users/felix.mutzl/Databricks Git/ai-native-mes/plan.md` — the high-water
  mark plan that inspired this methodology
- `CLAUDE.md` — working mode that implementation follows after this skill
  hands off
