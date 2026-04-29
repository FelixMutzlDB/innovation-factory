# Visual baselines for chrome-devtools driven verification

Each `<page>.md` file is a normalized accessibility-tree snapshot of a deployed-app page. The agent captures a fresh snapshot via `chrome-devtools__take_snapshot`, then runs:

```
python scripts/snapshot_diff.py \
    --baseline tests/visual/baselines/<page>.md \
    --current  /tmp/<page>.md
```

A clean diff means the UI hasn't drifted. After an intentional UI change, regenerate the baseline:

```
python scripts/snapshot_diff.py \
    --baseline tests/visual/baselines/<page>.md \
    --current  /tmp/<page>.md \
    --update
```

## What the diff strips

`scripts/snapshot_diff.NORMALIZERS` strips the volatile bits the user shouldn't
have to chase:

- chrome-devtools `uid=N_M` identifiers (regenerated every snapshot)
- Live IoT readings (zone temp, CO2, humidity — change every 10 s)
- ISO timestamps and date-strings
- Recharts month-day axis tick labels
- Synthetic sensor codes generated at seed time

If you find a new volatile field, add it to `NORMALIZERS` so future
diffs stop flagging it.

## Capturing a baseline (workflow)

1. `python scripts/dump_openapi.py && uv run apx frontend build` (so the UI compiles)
2. Deploy or reach the live page in a browser session.
3. Drive the agent through the page with chrome-devtools MCP (`new_page` → `take_snapshot`).
4. Save the snapshot to `/tmp/<page>.md`.
5. Run `--update` once to seed the baseline.
6. From then on, run the diff (without `--update`) to detect drift.

## Existing baselines

| Baseline | Page | Captured |
|----------|------|----------|
| `aeco-hub-portfolio.md` | `/projects/aeco-hub` | 2026-04-29 |
| `aeco-hub-tools.md` | `/projects/aeco-hub/tools` | 2026-04-29 |
