"""Seeding helpers for mol_asm_cockpit tests.

All helpers follow the yard_pro ``_seed`` pattern: they acquire the
session from the client's DB override and commit so subsequent HTTP
requests through the same client see the inserted rows.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timezone
from typing import Any


@contextmanager
def _seeding_session(client: Any):
    """Yield a live DB session (then commit) via the client's override."""
    from innovation_factory.backend.app import app
    from innovation_factory.backend.dependencies import get_session

    override = app.dependency_overrides.get(get_session)
    assert override is not None, "client fixture must be active"
    gen = override()
    session = next(gen)
    try:
        yield session
        session.commit()
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


def seed_region_and_station(client: Any, suffix: str) -> tuple[int, int]:
    """Create a region + station with a unique code suffix.

    Returns (region_id, station_id).
    """
    from innovation_factory.backend.projects.mol_asm_cockpit.models import (
        MacRegion,
        MacStation,
        StationType,
    )

    with _seeding_session(client) as session:
        region = MacRegion(name=f"MAC Test Region {suffix}", country="HU")
        session.add(region)
        session.flush()
        station = MacStation(
            station_code=f"TST-{suffix}",
            name=f"MAC Test Station {suffix}",
            city="Budapest",
            region_id=region.id,
            station_type=StationType.urban,
            latitude=47.5,
            longitude=19.0,
        )
        session.add(station)
        session.flush()
        assert region.id is not None
        assert station.id is not None
        return region.id, station.id


def seed_anomaly_alert(
    client: Any,
    station_id: int,
    suffix: str,
    severity: str = "high",
    status: str = "active",
) -> int:
    """Create a MacAnomalyAlert; returns its id."""
    from innovation_factory.backend.projects.mol_asm_cockpit.models import (
        MacAnomalyAlert,
        MacAlertSeverity,
        MacAlertStatus,
    )

    with _seeding_session(client) as session:
        alert = MacAnomalyAlert(
            station_id=station_id,
            metric_type="fuel_volume",
            severity=MacAlertSeverity(severity),
            title=f"Test Alert {suffix}",
            description="Test description",
            suggested_action="Test action",
            status=MacAlertStatus(status),
        )
        session.add(alert)
        session.flush()
        assert alert.id is not None
        return alert.id


def seed_fuel_sale(
    client: Any,
    station_id: int,
    *,
    sale_date: date,
    fuel_type: str = "diesel",
    volume_liters: float = 100.0,
    revenue: float = 160.0,
    unit_price: float = 1.60,
    margin: float = 12.0,
) -> int:
    """Create a MacFuelSale; returns its id."""
    from innovation_factory.backend.projects.mol_asm_cockpit.models import (
        MacFuelSale,
        FuelType,
    )

    with _seeding_session(client) as session:
        sale = MacFuelSale(
            station_id=station_id,
            sale_date=sale_date,
            fuel_type=FuelType(fuel_type),
            volume_liters=volume_liters,
            revenue=revenue,
            unit_price=unit_price,
            margin=margin,
        )
        session.add(sale)
        session.flush()
        assert sale.id is not None
        return sale.id


def seed_nonfuel_sale(
    client: Any,
    station_id: int,
    *,
    sale_date: date,
    category: str = "coffee",
    quantity: int = 10,
    revenue: float = 30.0,
    margin: float = 15.0,
) -> int:
    """Create a MacNonfuelSale; returns its id."""
    from innovation_factory.backend.projects.mol_asm_cockpit.models import (
        MacNonfuelSale,
        NonfuelCategory,
    )

    with _seeding_session(client) as session:
        sale = MacNonfuelSale(
            station_id=station_id,
            sale_date=sale_date,
            category=NonfuelCategory(category),
            quantity=quantity,
            revenue=revenue,
            margin=margin,
        )
        session.add(sale)
        session.flush()
        assert sale.id is not None
        return sale.id


def seed_chat_session(client: Any) -> int:
    """Create a MacChatSession with one user message; returns session_id."""
    from innovation_factory.backend.projects.mol_asm_cockpit.models import (
        MacChatSession,
        MacChatMessage,
        MacChatRole,
    )

    with _seeding_session(client) as session:
        chat_session = MacChatSession(session_type="issue_resolution")
        session.add(chat_session)
        session.flush()
        msg = MacChatMessage(
            session_id=chat_session.id,
            role=MacChatRole.user,
            content="How is station performance?",
        )
        session.add(msg)
        session.flush()
        assert chat_session.id is not None
        return chat_session.id
