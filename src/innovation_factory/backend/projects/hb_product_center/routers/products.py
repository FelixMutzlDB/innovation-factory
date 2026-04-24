"""Product catalog and image management endpoints using Unity Catalog."""

from typing import Annotated, Optional

from databricks.sdk import WorkspaceClient
from fastapi import APIRouter, Depends, HTTPException, Query

from ....dependencies import RuntimeDep
from ..models import (
    HbProductImageOut,
    HbProductOut,
    ImageType,
    ProductCategory,
    ProductCollection,
    ProductSeason,
    ProductStatus,
)
from ..services.uc_query_service import search_like, select_all, select_by_id

router = APIRouter(prefix="/products", tags=["hb-product-center"])

_VALID_CATEGORIES = {e.value for e in ProductCategory}
_VALID_COLLECTIONS = {e.value for e in ProductCollection}
_VALID_SEASONS = {e.value for e in ProductSeason}
_VALID_PRODUCT_STATUSES = {e.value for e in ProductStatus}
_VALID_IMAGE_TYPES = {e.value for e in ImageType}


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


def _sanitize_image_row(row: dict) -> HbProductImageOut:
    row = dict(row)
    if "image_type" in row and row["image_type"] is not None:
        val = str(row["image_type"]).strip().lower()
        row["image_type"] = val if val in _VALID_IMAGE_TYPES else "master"
    return HbProductImageOut(**row)


def get_ws(runtime: RuntimeDep) -> WorkspaceClient:
    """Get WorkspaceClient from runtime (uses app SP identity)."""
    return runtime.ws


WsDep = Annotated[WorkspaceClient, Depends(get_ws)]


@router.get("", response_model=list[HbProductOut], operation_id="hb_listProducts")
def list_products(
    ws: WsDep,
    category: Optional[str] = Query(None),
    collection: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    """List products from Unity Catalog.

    Every filter value is routed through the safe `filters` dict (equality)
    or through `search_like` (LIKE with escaped wildcards). No raw SQL is
    built from `search` / `category` / etc. — the SQL-injection regression
    that traced back here (CVE-style LIKE wildcard bypass) is closed by
    the allowlist + escape combo inside uc_query_service.
    """
    filters: dict[str, object] = {}
    if category:
        filters["category"] = category
    if collection:
        filters["collection"] = collection
    if season:
        filters["season"] = season

    if search:
        rows = search_like(
            ws,
            "hb_products",
            columns=["style_name", "sku"],
            term=search,
            filters=filters,
            order_by_column="created_at",
            order_desc=True,
            limit=limit,
            offset=offset,
        )
    else:
        rows = select_all(
            ws,
            "hb_products",
            filters=filters,
            order_by_column="created_at",
            order_desc=True,
            limit=limit,
            offset=offset,
        )
    return [_sanitize_product_row(row) for row in rows]

@router.get("/{product_id}", response_model=HbProductOut, operation_id="hb_getProduct")
def get_product(product_id: int, ws: WsDep):
    """Get a single product by ID from Unity Catalog."""
    row = select_by_id(ws, "hb_products", product_id)
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return _sanitize_product_row(row)

@router.get("/{product_id}/images", response_model=list[HbProductImageOut], operation_id="hb_getProductImages")
def get_product_images(product_id: int, ws: WsDep):
    """Get product images from Unity Catalog."""
    try:
        rows = select_all(ws, "hb_product_images", filters={"product_id": product_id})
        return [_sanitize_image_row(row) for row in rows]
    except RuntimeError:
        return []
