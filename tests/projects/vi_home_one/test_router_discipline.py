"""Router-discipline regression test for vi_home_one.

Contract: every @router.(get|post|patch|delete|put) decorator under
src/innovation_factory/backend/projects/vi_home_one/ MUST declare both:
  (1) operation_id=
  (2) one of response_model / response_class / responses
      OR be additionally decorated with @streaming_endpoint

Any violation indicates a route that will produce a broken TypeScript
client (api.ts auto-generation requires operation_id, and response_model
drives the return type).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
VI_HOME_ONE_DIR = (
    REPO_ROOT
    / "src"
    / "innovation_factory"
    / "backend"
    / "projects"
    / "vi_home_one"
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
    for py_path in VI_HOME_ONE_DIR.rglob("*.py"):
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


def test_vi_home_one_routes_have_operation_id_and_response_declaration():
    """Every vi_home_one route must declare operation_id + a response shape."""
    violations = _collect_violations()
    if violations:
        lines = [
            f"  {path}:{lineno}  @{method} {fn}  missing: {', '.join(sorted(missing))}"
            for path, lineno, fn, method, missing in violations
        ]
        pytest.fail(
            f"\nFound {len(violations)} vi_home_one route(s) violating "
            "router discipline (CLAUDE.md: 'All API routes need response_model "
            "and operation_id'):\n" + "\n".join(lines)
        )


def test_vi_home_one_router_dir_exists():
    """Sanity: the vi_home_one routers directory must exist."""
    assert (VI_HOME_ONE_DIR / "routers").is_dir()
