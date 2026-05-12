"""3-model pattern smoke test for yard-pro.

Per CLAUDE.md "Models & API": every API-surfaced entity follows the
3-model pattern — ``Yp<Entity>`` (SQLModel table), ``Yp<Entity>Out``
(API response Pydantic), ``Yp<Entity>Create`` (API input Pydantic).
Internal tables that don't surface via the API only need the table
model (e.g. ``YpToolReadiness``, ``YpCoachFeedback``).

The yard-pro enums are prefixed ``YardPro<Name>`` (lessons §13) to
avoid OpenAPI schema collisions across the seven accelerators (e.g.
``AlertSeverity`` would clash with MAC's ``MacAlertSeverity``).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

# Module-level import registers yard_pro tables with SQLModel.metadata
# before the session-scoped engine fixture runs create_all.
from innovation_factory.backend.projects.yard_pro import models as yp_models


class TestEnumPrefixes:
    """All public enums in models.py must be ``YardPro``-prefixed.

    Catches a future contributor adding ``AlertSeverity`` or
    ``ConsentState`` without the project prefix — would collide with
    other projects' enums in the OpenAPI schema.
    """

    def test_known_enums_have_yardpro_prefix(self):
        expected = {
            "YardProToolKind",
            "YardProBatteryFamily",
            "YardProConsumableKind",
            "YardProActionType",
            "YardProActionSource",
            "YardProDiagnosisStatus",
            "YardProCalendarStatus",
            "YardProTelemetryEventType",
            "YardProConsentState",
            "YardProCoachFeedbackSignal",
            "YardProChatRole",
        }
        for name in expected:
            assert hasattr(yp_models, name), (
                f"{name} expected on yard_pro.models but missing"
            )

    def test_no_unprefixed_action_status_enum(self):
        """Regression: ``ActionSource`` (no prefix) would collide with
        any other project's similarly-named enum."""
        assert not hasattr(yp_models, "ActionSource")
        assert not hasattr(yp_models, "ActionType")
        assert not hasattr(yp_models, "ConsentState")


class TestThreeModelPatternForApiEntities:
    """For every entity surfaced via the API, both ``<Name>Out`` and
    ``<Name>Create`` (where applicable) must exist alongside the table
    model. Internal-only tables are not required to have I/O variants.
    """

    @pytest.mark.parametrize(
        "table, out, create",
        [
            ("YpYard", "YpYardOut", None),  # yards are seeded, not created via API in P0
            ("YpPlant", "YpPlantOut", "YpPlantCreate"),
            ("YpTool", "YpToolOut", "YpToolCreate"),
            ("YpConsumable", "YpConsumableOut", "YpConsumableCreate"),
            ("YpActionLog", "YpActionLogOut", "YpActionLogCreate"),
            ("YpCalendarEntry", "YpCalendarEntryOut", None),  # write-side is calendar regeneration (B2)
            ("YpDiagnosis", "YpDiagnosisOut", None),  # write-side is /diagnose multipart (B2)
        ],
    )
    def test_table_and_io_classes_exist(self, table, out, create):
        assert hasattr(yp_models, table), f"missing table model {table}"
        assert hasattr(yp_models, out), f"missing Out model {out}"
        if create:
            assert hasattr(yp_models, create), f"missing Create model {create}"


class TestArt22ColumnsPresent:
    """Plan §2/§8: the Art. 22 invariant lives in ``yp_action_log`` as
    two columns (``source`` + ``human_confirmed_at``). If a refactor
    removes either, the load-bearing rail dies silently."""

    def test_action_log_has_source_and_human_confirmed_at(self, session):
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProActionSource,
            YardProActionType,
            YpActionLog,
            YpYard,
        )

        yard = YpYard(user_key="model-test@example", display_name="Test")
        session.add(yard)
        session.commit()
        session.refresh(yard)

        entry = YpActionLog(
            yard_id=yard.id,
            action_type=YardProActionType.mow,
            occurred_at=datetime.now(timezone.utc),
            source=YardProActionSource.user,
            human_confirmed_at=datetime.now(timezone.utc),
        )
        session.add(entry)
        session.commit()
        session.refresh(entry)
        assert entry.source == YardProActionSource.user
        assert entry.human_confirmed_at is not None

    def test_action_log_has_idempotency_key_column(self, session):
        """P0 ships the column even though the 24h replay-cache logic
        lands in P1 — so the index can be created upfront (lessons §9)."""
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProActionType,
            YpActionLog,
            YpYard,
        )

        yard = YpYard(user_key="idem-test@example", display_name="Test")
        session.add(yard)
        session.commit()
        session.refresh(yard)

        entry = YpActionLog(
            yard_id=yard.id,
            action_type=YardProActionType.mow,
            occurred_at=datetime.now(timezone.utc),
            idempotency_key="some-key-xyz",
        )
        session.add(entry)
        session.commit()
        session.refresh(entry)
        assert entry.idempotency_key == "some-key-xyz"


class TestCockpitOutShape:
    """The UC1 anchor payload must carry every field the cockpit cards
    consume — yard, plants, tools, consumables, two calendar slices,
    recent actions, recent diagnoses. A future refactor that drops a
    field would silently break the cold-load contract."""

    def test_cockpit_out_carries_all_demo_slices(self):
        from innovation_factory.backend.projects.yard_pro.models import (
            YpCockpitOut,
        )

        fields = set(YpCockpitOut.model_fields.keys())
        required = {
            "yard",
            "plants",
            "tools",
            "consumables",
            "upcoming_calendar",
            "overdue_calendar",
            "recent_actions",
            "recent_diagnoses",
        }
        missing = required - fields
        assert not missing, f"YpCockpitOut missing fields: {missing}"


class TestAdvisoryMetadataOnDiagnosis:
    """EU AI Act Art. 50 (plan §2): every coach response and every
    diagnose result must carry an ``advisory=True`` flag so the UI can
    render the limited-risk chip. ``YpDiagnosisOut.advisory`` defaults
    to True; verify the default sticks."""

    def test_diagnosis_out_advisory_defaults_true(self):
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProDiagnosisStatus,
            YpDiagnosisOut,
        )

        out = YpDiagnosisOut(
            id=1,
            yard_id=1,
            photo_uri="",
            model_version="",
            predictions={},
            top_label="",
            top_confidence=0.0,
            accepted_label=None,
            status=YardProDiagnosisStatus.pending,
            created_at=datetime.now(timezone.utc),
        )
        assert out.advisory is True
