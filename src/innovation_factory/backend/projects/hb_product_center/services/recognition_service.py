"""Simulated image recognition service.

Provides mock AI responses for product identification from images.
Designed to be replaced with real Databricks Model Serving endpoint calls.
"""

import random
from datetime import datetime, timezone

from sqlmodel import Session, select

from ..models import (
    HbProduct,
    HbRecognitionJob,
    HbRecognitionResult,
    RecognitionJobStatus,
)

_rng = random.Random()


def process_recognition_job(session: Session, job: HbRecognitionJob) -> HbRecognitionJob:
    """Simulate processing a recognition job by matching against product catalog."""
    job.status = RecognitionJobStatus.processing

    products = list(session.exec(select(HbProduct)).all())
    if not products:
        job.status = RecognitionJobStatus.failed
        session.add(job)
        session.flush()
        return job

    for i in range(job.image_count):
        matched = _rng.random() < 0.85
        product = _rng.choice(products) if matched else None
        confidence = round(_rng.uniform(0.82, 0.99), 3) if matched else round(_rng.uniform(0.15, 0.55), 3)

        result = HbRecognitionResult(
            job_id=job.id,
            product_id=product.id if product else None,
            image_url=f"https://uploads.hugoboss.com/recognition/{job.id}_{i}.jpg",
            confidence_score=confidence,
            detected_sku=product.sku if product else None,
            detected_color=product.color if product else None,
            detected_size=product.size if product else None,
            detected_category=product.category.value if product else None,
            processing_time_ms=_rng.randint(150, 3000),
        )
        session.add(result)

    job.status = RecognitionJobStatus.completed
    job.completed_count = job.image_count
    job.completed_at = datetime.now(timezone.utc)
    session.add(job)
    session.flush()
    return job
