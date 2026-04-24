"""Image similarity service using CLIP embeddings and Databricks Vector Search.

torch + open_clip are heavy (~900 MB installed) so they're imported
lazily inside :func:`compute_embedding`. Callers that never invoke this
function (every non-HB deploy and every test that doesn't need CLIP)
never pay the import cost. If the optional ``image-recognition`` extra
isn't installed, a clear :class:`RuntimeError` is raised instead of a
bare ``ModuleNotFoundError``.

Install the extra with:
    uv sync --extra image-recognition
"""

import io
import logging
from typing import Any

from databricks.sdk import WorkspaceClient
from PIL import Image as PILImage

from ..databricks_config import VS_ENDPOINT_NAME, VS_INDEX_NAME

logger = logging.getLogger(__name__)

# Cached after first successful load. None until then (not "" — we want
# to distinguish "not loaded yet" from "load failed").
_model: Any = None
_preprocess: Any = None


def _load_clip_deps():
    """Import torch + open_clip lazily, surfacing a helpful error if the
    optional ``image-recognition`` extra isn't installed.

    Returns ``(torch, open_clip)``.
    """
    try:
        import open_clip  # type: ignore[import-not-found]
        import torch  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover — env-dependent
        raise RuntimeError(
            "Visual product recognition requires the optional "
            "'image-recognition' extra (torch + open-clip-torch, ~900 MB). "
            "Install with: uv sync --extra image-recognition"
        ) from exc
    return torch, open_clip


def _get_clip():
    """Lazy-load the CLIP model (singleton)."""
    global _model, _preprocess
    if _model is None:
        _, open_clip = _load_clip_deps()
        logger.info("Loading CLIP ViT-B-32 model...")
        _model, _, _preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="openai"
        )
        _model.eval()
        logger.info("CLIP model loaded")
    return _model, _preprocess


def compute_embedding(image_bytes: bytes) -> list[float]:
    """Compute a normalised CLIP embedding for raw image bytes.

    Raises RuntimeError if the ``image-recognition`` extra isn't
    installed on this environment.
    """
    torch, _ = _load_clip_deps()
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
    """Query the Vector Search index and return similar images.

    Does NOT require torch — this path only hits the VS API. Safe to
    call from any deploy flavour.
    """
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
