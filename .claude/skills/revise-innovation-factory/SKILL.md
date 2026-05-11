---
name: revise-innovation-factory
description: Drives the periodic revision workflow in docs/revision-checklist.md to keep Innovation Factory healthy as new accelerators land. Three cadences (per-PR, monthly, quarterly); spawns fresh sub-agents (consistency-auditor, backlog-groomer, lessons-miner, dead-code-hunter, convention-guardian) for the judgment-call sections. Use when the user wants to run a monthly or quarterly revision, audit doc/code drift, groom the backlog, or capture lessons from recent commits.
---

# revise-innovation-factory

Drives the workflow in `docs/revision-checklist.md`. Single output per run: one
commit (`docs: monthly revision YYYY-MM` or `chore: quarterly revision YYYY-Q[N]`)
with a body that lists what changed per section.

## Operating principles

1. **The checklist is the source of truth.** Read `docs/revision-checklist.md`
   first, every run. This skill just runs it — never invent new checks here.
2. **Pick one cadence per session.** Monthly and quarterly are different
   budgets (30 min vs half day); don't mix them. Per-PR isn't run by this
   skill at all — it lives in CI + the PR template.
3. **Sub-agents have no memory.** Each section's sub-agent sees only the
   files it needs and the role prompt from `docs/revision-checklist.md`.
   Never pass conversation history.
4. **The user owns acceptance.** Sub-agents propose; the user decides which
   findings to apply. The skill never auto-applies a critique.
5. **One commit per run.** Resist the urge to commit per-section. The whole
   revision lands as a single commit so the trend is searchable
   (`git log --grep='monthly revision'`).

## Initial setup

When the skill starts:

1. **Read `docs/revision-checklist.md`** end-to-end. It defines every check,
   every command, every sub-agent prompt — copied verbatim.
2. **Ask the user which cadence:**
   - Monthly (~30 min): M1 consistency, M2 backlog, M3 lessons capture
   - Quarterly (~half day): Q1 dead code, Q2 security, Q3 operational, Q4 lessons mining (deeper)
3. **Confirm scope:** if the user wants only some sections (e.g. "just M2
   today"), respect that. The full pass is a default, not a requirement.
4. **Print a one-line plan** before starting work so the user knows the
   order: e.g. "Running monthly: M1 → M2 → M3. Will spawn 3 sub-agents."

## Per-section loop

For each selected section:

### Step 1 — Run the checks

Run the commands listed in `docs/revision-checklist.md` for that section.
Capture output into `/tmp/revision_<section>_<timestamp>.txt` so the
sub-agent (and the user) can reference it.

Some commands need the user's machine (e.g. `databricks` CLI, `gh`, `git
log`). Run them via Bash. If a command fails (e.g. `deptry` not installed),
note it and continue — don't block on tooling gaps.

### Step 2 — Spawn the section's sub-agent (if applicable)

Each section in the checklist names its sub-agent (`consistency-auditor`,
`backlog-groomer`, `lessons-miner`, `dead-code-hunter`, `convention-guardian`).

Use the Agent tool with `subagent_type=general-purpose`. The prompt must:

1. Quote the **exact role prompt** from `docs/revision-checklist.md`.
2. Tell the agent which files / command outputs to read (with full paths).
3. Include the word cap from the checklist.
4. **Not pass conversation history.** The agent reads files, not the chat.

Example invocation (for M1 consistency-auditor):

```
Agent({
  description: "Monthly consistency audit",
  subagent_type: "general-purpose",
  prompt: `You are a documentation consistency auditor. You have not seen the
prior conversation.

Read these files in order:
1. /Users/felix.mutzl/Databricks Git/innovation-factory/CLAUDE.md
2. /Users/felix.mutzl/Databricks Git/innovation-factory/README.md
3. /Users/felix.mutzl/Databricks Git/innovation-factory/docs/lessons-learned.md (header + summary table only)
4. Each .md file under /Users/felix.mutzl/Databricks Git/innovation-factory/docs/projects/ (header + Status line only)

Ground truth — accelerator list:
$(ls -1 /Users/felix.mutzl/Databricks Git/innovation-factory/src/innovation_factory/backend/projects/)

<paste the exact consistency-auditor prompt from docs/revision-checklist.md>

Return findings in the format the prompt specifies. Cap at 600 words.`
})
```

For sections without a named sub-agent (e.g. Q3 operational drift is mostly
mechanical), do the work yourself — read the command outputs, summarize
findings, ask the user what to act on.

### Step 3 — Present findings to user

After the sub-agent returns (or after manual checks):

1. Show a **one-paragraph summary** of what the section found (don't dump
   the full agent output — the user can ask for it).
2. List **the top 3-5 findings** as actionable items with one-line
   descriptions.
3. Ask: "which of these to apply?" — accept "all", "top 3", "1,3,5", or
   skip the whole section.

### Step 4 — Apply accepted changes

Edit files directly. Stage changes but **do not commit yet** — accumulate
across all sections for the single end-of-run commit.

Track what you applied in an in-memory log:

```
[M1] Updated CLAUDE.md accelerator count: 6 → 7 (line 18)
[M1] Updated README.md quickstart command: 'apx dev start' (was missing 'uv run')
[M2] Marked TODO.md A4 as stalled (no commit in 90 days, downgrade to backlog)
[M3] Proposed lesson §32 (Lakebase branch lifecycle) — user accepted, added
```

### Step 5 — Section gate

"Section M1 complete. Continue to M2?" — wait for go-ahead. Lets the user
sleep on a finding or escalate a discovery into a separate task.

## End-of-run commit

When all selected sections are done:

1. Print a **final summary** of every accepted change, grouped by section.
2. Stage all changes: `git add <files>` (the specific files, never `-A`).
3. Show the user the proposed commit message:

   ```
   docs: monthly revision 2026-05

   M1. Cross-doc consistency
   - CLAUDE.md: accelerator count 6 → 7
   - README.md: added 'uv run' prefix to quickstart commands

   M2. Backlog hygiene
   - TODO.md: A4 downgraded to backlog (90d no movement)
   - aeco-hub-plan.md: resolved Open Q3 (answered by commit abc1234)

   M3. Knowledge capture
   - lessons-learned.md: added §32 (Lakebase branch lifecycle, see commit def5678)
   ```

4. Ask the user to confirm. On approval, commit.
5. **Do not push.** The user pushes — same convention as the rest of this repo.

## What this skill does NOT do

- **Per-PR checks.** Those live in CI + the PR template, not here.
- **P0/P1 bug fixes.** If a revision surfaces a real bug, flag it and stop —
  bug fixes belong in their own commit/PR, not in a grooming commit.
- **New convention enforcement.** New lessons go to
  `docs/lessons-learned.md`; new checks go to `docs/revision-checklist.md` —
  this skill consumes the checklist, never silently extends it.
- **Resource cleanup on Databricks.** Q3 *identifies* orphan
  branches/integrations/tables. Deleting them is a user decision — the
  skill prints the exact `databricks ... delete` command but doesn't run it.

## Failure modes & how to recover

- **Sub-agent returns vague critique.** Refeed with stricter word cap and an
  explicit "be specific, quote files, propose exact replacements". If still
  vague after one retry, skip and rely on the user's judgment.
- **A check command isn't installed locally** (e.g. `deptry`, `gitleaks`).
  Note it in the section output, suggest a one-liner to install (`pipx run
  deptry ...`), continue with remaining checks.
- **The revision uncovers > 20 findings in one section.** Don't try to
  resolve all of them — pick the top 5 with the user and queue the rest as
  TODOs in `docs/TODO.md`. A single revision should never balloon into a
  multi-day effort.
- **The user wants to keep going past the cadence's budget.** Soft warn
  ("we're 45 min in, monthly budget is 30") but respect their call. Just
  don't promise that grooming this aggressively will repeat next month.
- **Conflict between the checklist and the user's instinct.** Update the
  checklist (with the user) rather than silently deviating. The checklist
  evolves; the skill follows it.

## Reference files

- `docs/revision-checklist.md` — the canonical workflow (read every run)
- `docs/lessons-learned.md` — what convention-guardian and lessons-miner ground against
- `docs/TODO.md` — what backlog-groomer operates on
- `docs/projects/*.md` — what consistency-auditor cross-checks
- `CLAUDE.md` — what consistency-auditor ground-truths against
- `.github/workflows/` — where per-PR automatable lints should land (out of scope here)

## Companion skill

`new-innovation-factory-project` (sibling) drives plan creation for new
accelerators. The revision workflow assumes plans land in
`docs/projects/*.md` following that skill's structure — if a new accelerator
appears outside that flow, expect `consistency-auditor` to flag it.
