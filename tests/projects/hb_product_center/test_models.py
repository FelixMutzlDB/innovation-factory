"""HB Product Center model tests.

Covers:
  - Enum values / completeness (no prefix collisions)
  - Pydantic I/O model serialisation round-trips
  - 3-model pattern: every API entity has both *Out and *Create/*Update
  - HbDashboardSummary and HbProductJourney aggregate shapes
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from innovation_factory.backend.projects.hb_product_center import models as hb_models


# ---------------------------------------------------------------------------
# Enum completeness
# ---------------------------------------------------------------------------


class TestEnumValues:
    def test_product_category_has_expected_members(self):
        members = {e.value for e in hb_models.ProductCategory}
        assert "suits" in members
        assert "shoes" in members
        assert "fragrances" in members

    def test_defect_severity_has_four_levels(self):
        assert len(list(hb_models.DefectSeverity)) == 4
        values = {e.value for e in hb_models.DefectSeverity}
        assert values == {"minor", "moderate", "major", "critical"}

    def test_inspection_status_covers_lifecycle(self):
        values = {e.value for e in hb_models.InspectionStatus}
        assert "pending" in values
        assert "approved" in values
        assert "rejected" in values
        assert "in_review" in values

    def test_verification_status_covers_all_outcomes(self):
        values = {e.value for e in hb_models.VerificationStatus}
        assert {"pending", "verified", "suspicious", "counterfeit"}.issubset(values)

    def test_supply_chain_event_type_includes_key_events(self):
        values = {e.value for e in hb_models.SupplyChainEventType}
        assert "manufactured" in values
        assert "shipped" in values
        assert "sold" in values

    def test_alert_resolution_has_confirmed_counterfeit(self):
        values = {e.value for e in hb_models.AlertResolution}
        assert "confirmed_counterfeit" in values
        assert "false_positive" in values


# ---------------------------------------------------------------------------
# 3-model pattern
# ---------------------------------------------------------------------------


class TestThreeModelPattern:
    """Every API-surfaced entity must have <Entity> (SQLModel), <Entity>Out
    (Pydantic response), and where applicable <Entity>Create or <Entity>Update.
    """

    @pytest.mark.parametrize(
        "table_cls, out_cls, input_cls",
        [
            ("HbProduct", "HbProductOut", None),
            ("HbRecognitionJob", "HbRecognitionJobOut", "HbRecognitionJobCreate"),
            ("HbQualityInspection", "HbQualityInspectionOut", "HbQualityInspectionCreate"),
            ("HbQualityDefect", "HbQualityDefectOut", None),
            ("HbAuthVerification", "HbAuthVerificationOut", "HbAuthVerificationCreate"),
            ("HbAuthAlert", "HbAuthAlertOut", "HbAuthAlertUpdate"),
            ("HbSupplyChainEvent", "HbSupplyChainEventOut", None),
            ("HbSustainabilityMetric", "HbSustainabilityMetricOut", None),
            ("HbChatSession", None, None),  # internal — no Out required
        ],
    )
    def test_models_exist(self, table_cls, out_cls, input_cls):
        assert hasattr(hb_models, table_cls), f"missing table model: {table_cls}"
        if out_cls:
            assert hasattr(hb_models, out_cls), f"missing Out model: {out_cls}"
        if input_cls:
            assert hasattr(hb_models, input_cls), f"missing input model: {input_cls}"


# ---------------------------------------------------------------------------
# Pydantic serialization round-trips
# ---------------------------------------------------------------------------


def _now():
    return datetime.now(timezone.utc)


class TestHbProductOutSerialization:
    def test_round_trip(self):
        data = dict(
            id=1,
            sku="BOS-001-BLK-50R",
            style_name="Boss Slim Fit Suit",
            color="Black",
            color_code="#000000",
            size="50R",
            category="suits",
            collection="BOSS",
            season="SS25",
            material="Wool",
            price=599.0,
            status="active",
            country_of_origin="Germany",
            supplier_name="Premium Tailors GmbH",
            created_at=_now(),
        )
        out = hb_models.HbProductOut(**data)  # type: ignore[invalid-argument-type]
        assert out.sku == "BOS-001-BLK-50R"
        assert out.category == hb_models.ProductCategory.suits
        assert out.collection == hb_models.ProductCollection.boss
        assert out.season == hb_models.ProductSeason.ss25

    def test_model_dump_contains_all_fields(self):
        data = dict(
            id=2,
            sku="HUG-002-WHT-M",
            style_name="Hugo Basic Tee",
            color="White",
            color_code="#FFFFFF",
            size="M",
            category="shirts",
            collection="HUGO",
            season="FW25",
            material="Cotton",
            price=49.0,
            status="active",
            country_of_origin="Portugal",
            supplier_name="TextileCo",
            created_at=_now(),
        )
        out = hb_models.HbProductOut(**data)  # type: ignore[invalid-argument-type]
        d = out.model_dump()
        assert "id" in d
        assert "sku" in d
        assert "price" in d


class TestHbQualityInspectionSerialization:
    def test_defaults_populated(self):
        insp = hb_models.HbQualityInspectionOut(
            id=10,
            product_id=1,
            batch_number="B-2026-001",
            inspector="Anna K.",
            manufacturing_partner="PartnerCo",
            overall_score=87.5,
            status=hb_models.InspectionStatus.approved,
            created_at=_now(),
        )
        assert insp.notes is None
        assert insp.completed_at is None

    def test_update_model_all_optional(self):
        """HbQualityInspectionUpdate must accept empty dict (all fields optional)."""
        update = hb_models.HbQualityInspectionUpdate()
        assert update.status is None
        assert update.overall_score is None
        assert update.notes is None


class TestHbAuthVerificationSerialization:
    def test_confidence_optional(self):
        v = hb_models.HbAuthVerificationOut(
            id=5,
            product_id=None,
            requester_type=hb_models.RequesterType.customer,
            requester_name="Test User",
            status=hb_models.VerificationStatus.pending,
            confidence_score=None,
            verification_method=hb_models.VerificationMethod.image_analysis,
            region="DE",
            created_at=_now(),
        )
        assert v.confidence_score is None

    def test_create_defaults(self):
        create = hb_models.HbAuthVerificationCreate(
            requester_type="customer",
        )
        assert create.verification_method == "image_analysis"
        assert create.region == ""


class TestHbDashboardSummary:
    def test_all_fields_present(self):
        summary = hb_models.HbDashboardSummary(
            total_products=100,
            active_products=80,
            recognition_jobs_today=5,
            recognition_jobs_total=200,
            avg_quality_score=88.0,
            inspections_pending=10,
            auth_success_rate=0.95,
            auth_alerts_open=3,
            supply_chain_events_total=500,
            avg_sustainability_score=72.0,
        )
        assert summary.total_products == 100
        assert summary.auth_success_rate == 0.95

    def test_zero_values_accepted(self):
        summary = hb_models.HbDashboardSummary(
            total_products=0,
            active_products=0,
            recognition_jobs_today=0,
            recognition_jobs_total=0,
            avg_quality_score=0.0,
            inspections_pending=0,
            auth_success_rate=0.0,
            auth_alerts_open=0,
            supply_chain_events_total=0,
            avg_sustainability_score=0.0,
        )
        assert summary.avg_quality_score == 0.0


class TestHbProductJourney:
    def test_sustainability_optional(self):
        product = hb_models.HbProductOut(
            id=1,
            sku="X-001",
            style_name="X Shirt",
            color="Blue",
            color_code="#00F",
            size="L",
            category=hb_models.ProductCategory.shirts,
            collection=hb_models.ProductCollection.boss,
            season=hb_models.ProductSeason.ss25,
            material="Cotton",
            price=99.0,
            status=hb_models.ProductStatus.active,
            country_of_origin="DE",
            supplier_name="X Co",
            created_at=_now(),
        )
        journey = hb_models.HbProductJourney(
            product=product,
            events=[],
            sustainability=None,
        )
        assert journey.sustainability is None
        assert journey.events == []


class TestHbRecognitionJobCreate:
    def test_defaults(self):
        create = hb_models.HbRecognitionJobCreate()
        assert create.job_type == "single"
        assert create.image_count == 1
        assert create.submitted_by is None


class TestHbQualityStats:
    def test_empty_defect_counts(self):
        stats = hb_models.HbQualityStats(
            total_inspections=0,
            approved=0,
            rejected=0,
            pending=0,
            in_review=0,
            avg_score=0.0,
            defect_counts={},
            severity_counts={},
        )
        assert stats.defect_counts == {}
        assert stats.severity_counts == {}
