"""Tests for backend/pagination.py.

Verifies the shared Pagination dependency's bounds and that list
endpoints actually honour ``skip`` + ``limit`` (no overlap, upper-bound
enforced).
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from innovation_factory.backend.pagination import (
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
    PageParams,
)


class TestPageParams:
    def test_defaults(self):
        p = PageParams()
        assert p.skip == 0
        assert p.limit == DEFAULT_PAGE_LIMIT

    def test_accepts_max_limit(self):
        p = PageParams(skip=0, limit=MAX_PAGE_LIMIT)
        assert p.limit == MAX_PAGE_LIMIT

    def test_rejects_over_max(self):
        with pytest.raises(ValidationError):
            PageParams(skip=0, limit=MAX_PAGE_LIMIT + 1)

    def test_rejects_negative_skip(self):
        with pytest.raises(ValidationError):
            PageParams(skip=-1, limit=10)

    def test_rejects_zero_limit(self):
        with pytest.raises(ValidationError):
            PageParams(skip=0, limit=0)


class TestVhTicketsPagination:
    """End-to-end: hit the VH tickets endpoint with different skip/limit
    combos and assert the responses don't overlap and respect the cap."""

    def _seed_tickets(self, session, household_id, count):
        from innovation_factory.backend.projects.vi_home_one.models import (
            VhHousehold,
            VhNeighborhood,
            VhTicket,
            VhTicketStatus,
        )

        # Ensure the FK chain (neighborhood -> household) exists. Without a
        # seeded vh_neighborhoods table this test would FK-error against a
        # clean engine; the previous test infra masked the dep via a
        # shared-state SQLite file (see TODO B2).
        nh_id = 9001
        if not session.get(VhNeighborhood, nh_id):
            session.add(VhNeighborhood(
                id=nh_id,
                name="Pagination-test neighborhood",
                location="Testville",
                total_households=1,
            ))
            session.flush()

        if not session.get(VhHousehold, household_id):
            hh = VhHousehold(
                id=household_id,
                neighborhood_id=nh_id,
                name="Test household",
                owner_name="pagination-test",
                address="pagination@example.test",
                num_residents=1,
            )
            session.add(hh)
            session.flush()

        for i in range(count):
            session.add(
                VhTicket(
                    household_id=household_id,
                    title=f"Ticket {i}",
                    description=f"body {i}",
                    priority="medium",
                    status=VhTicketStatus.new,
                )
            )
        session.commit()

    def test_rejects_limit_over_max(self, client):
        resp = client.get(
            f"/api/projects/vi-home-one/tickets?limit={MAX_PAGE_LIMIT + 1}"
        )
        assert resp.status_code == 422

    def test_rejects_negative_skip(self, client):
        resp = client.get("/api/projects/vi-home-one/tickets?skip=-1")
        assert resp.status_code == 422

    def test_pages_dont_overlap(self, client, session):
        # Use a household id that's unlikely to collide with seed data.
        hh = 9001
        self._seed_tickets(session, hh, 25)
        first = client.get(
            f"/api/projects/vi-home-one/tickets"
            f"?household_id={hh}&skip=0&limit=10"
        )
        second = client.get(
            f"/api/projects/vi-home-one/tickets"
            f"?household_id={hh}&skip=10&limit=10"
        )
        assert first.status_code == 200 and second.status_code == 200
        ids_first = {t["id"] for t in first.json()}
        ids_second = {t["id"] for t in second.json()}
        assert len(ids_first) == 10
        assert len(ids_second) == 10
        assert ids_first.isdisjoint(ids_second), "pages must not overlap"

    def test_limit_bounds_response(self, client, session):
        hh = 9002
        self._seed_tickets(session, hh, 5)
        resp = client.get(
            f"/api/projects/vi-home-one/tickets"
            f"?household_id={hh}&limit=2"
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2
