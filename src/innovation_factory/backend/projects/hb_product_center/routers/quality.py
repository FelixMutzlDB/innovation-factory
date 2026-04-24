"""Quality control inspection and defect endpoints using Unity Catalog."""

from typing import Annotated, Optional

from databricks.sdk import WorkspaceClient
from fastapi import APIRouter, Depends, HTTPException, Query

from ....dependencies import RuntimeDep
from ....pagination import Pagination
from ..models import (
    DefectSeverity,
    DefectType,
    HbInspectionDetailOut,
    HbProductOut,
    HbQualityDefectOut,
    HbQualityInspectionCreate,
    HbQualityInspectionOut,
    HbQualityInspectionUpdate,
    HbQualityStats,
    InspectionStatus,
    ProductCategory,
    ProductCollection,
    ProductSeason,
    ProductStatus,
)
from ..services.uc_query_service import (
    select_all,
    select_by_id,
    insert_row,
    update_row,
    execute_query,
    get_table_name,
)

router = APIRouter(prefix="/quality", tags=["hb-product-center"])

_VALID_INSPECTION_STATUSES = {e.value for e in InspectionStatus}
_VALID_DEFECT_TYPES = {e.value for e in DefectType}
_VALID_DEFECT_SEVERITIES = {e.value for e in DefectSeverity}
_VALID_CATEGORIES = {e.value for e in ProductCategory}
_VALID_COLLECTIONS = {e.value for e in ProductCollection}
_VALID_SEASONS = {e.value for e in ProductSeason}
_VALID_PRODUCT_STATUSES = {e.value for e in ProductStatus}


def _sanitize_inspection_row(row: dict) -> HbQualityInspectionOut:
    row = dict(row)
    if "status" in row and row["status"] is not None:
        val = str(row["status"]).strip().lower()
        row["status"] = val if val in _VALID_INSPECTION_STATUSES else "pending"
    return HbQualityInspectionOut(**row)


def _sanitize_defect_row(row: dict) -> HbQualityDefectOut:
    row = dict(row)
    if "defect_type" in row and row["defect_type"] is not None:
        val = str(row["defect_type"]).strip().lower()
        row["defect_type"] = val if val in _VALID_DEFECT_TYPES else "fabric_flaw"
    if "severity" in row and row["severity"] is not None:
        val = str(row["severity"]).strip().lower()
        row["severity"] = val if val in _VALID_DEFECT_SEVERITIES else "minor"
    return HbQualityDefectOut(**row)


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


@router.get("/inspections", response_model=list[HbQualityInspectionOut], operation_id="hb_listInspections")
def list_inspections(
    ws: WsDep,
    page: Pagination,
    status: Optional[str] = Query(None),
    product_id: Optional[int] = Query(None),
):
    """List quality inspections from Unity Catalog."""
    filters: dict[str, object] = {}
    if status:
        filters["status"] = status
    if product_id:
        filters["product_id"] = product_id

    rows = select_all(
        ws, "hb_quality_inspections", filters=filters,
        order_by_column="created_at", order_desc=True,
        limit=page.limit, offset=page.skip,
    )
    return [_sanitize_inspection_row(row) for row in rows]

@router.get("/inspections/{inspection_id}", response_model=HbInspectionDetailOut, operation_id="hb_getInspection")
def get_inspection(inspection_id: int, ws: WsDep):
    """Get inspection details including defects from Unity Catalog."""
    inspection = select_by_id(ws, "hb_quality_inspections", inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    sanitized = _sanitize_inspection_row(inspection)
    defects = select_all(ws, "hb_quality_defects", filters={"inspection_id": inspection_id})
    product = select_by_id(ws, "hb_products", inspection["product_id"]) if inspection.get("product_id") else None

    return HbInspectionDetailOut(
        **sanitized.model_dump(),
        defects=[_sanitize_defect_row(d) for d in defects],
        product=_sanitize_product_row(product) if product else None,
    )


@router.post("/inspections", response_model=HbQualityInspectionOut, operation_id="hb_createInspection")
def create_inspection(data: HbQualityInspectionCreate, ws: WsDep):
    """Create a new quality inspection in Unity Catalog."""
    product = select_by_id(ws, "hb_products", data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    from datetime import datetime, timezone
    from ..services.quality_service import generate_inspection_score

    # Generate inspection results
    score, status = generate_inspection_score()

    inspection_data = {
        **data.model_dump(),
        "overall_score": score,
        "status": status,
        "created_at": datetime.now(timezone.utc),
    }

    insert_row(ws, "hb_quality_inspections", inspection_data)

    # Return the created inspection
    rows = select_all(ws, "hb_quality_inspections", order_by_column="id", order_desc=True, limit=1)
    return _sanitize_inspection_row(rows[0]) if rows else HbQualityInspectionOut(**inspection_data, id=0)  # type: ignore[arg-type]

@router.patch("/inspections/{inspection_id}", response_model=HbQualityInspectionOut, operation_id="hb_updateInspection")
def update_inspection(inspection_id: int, data: HbQualityInspectionUpdate, ws: WsDep):
    """Update an inspection in Unity Catalog."""
    inspection = select_by_id(ws, "hb_quality_inspections", inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        update_row(ws, "hb_quality_inspections", inspection_id, update_data)

    updated = select_by_id(ws, "hb_quality_inspections", inspection_id)
    return _sanitize_inspection_row(updated) if updated else _sanitize_inspection_row(inspection)

@router.get("/stats", response_model=HbQualityStats, operation_id="hb_getQualityStats")
def get_quality_stats(ws: WsDep):
    """Get quality statistics from Unity Catalog."""
    insp_table = get_table_name("hb_quality_inspections")
    defect_table = get_table_name("hb_quality_defects")

    # Status counts
    status_sql = f"SELECT status, COUNT(*) as cnt FROM {insp_table} GROUP BY status"
    status_rows = execute_query(ws, status_sql)
    status_counts = {row[0]: int(row[1]) for row in status_rows}

    # Average score
    avg_sql = f"SELECT AVG(overall_score) FROM {insp_table} WHERE overall_score > 0"
    avg_rows = execute_query(ws, avg_sql)
    avg_score = float(avg_rows[0][0]) if avg_rows and avg_rows[0][0] else 0.0

    # Total count
    total_sql = f"SELECT COUNT(*) FROM {insp_table}"
    total_rows = execute_query(ws, total_sql)
    total = int(total_rows[0][0]) if total_rows else 0

    # Defect counts by type
    defect_sql = f"SELECT defect_type, COUNT(*) as cnt FROM {defect_table} GROUP BY defect_type"
    defect_rows = execute_query(ws, defect_sql)
    defect_counts = {row[0]: int(row[1]) for row in defect_rows}

    # Severity counts
    severity_sql = f"SELECT severity, COUNT(*) as cnt FROM {defect_table} GROUP BY severity"
    severity_rows = execute_query(ws, severity_sql)
    severity_counts = {row[0]: int(row[1]) for row in severity_rows}

    return HbQualityStats(
        total_inspections=total,
        approved=status_counts.get("approved", 0),
        rejected=status_counts.get("rejected", 0),
        pending=status_counts.get("pending", 0),
        in_review=status_counts.get("in_review", 0),
        avg_score=round(avg_score, 1),
        defect_counts=defect_counts,
        severity_counts=severity_counts,
    )
