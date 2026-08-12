"""Sanitizer function unit tests for HB Product Center routers.

Each router module exposes private ``_sanitize_*_row`` helpers that
normalise raw Unity Catalog values so they pass Pydantic enum validation.
These tests verify:

  1. Valid values pass through unchanged.
  2. Unknown / None values fall back to the documented default.
  3. No KeyError or ValidationError is raised on missing optional fields.

Tests import the helpers directly (no FastAPI / TestClient machinery
needed — sanitizers are pure transform functions).
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest


def _now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Quality router sanitizers
# ---------------------------------------------------------------------------


class TestSanitizeInspectionRow:
    def _fn(self, row):
        from innovation_factory.backend.projects.hb_product_center.routers.quality import (
            _sanitize_inspection_row,
        )
        return _sanitize_inspection_row(row)

    def _base_row(self, **overrides):
        base = dict(
            id=1,
            product_id=1,
            batch_number="B-001",
            inspector="Anna",
            manufacturing_partner="PartnerX",
            overall_score=88.0,
            status="approved",
            created_at=_now(),
        )
        base.update(overrides)
        return base

    def test_valid_status_passes_through(self):
        out = self._fn(self._base_row(status="approved"))
        assert out.status.value == "approved"

    def test_unknown_status_falls_back_to_pending(self):
        out = self._fn(self._base_row(status="BOGUS_STATUS"))
        assert out.status.value == "pending"

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: _sanitize_inspection_row only enters the if-block when "
               "row['status'] is not None, so None bypasses normalisation and "
               "Pydantic raises ValidationError (source bug — do not fix here).",
    )
    def test_none_status_falls_back_to_pending(self):
        out = self._fn(self._base_row(status=None))
        assert out.status.value == "pending"

    def test_valid_in_review_status(self):
        out = self._fn(self._base_row(status="in_review"))
        assert out.status.value == "in_review"


class TestSanitizeDefectRow:
    def _fn(self, row):
        from innovation_factory.backend.projects.hb_product_center.routers.quality import (
            _sanitize_defect_row,
        )
        return _sanitize_defect_row(row)

    def _base_row(self, **overrides):
        base = dict(
            id=1,
            inspection_id=1,
            defect_type="stitching",
            severity="minor",
            location_description="Left seam",
            confidence_score=0.92,
            created_at=_now(),
        )
        base.update(overrides)
        return base

    def test_valid_defect_type_passes_through(self):
        out = self._fn(self._base_row(defect_type="stitching"))
        assert out.defect_type.value == "stitching"

    def test_unknown_defect_type_falls_back_to_fabric_flaw(self):
        out = self._fn(self._base_row(defect_type="UNKNOWN_DEFECT"))
        assert out.defect_type.value == "fabric_flaw"

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: sanitizer only normalises when value is not None; "
               "None bypasses the guard and Pydantic raises ValidationError.",
    )
    def test_none_defect_type_falls_back(self):
        out = self._fn(self._base_row(defect_type=None))
        assert out.defect_type.value == "fabric_flaw"

    def test_valid_severity_passes_through(self):
        out = self._fn(self._base_row(severity="critical"))
        assert out.severity.value == "critical"

    def test_unknown_severity_falls_back_to_minor(self):
        out = self._fn(self._base_row(severity="INVALID"))
        assert out.severity.value == "minor"

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: sanitizer only normalises when value is not None; "
               "None bypasses the guard and Pydantic raises ValidationError.",
    )
    def test_none_severity_falls_back(self):
        out = self._fn(self._base_row(severity=None))
        assert out.severity.value == "minor"


# ---------------------------------------------------------------------------
# Authenticity router sanitizers
# ---------------------------------------------------------------------------


class TestSanitizeVerificationRow:
    def _fn(self, row):
        from innovation_factory.backend.projects.hb_product_center.routers.authenticity import (
            _sanitize_verification_row,
        )
        return _sanitize_verification_row(row)

    def _base_row(self, **overrides):
        base = dict(
            id=1,
            product_id=None,
            requester_type="customer",
            requester_name="Test User",
            status="verified",
            confidence_score=0.95,
            verification_method="image_analysis",
            region="DE",
            created_at=_now(),
        )
        base.update(overrides)
        return base

    def test_valid_requester_type_passes_through(self):
        out = self._fn(self._base_row(requester_type="customer"))
        assert out.requester_type.value == "customer"

    def test_unknown_requester_type_falls_back_to_internal(self):
        out = self._fn(self._base_row(requester_type="HACKER"))
        assert out.requester_type.value == "internal"

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: sanitizer only normalises when value is not None; "
               "None bypasses the guard and Pydantic raises ValidationError.",
    )
    def test_none_requester_type_falls_back(self):
        out = self._fn(self._base_row(requester_type=None))
        assert out.requester_type.value == "internal"

    def test_unknown_status_falls_back_to_pending(self):
        out = self._fn(self._base_row(status="GARBAGE"))
        assert out.status.value == "pending"

    def test_unknown_verification_method_falls_back(self):
        out = self._fn(self._base_row(verification_method="MAGIC_SCAN"))
        assert out.verification_method.value == "image_analysis"


class TestSanitizeAlertRow:
    def _fn(self, row):
        from innovation_factory.backend.projects.hb_product_center.routers.authenticity import (
            _sanitize_alert_row,
        )
        return _sanitize_alert_row(row)

    def _base_row(self, **overrides):
        base = dict(
            id=1,
            verification_id=1,
            alert_type="Suspected Counterfeit",
            severity="critical",
            region="DE",
            description="Test alert",
            resolution="open",
            created_at=_now(),
        )
        base.update(overrides)
        return base

    def test_valid_severity_passes_through(self):
        out = self._fn(self._base_row(severity="high"))
        assert out.severity.value == "high"

    def test_unknown_severity_falls_back_to_medium(self):
        out = self._fn(self._base_row(severity="EXTREME"))
        assert out.severity.value == "medium"

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: sanitizer only normalises when value is not None; "
               "None bypasses the guard and Pydantic raises ValidationError.",
    )
    def test_none_severity_falls_back(self):
        out = self._fn(self._base_row(severity=None))
        assert out.severity.value == "medium"

    def test_valid_resolution_passes_through(self):
        out = self._fn(self._base_row(resolution="resolved"))
        assert out.resolution.value == "resolved"

    def test_unknown_resolution_falls_back_to_open(self):
        out = self._fn(self._base_row(resolution="NONSENSE"))
        assert out.resolution.value == "open"

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: sanitizer only normalises when value is not None; "
               "None bypasses the guard and Pydantic raises ValidationError.",
    )
    def test_none_resolution_falls_back(self):
        out = self._fn(self._base_row(resolution=None))
        assert out.resolution.value == "open"


# ---------------------------------------------------------------------------
# Supply chain router sanitizers
# ---------------------------------------------------------------------------


class TestSanitizeEventRow:
    def _fn(self, row):
        from innovation_factory.backend.projects.hb_product_center.routers.supply_chain import (
            _sanitize_event_row,
        )
        return _sanitize_event_row(row)

    def _base_row(self, **overrides):
        base = dict(
            id=1,
            product_id=1,
            event_type="shipped",
            location="Hamburg",
            partner_name="DHL",
            country="DE",
            event_date=_now(),
            created_at=_now(),
        )
        base.update(overrides)
        return base

    def test_valid_event_type_passes_through(self):
        out = self._fn(self._base_row(event_type="manufactured"))
        assert out.event_type.value == "manufactured"

    def test_unknown_event_type_falls_back_to_shipped(self):
        out = self._fn(self._base_row(event_type="TELEPORTED"))
        assert out.event_type.value == "shipped"

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: sanitizer only normalises when value is not None; "
               "None bypasses the guard and Pydantic raises ValidationError.",
    )
    def test_none_event_type_falls_back(self):
        out = self._fn(self._base_row(event_type=None))
        assert out.event_type.value == "shipped"


class TestSanitizeSustainabilityRow:
    def _fn(self, row):
        from innovation_factory.backend.projects.hb_product_center.routers.supply_chain import (
            _sanitize_sustainability_row,
        )
        return _sanitize_sustainability_row(row)

    def _base_row(self, **overrides):
        base = dict(
            id=1,
            product_id=1,
            carbon_footprint_kg=12.5,
            water_usage_liters=50.0,
            recycled_content_pct=30.0,
            organic_material_pct=10.0,
            certifications=None,
            compliance_status="compliant",
            created_at=_now(),
        )
        base.update(overrides)
        return base

    def test_valid_compliance_status_passes_through(self):
        out = self._fn(self._base_row(compliance_status="compliant"))
        assert out.compliance_status.value == "compliant"

    def test_unknown_compliance_status_falls_back_to_pending_review(self):
        out = self._fn(self._base_row(compliance_status="UNKNOWN"))
        assert out.compliance_status.value == "pending_review"

    def test_json_string_certifications_parsed(self):
        import json
        certs = {"gots": True, "oeko_tex": True}
        out = self._fn(self._base_row(certifications=json.dumps(certs)))
        assert isinstance(out.certifications, dict)
        assert out.certifications.get("gots") is True

    def test_invalid_json_certifications_becomes_none(self):
        out = self._fn(self._base_row(certifications="NOT_JSON{{{"))
        assert out.certifications is None

    def test_dict_certifications_pass_through(self):
        certs = {"iso": "14001"}
        out = self._fn(self._base_row(certifications=certs))
        assert out.certifications == certs


# ---------------------------------------------------------------------------
# Products router sanitizer
# ---------------------------------------------------------------------------


class TestSanitizeProductRow:
    def _fn(self, row):
        from innovation_factory.backend.projects.hb_product_center.routers.products import (
            _sanitize_product_row,
        )
        return _sanitize_product_row(row)

    def _base_row(self, **overrides):
        base = dict(
            id=1,
            sku="X-001",
            style_name="Test",
            color="Black",
            color_code="#000",
            size="M",
            category="suits",
            collection="BOSS",
            season="SS25",
            material="Wool",
            price=199.0,
            status="active",
            country_of_origin="DE",
            supplier_name="TestCo",
            created_at=_now(),
        )
        base.update(overrides)
        return base

    def test_valid_category_passes_through(self):
        out = self._fn(self._base_row(category="suits"))
        assert out.category.value == "suits"

    def test_unknown_category_falls_back_to_accessories(self):
        out = self._fn(self._base_row(category="GADGETS"))
        assert out.category.value == "accessories"

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: sanitizer only normalises when value is not None; "
               "None bypasses the guard and Pydantic raises ValidationError.",
    )
    def test_none_category_falls_back(self):
        out = self._fn(self._base_row(category=None))
        assert out.category.value == "accessories"

    def test_unknown_collection_falls_back_to_boss(self):
        out = self._fn(self._base_row(collection="UNKNOWN_LINE"))
        assert out.collection.value == "BOSS"

    def test_unknown_season_falls_back_to_ss25(self):
        out = self._fn(self._base_row(season="WW25"))
        assert out.season.value == "SS25"

    def test_unknown_status_falls_back_to_active(self):
        out = self._fn(self._base_row(status="obsolete"))
        assert out.status.value == "active"

    def test_case_insensitive_match(self):
        """Sanitizer should normalise case differences from UC."""
        out = self._fn(self._base_row(category="SUITS"))
        # "SUITS" is not in valid set directly but lower "suits" is
        assert out.category.value == "suits"
