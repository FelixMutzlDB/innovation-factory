"""GDPR Art. 20 (data portability) export — schema regression.

Plan §8 row mandates:
``GET /api/projects/yard-pro/yards/{id}/export/portability`` returns
the same snapshot as Art. 15 wrapped in a versioned envelope so a
future provider can ingest the JSON without guessing the layout. The
schema is documented in
``docs/projects/yard-pro-data-export-schema.md``.

Test titles reference the **symptom** ("alice cannot read bob's
portability export", "Art. 20 schema drifted from doc", "portability
export non-JSON-serializable") so a refactor that moves the
envelope-builder elsewhere leaves these green.
"""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone

import pytest

# Register yard_pro models with SQLModel.metadata.
import innovation_factory.backend.projects.yard_pro.models  # noqa: F401


# ---------------------------------------------------------------------------
# Test helpers — same footprint as the Art. 15 test
# ---------------------------------------------------------------------------


def _seed_minimal_footprint(session, user_key: str, display_name: str):
    """Lighter footprint than the Art. 17/15 tests — schema regression
    doesn't need every yp_* table populated, just enough to exercise
    the envelope. We also seed a yp_plants row so the snapshot has
    non-empty tables for the JSON serialization round-trip.
    """
    from innovation_factory.backend.projects.yard_pro.models import (
        YardProBatteryFamily,
        YardProToolKind,
        YpPlant,
        YpTool,
        YpYard,
    )

    yard = YpYard(
        user_key=user_key,
        display_name=display_name,
        region_code="DE-BW",
        lat=48.7758,
        lng=9.1829,
        size_m2=900.0,
        yard_metadata={},
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
        display_name="trimmer",
        battery_family=YardProBatteryFamily.ap,
    )
    session.add(plant)
    session.add(tool)
    session.commit()

    return yard


@pytest.fixture
def martin(session):
    run = uuid.uuid4().hex[:8]
    user_key = f"martin-art20-{run}@yard-pro.local"
    yard = _seed_minimal_footprint(session, user_key, "Martin")
    return {
        "yard": yard,
        "user_key": user_key,
        "headers": {"X-Forwarded-User": user_key},
    }


@pytest.fixture
def alice_and_bob(session):
    run = uuid.uuid4().hex[:8]
    alice_key = f"alice-art20-{run}@yard-pro.local"
    bob_key = f"bob-art20-{run}@yard-pro.local"
    alice_yard = _seed_minimal_footprint(session, alice_key, "Alice")
    bob_yard = _seed_minimal_footprint(session, bob_key, "Bob")
    return {
        "alice_yard": alice_yard,
        "bob_yard": bob_yard,
        "alice_headers": {"X-Forwarded-User": alice_key},
        "bob_headers": {"X-Forwarded-User": bob_key},
    }


# ---------------------------------------------------------------------------
# Service-layer + envelope tests
# ---------------------------------------------------------------------------


class TestArt20Envelope:
    """Exercise :func:`export_yard_portability` directly."""

    def test_schema_matches_documented_shape_regression(
        self, session, martin
    ):
        """Schema regression — the load-bearing assertion: the exact
        set of keys in the Art. 20 payload matches the documented
        layout in ``docs/projects/yard-pro-data-export-schema.md``.

        A contributor that breaks the schema breaks this test by name.
        The error message points back at the doc — the fix is to update
        BOTH the doc and the test so the contract change is reviewable.
        """
        from innovation_factory.backend.projects.yard_pro.services.gdpr_service import (  # noqa: E501
            DATA_EXPORT_SCHEMA_VERSION,
            export_yard_portability,
        )

        yard_id = martin["yard"].id
        payload = export_yard_portability(session, ws=None, yard_id=yard_id)

        # Top-level envelope keys (matches §1 of the schema doc).
        expected_top = {"schema_version", "article", "generated_at", "yard"}
        actual_top = set(payload.keys())
        assert actual_top == expected_top, (
            f"Art. 20 envelope top-level keys drifted from "
            f"docs/projects/yard-pro-data-export-schema.md §1. "
            f"Expected: {sorted(expected_top)}; saw: {sorted(actual_top)}. "
            f"Update the doc AND bump DATA_EXPORT_SCHEMA_VERSION."
        )
        assert payload["schema_version"] == DATA_EXPORT_SCHEMA_VERSION
        assert payload["article"] == "GDPR Art. 20"

        # Yard sub-object keys (matches §2 of the schema doc).
        expected_yard = {
            "yard_id",
            "yards",
            "tables",
            "photos",
            "coach_transcripts_external",
        }
        actual_yard = set(payload["yard"].keys())
        assert actual_yard == expected_yard, (
            f"Art. 20 'yard' sub-object keys drifted from "
            f"docs/projects/yard-pro-data-export-schema.md §2. "
            f"Expected: {sorted(expected_yard)}; saw: {sorted(actual_yard)}."
        )

        # Photos sub-object keys (§2.1).
        photos_keys = set(payload["yard"]["photos"].keys())
        assert photos_keys == {"volume_path", "uris"}, (
            f"Art. 20 photos sub-object keys drifted from §2.1: {photos_keys}"
        )

        # Coach transcripts external sub-object keys (§2.2).
        ext_keys = set(payload["yard"]["coach_transcripts_external"].keys())
        assert ext_keys == {
            "source",
            "consent_gated",
            "retention_unconsented_days",
            "retention_consented_months",
            "note",
        }, (
            f"Art. 20 coach_transcripts_external keys drifted from §2.2: "
            f"{ext_keys}"
        )

    def test_portability_export_is_json_only_no_binary(
        self, session, martin
    ):
        """The portability payload must be pure JSON — no bytes, no
        non-serializable types. ``json.dumps(payload)`` must succeed.
        """
        from innovation_factory.backend.projects.yard_pro.services.gdpr_service import (  # noqa: E501
            export_yard_portability,
        )

        yard_id = martin["yard"].id
        payload = export_yard_portability(session, ws=None, yard_id=yard_id)

        # Round-trip through JSON — raises on any non-serializable type.
        serialized = json.dumps(payload)
        # Sanity: round-trip back and assert it's the same dict.
        re_parsed = json.loads(serialized)
        assert re_parsed["schema_version"] == payload["schema_version"]
        assert re_parsed["yard"]["yard_id"] == yard_id

    def test_portability_export_parseable_as_response_model(
        self, session, martin
    ):
        """The payload must validate against the documented
        :class:`YpYardPortabilityExportOut` Pydantic model — i.e. a
        third-party importer that knows only the Pydantic schema can
        load the JSON.
        """
        from innovation_factory.backend.projects.yard_pro.routers.yards import (  # noqa: E501
            YpYardPortabilityExportOut,
        )
        from innovation_factory.backend.projects.yard_pro.services.gdpr_service import (  # noqa: E501
            export_yard_portability,
        )

        yard_id = martin["yard"].id
        payload = export_yard_portability(session, ws=None, yard_id=yard_id)

        # Pydantic will raise if any required field is missing or any
        # type is off. This is the contract the API exposes to clients.
        parsed = YpYardPortabilityExportOut(**payload)
        assert parsed.schema_version == payload["schema_version"]
        assert parsed.yard.yard_id == yard_id


# ---------------------------------------------------------------------------
# Router-layer tests
# ---------------------------------------------------------------------------


class TestArt20Endpoint:
    """End-to-end tests via the TestClient."""

    def test_owner_can_get_portability_export_200(self, client, martin):
        resp = client.get(
            f"/api/projects/yard-pro/yards/{martin['yard'].id}/export/portability",
            headers=martin["headers"],
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["article"] == "GDPR Art. 20"
        assert body["schema_version"]
        assert body["yard"]["yard_id"] == martin["yard"].id
        # Sanity: at least one row in yp_plants.
        assert "yp_plants" in body["yard"]["tables"]
        assert len(body["yard"]["tables"]["yp_plants"]) >= 1

    def test_alice_cannot_read_bobs_portability_export_returns_404(
        self, client, alice_and_bob
    ):
        """RLS on Art. 20 endpoint."""
        bob_yard_id = alice_and_bob["bob_yard"].id
        resp = client.get(
            f"/api/projects/yard-pro/yards/{bob_yard_id}/export/portability",
            headers=alice_and_bob["alice_headers"],
        )
        assert resp.status_code == 404, resp.text
