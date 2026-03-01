"""Set up the image similarity vector search resources on the e2 workspace.

Uploads images to a UC Volume, computes CLIP embeddings,
creates the embeddings Delta table, and sets up the VS index.
"""

import hashlib
import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import open_clip
import requests
import torch
from databricks.sdk import WorkspaceClient
from PIL import Image as PILImage

CATALOG = "saschas"
SCHEMA = "image_similarity"
VOLUME = "images"
IMAGE_TABLE = f"{CATALOG}.{SCHEMA}.image_embeddings"
VS_ENDPOINT_NAME = "image_similarity_endpoint"
VS_INDEX_NAME = f"{CATALOG}.{SCHEMA}.image_similarity_index"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"
EMBEDDING_DIM = 512

WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "862f1d757f0424f7")

ASSETS_DIR = Path(__file__).parent.parent / ".cursor" / "projects" / "Users-sascha-saumer-GIT-innovation-factory" / "assets"
if not ASSETS_DIR.exists():
    ASSETS_DIR = Path(os.path.expanduser(
        "~/.cursor/projects/Users-sascha-saumer-GIT-innovation-factory/assets"
    ))

IMAGE_RENAMES = {
    "Screenshot_2026-02-11_at_17.44.19-4dd7114e-6e64-408f-aa47-45f04c0533b6.png": "hugo/Screenshot 2026-02-11 at 17.44.19.png",
    "Screenshot_2026-02-11_at_17.44.25-0be7e168-d0de-44b0-a287-7ed153a8de8d.png": "hugo/Screenshot 2026-02-11 at 17.44.25.png",
    "Screenshot_2026-02-11_at_17.47.03-09777936-ea12-49a8-adb9-dc20e2409eb5.png": "hugo/Screenshot 2026-02-11 at 17.47.03.png",
    "Screenshot_2026-02-11_at_17.47.11-2d536099-fef2-4a44-82a4-285cf8aabc86.png": "hugo/Screenshot 2026-02-11 at 17.47.11.png",
    "Screenshot_2026-02-11_at_17.47.18-d7126765-a2e9-4bcc-9a5c-4b371f79b460.png": "hugo/Screenshot 2026-02-11 at 17.47.18.png",
    "green-1-6208ecde-4d07-4705-a5e0-0584b7c56785.png": "hugo/green-1.png",
    "green-2-8cc95f44-7cab-4798-b7c4-a7234a26d009.png": "hugo/green-2.png",
    "green-3-954381c2-f843-4c57-9155-e21f1dbf9839.png": "hugo/green-3.png",
    "test_black_tshirt-52a79a5a-a944-4474-a159-9ce0c4e657c8.png": "hugo/test_black_tshirt.png",
}


def make_id(image_uri: str) -> str:
    return hashlib.sha256(image_uri.encode()).hexdigest()[:16]


def run_sql(ws: WorkspaceClient, sql: str):
    from databricks.sdk.service.sql import StatementState
    result = ws.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID, statement=sql, wait_timeout="50s"
    )
    if result.status and result.status.state == StatementState.FAILED:
        msg = result.status.error.message if result.status.error else "Unknown"
        raise RuntimeError(f"SQL failed: {msg}")
    return result


def upload_images(ws: WorkspaceClient):
    """Upload images to UC Volume via the Files API."""
    print("\n=== Step 1: Upload images to UC Volume ===")
    host = ws.config.host.rstrip("/")
    headers = ws.config._header_factory()

    for local_name, remote_path in IMAGE_RENAMES.items():
        local_file = ASSETS_DIR / local_name
        if not local_file.exists():
            print(f"  SKIP {local_name} (not found)")
            continue

        volume_file = f"{VOLUME_PATH}/{remote_path}"
        api_path = f"/api/2.0/fs/files{volume_file}"
        url = f"{host}{api_path}"

        with open(local_file, "rb") as f:
            data = f.read()

        resp = requests.put(
            url, headers={**headers, "Content-Type": "application/octet-stream"}, data=data
        )
        if resp.status_code in (200, 201, 204):
            print(f"  OK  {remote_path} ({len(data) // 1024} KB)")
        else:
            print(f"  ERR {remote_path}: {resp.status_code} {resp.text[:200]}")

    print("Upload complete.")


def create_table(ws: WorkspaceClient):
    """Create the embeddings table if it doesn't exist."""
    print("\n=== Step 2: Create embeddings table ===")
    run_sql(ws, f"""
        CREATE TABLE IF NOT EXISTS {IMAGE_TABLE} (
            id            STRING    NOT NULL,
            image_uri     STRING    NOT NULL,
            file_name     STRING,
            category      STRING,
            embedding     ARRAY<FLOAT>,
            embedding_dim INT,
            ingested_at   TIMESTAMP
        )
        TBLPROPERTIES (delta.enableChangeDataFeed = true)
    """)
    print(f"  Table {IMAGE_TABLE} ready")


def compute_and_insert_embeddings(ws: WorkspaceClient):
    """Compute CLIP embeddings locally and insert into the table."""
    print("\n=== Step 3: Compute embeddings and insert ===")
    print("  Loading CLIP model...")
    model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
    model.eval()
    print("  CLIP model loaded")

    for local_name, remote_path in IMAGE_RENAMES.items():
        local_file = ASSETS_DIR / local_name
        if not local_file.exists():
            continue

        volume_uri = f"{VOLUME_PATH}/{remote_path}"
        row_id = make_id(volume_uri)
        fname = os.path.basename(remote_path)
        category = os.path.dirname(remote_path) or "uncategorized"

        img = PILImage.open(local_file).convert("RGB")
        img_tensor = preprocess(img).unsqueeze(0)
        with torch.no_grad():
            emb = model.encode_image(img_tensor)
            emb = emb / emb.norm(dim=-1, keepdim=True)
        embedding = emb.squeeze().tolist()

        emb_str = ",".join(str(round(v, 8)) for v in embedding)
        escaped_uri = volume_uri.replace("'", "''")
        escaped_fname = fname.replace("'", "''")

        sql = f"""
            MERGE INTO {IMAGE_TABLE} AS target
            USING (SELECT '{row_id}' AS id) AS source
            ON target.id = source.id
            WHEN MATCHED THEN UPDATE SET
                image_uri = '{escaped_uri}',
                file_name = '{escaped_fname}',
                category = '{category}',
                embedding = ARRAY({emb_str}),
                embedding_dim = {EMBEDDING_DIM},
                ingested_at = current_timestamp()
            WHEN NOT MATCHED THEN INSERT (id, image_uri, file_name, category, embedding, embedding_dim, ingested_at)
            VALUES ('{row_id}', '{escaped_uri}', '{escaped_fname}', '{category}', ARRAY({emb_str}), {EMBEDDING_DIM}, current_timestamp())
        """
        run_sql(ws, sql)
        print(f"  OK  {fname} (id={row_id})")

    print("Embeddings inserted.")


def setup_vector_search(ws: WorkspaceClient):
    """Create the VS endpoint and index."""
    print("\n=== Step 4: Set up Vector Search ===")
    host = ws.config.host.rstrip("/")
    headers = {**ws.config._header_factory(), "Content-Type": "application/json"}

    # Check/create endpoint
    ep_resp = requests.get(f"{host}/api/2.0/vector-search/endpoints/{VS_ENDPOINT_NAME}", headers=headers)
    if ep_resp.status_code == 200:
        state = ep_resp.json().get("endpoint_status", {}).get("state", "UNKNOWN")
        print(f"  Endpoint '{VS_ENDPOINT_NAME}' exists (state={state})")
    else:
        print(f"  Creating endpoint '{VS_ENDPOINT_NAME}'...")
        r = requests.post(
            f"{host}/api/2.0/vector-search/endpoints",
            headers=headers,
            json={"name": VS_ENDPOINT_NAME, "endpoint_type": "STANDARD"},
        )
        if r.status_code not in (200, 201):
            print(f"  ERR creating endpoint: {r.status_code} {r.text[:300]}")
            return
        print(f"  Endpoint created, waiting for ONLINE...")

    # Wait for endpoint to be ONLINE
    for _ in range(40):
        r = requests.get(f"{host}/api/2.0/vector-search/endpoints/{VS_ENDPOINT_NAME}", headers=headers)
        state = r.json().get("endpoint_status", {}).get("state", "UNKNOWN")
        if state == "ONLINE":
            break
        print(f"  Endpoint state: {state} ... waiting 15s")
        time.sleep(15)
    else:
        print("  TIMEOUT waiting for endpoint")
        return
    print(f"  Endpoint '{VS_ENDPOINT_NAME}' is ONLINE")

    # Check/create index
    idx_resp = requests.get(
        f"{host}/api/2.0/vector-search/indexes/{VS_INDEX_NAME}",
        headers=headers,
    )
    if idx_resp.status_code == 200:
        print(f"  Index '{VS_INDEX_NAME}' exists, triggering sync...")
        requests.post(
            f"{host}/api/2.0/vector-search/indexes/{VS_INDEX_NAME}/sync",
            headers=headers,
        )
    else:
        print(f"  Creating index '{VS_INDEX_NAME}'...")
        r = requests.post(
            f"{host}/api/2.0/vector-search/indexes",
            headers=headers,
            json={
                "name": VS_INDEX_NAME,
                "endpoint_name": VS_ENDPOINT_NAME,
                "primary_key": "id",
                "index_type": "DELTA_SYNC",
                "delta_sync_index_spec": {
                    "source_table": IMAGE_TABLE,
                    "pipeline_type": "TRIGGERED",
                    "embedding_vector_columns": [
                        {"name": "embedding", "embedding_dimension": EMBEDDING_DIM}
                    ],
                },
            },
        )
        if r.status_code not in (200, 201):
            print(f"  ERR creating index: {r.status_code} {r.text[:500]}")
            return
        print(f"  Index created")

    # Wait for index to be ready
    for _ in range(40):
        r = requests.get(f"{host}/api/2.0/vector-search/indexes/{VS_INDEX_NAME}", headers=headers)
        status = r.json().get("status", {})
        ready = status.get("ready", False)
        if ready:
            break
        msg = status.get("message", "")
        print(f"  Index not ready: {msg[:100]} ... waiting 15s")
        time.sleep(15)
    else:
        print("  TIMEOUT waiting for index")
        return
    print(f"  Index '{VS_INDEX_NAME}' is READY")


def grant_permissions(ws: WorkspaceClient):
    """Grant the app SP permissions on the table and volume."""
    print("\n=== Step 5: Grant permissions ===")
    app_sp = "fe8519c1-c112-4e9f-abaf-b635329a7080"
    for grant_sql in [
        f"GRANT SELECT ON TABLE {IMAGE_TABLE} TO `{app_sp}`",
        f"GRANT READ VOLUME ON VOLUME {CATALOG}.{SCHEMA}.{VOLUME} TO `{app_sp}`",
        f"GRANT USE CATALOG ON CATALOG {CATALOG} TO `{app_sp}`",
        f"GRANT USE SCHEMA ON SCHEMA {CATALOG}.{SCHEMA} TO `{app_sp}`",
    ]:
        try:
            run_sql(ws, grant_sql)
            print(f"  OK  {grant_sql.split('TO')[0].strip()}")
        except Exception as e:
            print(f"  WARN {grant_sql.split('TO')[0].strip()}: {e}")
    print("Permissions granted.")


def main():
    print("Setting up image similarity resources on e2 workspace")
    os.environ.setdefault("DATABRICKS_CONFIG_PROFILE", "e2")
    ws = WorkspaceClient()
    print(f"Connected to: {ws.config.host}")

    upload_images(ws)
    create_table(ws)
    compute_and_insert_embeddings(ws)
    setup_vector_search(ws)
    grant_permissions(ws)

    print("\n=== DONE ===")
    print(f"Table:    {IMAGE_TABLE}")
    print(f"Index:    {VS_INDEX_NAME}")
    print(f"Endpoint: {VS_ENDPOINT_NAME}")
    print(f"Volume:   {VOLUME_PATH}")


if __name__ == "__main__":
    main()
