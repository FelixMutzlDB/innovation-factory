"""Regex post-filter on log emission — RT-024 belt-and-suspenders mitigation.

Plan §10 RT-024 rates "logs leak yard photos or coach transcripts" as
**Critical** (GDPR Art. 32 violation = up to €20M / 4% global turnover).
The mitigation is three-layered:

1. **Name-based field exclusion** — sensitive field names
   (``photo_uri``, ``predictions``, ``coach_transcript_chunk``) never go
   into structured log calls in the first place.
2. **Regex post-filter on emission** (this module) — last-line defense.
   Wraps the standard library :class:`logging.Filter` and rewrites the
   ``record.msg`` + ``record.args`` so even an accidental
   ``logger.info("got %s", chunk)`` is scrubbed at emission time, before
   the formatter ever sees the bytes.
3. **Log-pipeline assertion test** — ``tests/projects/yard_pro/
   test_log_pipeline_no_pii.py`` runs the diagnose + coach happy paths
   and greps the emitted log stream for canary strings; fails CI if any
   slip through.

## What the filter scrubs

- **Base64 image data** — any string ≥100 chars matching
  ``^[A-Za-z0-9+/=]+$``. Replaced with ``[redacted:base64]``. Lower-
  bound at 100 chars to avoid false positives on UUIDs / hashes / short
  tokens that happen to be base64-shaped.
- **UUID-shaped photo refs** — anything matching ``yard_pro/photos/<uuid
  or numeric id>/...``. Replaced with ``[redacted:photo_uri]``. Catches
  both the production UC Volume path and the local dev ``seed://photos/
  ...`` shape used in tests.
- **Multi-line text blocks > 500 chars** — any string field containing
  one or more newlines AND ≥500 chars. Replaced with
  ``[redacted:long_text]``. This is the coach-transcript / KA-chunk
  shape; we explicitly DO NOT scrub short error stack traces (≤500
  chars) because those are operationally useful.

## Idempotency

The filter is idempotent: running the substitutions twice produces the
same output. The redaction tokens themselves don't match any of the
three regexes, so a double-pass on already-scrubbed text is a no-op.

## Wiring

Attach the filter to the application logger (or any specific logger) in
the FastAPI lifespan or — for tests — directly via
:func:`attach_log_filter`. Returns the filter instance so callers can
detach in teardown.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

_REDACT_BASE64 = "[redacted:base64]"
_REDACT_PHOTO_URI = "[redacted:photo_uri]"
_REDACT_LONG_TEXT = "[redacted:long_text]"

# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

#: UUID-shaped photo refs. Matches both production (``yard_pro/photos/
#: <uuid>/...``) and local-dev seed (``seed://photos/<id>/...``) shapes.
#: The capture is everything after ``photos/`` until whitespace or the
#: end of the string, so a path with subdirectories (``.../leaf.jpg``)
#: is fully replaced — we never want a partial path leaking.
_PHOTO_URI_RE = re.compile(
    r"(?:[A-Za-z0-9_.+-]+(?::/+|/))?(?:yard_pro/)?photos/[^\s\"'`,;)]+"
)

#: Long base64 blob (≥100 chars). Word-boundaried so we don't eat the
#: surrounding whitespace.
_BASE64_RE = re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/=]{100,}(?![A-Za-z0-9+/=])")

#: Multi-line text block > 500 chars. The match must contain at least
#: one newline AND be at least 500 chars. We require a delimiter on each
#: side that isn't whitespace-only so we don't swallow a JSON wrapper.
_MULTILINE_RE = re.compile(r"[^\s][^\x00]*?\n[^\x00]{300,}[^\s]", re.DOTALL)


def scrub_text(value: str) -> str:
    """Apply all three scrubs to a single string.

    Public for testing. Returns the input unchanged when nothing
    matches. Order matters: photo-URI runs FIRST (otherwise a long
    base64-shaped path component could be eaten by the base64 rule);
    base64 runs SECOND; multi-line LAST because the redaction tokens
    themselves don't contain newlines and won't double-trigger.
    """
    if not isinstance(value, str):
        return value
    # Photo URIs first — narrow, targeted rule.
    value = _PHOTO_URI_RE.sub(_REDACT_PHOTO_URI, value)
    # Base64 blobs next.
    value = _BASE64_RE.sub(_REDACT_BASE64, value)
    # Multi-line long text last. Use a length+newline check so we don't
    # spend regex cycles on every short message.
    if "\n" in value and len(value) > 500:
        # Replace the longest run that spans newlines and is large.
        # Conservative: if the whole string qualifies, redact it whole.
        if _MULTILINE_RE.search(value):
            return _REDACT_LONG_TEXT
    return value


def _scrub_args(args: object) -> object:
    """Walk ``record.args`` recursively, applying :func:`scrub_text`.

    ``record.args`` is conventionally a tuple of positional placeholders
    or a single mapping (when the logger is called with %(name)s-style
    format strings). We handle both.
    """
    if isinstance(args, str):
        return scrub_text(args)
    if isinstance(args, tuple):
        return tuple(_scrub_args(a) for a in args)
    if isinstance(args, list):
        return [_scrub_args(a) for a in args]
    if isinstance(args, dict):
        return {k: _scrub_args(v) for k, v in args.items()}
    return args


class YardProPIIFilter(logging.Filter):
    """:class:`logging.Filter` that scrubs PII from records on emission.

    Mutates ``record.msg`` and ``record.args`` in place so downstream
    formatters see the scrubbed payload. Always returns True (filter
    doesn't drop records — only rewrites them).
    """

    name = "yard_pro_pii_filter"

    def filter(self, record: logging.LogRecord) -> bool:
        # Scrub the format string first; many callers do f-string
        # interpolation before passing the result as record.msg, so the
        # sensitive bytes can land here without args.
        if isinstance(record.msg, str):
            record.msg = scrub_text(record.msg)
        # Then the args tuple/mapping.
        if record.args:
            record.args = _scrub_args(record.args)  # type: ignore[assignment]
        return True


def attach_log_filter(
    logger: Optional[logging.Logger] = None,
) -> YardProPIIFilter:
    """Attach :class:`YardProPIIFilter` to a logger (default: root).

    Idempotent: adding the filter twice is harmless — the second
    instance has the same name and is detected on the existing
    handlers' filter lists. Tests and the FastAPI lifespan call this.
    """
    target = logger if logger is not None else logging.getLogger()
    # Idempotency: skip if already attached.
    for f in target.filters:
        if isinstance(f, YardProPIIFilter):
            return f
    instance = YardProPIIFilter()
    target.addFilter(instance)
    return instance


def detach_log_filter(logger: Optional[logging.Logger] = None) -> None:
    """Remove :class:`YardProPIIFilter` from the logger if attached."""
    target = logger if logger is not None else logging.getLogger()
    for f in list(target.filters):
        if isinstance(f, YardProPIIFilter):
            target.removeFilter(f)


__all__ = [
    "YardProPIIFilter",
    "attach_log_filter",
    "detach_log_filter",
    "scrub_text",
]
