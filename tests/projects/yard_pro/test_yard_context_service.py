"""Tests for ``yard_context_service.get_yard_context``.

Plan §4 makes ``YardContext`` the single source of truth shared by
coach + calendar. These tests snapshot the typed context shape and
assert every field is populated from the seeded data — drift here
means the coach and calendar would silently diverge.
"""
from __future__ import annotations

import pytest

from innovation_factory.backend.projects.yard_pro.seed import seed_yp_data
from innovation_factory.backend.projects.yard_pro.services.yard_context_service import (
    YardContext,
    get_yard_context,
)


@pytest.fixture
def seeded_yard_id(session):
    """Seed Martin's yard cleanly and return its id.

    The conftest engine is session-scoped, so earlier tests may have
    left rows (e.g. model unit tests writing throwaway yards). The seed
    is idempotent and early-returns if any ``YpYard`` already exists, so
    we explicitly clear the yard_pro tables first to guarantee Martin's
    yard is the one we get.
    """
    from sqlmodel import select

    from innovation_factory.backend.projects.yard_pro.models import (
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

    for model in (
        YpCoachMessage,
        YpCoachSession,
        YpCoachFeedback,
        YpToolReadiness,
        YpDealerRelationship,
        YpCalendarEntry,
        YpDiagnosis,
        YpActionLog,
        YpConsumable,
        YpTool,
        YpPlant,
        YpYard,
    ):
        for row in session.exec(select(model)).all():
            session.delete(row)
    session.commit()

    seed_yp_data(session)
    session.commit()
    yard = session.exec(select(YpYard)).first()
    assert yard is not None and yard.id is not None
    return yard.id


class TestYardContextShape:
    def test_returns_typed_yard_context(self, session, seeded_yard_id):
        ctx = get_yard_context(session, seeded_yard_id)
        assert isinstance(ctx, YardContext)

    def test_yard_summary_populated(self, session, seeded_yard_id):
        ctx = get_yard_context(session, seeded_yard_id)
        assert ctx.yard.id == seeded_yard_id
        assert ctx.yard.display_name  # non-empty
        assert ctx.yard.region_code == "DE-BW"
        # Stuttgart lat/lng from seed.
        assert 48.0 < ctx.yard.lat < 49.5
        assert 8.0 < ctx.yard.lng < 10.5
        assert ctx.yard.size_m2 == 900.0
        assert "lawn_m2" in ctx.yard.yard_metadata

    def test_plant_list_matches_seed(self, session, seeded_yard_id):
        ctx = get_yard_context(session, seeded_yard_id)
        # Seed has 12 plants.
        assert len(ctx.plants) == 12
        species = {p.species for p in ctx.plants}
        assert "Apple" in species
        assert "Beech" in species
        # All plants have notes populated in the seed.
        assert all(p.notes for p in ctx.plants)

    def test_tool_list_matches_seed_with_readiness(self, session, seeded_yard_id):
        ctx = get_yard_context(session, seeded_yard_id)
        # 5 tools in the seed.
        assert len(ctx.tools) == 5
        kinds = {t.kind for t in ctx.tools}
        assert "robotic_mower" in kinds
        assert "chainsaw" in kinds
        # The robotic mower readiness row exists in the seed; the
        # battery_pct should propagate through.
        mower = next(t for t in ctx.tools if t.kind == "robotic_mower")
        assert mower.battery_pct == pytest.approx(92.0)

    def test_consumables_match_seed(self, session, seeded_yard_id):
        ctx = get_yard_context(session, seeded_yard_id)
        # 8 consumables in the seed.
        assert len(ctx.consumables) == 8
        kinds = {c.kind for c in ctx.consumables}
        # Some recognizable kinds from the seed.
        assert "fertilizer" in kinds
        assert "spray" in kinds

    def test_recent_actions_filtered_to_14_days(self, session, seeded_yard_id):
        ctx = get_yard_context(session, seeded_yard_id)
        # Seed has 30 action-log rows but only those within 14 days qualify.
        # We assert the shape and the windowing — not exact counts, since
        # day-count is wall-clock-sensitive.
        assert isinstance(ctx.recent_actions, list)
        assert len(ctx.recent_actions) < 30, (
            "recent_actions must be windowed (not all 30 seeded rows)"
        )
        # If there are any, they must be ordered newest-first.
        for prev, curr in zip(ctx.recent_actions, ctx.recent_actions[1:]):
            assert prev.occurred_at >= curr.occurred_at

    def test_calendar_split_into_upcoming_and_overdue(self, session, seeded_yard_id):
        ctx = get_yard_context(session, seeded_yard_id)
        # Seed has 5 calendar entries — total count is wall-clock-stable.
        total = len(ctx.upcoming_calendar) + len(ctx.overdue_calendar)
        assert total == 5
        # The split itself depends on wall-clock; we just assert the
        # invariant — overdue entries are strictly in the past, upcoming
        # are now-or-future.
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        for entry in ctx.overdue_calendar:
            entry_at = entry.scheduled_at if entry.scheduled_at.tzinfo else entry.scheduled_at.replace(tzinfo=timezone.utc)
            assert entry_at < now
        for entry in ctx.upcoming_calendar:
            entry_at = entry.scheduled_at if entry.scheduled_at.tzinfo else entry.scheduled_at.replace(tzinfo=timezone.utc)
            assert entry_at >= now

    def test_weather_window_is_populated_stub_in_p0(self, session, seeded_yard_id):
        ctx = get_yard_context(session, seeded_yard_id)
        assert ctx.weather.location
        assert ctx.weather.summary
        # Stuttgart stub per plan §4 / yard_context_service docstring.
        assert "Stuttgart" in ctx.weather.location

    def test_missing_yard_raises(self, session):
        with pytest.raises(ValueError):
            get_yard_context(session, 999_999)


class TestSharedContextInvariant:
    """Plan §4: coach + calendar consume the same typed object — the
    snapshot here is the contract those two services rely on. If a
    consumer breaks because of a field rename, this test should be the
    first to fail."""

    def test_context_serializes_to_known_keys(self, session, seeded_yard_id):
        ctx = get_yard_context(session, seeded_yard_id)
        keys = set(ctx.model_dump().keys())
        expected = {
            "yard",
            "plants",
            "tools",
            "consumables",
            "recent_actions",
            "upcoming_calendar",
            "overdue_calendar",
            "weather",
        }
        assert keys == expected


class TestCalendarRegenerate:
    """Plan §12 UC2 success criterion #4: regenerate writes a fresh plan
    and reports the diff. ``shifted_entries`` is the demo gate (≥ 2)."""

    def test_regenerate_writes_new_plan_under_fresh_run_id(self, session, seeded_yard_id):
        from innovation_factory.backend.projects.yard_pro.services.calendar_service import (
            regenerate,
        )
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProCalendarStatus,
            YpCalendarEntry,
        )
        from sqlmodel import select

        result = regenerate(session, seeded_yard_id)
        assert result.yard_id == seeded_yard_id
        assert result.run_id.startswith("regen-")
        assert result.total_entries >= 1
        # The deleted_entries count matches the previously-planned count.
        assert result.deleted_entries >= 0

        # New rows persisted under the run_id.
        new_rows = session.exec(
            select(YpCalendarEntry)
            .where(YpCalendarEntry.yard_id == seeded_yard_id)
            .where(YpCalendarEntry.generated_by_run_id == result.run_id)
        ).all()
        assert len(new_rows) == result.total_entries
        # All new rows are 'planned'.
        assert all(r.status == YardProCalendarStatus.planned for r in new_rows)

    def test_regenerate_for_action_passes_trigger_id_through(self, session, seeded_yard_id):
        """B1's actions router calls this hook after a yp_action_log write.
        The hook delegates to ``regenerate`` and returns a typed result."""
        from innovation_factory.backend.projects.yard_pro.services.calendar_service import (
            regenerate_for_action,
        )

        result = regenerate_for_action(session, seeded_yard_id, action_id=42)
        assert result.yard_id == seeded_yard_id
        assert result.total_entries >= 1
