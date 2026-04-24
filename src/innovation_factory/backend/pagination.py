"""Shared pagination helpers for list endpoints.

The project had inconsistent pagination: some endpoints accepted
``skip`` / ``limit`` with caps, some hard-coded ``.limit(20)`` and
didn't accept ``skip`` at all. This module provides a single FastAPI
dependency so every list endpoint looks the same and can't accidentally
return a 50k-row payload.

Usage:

    from fastapi import Depends
    from ....pagination import PageParams, Pagination

    @router.get("/items", response_model=list[Item])
    def list_items(page: Pagination):
        return db.exec(select(Item).offset(page.skip).limit(page.limit)).all()

Bounds:
  - ``skip`` must be ≥ 0.
  - ``limit`` is capped at :data:`MAX_PAGE_LIMIT` = 500 per page.
  - Default ``limit`` = 50 when caller doesn't specify.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query
from pydantic import BaseModel, Field

MAX_PAGE_LIMIT = 500
DEFAULT_PAGE_LIMIT = 50


class PageParams(BaseModel):
    """Validated pagination parameters."""

    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT)


def _page_params(
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of items to skip before returning results.",
    ),
    limit: int = Query(
        default=DEFAULT_PAGE_LIMIT,
        ge=1,
        le=MAX_PAGE_LIMIT,
        description=(
            f"Maximum items to return. Capped at {MAX_PAGE_LIMIT} "
            "to keep responses bounded."
        ),
    ),
) -> PageParams:
    return PageParams(skip=skip, limit=limit)


#: Drop-in FastAPI dependency. Use with ``page: Pagination`` in signatures.
Pagination = Annotated[PageParams, Depends(_page_params)]
