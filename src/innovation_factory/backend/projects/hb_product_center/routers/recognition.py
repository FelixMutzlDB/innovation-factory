"""Visual product recognition endpoints using Unity Catalog."""

import base64
import logging
import mimetypes
import os
import re
from typing import Annotated, Optional

from databricks.sdk import WorkspaceClient
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, BeforeValidator, Field

from ....dependencies import RuntimeDep
from ....input_sanitize import sanitize_text
from ....rate_limit import limiter
from ..databricks_config import IMAGE_VOLUME_PATH, MAS_ENDPOINT_NAME, VS_IMAGE_TABLE
from ..models import (
    HbRecognitionJobCreate,
    HbRecognitionJobDetailOut,
    HbRecognitionJobOut,
    HbRecognitionResultOut,
    RecognitionJobStatus,
    RecognitionJobType,
    UserRole,
)
from ..services.image_similarity_service import compute_embedding, find_similar_images
from ..services.uc_query_service import search_like, select_all, select_by_id, insert_row

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recognition", tags=["hb-product-center"])

_VALID_JOB_TYPES = {e.value for e in RecognitionJobType}
_VALID_JOB_STATUSES = {e.value for e in RecognitionJobStatus}
_VALID_USER_ROLES = {e.value for e in UserRole}

_HEX_RE = re.compile(r"^[a-fA-F0-9\-]+$")


def _sanitize_job_row(row: dict) -> HbRecognitionJobOut:
    """Normalise UC row values so they pass Pydantic enum validation."""
    row = dict(row)
    if "job_type" in row and row["job_type"] is not None:
        val = str(row["job_type"]).strip().lower()
        row["job_type"] = val if val in _VALID_JOB_TYPES else "single"
    if "status" in row and row["status"] is not None:
        val = str(row["status"]).strip().lower()
        row["status"] = val if val in _VALID_JOB_STATUSES else "pending"
    if "user_role" in row and row["user_role"] is not None:
        val = str(row["user_role"]).strip().lower()
        row["user_role"] = val if val in _VALID_USER_ROLES else None
    return HbRecognitionJobOut(**row)


def get_ws(runtime: RuntimeDep) -> WorkspaceClient:
    """Get WorkspaceClient from runtime (uses app SP identity)."""
    return runtime.ws


WsDep = Annotated[WorkspaceClient, Depends(get_ws)]


class ProductIdentifyRequest(BaseModel):
    # sanitize_text strips HTML tags + null bytes before min/max_length
    # constraints apply — so a payload padded to 400 chars with stripped
    # tags still has to pass min_length=2 on the cleaned value.
    description: Annotated[
        str,
        BeforeValidator(sanitize_text),
        Field(min_length=2, max_length=500),
    ]


class ProductMatch(BaseModel):
    product_id: int
    sku: str
    style_name: str
    color: Optional[str] = None
    category: str
    collection: Optional[str] = None
    material: Optional[str] = None
    price: Optional[float] = None
    confidence: str


class ProductIdentifyResponse(BaseModel):
    matches: list[ProductMatch]
    ai_analysis: str


@router.post(
    "/identify",
    response_model=ProductIdentifyResponse,
    operation_id="hb_identifyProduct",
)
@limiter.limit("10/minute")
async def identify_product(
    request: Request,
    payload: ProductIdentifyRequest,
    ws: WsDep,
):
    """Identify a HB product from a visual description using AI.

    Note: the first param is named ``request`` (FastAPI/slowapi convention
    for the limiter key extractor). The ProductIdentifyRequest body is
    ``payload`` to avoid shadowing.
    """
    desc = payload.description.lower()

    # Search products by description keywords using safe LIKE search
    search_columns = ["style_name", "category", "color", "material", "collection"]
    db_matches = search_like(ws, "hb_products", search_columns, desc, limit=5)

    # If no matches, try individual keywords
    keywords = desc.split()
    if not db_matches and keywords:
        for kw in keywords:
            if len(kw) < 3:
                continue
            db_matches = search_like(
                ws, "hb_products",
                ["style_name", "category", "color", "material"],
                kw,
                limit=5,
            )
            if db_matches:
                break

    matches = []
    for p in db_matches:
        conf = "low"
        name_lower = (p.get("style_name") or "").lower()
        cat_lower = (p.get("category") or "").lower()
        if name_lower in desc or cat_lower in desc:
            conf = "high"
        elif (p.get("color") or "").lower() in desc or (p.get("material") or "").lower() in desc:
            conf = "medium"
        matches.append(ProductMatch(
            product_id=p["id"],
            sku=p["sku"],
            style_name=p["style_name"],
            color=p.get("color"),
            category=p["category"],
            collection=p.get("collection"),
            material=p.get("material"),
            price=p.get("price"),
            confidence=conf,
        ))

    ai_analysis = ""
    try:
        prompt = f"Briefly analyze this product description and suggest what HB product it might be: '{payload.description}'. Mention likely category, style, and material. Keep it under 100 words."
        result = ws.api_client.do(
            "POST",
            f"/serving-endpoints/{MAS_ENDPOINT_NAME}/invocations",
            body={"messages": [{"role": "user", "content": prompt}], "max_tokens": 200},
        )
        choices = result.get("choices", [])
        if choices:
            ai_analysis = choices[0].get("message", {}).get("content", "")
    except Exception as e:
        logger.warning(f"AI analysis unavailable: {e}")
        ai_analysis = f"Found {len(matches)} potential matches based on description keywords."

    return ProductIdentifyResponse(matches=matches, ai_analysis=ai_analysis)


@router.get("/jobs", response_model=list[HbRecognitionJobOut], operation_id="hb_listRecognitionJobs")
def list_recognition_jobs(
    ws: WsDep,
    status: Optional[str] = Query(None, max_length=50),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    """List recognition jobs from Unity Catalog."""
    filters: dict[str, str] | None = None
    if status:
        filters = {"status": status}

    rows = select_all(
        ws, "hb_recognition_jobs",
        filters=filters,
        order_by_column="created_at",
        order_desc=True,
        limit=limit,
        offset=offset,
    )
    return [_sanitize_job_row(row) for row in rows]

@router.get("/jobs/{job_id}", response_model=HbRecognitionJobDetailOut, operation_id="hb_getRecognitionJob")
def get_recognition_job(job_id: int, ws: WsDep):
    """Get recognition job details from Unity Catalog."""
    job = select_by_id(ws, "hb_recognition_jobs", job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Recognition job not found")

    sanitized = _sanitize_job_row(job)
    results = select_all(ws, "hb_recognition_results", filters={"job_id": str(job_id)})
    return HbRecognitionJobDetailOut(
        **sanitized.model_dump(),
        results=[HbRecognitionResultOut(**r) for r in results],
    )


@router.post("/jobs", response_model=HbRecognitionJobOut, operation_id="hb_createRecognitionJob")
def create_recognition_job(data: HbRecognitionJobCreate, ws: WsDep):
    """Create a new recognition job in Unity Catalog."""
    from datetime import datetime, timezone

    job_data = {
        **data.model_dump(),
        "status": "completed",
        "completed_count": data.image_count,
        "created_at": datetime.now(timezone.utc),
        "completed_at": datetime.now(timezone.utc),
    }

    insert_row(ws, "hb_recognition_jobs", job_data)

    rows = select_all(ws, "hb_recognition_jobs", order_by_column="id", order_desc=True, limit=1)
    return _sanitize_job_row(rows[0]) if rows else HbRecognitionJobOut(**job_data, id=0)  # type: ignore[arg-type]

@router.post("/jobs/batch", response_model=HbRecognitionJobOut, operation_id="hb_createBatchRecognitionJob")
def create_batch_recognition_job(data: HbRecognitionJobCreate, ws: WsDep):
    """Create a batch recognition job in Unity Catalog."""
    from datetime import datetime, timezone

    job_data = {
        **data.model_dump(),
        "job_type": "batch",
        "status": "completed",
        "completed_count": data.image_count,
        "created_at": datetime.now(timezone.utc),
        "completed_at": datetime.now(timezone.utc),
    }

    insert_row(ws, "hb_recognition_jobs", job_data)

    rows = select_all(ws, "hb_recognition_jobs", order_by_column="id", order_desc=True, limit=1)
    return _sanitize_job_row(rows[0]) if rows else HbRecognitionJobOut(**job_data, id=0)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Image Similarity Search (Vector Search + CLIP)
# ---------------------------------------------------------------------------


class SimilarImageRequest(BaseModel):
    image_base64: str
    top_k: int = 5


class SimilarImageResult(BaseModel):
    id: str
    file_name: str
    category: str
    score: float
    image_url: str


class SimilarImagesResponse(BaseModel):
    results: list[SimilarImageResult]


@router.post(
    "/similar",
    response_model=SimilarImagesResponse,
    operation_id="hb_findSimilarImages",
)
async def find_similar(request: SimilarImageRequest, ws: WsDep):
    """Upload a base64-encoded image, compute its CLIP embedding, and return similar images from the vector search index."""
    try:
        image_bytes = base64.b64decode(request.image_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

    try:
        embedding = compute_embedding(image_bytes)
    except Exception as e:
        logger.error(f"Failed to compute embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to process image")

    try:
        raw_results = find_similar_images(ws, embedding, top_k=request.top_k)
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail="Similarity search failed")

    results = [
        SimilarImageResult(
            id=r["id"],
            file_name=r["file_name"],
            category=r["category"],
            score=round(r["score"], 4),
            image_url=f"/api/projects/hb-product-center/recognition/images/{r['id']}",
        )
        for r in raw_results
    ]
    return SimilarImagesResponse(results=results)


@router.get(
    "/images/{image_id}",
    operation_id="hb_getRecognitionImage",
    responses={200: {"content": {"image/*": {}}}},
)
def get_recognition_image(image_id: str, ws: WsDep):
    """Serve an image from UC Volumes by looking up its path in the embeddings table."""
    from ..services.uc_query_service import _escape_value, execute_query_with_schema

    # Validate image_id is a safe hex/UUID string
    if not _HEX_RE.match(image_id):
        raise HTTPException(status_code=400, detail="Invalid image ID format")

    escaped_id = _escape_value(image_id)
    sql = f"SELECT image_uri FROM {VS_IMAGE_TABLE} WHERE id = {escaped_id} LIMIT 1"

    try:
        columns, rows = execute_query_with_schema(ws, sql)
    except Exception as e:
        logger.error(f"Failed to look up image {image_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to look up image")

    if not rows:
        raise HTTPException(status_code=404, detail="Image not found")

    image_uri = rows[0][0]

    if not os.path.exists(image_uri):
        raise HTTPException(status_code=404, detail=f"Image file not found on volume")

    content_type, _ = mimetypes.guess_type(image_uri)
    if not content_type:
        content_type = "image/png"

    with open(image_uri, "rb") as f:
        image_bytes = f.read()

    return Response(content=image_bytes, media_type=content_type)
