"""Post-deploy smoke test for innovation-factory.

Hits ``/api/_health`` and one portfolio endpoint per accelerator, asserts
2xx + non-empty payload, prints a structured summary. Designed for the
agent (or CI) to run after ``databricks bundle deploy`` to catch the
class of issues that bit Phase 6 (silent ``permission denied`` on
``CREATE``, missing platform Project row, empty per-accelerator tables).

Usage:

    # Local dev (apx dev start running)
    python scripts/smoke.py --base http://localhost:9001

    # Deployed app — needs a Databricks PAT in DATABRICKS_TOKEN so the
    # auth proxy lets us through without an SSO browser.
    DATABRICKS_TOKEN=<pat> python scripts/smoke.py \\
        --base https://innovation-factory-7474658643170817.aws.databricksapps.com

Exits 0 if every check passes; 1 otherwise. Prints a one-line summary
plus per-accelerator detail.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import urllib.error
import urllib.request


# (slug, portfolio-style endpoint that should return non-empty data
# when the accelerator's seed has run successfully). For accelerators
# without a portfolio endpoint, fall back to a list endpoint.
ACCELERATORS: list[tuple[str, str]] = [
    ("vi-home-one",          "/api/projects/vi-home-one/neighborhoods"),
    ("bsh-home-connect",     "/api/projects/bsh-home-connect/devices"),
    ("mol-asm-cockpit",      "/api/projects/mol-asm-cockpit/stations"),
    ("adtech-intelligence",  "/api/projects/adtech-intelligence/dashboard/summary"),
    ("hb-product-center",    "/api/projects/hb-product-center/products"),
    ("aeco-hub",             "/api/projects/aeco-hub/portfolio/stats"),
]


def _get(url: str, token: str | None) -> tuple[int, Any]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")[:300]
    except Exception as e:
        return -1, str(e)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base", default="http://localhost:9001",
        help="App base URL (no trailing slash).",
    )
    parser.add_argument(
        "--token", default=os.environ.get("DATABRICKS_TOKEN"),
        help="Databricks PAT (defaults to DATABRICKS_TOKEN).",
    )
    args = parser.parse_args()
    base = args.base.rstrip("/")

    print(f"Smoke target: {base}\n")
    failures: list[str] = []

    # 1. /api/_health
    status, body = _get(f"{base}/api/_health", args.token)
    if status != 200 or not isinstance(body, dict):
        failures.append(f"/api/_health: status={status} body={body!r}")
        print(f"  [FAIL] /api/_health  status={status}")
    else:
        ok = body.get("db_ok") is True
        n = body.get("accelerators_registered", 0)
        warns = body.get("startup_warnings", [])
        marker = "✓" if ok and n >= 1 and not warns else "✗"
        print(f"  [{marker}] /api/_health  db_ok={ok}  accelerators={n}  warnings={len(warns)}")
        if not ok:
            failures.append("/api/_health.db_ok=False")
        if warns:
            failures.append(f"/api/_health.startup_warnings={warns}")
        # Surface table counts (helps debug missing seeds).
        for tbl, count in (body.get("table_counts") or {}).items():
            print(f"        {tbl:18} = {count}")

    # 2. Each accelerator's portfolio endpoint
    print()
    for slug, path in ACCELERATORS:
        status, body = _get(f"{base}{path}", args.token)
        if status != 200:
            failures.append(f"{path}: status={status}")
            print(f"  [FAIL] {slug:22} {path}  status={status}")
            continue
        # Non-empty assertion: list must have items, dict must have any non-zero number
        empty = (
            (isinstance(body, list) and len(body) == 0)
            or (isinstance(body, dict) and not any(
                isinstance(v, (int, float)) and v > 0 for v in body.values()
            ))
        )
        marker = "✗" if empty else "✓"
        size = len(body) if isinstance(body, (list, dict)) else 0
        print(f"  [{marker}] {slug:22} {path}  size={size}")
        if empty:
            failures.append(f"{path}: empty payload")

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed:")
        for f in failures:
            print(f"    - {f}")
        return 1
    print("PASS — all smoke checks green.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
