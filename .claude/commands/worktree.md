---
description: Create an isolated git worktree for parallel accelerator work, with its own apx dev ports, env, and bootstrapped deps.
argument-hint: <branch-name> [base-branch]
allowed-tools: Bash(git worktree*), Bash(git rev-parse*), Bash(git branch*), Bash(git show-ref*), Bash(cp*), Bash(mkdir*), Bash(uv*), Bash(cd*), Bash(echo*), Bash(ls*)
---

Create an isolated git worktree so this workstream can run in parallel with the
main checkout without colliding on files, branches, or dev-server ports. This is
the safe way to run several Claude sessions against the Innovation Factory gallery
at once — each worktree is a separate working directory sharing one `.git`, so a
`reset --hard` / `cherry-pick` in one can never clobber unstaged work in another.

**Arguments:** `$1` = new branch name (required). `$2` = base branch to fork from
(optional; defaults to the current branch).

Run this from anywhere inside the gallery repo (`.../innovation-factory/innovation-factory`).
Execute these steps in order and stop if any step fails:

1. **Resolve paths.** `REPO=$(git rev-parse --show-toplevel)`. Worktrees live under
   the container dir, grouped and out of the way: `WT_HOME="$REPO/../.worktrees"`;
   `mkdir -p "$WT_HOME"`. Target path: `WT="$WT_HOME/$1"`.

2. **Guard.** If `$1` is empty, stop and tell the user the branch name is required.
   If `$WT` already exists, stop and point them at `git worktree list`.

3. **Create the worktree + branch.**
   - If branch `$1` already exists: `git worktree add "$WT" "$1"`.
   - Otherwise create it: `git worktree add -b "$1" "$WT" "${2:-HEAD}"`.

4. **Assign non-colliding dev ports.** Derive a unique offset from how many
   worktrees already exist: `OFF=$(git worktree list | wc -l | tr -d ' ')`. Use
   high ranges that won't clash with the main checkout's defaults:
   - `APX_FRONTEND_PORT=$((4300 + OFF))`
   - `APX_DEV_SERVER_PORT=$((8300 + OFF))`
   - `APX_DEV_DB_PORT=$((54400 + OFF))`

5. **Carry over local env.** `.env` is gitignored, so a fresh worktree has none:
   `cp "$REPO/.env" "$WT/.env"` (skip with a warning if the source `.env` is absent).
   `.envrc` is tracked and comes with the checkout automatically.

6. **Bootstrap gitignored deps** (`.venv`, `node_modules`, `.tanstack` don't copy):
   `cd "$WT" && uv sync && uv run apx bun install`. Running `uv sync` inside the
   worktree gives it its own correct `.venv` (do not reuse the main one).

7. **Report back** with a ready-to-paste start command and the cleanup command:
   ```
   cd <WT>
   APX_FRONTEND_PORT=<f> APX_DEV_SERVER_PORT=<s> APX_DEV_DB_PORT=<d> uv run apx dev start
   ```
   Cleanup when done: `git worktree remove <WT>` (add `--force` if it has untracked files),
   then optionally `git branch -d <branch>`.

Keep the summary short: print the worktree path, the three ports, and the two
commands above. Do not start the dev server yourself unless the user asks.
