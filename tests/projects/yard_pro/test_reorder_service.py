"""UC5 reorder-hint heuristic tests (plan §12 P1).

Plan §2 UC5: "Inventory & consumables — suggests reorder timing (oil,
lubricant, fertilizer, blade)." Tests cover both rules of the
heuristic (quantity floor + staleness) and the precedence between them.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

import innovation_factory.backend.projects.yard_pro.models  # noqa: F401


def _consumable(kind, quantity: float, last_restock_at=None, display_name="x"):
    from innovation_factory.backend.projects.yard_pro.models import YpConsumable

    return YpConsumable(
        yard_id=1,
        kind=kind,
        display_name=display_name,
        quantity=quantity,
        unit="",
        last_restock_at=last_restock_at,
    )


class TestQuantityFloor:
    def test_fertilizer_below_threshold_suggests_reorder(self):
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProConsumableKind,
        )
        from innovation_factory.backend.projects.yard_pro.services.reorder_service import (
            suggest_reorder,
        )

        c = _consumable(YardProConsumableKind.fertilizer, quantity=2.5)
        suggested, reason = suggest_reorder(c)
        assert suggested is True
        assert reason is not None
        assert "Running low" in reason

    def test_fertilizer_above_threshold_does_not_suggest(self):
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProConsumableKind,
        )
        from innovation_factory.backend.projects.yard_pro.services.reorder_service import (
            suggest_reorder,
        )

        c = _consumable(YardProConsumableKind.fertilizer, quantity=10.0)
        suggested, reason = suggest_reorder(c)
        assert suggested is False
        assert reason is None

    def test_blade_below_threshold_suggests_reorder(self):
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProConsumableKind,
        )
        from innovation_factory.backend.projects.yard_pro.services.reorder_service import (
            suggest_reorder,
        )

        c = _consumable(YardProConsumableKind.blade, quantity=2.0)
        suggested, _ = suggest_reorder(c)
        assert suggested is True


class TestStaleness:
    def test_old_oil_suggests_reorder_even_with_quantity(self):
        """Oil with healthy quantity but >1y old returns suggested=True
        on the staleness rule. The mineral oil shelf life invariant per
        the service heuristic."""
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProConsumableKind,
        )
        from innovation_factory.backend.projects.yard_pro.services.reorder_service import (
            suggest_reorder,
        )

        old = date(2026, 5, 13) - timedelta(days=400)
        c = _consumable(YardProConsumableKind.oil, quantity=5.0, last_restock_at=old)
        suggested, reason = suggest_reorder(c, today=date(2026, 5, 13))
        assert suggested is True
        assert reason is not None
        assert "Last restocked" in reason

    def test_fresh_oil_with_quantity_does_not_suggest(self):
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProConsumableKind,
        )
        from innovation_factory.backend.projects.yard_pro.services.reorder_service import (
            suggest_reorder,
        )

        fresh = date(2026, 5, 13) - timedelta(days=30)
        c = _consumable(YardProConsumableKind.oil, quantity=5.0, last_restock_at=fresh)
        suggested, reason = suggest_reorder(c, today=date(2026, 5, 13))
        assert suggested is False
        assert reason is None


class TestPrecedence:
    def test_quantity_wins_over_staleness(self):
        """Both rules fire — operator sees the more specific 'running
        low' message, not the staleness one."""
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProConsumableKind,
        )
        from innovation_factory.backend.projects.yard_pro.services.reorder_service import (
            suggest_reorder,
        )

        old = date(2026, 5, 13) - timedelta(days=400)
        c = _consumable(YardProConsumableKind.oil, quantity=0.5, last_restock_at=old)
        suggested, reason = suggest_reorder(c, today=date(2026, 5, 13))
        assert suggested is True
        assert reason is not None
        assert "Running low" in reason
        assert "Last restocked" not in reason


class TestInventoryEndpoint:
    """Wire-level test: GET /api/projects/yard-pro/inventory carries
    reorder_suggested + reorder_reason."""

    def test_seeded_consumables_surface_reorder_field(self, client):
        # The seeded yard has fertilizer below 5 kg threshold + blade
        # set above threshold + spray above threshold. We just assert
        # the field shape is present on every row.
        resp = client.get(
            "/api/projects/yard-pro/inventory",
            headers={"X-Forwarded-User": "martin@yard-pro.local"},
        )
        if resp.status_code == 404:
            # Local seed doesn't always include martin@yard-pro.local
            # under test isolation; skip if no yard
            pytest.skip("martin yard not seeded in this test session")
        assert resp.status_code == 200, resp.text
        rows = resp.json()
        for row in rows:
            assert "reorder_suggested" in row
            assert "reorder_reason" in row
            if row["reorder_suggested"]:
                assert row["reorder_reason"]
