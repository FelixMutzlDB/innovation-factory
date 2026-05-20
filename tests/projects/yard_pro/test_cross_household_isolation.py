"""RT-016 (Critical) — cross-household isolation regression test.

Plan §10 RT-016 explicitly enumerates the attack vectors:

  - Path: ``GET /plants?yard_id={B.id}`` with ``X-Forwarded-User=A`` →
    must NOT return B's plants.
  - Body: ``POST /actions`` with A's header but a plant_id belonging to
    B → must reject (not silently write into B's data).
  - Query: ``PATCH /plants/{B.plant_id}`` with A's header → must reject.
  - DELETE: same on B's resources from A → must reject.
  - JSON-body yard_id override: a payload-supplied ``yard_id`` MUST be
    ignored; RLS wins.

The test names reference the **symptom** ("alice cannot see bob's
plants") rather than the implementation. If the RLS layer moves from
the router into the SQL layer (Lakebase RLS), these tests should still
pass without changes.
"""
from __future__ import annotations

import pytest

# Register yard_pro models with SQLModel.metadata at module-import time
# so the session-scoped engine fixture's create_all picks them up.
import innovation_factory.backend.projects.yard_pro.models  # noqa: F401


import uuid


@pytest.fixture
def two_yards(session):
    """Seed two yards (alice + bob) with one plant, one tool, one
    consumable each. Returns (alice_yard, bob_yard) — both refreshed.

    User_keys are randomized per fixture invocation because the conftest
    engine is session-scoped — committed rows from earlier tests persist
    on the same engine, so a fixed ``alice@yard-pro.local`` would collide
    after the first test. The headers used by API calls are derived from
    the same random keys so each test gets a clean Alice/Bob pair.
    """
    from datetime import date

    from innovation_factory.backend.projects.yard_pro.models import (
        YardProBatteryFamily,
        YardProConsumableKind,
        YardProToolKind,
        YpConsumable,
        YpPlant,
        YpTool,
        YpYard,
    )

    test_run = uuid.uuid4().hex[:8]
    alice_key = f"alice-{test_run}@yard-pro.local"
    bob_key = f"bob-{test_run}@yard-pro.local"

    alice_yard = YpYard(
        user_key=alice_key,
        display_name="Alice's Yard",
        region_code="DE-BW",
        size_m2=500.0,
        yard_metadata={},
    )
    bob_yard = YpYard(
        user_key=bob_key,
        display_name="Bob's Yard",
        region_code="DE-BW",
        size_m2=700.0,
        yard_metadata={},
    )
    session.add(alice_yard)
    session.add(bob_yard)
    session.commit()
    session.refresh(alice_yard)
    session.refresh(bob_yard)

    # One plant per yard
    alice_plant = YpPlant(yard_id=alice_yard.id, species="Apple", variety="A1")
    bob_plant = YpPlant(yard_id=bob_yard.id, species="Cherry", variety="B1")
    # One tool per yard
    alice_tool = YpTool(
        yard_id=alice_yard.id,
        kind=YardProToolKind.trimmer,
        display_name="Alice's trimmer",
        battery_family=YardProBatteryFamily.ap,
    )
    bob_tool = YpTool(
        yard_id=bob_yard.id,
        kind=YardProToolKind.hedge_cutter,
        display_name="Bob's hedge cutter",
        battery_family=YardProBatteryFamily.ap,
    )
    # One consumable per yard
    alice_cons = YpConsumable(
        yard_id=alice_yard.id,
        kind=YardProConsumableKind.fertilizer,
        display_name="Alice's fertilizer",
        quantity=1.0,
        unit="kg",
    )
    bob_cons = YpConsumable(
        yard_id=bob_yard.id,
        kind=YardProConsumableKind.oil,
        display_name="Bob's oil",
        quantity=0.5,
        unit="L",
    )
    for obj in (
        alice_plant,
        bob_plant,
        alice_tool,
        bob_tool,
        alice_cons,
        bob_cons,
    ):
        session.add(obj)
    session.commit()
    for obj in (
        alice_plant,
        bob_plant,
        alice_tool,
        bob_tool,
        alice_cons,
        bob_cons,
    ):
        session.refresh(obj)

    return {
        "alice_yard": alice_yard,
        "bob_yard": bob_yard,
        "alice_plant": alice_plant,
        "bob_plant": bob_plant,
        "alice_tool": alice_tool,
        "bob_tool": bob_tool,
        "alice_cons": alice_cons,
        "bob_cons": bob_cons,
        "alice_headers": {"X-Forwarded-User": alice_key},
        "bob_headers": {"X-Forwarded-User": bob_key},
    }


# ---------------------------------------------------------------------------
# Vector 1: read paths — alice cannot see bob's data
# ---------------------------------------------------------------------------


class TestAliceCannotReadBobsData:
    def test_yards_me_returns_only_callers_yard(self, client, two_yards):
        resp_a = client.get(
            "/api/projects/yard-pro/yards/me", headers=two_yards["alice_headers"]
        )
        assert resp_a.status_code == 200
        assert resp_a.json()["display_name"] == "Alice's Yard"

        resp_b = client.get(
            "/api/projects/yard-pro/yards/me", headers=two_yards["bob_headers"]
        )
        assert resp_b.status_code == 200
        assert resp_b.json()["display_name"] == "Bob's Yard"

    def test_cockpit_path_with_bobs_yard_id_returns_404_to_alice(
        self, client, two_yards
    ):
        """Even if Alice knows Bob's yard_id, she gets 404 — RLS wins
        over the path parameter."""
        bob_yard_id = two_yards["bob_yard"].id
        resp = client.get(
            f"/api/projects/yard-pro/yards/{bob_yard_id}/cockpit",
            headers=two_yards["alice_headers"],
        )
        assert resp.status_code == 404

    def test_list_plants_does_not_leak_bobs_plants(self, client, two_yards):
        """The list endpoint has no yard_id query param, but the
        underlying RLS must still confine the result to Alice's yard."""
        resp = client.get(
            "/api/projects/yard-pro/plants", headers=two_yards["alice_headers"]
        )
        assert resp.status_code == 200
        species_seen = [row["species"] for row in resp.json()]
        assert "Apple" in species_seen
        assert "Cherry" not in species_seen, (
            "Alice saw Bob's cherry plant — RLS leak (RT-016)"
        )

    def test_list_tools_does_not_leak_bobs_tools(self, client, two_yards):
        resp = client.get(
            "/api/projects/yard-pro/tools", headers=two_yards["alice_headers"]
        )
        assert resp.status_code == 200
        names = [row["display_name"] for row in resp.json()]
        assert "Alice's trimmer" in names
        assert "Bob's hedge cutter" not in names

    def test_list_inventory_does_not_leak_bobs_consumables(
        self, client, two_yards
    ):
        resp = client.get(
            "/api/projects/yard-pro/inventory", headers=two_yards["alice_headers"]
        )
        assert resp.status_code == 200
        names = [row["display_name"] for row in resp.json()]
        assert "Alice's fertilizer" in names
        assert "Bob's oil" not in names


# ---------------------------------------------------------------------------
# Vector 2: write paths — alice cannot mutate bob's resources
# ---------------------------------------------------------------------------


class TestAliceCannotWriteToBobsData:
    def test_patch_plant_with_bobs_plant_id_returns_404(
        self, client, two_yards
    ):
        bob_plant_id = two_yards["bob_plant"].id
        resp = client.patch(
            f"/api/projects/yard-pro/plants/{bob_plant_id}",
            headers=two_yards["alice_headers"],
            json={"species": "Pwned", "variety": "x", "notes": ""},
        )
        assert resp.status_code == 404

    def test_delete_plant_with_bobs_plant_id_returns_404(
        self, client, two_yards
    ):
        bob_plant_id = two_yards["bob_plant"].id
        resp = client.delete(
            f"/api/projects/yard-pro/plants/{bob_plant_id}",
            headers=two_yards["alice_headers"],
        )
        assert resp.status_code == 404

    def test_patch_tool_with_bobs_tool_id_returns_404(self, client, two_yards):
        bob_tool_id = two_yards["bob_tool"].id
        resp = client.patch(
            f"/api/projects/yard-pro/tools/{bob_tool_id}",
            headers=two_yards["alice_headers"],
            json={
                "kind": "trimmer",
                "display_name": "Stolen",
                "battery_family": "ap",
            },
        )
        assert resp.status_code == 404

    def test_delete_tool_with_bobs_tool_id_returns_404(self, client, two_yards):
        bob_tool_id = two_yards["bob_tool"].id
        resp = client.delete(
            f"/api/projects/yard-pro/tools/{bob_tool_id}",
            headers=two_yards["alice_headers"],
        )
        assert resp.status_code == 404

    def test_patch_consumable_with_bobs_id_returns_404(
        self, client, two_yards
    ):
        bob_cons_id = two_yards["bob_cons"].id
        resp = client.patch(
            f"/api/projects/yard-pro/inventory/{bob_cons_id}",
            headers=two_yards["alice_headers"],
            json={
                "kind": "oil",
                "display_name": "Stolen",
                "quantity": 0,
                "unit": "L",
            },
        )
        assert resp.status_code == 404

    def test_delete_consumable_with_bobs_id_returns_404(
        self, client, two_yards
    ):
        bob_cons_id = two_yards["bob_cons"].id
        resp = client.delete(
            f"/api/projects/yard-pro/inventory/{bob_cons_id}",
            headers=two_yards["alice_headers"],
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Vector 3: body-reference cross-tenant — POST /actions referencing
# another household's plant_id / tool_id / consumable_id
# ---------------------------------------------------------------------------


class TestActionWriteCannotReferenceBobsData:
    """The most insidious attack: log an action with Alice's identity but
    point at Bob's plant. Without ownership checks on FK references,
    Alice's action would silently land in the log pointing at Bob's
    plant_id — RT-016 (RLS leak through FK)."""

    def test_action_post_with_bobs_plant_id_returns_404(
        self, client, two_yards
    ):
        bob_plant_id = two_yards["bob_plant"].id
        resp = client.post(
            "/api/projects/yard-pro/actions",
            headers=two_yards["alice_headers"],
            json={
                "action_type": "prune",
                "target_plant_id": bob_plant_id,
                "notes": "Trying to log against Bob's plant",
                "source": "user",
            },
        )
        assert resp.status_code == 404, resp.text

    def test_action_post_with_bobs_tool_id_returns_404(self, client, two_yards):
        bob_tool_id = two_yards["bob_tool"].id
        resp = client.post(
            "/api/projects/yard-pro/actions",
            headers=two_yards["alice_headers"],
            json={
                "action_type": "mow",
                "tool_id": bob_tool_id,
                "source": "user",
            },
        )
        assert resp.status_code == 404

    def test_action_post_with_bobs_consumable_id_returns_404(
        self, client, two_yards
    ):
        bob_cons_id = two_yards["bob_cons"].id
        resp = client.post(
            "/api/projects/yard-pro/actions",
            headers=two_yards["alice_headers"],
            json={
                "action_type": "fertilize",
                "consumable_id": bob_cons_id,
                "source": "user",
            },
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Vector 4: confirm endpoint
# ---------------------------------------------------------------------------


class TestConfirmCannotTouchBobsActions:
    def test_confirm_with_bobs_action_id_returns_404(self, client, two_yards, session):
        """Alice cannot confirm Bob's pending coach-recommendation row
        — the Mark-as-done rail must be tenant-scoped or it becomes an
        Art. 22 leak (a malicious user could "confirm" advisory rows
        in someone else's household to skew downstream analytics)."""
        from datetime import datetime, timezone

        from innovation_factory.backend.projects.yard_pro.models import (
            YardProActionSource,
            YardProActionType,
            YpActionLog,
        )

        bob_action = YpActionLog(
            yard_id=two_yards["bob_yard"].id,
            action_type=YardProActionType.fertilize,
            occurred_at=datetime.now(timezone.utc),
            source=YardProActionSource.coach_recommendation,
            human_confirmed_at=None,
        )
        session.add(bob_action)
        session.commit()
        session.refresh(bob_action)

        resp = client.patch(
            f"/api/projects/yard-pro/actions/{bob_action.id}/confirm",
            headers=two_yards["alice_headers"],
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Vector 5: JSON-body yard_id override — body fields MUST be ignored;
# RLS wins. Our Create models don't carry a yard_id field at all, so
# this is closed by design — verify the design holds.
# ---------------------------------------------------------------------------


class TestBodyYardIdOverrideIsIgnored:
    def test_create_plant_ignores_body_supplied_yard_id(
        self, client, two_yards
    ):
        """Even with a payload that includes a spurious ``yard_id`` —
        which the Create model doesn't declare and Pydantic should
        drop — the created plant MUST belong to the caller's yard."""
        from sqlmodel import select

        from innovation_factory.backend.projects.yard_pro.models import YpPlant

        bob_yard_id = two_yards["bob_yard"].id
        alice_yard_id = two_yards["alice_yard"].id
        resp = client.post(
            "/api/projects/yard-pro/plants",
            headers=two_yards["alice_headers"],
            json={
                "species": "ProbePlant",
                "variety": "x",
                "notes": "",
                # Attempt to override:
                "yard_id": bob_yard_id,
            },
        )
        assert resp.status_code == 201
        new_id = resp.json()["id"]
        # The body field MUST be ignored — the plant lands in Alice's yard.
        assert resp.json()["yard_id"] == alice_yard_id, (
            "Body-supplied yard_id was honored — RLS bypass (RT-016)"
        )

    def test_create_action_with_body_yard_id_does_not_write_to_bob(
        self, client, two_yards, session
    ):
        from sqlmodel import select

        from innovation_factory.backend.projects.yard_pro.models import (
            YpActionLog,
        )

        bob_yard_id = two_yards["bob_yard"].id
        alice_yard_id = two_yards["alice_yard"].id
        resp = client.post(
            "/api/projects/yard-pro/actions",
            headers=two_yards["alice_headers"],
            json={
                "action_type": "water",
                "notes": "probe",
                "source": "user",
                "yard_id": bob_yard_id,  # ignored
            },
        )
        assert resp.status_code == 201
        new_id = resp.json()["id"]
        row = session.exec(
            select(YpActionLog).where(YpActionLog.id == new_id)
        ).first()
        assert row is not None
        assert row.yard_id == alice_yard_id, (
            "Body-supplied yard_id ended up on Bob's yard — RT-016 leak"
        )
