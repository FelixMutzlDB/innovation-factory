"""Regression: torch + open_clip must not import at module-load time.

C4 moved ``torch`` and ``open-clip-torch`` into the
``image-recognition`` optional extra so every non-HB deploy (and every
test run that doesn't exercise CLIP) starts faster and installs ~900 MB
less. This test confirms:

  1. Importing ``image_similarity_service`` works without the extra —
     the heavy deps are not pulled in at import time.
  2. Calling :func:`compute_embedding` without the extra raises a
     clear RuntimeError pointing the user at ``uv sync --extra
     image-recognition``, not a bare ModuleNotFoundError.
  3. :func:`find_similar_images` works without the extra (it only
     needs the Databricks SDK, not torch).

If the test env happens to have torch installed (e.g. because someone
ran ``uv sync --extra image-recognition``), checks (1) and (3) still
pass and (2) is skipped — we can't simulate "extra not installed" in a
worker that already imported torch, and faking it would be more
brittle than useful.
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
from unittest.mock import MagicMock

import pytest


MODULE_PATH = (
    "innovation_factory.backend.projects.hb_product_center.services"
    ".image_similarity_service"
)


def _torch_installed() -> bool:
    # Use find_spec rather than ``import torch`` so static type-checkers
    # don't flag this file when the optional extra isn't installed.
    return importlib.util.find_spec("torch") is not None


def test_module_imports_without_torch():
    """importlib the service module and confirm it loads regardless of
    whether torch is present."""
    mod = importlib.import_module(MODULE_PATH)
    assert hasattr(mod, "compute_embedding")
    assert hasattr(mod, "find_similar_images")
    assert hasattr(mod, "_load_clip_deps")


def test_torch_not_a_module_level_import():
    """The service must not trigger a top-level ``import torch``.

    We check by reading the source — lightweight, reliable, and doesn't
    depend on whether torch is already cached in sys.modules from some
    other import earlier in the test run.
    """
    import pathlib

    src = pathlib.Path(
        __file__
    ).parents[2] / "src/innovation_factory/backend/projects/hb_product_center/services/image_similarity_service.py"
    text = src.read_text()
    # Module-level imports appear before any function or class def.
    # Grab the import block (everything before the first `def ` / `class `).
    header_end = min(
        (text.find(marker) for marker in ("\ndef ", "\nclass ") if marker in text),
        default=len(text),
    )
    header = text[:header_end]

    assert "import torch" not in header, (
        "torch must be imported lazily, not at module level"
    )
    assert "import open_clip" not in header, (
        "open_clip must be imported lazily, not at module level"
    )


@pytest.mark.skipif(
    _torch_installed(),
    reason="torch already installed in this env — can't simulate missing extra",
)
def test_compute_embedding_raises_helpful_error_when_extra_missing():
    """Without the ``image-recognition`` extra, calling compute_embedding
    must raise RuntimeError with install instructions, not a naked
    ModuleNotFoundError."""
    mod = importlib.import_module(MODULE_PATH)
    with pytest.raises(RuntimeError) as excinfo:
        mod.compute_embedding(b"fake image bytes")
    msg = str(excinfo.value)
    assert "image-recognition" in msg
    assert "uv sync" in msg or "extra" in msg


def test_find_similar_images_does_not_need_torch():
    """The VS-query path must not require torch — it only talks to the
    Databricks Vector Search API via the SDK. Works on any deploy
    flavour."""
    mod = importlib.import_module(MODULE_PATH)

    class _MockApiClient:
        def do(self, method, path, body=None, **_kw):
            assert method == "POST"
            assert "vector-search" in path
            return {"result": {"data_array": [[1, "s3://x", "img.jpg", "suits", 0.9]]}}

    ws = MagicMock()
    ws.api_client = _MockApiClient()
    results = mod.find_similar_images(ws, query_embedding=[0.1] * 512, top_k=5)
    assert len(results) == 1
    assert results[0] == {
        "id": 1,
        "image_uri": "s3://x",
        "file_name": "img.jpg",
        "category": "suits",
        "score": 0.9,
    }
