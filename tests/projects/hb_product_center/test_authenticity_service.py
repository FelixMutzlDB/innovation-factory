"""HB Product Center authenticity service tests.

Covers:
  - generate_verification_result(): pure function — status/confidence ranges
  - verify_product(): DB-backed — confidence set, status updated, alerts
    created only for suspicious/counterfeit outcomes

Randomness: both functions call random.choices() internally. Tests avoid
fixing the seed; instead they verify invariants that must hold for any outcome.
"""
from __future__ import annotations

import pytest

import innovation_factory.backend.projects.hb_product_center.models  # noqa: F401
from innovation_factory.backend.projects.hb_product_center.services.authenticity_service import (
    generate_verification_result,
    verify_product,
)
from innovation_factory.backend.projects.hb_product_center.models import (
    AlertResolution,
    AlertSeverity,
    HbAuthAlert,
    HbAuthVerification,
    HbProduct,
    RequesterType,
    VerificationMethod,
    VerificationStatus,
    ProductCategory,
    ProductCollection,
    ProductSeason,
    ProductStatus,
)


# ---------------------------------------------------------------------------
# generate_verification_result — pure function
# ---------------------------------------------------------------------------


class TestGenerateVerificationResult:
    def test_returns_two_tuple(self):
        result = generate_verification_result()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_status_is_valid(self):
        valid = {e.value for e in VerificationStatus}
        for _ in range(50):
            status, confidence = generate_verification_result()
            assert status in valid, f"unexpected status {status!r}"

    def test_confidence_in_unit_range(self):
        for _ in range(50):
            _, confidence = generate_verification_result()
            assert 0.0 < confidence <= 1.0, f"confidence {confidence} outside (0,1]"

    def test_confidence_is_float(self):
        _, confidence = generate_verification_result()
        assert isinstance(confidence, float)

    def test_verified_confidence_is_high(self):
        """Verified outcomes should have confidence >= 0.88."""
        for _ in range(200):
            status, confidence = generate_verification_result()
            if status == VerificationStatus.verified.value:
                assert confidence >= 0.88, (
                    f"verified confidence {confidence} below expected threshold 0.88"
                )

    def test_counterfeit_confidence_is_low(self):
        """Counterfeit outcomes should have confidence < 0.41."""
        for _ in range(500):
            status, confidence = generate_verification_result()
            if status == VerificationStatus.counterfeit.value:
                assert confidence < 0.41, (
                    f"counterfeit confidence {confidence} unexpectedly high"
                )
                return  # found a counterfeit case — test passes
        pytest.skip("no counterfeit outcome in 500 iterations (low probability path)")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_product(session) -> HbProduct:
    import random
    suffix = random.randint(0, 999999)
    p = HbProduct(
        sku=f"AUTH-TST-{suffix}-M",
        style_name="Auth Test Jacket",
        color="Blue",
        color_code="#00F",
        size="M",
        category=ProductCategory.outerwear,
        collection=ProductCollection.boss,
        season=ProductSeason.ss25,
        material="Nylon",
        price=199.0,
        status=ProductStatus.active,
    )
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


def _make_verification(session, product_id=None) -> HbAuthVerification:
    v = HbAuthVerification(
        product_id=product_id,
        requester_type=RequesterType.customer,
        requester_name="Test Requester",
        verification_method=VerificationMethod.image_analysis,
        region="DE",
        status=VerificationStatus.pending,
    )
    session.add(v)
    session.commit()
    session.refresh(v)
    return v


# ---------------------------------------------------------------------------
# verify_product — DB-backed
# ---------------------------------------------------------------------------


class TestVerifyProduct:
    def test_verification_status_updated(self, session):
        p = _make_product(session)
        v = _make_verification(session, product_id=p.id)
        assert v.status == VerificationStatus.pending

        verify_product(session, v)

        assert v.status != VerificationStatus.pending

    def test_confidence_score_set(self, session):
        p = _make_product(session)
        v = _make_verification(session, product_id=p.id)

        verify_product(session, v)

        assert v.confidence_score is not None
        assert 0.0 < v.confidence_score <= 1.0

    def test_completed_at_set(self, session):
        p = _make_product(session)
        v = _make_verification(session, product_id=p.id)

        verify_product(session, v)

        assert v.completed_at is not None

    def test_alert_created_for_suspicious(self, session):
        """When verification outcome is suspicious, an HbAuthAlert must be created."""
        from sqlmodel import select as sq_select

        for _ in range(200):
            p = _make_product(session)
            v = _make_verification(session, product_id=p.id)
            verify_product(session, v)
            session.commit()

            if v.status == VerificationStatus.suspicious:
                alerts = session.exec(
                    sq_select(HbAuthAlert).where(
                        HbAuthAlert.verification_id == v.id
                    )
                ).all()
                assert len(alerts) == 1, "suspicious outcome should create exactly 1 alert"
                assert alerts[0].severity == AlertSeverity.high
                assert alerts[0].resolution == AlertResolution.open
                return

        pytest.skip("no suspicious outcome in 200 iterations")

    def test_alert_created_for_counterfeit(self, session):
        """Counterfeit outcome must produce a critical alert."""
        from sqlmodel import select as sq_select

        for _ in range(500):
            p = _make_product(session)
            v = _make_verification(session, product_id=p.id)
            verify_product(session, v)
            session.commit()

            if v.status == VerificationStatus.counterfeit:
                alerts = session.exec(
                    sq_select(HbAuthAlert).where(
                        HbAuthAlert.verification_id == v.id
                    )
                ).all()
                assert len(alerts) == 1
                assert alerts[0].severity == AlertSeverity.critical
                return

        pytest.skip("no counterfeit outcome in 500 iterations (probability ~5%)")

    def test_no_alert_for_verified(self, session):
        """Verified outcome must NOT create any alerts."""
        from sqlmodel import select as sq_select

        for _ in range(200):
            p = _make_product(session)
            v = _make_verification(session, product_id=p.id)
            verify_product(session, v)
            session.commit()

            if v.status == VerificationStatus.verified:
                alerts = session.exec(
                    sq_select(HbAuthAlert).where(
                        HbAuthAlert.verification_id == v.id
                    )
                ).all()
                assert alerts == [], "verified outcome must not create alerts"
                return

        pytest.skip("no verified outcome in 200 iterations")

    def test_alert_description_contains_confidence(self, session):
        """Alert description should mention confidence for traceability."""
        from sqlmodel import select as sq_select

        for _ in range(300):
            p = _make_product(session)
            v = _make_verification(session, product_id=p.id)
            verify_product(session, v)
            session.commit()

            if v.status in (VerificationStatus.suspicious, VerificationStatus.counterfeit):
                alerts = session.exec(
                    sq_select(HbAuthAlert).where(
                        HbAuthAlert.verification_id == v.id
                    )
                ).all()
                assert len(alerts) > 0
                # The description should contain the confidence value
                assert str(v.confidence_score) in alerts[0].description or \
                       "Confidence:" in alerts[0].description
                return

        pytest.skip("no non-verified outcome in 300 iterations")

    def test_verification_without_product_id(self, session):
        """Verifications without a linked product_id should still succeed."""
        v = _make_verification(session, product_id=None)
        assert v.product_id is None

        result = verify_product(session, v)

        assert result.confidence_score is not None
        assert result.status != VerificationStatus.pending
