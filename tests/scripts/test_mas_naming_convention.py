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
        """Every sub-agent name appended to ``<x>_agents`` must appear
        verbatim inside the ``instructions`` string of the next POST
        body to ``/api/2.1/supervisor-agents`` whose ``"agents"`` is
        bound to that same list.

        Uses an AST visitor (not regex) so re-ordering MAS blocks no
        longer breaks the test — the previous regex grabbed the first
        ``"instructions": (...)`` after ``<x>_agents = []``, which
        leaked the AECO block's text into HB's check when AECO was
        inserted between them in Phase 4.
        """
        import ast

        src = self._phase_7_source()
        tree = ast.parse(src)

        agents_to_names: dict[str, list[str]] = {}
        agents_to_instructions: dict[str, str] = {}

        for node in ast.walk(tree):
            # `<var>_agents.append(_build_agent("name", ...))`
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "append"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id.endswith("_agents")
                and node.args
                and isinstance(node.args[0], ast.Call)
                and isinstance(node.args[0].func, ast.Name)
                and node.args[0].func.id == "_build_agent"
                and node.args[0].args
                and isinstance(node.args[0].args[0], ast.Constant)
                and isinstance(node.args[0].args[0].value, str)
            ):
                var = node.func.value.id
                name = node.args[0].args[0].value
                agents_to_names.setdefault(var, []).append(name)

            # `_api("post", "/api/2.1/supervisor-agents", body)`
            # where body is a dict with "instructions" → str and
            # "agents" → Name reference.
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_api"
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value == "/api/2.1/supervisor-agents"
            ):
                # Body is the next sibling — find ``body`` variable
                # assigned in the enclosing scope right above.
                pass

        # Second pass: find dict literals with "instructions" + "agents"
        # → links variable name to instructions string.
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if not (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == "body"):
                continue
            if not isinstance(node.value, ast.Dict):
                continue
            keys = [k.value for k in node.value.keys if isinstance(k, ast.Constant)]
            if "instructions" not in keys or "agents" not in keys:
                continue
            kv = dict(zip(keys, node.value.values))
            agents_node = kv.get("agents")
            instr_node = kv.get("instructions")
            if not isinstance(agents_node, ast.Name):
                continue
            if instr_node is None:
                continue
            # instructions is a parenthesized string-concatenation; we
            # walk it to collect every Constant string literal value.
            instr_text = "".join(
                n.value for n in ast.walk(instr_node)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
            )
            agents_to_instructions[agents_node.id] = instr_text

        # Now assert every sub-agent name appears in its parent MAS's
        # instructions.
        assert agents_to_names, "no _build_agent calls found in any *_agents list"
        assert agents_to_instructions, (
            "no MAS body dict with `agents` + `instructions` keys found"
        )
        for var, names in agents_to_names.items():
            assert var in agents_to_instructions, (
                f"`{var}` is appended to in phase 7 but never referenced "
                f"as `agents` in a supervisor-agents POST body."
            )
            instructions = agents_to_instructions[var]
            for name in names:
                assert name in instructions, (
                    f"Sub-agent {name!r} missing from instructions for "
                    f"{var!r}. Routing must reference the machine name."
                )
