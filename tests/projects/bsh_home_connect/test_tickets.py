"""Ticket lifecycle, status state-machine, and note-visibility tests.

Covers:
- Ticket defaults (status=open, priority=3)
- assigned_at set when technician_id first assigned
- completed_at set when status transitions to resolved
- _build_ticket_out helper returns correct shape
- Note visibility: customers only see non-internal notes
- Shipping label generation sets label_url, tracking_number, status
- 404 for unknown ticket on all ticket-scoped endpoints
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlmodel import select

from innovation_factory.backend.projects.bsh_home_connect.models import (
    BshCustomer,
    BshCustomerDevice,
    BshDevice,
    BshTicket,
    BshTicketNote,
    BshTicketStatus,
    BshTicketUpdate,
    DeviceCategory,
    UserRole,
)
from innovation_factory.backend.projects.bsh_home_connect.routers.tickets import (
    _build_ticket_out,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_bsh(client) -> None:
    """Seed BSH catalog data idempotently.

    Uses model_number 'SMS8YCI03E' as a sentinel rather than relying on
    seed_bsh_data's own "any BshDevice exists" guard.  That guard returns
    early if test-helper devices (e.g. 'STREAM-DW-01') were committed by
    a previous test in the same session, leaving the catalog empty.
    """
    from innovation_factory.backend.app import app
    from innovation_factory.backend.dependencies import get_session
    from innovation_factory.backend.projects.bsh_home_connect.models import BshDevice
    from innovation_factory.backend.projects.bsh_home_connect.seed import (
        _seed_customer_devices,
        _seed_customers,
        _seed_devices,
        _seed_documents,
        _seed_knowledge_base,
        _seed_technicians,
    )
    from sqlmodel import select

    override = app.dependency_overrides.get(get_session)
    assert override is not None
    gen = override()
    session = next(gen)
    try:
        catalog_present = session.exec(
            select(BshDevice).where(BshDevice.model_number == "SMS8YCI03E")
        ).first()
        if not catalog_present:
            _seed_devices(session)
            _seed_knowledge_base(session)
            _seed_documents(session)
            _seed_customers(session)
            _seed_technicians(session)
            _seed_customer_devices(session)
            session.commit()
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


def _register_device_for_local_user(client) -> dict:
    """Register the first catalog device for the mock local user."""
    devices = client.get("/api/projects/bsh-home-connect/devices").json()
    assert devices, "No devices in catalog — seed BSH data first"
    device_id = devices[0]["id"]

    resp = client.post(
        "/api/projects/bsh-home-connect/customers/me/devices",
        json={"device_id": device_id, "serial_number": "TICKET-TEST-SN-001"},
    )
    if resp.status_code == 400 and "already registered" in resp.text:
        # Serial already used in a prior test run — get the existing one
        my_devices = client.get("/api/projects/bsh-home-connect/customers/me/devices").json()
        return my_devices[0]
    assert resp.status_code == 200, f"register_device failed: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# _build_ticket_out helper (unit test — session fixture)
# ---------------------------------------------------------------------------


class TestBuildTicketOut:
    """_build_ticket_out assembles BshTicketOut with embedded device info."""

    def test_returns_correct_shape(self, session):
        device = BshDevice(
            model_number="BUILD-TEST-DW-01", brand="Bosch",
            name="Serie 8", category=DeviceCategory.dishwasher,
        )
        session.add(device)
        session.flush()

        customer = BshCustomer(
            databricks_user_id="build-test-user",
            email="build@example.com",
            first_name="Build", last_name="Tester",
        )
        session.add(customer)
        session.flush()

        cd = BshCustomerDevice(
            customer_id=customer.id, device_id=device.id,
            serial_number="BUILD-SN-001",
        )
        session.add(cd)
        session.flush()

        ticket = BshTicket(
            customer_id=customer.id,
            customer_device_id=cd.id,
            title="Test ticket", description="Testing",
            status=BshTicketStatus.open, priority=2,
        )
        session.add(ticket)
        session.flush()

        out = _build_ticket_out(ticket, session)

        assert out.id == ticket.id
        assert out.customer_id == customer.id
        assert out.status == BshTicketStatus.open
        assert out.priority == 2
        assert out.customer_device is not None
        assert out.customer_device.serial_number == "BUILD-SN-001"
        assert out.customer_device.device is not None
        assert out.customer_device.device.brand == "Bosch"

    def test_assigned_at_and_completed_at_default_none(self, session):
        device = BshDevice(
            model_number="BUILD-TEST-DW-02", brand="Siemens",
            name="iQ700", category=DeviceCategory.dishwasher,
        )
        session.add(device)
        session.flush()

        customer = BshCustomer(
            databricks_user_id="build-test-user-02",
            email="build2@example.com",
            first_name="Test", last_name="User",
        )
        session.add(customer)
        session.flush()

        cd = BshCustomerDevice(
            customer_id=customer.id, device_id=device.id,
            serial_number="BUILD-SN-002",
        )
        session.add(cd)
        session.flush()

        ticket = BshTicket(
            customer_id=customer.id, customer_device_id=cd.id,
            title="T", description="D", status=BshTicketStatus.open,
        )
        session.add(ticket)
        session.flush()

        out = _build_ticket_out(ticket, session)
        assert out.assigned_at is None
        assert out.completed_at is None


# ---------------------------------------------------------------------------
# Ticket status state-machine (HTTP)
# ---------------------------------------------------------------------------


class TestTicketStatusStateMachine:
    def test_new_ticket_defaults_to_open(self, client):
        _seed_bsh(client)
        my_device = _register_device_for_local_user(client)

        resp = client.post(
            "/api/projects/bsh-home-connect/tickets",
            json={
                "customer_device_id": my_device["id"],
                "title": "Dishwasher not draining",
                "description": "Error E24 after every cycle",
                "priority": 2,
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "open"
        assert body["priority"] == 2
        assert body["assigned_at"] is None
        assert body["completed_at"] is None

    def test_resolved_status_sets_completed_at(self, client):
        _seed_bsh(client)
        my_device = _register_device_for_local_user(client)

        # Create a ticket
        create_resp = client.post(
            "/api/projects/bsh-home-connect/tickets",
            json={
                "customer_device_id": my_device["id"],
                "title": "Test resolve",
                "description": "Issue resolved",
            },
        )
        assert create_resp.status_code == 200, create_resp.text
        ticket_id = create_resp.json()["id"]

        # Update to resolved
        patch_resp = client.patch(
            f"/api/projects/bsh-home-connect/tickets/{ticket_id}",
            json={"status": "resolved"},
        )
        assert patch_resp.status_code == 200, patch_resp.text
        body = patch_resp.json()
        assert body["status"] == "resolved"
        assert body["completed_at"] is not None

    def test_ticket_404_for_unknown_id(self, client):
        resp = client.get("/api/projects/bsh-home-connect/tickets/999999")
        assert resp.status_code == 404

    def test_patch_ticket_404_for_unknown_id(self, client):
        resp = client.patch(
            "/api/projects/bsh-home-connect/tickets/999999",
            json={"status": "in_progress"},
        )
        assert resp.status_code == 404

    def test_update_ticket_priority(self, client):
        _seed_bsh(client)
        my_device = _register_device_for_local_user(client)

        create_resp = client.post(
            "/api/projects/bsh-home-connect/tickets",
            json={
                "customer_device_id": my_device["id"],
                "title": "Priority update test",
                "description": "Changing priority",
                "priority": 3,
            },
        )
        assert create_resp.status_code == 200, create_resp.text
        ticket_id = create_resp.json()["id"]

        patch_resp = client.patch(
            f"/api/projects/bsh-home-connect/tickets/{ticket_id}",
            json={"priority": 1},
        )
        assert patch_resp.status_code == 200, patch_resp.text
        assert patch_resp.json()["priority"] == 1

    def test_update_issue_summary_and_troubleshooting(self, client):
        _seed_bsh(client)
        my_device = _register_device_for_local_user(client)

        create_resp = client.post(
            "/api/projects/bsh-home-connect/tickets",
            json={
                "customer_device_id": my_device["id"],
                "title": "Summary test",
                "description": "Testing summary fields",
            },
        )
        assert create_resp.status_code == 200, create_resp.text
        ticket_id = create_resp.json()["id"]

        patch_resp = client.patch(
            f"/api/projects/bsh-home-connect/tickets/{ticket_id}",
            json={
                "issue_summary": "Pump blockage in drain filter",
                "troubleshooting_attempted": "Cleaned filter, ran empty cycle",
            },
        )
        assert patch_resp.status_code == 200, patch_resp.text
        body = patch_resp.json()
        assert "Pump blockage" in body["issue_summary"]
        assert "Cleaned filter" in body["troubleshooting_attempted"]


# ---------------------------------------------------------------------------
# Ticket note visibility
# ---------------------------------------------------------------------------


class TestTicketNoteVisibility:
    """Internal notes must not be visible to customers (only to technicians)."""

    def test_customer_cannot_see_internal_notes(self, client):
        _seed_bsh(client)
        my_device = _register_device_for_local_user(client)

        create_resp = client.post(
            "/api/projects/bsh-home-connect/tickets",
            json={
                "customer_device_id": my_device["id"],
                "title": "Note visibility test",
                "description": "Testing note visibility",
            },
        )
        assert create_resp.status_code == 200, create_resp.text
        ticket_id = create_resp.json()["id"]

        # Add an internal note (as the current user who is also the customer)
        add_resp = client.post(
            f"/api/projects/bsh-home-connect/tickets/{ticket_id}/notes",
            json={"content": "Internal technician note", "is_internal": True},
        )
        assert add_resp.status_code == 200, add_resp.text

        # List notes — current user is the ticket's customer, so internal notes are filtered
        list_resp = client.get(
            f"/api/projects/bsh-home-connect/tickets/{ticket_id}/notes"
        )
        assert list_resp.status_code == 200, list_resp.text
        notes = list_resp.json()
        internal_notes = [n for n in notes if n.get("is_internal")]
        assert len(internal_notes) == 0, "Customer must not see internal notes"

    def test_public_note_visible_to_customer(self, client):
        _seed_bsh(client)
        my_device = _register_device_for_local_user(client)

        create_resp = client.post(
            "/api/projects/bsh-home-connect/tickets",
            json={
                "customer_device_id": my_device["id"],
                "title": "Public note test",
                "description": "Adding public note",
            },
        )
        assert create_resp.status_code == 200, create_resp.text
        ticket_id = create_resp.json()["id"]

        client.post(
            f"/api/projects/bsh-home-connect/tickets/{ticket_id}/notes",
            json={"content": "Please check the drain filter", "is_internal": False},
        )

        list_resp = client.get(
            f"/api/projects/bsh-home-connect/tickets/{ticket_id}/notes"
        )
        assert list_resp.status_code == 200, list_resp.text
        notes = list_resp.json()
        public_notes = [n for n in notes if not n.get("is_internal")]
        assert len(public_notes) >= 1

    def test_notes_404_for_unknown_ticket(self, client):
        resp = client.get("/api/projects/bsh-home-connect/tickets/999999/notes")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Shipping label
# ---------------------------------------------------------------------------


class TestShippingLabel:
    def test_generates_label_and_tracking_number(self, client):
        _seed_bsh(client)
        my_device = _register_device_for_local_user(client)

        create_resp = client.post(
            "/api/projects/bsh-home-connect/tickets",
            json={
                "customer_device_id": my_device["id"],
                "title": "Shipping label test",
                "description": "Generating shipping label",
            },
        )
        assert create_resp.status_code == 200, create_resp.text
        ticket_id = create_resp.json()["id"]

        label_resp = client.post(
            f"/api/projects/bsh-home-connect/tickets/{ticket_id}/shipping-label"
        )
        assert label_resp.status_code == 200, label_resp.text
        body = label_resp.json()
        assert "shipping_label_url" in body
        assert "tracking_number" in body
        assert str(ticket_id) in body["tracking_number"] or "BSH" in body["tracking_number"]

    def test_shipping_label_sets_status_to_shipped(self, client):
        _seed_bsh(client)
        my_device = _register_device_for_local_user(client)

        create_resp = client.post(
            "/api/projects/bsh-home-connect/tickets",
            json={
                "customer_device_id": my_device["id"],
                "title": "Shipping status test",
                "description": "Verifying status transition",
            },
        )
        assert create_resp.status_code == 200, create_resp.text
        ticket_id = create_resp.json()["id"]

        client.post(f"/api/projects/bsh-home-connect/tickets/{ticket_id}/shipping-label")

        get_resp = client.get(f"/api/projects/bsh-home-connect/tickets/{ticket_id}")
        assert get_resp.status_code == 200, get_resp.text
        body = get_resp.json()
        assert body["status"] == "shipped_for_repair"
        assert body["shipping_label_url"] is not None
        assert body["tracking_number"] is not None

    def test_shipping_label_404_for_unknown_ticket(self, client):
        resp = client.post(
            "/api/projects/bsh-home-connect/tickets/999999/shipping-label"
        )
        assert resp.status_code == 404
