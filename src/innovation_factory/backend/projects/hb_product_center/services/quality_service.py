"""Simulated quality scoring service.

Provides mock AI-powered defect detection and quality scoring.
Designed to be replaced with real Databricks Model Serving endpoint calls.
"""

import random
from datetime import datetime, timezone

from sqlmodel import Session

from ..models import (
    DefectSeverity,
    DefectType,
    HbQualityDefect,
    HbQualityInspection,
    InspectionStatus,
)

_rng = random.Random()

DEFECT_LOCATIONS = [
    "Left shoulder seam", "Right cuff area", "Front panel center",
    "Back collar region", "Button placket", "Lapel edge",
    "Hem area", "Sleeve attachment point", "Pocket lining",
    "Zipper track", "Inner lining", "Waistband",
]


def run_quality_inspection(session: Session, inspection: HbQualityInspection) -> HbQualityInspection:
    """Simulate an AI quality inspection with defect detection."""
    inspection.status = InspectionStatus.in_review

    n_defects = _rng.choices([0, 1, 2, 3, 4], weights=[40, 30, 15, 10, 5])[0]

    if n_defects == 0:
        score = round(_rng.uniform(92, 100), 1)
    elif n_defects <= 2:
        score = round(_rng.uniform(70, 91), 1)
    else:
        score = round(_rng.uniform(35, 69), 1)

    inspection.overall_score = score

    for _ in range(n_defects):
        severity_weights = [4, 3, 2, 1]
        severity = _rng.choices(list(DefectSeverity), weights=severity_weights)[0]

        defect = HbQualityDefect(
            inspection_id=inspection.id,
            defect_type=_rng.choice(list(DefectType)),
            severity=severity,
            location_description=_rng.choice(DEFECT_LOCATIONS),
            confidence_score=round(_rng.uniform(0.7, 0.99), 3),
        )
        session.add(defect)

    if score >= 85 and n_defects <= 1:
        inspection.status = InspectionStatus.approved
        inspection.completed_at = datetime.now(timezone.utc)
    elif score < 50:
        inspection.status = InspectionStatus.rejected
        inspection.completed_at = datetime.now(timezone.utc)

    session.add(inspection)
    session.flush()
    return inspection
