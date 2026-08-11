"""Tests for workforce shifts, operational issues, and customer endpoints."""
from __future__ import annotations

from datetime import date, timedelta

from ._helpers import _seeding_session, seed_region_and_station

BASE = "/api/projects/mol-asm-cockpit"


def _seed_shift(client, station_id: int, *, shift_date: date,
                shift_type: str = "morning") -> int:
    from innovation_factory.backend.projects.mol_asm_cockpit.models import (
        MacWorkforceShift, ShiftType,
    )
    with _seeding_session(client) as session:
        shift = MacWorkforceShift(
            station_id=station_id,
            shift_date=shift_date,
            shift_type=ShiftType(shift_type),
            planned_headcount=3,
            actual_headcount=2,
            overtime_hours=0.5,
        )
        session.add(shift)
        session.flush()
        assert shift.id is not None
        return shift.id


def _seed_issue(client, station_id: int, suffix: str, *,
                status: str = "open", category: str = "equipment") -> int:
    from innovation_factory.backend.projects.mol_asm_cockpit.models import (
        MacIssue, MacIssueStatus, MacIssueCategory,
    )
    with _seeding_session(client) as session:
        issue = MacIssue(
            station_id=station_id,
            category=MacIssueCategory(category),
            title=f"Test Issue {suffix}",
            description="Something needs attention",
            status=MacIssueStatus(status),
        )
        session.add(issue)
        session.flush()
        assert issue.id is not None
        return issue.id


def _seed_customer(client, suffix: str) -> int:
    from innovation_factory.backend.projects.mol_asm_cockpit.models import (
        MacCustomerProfile, LoyaltyTier,
    )
    with _seeding_session(client) as session:
        customer = MacCustomerProfile(
            company_name=f"Test Corp {suffix}",
            contact_name=f"Contact {suffix}",
            contact_email=f"contact-{suffix}@testcorp.example",
            fleet_size=10,
            loyalty_tier=LoyaltyTier.silver,
        )
        session.add(customer)
        session.flush()
        assert customer.id is not None
        return customer.id


def _seed_contract(client, customer_id: int, suffix: str) -> int:
    from innovation_factory.backend.projects.mol_asm_cockpit.models import (
        MacCustomerContract,
    )
    with _seeding_session(client) as session:
        contract = MacCustomerContract(
            customer_id=customer_id,
            contract_type="fleet",
            monthly_volume_commitment=5000.0,
            discount_pct=0.05,
            start_date=date(2025, 1, 1),
        )
        session.add(contract)
        session.flush()
        assert contract.id is not None
        return contract.id


# ---------------------------------------------------------------------------
# Workforce shifts
# ---------------------------------------------------------------------------


class TestWorkforceShifts:
    def test_returns_200(self, client):
        resp = client.get(f"{BASE}/workforce/shifts")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_seeded_shift_appears(self, client):
        _, station_id = seed_region_and_station(client, "SHIFT-A")
        shift_id = _seed_shift(client, station_id, shift_date=date.today())
        resp = client.get(f"{BASE}/workforce/shifts?station_id={station_id}")
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert shift_id in ids

    def test_filter_by_station_id(self, client):
        _, station_id = seed_region_and_station(client, "SHIFT-B")
        _seed_shift(client, station_id, shift_date=date.today())
        resp = client.get(f"{BASE}/workforce/shifts?station_id={station_id}")
        assert resp.status_code == 200
        assert all(s["station_id"] == station_id for s in resp.json())

    def test_days_cutoff_excludes_old_shift(self, client):
        _, station_id = seed_region_and_station(client, "SHIFT-C")
        old_id = _seed_shift(
            client, station_id,
            shift_date=date.today() - timedelta(days=100),
        )
        resp = client.get(
            f"{BASE}/workforce/shifts?station_id={station_id}&days=7"
        )
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert old_id not in ids

    def test_shift_has_required_fields(self, client):
        _, station_id = seed_region_and_station(client, "SHIFT-D")
        _seed_shift(client, station_id, shift_date=date.today())
        resp = client.get(f"{BASE}/workforce/shifts?station_id={station_id}")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        row = rows[0]
        for field in (
            "id", "station_id", "shift_date", "shift_type",
            "planned_headcount", "actual_headcount", "overtime_hours",
        ):
            assert field in row, f"Shift missing field: {field}"


# ---------------------------------------------------------------------------
# Operational issues
# ---------------------------------------------------------------------------


class TestIssues:
    def test_returns_200(self, client):
        resp = client.get(f"{BASE}/workforce/issues")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_seeded_issue_appears(self, client):
        _, station_id = seed_region_and_station(client, "ISSUE-A")
        issue_id = _seed_issue(client, station_id, "IA1")
        resp = client.get(f"{BASE}/workforce/issues?station_id={station_id}")
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()]
        assert issue_id in ids

    def test_filter_by_status_open(self, client):
        _, station_id = seed_region_and_station(client, "ISSUE-B")
        open_id = _seed_issue(client, station_id, "IB1", status="open")
        resolved_id = _seed_issue(client, station_id, "IB2", status="resolved")
        resp = client.get(
            f"{BASE}/workforce/issues?station_id={station_id}&status=open"
        )
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()]
        assert open_id in ids
        assert resolved_id not in ids

    def test_filter_by_category(self, client):
        _, station_id = seed_region_and_station(client, "ISSUE-C")
        equip_id = _seed_issue(
            client, station_id, "IC1", category="equipment"
        )
        staff_id = _seed_issue(
            client, station_id, "IC2", category="staffing"
        )
        resp = client.get(
            f"{BASE}/workforce/issues?station_id={station_id}&category=equipment"
        )
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()]
        assert equip_id in ids
        assert staff_id not in ids

    def test_issue_has_required_fields(self, client):
        _, station_id = seed_region_and_station(client, "ISSUE-D")
        _seed_issue(client, station_id, "ID1")
        resp = client.get(f"{BASE}/workforce/issues?station_id={station_id}")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        row = rows[0]
        for field in (
            "id", "station_id", "category", "title", "description",
            "status", "priority", "created_at",
        ):
            assert field in row, f"Issue missing field: {field}"


# ---------------------------------------------------------------------------
# Customer profiles and contracts
# ---------------------------------------------------------------------------


class TestCustomers:
    def test_returns_200(self, client):
        resp = client.get(f"{BASE}/workforce/customers")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_seeded_customer_appears(self, client):
        customer_id = _seed_customer(client, "CUSTSA")
        resp = client.get(f"{BASE}/workforce/customers")
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.json()]
        assert customer_id in ids

    def test_customer_has_required_fields(self, client):
        _seed_customer(client, "CUSTFIELDS")
        resp = client.get(f"{BASE}/workforce/customers")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        row = rows[0]
        for field in (
            "id", "company_name", "contact_name", "contact_email",
            "fleet_size", "loyalty_tier",
        ):
            assert field in row, f"Customer missing field: {field}"


class TestCustomerContracts:
    def test_returns_contracts_for_customer(self, client):
        customer_id = _seed_customer(client, "CONTR-A")
        contract_id = _seed_contract(client, customer_id, "CA1")
        resp = client.get(
            f"{BASE}/workforce/customers/{customer_id}/contracts"
        )
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.json()]
        assert contract_id in ids

    def test_unknown_customer_returns_empty_list(self, client):
        """No customer → no contracts; endpoint returns empty list (not 404)."""
        resp = client.get(f"{BASE}/workforce/customers/999999/contracts")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_contract_has_required_fields(self, client):
        customer_id = _seed_customer(client, "CONTR-B")
        _seed_contract(client, customer_id, "CB1")
        resp = client.get(
            f"{BASE}/workforce/customers/{customer_id}/contracts"
        )
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        row = rows[0]
        for field in (
            "id", "customer_id", "contract_type",
            "monthly_volume_commitment", "discount_pct", "start_date",
        ):
            assert field in row, f"Contract missing field: {field}"
