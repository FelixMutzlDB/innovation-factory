"""Coach SSE streaming contract tests (UC2).

These exercise the streaming protocol (lessons §12), the advisory chip
invariant (plan §2 — EU AI Act Art. 50), session/message persistence,
and the "not configured" first-class state (lessons §18). The provenance
rail (citations on recommendation turns) is covered separately in
``test_provenance_required.py``.

Note: ``VISION_ENDPOINT`` / ``COACH_KA_ENDPOINT`` are empty in the test
env, so by default the coach takes the "not configured" path and returns
a stable string. Tests that need to exercise the live KA path patch the
endpoint constant inline.
"""
from __future__ import annotations

from unittest.mock import patch

from innovation_factory.backend.projects.yard_pro.seed import seed_yp_data
from innovation_factory.backend.projects.yard_pro.services import coach_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed(client) -> None:
    """Seed Martin's yard via the same session the test client uses."""
    from sqlmodel import Session, select

    from innovation_factory.backend.app import app
    from innovation_factory.backend.dependencies import get_session
    from innovation_factory.backend.projects.yard_pro.models import YpYard

    override = app.dependency_overrides.get(get_session)
    assert override is not None
    gen = override()
    session = next(gen)
    try:
        existing = session.exec(select(YpYard)).first()
        if not existing:
            seed_yp_data(session)
            session.commit()
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


def _open_session(client) -> int:
    r = client.post(
        "/api/projects/yard-pro/coach/sessions",
        json={"yard_id": 1, "title": "Test session"},
        headers={"X-Forwarded-User": "martin@yard-pro.local"},
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _consume_sse(content: bytes) -> list[str]:
    """Split an SSE byte stream into the ``data:`` payload values."""
    text = content.decode()
    out = []
    for block in text.split("\n\n"):
        if block.startswith("data: "):
            out.append(block[len("data: ") :])
    return out


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------


class TestCoachSessions:
    def test_create_session(self, client):
        _seed(client)
        r = client.post(
            "/api/projects/yard-pro/coach/sessions",
            json={"yard_id": 1, "title": "Weekend chat"},
            headers={"X-Forwarded-User": "martin@yard-pro.local"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["yard_id"] == 1
        assert body["title"] == "Weekend chat"
        assert isinstance(body["id"], int)

    def test_list_sessions_empty_for_no_yard(self, client):
        # No seed → resolver falls back to "any yard" or 404.
        r = client.get(
            "/api/projects/yard-pro/coach/sessions",
            headers={"X-Forwarded-User": "unknown@yard-pro.local"},
        )
        # When no yard exists at all → 404 from the resolver.
        assert r.status_code in (200, 404)

    def test_list_sessions_returns_recent(self, client):
        _seed(client)
        sid_a = _open_session(client)
        sid_b = _open_session(client)
        r = client.get(
            "/api/projects/yard-pro/coach/sessions",
            headers={"X-Forwarded-User": "martin@yard-pro.local"},
        )
        assert r.status_code == 200
        ids = [row["id"] for row in r.json()]
        assert sid_a in ids and sid_b in ids


# ---------------------------------------------------------------------------
# Streaming SSE
# ---------------------------------------------------------------------------


class TestCoachStreaming:
    def test_chat_not_configured_returns_stream_with_explanation(self, client):
        """When ``COACH_KA_ENDPOINT`` is unset (default in test env), the
        service returns a stable "not configured" response and streams
        it as plain-text chunks ending with [DONE] (lessons §12, §18).
        """
        _seed(client)
        sid = _open_session(client)
        r = client.post(
            f"/api/projects/yard-pro/coach/sessions/{sid}/chat",
            json={"prompt": "what should I do this weekend?"},
            headers={"X-Forwarded-User": "martin@yard-pro.local"},
        )
        assert r.status_code == 200
        events = _consume_sse(r.content)
        # Must end with [DONE] sentinel per the shared streaming protocol.
        assert "[DONE]" in events
        # At least one chunk before the sentinel.
        assert len(events) >= 2
        # The "not configured" text mentions YARD_PRO_COACH_KA_ENDPOINT.
        joined = "".join(events)
        assert "not configured" in joined.lower()

    def test_chat_with_mocked_ka_streams_response(self, client):
        """With a mocked KA endpoint, the chat streams the model's text
        as plain-text chunks then [DONE].

        The router checks ``databricks_config.COACH_KA_ENDPOINT`` (still
        empty in tests) to decide whether to touch ``runtime.ws`` — so we
        only need to patch ``coach_service.COACH_KA_ENDPOINT`` to make
        the synthesis path go live, and ``query_agent_endpoint`` to
        avoid the real Databricks call.
        """
        _seed(client)
        sid = _open_session(client)

        fake_response = {
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Mow the lawn tomorrow."}],
                }
            ],
            "citations": [
                {"doc_path": "ka_docs/regional_almanac/stuttgart_may.md", "chunk_id": "c1", "score": 0.92}
            ],
        }
        with patch.object(coach_service, "COACH_KA_ENDPOINT", "fake-ka-endpoint"), patch(
            "innovation_factory.backend.projects.yard_pro.services.coach_service.query_agent_endpoint",
            return_value=fake_response,
        ):
            r = client.post(
                f"/api/projects/yard-pro/coach/sessions/{sid}/chat",
                json={"prompt": "general chat — how is my yard"},
                headers={"X-Forwarded-User": "martin@yard-pro.local"},
            )
        assert r.status_code == 200
        events = _consume_sse(r.content)
        # Plain text chunks were emitted, not a wrapped JSON envelope.
        assert "[DONE]" in events
        joined = "".join(e for e in events if e != "[DONE]")
        assert "Mow the lawn tomorrow." in joined

    def test_chat_persists_assistant_message_with_advisory_true(self, client):
        """Plan §2 NN: every coach assistant message must carry
        ``advisory=True`` so the UI renders the Art. 50 chip."""
        _seed(client)
        sid = _open_session(client)
        # Even on the "not configured" path the assistant message is
        # persisted with the chip.
        client.post(
            f"/api/projects/yard-pro/coach/sessions/{sid}/chat",
            json={"prompt": "hello"},
            headers={"X-Forwarded-User": "martin@yard-pro.local"},
        )
        # Read history.
        r = client.get(
            f"/api/projects/yard-pro/coach/sessions/{sid}/messages",
            headers={"X-Forwarded-User": "martin@yard-pro.local"},
        )
        assert r.status_code == 200
        msgs = r.json()
        assistants = [m for m in msgs if m["role"] == "assistant"]
        assert len(assistants) >= 1
        assert all(m["advisory"] is True for m in assistants)

    def test_chat_user_message_carries_no_advisory(self, client):
        """The advisory chip is for AI-generated content. Persisted user
        turns should NOT have it set (otherwise the chip becomes
        meaningless noise)."""
        _seed(client)
        sid = _open_session(client)
        client.post(
            f"/api/projects/yard-pro/coach/sessions/{sid}/chat",
            json={"prompt": "hello"},
            headers={"X-Forwarded-User": "martin@yard-pro.local"},
        )
        r = client.get(
            f"/api/projects/yard-pro/coach/sessions/{sid}/messages",
            headers={"X-Forwarded-User": "martin@yard-pro.local"},
        )
        users = [m for m in r.json() if m["role"] == "user"]
        assert len(users) >= 1
        assert all(m["advisory"] is False for m in users)

    def test_chat_rejects_html_via_sanitizer(self, client):
        """Plan §8 + lessons §20 — user-supplied text is sanitized at the
        API boundary so HTML tags never persist."""
        _seed(client)
        sid = _open_session(client)
        r = client.post(
            f"/api/projects/yard-pro/coach/sessions/{sid}/chat",
            json={"prompt": "<script>alert('x')</script>hi"},
            headers={"X-Forwarded-User": "martin@yard-pro.local"},
        )
        # Either 200 (sanitizer strips silently) or 422 (max-length etc).
        assert r.status_code == 200
        # Pull history and assert no <script> survived.
        msgs = client.get(
            f"/api/projects/yard-pro/coach/sessions/{sid}/messages",
            headers={"X-Forwarded-User": "martin@yard-pro.local"},
        ).json()
        user_turns = [m for m in msgs if m["role"] == "user"]
        assert all("<script>" not in m["content"] for m in user_turns)


# ---------------------------------------------------------------------------
# Router discipline + operation_id prefix
# ---------------------------------------------------------------------------


class TestCoachOperationIds:
    def test_all_coach_operation_ids_use_yp_prefix(self):
        from innovation_factory.backend.projects.yard_pro.router import (
            router as yard_pro_router,
        )
        from fastapi.routing import APIRoute

        coach_paths = [r for r in yard_pro_router.routes if isinstance(r, APIRoute) and "coach" in r.path]
        assert coach_paths, "coach routes must be registered under yard_pro router"
        for r in coach_paths:
            assert r.operation_id is not None
            assert r.operation_id.startswith("yp_"), (
                f"coach operation_id must start with yp_: {r.operation_id}"
            )
