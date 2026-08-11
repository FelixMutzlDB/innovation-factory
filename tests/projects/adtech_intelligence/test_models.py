"""Pure-unit tests for AdTech Intelligence models.

Covers:
- Enum values are correct
- 3-model pattern: each API-surfaced entity has a table model + Out schema (+ In where applicable)
- AtDashboardSummaryOut carries all required fields
- Pydantic model defaults and optional-field contracts
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

import innovation_factory.backend.projects.adtech_intelligence.models as at_models


# ---------------------------------------------------------------------------
# Enum spot-checks
# ---------------------------------------------------------------------------


class TestEnumValues:
    """Spot-check that enum members have the expected string values.

    These tests catch a rename that would silently break the API contract
    (e.g. renaming CampaignStatus.active to CampaignStatus.running).
    """

    def test_campaign_status_values(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            CampaignStatus,
        )

        assert CampaignStatus.draft == "draft"
        assert CampaignStatus.active == "active"
        assert CampaignStatus.paused == "paused"
        assert CampaignStatus.completed == "completed"
        assert CampaignStatus.cancelled == "cancelled"

    def test_campaign_type_values(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            CampaignType,
        )

        assert CampaignType.online == "online"
        assert CampaignType.outdoor == "outdoor"
        assert CampaignType.crossmedia == "crossmedia"

    def test_anomaly_severity_values(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AnomalySeverity,
        )

        assert AnomalySeverity.low == "low"
        assert AnomalySeverity.medium == "medium"
        assert AnomalySeverity.high == "high"
        assert AnomalySeverity.critical == "critical"

    def test_anomaly_status_values(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AnomalyStatus,
        )

        assert AnomalyStatus.new == "new"
        assert AnomalyStatus.acknowledged == "acknowledged"
        assert AnomalyStatus.investigating == "investigating"
        assert AnomalyStatus.resolved == "resolved"
        assert AnomalyStatus.dismissed == "dismissed"

    def test_issue_priority_values(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            IssuePriority,
        )

        assert IssuePriority.low == "low"
        assert IssuePriority.medium == "medium"
        assert IssuePriority.high == "high"
        assert IssuePriority.urgent == "urgent"

    def test_issue_status_values(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            IssueStatus,
        )

        assert IssueStatus.open == "open"
        assert IssueStatus.in_progress == "in_progress"
        assert IssueStatus.waiting_on_customer == "waiting_on_customer"
        assert IssueStatus.resolved == "resolved"
        assert IssueStatus.closed == "closed"

    def test_inventory_type_includes_dooh(self):
        """DOOH formats must be present — they are the OOH USP of this accelerator."""
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            InventoryType,
        )

        dooh_types = {InventoryType.dooh_screen, InventoryType.billboard, InventoryType.transit_poster}
        assert len(dooh_types) == 3

    def test_chat_role_values(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtChatRole,
        )

        assert AtChatRole.user == "user"
        assert AtChatRole.assistant == "assistant"
        assert AtChatRole.system == "system"


# ---------------------------------------------------------------------------
# 3-model pattern
# ---------------------------------------------------------------------------


class TestThreeModelPattern:
    """Every API-surfaced entity must have a table model and at least an Out schema.
    Entities with write paths also need an In schema.
    """

    @pytest.mark.parametrize(
        "table_cls, out_cls, in_cls",
        [
            ("AtAdvertiser", "AtAdvertiserOut", None),
            ("AtCampaign", "AtCampaignOut", "AtCampaignIn"),
            ("AtAdInventory", "AtAdInventoryOut", None),
            ("AtPlacement", "AtPlacementOut", "AtPlacementIn"),
            ("AtAnomaly", "AtAnomalyOut", None),
            ("AtAnomalyRule", "AtAnomalyRuleOut", None),
            ("AtIssue", "AtIssueOut", "AtIssueIn"),
            ("AtCustomerContract", "AtCustomerContractOut", None),
            ("AtChatSession", None, None),  # internal — surfaced via AtChatHistoryOut
            ("AtChatMessage", "AtChatMessageOut", "AtChatMessageIn"),
        ],
    )
    def test_model_classes_exist(self, table_cls, out_cls, in_cls):
        assert hasattr(at_models, table_cls), f"Missing table model: {table_cls}"
        if out_cls:
            assert hasattr(at_models, out_cls), f"Missing Out model: {out_cls}"
        if in_cls:
            assert hasattr(at_models, in_cls), f"Missing In model: {in_cls}"

    def test_update_models_exist(self):
        """PATCH endpoints need Update models with all-optional fields."""
        for name in ("AtCampaignUpdate", "AtAnomalyUpdate", "AtIssueUpdate"):
            assert hasattr(at_models, name), f"Missing update model: {name}"


# ---------------------------------------------------------------------------
# Dashboard summary output shape
# ---------------------------------------------------------------------------


class TestAtDashboardSummaryOut:
    """The dashboard card contract: all numeric KPI fields must be present."""

    def test_all_fields_present(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtDashboardSummaryOut,
        )

        required = {
            "total_campaigns",
            "active_campaigns",
            "total_inventory",
            "available_inventory",
            "total_spend",
            "total_impressions",
            "avg_ctr",
            "active_anomalies",
            "critical_anomalies",
        }
        fields = set(AtDashboardSummaryOut.model_fields.keys())
        missing = required - fields
        assert not missing, f"AtDashboardSummaryOut missing fields: {missing}"

    def test_instantiation(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtDashboardSummaryOut,
        )

        obj = AtDashboardSummaryOut(
            total_campaigns=10,
            active_campaigns=3,
            total_inventory=50,
            available_inventory=20,
            total_spend=99999.99,
            total_impressions=1_000_000,
            avg_ctr=0.0245,
            active_anomalies=2,
            critical_anomalies=1,
        )
        assert obj.total_campaigns == 10
        assert obj.avg_ctr == pytest.approx(0.0245)


# ---------------------------------------------------------------------------
# AtCampaignUpdate — all fields optional
# ---------------------------------------------------------------------------


class TestAtCampaignUpdate:
    """PATCH payload must allow partial updates (all fields optional)."""

    def test_empty_update_is_valid(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtCampaignUpdate,
        )

        upd = AtCampaignUpdate()
        dumped = upd.model_dump(exclude_unset=True)
        assert dumped == {}

    def test_single_field_update(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtCampaignUpdate,
            CampaignStatus,
        )

        upd = AtCampaignUpdate(status=CampaignStatus.paused)
        dumped = upd.model_dump(exclude_unset=True)
        assert set(dumped.keys()) == {"status"}
        assert dumped["status"] == CampaignStatus.paused


# ---------------------------------------------------------------------------
# AtCampaignIn — required vs optional fields
# ---------------------------------------------------------------------------


class TestAtCampaignIn:
    """Input schema contract for campaign creation."""

    def test_required_fields_present(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtCampaignIn,
            CampaignType,
        )

        obj = AtCampaignIn(
            advertiser_id=1,
            name="Test Campaign",
            campaign_type=CampaignType.online,
            budget=10000.0,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        assert obj.name == "Test Campaign"
        assert obj.budget == 10000.0
        assert obj.description is None
        assert obj.target_regions is None
        assert obj.kpi_targets is None

    def test_optional_kpi_targets(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtCampaignIn,
            CampaignType,
        )

        kpis = {"ctr_target": 0.05, "viewability": 0.70}
        obj = AtCampaignIn(
            advertiser_id=1,
            name="KPI Campaign",
            campaign_type=CampaignType.crossmedia,
            budget=5000.0,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30),
            kpi_targets=kpis,
        )
        assert obj.kpi_targets == kpis


# ---------------------------------------------------------------------------
# AtChatMessageIn — optional session_id
# ---------------------------------------------------------------------------


class TestAtChatMessageIn:
    """session_id is optional; message is required."""

    def test_message_without_session(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtChatMessageIn,
        )

        obj = AtChatMessageIn(message="Hello agent")
        assert obj.message == "Hello agent"
        assert obj.session_id is None

    def test_message_with_session(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtChatMessageIn,
        )

        obj = AtChatMessageIn(message="Follow-up", session_id=42)
        assert obj.session_id == 42


# ---------------------------------------------------------------------------
# AtIssueIn — defaults
# ---------------------------------------------------------------------------


class TestAtIssueIn:
    """Priority defaults to medium."""

    def test_default_priority_is_medium(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtIssueIn,
            IssueCategory,
            IssuePriority,
        )

        obj = AtIssueIn(
            title="Ad not delivering",
            description="Campaign impressions dropped to zero",
            category=IssueCategory.delivery,
        )
        assert obj.priority == IssuePriority.medium

    def test_explicit_urgent_priority(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtIssueIn,
            IssueCategory,
            IssuePriority,
        )

        obj = AtIssueIn(
            title="Critical billing error",
            description="Overcharged 10x",
            category=IssueCategory.billing,
            priority=IssuePriority.urgent,
        )
        assert obj.priority == IssuePriority.urgent


# ---------------------------------------------------------------------------
# AtPerformanceMetric defaults
# ---------------------------------------------------------------------------


class TestAtPerformanceMetricDefaults:
    """Metric fields default to 0 — no None coercions that could cause aggregation errors."""

    def test_defaults_are_zero(self):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtPerformanceMetric,
        )

        m = AtPerformanceMetric(placement_id=1, metric_date=date.today())
        assert m.impressions == 0
        assert m.clicks == 0
        assert m.ctr == 0.0
        assert m.conversions == 0
        assert m.spend == 0.0
        assert m.viewability_rate == 0.0
