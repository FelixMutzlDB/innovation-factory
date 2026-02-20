"""Product catalog and image management endpoints."""

from typing import Optional

from fastapi import APIRouter, Query
from sqlmodel import select

from ....dependencies import SessionDep
from ..models import (
    HbProduct,
    HbProductImage,
    HbProductImageOut,
    HbProductOut,
)

router = APIRouter(prefix="/products", tags=["hb-product-center"])


@router.get("", response_model=list[HbProductOut], operation_id="hb_listProducts")
def list_products(
    session: SessionDep,
    category: Optional[str] = Query(None),
    collection: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    stmt = select(HbProduct)
    if category:
        stmt = stmt.where(HbProduct.category == category)
    if collection:
        stmt = stmt.where(HbProduct.collection == collection)
    if season:
        stmt = stmt.where(HbProduct.season == season)
    if search:
        stmt = stmt.where(
            HbProduct.style_name.ilike(f"%{search}%")  # type: ignore[union-attr]
            | HbProduct.sku.ilike(f"%{search}%")  # type: ignore[union-attr]
        )
    stmt = stmt.order_by(HbProduct.created_at.desc()).offset(offset).limit(limit)  # type: ignore[union-attr]
    return list(session.exec(stmt).all())


@router.get("/{product_id}", response_model=HbProductOut, operation_id="hb_getProduct")
def get_product(product_id: int, session: SessionDep):
    product = session.get(HbProduct, product_id)
    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{product_id}/images", response_model=list[HbProductImageOut], operation_id="hb_getProductImages")
def get_product_images(product_id: int, session: SessionDep):
    stmt = select(HbProductImage).where(HbProductImage.product_id == product_id)
    return list(session.exec(stmt).all())
