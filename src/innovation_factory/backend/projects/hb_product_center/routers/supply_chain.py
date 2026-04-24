"""Supply chain intelligence and sustainability endpoints using Unity Catalog."""

import json
from typing import Annotated, Optional

from databricks.sdk import WorkspaceClient
from fastapi import APIRouter, Depends, HTTPException, Query

from ....dependencies import RuntimeDep
from ....pagination import Pagination
from ..models import (
    ComplianceStatus,
    HbProductJourney,
    HbProductOut,
    HbSupplyChainEventOut,
    HbSustainabilityMetricOut,
    ProductCategory,
    ProductCollection,
    ProductSeason,
    ProductStatus,
    SupplyChainEventType,
)
from ..services.uc_query_service import select_all, select_by_id, select_one

router = APIRouter(prefix="/supply-chain", tags=["hb-product-center"])

_VALID_EVENT_TYPES = {e.value for e in SupplyChainEventType}
_VALID_COMPLIANCE = {e.value for e in ComplianceStatus}
_VALID_CATEGORIES = {e.value for e in ProductCategory}
_VALID_COLLECTIONS = {e.value for e in ProductCollection}
_VALID_SEASONS = {e.value for e in ProductSeason}
_VALID_PRODUCT_STATUSES = {e.value for e in ProductStatus}


def _sanitize_event_row(row: dict) -> HbSupplyChainEventOut:
    row = dict(row)
    if "event_type" in row and row["event_type"] is not None:
        val = str(row["event_type"]).strip().lower()
        row["event_type"] = val if val in _VALID_EVENT_TYPES else "shipped"
    return HbSupplyChainEventOut(**row)


def _sanitize_sustainability_row(row: dict) -> HbSustainabilityMetricOut:
    row = dict(row)
    if "compliance_status" in row and row["compliance_status"] is not None:
        val = str(row["compliance_status"]).strip().lower()
        row["compliance_status"] = val if val in _VALID_COMPLIANCE else "pending_review"
    if "certifications" in row and row["certifications"] is not None:
        val = row["certifications"]
        if isinstance(val, str):
            try:
                row["certifications"] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                row["certifications"] = None
    return HbSustainabilityMetricOut(**row)


def _sanitize_product_row(row: dict) -> HbProductOut:
    row = dict(row)
    for field, valid, default in [
        ("category", _VALID_CATEGORIES, "accessories"),
        ("collection", _VALID_COLLECTIONS, "BOSS"),
        ("season", _VALID_SEASONS, "SS25"),
        ("status", _VALID_PRODUCT_STATUSES, "active"),
    ]:
        if field in row and row[field] is not None:
            val = str(row[field]).strip()
            val_lower = val.lower()
            row[field] = val if val in valid else (val_lower if val_lower in valid else default)
    return HbProductOut(**row)


def get_ws(runtime: RuntimeDep) -> WorkspaceClient:
    """Get WorkspaceClient from runtime (uses app SP identity)."""
    return runtime.ws


WsDep = Annotated[WorkspaceClient, Depends(get_ws)]


@router.get("/events", response_model=list[HbSupplyChainEventOut], operation_id="hb_listSupplyChainEvents")
def list_supply_chain_events(
    ws: WsDep,
    page: Pagination,
    product_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
):
    """List supply chain events from Unity Catalog."""
    filters: dict[str, object] = {}
    if product_id:
        filters["product_id"] = product_id
    if event_type:
        filters["event_type"] = event_type
    if country:
        filters["country"] = country

    rows = select_all(
        ws, "hb_supply_chain_events", filters=filters,
        order_by_column="event_date", order_desc=True,
        limit=page.limit, offset=page.skip,
    )
    return [_sanitize_event_row(row) for row in rows]

@router.get("/products/{product_id}/journey", response_model=HbProductJourney, operation_id="hb_getProductJourney")
def get_product_journey(product_id: int, ws: WsDep):
    """Get full product journey from Unity Catalog."""
    product = select_by_id(ws, "hb_products", product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    events = select_all(
        ws, "hb_supply_chain_events",
        filters={"product_id": product_id},
        order_by_column="event_date",
        order_desc=False,
        limit=100,
    )

    sustainability = select_one(
        ws, "hb_sustainability_metrics", filters={"product_id": product_id}
    )

    return HbProductJourney(
        product=_sanitize_product_row(product),
        events=[_sanitize_event_row(e) for e in events],
        sustainability=_sanitize_sustainability_row(sustainability) if sustainability else None,
    )


@router.get("/sustainability", response_model=list[HbSustainabilityMetricOut], operation_id="hb_listSustainabilityMetrics")
def list_sustainability_metrics(
    ws: WsDep,
    page: Pagination,
):
    """List sustainability metrics from Unity Catalog."""
    rows = select_all(ws, "hb_sustainability_metrics", limit=page.limit, offset=page.skip)
    return [_sanitize_sustainability_row(row) for row in rows]

@router.get("/sustainability/{product_id}", response_model=HbSustainabilityMetricOut, operation_id="hb_getProductSustainability")
def get_product_sustainability(product_id: int, ws: WsDep):
    """Get sustainability metrics for a product from Unity Catalog."""
    metric = select_one(
        ws, "hb_sustainability_metrics", filters={"product_id": product_id}
    )
    if not metric:
        raise HTTPException(status_code=404, detail="Sustainability metrics not found")
    return _sanitize_sustainability_row(metric)