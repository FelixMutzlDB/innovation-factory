"""Simulated authenticity verification service.

Provides mock counterfeit detection and product authentication.
Designed to be replaced with real Databricks Model Serving endpoint calls.
"""

import random
from datetime import datetime, timezone

from sqlmodel import Session

from ..models import (
    AlertResolution,
    AlertSeverity,
    HbAuthAlert,
    HbAuthVerification,
    VerificationStatus,
)

_rng = random.Random()


def verify_product(session: Session, verification: HbAuthVerification) -> HbAuthVerification:
    """Simulate product authenticity verification."""
    outcome = _rng.choices(
        [VerificationStatus.verified, VerificationStatus.suspicious, VerificationStatus.counterfeit],
        weights=[85, 10, 5],
    )[0]

    if outcome == VerificationStatus.verified:
        confidence = round(_rng.uniform(0.88, 0.99), 3)
    elif outcome == VerificationStatus.suspicious:
        confidence = round(_rng.uniform(0.40, 0.65), 3)
    else:
        confidence = round(_rng.uniform(0.15, 0.40), 3)

    verification.status = outcome
    verification.confidence_score = confidence
    verification.completed_at = datetime.now(timezone.utc)
    session.add(verification)
    session.flush()

    if outcome in (VerificationStatus.suspicious, VerificationStatus.counterfeit):
        alert_type = "Suspected Counterfeit" if outcome == VerificationStatus.counterfeit else "Quality Anomaly Detected"
        severity = AlertSeverity.critical if outcome == VerificationStatus.counterfeit else AlertSeverity.high

        alert = HbAuthAlert(
            verification_id=verification.id,
            alert_type=alert_type,
            severity=severity,
            region=verification.region,
            description=f"{alert_type} detected during {verification.verification_method.value} analysis. Confidence: {confidence}. Region: {verification.region}.",
            resolution=AlertResolution.open,
        )
        session.add(alert)
        session.flush()

    return verification
