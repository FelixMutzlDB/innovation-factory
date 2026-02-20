"""Visual product recognition endpoints."""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import select

from ....dependencies import SessionDep, get_runtime
from ....runtime import Runtime
from ..databricks_config import LLM_ENDPOINT_NAME
from ..models import (
    HbProduct,
    HbRecognitionJob,
    HbRecognitionJobCreate,
    HbRecognitionJobDetailOut,
    HbRecognitionJobOut,
    HbRecognitionResult,
    HbRecognitionResultOut,
)
from ..services.recognition_service import process_recognition_job

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recognition", tags=["hb-product-center"])


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
async def identify_product(
    request: ProductIdentifyRequest,
    session: SessionDep,
    runtime: Annotated[Runtime, Depends(get_runtime)],
):
    """Identify a Hugo Boss product from a visual description using AI."""
    desc = request.description.lower()

    stmt = select(HbProduct).where(
        HbProduct.style_name.icontains(desc)  # type: ignore[union-attr]
        | HbProduct.category.icontains(desc)  # type: ignore[union-attr]
        | HbProduct.color.icontains(desc)  # type: ignore[union-attr]
        | HbProduct.material.icontains(desc)  # type: ignore[union-attr]
        | HbProduct.collection.icontains(desc)  # type: ignore[union-attr]
    ).limit(5)
    db_matches = list(session.exec(stmt).all())

    keywords = desc.split()
    if not db_matches and keywords:
        for kw in keywords:
            if len(kw) < 3:
                continue
            kw_stmt = select(HbProduct).where(
                HbProduct.style_name.icontains(kw)  # type: ignore[union-attr]
                | HbProduct.category.icontains(kw)  # type: ignore[union-attr]
                | HbProduct.color.icontains(kw)  # type: ignore[union-attr]
                | HbProduct.material.icontains(kw)  # type: ignore[union-attr]
            ).limit(5)
            db_matches = list(session.exec(kw_stmt).all())
            if db_matches:
                break

    matches = []
    for p in db_matches:
        conf = "low"
        name_lower = (p.style_name or "").lower()
        cat_lower = (p.category or "").lower()
        if name_lower in desc or cat_lower in desc:
            conf = "high"
        elif (p.color or "").lower() in desc or (p.material or "").lower() in desc:
            conf = "medium"
        matches.append(ProductMatch(
            product_id=p.id,  # type: ignore[arg-type]
            sku=p.sku,
            style_name=p.style_name,
            color=p.color,
            category=p.category,
            collection=p.collection,
            material=p.material,
            price=p.price,
            confidence=conf,
        ))

    ai_analysis = ""
    try:
        prompt = f"Briefly analyze this product description and suggest what Hugo Boss product it might be: '{request.description}'. Mention likely category, style, and material. Keep it under 100 words."
        result = runtime.ws.api_client.do(
            "POST",
            f"/serving-endpoints/{LLM_ENDPOINT_NAME}/invocations",
            body={"messages": [{"role": "user", "content": prompt}], "max_tokens": 200},
        )
        choices = result.get("choices", [])  # type: ignore[union-attr]
        if choices:
            ai_analysis = choices[0].get("message", {}).get("content", "")
    except Exception as e:
        logger.warning(f"AI analysis unavailable: {e}")
        ai_analysis = f"Found {len(matches)} potential matches based on description keywords."

    return ProductIdentifyResponse(matches=matches, ai_analysis=ai_analysis)


@router.get("/jobs", response_model=list[HbRecognitionJobOut], operation_id="hb_listRecognitionJobs")
def list_recognition_jobs(
    session: SessionDep,
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    stmt = select(HbRecognitionJob)
    if status:
        stmt = stmt.where(HbRecognitionJob.status == status)
    stmt = stmt.order_by(HbRecognitionJob.created_at.desc()).offset(offset).limit(limit)  # type: ignore[union-attr]
    return list(session.exec(stmt).all())


@router.get("/jobs/{job_id}", response_model=HbRecognitionJobDetailOut, operation_id="hb_getRecognitionJob")
def get_recognition_job(job_id: int, session: SessionDep):
    job = session.get(HbRecognitionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Recognition job not found")
    results = list(session.exec(
        select(HbRecognitionResult).where(HbRecognitionResult.job_id == job_id)
    ).all())
    return HbRecognitionJobDetailOut(
        **job.model_dump(),
        results=[HbRecognitionResultOut(**r.model_dump()) for r in results],
    )


@router.post("/jobs", response_model=HbRecognitionJobOut, operation_id="hb_createRecognitionJob")
def create_recognition_job(data: HbRecognitionJobCreate, session: SessionDep):
    job = HbRecognitionJob(**data.model_dump())
    session.add(job)
    session.flush()
    job = process_recognition_job(session, job)
    session.commit()
    return job


@router.post("/jobs/batch", response_model=HbRecognitionJobOut, operation_id="hb_createBatchRecognitionJob")
def create_batch_recognition_job(data: HbRecognitionJobCreate, session: SessionDep):
    from ..models import RecognitionJobType
    job = HbRecognitionJob(**data.model_dump(), job_type=RecognitionJobType.batch)
    session.add(job)
    session.flush()
    job = process_recognition_job(session, job)
    session.commit()
    return job
