# yard-pro AI Surfaces — Deploy Runbook

> **Purpose.** Stand up the two yard-pro AI surfaces — the **Coach KA**
> (UC2, conversational gardening advice grounded in the curated
> `ka_docs/` corpus) and the **Vision endpoint** (UC3, snap-and-diagnose
> plant/lawn/pest classification) — on the `fevm-felix-demo` workspace
> and wire them into the deployed app.
>
> Target reader: a Databricks Field Engineer or ops engineer who has the
> repo checked out, the Databricks CLI installed, and `uv` available.
> They have never deployed this accelerator before.

## tl;dr

```bash
# 0. Auth (one-time per machine)
databricks auth login --profile fevm-felix-demo

# 1. UC tables (Bronze/Silver/Gold for yard-pro)
uv run python -m src.innovation_factory.backend.projects.yard_pro.seed_uc_tables \
  --catalog felix_demo_catalog \
  --profile fevm-felix-demo \
  --warehouse-id f7cdb11888c4799e

# 2. KA: corpus → UC Volume → Knowledge Assistant
uv run python -m scripts.yard_pro.deploy_ka \
  --catalog felix_demo_catalog \
  --profile fevm-felix-demo \
  --warehouse-id f7cdb11888c4799e \
  --skip-vs

# Note the printed:
#   KA endpoint: ka-<xxxxxxxx>-endpoint
# Update YARD_PRO_COACH_KA_ENDPOINT in app.yml + databricks.yml + .env.

# 3. Vision (verify-only shell — model upload is best-effort, see §5)
uv run python -m scripts.yard_pro.deploy_vision \
  --profile fevm-felix-demo \
  --endpoint-name yard-pro-vision-v1

# 4. Deploy app with the new env vars
uv run apx build
databricks bundle deploy -t dev --profile fevm-felix-demo

# 5. Verify
curl https://innovation-factory-<workspace>.cloud.databricks.com/api/projects/yard-pro/databricks-resources
# Expect: coach_ka_configured: true, vision_configured: true
```

If anything is unclear, read the corresponding section below.

---

## 0. Prerequisites

| Tool | Version | Why |
|------|---------|-----|
| Databricks CLI | ≥ 0.229 | `databricks fs cp`, `databricks bundle deploy`, OAuth refresh |
| `uv` | ≥ 0.4 | Project Python + module entry points |
| `git` | any | This repo |
| `jq` | any | (optional) pretty-printing curl output during verification |

Repository checked out at the branch you want to deploy from (typically
`feature/yard-pro` or whatever has been merged forward to `master`).

Workspace target: **`fevm-felix-demo`** (`https://fevm-felix-demo.cloud.databricks.com`).
SQL warehouse ID: **`f7cdb11888c4799e`** (the shared warehouse the other
6 accelerators use; matches `app.yml`).
UC catalog: **`felix_demo_catalog`**.

---

## 1. Authenticate (often the first failure point)

```bash
databricks auth profiles | grep fevm-felix-demo
```

If the row shows `Valid: NO`, refresh the OAuth token:

```bash
databricks auth login --profile fevm-felix-demo \
  --host https://fevm-felix-demo.cloud.databricks.com
```

This opens a browser. Approve the OAuth flow, then re-check:

```bash
databricks auth profiles | grep fevm-felix-demo
# expected: Valid: YES
databricks current-user me --profile fevm-felix-demo
# expected: { ... "user_name": "felix.mutzl@databricks.com", ... }
```

> **Common pitfall — refresh-token expired.** The local dev backend logs
> `Credentials validation failed: ...refresh token is invalid` when the
> stored OAuth refresh token has expired. There is no "refresh the
> refresh token" command — you have to re-run `databricks auth login`.
> Tokens last ~90 days but workspace-side revocation can shorten that.
>
> **If `databricks auth login` itself fails** (browser hangs, callback
> port already in use), pass `--no-browser` and follow the device-code
> instructions printed to stdout.

---

## 2. Seed Unity Catalog (Bronze / Silver / Gold)

The yard-pro app reads PGlite locally, but production runs against
Lakebase + a Lakehouse Sync into Delta Bronze/Silver/Gold. The UC seed
populates the analytical side — required for the cockpit's "live load"
demo (UC1) and for the dealer panel (UC6, P5).

```bash
uv run python -m src.innovation_factory.backend.projects.yard_pro.seed_uc_tables \
  --catalog felix_demo_catalog \
  --profile fevm-felix-demo \
  --warehouse-id f7cdb11888c4799e
```

**Expected output (truncated):**

```
== Seeding yard-pro UC tables in felix_demo_catalog ==
  Creating schema felix_demo_catalog.yard_pro_bronze
  Creating schema felix_demo_catalog.yard_pro_silver
  Creating schema felix_demo_catalog.yard_pro_gold
  [CREATE yard_pro_bronze.telemetry_events] OK
  [CREATE yard_pro_bronze.diagnoses_raw] OK
  [CREATE yard_pro_bronze.coach_transcripts] OK
  [CREATE yard_pro_silver.tool_health] OK
  [CREATE yard_pro_silver.yard_state] OK
  [CREATE yard_pro_gold.dealer_customer_summary] OK
  ...
  Inserted 100000 telemetry rows
```

**Verify in the workspace UI:** Catalog → `felix_demo_catalog` →
schemas `yard_pro_bronze`, `yard_pro_silver`, `yard_pro_gold` should
exist, with the 6 tables listed above.

**Note: this script has no `--dry-run` flag.** All operations use
`CREATE IF NOT EXISTS` so re-runs are idempotent. The DDL is canonical
in `scripts/uc_schema.py`; only the `INSERT … SELECT FROM range(N)`
telemetry seed is destructive in the sense of replacing rows.

---

## 3. Deploy the Coach Knowledge Assistant (KA)

The KA wraps `src/innovation_factory/backend/projects/yard_pro/ka_docs/`
(22 hand-authored Markdown documents covering plant care, the Stuttgart
regional almanac, consumables specs, and diagnostic playbooks). The KA
endpoint is what `services/coach_service.py` calls via
`query_agent_endpoint(COACH_KA_ENDPOINT, ...)`.

### 3.1 Dry-run first — corpus readiness gate

Plan §7 — "KA corpus quality is risk #1". Before touching the workspace,
sanity-check the corpus chunking and confirm `ka_docs/INDEX.md` matches
disk:

```bash
uv run python -m scripts.yard_pro.deploy_ka --dry-run
```

**Expected output:**

```
== yard-pro KA corpus summary (from ka_docs/INDEX.md) ==
  Docs:    22
  Chunks:  ~80-150  (varies by section depth in the source docs)
    almanac: N
    consumables: N
    plant_care: N
    playbook: N
```

If `MISSING from disk` appears, fix the corpus before continuing — the
script refuses to deploy with broken `INDEX.md` rows.

### 3.2 Live deploy (recommended path)

```bash
uv run python -m scripts.yard_pro.deploy_ka \
  --catalog felix_demo_catalog \
  --profile fevm-felix-demo \
  --warehouse-id f7cdb11888c4799e \
  --skip-vs
```

**What this does (in order):**

1. `CREATE SCHEMA IF NOT EXISTS felix_demo_catalog.yard_pro`
2. `CREATE VOLUME IF NOT EXISTS felix_demo_catalog.yard_pro.ka_docs`
3. Uploads each `ka_docs/**/*.md` (skipping `INDEX.md`) to the volume
   using `databricks fs cp`. Subdirectory paths are flattened
   (`plant_care/apple.md` → `plant_care__apple.md`) because the KA
   `files` source treats one file as one document and doesn't recurse on
   every workspace.
4. `POST /api/2.1/knowledge-assistants` (lessons §11 — current path;
   falls back to `/api/2.0/agent-bricks/knowledge-assistants` on older
   workspaces).
5. `POST /api/2.1/knowledge-assistants/{tile_id}/knowledge-sources`
   with `source_type: "files"` pointing at the volume — **this is the
   step that makes the KA non-empty**. The original Stream B4 script
   forgot to do this; fixed 2026-05-12.
6. Triggers `knowledge-sources:sync` and polls until `endpoint_status` is
   `ONLINE` (up to 15 minutes).

**Expected tail output:**

```
== DONE ==
  Catalog:     felix_demo_catalog
  Volume:      /Volumes/felix_demo_catalog/yard_pro/ka_docs
  KA endpoint: ka-abc12345-endpoint
  Tile id:     abc12345-...

  Set in app.yml / .env:
    YARD_PRO_COACH_KA_ENDPOINT=ka-abc12345-endpoint
```

**Take that endpoint name.** You need it for §6.

### 3.3 Why `--skip-vs`

The script's default path builds a parallel Vector Search index over a
chunks Delta table. That index is **orphan**: the KA owns embedding and
indexing internally — `services/coach_service.py` only queries the KA
endpoint, never the VS index. Pass `--skip-vs` unless you want the VS
index for ad-hoc retrieval-quality experiments outside the KA.

### 3.4 Retrieval-readiness validation (do this before any demo)

Per plan §7 risk callout, validate that the KA actually retrieves the
right chunks for 5 representative questions. From the workspace UI →
Agent Bricks → your KA → Test → run each of these:

| # | Question | Expected source chunk(s) (top-3) |
|---|---|---|
| 1 | What should I do in the yard this weekend in Stuttgart? | `almanac__stuttgart_*.md` |
| 2 | My apple tree has brown rings on the leaves — what is it and what do I do? | `plant_care__apple.md`, `playbook__apple_scab.md` or similar |
| 3 | When should I apply nitrogen-rich fertilizer? | `consumables__fertilizer_*.md`, `almanac__*.md` |
| 4 | Is my robotic mower ready for the season? | `playbook__mower_readiness.md` or `tools_*.md` |
| 5 | I see webbing in my boxwood — what pest? | `playbook__boxwood_moth.md` or `plant_care__boxwood.md` |

If retrieval is wrong on more than 1 of 5, the demo will die in the
first turn. The fix is corpus curation, not script changes — re-author
the `ka_docs/` content and re-run §3.2 (you can pass `--skip-upload`
on subsequent re-runs once the docs are stable to skip the file copy).

### 3.5 Re-running

The KA-create step is **not** idempotent — re-running creates a second
KA. To re-deploy:

- **Content-only changes** (you edited `ka_docs/*.md`): re-run with
  `--skip-vs` but DO NOT pass `--skip-upload`. The script uploads the
  changed files; sync the KA from the UI (or by hitting the
  `knowledge-sources:sync` endpoint manually with the tile_id from your
  first run).
- **Clean slate**: delete the KA in the UI (Agent Bricks → your KA →
  Delete), then re-run.

---

## 4. Deploy the Vision endpoint

Plan §12 explicitly designates this as **best-effort for P0** — the
verify-only shell ships; the actual classifier upload is post-P0 work.
This section covers two acceptable end-states.

### 4.1 If the endpoint already exists (happy path)

```bash
uv run python -m scripts.yard_pro.deploy_vision \
  --profile fevm-felix-demo \
  --endpoint-name yard-pro-vision-v1
```

**Expected output:**

```
== yard-pro Vision endpoint check (yard-pro-vision-v1) ==
  Workspace: https://fevm-felix-demo.cloud.databricks.com
  Endpoint 'yard-pro-vision-v1' exists. Readiness: READY
  URL: https://fevm-felix-demo.cloud.databricks.com/serving-endpoints/yard-pro-vision-v1/invocations

  Sample curl to test the endpoint (substitute IMAGE_BASE64): ...

  Status: READY

  Set in app.yml / .env:
    YARD_PRO_VISION_ENDPOINT=yard-pro-vision-v1
```

Done. Move to §6.

### 4.2 If the endpoint does NOT exist — stub-classifier shortcut for demo

The verify shell will print the setup instructions and exit 1. For a
P0 demo where the actual classifier hasn't been trained yet, deploy a
**stub model** that returns canned predictions (per plan §12: "a stubbed
classifier returning canned predictions is acceptable so the demo's UC3
step works").

The stub lives outside this repo — quickest path is a Databricks
notebook. Open the workspace → New → Notebook → Python, paste:

```python
# yard-pro stub vision classifier — returns canned predictions so UC3
# wires through end-to-end before a real classifier exists.
import mlflow, pandas as pd

mlflow.set_registry_uri("databricks-uc")
CATALOG = "felix_demo_catalog"

class YardProVisionStub(mlflow.pyfunc.PythonModel):
    """Canned classifier. Returns 'apple_scab' on every image so the
    diagnose flow can be demoed deterministically. Confidence below
    the 0.6 floor returns 'unsure' per diagnose_service.py."""

    LABELS = ["apple_scab", "powdery_mildew", "fusarium_blight_lawn",
              "boxwood_moth", "healthy"]

    def predict(self, context, model_input):
        # model_input: pandas DataFrame with column 'image_b64'
        n = len(model_input)
        return pd.DataFrame({
            "label": ["apple_scab"] * n,
            "confidence": [0.74] * n,        # above the 0.6 floor
            "alternatives": [
                [{"label": "powdery_mildew", "confidence": 0.18},
                 {"label": "healthy",         "confidence": 0.08}]
            ] * n,
            "stub": [True] * n,
        })

with mlflow.start_run():
    mlflow.pyfunc.log_model(
        artifact_path="model",
        python_model=YardProVisionStub(),
        input_example=pd.DataFrame({"image_b64": ["..."]}),
        registered_model_name=f"{CATALOG}.yard_pro.vision",
    )

# Create the serving endpoint
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    EndpointCoreConfigInput, ServedEntityInput,
)
ws = WorkspaceClient()
ws.serving_endpoints.create(
    name="yard-pro-vision-v1",
    config=EndpointCoreConfigInput(
        served_entities=[
            ServedEntityInput(
                entity_name=f"{CATALOG}.yard_pro.vision",
                entity_version="1",
                workload_size="Small",
                scale_to_zero_enabled=True,
            ),
        ],
    ),
)
```

Run the notebook on serverless compute. Endpoint creation takes ~10
minutes (scale-to-zero start is fast on subsequent invokes).

Re-run §4.1 — it should print `Readiness: READY` and you're done.

### 4.3 When a real classifier is ready

Follow the full instructions printed by `deploy_vision.py` when no
endpoint exists. The script is intentionally a verify shell — training
+ MLflow registration of a real classifier is post-P0 engineering.

---

## 5. Wire the endpoint names into app.yml / databricks.yml

Two values to update from the deploy outputs:

| Env var | Source |
|---------|--------|
| `YARD_PRO_COACH_KA_ENDPOINT` | §3.2 — `ka-<tile>-endpoint` |
| `YARD_PRO_VISION_ENDPOINT` | §4 — `yard-pro-vision-v1` (or whatever name you used) |

Both files have a `YARD_PRO_AUTOGEN_BEGIN` block placed by this stream's
PR. The placeholder values match `yard-pro-coach-ka` / `yard-pro-vision-v1`
which work IF you use the default endpoint names in the deploy scripts
and the workspace happens to mint the friendly endpoint name on KA
create. Most workspaces instead mint `ka-<tile_id>-endpoint`, so you
will typically need to **overwrite** `YARD_PRO_COACH_KA_ENDPOINT` with
the real value.

Edit `app.yml`:

```yaml
  # YARD_PRO_AUTOGEN_BEGIN: resource-ids
  - name: YARD_PRO_COACH_KA_ENDPOINT
    value: ka-abc12345-endpoint     # <-- paste from §3.2
  - name: YARD_PRO_COACH_KA_TILE_ID
    value: abc12345-...             # <-- optional, for the UI tile embed
  - name: YARD_PRO_VISION_ENDPOINT
    value: yard-pro-vision-v1
```

Same edit in `databricks.yml` under the matching `YARD_PRO_AUTOGEN_BEGIN`
block. Also update the matching `serving_endpoint` resource entries
near the top of each file so the deployed app's service principal gets
`CAN_QUERY` permission on the real endpoint name (look for
`yard-pro-coach-ka` and `yard-pro-vision` resource entries).

For local dev only: append to `.env`:

```
YARD_PRO_COACH_KA_ENDPOINT=ka-abc12345-endpoint
YARD_PRO_VISION_ENDPOINT=yard-pro-vision-v1
```

---

## 6. Deploy the app

```bash
uv run apx build
databricks bundle deploy -t dev --profile fevm-felix-demo
```

Wait for `Deployment complete`. Open the app URL printed at the end.

---

## 7. Verify end-to-end

### 7.1 Resources endpoint

```bash
APP=https://innovation-factory-<workspace-id>.cloud.databricks.com
curl -s "$APP/api/projects/yard-pro/databricks-resources" | jq .
```

**Expected:**

```json
{
  "workspace_url": "fevm-felix-demo.cloud.databricks.com",
  "coach_model": "databricks-meta-llama-3-3-70b",
  "coach_ka_endpoint": "ka-abc12345-endpoint",
  "coach_ka_configured": true,
  "vision_endpoint": "yard-pro-vision-v1",
  "vision_configured": true,
  "configured": true
}
```

If `coach_ka_configured` or `vision_configured` is `false`, the env var
didn't reach the deployed app — re-check §5 and re-run §6.

### 7.2 Coach chat (returns real answer, not the 503 "not configured")

```bash
curl -s -X POST "$APP/api/projects/yard-pro/coach/chat" \
  -H 'Content-Type: application/json' \
  -H "X-Forwarded-User: $(whoami)" \
  -d '{"yard_id": "martin_stuttgart", "message": "Apple tree has brown rings on leaves — what is it?"}' \
  | tee /tmp/coach.out | head -200
```

A real KA response includes a non-empty `content` with at least one
citation reference. A 503 means the env var still says "not configured"
or the KA endpoint isn't ONLINE yet (wait + retry).

### 7.3 Diagnose (Vision)

```bash
curl -s -X POST "$APP/api/projects/yard-pro/diagnose" \
  -H "X-Forwarded-User: $(whoami)" \
  -F "image=@/path/to/some/leaf.jpg" \
  -F "yard_id=martin_stuttgart" \
  -F "plant_id=apple_01"
```

With the stub classifier (§4.2), this should return
`{"label": "apple_scab", "confidence": 0.74, ...}` for any input image.

---

## 8. Troubleshooting

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| `databricks current-user me` returns 401 | OAuth refresh token expired | §1 — re-run `databricks auth login --profile fevm-felix-demo` |
| `deploy_ka.py` exits at `_create_ka` with HTTP 404 ENDPOINT_NOT_FOUND on both paths | Workspace doesn't expose Agent Bricks REST API | Create KA in the UI (Agent Bricks → New), then manually upload `ka_docs/` to the volume and attach as files source. Lessons §11. |
| `deploy_ka.py` step "Uploading ka_docs/" prints `FAIL: 'databricks' CLI not on PATH` | The Databricks CLI binary isn't installed where uv can find it | `brew install databricks` (macOS) or follow https://docs.databricks.com/dev-tools/cli/install.html |
| KA created, sync triggered, but queries return generic gardening answers | Knowledge source attach didn't link, or sync still pending | Wait 10 min then re-query. Confirm in UI: KA → Knowledge sources tab lists `/Volumes/.../ka_docs` with non-zero "Documents indexed". If empty, attach a source manually in the UI. |
| `coach_ka_configured: false` in `databricks-resources` despite the env var being set | App wasn't redeployed after env var change, or value points at a non-existent endpoint | Re-run §6. Verify the endpoint name exists with `databricks serving-endpoints list --profile fevm-felix-demo \| grep yard-pro`. |
| Vision verify exits with the SETUP_INSTRUCTIONS block | Endpoint doesn't exist | §4.2 (stub) or §4.3 (real classifier) |
| Coach response includes citations but they all 404 when clicked | KA citation paths are relative to the volume; the UI assumes ka_docs/ tree paths | Known limitation — file an issue. Doesn't block the demo. |

---

## 9. State file

`scripts/yard_pro/ka_state.json` would persist the KA tile_id +
endpoint name between runs. The current `deploy_ka.py` does NOT write
this file (the AECO/AdTech equivalent in `scripts/deploy_agents_fevm.py`
does, via `fevm_agents_state.json`). If you re-run the KA deploy and
get duplicate KAs, delete the old one in the UI before retrying — this
is a known wart, tracked but not blocking P0.

---

## 10. What this runbook does NOT cover

- **Genie space (P5).** `deploy_genie_space.py` is a placeholder; the
  dealer panel ships in P5, not P0.
- **Lakehouse Sync configuration.** Lakebase → Delta sync is wired in
  `databricks.yml` resources (`lakebase-db`), not yard-pro–specific.
- **GDPR delete pipeline.** Runs as part of the app at runtime; no
  deploy step.
- **PGlite local dev.** `apx dev start` boots PGlite automatically; no
  deploy step needed. Local dev with these endpoints requires the
  `.env` variables from §5 plus `DATABRICKS_CONFIG_PROFILE=fevm-felix-demo`
  (already in `.env`).

---

## 11. Last-resort: deploy without scripts

If both deploy scripts are broken in some way these notes don't cover,
the manual UI path works:

1. **UC schema + volume:** Catalog Explorer → `felix_demo_catalog` → +
   New schema → `yard_pro`. Then → + Add volume → `ka_docs` (managed).
2. **Upload corpus:** From local repo, run
   `databricks fs cp src/innovation_factory/backend/projects/yard_pro/ka_docs/*.md dbfs:/Volumes/felix_demo_catalog/yard_pro/ka_docs/ --recursive --overwrite --profile fevm-felix-demo`
3. **KA:** Agent Bricks → + Knowledge Assistant → Name: "Yard-Pro
   Gardening Coach" → Save → Knowledge sources → + Add → Files →
   `/Volumes/felix_demo_catalog/yard_pro/ka_docs` → Sync.
4. **Vision:** §4.2 notebook path.
5. **Env vars:** §5.
6. **Deploy:** §6.

Total wall time ~30 minutes plus KA-sync wait (~10-15 min).
