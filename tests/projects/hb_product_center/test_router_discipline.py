"""Router-discipline regression test for hb_product_center.

Every ``@router.(get|post|patch|delete|put)`` decorator under
``src/innovation_factory/backend/projects/hb_product_center/`` MUST declare:
  1. ``operation_id=``
  2. One of ``response_model`` / ``response_class`` / ``responses``
     OR be additionally decorated with ``@streaming_endpoint``.

This mirrors the pattern in tests/projects/yard_pro/test_router_discipline.py.
Any new violation should be fixed in source, not added to KNOWN_DEBT here.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
HB_DIR = (
    REPO_ROOT
    / "src"
    / "innovation_factory"
    / "backend"
    / "projects"
    / "hb_product_center"
)
ROUTE_METHODS = {"get", "post", "patch", "delete", "put"}
RESPONSE_KWARGS = {"response_model", "response_class", "responses"}
STREAMING_DECORATOR = "streaming_endpoint"


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
    for py_path in HB_DIR.rglob("*.py"):
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


def test_hb_routes_have_operation_id_and_response_declaration():
    """Every hb_product_center route must declare operation_id + a response shape."""
    violations = _collect_violations()
    if violations:
        lines = [
            f"  {path}:{lineno}  @{m} {fn}  missing: {', '.join(sorted(miss))}"
            for path, lineno, fn, m, miss in violations
        ]
        pytest.fail(
            f"\nFound {len(violations)} hb_product_center route(s) violating "
            "router-discipline (CLAUDE.md §API routes):\n" + "\n".join(lines)
        )


def test_hb_dir_has_router_files():
    """Sanity: the routers/ subdirectory must contain at least 4 .py files."""
    routers_dir = HB_DIR / "routers"
    py_files = [f for f in routers_dir.glob("*.py") if f.name != "__init__.py"]
    assert len(py_files) >= 4, (
        f"expected ≥4 router files in {routers_dir}, found {len(py_files)}"
    )
