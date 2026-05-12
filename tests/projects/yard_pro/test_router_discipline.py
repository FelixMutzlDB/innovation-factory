"""Router-discipline regression test for yard-pro.

Mirrors ``tests/common/test_router_discipline.py`` but scoped to the
yard-pro project tree. Per plan §7 (lessons §34 row), yard-pro lands
greenfield with ``KNOWN_DEBT = set()`` — there is no debt to grandfather
in, and the allowlist stays empty by policy.

Contract: every ``@router.(get|post|patch|delete|put)`` decorator under
``src/innovation_factory/backend/projects/yard_pro/`` MUST declare both
(1) ``operation_id=`` and (2) one of ``response_model`` /
``response_class`` / ``responses``, OR be additionally decorated with
``@streaming_endpoint``.

Why a separate test, not just relying on the common one: the common
test is global and catches *new* violations across the whole backend.
A yard-pro-scoped test fails specifically for yard-pro changes, which
is a clearer signal during the P0 fan-out (B1/B2 routers landing in
parallel).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
YARD_PRO_DIR = (
    REPO_ROOT
    / "src"
    / "innovation_factory"
    / "backend"
    / "projects"
    / "yard_pro"
)
ROUTE_METHODS = {"get", "post", "patch", "delete", "put"}
RESPONSE_KWARGS = {"response_model", "response_class", "responses"}
STREAMING_DECORATOR = "streaming_endpoint"

# Greenfield project — no debt grandfathered in. Per plan §7 lessons §34
# row, this set stays empty by policy. If a new route lands without
# operation_id + response_model, fix it; do NOT add to this set.
KNOWN_DEBT: set[tuple[str, str]] = set()


def _is_router_decorator(node: ast.expr) -> tuple[bool, str | None]:
    if not isinstance(node, ast.Call):
        return False, None
    func = node.func
    if not isinstance(func, ast.Attribute):
        return False, None
    if func.attr not in ROUTE_METHODS:
        return False, None
    if not isinstance(func.value, ast.Name):
        return False, None
    if not func.value.id.endswith("router"):
        return False, None
    return True, func.attr


def _decorator_names(decorator_list: list[ast.expr]) -> set[str]:
    names: set[str] = set()
    for dec in decorator_list:
        if isinstance(dec, ast.Name):
            names.add(dec.id)
        elif isinstance(dec, ast.Attribute):
            names.add(dec.attr)
    return names


def _missing_kwargs(provided: set[str], extra_decorators: set[str]) -> set[str]:
    missing: set[str] = set()
    if "operation_id" not in provided:
        missing.add("operation_id")
    if STREAMING_DECORATOR in extra_decorators:
        return missing
    if not (provided & RESPONSE_KWARGS):
        missing.add("response_model|response_class|responses (or @streaming_endpoint)")
    return missing


def _collect_violations() -> list[tuple[Path, int, str, str, set[str]]]:
    violations: list[tuple[Path, int, str, str, set[str]]] = []
    for py_path in YARD_PRO_DIR.rglob("*.py"):
        if "__pycache__" in py_path.parts:
            continue
        try:
            tree = ast.parse(py_path.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            extra_decorators = _decorator_names(node.decorator_list)
            for dec in node.decorator_list:
                is_route, method = _is_router_decorator(dec)
                if not is_route:
                    continue
                assert isinstance(dec, ast.Call)
                provided = {kw.arg for kw in dec.keywords if kw.arg}
                missing = _missing_kwargs(provided, extra_decorators)
                if missing:
                    rel_path = py_path.relative_to(REPO_ROOT)
                    violations.append(
                        (
                            rel_path,
                            dec.lineno,
                            node.name,
                            method or "?",
                            missing,
                        )
                    )
    return violations


def test_yard_pro_routes_have_operation_id_and_response_declaration():
    """Every yard-pro route must declare operation_id + a response shape."""
    all_violations = _collect_violations()
    new_violations = [
        v for v in all_violations if (v[0].as_posix(), v[2]) not in KNOWN_DEBT
    ]
    cleared = [
        e
        for e in KNOWN_DEBT
        if not any(v[0].as_posix() == e[0] and v[2] == e[1] for v in all_violations)
    ]
    if cleared:
        cleared_lines = [f"  ({path!r}, {fn!r})" for path, fn in sorted(cleared)]
        pytest.fail(
            f"\n{len(cleared)} KNOWN_DEBT entry(ies) no longer violate the contract — "
            "remove from KNOWN_DEBT in "
            "tests/projects/yard_pro/test_router_discipline.py:\n"
            + "\n".join(cleared_lines)
        )
    if new_violations:
        lines = [
            f"  {path}:{lineno}  @{router_method} {fn}  missing: {', '.join(sorted(missing))}"
            for path, lineno, fn, router_method, missing in new_violations
        ]
        pytest.fail(
            f"\nFound {len(new_violations)} NEW yard-pro route(s) violating "
            "router-discipline (lessons §13). Either fix or add to KNOWN_DEBT "
            "with a TODO:\n" + "\n".join(lines)
        )


def test_yard_pro_known_debt_is_empty():
    """Plan §7 lessons §34 row: yard-pro is greenfield; the allowlist
    stays empty by policy. This is a separate assertion from the
    violation check so the failure message names the policy, not the
    individual debt entry."""
    assert KNOWN_DEBT == set(), (
        "yard-pro KNOWN_DEBT must stay empty (plan §7 lessons §34 row). "
        f"Found: {KNOWN_DEBT}"
    )
