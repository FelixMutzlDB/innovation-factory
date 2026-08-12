"""API tests for support ticket CRUD.

Covers:
- GET  /tickets              → list (empty, filtered by household/status)
- POST /tickets              → create (200 / 404 household / shape)
- GET  /tickets/{id}         → 200 / 404
- PATCH /tickets/{id}        → status transitions / resolved_at set / 404
"""
from __future__ import annotations

import pytest

import innovation_factory.backend.projects.vi_home_one.models  # noqa: F401

BASE = "/api/projects/vi-home-one"


def _seed_neighborhood_and_household(session, owner="Ticket User"):
    from innovation_factory.backend.projects.vi_home_one.models import VhNeighborhood, VhHousehold
    n = VhNeighborhood(name="Ticket Hood", location="Berlin", total_households=1)
    session.add(n)
    session.commit()
    session.refresh(n)
    h = VhHousehold(neighborhood_id=n.id, owner_name=owner, address="Ticket Str. 1")
    session.add(h)
    session.commit()
    session.refresh(h)
    return h


def _create_ticket_via_api(client, household_id, title="Test Ticket", description="Details"):
    return client.post(
        f"{BASE}/tickets",
        params={"household_id": household_id},
        json={"title": title, "description": description},
    )


class TestListTickets:
    def test_empty_returns_empty_list(self, client):
        resp = client.get(f"{BASE}/tickets")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_filter_by_household_id(self, client, session):
        h1 = _seed_neighborhood_and_household(session, owner="User A")
        h2 = _seed_neighborhood_and_household(session, owner="User B")
        _create_ticket_via_api(client, h1.id, title="Ticket for H1")
        _create_ticket_via_api(client, h2.id, title="Ticket for H2")

        resp = client.get(f"{BASE}/tickets?household_id={h1.id}")
        assert resp.status_code == 200
        tickets = resp.json()
        for t in tickets:
            assert t["household_id"] == h1.id

    def test_filter_by_status(self, client, session):
        h = _seed_neighborhood_and_household(session)
        r1 = _create_ticket_via_api(client, h.id, title="New ticket")
        assert r1.status_code == 200
        ticket_id = r1.json()["id"]

        # Resolve it
        client.patch(f"{BASE}/tickets/{ticket_id}", json={"status": "resolved"})

        new_resp = client.get(f"{BASE}/tickets?status=new")
        resolved_resp = client.get(f"{BASE}/tickets?status=resolved")
        assert all(t["status"] == "new" for t in new_resp.json())
        assert all(t["status"] == "resolved" for t in resolved_resp.json())

    def test_newest_first_ordering(self, client, session):
        h = _seed_neighborhood_and_household(session)
        _create_ticket_via_api(client, h.id, title="First ticket")
        _create_ticket_via_api(client, h.id, title="Second ticket")

        resp = client.get(f"{BASE}/tickets?household_id={h.id}")
        assert resp.status_code == 200
        tickets = resp.json()
        timestamps = [t["created_at"] for t in tickets]
        assert timestamps == sorted(timestamps, reverse=True)


class TestCreateTicket:
    def test_unknown_household_returns_404(self, client):
        resp = client.post(
            f"{BASE}/tickets",
            params={"household_id": 99999},
            json={"title": "Test", "description": "Desc"},
        )
        assert resp.status_code == 404

    def test_create_returns_200_with_shape(self, client, session):
        h = _seed_neighborhood_and_household(session)
        resp = _create_ticket_via_api(client, h.id, title="My Issue", description="Details here")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "My Issue"
        assert data["description"] == "Details here"
        assert data["status"] == "new"
        assert data["household_id"] == h.id
        assert data["resolved_at"] is None

    def test_create_with_optional_priority(self, client, session):
        h = _seed_neighborhood_and_household(session)
        resp = client.post(
            f"{BASE}/tickets",
            params={"household_id": h.id},
            json={"title": "Urgent", "description": "It's urgent", "priority": "high"},
        )
        assert resp.status_code == 200
        assert resp.json()["priority"] == "high"

    def test_create_without_priority(self, client, session):
        h = _seed_neighborhood_and_household(session)
        resp = _create_ticket_via_api(client, h.id)
        assert resp.status_code == 200
        assert resp.json()["priority"] is None

    def test_missing_title_returns_422(self, client, session):
        h = _seed_neighborhood_and_household(session)
        resp = client.post(
            f"{BASE}/tickets",
            params={"household_id": h.id},
            json={"description": "Missing title"},
        )
        assert resp.status_code == 422

    def test_missing_description_returns_422(self, client, session):
        h = _seed_neighborhood_and_household(session)
        resp = client.post(
            f"{BASE}/tickets",
            params={"household_id": h.id},
            json={"title": "No description"},
        )
        assert resp.status_code == 422


class TestGetTicket:
    def test_unknown_id_returns_404(self, client):
        resp = client.get(f"{BASE}/tickets/99999")
        assert resp.status_code == 404

    def test_known_id_returns_200(self, client, session):
        h = _seed_neighborhood_and_household(session)
        create_resp = _create_ticket_via_api(client, h.id, title="Test Ticket")
        ticket_id = create_resp.json()["id"]
        resp = client.get(f"{BASE}/tickets/{ticket_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Test Ticket"

    def test_response_shape(self, client, session):
        h = _seed_neighborhood_and_household(session)
        ticket_id = _create_ticket_via_api(client, h.id).json()["id"]
        resp = client.get(f"{BASE}/tickets/{ticket_id}")
        assert resp.status_code == 200
        data = resp.json()
        expected = {
            "id", "household_id", "title", "description", "status",
            "created_at", "updated_at", "resolved_at",
        }
        assert expected.issubset(set(data.keys()))


class TestUpdateTicket:
    def test_unknown_id_returns_404(self, client):
        resp = client.patch(f"{BASE}/tickets/99999", json={"status": "resolved"})
        assert resp.status_code == 404

    def test_status_transition_new_to_in_progress(self, client, session):
        h = _seed_neighborhood_and_household(session)
        tid = _create_ticket_via_api(client, h.id).json()["id"]
        resp = client.patch(f"{BASE}/tickets/{tid}", json={"status": "in_progress"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    def test_resolved_status_sets_resolved_at(self, client, session):
        h = _seed_neighborhood_and_household(session)
        tid = _create_ticket_via_api(client, h.id).json()["id"]
        resp = client.patch(f"{BASE}/tickets/{tid}", json={"status": "resolved"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "resolved"
        assert data["resolved_at"] is not None

    def test_resolution_notes_can_be_added(self, client, session):
        h = _seed_neighborhood_and_household(session)
        tid = _create_ticket_via_api(client, h.id).json()["id"]
        resp = client.patch(
            f"{BASE}/tickets/{tid}",
            json={"status": "resolved", "resolution_notes": "Fixed by replacing filter"},
        )
        assert resp.status_code == 200
        assert resp.json()["resolution_notes"] == "Fixed by replacing filter"

    def test_patch_without_status_preserves_original_status(self, client, session):
        h = _seed_neighborhood_and_household(session)
        tid = _create_ticket_via_api(client, h.id).json()["id"]
        resp = client.patch(f"{BASE}/tickets/{tid}", json={"resolution_notes": "Working on it"})
        assert resp.status_code == 200
        # Status unchanged from 'new' since no status field in patch
        assert resp.json()["status"] == "new"

    def test_status_escalated_transition(self, client, session):
        h = _seed_neighborhood_and_household(session)
        tid = _create_ticket_via_api(client, h.id).json()["id"]
        resp = client.patch(f"{BASE}/tickets/{tid}", json={"status": "escalated"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "escalated"
        # escalated does NOT set resolved_at
        assert resp.json()["resolved_at"] is None
