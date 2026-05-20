"""Consumables reorder-hint heuristic (UC5 polish — plan §12 P1).

Plan §2 UC5: "Inventory & consumables — knows what tools/products Martin
has; suggests reorder timing (oil, lubricant, fertilizer, blade)." This
module owns the suggest-or-not logic so the router stays thin and the
heuristic is unit-testable in isolation.

The heuristic is intentionally simple in P1:

1. **Quantity floor**: per ``YardProConsumableKind`` minimum quantity
   below which we always suggest reorder. Below these numbers, the
   consumable is "running low for a typical weekend job".
2. **Staleness**: time-sensitive consumables (oil, spray, fungicide)
   degrade or volatilize and get a "last restocked > N days ago"
   secondary rule even if quantity looks OK on paper.

When both rules fire, the heuristic returns the more specific reason
(quantity wins — operators see "almost out" before "old").

This is advisory. No action is auto-taken — the cockpit renders a
badge; the user clicks Mark-as-done or buys via dealer (P5). Art. 22
invariant respected.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from ..models import YardProConsumableKind, YpConsumable


#: Per-kind low-stock floor. Below this quantity the heuristic fires
#: regardless of last restock date. Values reflect "a typical homeowner
#: weekend job's draw" not "industrial reserve" — Stuttgart 900 m² yard.
_QUANTITY_FLOOR: dict[YardProConsumableKind, tuple[float, str]] = {
    YardProConsumableKind.fertilizer: (5.0, "kg"),
    YardProConsumableKind.oil: (1.5, "L"),
    YardProConsumableKind.lubricant: (0.2, "kg"),
    YardProConsumableKind.blade: (4.0, "pcs"),
    YardProConsumableKind.fuel: (3.0, "L"),
    YardProConsumableKind.spray: (0.4, "L"),
    YardProConsumableKind.seed: (1.0, "kg"),
}

#: Per-kind staleness threshold (days). Above this, the heuristic fires
#: even when quantity looks healthy — the consumable degrades. Kinds not
#: in this dict don't carry a staleness rule (e.g. blades don't expire).
_STALENESS_DAYS: dict[YardProConsumableKind, int] = {
    YardProConsumableKind.oil: 365,  # mineral oil shelf life ~1 year once opened
    YardProConsumableKind.fuel: 60,  # alkylate petrol fares better than pump but still degrades
    YardProConsumableKind.spray: 180,  # diluted concentrates lose efficacy
    YardProConsumableKind.lubricant: 365,
}


def suggest_reorder(
    consumable: YpConsumable, *, today: Optional[date] = None
) -> tuple[bool, Optional[str]]:
    """Return ``(reorder_suggested, reason)``.

    Quantity floor wins over staleness — operators see "almost out"
    before "old". When neither rule fires, returns
    ``(False, None)`` and the frontend renders no badge.
    """
    today = today or date.today()
    kind = consumable.kind

    floor = _QUANTITY_FLOOR.get(kind)
    if floor is not None:
        threshold, _ = floor
        if consumable.quantity < threshold:
            return (
                True,
                f"Running low — {consumable.quantity:g} {consumable.unit or ''} left "
                f"(typical reorder threshold {threshold:g}).",
            )

    staleness_days = _STALENESS_DAYS.get(kind)
    if (
        staleness_days is not None
        and consumable.last_restock_at is not None
        and (today - consumable.last_restock_at) > timedelta(days=staleness_days)
    ):
        age_days = (today - consumable.last_restock_at).days
        return (
            True,
            f"Last restocked {age_days} days ago — consider refreshing for efficacy.",
        )

    return (False, None)
