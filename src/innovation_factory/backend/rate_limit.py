"""Rate limiting for expensive chat / recognition endpoints.

Background on keying (civion-safe lesson 19.9 + elaboration in
docs/cleanup-and-improvement-plan.md):

This app sits behind the Databricks Apps auth proxy. Every request seen
by FastAPI shares the same remote IP (the proxy's), so keying a rate
limit on ``get_remote_address`` collapses to a single global quota. The
proxy forwards the authenticated user in ``X-Forwarded-User``, which is
what we key off. Local development (no proxy) falls back to the socket
IP so the limiter is still functional during ``apx dev start``.

Per-endpoint budgets target realistic demo traffic (lesson 19.9):

  - chat endpoints (MAS / KA invocation):   30/minute per user
  - recognition / identify:                 10/minute per user
  - platform ideas session:                 20/minute per user

These are deliberately generous — a persona clicking around shouldn't
hit 429. Tighten only when a specific endpoint has a narrower cost
signal.

Lesson 19.12 also applies: for SSE chat, the limiter fires on the POST
that starts a stream, not per chunk. Today each chat turn is one POST,
so this is already per-message. If we ever add multi-turn over a single
connection, the limit must move inside the generator.
"""
from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


def _user_or_ip(request: Request) -> str:
    """Key rate limits on the authenticated user, falling back to IP.

    Databricks Apps injects the authenticated identity into
    ``X-Forwarded-User`` (set by the auth proxy). In local dev the
    proxy is absent; fall through to ``X-Forwarded-Preferred-Username``
    (some deployments use that) and finally to ``get_remote_address``.
    """
    for header in ("X-Forwarded-User", "X-Forwarded-Preferred-Username"):
        value = request.headers.get(header)
        if value:
            return f"user:{value}"
    return f"ip:{get_remote_address(request)}"


# Module-level limiter instance — registered with the FastAPI app in
# app.py and consumed by @limiter.limit("...") decorators in routers.
limiter = Limiter(key_func=_user_or_ip)


__all__ = ["limiter", "RateLimitExceeded", "_user_or_ip"]
