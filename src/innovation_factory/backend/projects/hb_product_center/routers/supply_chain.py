"""Supply chain intelligence and sustainability endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from ....dependencies import SessionDep
from ..models import (
    HbProduct,
    HbProductJourney,
    HbProductOut,
    HbSupplyChainEvent,
    HbSupplyChainEventOut,
    HbSustainabilityMetric,
    HbSustainabilityMetricOut,
)

router = APIRouter(prefix="/supply-chain", tags=["hb-product-center"])


@router.get("/events", response_model=list[HbSupplyChainEventOut], operation_id="hb_listSupplyChainEvents")
def list_supply_chain_events(
    session: SessionDep,
    product_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    stmt = select(HbSupplyChainEvent)
    if product_id:
        stmt = stmt.where(HbSupplyChainEvent.product_id == product_id)
    if event_type:
        stmt = stmt.where(HbSupplyChainEvent.event_type == event_type)
    if country:
        stmt = stmt.where(HbSupplyChainEvent.country == country)
    stmt = stmt.order_by(HbSupplyChainEvent.event_date.desc()).offset(offset).limit(limit)  # type: ignore[union-attr]
    return list(session.exec(stmt).all())


@router.get("/products/{product_id}/journey", response_model=HbProductJourney, operation_id="hb_getProductJourney")
def get_product_journey(product_id: int, session: SessionDep):
    product = session.get(HbProduct, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    events = list(session.exec(
        select(HbSupplyChainEvent)
        .where(HbSupplyChainEvent.product_id == product_id)
        .order_by(HbSupplyChainEvent.event_date.asc())  # type: ignore[union-attr]
    ).all())
    sustainability = session.exec(
        select(HbSustainabilityMetric).where(HbSustainabilityMetric.product_id == product_id)
    ).first()
    return HbProductJourney(
        product=HbProductOut(**product.model_dump()),
        events=[HbSupplyChainEventOut(**e.model_dump()) for e in events],
        sustainability=HbSustainabilityMetricOut(**sustainability.model_dump()) if sustainability else None,
    )


@router.get("/sustainability", response_model=list[HbSustainabilityMetricOut], operation_id="hb_listSustainabilityMetrics")
def list_sustainability_metrics(
    session: SessionDep,
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    stmt = select(HbSustainabilityMetric).offset(offset).limit(limit)
    return list(session.exec(stmt).all())


@router.get("/sustainability/{product_id}", response_model=HbSustainabilityMetricOut, operation_id="hb_getProductSustainability")
def get_product_sustainability(product_id: int, session: SessionDep):
    metric = session.exec(
        select(HbSustainabilityMetric).where(HbSustainabilityMetric.product_id == product_id)
    ).first()
    if not metric:
        raise HTTPException(status_code=404, detail="Sustainability metrics not found")
    return metric
