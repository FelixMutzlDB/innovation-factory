"""Shared input sanitization helpers for Pydantic ``*In`` / ``*Create`` models.

Civion-safe lesson 19.1 applied here: sanitize untrusted text at the API
boundary, not just at the render boundary. The SafeMarkdown wrapper
closes the XSS vector at render time; this layer closes it at ingest
time so the bad bytes never land in the database, in logs, in exports,
or in any future non-React consumer.

## What ``sanitize_text`` does

- Drops every HTML tag via a strict regex (``<[^>]+>``). No full HTML
  parser — we never need HTML inside these fields.
- Drops null bytes.
- Collapses surrounding whitespace (``.strip()``).
- Leaves the text otherwise intact — emoji, umlauts, markdown-like
  punctuation (``*``, ``_``, ``#``) all pass through because they're
  meaningful in chat and descriptions.

## Using the annotated type

Applied via Pydantic's ``BeforeValidator`` so it runs on every
construction, including when FastAPI parses a request body:

    from typing import Annotated
    from .input_sanitize import SanitizedStr, ShortText, LongText

    class ChatMessageIn(BaseModel):
        content: LongText  # sanitized + max_length=5000

Three ready-made bounds cover the usual cases:

    ShortText  = Annotated[str, ..., max_length=200]   # names, titles
    MediumText = Annotated[str, ..., max_length=500]   # descriptions, search
    LongText   = Annotated[str, ..., max_length=5000]  # chat bodies, free-form

Use them unless you have a specific reason not to.
"""
from __future__ import annotations

import re
from typing import Annotated

from pydantic import BeforeValidator, Field

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def sanitize_text(value: object) -> object:
    """Strip HTML tags, null bytes, and surrounding whitespace.

    Non-``str`` input passes through untouched so Pydantic's own type
    check reports the right error (``input_type`` instead of our regex
    exploding on a dict).
    """
    if not isinstance(value, str):
        return value
    # Drop null bytes before the tag regex — they can terminate strings
    # in some downstream drivers.
    value = value.replace("\x00", "")
    # Remove anything that looks like an HTML tag. This is intentionally
    # strict: "<" not followed by ">" stays; actual tags are dropped.
    value = _HTML_TAG_RE.sub("", value)
    return value.strip()


#: Base type for any sanitized string.
SanitizedStr = Annotated[str, BeforeValidator(sanitize_text)]

#: Names / titles / short enums-as-strings. 200 chars covers most UI labels.
ShortText = Annotated[str, BeforeValidator(sanitize_text), Field(max_length=200)]

#: Descriptions / search terms. 500 chars matches the existing product-identify limit.
MediumText = Annotated[str, BeforeValidator(sanitize_text), Field(max_length=500)]

#: Chat bodies / free-form user content. 5k covers a long message without
#: blowing up the LLM context window on the backend.
LongText = Annotated[str, BeforeValidator(sanitize_text), Field(max_length=5000)]
