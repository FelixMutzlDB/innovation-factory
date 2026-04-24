"""Authenticity verification and alert endpoints using Unity Catalog."""

from typing import Annotated, Optional

from databricks.sdk import WorkspaceClient
from fastapi import APIRouter, Depends, HTTPException, Query

from ....dependencies import RuntimeDep
from ....pagination import Pagination
from ..models import (
    AlertResolution,
    AlertSeverity,
    HbAuthAlertOut,
    HbAuthAlertUpdate,
    HbAuthVerificationCreate,
    HbAuthVerificationOut,
    RequesterType,
    VerificationMethod,
    VerificationStatus,
)
from ..services.uc_query_service import select_all, select_by_id, insert_row, update_row

router = APIRouter(prefix="/authenticity", tags=["hb-product-center"])

_VALID_REQUESTER_TYPES = {e.value for e in RequesterType}
_VALID_VERIFICATION_STATUSES = {e.value for e in VerificationStatus}
_VALID_VERIFICATION_METHODS = {e.value for e in VerificationMethod}
_VALID_ALERT_SEVERITIES = {e.value for e in AlertSeverity}
_VALID_ALERT_RESOLUTIONS = {e.value for e in AlertResolution}


def _sanitize_verification_row(row: dict) -> HbAuthVerificationOut:
    """Normalise UC row values so they pass Pydantic enum validation."""
    row = dict(row)
    if "requester_type" in row and row["requester_type"] is not None:
        val = str(row["requester_type"]).strip().lower()
        row["requester_type"] = val if val in _VALID_REQUESTER_TYPES else "internal"
    if "status" in row and row["status"] is not None:
        val = str(row["status"]).strip().lower()
        row["status"] = val if val in _VALID_VERIFICATION_STATUSES else "pending"
    if "verification_method" in row and row["verification_method"] is not None:
        val = str(row["verification_method"]).strip().lower()
        row["verification_method"] = val if val in _VALID_VERIFICATION_METHODS else "image_analysis"
    return HbAuthVerificationOut(**row)


def _sanitize_alert_row(row: dict) -> HbAuthAlertOut:
    """Normalise UC row values so they pass Pydantic enum validation."""
    row = dict(row)
    if "severity" in row and row["severity"] is not None:
        val = str(row["severity"]).strip().lower()
        row["severity"] = val if val in _VALID_ALERT_SEVERITIES else "medium"
    if "resolution" in row and row["resolution"] is not None:
        val = str(row["resolution"]).strip().lower()
        row["resolution"] = val if val in _VALID_ALERT_RESOLUTIONS else "open"
    return HbAuthAlertOut(**row)


def get_ws(runtime: RuntimeDep) -> WorkspaceClient:
    """Get WorkspaceClient from runtime (uses app SP identity)."""
    return runtime.ws


WsDep = Annotated[WorkspaceClient, Depends(get_ws)]


@router.get("/verifications", response_model=list[HbAuthVerificationOut], operation_id="hb_listVerifications")
def list_verifications(
    ws: WsDep,
    page: Pagination,
    status: Optional[str] = Query(None),
    requester_type: Optional[str] = Query(None),
):
    """List authenticity verifications from Unity Catalog."""
    filters: dict[str, object] = {}
    if status:
        filters["status"] = status
    if requester_type:
        filters["requester_type"] = requester_type

    rows = select_all(
        ws, "hb_auth_verifications", filters=filters,
        order_by_column="created_at", order_desc=True,
        limit=page.limit, offset=page.skip,
    )
    return [_sanitize_verification_row(row) for row in rows]

@router.get("/verifications/{verification_id}", response_model=HbAuthVerificationOut, operation_id="hb_getVerification")
def get_verification(verification_id: int, ws: WsDep):
    """Get a verification by ID from Unity Catalog."""
    v = select_by_id(ws, "hb_auth_verifications", verification_id)
    if not v:
        raise HTTPException(status_code=404, detail="Verification not found")
    return _sanitize_verification_row(v)

@router.post("/verify", response_model=HbAuthVerificationOut, operation_id="hb_createVerification")
def create_verification(data: HbAuthVerificationCreate, ws: WsDep):
    """Create a new verification in Unity Catalog."""
    from datetime import datetime, timezone
    from ..services.authenticity_service import generate_verification_result

    status, confidence = generate_verification_result()

    verification_data = {
        **data.model_dump(),
        "status": status,
        "confidence_score": confidence,
        "created_at": datetime.now(timezone.utc),
    }

    insert_row(ws, "hb_auth_verifications", verification_data)

    rows = select_all(ws, "hb_auth_verifications", order_by_column="id", order_desc=True, limit=1)
    return _sanitize_verification_row(rows[0]) if rows else HbAuthVerificationOut(**verification_data, id=0)  # type: ignore[arg-type]

@router.get("/alerts", response_model=list[HbAuthAlertOut], operation_id="hb_listAlerts")
def list_alerts(
    ws: WsDep,
    page: Pagination,
    resolution: Optional[str] = Query(None),
):
    """List authenticity alerts from Unity Catalog."""
    filters: dict[str, object] = {}
    if resolution:
        filters["resolution"] = resolution

    rows = select_all(
        ws, "hb_auth_alerts", filters=filters,
        order_by_column="created_at", order_desc=True,
        limit=page.limit, offset=page.skip,
    )
    return [_sanitize_alert_row(row) for row in rows]

@router.patch("/alerts/{alert_id}", response_model=HbAuthAlertOut, operation_id="hb_updateAlert")
def update_alert(alert_id: int, data: HbAuthAlertUpdate, ws: WsDep):
    """Update an alert in Unity Catalog."""
    alert = select_by_id(ws, "hb_auth_alerts", alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        update_row(ws, "hb_auth_alerts", alert_id, update_data)

    updated = select_by_id(ws, "hb_auth_alerts", alert_id)
    return _sanitize_alert_row(updated) if updated else HbAuthAlertOut(**alert)