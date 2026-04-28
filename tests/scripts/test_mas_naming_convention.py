"""Regression: MAS sub-agent names follow snake_case, display_name ends
with "Supervisor", and MAS instructions reference every sub-agent by its
exact machine name.

D3 introduced the convention to stop the MAS framework from emitting
tool calls with inconsistent names (``genie_data_explorer``,
``transfer_to_issue_resolution_specialist``, ``query_agent``,
``call_agent_tool``, ``product_identifier_agent``,
``query_agent_quality_auth_analyst``) which made the Agent Bricks
dashboard confusing and the routing non-deterministic.

This test reads the phase-7 POST body that ``deploy_agents_fevm.py``
would send and enforces the naming contract. It doesn't hit the live
workspace — the contract is what matters, not the runtime.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys


SNAKE_CASE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


def _load_script():
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "deploy_agents_fevm.py"
    spec = importlib.util.spec_from_file_location("deploy_agents_fevm_d3", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["deploy_agents_fevm_d3"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestMasNamingConvention:
    """Read the phase-7 source and assert the naming contract without
    executing any network calls."""

    def _phase_7_source(self) -> str:
        repo_root = pathlib.Path(__file__).resolve().parents[2]
        return (repo_root / "scripts" / "deploy_agents_fevm.py").read_text(encoding="utf-8")

    def test_all_sub_agent_names_are_snake_case(self):
        src = self._phase_7_source()
        # Every call that constructs a sub-agent uses _build_agent(name, ...).
        # The first positional arg is a string literal in the source.
        matches = re.findall(
            r"_build_agent\(\s*\n?\s*[\"']([^\"']+)[\"']",
            src,
        )
        assert matches, "no _build_agent calls found — phase 7 source changed?"
        for name in matches:
            assert SNAKE_CASE_NAME.match(name), (
                f"Sub-agent name {name!r} must be snake_case_lowercase. "
                "See scripts/deploy_agents_fevm.py phase 7."
            )

    def test_display_names_end_with_supervisor(self):
        """Each MAS display_name is assigned to a local variable of the
        form `<slug>_display = "..."`. Enforce the Supervisor suffix on
        every such variable."""
        src = self._phase_7_source()
        displays = re.findall(
            r'(\w+_display)\s*=\s*"([^"]+)"',
            src,
        )
        assert displays, (
            "no `<slug>_display = \"...\"` assignments found — "
            "phase 7 source structure changed?"
        )
        supervisor_displays = [d for _, d in displays]
        assert len(supervisor_displays) >= 2, (
            f"expected at least 2 MAS display names, got: {displays}"
        )
        for name in supervisor_displays:
            assert name.endswith("Supervisor"), (
                f"display_name {name!r} must end with 'Supervisor' for "
                "consistency across MASes"
            )

    def test_instructions_reference_every_sub_agent_name(self):
        """Every sub-agent name that phase 7 defines must appear verbatim
        inside the `instructions` string of its parent MAS, so the LLM
        can emit a deterministic tool call. We pair each
        _build_agent("name", ...) with the nearest `"instructions": (...)`
        block above or below it and check.
        """
        src = self._phase_7_source()

        # Find the AdTech MAS block and the HB MAS block separately.
        # Each block starts with `adtech_agents = []` / `hb_agents = []`
        # and extends through its corresponding `_api("post", "/api/2.1/
        # supervisor-agents"` call.
        for var, display_token in [
            ("adtech_agents", "AdTech Intelligence Supervisor"),
            ("hb_agents", "HB Product Center Supervisor"),
            ("aeco_agents", "AECO Hub Supervisor"),
        ]:
            start = src.find(f"{var} = []")
            assert start >= 0, f"couldn't find {var} block"
            # Find the end: the next `_api("post", "/api/2.1/supervisor-agents"`
            end = src.find('"/api/2.1/supervisor-agents"', start)
            assert end >= 0, f"couldn't find POST for {var}"
            block = src[start:end + 300]

            names = re.findall(
                r"_build_agent\(\s*\n?\s*[\"']([^\"']+)[\"']",
                block,
            )
            instructions_match = re.search(
                r'"instructions"\s*:\s*\(([^)]+)\)',
                block,
                re.S,
            )
            assert instructions_match, f"no instructions block in {var}"
            instructions = instructions_match.group(1)

            for name in names:
                assert name in instructions, (
                    f"Sub-agent {name!r} missing from {display_token} "
                    f"instructions. Routing must reference the machine name."
                )
