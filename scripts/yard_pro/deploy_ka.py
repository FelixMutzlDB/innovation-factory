"""Deploy the yard-pro Knowledge Assistant.

Recommended (production) path — what the coach actually hits:

  * UC Schema ``{catalog}.yard_pro`` (created if missing)
  * UC Volume ``{catalog}.yard_pro.ka_docs`` (created if missing)
  * Upload of ``ka_docs/**/*.md`` (skipping INDEX.md) into the volume,
    with subdirs flattened (``plant_care/apple.md`` →
    ``plant_care__apple.md``) so the KA's ``files`` source treats each
    as a separate document.
  * Knowledge Assistant via ``POST /api/2.1/knowledge-assistants``
    (lessons §11; falls back to ``/api/2.0/agent-bricks/...`` on older
    workspaces).
  * ``files`` knowledge source attached to the volume.
  * ``knowledge-sources:sync`` triggered.

Pass ``--skip-vs`` to use only the recommended path. The default still
builds an orphan Vector Search index over a chunks Delta table for
ad-hoc retrieval-quality probing — preserved for backwards compatibility
with the Stream B4 design but NOT what production queries hit (the KA
owns embedding + indexing internally; lessons §11 confirms this is the
proven pattern from AECO + AdTech).

Dry-run mode (``--dry-run``) parses ``ka_docs/INDEX.md``, chunks every
listed document, and prints a histogram by ``doc_type`` — useful for the
plan §7 risk-callout retrieval-readiness gate before standing up the
live endpoint.

CLI (lessons §28 catalog-parameterized):

  # Recommended: KA-only deploy
  python -m scripts.yard_pro.deploy_ka \\
      --catalog felix_demo_catalog \\
      --profile fevm-felix-demo \\
      --skip-vs

  # Full (legacy) path including orphan VS index:
  python -m scripts.yard_pro.deploy_ka \\
      --catalog felix_demo_catalog \\
      --profile fevm-felix-demo

After success, paste the printed ``ka-<tile>-endpoint`` into ``app.yml``
under ``YARD_PRO_COACH_KA_ENDPOINT`` (or re-run
``scripts/sync_env_from_state.py`` if that wires up).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterator

import requests

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

KA_DOCS_ROOT = (
    _REPO_ROOT
    / "src"
    / "innovation_factory"
    / "backend"
    / "projects"
    / "yard_pro"
    / "ka_docs"
)

DEFAULT_CATALOG = os.getenv("YARD_PRO_UC_CATALOG", "innovation_factory_catalog")
DEFAULT_SCHEMA = "yard_pro"
DEFAULT_VOLUME = "ka_docs"
DEFAULT_CHUNKS_TABLE = "yard_pro_kb_chunks"
DEFAULT_INDEX = "yard_pro_gardening_kb"
DEFAULT_VS_ENDPOINT = "yard_pro_gardening_kb_endpoint"
DEFAULT_KA_ENDPOINT = "yard-pro-coach-ka"
DEFAULT_EMBEDDING_MODEL = "databricks-gte-large-en"

CHUNK_CHAR_CAP = 1200

# ---------------------------------------------------------------------------
# Markdown chunking
# ---------------------------------------------------------------------------


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML-ish frontmatter (limited to ``key: value`` lines) and
    return (metadata_dict, body). Avoids the PyYAML dependency."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    meta_text = match.group(1)
    body = text[match.end():]
    meta = {}
    for line in meta_text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, body


def _chunk_markdown(body: str) -> Iterator[tuple[str, str]]:
    """Yield (section_heading, chunk_text) pairs.

    Strategy: split on the first level of ``##`` headings. If a section
    is longer than CHUNK_CHAR_CAP, split further on blank lines.
    Documents that lack ``##`` headings yield a single chunk.
    """
    sections: list[tuple[str, list[str]]] = []
    current_heading = "_intro"
    current_lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append((current_heading, current_lines))
            current_heading = line[3:].strip() or "_section"
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_heading, current_lines))

    for heading, lines in sections:
        text = "\n".join(lines).strip()
        if not text:
            continue
        if len(text) <= CHUNK_CHAR_CAP:
            yield heading, text
            continue
        # split on blank line, accumulate until CHUNK_CHAR_CAP
        parts = re.split(r"\n\s*\n", text)
        buf: list[str] = []
        running = 0
        sub_idx = 1
        for part in parts:
            if running + len(part) > CHUNK_CHAR_CAP and buf:
                yield f"{heading}#{sub_idx}", "\n\n".join(buf)
                buf = [part]
                running = len(part)
                sub_idx += 1
            else:
                buf.append(part)
                running += len(part)
        if buf:
            yield f"{heading}#{sub_idx}", "\n\n".join(buf)


def _doc_paths_from_index() -> list[tuple[str, str]]:
    """Parse ``INDEX.md`` and return [(relative_path, doc_type), ...]."""
    index = KA_DOCS_ROOT / "INDEX.md"
    if not index.exists():
        raise FileNotFoundError(f"KA corpus index not found at {index}")
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    # match table rows like: | `path` | doc_type | ... |
    row_re = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([a-z_]+)\s*\|")
    for line in index.read_text(encoding="utf-8").splitlines():
        m = row_re.match(line.strip())
        if m:
            path, doc_type = m.group(1), m.group(2)
            if path in seen:
                continue
            seen.add(path)
            out.append((path, doc_type))
    return out


def build_corpus_chunks() -> list[dict]:
    """Read every doc in INDEX.md, chunk, and return chunk dicts ready
    to insert into the Delta chunks table."""
    chunks: list[dict] = []
    for rel_path, expected_doc_type in _doc_paths_from_index():
        full_path = KA_DOCS_ROOT / rel_path
        if not full_path.exists():
            raise FileNotFoundError(f"INDEX.md lists missing doc: {full_path}")
        text = full_path.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(text)
        doc_type = meta.get("doc_type", expected_doc_type)
        for section_heading, chunk_text in _chunk_markdown(body):
            digest = hashlib.sha256(
                f"{rel_path}#{section_heading}".encode("utf-8")
            ).hexdigest()[:16]
            chunks.append({
                "chunk_id": digest,
                "source_path": rel_path,
                "doc_type": doc_type,
                "section": section_heading,
                "content": chunk_text,
                "metadata_json": json.dumps(meta, sort_keys=True),
            })
    return chunks


# ---------------------------------------------------------------------------
# Databricks resource creation
# ---------------------------------------------------------------------------


def _run_sql(ws, statement: str, *, warehouse_id: str, label: str) -> None:
    from databricks.sdk.service.sql import StatementState
    result = ws.statement_execution.execute_statement(
        warehouse_id=warehouse_id, statement=statement, wait_timeout="50s",
    )
    state = result.status.state if result.status else None
    while state in (StatementState.PENDING, StatementState.RUNNING) and result.statement_id:
        result = ws.statement_execution.get_statement(statement_id=result.statement_id)
        state = result.status.state if result.status else None
    if state == StatementState.FAILED:
        err = result.status.error.message if result.status and result.status.error else "?"
        raise RuntimeError(f"SQL FAILED ({label}): {err}")
    print(f"    [{label}] OK")


def _ensure_schema_and_volume(ws, *, catalog: str, schema: str, volume: str,
                              warehouse_id: str) -> None:
    _run_sql(
        ws,
        f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}",
        warehouse_id=warehouse_id,
        label=f"CREATE SCHEMA {schema}",
    )
    _run_sql(
        ws,
        f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.{volume}",
        warehouse_id=warehouse_id,
        label=f"CREATE VOLUME {volume}",
    )


def _ensure_chunks_table(ws, *, catalog: str, schema: str, table: str,
                         warehouse_id: str) -> None:
    """Create the chunks Delta table. Change-data-feed is enabled because
    Vector Search delta-sync indexes require it."""
    ddl = f"""
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.{table} (
    chunk_id      STRING NOT NULL,
    source_path   STRING NOT NULL,
    doc_type      STRING NOT NULL,
    section       STRING,
    content       STRING NOT NULL,
    metadata_json STRING,
    ingested_at   TIMESTAMP
)
TBLPROPERTIES (delta.enableChangeDataFeed = true)
""".strip()
    _run_sql(ws, ddl, warehouse_id=warehouse_id, label=f"CREATE {table}")


def _upsert_chunks(ws, *, catalog: str, schema: str, table: str,
                   chunks: list[dict], warehouse_id: str) -> None:
    """Idempotently load the chunks into the Delta table.

    Strategy: DELETE everything (corpus is small — ~22 docs × few chunks
    each ~ 50-100 rows), then INSERT VALUES. Re-running the script is
    safe and the index re-syncs from the change-data feed.
    """
    fq = f"{catalog}.{schema}.{table}"
    _run_sql(ws, f"DELETE FROM {fq}", warehouse_id=warehouse_id, label=f"DELETE {table}")

    if not chunks:
        return

    def esc(value: str) -> str:
        return value.replace("\\", "\\\\").replace("'", "''")

    # Insert in batches of 50 rows to stay well within the SQL statement
    # size cap on the Statement Execution API.
    BATCH = 25
    for batch_start in range(0, len(chunks), BATCH):
        batch = chunks[batch_start:batch_start + BATCH]
        rows = []
        for c in batch:
            rows.append(
                f"('{esc(c['chunk_id'])}', "
                f"'{esc(c['source_path'])}', "
                f"'{esc(c['doc_type'])}', "
                f"'{esc(c.get('section', ''))}', "
                f"'{esc(c['content'])}', "
                f"'{esc(c['metadata_json'])}', "
                f"current_timestamp())"
            )
        stmt = (
            f"INSERT INTO {fq} (chunk_id, source_path, doc_type, section, "
            f"content, metadata_json, ingested_at) VALUES\n" + ",\n".join(rows)
        )
        _run_sql(ws, stmt, warehouse_id=warehouse_id,
                 label=f"INSERT {table} batch {batch_start // BATCH + 1}")


def _ensure_vs_endpoint(ws, *, name: str) -> None:
    """Create the Vector Search endpoint if it doesn't exist."""
    host = ws.config.host.rstrip("/")
    headers = {**ws.config._header_factory(), "Content-Type": "application/json"}
    resp = requests.get(
        f"{host}/api/2.0/vector-search/endpoints/{name}", headers=headers
    )
    if resp.status_code == 200:
        state = resp.json().get("endpoint_status", {}).get("state", "UNKNOWN")
        print(f"  VS endpoint '{name}' exists (state={state})")
        return
    print(f"  Creating VS endpoint '{name}' (STORAGE_OPTIMIZED per plan §5)...")
    # Storage-optimized is what plan §5 calls for; if the workspace
    # doesn't support it, fall back to STANDARD.
    create = requests.post(
        f"{host}/api/2.0/vector-search/endpoints",
        headers=headers,
        json={"name": name, "endpoint_type": "STORAGE_OPTIMIZED"},
    )
    if create.status_code not in (200, 201):
        print(f"  STORAGE_OPTIMIZED rejected ({create.status_code}); "
              f"falling back to STANDARD")
        create = requests.post(
            f"{host}/api/2.0/vector-search/endpoints",
            headers=headers,
            json={"name": name, "endpoint_type": "STANDARD"},
        )
    if create.status_code not in (200, 201):
        raise RuntimeError(
            f"VS endpoint creation failed: {create.status_code} {create.text[:300]}"
        )
    # Wait for ONLINE
    for _ in range(40):
        time.sleep(15)
        r = requests.get(
            f"{host}/api/2.0/vector-search/endpoints/{name}", headers=headers
        )
        state = r.json().get("endpoint_status", {}).get("state", "UNKNOWN")
        print(f"  VS endpoint state: {state}")
        if state == "ONLINE":
            return
    raise RuntimeError(f"VS endpoint '{name}' did not reach ONLINE in time")


def _ensure_vs_index(ws, *, catalog: str, schema: str, source_table: str,
                     index_name: str, endpoint: str,
                     embedding_model: str) -> None:
    host = ws.config.host.rstrip("/")
    headers = {**ws.config._header_factory(), "Content-Type": "application/json"}
    full_index = f"{catalog}.{schema}.{index_name}"
    full_source = f"{catalog}.{schema}.{source_table}"

    resp = requests.get(
        f"{host}/api/2.0/vector-search/indexes/{full_index}", headers=headers
    )
    if resp.status_code == 200:
        print(f"  VS index '{full_index}' exists — triggering sync")
        requests.post(
            f"{host}/api/2.0/vector-search/indexes/{full_index}/sync",
            headers=headers,
        )
        return

    print(f"  Creating VS index '{full_index}' (delta-sync, managed embed)...")
    create = requests.post(
        f"{host}/api/2.0/vector-search/indexes",
        headers=headers,
        json={
            "name": full_index,
            "endpoint_name": endpoint,
            "primary_key": "chunk_id",
            "index_type": "DELTA_SYNC",
            "delta_sync_index_spec": {
                "source_table": full_source,
                "pipeline_type": "TRIGGERED",
                "embedding_source_columns": [{
                    "name": "content",
                    "embedding_model_endpoint_name": embedding_model,
                }],
            },
        },
    )
    if create.status_code not in (200, 201):
        raise RuntimeError(
            f"VS index creation failed: {create.status_code} {create.text[:500]}"
        )
    print(f"  VS index '{full_index}' creation initiated")


def _upload_ka_docs_to_volume(*, profile: str | None, catalog: str,
                              schema: str, volume: str) -> int:
    """Upload every ``ka_docs/**/*.md`` (skipping INDEX.md) into the UC Volume
    using the ``databricks fs cp`` CLI — same approach as
    ``deploy_agents_fevm.py`` phase 2. Returns the number of files uploaded.

    Subdirectory paths (``plant_care/apple.md``) are flattened to
    ``plant_care__apple.md`` because the KA's ``files`` source treats one
    file as one document and doesn't recurse on every workspace.
    """
    if not KA_DOCS_ROOT.exists():
        raise FileNotFoundError(f"ka_docs root missing: {KA_DOCS_ROOT}")
    uploaded = 0
    for md_path in sorted(KA_DOCS_ROOT.rglob("*.md")):
        rel = md_path.relative_to(KA_DOCS_ROOT).as_posix()
        if rel == "INDEX.md":
            continue
        flat = rel.replace("/", "__").replace("\\", "__")
        remote = f"dbfs:/Volumes/{catalog}/{schema}/{volume}/{flat}"
        cmd = ["databricks", "fs", "cp", str(md_path), remote, "--overwrite"]
        if profile:
            cmd += ["--profile", profile]
        print(f"  Uploading {rel} -> {flat}")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except FileNotFoundError:
            print("    FAIL: 'databricks' CLI not on PATH — install or set $PATH")
            return uploaded
        if res.returncode != 0:
            print(f"    FAIL: {res.stderr[:400] or res.stdout[:400]}")
            continue
        uploaded += 1
    return uploaded


def _ensure_ka_endpoint(ws, *, ka_endpoint_name: str,
                        index_full_name: str,
                        volume_path: str | None = None) -> str | None:
    """Create or upsert the Knowledge Assistant.

    Returns the KA endpoint name on success (matches
    ``YARD_PRO_COACH_KA_ENDPOINT`` env var consumed by the coach
    service), or None if the workspace doesn't support the
    Agent-Bricks KA REST API.

    BUG FIX (2026-05-12): the create-KA call alone produces an empty KA
    with no knowledge source — queries return generic answers. After
    create we now attach a ``files`` knowledge source pointing at the UC
    Volume that holds the uploaded ``ka_docs/`` (when ``volume_path`` is
    provided) and trigger a sync. This mirrors the proven AECO /
    AdTech pattern in ``scripts/deploy_agents_fevm.py`` phase 6.

    NOTE: this script's separate VS-index path (the chunks Delta table +
    delta-sync index built above) is orphan once the KA is wired to the
    Volume — the KA owns embedding + indexing internally. The VS index
    is preserved as a side artifact for ad-hoc retrieval-quality probing
    against the same corpus, but it is NOT what production queries hit.
    See ``scripts/yard_pro/RUNBOOK.md`` for the recommended flow.
    """
    host = ws.config.host.rstrip("/")
    headers = {**ws.config._header_factory(), "Content-Type": "application/json"}
    body = {
        "display_name": "Yard-Pro Gardening Coach",
        "description": (
            "Curated gardening + tool-care knowledge for the yard-pro coach. "
            "Sources: plant-care manuals (per species), Stuttgart-region "
            "almanac fragments, consumables specs, diagnostic playbooks. "
            "Trust tier: ground-truth. Advisory-only; the coach annotates "
            "every recommendation with the required citation."
        ),
    }
    resp = requests.post(
        f"{host}/api/2.1/knowledge-assistants", headers=headers, json=body
    )
    if resp.status_code not in (200, 201):
        # KA REST API path can differ by workspace version (lessons §11)
        # — try the v2 path
        resp = requests.post(
            f"{host}/api/2.0/agent-bricks/knowledge-assistants",
            headers=headers, json=body,
        )
    if resp.status_code not in (200, 201):
        print(f"  KA endpoint creation skipped (HTTP {resp.status_code}); "
              f"set YARD_PRO_COACH_KA_ENDPOINT manually after manual KA "
              f"creation in the workspace UI.")
        return None
    data = resp.json()
    tile_id = (
        data.get("id")
        or (data.get("name", "").split("/")[-1] if data.get("name") else None)
    )
    endpoint_name = (
        data.get("endpoint_name")
        or data.get("knowledge_assistant", {}).get("endpoint_name")
        or (f"ka-{tile_id}-endpoint" if tile_id else ka_endpoint_name)
    )
    print(f"  KA endpoint created: {endpoint_name} (tile_id={tile_id})")

    # Bug fix: attach a knowledge source so the KA is non-empty. Without
    # this, queries return generic answers regardless of corpus quality.
    if tile_id and volume_path:
        src_body = {
            "display_name": "Yard-Pro Gardening Corpus",
            "description": "yard-pro plant_care + almanac + consumables + playbooks.",
            "source_type": "files",
            "files": {"path": volume_path},
        }
        src = requests.post(
            f"{host}/api/2.1/knowledge-assistants/{tile_id}/knowledge-sources",
            headers=headers, json=src_body,
        )
        if src.status_code in (200, 201):
            print(f"  Knowledge source attached: {src.json().get('id', '?')}")
            sync = requests.post(
                f"{host}/api/2.1/knowledge-assistants/{tile_id}/knowledge-sources:sync",
                headers=headers, json={},
            )
            print(f"  Sync triggered: HTTP {sync.status_code}")
        else:
            print(f"  Knowledge source attach FAILED (HTTP {src.status_code}): "
                  f"{src.text[:300]} — KA exists but will return generic answers "
                  f"until a source is attached via UI.")
    elif tile_id and not volume_path:
        print(f"  No volume_path passed — KA is empty. Upload ka_docs/ to "
              f"a UC Volume and attach via the UI, or re-run with "
              f"--upload-ka-docs.")

    return endpoint_name


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deploy the yard-pro KA + Vector Search index "
                    "(lessons §28 catalog-parameterized)",
    )
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA)
    parser.add_argument("--volume", default=DEFAULT_VOLUME)
    parser.add_argument("--chunks-table", default=DEFAULT_CHUNKS_TABLE)
    parser.add_argument("--index-name", default=DEFAULT_INDEX)
    parser.add_argument("--vs-endpoint", default=DEFAULT_VS_ENDPOINT)
    parser.add_argument("--endpoint-name", "--ka-endpoint",
                        dest="ka_endpoint", default=DEFAULT_KA_ENDPOINT)
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--workspace-url", default=None)
    parser.add_argument("--profile", default=None)
    parser.add_argument(
        "--warehouse-id", default=None,
        help="SQL warehouse for DDL / inserts. Default: env YARD_PRO_WAREHOUSE_ID / WAREHOUSE_ID.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Just chunk locally and print a summary; no Databricks calls.",
    )
    parser.add_argument(
        "--skip-upload", action="store_true",
        help="Skip uploading ka_docs/ to the UC Volume (use when re-running "
             "and files haven't changed — the sync below picks up the existing volume).",
    )
    parser.add_argument(
        "--skip-vs", action="store_true",
        help="Skip the orphan Vector Search index path (chunks Delta + VS endpoint + "
             "VS index). The KA owns its own VS internally; this flag stops the "
             "script from building a parallel index nothing reads. Recommended.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    print("== Building KA corpus chunks from ka_docs/ ==")
    chunks = build_corpus_chunks()
    by_type: dict[str, int] = {}
    for c in chunks:
        by_type[c["doc_type"]] = by_type.get(c["doc_type"], 0) + 1
    print(f"  Total chunks: {len(chunks)}")
    for k, v in sorted(by_type.items()):
        print(f"    {k}: {v}")

    if args.dry_run:
        print("\n  --dry-run set; skipping Databricks deploy.")
        return

    from databricks.sdk import WorkspaceClient
    if args.profile:
        ws = WorkspaceClient(profile=args.profile)
    elif args.workspace_url:
        ws = WorkspaceClient(host=args.workspace_url)
    else:
        ws = WorkspaceClient()

    warehouse_id = (
        args.warehouse_id
        or os.getenv("YARD_PRO_WAREHOUSE_ID")
        or os.getenv("WAREHOUSE_ID")
    )
    if not warehouse_id:
        raise RuntimeError("--warehouse-id or WAREHOUSE_ID env required")

    volume_path = f"/Volumes/{args.catalog}/{args.schema}/{args.volume}"

    print("\n== Ensuring UC schema + volume ==")
    _ensure_schema_and_volume(
        ws,
        catalog=args.catalog,
        schema=args.schema,
        volume=args.volume,
        warehouse_id=warehouse_id,
    )

    if args.skip_upload:
        print("\n== Skipping ka_docs upload (--skip-upload) ==")
    else:
        print(f"\n== Uploading ka_docs/ -> {volume_path} ==")
        n = _upload_ka_docs_to_volume(
            profile=args.profile,
            catalog=args.catalog,
            schema=args.schema,
            volume=args.volume,
        )
        print(f"  Uploaded {n} files")

    if args.skip_vs:
        print("\n== Skipping Vector Search index path (--skip-vs; recommended) ==")
    else:
        print("\n== Ensuring KB chunks Delta table ==")
        _ensure_chunks_table(
            ws,
            catalog=args.catalog,
            schema=args.schema,
            table=args.chunks_table,
            warehouse_id=warehouse_id,
        )

        print("\n== Upserting chunks ==")
        _upsert_chunks(
            ws,
            catalog=args.catalog,
            schema=args.schema,
            table=args.chunks_table,
            chunks=chunks,
            warehouse_id=warehouse_id,
        )

        print("\n== Ensuring Vector Search endpoint ==")
        _ensure_vs_endpoint(ws, name=args.vs_endpoint)

        print("\n== Ensuring Vector Search index ==")
        _ensure_vs_index(
            ws,
            catalog=args.catalog,
            schema=args.schema,
            source_table=args.chunks_table,
            index_name=args.index_name,
            endpoint=args.vs_endpoint,
            embedding_model=args.embedding_model,
        )

    print("\n== Ensuring Knowledge Assistant endpoint ==")
    ka_name = _ensure_ka_endpoint(
        ws,
        ka_endpoint_name=args.ka_endpoint,
        index_full_name=f"{args.catalog}.{args.schema}.{args.index_name}",
        volume_path=volume_path,
    )

    print("\n== DONE ==")
    print(f"  Catalog:     {args.catalog}")
    print(f"  Volume:      {volume_path}")
    if not args.skip_vs:
        print(f"  Chunks tbl:  {args.catalog}.{args.schema}.{args.chunks_table}")
        print(f"  VS index:    {args.catalog}.{args.schema}.{args.index_name} (orphan; KA does its own VS)")
        print(f"  VS endpoint: {args.vs_endpoint}")
    if ka_name:
        print(f"  KA endpoint: {ka_name}")
        print("\n  Set in app.yml / .env:")
        print(f"    YARD_PRO_COACH_KA_ENDPOINT={ka_name}")


if __name__ == "__main__":
    main()
