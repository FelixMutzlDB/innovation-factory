"""Dealer anonymization regression test (UC6, plan §2 P2).

Plan §2 non-negotiable: "anonymization is **irreversible at ingest**".
Plan §8 access-control row + RT-022: "Klaus's SP has UC SELECT only on
``yard_pro_gold.*``; cannot reach ``yard_pro_bronze/silver``".
RT-012: "Stale dealer consent state — Klaus's query returns a household
that revoked after query started" → aggregation reads consent on every
batch.
RT-023: "Dealer brute-forces consent state by probing for which
households appear" → HMAC with rotating secret.

Test names reference the **symptom** the invariant prevents. These are
unit-level — they call :mod:`aggregation_service` directly, no test
client. The integration coverage lives in
``test_klaus_cannot_see_revoked_household_data.py``.
"""
from __future__ import annotations

import os
import uuid

import pytest

# Register yard_pro models with SQLModel.metadata at import time.
import innovation_factory.backend.projects.yard_pro.models  # noqa: F401


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fixed_hmac_secret(monkeypatch):
    """Pin the HMAC secret so tests can assert specific hash values.

    The aggregation_service reads ``DEALER_HMAC_SECRET`` from the
    ``databricks_config`` module at hash time; we monkey-patch the module
    attribute so every test starts with a known secret.
    """
    secret = "test-hmac-secret-fixed-for-determinism"
    from innovation_factory.backend.projects.yard_pro import (
        databricks_config,
    )

    monkeypatch.setattr(databricks_config, "DEALER_HMAC_SECRET", secret)
    return secret


@pytest.fixture
def yard_with_tools(session, fixed_hmac_secret):
    """Seed a yard + 3 tools (one robotic mower) and grant consent."""
    from innovation_factory.backend.projects.yard_pro.models import (
        YardProBatteryFamily,
        YardProConsentState,
        YardProToolKind,
        YpDealerRelationship,
        YpTool,
        YpYard,
    )

    user_key = f"yard-{uuid.uuid4().hex[:8]}@yard-pro.local"
    yard = YpYard(
        user_key=user_key,
        display_name="Test Yard",
        region_code="DE-BW-stuttgart-basin",
        size_m2=750.0,
        yard_metadata={},
    )
    session.add(yard)
    session.commit()
    session.refresh(yard)

    # Intentionally avoid YardProToolKind.robotic_mower here — the
    # session-scoped engine in conftest.py is shared, and other tests
    # (test_telemetry_synthesizer) assume a single robotic mower in
    # the database. Use trimmer + hedge_cutter so this fixture has a
    # non-degenerate tool_inventory_hash without colliding with that
    # test's brittle ``.one()`` assertion.
    tools = [
        YpTool(
            yard_id=yard.id,
            kind=YardProToolKind.trimmer,
            display_name="Trimmer",
            battery_family=YardProBatteryFamily.ap,
        ),
        YpTool(
            yard_id=yard.id,
            kind=YardProToolKind.hedge_cutter,
            display_name="Hedge cutter",
            battery_family=YardProBatteryFamily.ap,
        ),
        YpTool(
            yard_id=yard.id,
            kind=YardProToolKind.blower,
            display_name="Blower",
            battery_family=YardProBatteryFamily.ap,
        ),
    ]
    for t in tools:
        session.add(t)
    session.commit()
    return yard


def _grant(session, yard_id, dealer_id: str):  # yard_id: int | None accepted
    from innovation_factory.backend.projects.yard_pro.models import (
        YardProConsentState,
    )
    from innovation_factory.backend.projects.yard_pro.services import (
        consent_service,
    )

    assert yard_id is not None
    for target in (
        YardProConsentState.pending,
        YardProConsentState.granted,
    ):
        consent_service.transition(
            session,
            yard_id=yard_id,
            dealer_id=dealer_id,
            target_state=target,
        )
    session.commit()


# ---------------------------------------------------------------------------
# RT-012 + RT-022 — anonymize_yard excludes non-granted households
# ---------------------------------------------------------------------------


class TestAnonymizeRespectsConsentGate:
    def test_anonymize_blocked_when_no_relationship_exists(
        self, session, yard_with_tools, fixed_hmac_secret
    ):
        """A yard with no consent relationship at all is structurally
        non-anonymizable. The function MUST raise — not silently return
        a record with consent_state=none."""
        from innovation_factory.backend.projects.yard_pro.services import (
            aggregation_service,
        )

        with pytest.raises(aggregation_service.AnonymizationBlockedError):
            aggregation_service.anonymize_yard(
                session,
                yard_with_tools.id,
                dealer_id="dealer_unknown",
            )

    def test_anonymize_blocked_when_state_is_pending(
        self, session, yard_with_tools, fixed_hmac_secret
    ):
        """RT-022 — a pending household must not appear in the gold
        table. The function raises, not returns."""
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProConsentState,
        )
        from innovation_factory.backend.projects.yard_pro.services import (
            aggregation_service,
            consent_service,
        )

        consent_service.transition(
            session,
            yard_id=yard_with_tools.id,
            dealer_id="dealer_stuttgart_nord",
            target_state=YardProConsentState.pending,
        )
        session.commit()

        with pytest.raises(aggregation_service.AnonymizationBlockedError):
            aggregation_service.anonymize_yard(
                session,
                yard_with_tools.id,
                dealer_id="dealer_stuttgart_nord",
            )

    def test_anonymize_blocked_after_revoke(
        self, session, yard_with_tools, fixed_hmac_secret
    ):
        """RT-012 — household revokes after being granted. The function
        MUST refuse to produce a record."""
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProConsentState,
        )
        from innovation_factory.backend.projects.yard_pro.services import (
            aggregation_service,
            consent_service,
        )

        _grant(session, yard_with_tools.id, "dealer_stuttgart_nord")
        consent_service.transition(
            session,
            yard_id=yard_with_tools.id,
            dealer_id="dealer_stuttgart_nord",
            target_state=YardProConsentState.revoked,
        )
        session.commit()

        with pytest.raises(aggregation_service.AnonymizationBlockedError):
            aggregation_service.anonymize_yard(
                session,
                yard_with_tools.id,
                dealer_id="dealer_stuttgart_nord",
            )

    def test_batch_anonymize_excludes_revoked_households(
        self, session, yard_with_tools, fixed_hmac_secret
    ):
        """Batch path: revoked households silently drop out (not raise).

        Engine is session-scoped — other tests may have created
        granted rows under common dealer names. Use a randomized
        dealer_id unique to this test so the assertion can be precise.
        """
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProConsentState,
            YpYard,
        )
        from innovation_factory.backend.projects.yard_pro.services import (
            aggregation_service,
            consent_service,
        )

        dealer_id = f"dealer-batch-test-{uuid.uuid4().hex[:8]}"

        # Yard A: granted with the unique dealer; yard B: revoked.
        _grant(session, yard_with_tools.id, dealer_id)

        yard_b_key = f"yard-b-{uuid.uuid4().hex[:8]}@yard-pro.local"
        yard_b = YpYard(
            user_key=yard_b_key,
            display_name="Revoked Yard",
            region_code="DE-BW-stuttgart-basin",
            size_m2=400.0,
            yard_metadata={},
        )
        session.add(yard_b)
        session.commit()
        session.refresh(yard_b)
        assert yard_b.id is not None
        _grant(session, yard_b.id, dealer_id)
        consent_service.transition(
            session,
            yard_id=yard_b.id,
            dealer_id=dealer_id,
            target_state=YardProConsentState.revoked,
        )
        session.commit()

        records = aggregation_service.anonymize_consented_yards(session)
        # Filter to OUR unique dealer; yard A must appear, yard B must
        # NOT — even though yard B has a granted-then-revoked history
        # on this dealer, the latest state is revoked.
        dealer_records = [r for r in records if r.dealer_id == dealer_id]
        assert len(dealer_records) == 1, (
            f"Expected exactly 1 record for {dealer_id} (yard A only), got "
            f"{len(dealer_records)}: {[(r.yard_size_bucket, r.yard_id_hash) for r in dealer_records]}"
        )
        assert dealer_records[0].yard_size_bucket == "medium_500_1000_m2"


# ---------------------------------------------------------------------------
# Anonymized-record shape: never returns raw yard_id
# ---------------------------------------------------------------------------


class TestAnonymizedRecordShape:
    def test_anonymized_record_has_no_yard_id_field(
        self, session, yard_with_tools, fixed_hmac_secret
    ):
        """Structural enforcement: ``AnonymizedRecord`` has no ``yard_id``
        attribute at all. This is the irreversible-at-ingest rail at the
        type level — a future refactor can't accidentally add the raw
        ID back without changing the dataclass."""
        from innovation_factory.backend.projects.yard_pro.services import (
            aggregation_service,
        )

        _grant(session, yard_with_tools.id, "dealer_stuttgart_nord")
        record = aggregation_service.anonymize_yard(
            session,
            yard_with_tools.id,
            dealer_id="dealer_stuttgart_nord",
        )
        # Type-level: no yard_id attribute on the dataclass.
        assert not hasattr(record, "yard_id"), (
            "AnonymizedRecord exposes raw yard_id — irreversible-at-"
            "ingest rail violated"
        )
        # And the hash must be the opaque HMAC token, never a plaintext
        # encoding of the raw id. A substring check on the hex digest is
        # meaningless — hex always contains decimal digits, so `str(id)`
        # lands in the digest by coincidence (flaky for low ids) — so we
        # assert the real leak modes instead: the token is not the raw id,
        # nor a `yh_<id>` passthrough, and is a proper `yh_`-prefixed digest.
        assert record.yard_id_hash != str(yard_with_tools.id)
        assert record.yard_id_hash != f"yh_{yard_with_tools.id}"
        assert record.yard_id_hash.startswith("yh_")

    def test_yard_id_hash_is_deterministic_given_fixed_secret(
        self, session, yard_with_tools, fixed_hmac_secret
    ):
        """Same yard_id + same secret → same hash. Multi-season analytics
        depend on this. (The secret rotation procedure breaks
        determinism deliberately — that's documented in the runbook.)"""
        from innovation_factory.backend.projects.yard_pro.services import (
            aggregation_service,
        )

        _grant(session, yard_with_tools.id, "dealer_stuttgart_nord")
        r1 = aggregation_service.anonymize_yard(
            session,
            yard_with_tools.id,
            dealer_id="dealer_stuttgart_nord",
        )
        r2 = aggregation_service.anonymize_yard(
            session,
            yard_with_tools.id,
            dealer_id="dealer_stuttgart_nord",
        )
        assert r1.yard_id_hash == r2.yard_id_hash

    def test_yard_id_hash_differs_per_yard_id(
        self, session, fixed_hmac_secret
    ):
        """Two distinct yards under the same secret → distinct hashes.
        Without this, every household would alias to one bucket and
        Klaus would see one synthetic "average customer" instead of N
        anonymized rows."""
        from innovation_factory.backend.projects.yard_pro.models import YpYard
        from innovation_factory.backend.projects.yard_pro.services import (
            aggregation_service,
        )

        yards = []
        for i in range(3):
            y = YpYard(
                user_key=f"yard-{i}-{uuid.uuid4().hex[:6]}@yard-pro.local",
                display_name=f"Yard {i}",
                region_code="DE-BW",
                size_m2=600.0,
                yard_metadata={},
            )
            session.add(y)
            session.commit()
            session.refresh(y)
            assert y.id is not None
            _grant(session, y.id, "dealer_x")
            yards.append(y)

        hashes = {
            aggregation_service.anonymize_yard(
                session, y.id, dealer_id="dealer_x"
            ).yard_id_hash
            for y in yards
            if y.id is not None
        }
        assert len(hashes) == 3, (
            "Distinct yard_ids collapsed to the same yard_id_hash — "
            "secret/HMAC bug, RT-023 mitigation breaks"
        )

    def test_yard_id_hash_changes_when_secret_rotates(
        self, session, yard_with_tools, monkeypatch
    ):
        """Rotating ``DEALER_HMAC_SECRET`` rotates the hash space. This
        is by design — and the runbook documents that previous-rotation
        rows become orphans until the seed is re-run."""
        from innovation_factory.backend.projects.yard_pro import (
            databricks_config,
        )
        from innovation_factory.backend.projects.yard_pro.services import (
            aggregation_service,
        )

        monkeypatch.setattr(databricks_config, "DEALER_HMAC_SECRET", "secret-A")
        _grant(session, yard_with_tools.id, "dealer_stuttgart_nord")
        h_a = aggregation_service.anonymize_yard(
            session,
            yard_with_tools.id,
            dealer_id="dealer_stuttgart_nord",
        ).yard_id_hash

        monkeypatch.setattr(databricks_config, "DEALER_HMAC_SECRET", "secret-B")
        h_b = aggregation_service.anonymize_yard(
            session,
            yard_with_tools.id,
            dealer_id="dealer_stuttgart_nord",
        ).yard_id_hash

        assert h_a != h_b

    def test_empty_secret_refuses_to_emit_hashes(
        self, session, yard_with_tools, monkeypatch
    ):
        """A zero/empty secret would defeat the irreversible-at-ingest
        rail. The service refuses; the dealer-side endpoint surfaces
        503 (lessons §18 "not configured" pattern)."""
        from innovation_factory.backend.projects.yard_pro import (
            databricks_config,
        )
        from innovation_factory.backend.projects.yard_pro.services import (
            aggregation_service,
        )

        monkeypatch.setattr(databricks_config, "DEALER_HMAC_SECRET", "")
        _grant(session, yard_with_tools.id, "dealer_x")
        with pytest.raises(aggregation_service.HmacSecretMissingError):
            aggregation_service.anonymize_yard(
                session, yard_with_tools.id, dealer_id="dealer_x"
            )


# ---------------------------------------------------------------------------
# Bucketing — no raw lat/lng or precision leak
# ---------------------------------------------------------------------------


class TestBucketing:
    @pytest.mark.parametrize(
        "size_m2,expected",
        [
            (199.0, "small_200_500_m2"),
            (350.0, "small_200_500_m2"),
            (500.0, "medium_500_1000_m2"),
            (999.0, "medium_500_1000_m2"),
            (1000.0, "large_1000_plus_m2"),
            (5000.0, "large_1000_plus_m2"),
        ],
    )
    def test_size_bucket_boundaries(self, size_m2, expected):
        from innovation_factory.backend.projects.yard_pro.services import (
            aggregation_service,
        )

        assert aggregation_service._yard_size_bucket(size_m2) == expected

    def test_region_bucket_same_prefix_collides(self, fixed_hmac_secret):
        """Two DE-BW yards must land in the same region bucket; a
        DE-BY yard must land in a different one. The bucket itself is
        opaque (HMAC hex), not the source code."""
        from innovation_factory.backend.projects.yard_pro.services import (
            aggregation_service,
        )

        secret = fixed_hmac_secret.encode("utf-8")
        b_stuttgart_1 = aggregation_service._region_bucket(
            "DE-BW-stuttgart-basin", secret=secret
        )
        b_stuttgart_2 = aggregation_service._region_bucket(
            "DE-BW-stuttgart-filder", secret=secret
        )
        b_munich = aggregation_service._region_bucket(
            "DE-BY-munich", secret=secret
        )
        assert b_stuttgart_1 == b_stuttgart_2
        assert b_stuttgart_1 != b_munich
