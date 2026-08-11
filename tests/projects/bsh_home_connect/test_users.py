"""Unit tests for get_or_create_customer / get_or_create_technician.

Covers:
- New user creates a customer/technician row
- Existing user returns the same row (idempotent)
- Email fallback when Databricks user has no emails
- Name fallback when Databricks user has no name attribute
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlmodel import select

from innovation_factory.backend.projects.bsh_home_connect.models import (
    BshCustomer,
    BshTechnician,
)
from innovation_factory.backend.projects.bsh_home_connect.routers.users import (
    get_or_create_customer,
    get_or_create_technician,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_user(user_id: str, email: str = "test@example.com",
               first_name: str = "Alice", last_name: str = "Smith"):
    """Build a minimal mock DatabricksUser."""
    user = MagicMock()
    user.id = user_id
    email_obj = MagicMock()
    email_obj.value = email
    user.emails = [email_obj]
    user.name = MagicMock()
    user.name.given_name = first_name
    user.name.family_name = last_name
    return user


def _mock_user_no_email(user_id: str):
    user = MagicMock()
    user.id = user_id
    user.emails = []
    user.name = MagicMock()
    user.name.given_name = "Ghost"
    user.name.family_name = "User"
    return user


def _mock_user_no_name(user_id: str, email: str = "noname@example.com"):
    user = MagicMock()
    user.id = user_id
    email_obj = MagicMock()
    email_obj.value = email
    user.emails = [email_obj]
    user.name = None
    return user


# ---------------------------------------------------------------------------
# get_or_create_customer
# ---------------------------------------------------------------------------


class TestGetOrCreateCustomer:
    def test_new_user_creates_customer(self, session):
        db_user = _mock_user("cust-new-001", "new@example.com", "Jane", "Doe")
        customer = get_or_create_customer(session, db_user)

        assert customer.id is not None
        assert customer.databricks_user_id == "cust-new-001"
        assert customer.email == "new@example.com"
        assert customer.first_name == "Jane"
        assert customer.last_name == "Doe"

    def test_existing_user_returns_same_customer(self, session):
        db_user = _mock_user("cust-existing-001", "existing@example.com")
        c1 = get_or_create_customer(session, db_user)
        c2 = get_or_create_customer(session, db_user)

        assert c1.id == c2.id, "Second call must return the existing row"

    def test_different_users_create_separate_customers(self, session):
        u1 = _mock_user("cust-sep-001", "user1@example.com")
        u2 = _mock_user("cust-sep-002", "user2@example.com")

        c1 = get_or_create_customer(session, u1)
        c2 = get_or_create_customer(session, u2)

        assert c1.id != c2.id
        assert c1.databricks_user_id != c2.databricks_user_id

    def test_email_fallback_when_no_emails(self, session):
        db_user = _mock_user_no_email("cust-noemail-001")
        customer = get_or_create_customer(session, db_user)

        # Fallback pattern: "{user_id}@unknown.com"
        assert "cust-noemail-001" in customer.email
        assert "@" in customer.email

    def test_name_fallback_when_no_name_attribute(self, session):
        db_user = _mock_user_no_name("cust-noname-001", "noname@example.com")
        customer = get_or_create_customer(session, db_user)

        # Must not raise — fallback values used
        assert customer.first_name == "Unknown"
        assert customer.last_name == "User"

    def test_customer_timestamps_set_on_creation(self, session):
        db_user = _mock_user("cust-ts-001", "ts@example.com")
        customer = get_or_create_customer(session, db_user)

        assert customer.created_at is not None
        assert customer.updated_at is not None


# ---------------------------------------------------------------------------
# get_or_create_technician
# ---------------------------------------------------------------------------


class TestGetOrCreateTechnician:
    def test_new_user_creates_technician(self, session):
        db_user = _mock_user("tech-new-001", "tech@example.com", "Bob", "Tech")
        technician = get_or_create_technician(session, db_user)

        assert technician.id is not None
        assert technician.databricks_user_id == "tech-new-001"
        assert technician.email == "tech@example.com"
        assert technician.first_name == "Bob"
        assert technician.last_name == "Tech"

    def test_existing_technician_returned_on_second_call(self, session):
        db_user = _mock_user("tech-existing-001", "techex@example.com")
        t1 = get_or_create_technician(session, db_user)
        t2 = get_or_create_technician(session, db_user)

        assert t1.id == t2.id

    def test_email_fallback_for_technician_without_emails(self, session):
        db_user = _mock_user_no_email("tech-noemail-001")
        technician = get_or_create_technician(session, db_user)

        assert "tech-noemail-001" in technician.email
        assert "@" in technician.email

    def test_name_fallback_for_technician_without_name(self, session):
        db_user = _mock_user_no_name("tech-noname-001", "technoname@example.com")
        technician = get_or_create_technician(session, db_user)

        assert technician.first_name == "Unknown"
        assert technician.last_name == "Technician"

    def test_customer_and_technician_are_independent_entities(self, session):
        """Same Databricks user_id can exist as both customer and technician
        (two different real-world roles, stored in two separate tables)."""
        db_user = _mock_user("dual-role-001", "dual@example.com", "Dual", "Role")
        customer = get_or_create_customer(session, db_user)
        technician = get_or_create_technician(session, db_user)

        # Both rows are created; their IDs come from separate sequences/tables
        assert customer is not None
        assert technician is not None
        assert customer.databricks_user_id == technician.databricks_user_id
