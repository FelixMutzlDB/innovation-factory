# Innovation Factory — Revision Checklist

> Three-cadence loop to keep the repo healthy as new accelerators land. Driven by
> the `revise-innovation-factory` skill. Mostly judgment-call work; a small set
> of automatable lints belongs in CI.

## Cadence at a glance

| Cadence | Frequency | Effort | Surface area |
|---|---|---|---|
| **Per-PR** | every change | 30s (manual) + CI (auto) | Convention drift — lessons-learned violations, missing tests, missing docs |
| **Monthly** | once a month | ~30 min | Cross-doc consistency, backlog hygiene, knowledge capture |
| **Quarterly** | once a quarter | ~half day | Codebase grooming, security drift, operational drift, full lessons mining |

The rule of three: if a check is too expensive for the per-PR cadence, push it to
monthly; if too expensive for monthly, push to quarterly; if too expensive for
quarterly, automate it or delete it.

---

## Per-PR

### Automated (CI must enforce)

These are the lessons-learned violations that have grep-cheap detection. CI is
the right place for them — never burn a human review on these.

| Check | Lesson ref | Implementation status |
|---|---|---|
| Every `@router.(get\|post\|patch\|delete)` has both `response_model=` and `operation_id=` | §13 | **Owed** — see TODO.md D1 / pick this up first |
| No `<ReactMarkdown` outside `ui/components/safe-markdown.tsx` | §20 | Done (grep regression in `tests/common/`) |
| MAS sub-agent names are `^[a-z][a-z0-9_]*$` and referenced in `instructions` | §24 | Done (`tests/scripts/test_mas_naming_convention.py`) |
| Chat streaming uses `create_chat_stream()`, not inline `event_generator` | §12 | Done (`tests/common/test_streaming_protocol.py`) |
| No `assert` in request handlers (release builds strip asserts) | §12 | **Owed** — grep `^\s*assert ` in `**/routers/*.py` |
| No f-string SQL interpolation in `services/*_query_service.py` | §9 | Done (`tests/projects/hb_product_center/test_uc_query_security.py`) |
| No `blanket # type: ignore` without `[rule]` | §4 | **Owed** — grep `# type: ignore$` |
| Rate-limit key derived from `X-Forwarded-User`, not `get_remote_address` directly | §21 | **Owed** — grep |

### Manual (PR template checkbox)

Five items in the PR template, takes 30 seconds. **Author runs, reviewer verifies.**

```markdown
## Revision checks
- [ ] Cited the specific `docs/lessons-learned.md` section(s) I leaned on (if any)
- [ ] Added a named regression test for any P0/P1 fix
- [ ] Updated the affected `docs/projects/*.md` status (if accelerator scope changed)
- [ ] Updated `CLAUDE.md` "Current State" table (if accelerator count / workspace / branch changed)
- [ ] Used project-specific enum prefix for any new enum (`MesOrderStatus`, not `OrderStatus`)
```

If a row doesn't apply, mark it `[N/A]`. Empty checkboxes block merge.

---

## Monthly (~30 min)

### M1. Cross-document consistency

**What to check:**
- `CLAUDE.md` § "Current State" table — accelerator count, workspace, branch, security row
- `README.md` — accelerator list, quickstart commands
- `docs/projects/*.md` — each `Phase: ...` / `Status: ...` header reflects reality
- `docs/lessons-learned.md` — header date, summary table length matches detail section count
- `.env.example` vs env vars actually referenced in code

**Commands:**
```bash
# Files unchanged > 90 days (might be stale)
find docs/ -name '*.md' -mtime +90 -not -path '*/images/*'

# Env vars in code vs .env.example
rg -o 'os\.getenv\("([A-Z_]+)"' src/ -r '$1' | sort -u > /tmp/code_vars.txt
rg -o '^([A-Z_]+)=' .env.example -r '$1' | sort -u > /tmp/example_vars.txt
diff /tmp/code_vars.txt /tmp/example_vars.txt
```

**Sub-agent:** see `consistency-auditor` prompt below.

**Good looks like:** `CLAUDE.md` accelerator count = actual count in `src/innovation_factory/backend/projects/`. README matches. Every plan's "Status" header is correct.

### M2. Backlog hygiene

**What to check:**
- `docs/TODO.md` rows with `[~]` (in progress) — has anyone touched them in 60 days?
- Rows dated > 90 days ago with no movement
- Items marked `[x]` still appearing in "open" priority lists at the bottom
- `docs/tasks/refinement.md` items completed but not marked
- "Open Questions" in each `docs/projects/*.md` that have been answered

**Commands:**
```bash
# Recent commits referencing TODO IDs (A1, B2, D1, etc.) — finds active vs stalled
git log --since=60.days.ago --oneline --grep -E '\b([A-Z][0-9]+)\b'
```

**Sub-agent:** see `backlog-groomer` prompt below.

**Good looks like:** every `[~]` has a recent commit or gets downgraded to `[ ]` (backlog) or `[~ stalled]`. No closed-but-still-listed items. Resolved Open Questions get an "answered: ..." line and move to a decisions log.

### M3. Knowledge capture from recent commits

**What to check:**
- Merge commits / PRs landed in the last 4 weeks
- Did any introduce a non-obvious pattern, surface an API quirk, or fix a tricky bug?
- Should that learning live in `docs/lessons-learned.md` so the next contributor doesn't relearn it?

**Commands:**
```bash
git log --since=4.weeks.ago --merges --oneline
git log --since=4.weeks.ago --first-parent --oneline
```

**Sub-agent:** see `lessons-miner` prompt below.

**Good looks like:** ≤ 3 proposed new lessons per month (more = the agent is being noisy). Each proposal cites the commit SHA and lands in the existing lesson template (Problem / Solution / Takeaway). New summary-table row added.

---

## Quarterly (~half day)

### Q1. Codebase grooming

**What to check:**
- Dead routes (`operation_id` not referenced in `ui/lib/api.ts`)
- Dead models (no router imports them)
- Dead services (no router or test imports)
- Top-level debug scripts (`test-*.js`, `browser-*.js`, `debug-*.js` at repo root — see §16)
- Committed build artifacts (`__dist__/`, `*-output/`, `.playwright-auth-state/` — see §15)
- Unused deps in `pyproject.toml` / `package.json`
- Code-level `TODO:` / `FIXME:` comments with no tracker entry

**Commands:**
```bash
# Dead operation_ids
rg -o 'operation_id=["\047]([a-zA-Z_]+)["\047]' src/innovation_factory/backend -r '$1' | sort -u > /tmp/ops.txt
rg -o 'use[A-Z][a-zA-Z]+Suspense' src/innovation_factory/ui -o | sort -u > /tmp/used.txt
# (manual diff — false positives from non-suspense use)

# Top-level debug scripts
find . -maxdepth 1 \( -name 'test-*.js' -o -name 'browser-*.js' -o -name 'debug-*.js' -o -name 'screenshot-*.js' \) -type f

# TODO/FIXME without tracker reference
rg -n '(TODO|FIXME):' src/ --no-heading | rg -v '\b([A-Z][0-9]+|#[0-9]+|FEIP-)\b'

# Unused python deps
uv pip check
deptry src/ 2>/dev/null || pipx run deptry src/

# Unused frontend deps
bunx depcheck . 2>/dev/null
```

**Sub-agent:** see `dead-code-hunter` prompt below.

**Good looks like:** every flagged dead code is either deleted, kept with a one-line comment explaining why, or moved to `scripts/archive/`. No `TODO:` in code without a corresponding TODO.md ID.

### Q2. Security drift

**What to check:**
- Open SAST / dep-audit findings (`pip-audit`, `npm audit`, `gitleaks`)
- Service-principal grants drift from least-privilege tables in plans
- New external endpoints lacking auth/rate-limit review
- Pinned-version weakening (`>=` creeping in where exact pins existed)
- Lessons-learned anti-patterns regressed (the grep list from "Per-PR / Automated")

**Commands:**
```bash
uv run pip-audit --skip-editable 2>&1 | grep -v 'No known vulnerabilities'
bun audit --prod 2>&1 | grep -i vuln
pipx run gitleaks detect --no-banner --redact -v
```

**Sub-agent:** see `convention-guardian` prompt below (catches anti-pattern regressions across all owed-CI lints in one pass).

**Good looks like:** zero open Critical/High dep vulns > 30 days. No new lessons-learned violations vs last quarter. SP grant tables in plans match actual `GRANT` statements in seed scripts.

### Q3. Operational / Databricks drift

**What to check:**
- Orphan Lakebase branches (created during dev, never wired in)
- Orphan OAuth integrations (count vs quota)
- Orphan UC tables / volumes / schemas not in `scripts/uc_schema.py::TABLES`
- Orphan Genie spaces / Agent Bricks endpoints
- Deployed app revision vs `master` HEAD

**Commands:**
```bash
# Lakebase branches per workspace
databricks postgres list-branches projects/innovation-factory -p fevm-felix-demo
databricks postgres list-branches projects/mes-core -p fe-sandbox-felix-demo-sandbox

# UC tables vs schema-of-truth
databricks api get /api/2.1/unity-catalog/tables \
  --query "catalog_name=innovation_factory_catalog" -p fevm-felix-demo \
  | jq -r '.tables[].full_name' | sort > /tmp/uc.txt
rg -o "'([a-z_]+\.[a-z_]+)':" scripts/uc_schema.py -r '$1' | sort > /tmp/canonical.txt
diff /tmp/canonical.txt /tmp/uc.txt

# App deployment status
databricks apps list -p fevm-felix-demo
```

**Good looks like:** every Lakebase branch / OAuth integration / UC table / Genie space corresponds to a live accelerator. Dead branches deleted. App `source_code_path` revision matches `master` HEAD (or has an explicit "intentionally pinned" note).

### Q4. Full lessons mining

**What to check:** Same as M3, but quarter-wide and with deeper scrutiny. Look for *meta-patterns*: have we repeated a fix in two accelerators? That's a candidate to extract into a shared module (precedents: `databricks_agents.py`, `streaming.py`, `pagination.py`, `uc_schema.py`).

**Sub-agent:** `lessons-miner` (same as M3) with `--since=12.weeks.ago` and extra instruction to flag repeated patterns across projects.

**Good looks like:** lessons-learned summary table grew by 1-4 rows. Any duplicated pattern across ≥ 2 projects has either been extracted into a shared module *or* has an explicit "left duplicated because diverging is correct" note.

---

## Sub-agent prompts

Each sub-agent is spawned fresh by the `revise-innovation-factory` skill. **No
conversation history is passed** — the agent reads files, not the chat. Word
caps are tight; if the agent rambles, refeed with a stricter cap.

### `consistency-auditor` (M1)

> You are a documentation consistency auditor. You have not seen the prior
> conversation. Read these files in order:
> 1. `CLAUDE.md` — focus on the "Current State" table at the top
> 2. `README.md` — accelerator list and quickstart
> 3. `docs/lessons-learned.md` — header date and summary-table count vs detail-section count
> 4. Each `docs/projects/*.md` — header and any "Status:" / "Phase:" line
>
> Also run (or have me run): `ls -1 src/innovation_factory/backend/projects/`
> to get the ground-truth accelerator list.
>
> Return a numbered list of inconsistencies. For each:
> - **File + line:** where the inconsistency lives
> - **Current text:** quote it
> - **What appears to be true:** based on majority vote across docs and ground truth
> - **Suggested fix:** exact replacement text
>
> Skip stylistic differences (one says "6 accelerators", another "six" — that's fine).
> Only flag factual conflicts.
>
> Cap at 600 words.

### `backlog-groomer` (M2)

> You are a backlog reviewer doing a monthly grooming pass. You have not seen
> the prior conversation. Read `docs/TODO.md`.
>
> Also run (or have me run):
> `git log --since=60.days.ago --oneline | head -100`
>
> For each item in `docs/TODO.md`:
> 1. If status is `[~]` (in progress) — check git log for any commit referencing
>    the item ID (A1, B2, D1, etc.). If none in 60 days, mark as **stalled**.
> 2. If status is `[ ]` (open) and dated > 90 days — propose **keep**, **defer to
>    backlog section**, or **drop** with a one-sentence rationale.
> 3. If status is `[x]` (done) — check whether it still appears in any "open"
>    priority list at the bottom of the file. Flag for cleanup.
>
> Also check each `docs/projects/*.md` for "Open Questions" that have visible
> answers elsewhere (in CLAUDE.md, in committed code, or in completed TODO items).
>
> Return a categorized list:
> ```
> ## Stalled [~] (no commit in 60d)
> - A2 — last commit 2026-03-28, no movement since
> ## Drop candidates
> - X4 — dated 2026-01, scope no longer relevant because of Y
> ## Move to done section
> - A5 — marked [x] but still in P2 list at line N
> ## Open Questions to resolve
> - aeco-hub-plan.md §13 Q3 — answered by commit abc1234
> ```
>
> Cap at 800 words.

### `lessons-miner` (M3, Q4)

> You are a knowledge-capture reviewer mining recent commits for lessons worth
> promoting into `docs/lessons-learned.md`. You have not seen the prior
> conversation.
>
> Run (or have me run):
> ```
> git log --since=4.weeks.ago --first-parent --oneline
> ```
> (for the quarterly run, use `--since=12.weeks.ago`)
>
> Read `docs/lessons-learned.md` summary table (just the table, not the detail
> sections) to know what's already captured.
>
> For each significant commit (skip trivial bumps, formatting, etc.):
> 1. Run `git show --stat <sha>` to see scope
> 2. Read the commit message and the largest 1-2 changed files
> 3. Ask: did this introduce a non-obvious pattern, surface an API quirk, fix
>    a tricky bug, or repeat a fix from another accelerator?
>
> Propose **at most 3 new lessons** (be ruthless about not duplicating). For
> each, draft a section in the existing format:
>
> ```markdown
> ## NN. <Title>
>
> ### Problem
> ...
>
> ### Solution
> ...
>
> ### Takeaway
> ...
> ```
>
> Plus one new row for the summary table.
>
> If a pattern appears in 2+ accelerators in the last quarter, flag it as
> **EXTRACT CANDIDATE** — it should probably become a shared module like
> `databricks_agents.py`.
>
> Cap at 1200 words.

### `dead-code-hunter` (Q1)

> You are a codebase grooming reviewer hunting dead code. You have not seen
> the prior conversation.
>
> Targets:
> 1. **Dead routes:** `operation_id` defined in a router but not used in
>    `src/innovation_factory/ui/` (search for the camelCase form as a hook
>    name like `useGet<OpId>Suspense`)
> 2. **Dead models:** SQLModel classes in `src/innovation_factory/backend/projects/*/models.py`
>    that no router imports
> 3. **Dead services:** modules in `services/` that no router or test imports
> 4. **Repo-root debug scripts:** `find . -maxdepth 1 \( -name 'test-*.js' -o -name 'debug-*.js' \) -type f`
> 5. **Code TODOs with no tracker:** `rg -n '(TODO|FIXME):' src/`
>
> For each finding return: **file:line**, **what it is**, **safe-to-delete
> rationale** (or "keep — used by X via dynamic import").
>
> Be conservative: if you can't confirm a thing is unused, mark it
> **investigate further** instead of **delete**.
>
> Cap at 1200 words.

### `convention-guardian` (Q2)

> You are a code-convention guardian. You have not seen the prior conversation.
> Your job is to catch lessons-learned anti-patterns that have crept back into
> the codebase.
>
> Run each of these greps and report any matches:
>
> ```bash
> # Routes missing response_model OR operation_id (§13)
> rg -nU '@router\.(get|post|patch|delete|put)\([^)]*\)' src/innovation_factory/backend --multiline-dotall \
>   | rg -v 'response_model' \
>   | rg -v 'operation_id'
>
> # Asserts in handlers (§12)
> rg -n '^\s*assert ' src/innovation_factory/backend/projects/*/routers/
>
> # Blanket type: ignore (§4)
> rg -n '# type: ignore\s*$' src/
>
> # f-string SQL interpolation outside the safe service (§9)
> rg -n 'execute\(f["\047]' src/innovation_factory/backend
>
> # ReactMarkdown outside SafeMarkdown (§20)
> rg -n '<ReactMarkdown' src/innovation_factory/ui --glob '!**/safe-markdown.tsx'
>
> # Raw get_remote_address (§21)
> rg -n 'get_remote_address' src/innovation_factory/backend --glob '!**/rate_limit.py'
>
> # Inline UC DDL outside scripts/uc_schema.py (§23)
> rg -n 'CREATE TABLE\s+.*\.' scripts/ src/ --glob '!scripts/uc_schema.py'
> ```
>
> Return: for each violation, **file:line + 2 lines of context + the lesson
> reference**. If zero violations across the board, return "Clean — N greps,
> 0 matches" and the date.
>
> Cap at 800 words.

---

## Output: revision commit conventions

Each cadence produces **one commit** (or one small PR), not a flurry of micro-commits.

| Cadence | Commit message format | Example |
|---|---|---|
| Monthly | `docs: monthly revision YYYY-MM` | `docs: monthly revision 2026-05` |
| Quarterly | `chore: quarterly revision YYYY-Q[N]` | `chore: quarterly revision 2026-Q2` |

Commit body lists what changed in each section (M1/M2/M3 or Q1-Q4) with a
one-liner per finding. This makes the next revision trivially searchable:
`git log --grep='monthly revision'` shows the trend.

If the revision surfaces a P0/P1 bug, that's a **separate commit** — don't
mix grooming with bug fixes.

---

## When to evolve this checklist

- Add a per-PR lint when a monthly check has caught the same drift twice.
- Drop a check when it's caught zero drift in three consecutive runs.
- Split a section when it's consistently taking > 40% of the cadence's budget.
- Promote a quarterly check to monthly only if the cost of catching it late
  has been demonstrably high.

The checklist is itself subject to the cadence — review *this file* during the
quarterly Q4 pass.
