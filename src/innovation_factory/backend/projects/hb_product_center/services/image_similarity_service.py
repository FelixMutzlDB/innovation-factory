"""Image similarity service using CLIP embeddings and Databricks Vector Search."""

import io
import logging
from typing import Any

import open_clip
import torch
from databricks.sdk import WorkspaceClient
from PIL import Image as PILImage

from ..databricks_config import VS_ENDPOINT_NAME, VS_INDEX_NAME

logger = logging.getLogger(__name__)

_model = None
_preprocess = None


def _get_clip():
    """Lazy-load the CLIP model (singleton)."""
    global _model, _preprocess
    if _model is None:
        logger.info("Loading CLIP ViT-B-32 model...")
        _model, _, _preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="openai"
        )
        _model.eval()
        logger.info("CLIP model loaded")
    return _model, _preprocess


def compute_embedding(image_bytes: bytes) -> list[float]:
    """Compute a normalised CLIP embedding for raw image bytes."""
    model, preprocess = _get_clip()
    img = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
    img_tensor = preprocess(img).unsqueeze(0)
    with torch.no_grad():
        emb = model.encode_image(img_tensor)
        emb = emb / emb.norm(dim=-1, keepdim=True)
    return emb.squeeze().tolist()


def find_similar_images(
    ws: WorkspaceClient,
    query_embedding: list[float],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Query the Vector Search index and return similar images."""
    body = {
        "columns": ["id", "image_uri", "file_name", "category"],
        "num_results": top_k,
        "query_vector": query_embedding,
    }

    resp = ws.api_client.do(
        "POST",
        f"/api/2.0/vector-search/indexes/{VS_INDEX_NAME}/query",
        body=body,
    )

    rows = resp.get("result", {}).get("data_array", [])
    results = []
    for row in rows:
        results.append(
            {
                "id": row[0],
                "image_uri": row[1],
                "file_name": row[2],
                "category": row[3],
                "score": row[4],
            }
        )
    return results
