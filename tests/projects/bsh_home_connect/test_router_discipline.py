"""Router-discipline regression test for bsh_home_connect.

Contract: every ``@router.(get|post|patch|delete|put)`` decorator under
``src/innovation_factory/backend/projects/bsh_home_connect/`` MUST declare
both (1) ``operation_id=`` and (2) one of ``response_model`` /
``response_class`` / ``responses``, OR be decorated with
``@streaming_endpoint``.

The ``bsh_home_connect`` project started before the yard-pro greenfield
push, so a small set of routes may carry known debt that is tracked in
KNOWN_DEBT. The set should trend toward empty over time; never grow it
without a dated TODO comment.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
BSH_DIR = (
    REPO_ROOT
    / "src"
    / "innovation_factory"
    / "backend"
    / "projects"
    / "bsh_home_connect"
)
ROUTE_METHODS = {"get", "post", "patch", "delete", "put"}
RESPONSE_KWARGS = {"response_model", "response_class", "responses"}
STREAMING_DECORATOR = "streaming_endpoint"

# Existing violations that pre-date this test run.
# Each entry is (relative_path_as_posix, function_name).
# Never add new entries without a dated TODO comment.
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
    for py_path in BSH_DIR.rglob("*.py"):
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
                        (rel_path, dec.lineno, node.name, method or "?", missing)
                    )
    return violations


def test_bsh_routes_have_operation_id_and_response_declaration():
    """Every bsh_home_connect route must declare operation_id + a response shape."""
    all_violations = _collect_violations()
    new_violations = [
        v for v in all_violations
        if (v[0].as_posix(), v[2]) not in KNOWN_DEBT
    ]
    # Check that grandfathered debt entries actually still violate
    cleared = [
        e for e in KNOWN_DEBT
        if not any(v[0].as_posix() == e[0] and v[2] == e[1] for v in all_violations)
    ]
    if cleared:
        cleared_lines = [f"  ({path!r}, {fn!r})" for path, fn in sorted(cleared)]
        pytest.fail(
            f"\n{len(cleared)} KNOWN_DEBT entry(ies) no longer violate the contract — "
            "remove from KNOWN_DEBT in "
            "tests/projects/bsh_home_connect/test_router_discipline.py:\n"
            + "\n".join(cleared_lines)
        )
    if new_violations:
        lines = [
            f"  {path}:{lineno}  @{router_method} {fn}  missing: {', '.join(sorted(missing))}"
            for path, lineno, fn, router_method, missing in new_violations
        ]
        pytest.fail(
            f"\nFound {len(new_violations)} bsh_home_connect route(s) violating "
            "router-discipline (CLAUDE.md). Either fix or add to KNOWN_DEBT "
            "with a dated TODO:\n" + "\n".join(lines)
        )


def test_bsh_operation_ids_use_bsh_prefix():
    """All bsh_home_connect operation_ids must start with 'bsh_' to avoid
    OpenAPI schema collisions with other accelerators (CLAUDE.md §13).
    """
    from innovation_factory.backend.projects.bsh_home_connect.router import (
        router as bsh_router,
    )
    from fastapi.routing import APIRoute

    routes = [r for r in bsh_router.routes if isinstance(r, APIRoute)]
    # Gather all operation_ids from sub-routers by walking included routes
    all_routes: list[APIRoute] = list(routes)
    for r in bsh_router.routes:
        if hasattr(r, "routes"):
            all_routes.extend(
                rr for rr in getattr(r, "routes") if isinstance(rr, APIRoute)
            )

    violations = [
        r for r in all_routes
        if r.operation_id and not r.operation_id.startswith("bsh_")
    ]
    if violations:
        ids = [r.operation_id for r in violations]
        pytest.fail(
            f"BSH operation_ids must start with 'bsh_'. Found bad IDs: {ids}"
        )
