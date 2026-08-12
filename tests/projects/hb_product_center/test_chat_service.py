"""HB Product Center chat service tests.

Covers the pure logic of ``HbChatService._extract_mas_response``:
  - Plain string output
  - Standard chat-completion fallback (choices list)
  - MAS list-of-items format: function_call + message items
  - Edge cases: non-dict input, missing keys, empty content blocks

The DB-backed methods (_get_or_create_session, _save_user_message, etc.)
are tested via the session fixture to verify SQLite compatibility.

torch / CLIP are NOT referenced anywhere here.
"""
from __future__ import annotations

import json

import pytest

import innovation_factory.backend.projects.hb_product_center.models  # noqa: F401
from innovation_factory.backend.projects.hb_product_center.services.chat_service import (
    HbChatService,
    SYSTEM_PROMPT,
)


# ---------------------------------------------------------------------------
# _extract_mas_response — pure logic
# ---------------------------------------------------------------------------


class TestExtractMasResponse:
    def _svc(self):
        return HbChatService()

    def test_plain_string_output(self):
        svc = self._svc()
        content, sources = svc._extract_mas_response({"output": "Hello!"})
        assert content == "Hello!"
        assert len(sources) == 1
        assert sources[0]["type"] == "agent"

    def test_none_output_falls_through_to_choices(self):
        svc = self._svc()
        resp = {
            "choices": [{"message": {"content": "From choices"}}],
        }
        content, sources = svc._extract_mas_response(resp)
        assert content == "From choices"

    def test_empty_choices_falls_through_to_str(self):
        svc = self._svc()
        resp = {"choices": []}
        content, sources = svc._extract_mas_response(resp)
        # Falls through to str(response)
        assert isinstance(content, str)

    def test_non_dict_input_returns_string(self):
        svc = self._svc()
        content, sources = svc._extract_mas_response("raw string response")
        assert content == "raw string response"
        assert sources == []

    def test_mas_list_format_message_items(self):
        svc = self._svc()
        resp = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"text": "Supply chain looks good."},
                        {"text": "No delays detected."},
                    ],
                }
            ]
        }
        content, sources = svc._extract_mas_response(resp)
        assert "Supply chain looks good." in content
        assert "No delays detected." in content

    def test_mas_function_call_items_populate_sources(self):
        svc = self._svc()
        resp = {
            "output": [
                {"type": "function_call", "name": "hb-quality-agent"},
                {"type": "function_call", "name": "hb-quality-agent"},  # duplicate
                {
                    "type": "message",
                    "content": [{"text": "Quality report."}],
                },
            ]
        }
        content, sources = svc._extract_mas_response(resp)
        # Duplicate agent name should appear only once in sources
        agent_names = [s["source"] for s in sources if s["type"] == "agent"]
        assert len(agent_names) == len(set(agent_names)), "duplicate agent in sources"

    def test_mas_name_tag_lines_skipped(self):
        """Content blocks that are just <name>...</name> tags must be filtered."""
        svc = self._svc()
        resp = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"text": "<name>quality-agent</name>"},
                        {"text": "Actual response content."},
                    ],
                }
            ]
        }
        content, _ = svc._extract_mas_response(resp)
        assert "<name>" not in content
        assert "Actual response content." in content

    def test_empty_output_list_returns_empty_string(self):
        svc = self._svc()
        content, sources = svc._extract_mas_response({"output": []})
        assert content == ""
        assert len(sources) == 1  # default source added

    def test_default_source_added_when_no_function_calls(self):
        svc = self._svc()
        resp = {
            "output": [
                {"type": "message", "content": [{"text": "Hello"}]}
            ]
        }
        _, sources = svc._extract_mas_response(resp)
        assert any(s["type"] == "agent" for s in sources)

    def test_non_list_output_returns_str(self):
        svc = self._svc()
        content, _ = svc._extract_mas_response({"output": 42})
        assert content == "42"

    def test_empty_text_blocks_are_skipped(self):
        svc = self._svc()
        resp = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"text": ""},       # empty — skip
                        {"text": "Keep."},
                    ],
                }
            ]
        }
        content, _ = svc._extract_mas_response(resp)
        assert content == "Keep."


# ---------------------------------------------------------------------------
# SYSTEM_PROMPT sanity
# ---------------------------------------------------------------------------


class TestSystemPrompt:
    def test_prompt_mentions_key_domains(self):
        assert "supply chain" in SYSTEM_PROMPT.lower()
        assert "quality" in SYSTEM_PROMPT.lower()
        assert "authenticity" in SYSTEM_PROMPT.lower()

    def test_prompt_is_nonempty(self):
        assert len(SYSTEM_PROMPT.strip()) > 50


# ---------------------------------------------------------------------------
# DB-backed: session creation and message persistence
# ---------------------------------------------------------------------------


class TestChatSessionDB:
    def test_creates_session_when_no_id(self, session):
        svc = HbChatService()
        chat_session = svc._get_or_create_session(session, session_id=None)
        assert chat_session.id is not None

    def test_reuses_existing_session(self, session):
        svc = HbChatService()
        first = svc._get_or_create_session(session, session_id=None)
        assert first.id is not None
        second = svc._get_or_create_session(session, session_id=first.id)
        assert second.id == first.id

    def test_save_user_message(self, session):
        from innovation_factory.backend.projects.hb_product_center.models import HbChatMessage
        from sqlmodel import select as sq_select

        svc = HbChatService()
        chat_session = svc._get_or_create_session(session, session_id=None)
        assert chat_session.id is not None
        svc._save_user_message(session, chat_session.id, "Hello, Product Center!")

        msgs = session.exec(
            sq_select(HbChatMessage).where(
                HbChatMessage.session_id == chat_session.id
            )
        ).all()
        assert len(msgs) == 1
        assert msgs[0].role == "user"
        assert msgs[0].content == "Hello, Product Center!"

    def test_message_history_returns_ordered(self, session):
        """_get_message_history should return messages in created_at order."""
        svc = HbChatService()
        chat_session = svc._get_or_create_session(session, session_id=None)
        assert chat_session.id is not None

        svc._save_user_message(session, chat_session.id, "First")
        svc._save_assistant_message(session, chat_session.id, "Reply", [])
        svc._save_user_message(session, chat_session.id, "Second")

        history = svc._get_message_history(session, chat_session.id, limit=10)
        assert len(history) == 3
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "First"
        assert history[2]["content"] == "Second"

    def test_message_history_respects_limit(self, session):
        svc = HbChatService()
        chat_session = svc._get_or_create_session(session, session_id=None)
        assert chat_session.id is not None

        for i in range(15):
            svc._save_user_message(session, chat_session.id, f"msg {i}")

        history = svc._get_message_history(session, chat_session.id, limit=5)
        assert len(history) == 5
