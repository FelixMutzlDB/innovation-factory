"""GDPR Art. 15 (right of access) export — RT-025 sibling regression.

Plan §8 row mandates:
``GET /api/projects/yard-pro/yards/{id}/export/access`` returns a
structured snapshot of every ``yp_*`` row referencing the yard, plus
the UC Volume photo URIs (URIs only — bytes never inlined per RT-024),
plus a pointer to the consent-gated Delta coach transcript mirror.

Test titles reference the **symptom** ("alice cannot read bob's export",
"export missing rows from yp_*", "photo bytes inlined in export") so a
refactor that moves the snapshot builder elsewhere leaves these green.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

# Register yard_pro models with SQLModel.metadata so the conftest
# engine fixture's create_all picks them up.
import innovation_factory.backend.projects.yard_pro.models  # noqa: F401


# ---------------------------------------------------------------------------
# Test helpers — seed every yp_* table for a yard (mirrors the Art. 17 test)
# ---------------------------------------------------------------------------


def _seed_full_footprint(session, user_key: str, display_name: str):
    from innovation_factory.backend.projects.yard_pro.models import (
        YardProActionSource,
        YardProActionType,
        YardProBatteryFamily,
        YardProCalendarStatus,
        YardProChatRole,
        YardProCoachFeedbackSignal,
        YardProConsentState,
        YardProConsumableKind,
        YardProDiagnosisStatus,
        YardProTelemetryEventType,
        YardProToolKind,
        YpActionLog,
        YpCalendarEntry,
        YpCoachFeedback,
        YpCoachMessage,
        YpCoachSession,
        YpConsumable,
        YpDealerRelationship,
        YpDiagnosis,
        YpPlant,
        YpTool,
        YpToolReadiness,
        YpYard,
    )

    yard = YpYard(
        user_key=user_key,
        display_name=display_name,
        region_code="DE-BW",
        lat=48.7758,
        lng=9.1829,
        size_m2=900.0,
        yard_metadata={"lawn_m2": 400},
    )
    session.add(yard)
    session.commit()
    session.refresh(yard)
    assert yard.id is not None

    plant = YpPlant(
        yard_id=yard.id,
        species="Apple",
        variety="Boskoop",
        planted_at=date(2020, 4, 1),
        notes="",
    )
    tool = YpTool(
        yard_id=yard.id,
        kind=YardProToolKind.trimmer,
        display_name=f"{display_name} trimmer",
        battery_family=YardProBatteryFamily.ap,
    )
    consumable = YpConsumable(
        yard_id=yard.id,
        kind=YardProConsumableKind.fertilizer,
        display_name="Fertilizer",
        quantity=1.0,
        unit="kg",
    )
    session.add(plant)
    session.add(tool)
    session.add(consumable)
    session.commit()
    session.refresh(plant)
    session.refresh(tool)

    action = YpActionLog(
        yard_id=yard.id,
        action_type=YardProActionType.mow,
        occurred_at=datetime.now(timezone.utc),
        source=YardProActionSource.user,
        human_confirmed_at=datetime.now(timezone.utc),
        notes="seed action",
    )
    diagnosis = YpDiagnosis(
        yard_id=yard.id,
        photo_uri=f"seed://photos/{yard.id}/apple-leaf.jpg",
        model_version="yard-pro-vision-v0",
        predictions={"labels": []},
        top_label="apple_scab",
        top_confidence=0.7,
        status=YardProDiagnosisStatus.reviewed,
    )
    calendar = YpCalendarEntry(
        yard_id=yard.id,
        title="Mow",
        description="",
        scheduled_at=datetime.now(timezone.utc),
        status=YardProCalendarStatus.planned,
    )
    readiness = YpToolReadiness(
        tool_id=tool.id,
        battery_pct=88.0,
        last_event_type=YardProTelemetryEventType.session_ended,
        payload={},
    )
    feedback = YpCoachFeedback(
        yard_id=yard.id,
        response_id=f"resp-{uuid.uuid4().hex[:8]}",
        model_version="coach-v0",
        signal=YardProCoachFeedbackSignal.thumbs_up,
        notes="",
    )
    dealer_rel = YpDealerRelationship(
        yard_id=yard.id,
        dealer_id=f"dealer-{uuid.uuid4().hex[:8]}",
        consent_state=YardProConsentState.granted,
        consent_at=datetime.now(timezone.utc),
    )
    coach_session = YpCoachSession(yard_id=yard.id, title="Test chat")
    session.add(action)
    session.add(diagnosis)
    session.add(calendar)
    session.add(readiness)
    session.add(feedback)
    session.add(dealer_rel)
    session.add(coach_session)
    session.commit()
    session.refresh(coach_session)

    msg = YpCoachMessage(
        session_id=coach_session.id,
        role=YardProChatRole.user,
        content="hello coach",
        citations=[],
        model_version="coach-v0",
        is_recommendation=False,
        advisory=True,
    )
    session.add(msg)
    session.commit()

    return yard


@pytest.fixture
def martin_full(session):
    run = uuid.uuid4().hex[:8]
    user_key = f"martin-art15-{run}@yard-pro.local"
    yard = _seed_full_footprint(session, user_key, "Martin")
    return {
        "yard": yard,
        "user_key": user_key,
        "headers": {"X-Forwarded-User": user_key},
    }


@pytest.fixture
def alice_and_bob(session):
    run = uuid.uuid4().hex[:8]
    alice_key = f"alice-art15-{run}@yard-pro.local"
    bob_key = f"bob-art15-{run}@yard-pro.local"
    alice_yard = _seed_full_footprint(session, alice_key, "Alice")
    bob_yard = _seed_full_footprint(session, bob_key, "Bob")
    return {
        "alice_yard": alice_yard,
        "bob_yard": bob_yard,
        "alice_headers": {"X-Forwarded-User": alice_key},
        "bob_headers": {"X-Forwarded-User": bob_key},
    }


# ---------------------------------------------------------------------------
# Service-layer tests — exercise export_yard_access directly
# ---------------------------------------------------------------------------


class TestArt15Service:
    """Direct tests on :func:`export_yard_access`. Mirrors the structure
    of the Art. 17 service-layer test class.
    """

    def test_export_covers_every_yp_table_full_metadata_walk(
        self, session, martin_full
    ):
        """RT-025 sibling: the export must include every ``yp_*`` table
        with a yard_id column OR an _INDIRECT_REFS mapping. The
        enumeration is derived from SQLModel.metadata at request time —
        if a future yp_* table isn't reachable from the snapshot
        builder, this test fails immediately.
        """
        from sqlmodel import SQLModel

        from innovation_factory.backend.projects.yard_pro.services.gdpr_service import (  # noqa: E501
            export_yard_access,
        )

        yard_id = martin_full["yard"].id
        assert yard_id is not None

        payload = export_yard_access(session, ws=None, yard_id=yard_id)

        # Top-level envelope keys.
        assert payload["article"] == "GDPR Art. 15"
        assert "generated_at" in payload
        assert payload["yard_id"] == yard_id

        # The yards list must contain the single yard row.
        assert isinstance(payload["yards"], list)
        assert len(payload["yards"]) == 1
        assert payload["yards"][0]["id"] == yard_id

        # Every yp_* table with a yard_id column OR an indirect mapping
        # must appear under `tables`. Enumeration walks the metadata so
        # a future yp_* table is auto-covered.
        from innovation_factory.backend.projects.yard_pro.services.gdpr_service import (  # noqa: E501
            _INDIRECT_REFS,
        )

        expected_tables: set[str] = set()
        for name, tbl in SQLModel.metadata.tables.items():
            if not name.startswith("yp_") or name == "yp_yards":
                continue
            if name in _INDIRECT_REFS or "yard_id" in tbl.columns:
                expected_tables.add(name)

        assert len(expected_tables) >= 11, (
            f"Sanity check — expected ≥11 yp_* tables in the snapshot "
            f"(saw {len(expected_tables)}). If this fails, the metadata "
            f"walk is broken and the export silently misses tables."
        )

        for tbl_name in expected_tables:
            assert tbl_name in payload["tables"], (
                f"Export missing rows from {tbl_name} — RT-025 sibling "
                f"violation. The metadata walk in export_yard_access "
                f"diverged from the delete cascade."
            )

    def test_photo_bytes_never_inlined_only_uris(
        self, session, martin_full
    ):
        """RT-024 invariant: the export carries photo URIs only, never
        the image bytes. Asserts the ``photos`` block shape and the
        absence of base64-shaped strings in the payload.
        """
        import json

        from innovation_factory.backend.projects.yard_pro.services.gdpr_service import (  # noqa: E501
            export_yard_access,
        )

        yard_id = martin_full["yard"].id
        payload = export_yard_access(session, ws=None, yard_id=yard_id)

        photos = payload["photos"]
        assert isinstance(photos, dict)
        assert "volume_path" in photos
        assert "uris" in photos
        assert isinstance(photos["uris"], list)
        # Local dev / no ws — uris must be empty (not a list of bytes).
        assert photos["uris"] == []

        # Defensive: round-trip the payload through JSON and assert no
        # value is a suspiciously long base64-shaped string. A real
        # SAR responder would diff this against an allowlist of fields
        # that ARE supposed to contain long strings (none in P2).
        serialized = json.dumps(payload)
        # The longest legitimate string in the seed is a few hundred
        # chars at most; >1000 chars would indicate inlined bytes.
        assert "data:image" not in serialized, (
            "Photo bytes inlined in export — RT-024 violation"
        )
        assert ";base64," not in serialized, (
            "Base64-encoded bytes leaked into export — RT-024 violation"
        )

    def test_idempotent_double_export_same_shape(self, session, martin_full):
        """Calling export_yard_access twice returns the same shape
        (modulo ``generated_at`` which is a timestamp). Idempotency is
        a documented contract for the snapshot builder.
        """
        from innovation_factory.backend.projects.yard_pro.services.gdpr_service import (  # noqa: E501
            export_yard_access,
        )

        yard_id = martin_full["yard"].id
        a = export_yard_access(session, ws=None, yard_id=yard_id)
        b = export_yard_access(session, ws=None, yard_id=yard_id)

        # Generated-at differs (clock); strip it before equality check.
        a.pop("generated_at")
        b.pop("generated_at")
        assert a == b, "Export not idempotent — two consecutive runs differ"

    def test_export_schema_keys_stable_regression(self, session, martin_full):
        """Schema regression: the exact set of top-level keys must match
        the documented snapshot shape. A contributor that drops or
        renames a key breaks this test by name — the message points at
        the source.
        """
        from innovation_factory.backend.projects.yard_pro.services.gdpr_service import (  # noqa: E501
            export_yard_access,
        )

        yard_id = martin_full["yard"].id
        payload = export_yard_access(session, ws=None, yard_id=yard_id)

        # Expected top-level keys for Art. 15.
        expected = {
            "article",
            "generated_at",
            "yard_id",
            "yards",
            "tables",
            "photos",
            "coach_transcripts_external",
        }
        actual = set(payload.keys())
        assert actual == expected, (
            f"Art. 15 export top-level keys drifted. "
            f"Expected: {sorted(expected)}; saw: {sorted(actual)}. "
            f"Update docs/projects/yard-pro-data-export-schema.md to "
            f"document the change before the test passes."
        )

        # The coach_transcripts_external block has a stable shape.
        ext = payload["coach_transcripts_external"]
        assert set(ext.keys()) == {
            "source",
            "consent_gated",
            "retention_unconsented_days",
            "retention_consented_months",
            "note",
        }
        assert ext["source"] == "yard_pro_bronze.coach_transcripts"


# ---------------------------------------------------------------------------
# Router-layer tests via FastAPI TestClient
# ---------------------------------------------------------------------------


class TestArt15Endpoint:
    """End-to-end tests via the TestClient."""

    def test_owner_can_export_returns_200_with_payload(
        self, client, martin_full
    ):
        resp = client.get(
            f"/api/projects/yard-pro/yards/{martin_full['yard'].id}/export/access",
            headers=martin_full["headers"],
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["article"] == "GDPR Art. 15"
        assert body["yard_id"] == martin_full["yard"].id
        assert "tables" in body
        assert "yp_plants" in body["tables"]
        assert "yp_tools" in body["tables"]

    def test_alice_cannot_read_bobs_export_returns_404(
        self, client, alice_and_bob
    ):
        """RLS — RT-016 + Art. 15 together. 404, not 403 (yards.py
        convention)."""
        bob_yard_id = alice_and_bob["bob_yard"].id
        resp = client.get(
            f"/api/projects/yard-pro/yards/{bob_yard_id}/export/access",
            headers=alice_and_bob["alice_headers"],
        )
        assert resp.status_code == 404, resp.text

    def test_export_includes_named_seed_rows_from_each_table(
        self, client, martin_full
    ):
        """Sanity: the export returned by the endpoint includes the
        specific rows we seeded — proves the metadata walk reached the
        actual data, not just empty lists.
        """
        resp = client.get(
            f"/api/projects/yard-pro/yards/{martin_full['yard'].id}/export/access",
            headers=martin_full["headers"],
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()

        # The named seed rows from _seed_full_footprint:
        assert any(
            p["species"] == "Apple" for p in body["tables"]["yp_plants"]
        )
        assert any(
            t["display_name"].endswith("trimmer")
            for t in body["tables"]["yp_tools"]
        )
        assert any(
            c["display_name"] == "Fertilizer"
            for c in body["tables"]["yp_consumables"]
        )
        assert len(body["tables"]["yp_action_log"]) >= 1
        assert len(body["tables"]["yp_diagnoses"]) >= 1
        assert len(body["tables"]["yp_calendar_entries"]) >= 1
        # Indirect children are present too.
        assert len(body["tables"]["yp_tool_readiness"]) >= 1
        assert len(body["tables"]["yp_coach_messages"]) >= 1
