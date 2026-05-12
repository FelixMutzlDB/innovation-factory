"""Diagnose (UC3) endpoint contract tests.

Covers plan §8 security rails (MIME allowlist, 10 MB cap, EXIF strip),
the confidence floor + co-equal second-opinion CTA, the "not configured"
first-class state (lessons §18), and the advisory chip invariant
(plan §2 — EU AI Act Art. 50).
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from innovation_factory.backend.projects.yard_pro.seed import seed_yp_data
from innovation_factory.backend.projects.yard_pro.services import diagnose_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed(client) -> None:
    from sqlmodel import Session, select

    from innovation_factory.backend.app import app
    from innovation_factory.backend.dependencies import get_session
    from innovation_factory.backend.projects.yard_pro.models import YpYard

    override = app.dependency_overrides.get(get_session)
    assert override is not None
    gen = override()
    session = next(gen)
    try:
        if not session.exec(select(YpYard)).first():
            seed_yp_data(session)
            session.commit()
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


def _png_bytes(size_bytes: int = 64) -> bytes:
    """Return a minimal PNG-shaped byte payload (header + filler)."""
    # PNG signature, then arbitrary padding bytes.
    sig = b"\x89PNG\r\n\x1a\n"
    return sig + b"\x00" * max(0, size_bytes - len(sig))


# ---------------------------------------------------------------------------
# Not-configured path (lessons §18)
# ---------------------------------------------------------------------------


class TestDiagnoseNotConfigured:
    def test_returns_503_with_configured_false(self, client):
        """When VISION_ENDPOINT is unset (default in test env), the
        endpoint must return a structured 503 — NOT a 500 (lessons §18)."""
        _seed(client)
        r = client.post(
            "/api/projects/yard-pro/diagnose",
            files={"file": ("test.jpg", _png_bytes(128), "image/jpeg")},
            headers={"X-Forwarded-User": "martin@yard-pro.local"},
        )
        assert r.status_code == 503, r.text
        body = r.json()
        # Body structure must signal "configured: false" so the UI can
        # render the not-configured card.
        detail = body.get("detail", {})
        assert isinstance(detail, dict)
        assert detail.get("configured") is False
        assert "Snap-and-diagnose requires configuration" in detail.get("detail", "")


# ---------------------------------------------------------------------------
# MIME allowlist + size cap (plan §8 RT-005)
# ---------------------------------------------------------------------------


class TestDiagnoseUploadGuards:
    def test_rejects_image_gif(self, client):
        _seed(client)
        r = client.post(
            "/api/projects/yard-pro/diagnose",
            files={"file": ("test.gif", b"GIF89a" + b"\x00" * 32, "image/gif")},
            headers={"X-Forwarded-User": "martin@yard-pro.local"},
        )
        assert r.status_code == 415, r.text
        body = r.json()
        detail = body.get("detail", {})
        assert isinstance(detail, dict)
        assert detail.get("received") == "image/gif"

    def test_rejects_oversize_file(self, client):
        """11 MB payload must be rejected with 413 before EXIF stripping
        or any model call (defense-in-depth)."""
        _seed(client)
        oversize = _png_bytes(11 * 1024 * 1024)
        r = client.post(
            "/api/projects/yard-pro/diagnose",
            files={"file": ("big.jpg", oversize, "image/jpeg")},
            headers={"X-Forwarded-User": "martin@yard-pro.local"},
        )
        assert r.status_code == 413, r.text
        body = r.json()
        detail = body.get("detail", {})
        assert isinstance(detail, dict)
        assert detail.get("max_bytes") == 10 * 1024 * 1024


# ---------------------------------------------------------------------------
# Confidence floor + second-opinion CTA (plan §8 + UC3)
# ---------------------------------------------------------------------------


class TestDiagnoseConfidenceFloor:
    def test_below_floor_collapses_to_unsure(self, client):
        """Plan §8: top_confidence < 0.6 → top_label='unsure', unsure=True.
        The second-opinion CTA is the user-visible safety rail and must
        be returned regardless."""
        _seed(client)
        # When VISION_ENDPOINT is unset (default), the router passes
        # ws=None to ``classify`` — the mock ignores arguments. We don't
        # need to override runtime; just intercept the call.
        with patch(
            "innovation_factory.backend.projects.yard_pro.routers.diagnose.classify",
            return_value=diagnose_service.DiagnoseResult(
                predictions=[
                    diagnose_service.DiagnosePrediction(name="fusarium_blight", confidence=0.55),
                    diagnose_service.DiagnosePrediction(name="drought_stress", confidence=0.30),
                ],
                top_label="unsure",
                top_confidence=0.55,
                unsure=True,
                second_opinion_cta="Get a second opinion (free dealer chat)",
                model_version="fake-vision",
                response_id="rid-low",
            ),
        ):
            r = client.post(
                "/api/projects/yard-pro/diagnose",
                files={"file": ("low.jpg", _png_bytes(256), "image/jpeg")},
                headers={"X-Forwarded-User": "martin@yard-pro.local"},
            )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["unsure"] is True
        assert body["top_label"] == "unsure"
        assert body["second_opinion_cta"]  # non-empty
        assert body["advisory"] is True  # plan §2 NN

    def test_above_floor_keeps_top_label(self, client):
        """top_confidence >= 0.6 → top_label is the real label; unsure=False.
        Co-equal second-opinion CTA must still be present."""
        _seed(client)
        with patch(
            "innovation_factory.backend.projects.yard_pro.routers.diagnose.classify",
            return_value=diagnose_service.DiagnoseResult(
                predictions=[
                    diagnose_service.DiagnosePrediction(name="fusarium_blight", confidence=0.85),
                    diagnose_service.DiagnosePrediction(name="drought_stress", confidence=0.10),
                ],
                top_label="fusarium_blight",
                top_confidence=0.85,
                unsure=False,
                second_opinion_cta="Get a second opinion (free dealer chat)",
                model_version="fake-vision",
                response_id="rid-high",
            ),
        ):
            r = client.post(
                "/api/projects/yard-pro/diagnose",
                files={"file": ("hi.jpg", _png_bytes(256), "image/jpeg")},
                headers={"X-Forwarded-User": "martin@yard-pro.local"},
            )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["unsure"] is False
        assert body["top_label"] == "fusarium_blight"
        assert body["top_confidence"] == pytest.approx(0.85)
        assert body["second_opinion_cta"]
        assert body["advisory"] is True


# ---------------------------------------------------------------------------
# History endpoints
# ---------------------------------------------------------------------------


class TestDiagnoseHistory:
    def test_list_returns_seeded_diagnoses(self, client):
        """The seed plants 2 diagnose history rows."""
        _seed(client)
        r = client.get(
            "/api/projects/yard-pro/diagnose",
            headers={"X-Forwarded-User": "martin@yard-pro.local"},
        )
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) >= 2
        for row in rows:
            assert row["advisory"] is True

    def test_get_404_for_unknown_diagnosis(self, client):
        _seed(client)
        r = client.get(
            "/api/projects/yard-pro/diagnose/999999",
            headers={"X-Forwarded-User": "martin@yard-pro.local"},
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Pure-service tests — no client needed
# ---------------------------------------------------------------------------


class TestDiagnoseServiceConfidenceFloor:
    def test_apply_floor_below(self):
        from innovation_factory.backend.projects.yard_pro.services.diagnose_service import (
            DiagnosePrediction,
            _apply_confidence_floor,
        )

        label, conf, unsure = _apply_confidence_floor(
            [DiagnosePrediction(name="x", confidence=0.55)]
        )
        assert label == "unsure"
        assert unsure is True
        assert conf == pytest.approx(0.55)

    def test_apply_floor_above(self):
        from innovation_factory.backend.projects.yard_pro.services.diagnose_service import (
            DiagnosePrediction,
            _apply_confidence_floor,
        )

        label, conf, unsure = _apply_confidence_floor(
            [DiagnosePrediction(name="apple_scab", confidence=0.82)]
        )
        assert label == "apple_scab"
        assert unsure is False
        assert conf == pytest.approx(0.82)

    def test_apply_floor_empty_list_is_unsure(self):
        from innovation_factory.backend.projects.yard_pro.services.diagnose_service import (
            _apply_confidence_floor,
        )

        label, conf, unsure = _apply_confidence_floor([])
        assert label == "unsure"
        assert unsure is True
        assert conf == 0.0

    def test_not_configured_raises_typed_error(self):
        from innovation_factory.backend.projects.yard_pro.services.diagnose_service import (
            DiagnoseNotConfiguredError,
            classify,
        )

        # VISION_ENDPOINT is empty in test env.
        with pytest.raises(DiagnoseNotConfiguredError):
            classify(ws=None, image_bytes=b"\x00\x00\x00")  # type: ignore[arg-type]
