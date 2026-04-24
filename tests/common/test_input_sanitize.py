"""Tests for backend/input_sanitize.py — the shared Pydantic sanitizer
applied to every user-provided free-text field.

Regression coverage for civion-safe lesson 19.1: sanitize at the API
boundary, not just at the render boundary. The SafeMarkdown wrapper
(B1) closes XSS at render time; these tests confirm the server-side
strip runs before any payload reaches the DB or logs.
"""
from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from innovation_factory.backend.input_sanitize import (
    LongText,
    MediumText,
    ShortText,
    sanitize_text,
)


class _Short(BaseModel):
    value: ShortText


class _Medium(BaseModel):
    value: MediumText


class _Long(BaseModel):
    value: LongText


# ---------------------------------------------------------------------------
# sanitize_text function
# ---------------------------------------------------------------------------


class TestSanitizeText:
    def test_strips_html_tags(self):
        assert sanitize_text("<b>hi</b>") == "hi"
        assert sanitize_text('<img src="x">after') == "after"
        assert (
            sanitize_text('before<script>alert("x")</script>after')
            == 'beforealert("x")after'
        )

    def test_strips_event_handlers(self):
        # The tag wrapper is the delivery mechanism; once the tag is gone,
        # the `onerror=` attribute goes with it.
        assert sanitize_text('<img src=x onerror=fetch("/api")>') == ""
        assert sanitize_text('normal<img onerror=x>text') == "normaltext"

    def test_drops_null_bytes(self):
        cleaned = sanitize_text("before\x00after")
        assert isinstance(cleaned, str)
        assert "\x00" not in cleaned
        assert cleaned == "beforeafter"

    def test_strips_surrounding_whitespace(self):
        assert sanitize_text("   hello   ") == "hello"
        assert sanitize_text("\n\tvalue\n") == "value"

    def test_leaves_safe_content_alone(self):
        # Markdown syntax, emoji, umlauts, punctuation: all pass through.
        safe = "# Heading\n*bold* **strong** — with `code` and 🎉 emoji. ä ö ü ß"
        assert sanitize_text(safe) == safe

    def test_lonely_angle_bracket_passes(self):
        # A `<` not followed by a closing `>` is not a tag. Leave it.
        assert sanitize_text("x < 5 is true") == "x < 5 is true"

    def test_non_string_passes_through(self):
        # Non-str input must not crash — Pydantic will emit its own
        # type error downstream.
        assert sanitize_text(42) == 42
        assert sanitize_text(None) is None


# ---------------------------------------------------------------------------
# Annotated types via Pydantic
# ---------------------------------------------------------------------------


class TestAnnotatedBounds:
    @pytest.mark.parametrize(
        "model, limit",
        [(_Short, 200), (_Medium, 500), (_Long, 5000)],
    )
    def test_accepts_at_limit(self, model, limit):
        m = model(value="x" * limit)
        assert len(m.value) == limit

    @pytest.mark.parametrize(
        "model, limit",
        [(_Short, 200), (_Medium, 500), (_Long, 5000)],
    )
    def test_rejects_over_limit(self, model, limit):
        with pytest.raises(ValidationError):
            model(value="x" * (limit + 1))

    def test_sanitize_runs_before_length_check(self):
        # 250 chars of <b></b> (50 tags × 5 chars tag overhead = padded up)
        # after sanitize becomes 0 chars → still fits in ShortText.
        raw = "<b></b>" * 50
        m = _Short(value=raw)
        assert m.value == ""

    def test_html_stripped_in_model(self):
        m = _Long(value="before<script>alert(1)</script>after")
        assert "<script>" not in m.value
        assert m.value == "beforealert(1)after"

    def test_null_byte_dropped_in_model(self):
        m = _Medium(value="user\x00input")
        assert "\x00" not in m.value


# ---------------------------------------------------------------------------
# Wiring into real chat-message models
# ---------------------------------------------------------------------------


class TestChatMessageModels:
    """The five per-project chat models and the platform idea model all
    use LongText for user content. Assert the wiring works end-to-end
    for each."""

    def test_idea_message_sanitizes(self):
        from innovation_factory.backend.models import IdeaMessageIn

        m = IdeaMessageIn(content="<img src=x onerror=alert(1)>normal message")
        assert m.content == "normal message"

    def test_idea_message_length_bound(self):
        from innovation_factory.backend.models import IdeaMessageIn

        with pytest.raises(ValidationError):
            IdeaMessageIn(content="x" * 5001)

    @pytest.mark.parametrize(
        "model_path, cls_name, field",
        [
            (
                "innovation_factory.backend.projects.hb_product_center.models",
                "HbChatMessageIn",
                "content",
            ),
            (
                "innovation_factory.backend.projects.vi_home_one.models",
                "VhChatMessageIn",
                "content",
            ),
            (
                "innovation_factory.backend.projects.bsh_home_connect.models",
                "BshChatMessageIn",
                "message",
            ),
            (
                "innovation_factory.backend.projects.adtech_intelligence.models",
                "AtChatMessageIn",
                "message",
            ),
            (
                "innovation_factory.backend.projects.mol_asm_cockpit.models",
                "MacChatMessageIn",
                "message",
            ),
        ],
    )
    def test_per_project_chat_models_sanitize_and_bound(
        self, model_path, cls_name, field
    ):
        import importlib

        cls = getattr(importlib.import_module(model_path), cls_name)

        # The sanitizer strips HTML tags but keeps their *text content*
        # (the safe interpretation: `<b>hi</b>` → `hi`). What matters is
        # that no angle-bracketed tag survives; the text "evil()" inside
        # is now an inert string.
        payload = "<script>evil()</script>legit content"
        m = cls(**{field: payload})
        cleaned = getattr(m, field)
        assert "<script>" not in cleaned, f"{cls_name}.{field} kept <script>"
        assert "</script>" not in cleaned, f"{cls_name}.{field} kept </script>"
        assert "legit content" in cleaned

        # And an entirely-HTML payload should come back empty.
        empty = cls(**{field: "<img src=x onerror=fetch('/api')>"})
        assert getattr(empty, field) == ""

        with pytest.raises(ValidationError):
            cls(**{field: "x" * 5001})
