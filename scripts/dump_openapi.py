"""Dump the FastAPI OpenAPI schema to a file without booting the backend.

The standard ``apx dev start`` regenerates ``ui/lib/api.ts`` as a side
effect of running the app, but if the backend lifespan crashes (DB
connection, missing tables, OAuth) the regeneration never happens — and
the frontend won't compile because hooks like ``useAeco_*Suspense``
don't exist yet. This script imports the FastAPI app *without* running
its ``lifespan`` (so no DB calls), serializes ``app.openapi()`` to JSON,
and writes it to a path that the frontend codegen can consume.

Usage:

    # Just dump:
    python scripts/dump_openapi.py
    # → writes .build/openapi.json

    # Custom output:
    python scripts/dump_openapi.py --output /tmp/openapi.json

After dumping, run ``uv run apx frontend build`` (or the project's
equivalent codegen step) to regenerate ``ui/lib/api.ts``.

This is the recovery move when ``apx dev start`` is broken because of a
runtime issue you don't want to debug yet. No database, no OAuth, no
seed — just the route shapes.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / ".build" / "openapi.json"),
        help="Output path. Defaults to .build/openapi.json.",
    )
    args = parser.parse_args()

    # Make sure the backend code is importable.
    src_path = REPO_ROOT / "src"
    sys.path.insert(0, str(src_path))

    # Force PGlite-fallback so engine_url doesn't try Lakebase. We never
    # actually connect — we just need ``app.openapi()`` — but the runtime
    # creates the engine eagerly via cached_property.
    os.environ.setdefault("APX_DEV_DB_PORT", "5432")
    os.environ.setdefault("APX_DEV_DB_PWD", "noop")

    # Import the app. The lifespan won't run because we never use the
    # ASGI lifespan protocol — we just instantiate and ask for the schema.
    from innovation_factory.backend.app import app

    schema = app.openapi()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, default=str)

    routes = len(schema.get("paths", {}))
    print(f"Wrote {out} ({routes} paths)")
    return 0


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(main())
