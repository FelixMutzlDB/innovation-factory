"""GDPR Art. 17 ("right to be forgotten") cascade — RT-025 regression test.

Plan §8 row mandates: ``DELETE /api/projects/yard-pro/yards/{id}``
cascades Lakebase ``yp_*`` rows by ``yard_id`` + UC Volume photo prefix
+ revokes ``yp_dealer_relationships.consent_state``. Plan §10 RT-025:
"GDPR delete endpoint misses a table — orphan rows survive."

The load-bearing test (``test_no_orphan_rows_after_delete_full_metadata_walk``)
walks ``SQLModel.metadata.tables`` at test time — NOT a hardcoded list —
and asserts every ``yp_*`` table with a ``yard_id`` column has zero rows
referencing the deleted yard. If a future contributor adds a ``yp_*``
table without wiring it into the cascade, this test catches the gap.

Test names reference the **symptom** ("orphan rows survive",
"alice cannot delete bob's yard", "dry-run preserves data") not the
implementation, so refactors that move the cascade elsewhere should
leave these green.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

# Register yard_pro models with SQLModel.metadata at module-import time
# so the session-scoped engine fixture's create_all picks them up.
import innovation_factory.backend.projects.yard_pro.models  # noqa: F401


# ---------------------------------------------------------------------------
# Test helpers — seed two households with the full yp_* table footprint
# ---------------------------------------------------------------------------


def _seed_full_footprint(session, user_key: str, display_name: str):
    """Seed a yard plus at least one row in every yp_* table.

    Returns the YpYard instance (refreshed) plus a dict of created child
    objects keyed by table name. The footprint is intentionally
    comprehensive so the metadata-walk regression test exercises every
    table: any future yp_* table without coverage here is a future bug.
    """
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
        size_m2=500.0,
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
    session.refresh(consumable)

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
        content="hello",
        citations=[],
        model_version="coach-v0",
        is_recommendation=False,
        advisory=True,
    )
    session.add(msg)
    session.commit()

    return yard, {
        "plant": plant,
        "tool": tool,
        "consumable": consumable,
        "action": action,
        "diagnosis": diagnosis,
        "calendar": calendar,
        "readiness": readiness,
        "feedback": feedback,
        "dealer_rel": dealer_rel,
        "coach_session": coach_session,
    }


@pytest.fixture
def martin_full(session):
    """Martin's yard with a row in every yp_* table.

    User_key is randomized per fixture invocation because the conftest
    engine is session-scoped — same pattern as
    ``test_cross_household_isolation.two_yards``.
    """
    run = uuid.uuid4().hex[:8]
    user_key = f"martin-{run}@yard-pro.local"
    yard, children = _seed_full_footprint(session, user_key, "Martin")
    return {
        "yard": yard,
        "children": children,
        "user_key": user_key,
        "headers": {"X-Forwarded-User": user_key},
    }


@pytest.fixture
def alice_and_bob(session):
    """Two yards owned by different users. Returns dict of both."""
    run = uuid.uuid4().hex[:8]
    alice_key = f"alice-{run}@yard-pro.local"
    bob_key = f"bob-{run}@yard-pro.local"
    alice_yard, _ = _seed_full_footprint(session, alice_key, "Alice")
    bob_yard, _ = _seed_full_footprint(session, bob_key, "Bob")
    return {
        "alice_yard": alice_yard,
        "bob_yard": bob_yard,
        "alice_headers": {"X-Forwarded-User": alice_key},
        "bob_headers": {"X-Forwarded-User": bob_key},
    }


# ---------------------------------------------------------------------------
# Direct service-layer tests on delete_yard_cascade
# ---------------------------------------------------------------------------


class TestCascadeServiceLayer:
    """Exercise :func:`delete_yard_cascade` directly — separate from
    the router-level tests so a router-vs-service regression can be
    diagnosed quickly.
    """

    def test_no_orphan_rows_after_delete_full_metadata_walk(
        self, session, martin_full
    ):
        """RT-025 regression: after the cascade, EVERY yp_* table with
        a yard_id column has zero rows referencing the deleted yard.

        The table list is derived from ``SQLModel.metadata.tables`` at
        test time — never hardcoded. Adding a new yp_* table without
        wiring it into the cascade fails this test immediately.
        """
        from sqlalchemy import select as sa_select
        from sqlmodel import SQLModel

        from innovation_factory.backend.projects.yard_pro.services.gdpr_service import (  # noqa: E501
            delete_yard_cascade,
        )

        yard_id = martin_full["yard"].id
        assert yard_id is not None

        result = delete_yard_cascade(session, ws=None, yard_id=yard_id)
        assert result.dry_run is False
        assert result.yard_id == yard_id

        # Pull the enumeration at test time — same logic as the service.
        yp_tables = {
            name: tbl
            for name, tbl in SQLModel.metadata.tables.items()
            if name.startswith("yp_")
        }
        assert len(yp_tables) >= 12, (
            "Sanity check: yard_pro should declare at least 12 yp_* "
            f"tables (saw {len(yp_tables)}). If this is failing, the "
            "metadata enumeration is broken — the cascade can't cover "
            "what it can't see (RT-025)."
        )

        # 1) yp_yards itself — row gone.
        yards_tbl = yp_tables["yp_yards"]
        survivors = session.execute(
            sa_select(yards_tbl.c.id).where(yards_tbl.c.id == yard_id)
        ).all()
        assert survivors == [], (
            "yp_yards row survived the cascade — Art. 17 violation"
        )

        # 2) Every other yp_* table with a yard_id column — zero rows.
        for name, tbl in yp_tables.items():
            if name == "yp_yards":
                continue
            if "yard_id" not in tbl.columns:
                continue
            survivors = session.execute(
                sa_select(tbl.c.yard_id).where(
                    tbl.c.yard_id == yard_id
                )
            ).all()
            assert survivors == [], (
                f"Orphan rows in {name} after delete_yard_cascade — "
                f"RT-025: the cascade missed this table. Survivors: "
                f"{survivors}"
            )

    def test_indirect_children_purged_yp_coach_messages_and_readiness(
        self, session, martin_full
    ):
        """yp_coach_messages (via session_id) and yp_tool_readiness
        (via tool_id) carry no yard_id — verify the cascade reaches
        them through the parent table mapping anyway.
        """
        from sqlalchemy import select as sa_select
        from sqlmodel import SQLModel

        from innovation_factory.backend.projects.yard_pro.services.gdpr_service import (  # noqa: E501
            delete_yard_cascade,
        )

        coach_session_id = martin_full["children"]["coach_session"].id
        tool_id = martin_full["children"]["tool"].id
        yard_id = martin_full["yard"].id
        assert yard_id is not None
        assert coach_session_id is not None
        assert tool_id is not None

        # Sanity: rows exist before the cascade.
        msgs_tbl = SQLModel.metadata.tables["yp_coach_messages"]
        ready_tbl = SQLModel.metadata.tables["yp_tool_readiness"]
        assert (
            len(
                session.execute(
                    sa_select(msgs_tbl.c.id).where(
                        msgs_tbl.c.session_id == coach_session_id
                    )
                ).all()
            )
            >= 1
        )
        assert (
            len(
                session.execute(
                    sa_select(ready_tbl.c.tool_id).where(
                        ready_tbl.c.tool_id == tool_id
                    )
                ).all()
            )
            == 1
        )

        delete_yard_cascade(session, ws=None, yard_id=yard_id)

        # After the cascade — both indirect children are gone.
        assert (
            session.execute(
                sa_select(msgs_tbl.c.id).where(
                    msgs_tbl.c.session_id == coach_session_id
                )
            ).all()
            == []
        ), "yp_coach_messages survived — indirect cascade missed it"
        assert (
            session.execute(
                sa_select(ready_tbl.c.tool_id).where(
                    ready_tbl.c.tool_id == tool_id
                )
            ).all()
            == []
        ), "yp_tool_readiness survived — indirect cascade missed it"

    def test_dry_run_preserves_data_and_reports_counts(
        self, session, martin_full
    ):
        """``dry_run=True`` returns the same shape but writes nothing.

        After the dry-run call, all rows seeded for the yard are still
        present. The reported ``tables_purged`` counts must be non-zero
        (otherwise the response is uninformative for ops verification).
        """
        from sqlalchemy import func, select as sa_select
        from sqlmodel import SQLModel

        from innovation_factory.backend.projects.yard_pro.services.gdpr_service import (  # noqa: E501
            delete_yard_cascade,
        )

        yard_id = martin_full["yard"].id
        assert yard_id is not None

        # Snapshot pre-counts for every yp_* table with a yard_id column.
        pre_counts: dict[str, int] = {}
        for name, tbl in SQLModel.metadata.tables.items():
            if not name.startswith("yp_"):
                continue
            if name == "yp_yards":
                pre_counts[name] = session.execute(
                    sa_select(func.count()).select_from(tbl).where(
                        tbl.c.id == yard_id
                    )
                ).scalar_one()
                continue
            if "yard_id" in tbl.columns:
                pre_counts[name] = session.execute(
                    sa_select(func.count()).select_from(tbl).where(
                        tbl.c.yard_id == yard_id
                    )
                ).scalar_one()

        result = delete_yard_cascade(
            session, ws=None, yard_id=yard_id, dry_run=True
        )
        assert result.dry_run is True

        # All counts unchanged.
        for name, pre in pre_counts.items():
            tbl = SQLModel.metadata.tables[name]
            if name == "yp_yards":
                post = session.execute(
                    sa_select(func.count()).select_from(tbl).where(
                        tbl.c.id == yard_id
                    )
                ).scalar_one()
            else:
                post = session.execute(
                    sa_select(func.count()).select_from(tbl).where(
                        tbl.c.yard_id == yard_id
                    )
                ).scalar_one()
            assert post == pre, (
                f"dry_run=True changed row count in {name}: "
                f"{pre} -> {post}"
            )

        # The reported counts must reflect real seed data — i.e. the
        # dry-run is not silently returning zeros.
        non_zero_tables = [
            n for n, c in result.tables_purged.items() if c > 0
        ]
        assert len(non_zero_tables) >= 5, (
            "dry_run reported suspiciously few non-zero tables: "
            f"{result.tables_purged}"
        )
        assert result.consent_revocations >= 1

    def test_consent_revoked_before_dealer_relationship_delete(
        self, session, martin_full
    ):
        """Plan §8 mandates the consent transition is recorded before
        the relationship row goes away.

        We assert two things:
        - End state: the row is GONE (Art. 17 — no row referencing the
          deleted yard survives).
        - Transition recorded: ``CascadeResult.consent_revocations``
          reports >= 1, so the explicit UPDATE-then-DELETE path ran
          (not a single DELETE that would be invisible to downstream
          consent-transition observers).
        """
        from sqlalchemy import select as sa_select
        from sqlmodel import SQLModel

        from innovation_factory.backend.projects.yard_pro.services.gdpr_service import (  # noqa: E501
            delete_yard_cascade,
        )

        yard_id = martin_full["yard"].id
        assert yard_id is not None

        # Pre-state: granted, no revoked_at.
        rels_tbl = SQLModel.metadata.tables["yp_dealer_relationships"]
        pre = session.execute(
            sa_select(
                rels_tbl.c.consent_state,
                rels_tbl.c.revoked_at,
            ).where(rels_tbl.c.yard_id == yard_id)
        ).first()
        assert pre is not None
        assert pre[0] == "granted"
        assert pre[1] is None

        result = delete_yard_cascade(session, ws=None, yard_id=yard_id)

        # End state: row gone — RT-025.
        survivors = session.execute(
            sa_select(rels_tbl.c.id).where(
                rels_tbl.c.yard_id == yard_id
            )
        ).all()
        assert survivors == [], (
            "yp_dealer_relationships row survived — Art. 17 violation"
        )
        # Transition was recorded (the cascade incremented the counter).
        assert result.consent_revocations == 1

    def test_photos_volume_unconfigured_is_graceful_no_op(
        self, session, martin_full
    ):
        """Local dev path: PHOTOS_VOLUME_PATH is empty → ``photos_purged
        == 0`` and no exception. (Live verification of the configured
        path runs against Databricks; this test is the in-memory
        regression.)
        """
        from innovation_factory.backend.projects.yard_pro.services.gdpr_service import (  # noqa: E501
            delete_yard_cascade,
        )

        yard_id = martin_full["yard"].id
        assert yard_id is not None
        result = delete_yard_cascade(session, ws=None, yard_id=yard_id)
        assert result.photos_purged == 0


# ---------------------------------------------------------------------------
# Router-layer tests on DELETE /api/projects/yard-pro/yards/{id}
# ---------------------------------------------------------------------------


class TestDeleteYardEndpoint:
    """End-to-end tests via the FastAPI TestClient — covers RLS, the
    response payload shape, idempotency, and dry-run via the query
    param.
    """

    def test_owner_can_delete_returns_200_with_summary(
        self, client, martin_full
    ):
        resp = client.request(
            "DELETE",
            f"/api/projects/yard-pro/yards/{martin_full['yard'].id}",
            headers=martin_full["headers"],
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["yard_id"] == martin_full["yard"].id
        assert body["deleted"] is True
        assert body["dry_run"] is False
        assert isinstance(body["tables_purged"], dict)
        # Should have removed at least a handful of yp_* tables.
        non_zero = {k: v for k, v in body["tables_purged"].items() if v > 0}
        assert len(non_zero) >= 5
        assert body["consent_revocations"] >= 1

    def test_alice_cannot_delete_bobs_yard_returns_404(
        self, client, alice_and_bob
    ):
        """RLS on DELETE — RT-016 + Art. 17 together. 404 (not 403)
        per the existing yards.py convention."""
        from sqlalchemy import func, select as sa_select
        from sqlmodel import SQLModel

        bob_yard_id = alice_and_bob["bob_yard"].id
        resp = client.request(
            "DELETE",
            f"/api/projects/yard-pro/yards/{bob_yard_id}",
            headers=alice_and_bob["alice_headers"],
        )
        assert resp.status_code == 404, resp.text

    def test_dry_run_query_param_does_not_delete(
        self, client, martin_full, session
    ):
        """``?dry_run=true`` returns the cascade summary but the seed
        rows survive — used by ops to verify the cascade plan before
        firing the real DELETE.
        """
        from sqlalchemy import func, select as sa_select
        from sqlmodel import SQLModel

        yard_id = martin_full["yard"].id

        # Pre-count rows.
        yards_tbl = SQLModel.metadata.tables["yp_yards"]
        pre = session.execute(
            sa_select(func.count())
            .select_from(yards_tbl)
            .where(yards_tbl.c.id == yard_id)
        ).scalar_one()
        assert pre == 1

        resp = client.request(
            "DELETE",
            f"/api/projects/yard-pro/yards/{yard_id}?dry_run=true",
            headers=martin_full["headers"],
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["dry_run"] is True
        assert body["deleted"] is False
        assert body["consent_revocations"] >= 1

        # Row survives — same engine + transaction-shared session.
        post = session.execute(
            sa_select(func.count())
            .select_from(yards_tbl)
            .where(yards_tbl.c.id == yard_id)
        ).scalar_one()
        assert post == 1, "dry_run=true deleted the yard row — bug"

    def test_idempotent_second_delete_returns_404(
        self, client, martin_full
    ):
        """A successful DELETE removes the yard; the same request a
        second time returns 404 because the yard no longer exists.
        Documents the idempotency contract from the plan."""
        yard_id = martin_full["yard"].id

        first = client.request(
            "DELETE",
            f"/api/projects/yard-pro/yards/{yard_id}",
            headers=martin_full["headers"],
        )
        assert first.status_code == 200, first.text

        second = client.request(
            "DELETE",
            f"/api/projects/yard-pro/yards/{yard_id}",
            headers=martin_full["headers"],
        )
        assert second.status_code == 404, second.text
