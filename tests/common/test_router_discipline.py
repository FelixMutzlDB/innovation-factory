"""Tests for the router discipline contract: every FastAPI route declared
with `@router.(get|post|patch|delete|put)` MUST provide:
  (1) ``operation_id=`` — always required so the generated TS client uses
      our intended camelCase name, not FastAPI's auto-derived
      ``get_things__api_v1_things__get`` form.
  (2) One of ``response_model=`` / ``response_class=`` / ``responses=``,
      OR be additionally decorated with ``@streaming_endpoint`` —
      so the OpenAPI schema documents the response shape (or is explicitly
      marked as SSE). The normal case is ``response_model=ThingOut``;
      streaming endpoints stack ``@streaming_endpoint``; binary/file
      endpoints declare ``responses={200: {"content": {...}}}``.

Why this matters:
  - Missing response declaration means the OpenAPI generator silently
    emits an untyped endpoint and the TypeScript client either skips it
    or types it as ``any``. Bugs land in the frontend instead of in CI.
  - Missing (or auto-generated) ``operation_id`` means the TS client uses
    a derived name; renames silently break the frontend.

This is lessons-learned §13, promoted to CI on 2026-05-11. The
``@streaming_endpoint`` exemption was introduced with the
``services/streaming.py`` decorator in commit ``fb43b87``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "src" / "innovation_factory" / "backend"
ROUTE_METHODS = {"get", "post", "patch", "delete", "put"}
RESPONSE_KWARGS = {"response_model", "response_class", "responses"}
STREAMING_DECORATOR = "streaming_endpoint"

# Routes that pre-date this lint (2026-05-11). Each entry is
# (relative_path, function_name) — declaring a route here means it's known
# debt; the test will only fail when *new* violations land.
#
# To clear an entry: either add `@streaming_endpoint` (preferred for SSE
# chat endpoints) or `response_class=StreamingResponse` /
# `response_model=...` / `responses={...}`. Then delete the line below.
#
# Tracked as TODO.md D6 (added 2026-05-11). Cleanup target: 2026-Q3.
KNOWN_DEBT: set[tuple[str, str]] = {
    # Streaming chat endpoints predating the @streaming_endpoint decorator
    # introduced in commit fb43b87 (AECO Hub uses it; these don't yet).
    ("src/innovation_factory/backend/routers/ideas.py", "send_idea_message"),
    ("src/innovation_factory/backend/projects/hb_product_center/routers/chat.py", "send_mas_chat_message"),
    ("src/innovation_factory/backend/projects/vi_home_one/routers/chat.py", "send_chat_message"),
    ("src/innovation_factory/backend/projects/bsh_home_connect/routers/chat.py", "send_chat_message"),
    ("src/innovation_factory/backend/projects/adtech_intelligence/routers/chat.py", "send_chat_message"),
    ("src/innovation_factory/backend/projects/adtech_intelligence/routers/chat.py", "send_mas_chat_message"),
    # File-upload endpoints — fix with `response_class=PlainTextResponse`
    # or `responses={200: {"content": {"application/json": {}}}}`.
    ("src/innovation_factory/backend/projects/vi_home_one/routers/tickets.py", "upload_ticket_media"),
    ("src/innovation_factory/backend/projects/bsh_home_connect/routers/tickets.py", "upload_ticket_media"),
    ("src/innovation_factory/backend/projects/bsh_home_connect/routers/tickets.py", "generate_shipping_label"),
    # Plain JSON dict return — should declare `response_model=dict[str, int]`.
    ("src/innovation_factory/backend/projects/adtech_intelligence/routers/anomalies.py", "get_anomaly_counts"),
}


def _is_router_decorator(node: ast.expr) -> tuple[bool, str | None]:
    """Return (is_route, method_name) for an AST decorator node.

    Matches calls like ``@router.get(...)``, ``@some_router.post(...)``.
    Bare ``@router.get`` without ``()`` is not a valid FastAPI decorator
    and is ignored.
    """
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
    """Return the set of bare decorator names on a function — used to
    detect @streaming_endpoint without confusing it with @router.post(...)."""
    names: set[str] = set()
    for dec in decorator_list:
        if isinstance(dec, ast.Name):
            names.add(dec.id)
        elif isinstance(dec, ast.Attribute):
            names.add(dec.attr)
    return names


def _missing_kwargs(provided: set[str], extra_decorators: set[str]) -> set[str]:
    """Return the set of contract violations for a route. Routes marked
    @streaming_endpoint are exempt from the response-declaration kwarg.
    """
    missing: set[str] = set()
    if "operation_id" not in provided:
        missing.add("operation_id")
    if STREAMING_DECORATOR in extra_decorators:
        return missing
    if not (provided & RESPONSE_KWARGS):
        missing.add("response_model|response_class|responses (or @streaming_endpoint)")
    return missing


def _collect_violations() -> list[tuple[Path, int, str, str, set[str]]]:
    """Walk every .py file under the backend directory, parse it, and
    return a list of (file, line, fn_name, http_method, missing_kwargs)
    for every router decorator that violates the contract.
    """
    violations: list[tuple[Path, int, str, str, set[str]]] = []
    for py_path in BACKEND_DIR.rglob("*.py"):
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


def test_every_route_has_operation_id_and_response_declaration():
    """Every router method decorator must declare operation_id + one of
    response_model / response_class / responses. Known pre-existing debt
    is allowlisted via ``KNOWN_DEBT`` so this test catches *new* violations
    while we chip away at the existing ones.
    """
    all_violations = _collect_violations()
    new_violations = [
        v for v in all_violations if (v[0].as_posix(), v[2]) not in KNOWN_DEBT
    ]
    cleared = [
        e for e in KNOWN_DEBT
        if not any(v[0].as_posix() == e[0] and v[2] == e[1] for v in all_violations)
    ]
    if cleared:
        cleared_lines = [f"  ({path!r}, {fn!r})" for path, fn in sorted(cleared)]
        pytest.fail(
            f"\n{len(cleared)} KNOWN_DEBT entry(ies) no longer violate the contract — "
            "remove from KNOWN_DEBT in tests/common/test_router_discipline.py:\n"
            + "\n".join(cleared_lines)
        )
    if new_violations:
        lines = [
            f"  {path}:{lineno}  @{router_method} {fn}  missing: {', '.join(sorted(missing))}"
            for path, lineno, fn, router_method, missing in new_violations
        ]
        pytest.fail(
            f"\nFound {len(new_violations)} NEW route(s) violating router-discipline "
            "(lessons-learned §13). Either fix or add to KNOWN_DEBT with a TODO:\n"
            + "\n".join(lines)
        )
