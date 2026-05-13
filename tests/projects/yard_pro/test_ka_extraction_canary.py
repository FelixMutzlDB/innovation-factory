"""Unit tests for the KA-extraction canary script.

The script itself runs against a live KA endpoint; these tests cover the
pure-function harness (response-shape parsing + leak detection) so the
cron job doesn't silently break on a KA response-format change.

Plan §8 RT-008 / "AI security — KA extraction" row: nightly canary
detects verbatim corpus extraction via prompt-injection-shaped probes.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load():
    """Import the script as a module without executing main()."""
    here = Path(__file__).resolve().parents[3] / "scripts" / "yard_pro" / "canary_ka_extraction.py"
    spec = importlib.util.spec_from_file_location("canary_ka_extraction", here)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # @dataclass looks itself up in sys.modules during class evaluation.
    # Register the module BEFORE exec_module so the lookup resolves.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestResponseShapeParsing:
    """Cover both the kbqa_agent shape (output[].content[].text) and a
    plain ChatCompletion fallback. The live yard-pro KA returned the
    former during 2026-05-13 deploy verification."""

    def test_extracts_text_from_kbqa_agent_shape(self):
        mod = _load()
        resp = {
            "model": "kbqa_agent",
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": "May is the busiest month in the Stuttgart garden."}
                    ],
                }
            ],
            "custom_outputs": {"sources_used": True},
        }
        assert mod._extract_assistant_text(resp) == "May is the busiest month in the Stuttgart garden."

    def test_extracts_text_from_chat_completion_fallback(self):
        mod = _load()
        resp = {"choices": [{"message": {"role": "assistant", "content": "Apple scab — Venturia inaequalis"}}]}
        assert mod._extract_assistant_text(resp) == "Apple scab — Venturia inaequalis"

    def test_empty_response_returns_empty_string(self):
        mod = _load()
        assert mod._extract_assistant_text({}) == ""
        assert mod._extract_assistant_text("") == ""
        assert mod._extract_assistant_text(None) == ""

    def test_ignores_user_role_outputs(self):
        mod = _load()
        resp = {
            "output": [
                {"role": "user", "content": [{"type": "output_text", "text": "echoed user input"}]},
                {"role": "assistant", "content": [{"type": "output_text", "text": "real answer"}]},
            ]
        }
        assert mod._extract_assistant_text(resp) == "real answer"


class TestProbeManifest:
    """The seed manifest must cover every ka_docs/ subdirectory and stay
    non-empty. A future contributor who deletes a subdir without dropping
    the matching probe should be flagged by this test."""

    def test_manifest_non_empty(self):
        mod = _load()
        assert len(mod.PROBES) >= 4

    def test_every_subdir_has_at_least_one_probe(self):
        mod = _load()
        subdirs = {p.expected_subdir for p in mod.PROBES} - {"*"}
        for required in ("plant_care", "diagnostic_playbooks", "regional_almanac", "consumables"):
            assert required in subdirs, f"missing canary probe for ka_docs/{required}/"

    def test_canaries_are_non_trivial_strings(self):
        mod = _load()
        for p in mod.PROBES:
            assert len(p.canary) >= 10, f"canary too short: {p.canary!r}"
            assert len(p.prompt) >= 20, f"prompt too short: {p.prompt!r}"
