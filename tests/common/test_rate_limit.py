"""Tests for backend/rate_limit.py.

The rate limiter keys on the authenticated user (``X-Forwarded-User``)
not the socket IP. Civion-safe lesson 19.9: sizing is realistic per
endpoint; lesson 19.10: the test strategy relies on fine-grained
keying so one test's requests don't fill another test's quota.
"""
from __future__ import annotations

from unittest.mock import MagicMock

from innovation_factory.backend.rate_limit import _user_or_ip


def _req_with_headers(**headers: str) -> MagicMock:
    r = MagicMock()
    r.headers = headers
    r.client = MagicMock()
    r.client.host = "127.0.0.1"
    return r


class TestKeyExtractor:
    def test_uses_x_forwarded_user(self):
        req = _req_with_headers(**{"X-Forwarded-User": "felix@example.test"})
        assert _user_or_ip(req) == "user:felix@example.test"

    def test_falls_back_to_preferred_username(self):
        req = _req_with_headers(
            **{"X-Forwarded-Preferred-Username": "felix"}
        )
        assert _user_or_ip(req) == "user:felix"

    def test_falls_back_to_ip_when_no_user_header(self):
        # No proxy headers → slowapi's get_remote_address uses request.client
        req = _req_with_headers()
        key = _user_or_ip(req)
        assert key.startswith("ip:")

    def test_different_users_get_different_keys(self):
        alice = _req_with_headers(**{"X-Forwarded-User": "alice@example.test"})
        bob = _req_with_headers(**{"X-Forwarded-User": "bob@example.test"})
        assert _user_or_ip(alice) != _user_or_ip(bob)


class TestLimiterEnforcement:
    """End-to-end test: hit the idea-session chat endpoint beyond its
    20/minute budget and assert the 21st request returns 429 with a
    JSON body and a Retry-After header."""

    def test_idea_chat_returns_429_after_budget_exhausted(self, client):
        # Create a session first
        create = client.post("/api/ideas/sessions")
        session_id = create.json()["id"]

        headers = {"X-Forwarded-User": "ratetest-idea@example.test"}
        url = f"/api/ideas/sessions/{session_id}/chat"
        payload = {"content": "hi"}

        # First 20 requests succeed (the budget)
        for i in range(20):
            resp = client.post(url, json=payload, headers=headers)
            # The idea flow returns 200 for the first two turns, then the
            # session status transitions and later turns also 200 (the
            # fallback template is used when IDEA_GENERATOR_ENDPOINT
            # isn't reachable). Either way, not 429.
            assert resp.status_code != 429, (
                f"hit 429 too early at request {i}: {resp.json()}"
            )

        # The 21st request should be rejected
        resp = client.post(url, json=payload, headers=headers)
        assert resp.status_code == 429
        body = resp.json()
        assert body["error"] == "rate_limit_exceeded"
        assert "retry_after_seconds" in body
        # Content-Type is application/json (civion lesson 19.11)
        assert resp.headers["content-type"].startswith("application/json")
        # Retry-After header is present
        assert "retry-after" in {k.lower() for k in resp.headers.keys()}

    def test_different_users_have_independent_quotas(self, client):
        create = client.post("/api/ideas/sessions")
        session_id = create.json()["id"]
        url = f"/api/ideas/sessions/{session_id}/chat"

        # User A exhausts their quota
        headers_a = {"X-Forwarded-User": "alice-quota@example.test"}
        for _ in range(20):
            client.post(url, json={"content": "hi"}, headers=headers_a)
        resp_a = client.post(url, json={"content": "hi"}, headers=headers_a)
        assert resp_a.status_code == 429

        # User B should still have a full quota
        headers_b = {"X-Forwarded-User": "bob-quota@example.test"}
        resp_b = client.post(url, json={"content": "hi"}, headers=headers_b)
        assert resp_b.status_code != 429, (
            "bob's quota was consumed by alice — keying is broken"
        )
