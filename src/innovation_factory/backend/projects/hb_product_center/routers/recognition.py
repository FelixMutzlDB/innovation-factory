"""Visual product recognition endpoints using Unity Catalog."""

import logging
from typing import Annotated, Optional

from databricks.sdk import WorkspaceClient
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ....dependencies import RuntimeDep
from ..databricks_config import MAS_ENDPOINT_NAME
from ..models import (
    HbRecognitionJobCreate,
    HbRecognitionJobDetailOut,
    HbRecognitionJobOut,
    HbRecognitionResultOut,
    RecognitionJobStatus,
    RecognitionJobType,
    UserRole,
)
from ..services.uc_query_service import select_all, select_by_id, insert_row

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recognition", tags=["hb-product-center"])

_VALID_JOB_TYPES = {e.value for e in RecognitionJobType}
_VALID_JOB_STATUSES = {e.value for e in RecognitionJobStatus}
_VALID_USER_ROLES = {e.value for e in UserRole}


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
    description: str


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
async def identify_product(request: ProductIdentifyRequest, ws: WsDep):
    """Identify a Hugo Boss product from a visual description using AI."""
    desc = request.description.lower()

    # Search products by description keywords
    escaped_desc = desc.replace("'", "''")
    where_clause = f"""
        LOWER(style_name) LIKE '%{escaped_desc}%'
        OR LOWER(category) LIKE '%{escaped_desc}%'
        OR LOWER(color) LIKE '%{escaped_desc}%'
        OR LOWER(material) LIKE '%{escaped_desc}%'
        OR LOWER(collection) LIKE '%{escaped_desc}%'
    """
    db_matches = select_all(ws, "hb_products", where=where_clause, limit=5)

    # If no matches, try individual keywords
    keywords = desc.split()
    if not db_matches and keywords:
        for kw in keywords:
            if len(kw) < 3:
                continue
            escaped_kw = kw.replace("'", "''")
            kw_where = f"""
                LOWER(style_name) LIKE '%{escaped_kw}%'
                OR LOWER(category) LIKE '%{escaped_kw}%'
                OR LOWER(color) LIKE '%{escaped_kw}%'
                OR LOWER(material) LIKE '%{escaped_kw}%'
            """
            db_matches = select_all(ws, "hb_products", where=kw_where, limit=5)
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
        prompt = f"Briefly analyze this product description and suggest what Hugo Boss product it might be: '{request.description}'. Mention likely category, style, and material. Keep it under 100 words."
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
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    """List recognition jobs from Unity Catalog."""
    conditions = []
    if status:
        conditions.append(f"status = '{status}'")

    where = " AND ".join(conditions) if conditions else ""
    rows = select_all(ws, "hb_recognition_jobs", where=where, order_by="created_at DESC", limit=limit, offset=offset)
    return [_sanitize_job_row(row) for row in rows]

@router.get("/jobs/{job_id}", response_model=HbRecognitionJobDetailOut, operation_id="hb_getRecognitionJob")
def get_recognition_job(job_id: int, ws: WsDep):
    """Get recognition job details from Unity Catalog."""
    job = select_by_id(ws, "hb_recognition_jobs", job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Recognition job not found")

    sanitized = _sanitize_job_row(job)
    results = select_all(ws, "hb_recognition_results", where=f"job_id = {job_id}")
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

    rows = select_all(ws, "hb_recognition_jobs", order_by="id DESC", limit=1)
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

    rows = select_all(ws, "hb_recognition_jobs", order_by="id DESC", limit=1)
    return _sanitize_job_row(rows[0]) if rows else HbRecognitionJobOut(**job_data, id=0)  # type: ignore[arg-type]