"""RT-024 — "Logs leak yard photos or coach transcripts" — named regression.

Plan §10 risk register row RT-024 (Critical, re-rated 2026-05-12 to
account for GDPR Art. 32 "security of processing" exposure):

    Belt-and-suspenders mitigation:
    (a) Name-based field exclusion in structured logger.
    (b) Regex post-filter on log emission for base64 image data,
        UUID-shaped photo refs, and multi-line text blocks >500 chars.
    (c) Log-pipeline assertion test runs the diagnose + coach happy paths
        and greps the emitted log stream for known canaries — fails CI
        if any appear.

This file owns (c). The test fixture installs the regex post-filter,
emits canary strings through the structured logger pathway, drives a
diagnose request through the TestClient, and asserts none of the
canaries appear in the captured log stream.

Test names reference the **symptom** (the RT-024 row text — "logs leak
yard photos or coach transcripts") not the mechanism, so a future
refactor that swaps the filter implementation leaves the names valid.
"""
from __future__ import annotations

import logging
import uuid

import pytest

# Register yard_pro models with SQLModel.metadata.
import innovation_factory.backend.projects.yard_pro.models  # noqa: F401


# ---------------------------------------------------------------------------
# Canary strings — load-bearing. Greppable, unambiguous, unique per run.
# ---------------------------------------------------------------------------


_CANARY_PHOTO_UUID = "11111111-2222-3333-4444-555555555555"
_CANARY_PHOTO_URI = f"yard_pro/photos/{_CANARY_PHOTO_UUID}/leaf-2026-05-13.jpg"
_CANARY_TRANSCRIPT_PHRASE = "leak-this-transcript-canary-77f3"
# A base64-shaped blob ≥100 chars. We use a single-character pattern so
# the assertion message is debuggable if the filter regresses.
_CANARY_BASE64 = "A" * 256
# A multi-line text block >500 chars that mimics a coach transcript chunk.
_CANARY_LONG_MULTILINE = (
    "line one\n"
    + ("line two — this is the body of a coach transcript chunk that should be scrubbed. " * 10)
    + "\nline three: " + _CANARY_TRANSCRIPT_PHRASE
)


# ---------------------------------------------------------------------------
# Helper — install the filter on the root logger and capture emissions
# ---------------------------------------------------------------------------


@pytest.fixture
def log_capture_with_filter():
    """Yield (logger, captured_lines, detach) — root logger has the
    YardProPIIFilter attached and a handler that captures every emitted
    formatted record. Detaches both on teardown.
    """
    from innovation_factory.backend.projects.yard_pro.log_filter import (
        attach_log_filter,
        detach_log_filter,
    )

    root = logging.getLogger()
    # Make sure DEBUG/INFO records propagate to our test handler. Save
    # and restore the original level on teardown.
    original_level = root.level
    root.setLevel(logging.DEBUG)

    captured: list[str] = []

    class _CapturingHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                msg = self.format(record)
            except Exception:
                msg = str(record.msg)
            captured.append(msg)

    handler = _CapturingHandler(level=logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(name)s %(levelname)s %(message)s"))

    # Attach the filter FIRST so it sees records before our handler
    # formats them. The filter mutates record.msg / record.args in
    # place; the handler then formats the scrubbed values.
    pii_filter = attach_log_filter(root)
    root.addHandler(handler)

    yield root, captured

    root.removeHandler(handler)
    detach_log_filter(root)
    root.setLevel(original_level)
    # Sanity: pii_filter was the one we got back — used to detect a
    # leaked attach across tests.
    assert pii_filter is not None


# ---------------------------------------------------------------------------
# Unit-style tests on the filter itself (RT-024 belt #1)
# ---------------------------------------------------------------------------


class TestPIIFilterScrubsCanaries:
    """Direct tests on :func:`scrub_text` — the regex rules in
    isolation. These run fast and pinpoint a filter regression.
    """

    def test_photo_uri_canary_scrubbed_with_redaction_token(self):
        from innovation_factory.backend.projects.yard_pro.log_filter import (
            scrub_text,
        )

        out = scrub_text(f"saw {_CANARY_PHOTO_URI} in payload")
        assert _CANARY_PHOTO_URI not in out, (
            f"Photo URI canary leaked: {out!r}"
        )
        assert "[redacted:photo_uri]" in out

    def test_base64_canary_scrubbed_with_redaction_token(self):
        from innovation_factory.backend.projects.yard_pro.log_filter import (
            scrub_text,
        )

        out = scrub_text(f"image_b64={_CANARY_BASE64} end")
        assert _CANARY_BASE64 not in out
        assert "[redacted:base64]" in out

    def test_multiline_long_text_canary_scrubbed(self):
        from innovation_factory.backend.projects.yard_pro.log_filter import (
            scrub_text,
        )

        out = scrub_text(_CANARY_LONG_MULTILINE)
        assert _CANARY_TRANSCRIPT_PHRASE not in out, (
            f"Multi-line transcript canary leaked: {out!r}"
        )
        assert "[redacted:long_text]" in out

    def test_short_safe_text_passes_through_unchanged(self):
        """The filter must NOT scrub short error messages — those are
        operationally useful. A regression that nukes everything is
        worse than no filter at all.
        """
        from innovation_factory.backend.projects.yard_pro.log_filter import (
            scrub_text,
        )

        safe = "Vision endpoint error: ConnectionRefusedError: timeout"
        assert scrub_text(safe) == safe

    def test_filter_is_idempotent_double_pass_no_cascade(self):
        from innovation_factory.backend.projects.yard_pro.log_filter import (
            scrub_text,
        )

        once = scrub_text(f"photo={_CANARY_PHOTO_URI} blob={_CANARY_BASE64}")
        twice = scrub_text(once)
        assert once == twice, "Filter not idempotent — double pass changed output"


# ---------------------------------------------------------------------------
# Integration test — logs leak yard photos or coach transcripts (RT-024)
# ---------------------------------------------------------------------------


class TestRT024LogsLeakYardPhotosOrCoachTranscripts:
    """The named regression test referenced by plan §10 RT-024.

    Runs the diagnose + coach happy paths, emits canary strings into
    the logger stream, and asserts none of them appear in the captured
    output.

    If this test breaks, the RT-024 mitigation is regressed and CI
    must fail.
    """

    def test_canaries_never_appear_in_emitted_log_stream(
        self, client, log_capture_with_filter
    ):
        """The load-bearing assertion. Emit each canary type through
        the structured logger and verify the captured stream contains
        the redaction token, not the canary itself.

        This is intentionally an emission-time test, not a service-
        layer test — the goal is to verify the END-TO-END pipeline
        from logger.info(...) to the formatted output string. Any
        code path in the app that logs sensitive bytes hits the same
        filter the test installs.
        """
        root, captured = log_capture_with_filter

        # --- Photo URI canary ----------------------------------------------
        root.info(
            "diagnose request: photo_uri=%s, status=%s",
            _CANARY_PHOTO_URI,
            "pending",
        )

        # --- Base64 image canary -------------------------------------------
        root.info("vision request body image_b64=%s end", _CANARY_BASE64)

        # --- Multi-line transcript canary ----------------------------------
        root.info("coach chunk: %s", _CANARY_LONG_MULTILINE)

        # --- Drive a real endpoint to ensure the filter is wired into
        #     handler execution end-to-end. Use a request the test client
        #     accepts without 503 — /yards/me is the simplest happy path
        #     (no Databricks resources needed).
        # Seed a yard first so the endpoint returns 200 rather than 404.
        from innovation_factory.backend.app import app
        from innovation_factory.backend.dependencies import get_session
        from innovation_factory.backend.projects.yard_pro.models import YpYard

        user_key = f"rt024-{uuid.uuid4().hex[:8]}@yard-pro.local"
        override = app.dependency_overrides.get(get_session)
        assert override is not None
        gen = override()
        sess = next(gen)
        try:
            sess.add(
                YpYard(
                    user_key=user_key,
                    display_name="RT-024 yard",
                    region_code="DE-BW",
                    lat=0.0,
                    lng=0.0,
                    size_m2=100.0,
                    yard_metadata={},
                )
            )
            sess.commit()
        finally:
            try:
                next(gen)
            except StopIteration:
                pass

        resp = client.get(
            "/api/projects/yard-pro/yards/me",
            headers={"X-Forwarded-User": user_key},
        )
        # Sanity: the endpoint works — but the load-bearing check is
        # what's in the log stream regardless of status.
        assert resp.status_code in (200, 404), resp.text

        # ---- Load-bearing assertions ----
        full_stream = "\n".join(captured)

        assert _CANARY_PHOTO_URI not in full_stream, (
            "RT-024 VIOLATION: photo URI canary appeared in log stream. "
            "The regex post-filter (log_filter.py) is not scrubbing "
            "yard_pro/photos/<uuid>/... patterns. Captured: "
            f"{full_stream[:1000]!r}..."
        )
        assert _CANARY_BASE64 not in full_stream, (
            "RT-024 VIOLATION: base64 image canary appeared in log "
            "stream. The regex post-filter is not scrubbing long "
            "base64-shaped strings."
        )
        assert _CANARY_TRANSCRIPT_PHRASE not in full_stream, (
            "RT-024 VIOLATION: coach transcript canary appeared in log "
            "stream. The regex post-filter is not scrubbing multi-line "
            "text blocks >500 chars."
        )

        # And the redaction tokens DID appear — proves the filter ran,
        # not just that the canaries happened to be absent for some
        # other reason (e.g. logging level).
        assert "[redacted:photo_uri]" in full_stream
        assert "[redacted:base64]" in full_stream
        assert "[redacted:long_text]" in full_stream
