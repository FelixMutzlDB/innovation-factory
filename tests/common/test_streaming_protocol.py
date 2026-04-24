"""Tests for the canonical SSE streaming protocol shared by all chat
endpoints (D1 normalization).

The protocol:
  - Each chunk is emitted as ``data: <plain text>\\n\\n``.
  - A mid-stream error is emitted as ``data: {"error": "..."}\\n\\n``
    then the stream ends.
  - The stream always ends with ``data: [DONE]\\n\\n``.

Every chat service in the repo must yield plain text (or raise) — not
JSON envelopes with ``{"content": ..., "done": ...}`` wrappers. These
tests enforce that contract.
"""
from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

import pytest

from innovation_factory.backend.services.streaming import create_chat_stream


async def _consume(stream_response) -> list[str]:
    """Collect every SSE `data:` line from a StreamingResponse into a
    list (one entry per chunk, without the ``data: `` prefix and the
    trailing blank line)."""
    body = b""
    async for piece in stream_response.body_iterator:
        if isinstance(piece, str):
            piece = piece.encode()
        body += piece
    lines = body.decode().split("\n\n")
    return [line[len("data: "):] for line in lines if line.startswith("data: ")]


async def _gen_plain(chunks):
    for c in chunks:
        yield c


async def _gen_error_after(chunks, exc):
    for c in chunks:
        yield c
    raise exc


class TestStreamingProtocol:
    @pytest.mark.asyncio
    async def test_plain_chunks_then_done_sentinel(self):
        stream = _gen_plain(["Hello", " world", "!"])
        resp = await create_chat_stream(stream)
        events = await _consume(resp)
        # Expect three text chunks then [DONE].
        assert events[:3] == ["Hello", " world", "!"]
        assert events[-1] == "[DONE]"

    @pytest.mark.asyncio
    async def test_on_complete_receives_full_response(self):
        captured: list[str] = []
        stream = _gen_plain(["a", "b", "c"])
        resp = await create_chat_stream(stream, on_complete=lambda s: captured.append(s))
        await _consume(resp)
        assert captured == ["abc"]

    @pytest.mark.asyncio
    async def test_error_emits_event_and_stops(self):
        stream = _gen_error_after(["partial"], RuntimeError("boom"))
        resp = await create_chat_stream(stream)
        events = await _consume(resp)
        # First a partial text chunk, then an error JSON envelope, then
        # the stream ends — no [DONE] sentinel after an error.
        assert events[0] == "partial"
        err = json.loads(events[1])
        assert "boom" in err["error"]
        assert "[DONE]" not in events

    @pytest.mark.asyncio
    async def test_empty_stream_still_emits_done(self):
        resp = await create_chat_stream(_gen_plain([]))
        events = await _consume(resp)
        assert events == ["[DONE]"]


class TestNoBshStyleJsonWrappingOfResponseText:
    """Regression: don't wrap the *response text itself* in a JSON
    envelope like BSH used to do (``yield json.dumps({"content":
    full_text, "done": False})``). That pattern forces the frontend
    to parse every chunk as JSON and extract ``.content`` instead of
    rendering it as a plain-text stream — inconsistent with the other
    four chat endpoints.

    Note: structured *metadata* envelopes (e.g. adtech/hb emit a
    single JSON blob carrying ``session_id`` + ``sources`` alongside
    the response) are fine. We only catch the inline-text pattern
    where ``content`` is interpolated from a local variable.
    """

    def test_no_response_text_in_content_envelope(self):
        import pathlib
        import re
        import subprocess

        repo = pathlib.Path(__file__).resolve().parents[2]
        r = subprocess.run(
            ["git", "ls-files", "src/innovation_factory/backend/"],
            cwd=repo, capture_output=True, text=True, check=True,
        )
        # The BSH anti-pattern was:
        #   yield json.dumps({"content": response, "done": False})
        # where ``response`` is the full assistant text already in hand.
        # We catch any ``{"content": <identifier>,`` or ``{"content":
        # <identifier>}`` where the identifier is a bare name
        # (not a string literal).
        offender_pattern = re.compile(
            r'yield\s+json\.dumps\(\{\s*"content"\s*:\s*[A-Za-z_][\w]*\s*[,}]'
        )
        offenders = []
        for rel in r.stdout.splitlines():
            path = repo / rel
            if path.suffix != ".py":
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if offender_pattern.search(line):
                    offenders.append(f"{rel}:{lineno}: {line.strip()}")
        assert not offenders, (
            "Chat services must stream response text as plain chunks "
            "(yield the text directly). Found BSH-style JSON-wrapped "
            "response text:\n" + "\n".join(offenders)
        )
