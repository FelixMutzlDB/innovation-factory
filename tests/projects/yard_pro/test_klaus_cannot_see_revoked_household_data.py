"""Named regression test from plan §7 — the headline UC6 invariant.

Plan §10 RT-003 (Critical): "Klaus sees raw Martin data via dealer
Genie space" — mitigation includes:
    "Regression test: ``test_klaus_cannot_see_revoked_household_data``
    + a P5 integration test that asserts a row deleted from Lakebase
    no longer appears in Klaus's Genie results within sync latency."

This file ships the API-layer half of that integration test:

  Seed yard_A with consent_state=granted →
  GET /dealer/customers/anonymized as Klaus → yard_A_hash present
  Transition yard_A to revoked →
  GET /dealer/customers/anonymized as Klaus → yard_A_hash absent

The Lakehouse-Sync half (Delta propagation) lives downstream of this
test and is documented in the runbook §11 — out of scope for the
Lakebase-side regression.

Test name and symptom match the plan reference verbatim. Do NOT rename
this file without updating plan §10 RT-003 to match.
"""
from __future__ import annotations

import uuid

import pytest

# Register yard_pro models with SQLModel.metadata at import time.
import innovation_factory.backend.projects.yard_pro.models  # noqa: F401


@pytest.fixture
def fixed_hmac_secret(monkeypatch):
    """Pin the HMAC secret so yard_A's hash is stable across the two
    queries this test issues. Without this the dealer endpoint would
    raise 503 ("not configured") and the test would fail trivially."""
    secret = "revoked-regression-secret"
    from innovation_factory.backend.projects.yard_pro import (
        databricks_config,
    )

    monkeypatch.setattr(databricks_config, "DEALER_HMAC_SECRET", secret)
    return secret


@pytest.fixture
def yard_a_granted(session, fixed_hmac_secret):
    """Seed a household (yard_A) that has explicitly granted consent
    to the test dealer.

    Uses a randomized dealer_id so this test's view is isolated from
    other tests' rows in the session-scoped engine — the named
    regression must be able to distinguish "yard_A revoked" from
    "some other test's yard still granted".
    """
    from innovation_factory.backend.projects.yard_pro.models import (
        YardProBatteryFamily,
        YardProConsentState,
        YardProToolKind,
        YpTool,
        YpYard,
    )
    from innovation_factory.backend.projects.yard_pro.services import (
        consent_service,
    )

    test_run = uuid.uuid4().hex[:8]
    user_key = f"martin-A-{test_run}@yard-pro.local"
    dealer_id = f"dealer-regression-{test_run}"
    yard = YpYard(
        user_key=user_key,
        display_name="Martin A",
        region_code="DE-BW-stuttgart-basin",
        size_m2=750.0,
        yard_metadata={},
    )
    session.add(yard)
    session.commit()
    session.refresh(yard)

    # One tool so the inventory hash is non-degenerate. Intentionally
    # NOT a robotic_mower — test_telemetry_synthesizer asserts globally
    # one robotic mower in the session-scoped DB.
    session.add(
        YpTool(
            yard_id=yard.id,
            kind=YardProToolKind.hedge_cutter,
            display_name="Hedge cutter",
            battery_family=YardProBatteryFamily.ap,
        )
    )
    session.commit()
    assert yard.id is not None

    for target in (
        YardProConsentState.pending,
        YardProConsentState.granted,
    ):
        consent_service.transition(
            session,
            yard_id=yard.id,
            dealer_id=dealer_id,
            target_state=target,
        )
    session.commit()
    return {
        "yard": yard,
        "dealer_id": dealer_id,
        "consumer_headers": {"X-Forwarded-User": user_key},
        "dealer_headers": {"X-Forwarded-Dealer": dealer_id},
    }


def test_klaus_cannot_see_revoked_household_data(
    client, session, yard_a_granted
):
    """The named regression. Sequence:

    1. Query dealer endpoint as Klaus — yard_A's hash MUST appear (granted).
    2. Transition yard_A → revoked via the consumer-side API.
    3. Re-query dealer endpoint as Klaus — yard_A's hash MUST be absent.
    """
    consumer_headers = yard_a_granted["consumer_headers"]
    dealer_headers = yard_a_granted["dealer_headers"]
    dealer_id = yard_a_granted["dealer_id"]

    # 1. Granted → yard_A appears. Scope to OUR dealer so other tests'
    # granted rows don't leak into the assertion.
    first = client.get(
        "/api/projects/yard-pro/dealer/customers/anonymized",
        headers=dealer_headers,
    )
    assert first.status_code == 200, first.text
    first_rows = [r for r in first.json() if r["dealer_id"] == dealer_id]
    assert len(first_rows) == 1, (
        f"Expected exactly 1 row for {dealer_id} while granted, got "
        f"{len(first_rows)}: {first_rows}"
    )
    yard_a_hash = first_rows[0]["yard_id_hash"]

    # 2. Consumer revokes via the API.
    rels = client.get(
        "/api/projects/yard-pro/dealer/relationships",
        headers=consumer_headers,
    )
    assert rels.status_code == 200
    rel = next(r for r in rels.json() if r["dealer_id"] == dealer_id)
    rel_id = rel["id"]
    revoke = client.delete(
        f"/api/projects/yard-pro/dealer/relationships/{rel_id}",
        headers=consumer_headers,
    )
    assert revoke.status_code == 200, revoke.text
    assert revoke.json()["consent_state"] == "revoked"

    # 3. Revoked → yard_A vanishes from Klaus's view for OUR dealer.
    second = client.get(
        "/api/projects/yard-pro/dealer/customers/anonymized",
        headers=dealer_headers,
    )
    assert second.status_code == 200, second.text
    second_for_our_dealer = [
        r for r in second.json() if r["dealer_id"] == dealer_id
    ]
    assert second_for_our_dealer == [], (
        "RT-003 leak: yard_A's row still visible to Klaus after revoke. "
        f"Got: {second_for_our_dealer}; revoked hash was: {yard_a_hash}"
    )
