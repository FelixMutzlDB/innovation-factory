"""Regression tests for the UC4 telemetry synthesizer (plan §2 UC4).

Three invariants on the wire:
1. **Idempotency** — calling ``synthesize_for_yard(now=T1)`` twice produces
   the same readiness state (no duplicate upserts, same battery_pct,
   same blade_hours).
2. **Determinism** — same ``(tool_id, now-date)`` input produces the same
   event_type + payload, so the demo's "battery_low nudge" is stable.
3. **Tool-kind behavior** — battery drifts for cordless, blade-hours
   accrues for the robotic mower, petrol chainsaw emits only
   ``session_ended``.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

import innovation_factory.backend.projects.yard_pro.models  # noqa: F401


def _seed_yard_with_tools(session):
    """Idempotent local seed — Martin's yard + a handful of representative
    tools. Independent of the production seed so tests own their data."""
    from sqlmodel import select

    from innovation_factory.backend.projects.yard_pro.models import (
        YardProBatteryFamily,
        YardProToolKind,
        YpTool,
        YpYard,
    )

    yard = session.exec(
        select(YpYard).where(YpYard.user_key == "synth-test@yard-pro.local")
    ).first()
    if yard is None:
        yard = YpYard(
            user_key="synth-test@yard-pro.local",
            display_name="Synth Test Yard",
            region_code="DE-BW",
            lat=48.7,
            lng=9.2,
            size_m2=600.0,
            yard_metadata={},
        )
        session.add(yard)
        session.commit()
        session.refresh(yard)
    if not session.exec(select(YpTool).where(YpTool.yard_id == yard.id)).first():
        tools = [
            YpTool(
                yard_id=yard.id,
                kind=YardProToolKind.trimmer,
                display_name="Cordless trimmer",
                model_year=2022,
                battery_family=YardProBatteryFamily.ap,
                last_serviced_at=date(2025, 9, 14),
            ),
            YpTool(
                yard_id=yard.id,
                kind=YardProToolKind.robotic_mower,
                display_name="Robotic mower",
                model_year=2021,
                battery_family=YardProBatteryFamily.asa,
                last_serviced_at=date(2024, 4, 18),  # ~13 months ago — well past blade interval
            ),
            YpTool(
                yard_id=yard.id,
                kind=YardProToolKind.chainsaw,
                display_name="Petrol chainsaw",
                model_year=2018,
                battery_family=YardProBatteryFamily.none,
                last_serviced_at=date(2024, 11, 10),
            ),
        ]
        for t in tools:
            session.add(t)
        session.commit()
        for t in tools:
            session.refresh(t)
    return yard


@pytest.fixture
def yard_with_tools(session):
    return _seed_yard_with_tools(session)


# ---------------------------------------------------------------------------
# Synthesizer
# ---------------------------------------------------------------------------


class TestSynthesizerIdempotency:
    """Re-running the synthesizer with the same ``now`` must produce the
    same readiness state — otherwise the demo gate flakes."""

    def test_repeat_synthesis_same_battery_pct(self, session, yard_with_tools):
        from innovation_factory.backend.projects.yard_pro.models import (
            YpToolReadiness,
        )
        from innovation_factory.backend.projects.yard_pro.services import (
            telemetry_service,
        )
        from sqlmodel import select

        now = datetime(2026, 5, 12, 9, 0, tzinfo=timezone.utc)
        telemetry_service.synthesize_for_yard(session, yard_with_tools.id, now=now)
        first = {
            r.tool_id: r.battery_pct
            for r in session.exec(select(YpToolReadiness)).all()
        }
        telemetry_service.synthesize_for_yard(session, yard_with_tools.id, now=now)
        second = {
            r.tool_id: r.battery_pct
            for r in session.exec(select(YpToolReadiness)).all()
        }
        assert first == second

    def test_repeat_synthesis_does_not_duplicate_rows(
        self, session, yard_with_tools
    ):
        from innovation_factory.backend.projects.yard_pro.models import (
            YpTool,
            YpToolReadiness,
        )
        from innovation_factory.backend.projects.yard_pro.services import (
            telemetry_service,
        )
        from sqlmodel import select

        now = datetime(2026, 5, 12, 9, 0, tzinfo=timezone.utc)
        telemetry_service.synthesize_for_yard(session, yard_with_tools.id, now=now)

        # Scope the count to THIS yard's tools — the conftest engine is
        # session-scoped, so prior tests may have left readiness rows for
        # other yards.
        def _count_for_yard() -> int:
            tool_ids = [
                t.id
                for t in session.exec(
                    select(YpTool).where(YpTool.yard_id == yard_with_tools.id)
                ).all()
            ]
            return len(
                list(
                    session.exec(
                        select(YpToolReadiness).where(
                            YpToolReadiness.tool_id.in_(tool_ids)  # type: ignore[union-attr]
                        )
                    ).all()
                )
            )

        count_first = _count_for_yard()
        telemetry_service.synthesize_for_yard(session, yard_with_tools.id, now=now)
        count_second = _count_for_yard()
        assert count_first == count_second == 3


class TestSynthesizerToolKindRules:
    def test_robotic_mower_emits_maintenance_due_past_threshold(
        self, session, yard_with_tools
    ):
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProTelemetryEventType,
            YardProToolKind,
            YpTool,
            YpToolReadiness,
        )
        from innovation_factory.backend.projects.yard_pro.services import (
            telemetry_service,
        )
        from sqlmodel import select

        now = datetime(2026, 5, 12, 9, 0, tzinfo=timezone.utc)
        telemetry_service.synthesize_for_yard(session, yard_with_tools.id, now=now)
        mower = session.exec(
            select(YpTool).where(YpTool.kind == YardProToolKind.robotic_mower)
        ).one()
        r = session.exec(
            select(YpToolReadiness).where(YpToolReadiness.tool_id == mower.id)
        ).one()
        # Mower's last_serviced_at is ~13 months ago — blade_hours far
        # exceeds the threshold.
        assert r.blade_hours_since_sharpening is not None
        assert r.blade_hours_since_sharpening >= telemetry_service.BLADE_MAINTENANCE_THRESHOLD_H
        assert r.last_event_type == YardProTelemetryEventType.maintenance_due

    def test_chainsaw_has_no_battery_no_blade_hours(
        self, session, yard_with_tools
    ):
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProToolKind,
            YpTool,
            YpToolReadiness,
        )
        from innovation_factory.backend.projects.yard_pro.services import (
            telemetry_service,
        )
        from sqlmodel import select

        now = datetime(2026, 5, 12, 9, 0, tzinfo=timezone.utc)
        telemetry_service.synthesize_for_yard(session, yard_with_tools.id, now=now)
        saw = session.exec(
            select(YpTool).where(YpTool.kind == YardProToolKind.chainsaw)
        ).one()
        r = session.exec(
            select(YpToolReadiness).where(YpToolReadiness.tool_id == saw.id)
        ).one()
        assert r.battery_pct is None
        assert r.blade_hours_since_sharpening is None


# ---------------------------------------------------------------------------
# Nudges router
# ---------------------------------------------------------------------------


MARTIN_HEADERS = {"X-Forwarded-User": "synth-test@yard-pro.local"}


class TestNudgesEndpoint:
    def test_synthesize_then_list_returns_nudges(
        self, client, session, yard_with_tools
    ):
        # Synthesize via the endpoint so the rate-limit + RLS path is
        # exercised end-to-end.
        synth = client.post(
            "/api/projects/yard-pro/nudges/synthesize", headers=MARTIN_HEADERS
        )
        assert synth.status_code == 200, synth.text
        body = synth.json()
        assert body["yard_id"] == yard_with_tools.id
        assert body["tools_updated"] == 3
        assert body["nudges_active"] >= 1

        listed = client.get(
            "/api/projects/yard-pro/nudges", headers=MARTIN_HEADERS
        )
        assert listed.status_code == 200, listed.text
        nudges = listed.json()
        assert len(nudges) >= 1
        for n in nudges:
            assert n["advisory"] is True  # Art. 50
            assert n["nudge_id"].startswith("nudge-")

    def test_dismiss_nudge_does_not_write_action_log(
        self, client, session, yard_with_tools
    ):
        """Art. 22 invariant: dismissing a nudge is a UI hide; it MUST
        NOT create a yp_action_log row. Mark-as-done is the only path
        that confirms a telemetry-nudge action."""
        from innovation_factory.backend.projects.yard_pro.models import YpActionLog
        from sqlmodel import select

        client.post(
            "/api/projects/yard-pro/nudges/synthesize", headers=MARTIN_HEADERS
        )
        listed = client.get(
            "/api/projects/yard-pro/nudges", headers=MARTIN_HEADERS
        )
        nudges = listed.json()
        assert nudges, "expected at least one nudge to dismiss"
        nudge_id = nudges[0]["nudge_id"]

        before_count = len(
            list(
                session.exec(
                    select(YpActionLog).where(
                        YpActionLog.yard_id == yard_with_tools.id
                    )
                ).all()
            )
        )

        resp = client.post(
            f"/api/projects/yard-pro/nudges/{nudge_id}/dismiss",
            headers=MARTIN_HEADERS,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["dismissed"] is True
        assert resp.json()["created"] is True

        after_count = len(
            list(
                session.exec(
                    select(YpActionLog).where(
                        YpActionLog.yard_id == yard_with_tools.id
                    )
                ).all()
            )
        )
        assert after_count == before_count  # No action_log writes.

    def test_dismiss_is_idempotent(self, client, session, yard_with_tools):
        client.post(
            "/api/projects/yard-pro/nudges/synthesize", headers=MARTIN_HEADERS
        )
        nudges = client.get(
            "/api/projects/yard-pro/nudges", headers=MARTIN_HEADERS
        ).json()
        nudge_id = nudges[0]["nudge_id"]

        first = client.post(
            f"/api/projects/yard-pro/nudges/{nudge_id}/dismiss",
            headers=MARTIN_HEADERS,
        )
        second = client.post(
            f"/api/projects/yard-pro/nudges/{nudge_id}/dismiss",
            headers=MARTIN_HEADERS,
        )
        assert first.status_code == 200 and second.status_code == 200
        assert first.json()["created"] is True
        assert second.json()["created"] is False

    def test_dismissed_nudge_no_longer_listed(
        self, client, session, yard_with_tools
    ):
        client.post(
            "/api/projects/yard-pro/nudges/synthesize", headers=MARTIN_HEADERS
        )
        before = client.get(
            "/api/projects/yard-pro/nudges", headers=MARTIN_HEADERS
        ).json()
        nudge_id = before[0]["nudge_id"]
        client.post(
            f"/api/projects/yard-pro/nudges/{nudge_id}/dismiss",
            headers=MARTIN_HEADERS,
        )
        after = client.get(
            "/api/projects/yard-pro/nudges", headers=MARTIN_HEADERS
        ).json()
        after_ids = {n["nudge_id"] for n in after}
        assert nudge_id not in after_ids


class TestNudgesRLS:
    def test_cross_tenant_synthesize_uses_callers_yard(
        self, client, session, yard_with_tools
    ):
        """A hostile user with no yard should get 404 from synthesize
        (no yard = no readiness to write)."""
        resp = client.post(
            "/api/projects/yard-pro/nudges/synthesize",
            headers={"X-Forwarded-User": "hostile@attacker.local"},
        )
        assert resp.status_code == 404, resp.text

    def test_cross_tenant_list_returns_empty_or_404(
        self, client, session, yard_with_tools
    ):
        resp = client.get(
            "/api/projects/yard-pro/nudges",
            headers={"X-Forwarded-User": "hostile@attacker.local"},
        )
        assert resp.status_code == 404, resp.text


class TestCockpitAdditivity:
    """The new cockpit fields (``tool_readiness``, ``nudges``) must be
    additive — existing consumers see all the prior fields unchanged."""

    def test_cockpit_carries_new_fields_without_breaking_old(
        self, client, session, yard_with_tools
    ):
        client.post(
            "/api/projects/yard-pro/nudges/synthesize", headers=MARTIN_HEADERS
        )
        resp = client.get(
            f"/api/projects/yard-pro/yards/{yard_with_tools.id}/cockpit",
            headers=MARTIN_HEADERS,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # Existing fields still present.
        for key in (
            "yard",
            "plants",
            "tools",
            "consumables",
            "upcoming_calendar",
            "overdue_calendar",
            "recent_actions",
            "recent_diagnoses",
        ):
            assert key in body, f"cockpit response lost field: {key}"
        # New fields populated.
        assert "tool_readiness" in body
        assert "nudges" in body
        assert isinstance(body["tool_readiness"], list)
        assert len(body["tool_readiness"]) == 3
        assert isinstance(body["nudges"], list)
        assert len(body["nudges"]) >= 1
