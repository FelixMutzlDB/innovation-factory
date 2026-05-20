"""Dealer-side tenancy isolation regression test (RT-003 + RT-022).

Plan §10 RT-003 (Critical): "Klaus sees raw Martin data via dealer
Genie space" — Klaus's SP grants exclude all ``yp_*`` and
``yard_pro_bronze/silver`` tables.
Plan §10 RT-022 (Critical): "Genie SQL leaks PII through an unintended
JOIN to a non-anonymized table".

This file covers the **API-layer** enforcement. The UC grant rail
(Klaus's service principal can SELECT only on
``yard_pro_gold.dealer_customer_summary`` and nothing else) is enforced
separately at deploy time and documented in
``scripts/yard_pro/RUNBOOK.md`` §11.

What the API layer must guarantee:

1. Klaus's ``X-Forwarded-Dealer`` header is **scoped** — he can only
   query rows for his dealer_id from
   ``GET /dealer/customers/anonymized``. Setting his header to another
   dealer's value gets him that other dealer's rows, but not Martin's
   household-side endpoints; setting it to nothing gets him the
   seeded-fallback dealer's rows.

2. Klaus cannot reach any ``yp_*`` Lakebase table through the dealer
   endpoint. The endpoint never returns yard_id; only yard_id_hash.

3. Klaus cannot reach ``yard_pro_bronze.*`` / ``yard_pro_silver.*`` —
   the dealer endpoint reads from the aggregation_service, which only
   touches Lakebase consent + yards + tools, and produces records
   shaped like the gold table. No bronze/silver SQL is issued by the
   API layer.

Test names reference the **symptom** (RT-003 + RT-022) per the
regression-test rule from CLAUDE.md.
"""
from __future__ import annotations

import uuid

import pytest

# Register yard_pro models with SQLModel.metadata at import time.
import innovation_factory.backend.projects.yard_pro.models  # noqa: F401


@pytest.fixture
def fixed_hmac_secret(monkeypatch):
    """Pin the HMAC secret so the dealer endpoint actually emits rows."""
    secret = "klaus-isolation-test-secret"
    from innovation_factory.backend.projects.yard_pro import (
        databricks_config,
    )

    monkeypatch.setattr(databricks_config, "DEALER_HMAC_SECRET", secret)
    return secret


@pytest.fixture
def two_dealers_two_yards(session, fixed_hmac_secret):
    """Seed:
    - Yard A (Alice) → grants consent to dealer_x (Klaus's competitor)
    - Yard B (Bob)   → grants consent to dealer_y (Klaus)
    Klaus's X-Forwarded-Dealer = dealer_y; the test asserts he sees
    yard B's hash but not yard A's.
    """
    from innovation_factory.backend.projects.yard_pro.models import (
        YardProConsentState,
        YpYard,
    )
    from innovation_factory.backend.projects.yard_pro.services import (
        consent_service,
    )

    alice_key = f"alice-{uuid.uuid4().hex[:8]}@yard-pro.local"
    bob_key = f"bob-{uuid.uuid4().hex[:8]}@yard-pro.local"

    alice_yard = YpYard(
        user_key=alice_key,
        display_name="Alice",
        region_code="DE-BW",
        size_m2=400.0,
        yard_metadata={},
    )
    bob_yard = YpYard(
        user_key=bob_key,
        display_name="Bob",
        region_code="DE-BW",
        size_m2=800.0,
        yard_metadata={},
    )
    session.add(alice_yard)
    session.add(bob_yard)
    session.commit()
    session.refresh(alice_yard)
    session.refresh(bob_yard)
    assert alice_yard.id is not None
    assert bob_yard.id is not None

    for yard_id, dealer in (
        (alice_yard.id, "dealer_x"),
        (bob_yard.id, "dealer_y"),
    ):
        for target in (
            YardProConsentState.pending,
            YardProConsentState.granted,
        ):
            consent_service.transition(
                session,
                yard_id=yard_id,
                dealer_id=dealer,
                target_state=target,
            )
    session.commit()

    return {
        "alice_yard": alice_yard,
        "bob_yard": bob_yard,
    }


# ---------------------------------------------------------------------------
# RT-003 + RT-022 — Klaus's dealer header scopes the result
# ---------------------------------------------------------------------------


class TestKlausDealerHeaderIsScoped:
    def test_klaus_sees_only_his_dealer_rows(
        self, client, two_dealers_two_yards
    ):
        """Klaus's X-Forwarded-Dealer = dealer_y → sees Bob's hash; the
        other dealer's row (Alice for dealer_x) MUST NOT appear."""
        resp = client.get(
            "/api/projects/yard-pro/dealer/customers/anonymized",
            headers={"X-Forwarded-Dealer": "dealer_y"},
        )
        assert resp.status_code == 200, resp.text
        rows = resp.json()
        dealer_ids_seen = {r["dealer_id"] for r in rows}
        assert dealer_ids_seen == {"dealer_y"} or dealer_ids_seen == set(), (
            "Klaus (dealer_y) saw another dealer's rows — RT-003 leak. "
            f"Got: {dealer_ids_seen}"
        )

    def test_klaus_cannot_query_another_dealers_scope(
        self, client, two_dealers_two_yards
    ):
        """Klaus tries spoofing ``X-Forwarded-Dealer=dealer_x``. In
        production the Databricks Apps proxy is the only writer of this
        header so this is a paper attack; in test we mimic the worst
        case where the header is settable. The expectation: Klaus only
        sees rows for whatever dealer the header NAMES. This test
        documents that the header IS the boundary — RT-006 (rate-limit
        bypass via header spoofing) mitigation row notes the same
        trust model.

        The reason this is OK: even with a malicious header, Klaus's
        UC grants at the workspace layer (documented in RUNBOOK.md §11)
        still scope what his SP can SELECT. The API-layer scoping here
        is defense-in-depth.
        """
        resp = client.get(
            "/api/projects/yard-pro/dealer/customers/anonymized",
            headers={"X-Forwarded-Dealer": "dealer_x"},
        )
        assert resp.status_code == 200, resp.text
        dealer_ids_seen = {r["dealer_id"] for r in resp.json()}
        assert dealer_ids_seen.issubset({"dealer_x"}), (
            "Header-scoped fetch leaked rows from a dealer not named "
            f"in X-Forwarded-Dealer. Got: {dealer_ids_seen}"
        )

    def test_dealer_endpoint_never_returns_raw_yard_id(
        self, client, two_dealers_two_yards
    ):
        """The endpoint response shape MUST NOT include a ``yard_id``
        field at all. The frontend has no path to surface it."""
        resp = client.get(
            "/api/projects/yard-pro/dealer/customers/anonymized",
            headers={"X-Forwarded-Dealer": "dealer_y"},
        )
        assert resp.status_code == 200
        rows = resp.json()
        assert rows, "Expected at least 1 row for dealer_y"
        for r in rows:
            assert "yard_id" not in r, (
                f"yard_id field exposed in dealer response: {r}"
            )
            assert "user_key" not in r
            assert "lat" not in r
            assert "lng" not in r


# ---------------------------------------------------------------------------
# RT-003 — Klaus can't reach yp_* household endpoints
# ---------------------------------------------------------------------------


class TestKlausCannotReachConsumerEndpoints:
    """Klaus authenticates as a dealer SP, not as a household. He has
    no X-Forwarded-User → consumer endpoints' RLS rejects him.

    These tests use the local-dev fallback user_key (``martin@yard-
    pro.local``) — a real Klaus deployment wouldn't have this header
    because the Apps proxy authenticates him as a dealer SP, not a
    household user. The boundary here is API-layer:

    - GET /yards/me with a yard-pro X-Forwarded-User Klaus made up →
      404 if no matching seed (the test uses a random key).
    - GET /plants, /tools, /inventory → same.

    We don't need to test that Klaus can't see Martin's
    yp_action_log etc. directly — the consumer endpoints use the
    yards.assert_yard_owned_by_caller helper, already exercised by
    test_cross_household_isolation.
    """

    def test_random_klaus_header_gets_404_on_consumer_yard(self, client):
        """Klaus's X-Forwarded-User (if he ever had one) doesn't match
        any yard. He gets 404 — the RLS rail closes the consumer side."""
        klaus_key = f"klaus-attacker-{uuid.uuid4().hex[:8]}@dealer.local"
        resp = client.get(
            "/api/projects/yard-pro/yards/me",
            headers={"X-Forwarded-User": klaus_key},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# RT-022 — Klaus can't reach yard_pro_bronze/silver via the API
# ---------------------------------------------------------------------------


class TestKlausCannotReachBronzeOrSilverViaApi:
    """No router under ``yard-pro`` exposes a Bronze or Silver Delta
    table read. The dealer endpoint reads from aggregation_service →
    Lakebase ``yp_*`` + ``yp_dealer_relationships`` only, then projects
    into the gold-table shape. We assert this by enumerating the
    yard-pro router tree."""

    def test_no_yard_pro_router_path_exposes_bronze_or_silver(self):
        """Walk the registered routes and confirm none of them name
        ``bronze`` or ``silver``. If a future router exposes the
        Bronze/Silver layer directly, this test fails."""
        from innovation_factory.backend.app import app

        offending = []
        for route in app.routes:
            path = getattr(route, "path", "")
            if not path.startswith("/api/projects/yard-pro"):
                continue
            lower = path.lower()
            if "bronze" in lower or "silver" in lower:
                offending.append(path)
        assert not offending, (
            "yard-pro router exposes a Bronze/Silver path — RT-022 "
            f"surface area widening: {offending}"
        )

    def test_aggregation_service_reads_no_delta_only_lakebase(self):
        """Source-level assertion: the aggregation_service module
        imports nothing that talks to Delta directly. A future
        contributor who wires a Delta read here gets flagged.

        We compare against the AST of the module (executable code
        only — docstrings and comments are excluded). This avoids
        false positives from the module's own documentation, which
        legitimately *mentions* the bronze/silver layer to explain
        why it never reads them.
        """
        import ast
        import inspect

        from innovation_factory.backend.projects.yard_pro.services import (
            aggregation_service,
        )

        source = inspect.getsource(aggregation_service)
        tree = ast.parse(source)

        # Walk import statements + name references (not Constant strings,
        # which would catch docstring text).
        names_used: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names_used.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                names_used.add(node.module or "")
                for alias in node.names:
                    names_used.add(alias.name)
            elif isinstance(node, ast.Attribute):
                names_used.add(node.attr)
            elif isinstance(node, ast.Name):
                names_used.add(node.id)

        forbidden_identifiers = {
            "spark",
            "SparkSession",
            "DeltaTable",
        }
        leaks = forbidden_identifiers & names_used
        assert not leaks, (
            f"aggregation_service references {leaks} — RT-022 widening "
            "(executable code, not docstring text)"
        )
        # And forbid imports of bronze/silver schema modules.
        forbidden_imports = {
            n for n in names_used if "yard_pro_bronze" in n or "yard_pro_silver" in n
        }
        assert not forbidden_imports, (
            f"aggregation_service imports {forbidden_imports} — "
            "RT-022 widening at the import layer"
        )
