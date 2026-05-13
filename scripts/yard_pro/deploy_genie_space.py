"""Deploy the yard-pro dealer Genie space (UC6, P5).

The dealer panel hangs off a single Genie space over the anonymized gold
table ``yard_pro_gold.dealer_customer_summary``. Klaus opens this space
and asks natural-language questions over **his rows only**. Plan §8
"AI security — Genie" row: "row-level filters baked into the underlying
Delta view, not relying on Genie's NL→SQL to enforce them".

What this script does (mirrors the AECO Genie deploy in
``scripts/deploy_agents_fevm.py::phase_5_genie_spaces``):

1. Confirms ``yard_pro_gold.dealer_customer_summary`` exists in the
   target catalog. If not, prints the seed step from the runbook §2 and
   exits 1 — refusing to create a Genie space against a missing table.

2. ``POST /api/2.0/data-rooms/`` with:
   - ``display_name``: ``yard-pro-dealer-genie``
   - ``table_identifiers``: only the gold table; explicitly NOT any
     ``yard_pro_bronze.*`` / ``yard_pro_silver.*`` / ``yp_*`` table.
     This is the UC-permission rail: even if Genie's NL→SQL tried to
     reach a non-anonymized table, the dealer SP's UC grants prevent it
     (RT-022). The Genie space's ``table_identifiers`` make the
     intention explicit.
   - ``run_as_type``: ``VIEWER`` — Genie queries run with the **caller's**
     identity, not the space owner's. The caller is the dealer SP, which
     has SELECT only on the gold table. This is what closes RT-003 +
     RT-022 at the SQL boundary.

3. Adds 6 curated sample questions matching plan §2 success criterion
   #6 ("which of my customers have a robotic mower past 4 years old that
   hasn't been serviced this season?") plus 5 more that exercise the
   bucketed columns.

4. Prints the resulting space_id and the exact env-var line to paste
   into ``app.yml`` + ``databricks.yml``:

       YARD_PRO_DEALER_GENIE_SPACE_ID=<uuid>

Row-level filter note:
  We do NOT create a separate filtered Delta view per dealer. The
  ``dealer_code`` column on ``dealer_customer_summary`` is the
  enforcement column; the dealer SP's UC grants include a row filter
  ``dealer_code = current_user_dealer()`` (or equivalent), set up in
  the runbook §11 alongside the SELECT grant. That filter belongs in
  Unity Catalog, not in this script — keeping the filter at the UC
  layer means **every** access path (Genie, SQL warehouse, JDBC, BI
  tools) inherits the same row scope automatically.

  If the runbook §11 UC grant + filter has not been applied, this
  script still creates the Genie space — but Klaus would see every
  dealer's rows in the demo until the filter is in place. The script
  prints a WARN in that case.

Idempotency:
  The script reads ``scripts/yard_pro/genie_state.json`` (created on
  first run). If the file exists and the space is still present in the
  workspace, the script exits 0 with "already deployed". Override with
  ``--force`` to recreate the space (note: this is destructive —
  current curated questions and pinned conversations are lost).

Authentication:
  Uses the ``databricks api`` CLI subcommand (lessons §28). The
  ``--profile`` flag selects the workspace; defaults to
  ``fevm-felix-demo`` matching the rest of the deploy scripts.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = Path(__file__).resolve().parent / "genie_state.json"

DEFAULT_PROFILE = "fevm-felix-demo"
DEFAULT_CATALOG = "felix_demo_catalog"
DEFAULT_WAREHOUSE_ID = "f7cdb11888c4799e"
DEFAULT_SPACE_NAME = "yard-pro-dealer-genie"

GOLD_TABLE = "yard_pro_gold.dealer_customer_summary"

# Sample questions match plan §2 success criterion #6 plus 5 that
# exercise the bucketed columns. All run safely against the seeded
# rows — no question requires un-anonymized columns to answer.
SAMPLE_QUESTIONS = [
    # The headline plan §2 demo question.
    "Which customers have a robotic mower 4+ years old that hasn't been "
    "serviced in the last 90 days?",
    "How many anonymized customers do I have in each region bucket?",
    "What is the distribution of yard sizes among my consented customers?",
    "Which tool inventory hashes appear most often in my customer base?",
    "How many of my customers have a robotic mower at all?",
    "Show me customers whose last service event was more than 6 months ago.",
]


# ---------------------------------------------------------------------------
# State file (mirrors fevm_agents_state.json from deploy_agents_fevm.py)
# ---------------------------------------------------------------------------


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ---------------------------------------------------------------------------
# Databricks CLI shim — same pattern as scripts/deploy_agents_fevm.py
# ---------------------------------------------------------------------------


def _api(
    method: str,
    path: str,
    body: dict | None = None,
    *,
    profile: str,
    timeout: int = 300,
) -> dict | None:
    """Invoke ``databricks api {method} {path}`` against the named profile.

    Returns parsed JSON on success, ``None`` on failure (with stderr
    printed). Mirrors ``deploy_agents_fevm._api`` so the workspace auth
    flow is identical across all the deploy scripts.
    """
    cmd = ["databricks", "api", method.lower(), path, "--profile", profile]
    if body is not None:
        cmd.extend(["--json", json.dumps(body)])
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if res.returncode != 0:
        print(f"    API ERROR {method} {path}: {res.stderr[:500]}")
        return None
    if not res.stdout.strip():
        return {}
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError:
        print(f"    Could not parse: {res.stdout[:300]}")
        return None


def _sql(
    statement: str,
    *,
    profile: str,
    warehouse_id: str,
    catalog: str | None = None,
    timeout: int = 60,
) -> dict | None:
    body: dict = {
        "warehouse_id": warehouse_id,
        "statement": statement,
        "wait_timeout": "30s",
    }
    if catalog:
        body["catalog"] = catalog
    return _api("post", "/api/2.0/sql/statements", body, profile=profile, timeout=timeout)


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------


def _verify_gold_table_exists(
    *, profile: str, catalog: str, warehouse_id: str
) -> bool:
    """Refuse to deploy a Genie space against a missing gold table."""
    table_fq = f"{catalog}.{GOLD_TABLE}"
    resp = _sql(
        f"DESCRIBE TABLE {table_fq}",
        profile=profile,
        warehouse_id=warehouse_id,
    )
    if resp is None:
        print(f"  ERROR: could not query {table_fq}; check profile + warehouse.")
        return False
    status = (resp.get("status") or {}).get("state", "UNKNOWN")
    if status == "FAILED":
        err = (
            (resp.get("status") or {}).get("error", {}).get("message", "?")
        )
        print(f"  ERROR: {table_fq} not found: {err[:300]}")
        print(
            "  Fix: run the seed step from the runbook §2:\n"
            "    uv run python -m src.innovation_factory.backend."
            "projects.yard_pro.seed_uc_tables --catalog "
            f"{catalog} --profile {profile} --warehouse-id {warehouse_id}"
        )
        return False
    print(f"  {table_fq}: OK")
    return True


def _verify_row_filter_warning(
    *, profile: str, catalog: str, warehouse_id: str
) -> None:
    """Check whether a UC row filter is attached to the gold table.

    If no filter is detected, print a WARN — the Genie space will still
    deploy, but every dealer would see every row until the filter is
    applied (runbook §11).
    """
    table_fq = f"{catalog}.{GOLD_TABLE}"
    # SHOW ROW FILTER or DESCRIBE TABLE EXTENDED both expose attached
    # filters. The exact syntax varies by workspace version; we use the
    # broadly-supported SHOW TBLPROPERTIES + DESCRIBE EXTENDED fallback.
    resp = _sql(
        f"DESCRIBE TABLE EXTENDED {table_fq}",
        profile=profile,
        warehouse_id=warehouse_id,
    )
    if resp is None:
        return
    text = json.dumps(resp)
    if "row filter" in text.lower() or "row_filter" in text.lower():
        print(f"  Row filter detected on {table_fq}: OK")
        return
    print(
        f"  WARN: no row filter visible on {table_fq}. Klaus would see "
        f"every dealer's rows until the runbook §11 UC grant + row filter "
        f"are applied. The Genie space will still deploy."
    )


def _create_genie_space(
    *,
    profile: str,
    catalog: str,
    warehouse_id: str,
    name: str,
) -> str | None:
    """Create the Genie space and return its space_id, or None on failure."""
    body = {
        "display_name": name,
        "description": (
            "yard-pro dealer Genie space (UC6, P5). Reads only "
            f"{catalog}.{GOLD_TABLE} — the anonymized aggregate view. "
            "yard_id_hash is the only join key; no raw PII reachable. "
            "Row-level filter at the UC layer scopes each dealer SP to "
            "its own dealer_code rows."
        ),
        "warehouse_id": warehouse_id,
        "table_identifiers": [f"{catalog}.{GOLD_TABLE}"],
        # VIEWER means queries run with the caller's identity → the
        # dealer SP's UC grants apply, closing RT-003 + RT-022 at the
        # SQL boundary.
        "run_as_type": "VIEWER",
    }
    print(f"  Creating Genie space: {name}...")
    resp = _api("post", "/api/2.0/data-rooms/", body, profile=profile)
    if resp is None:
        return None
    space_id = resp.get("space_id") or resp.get("id")
    if not space_id:
        print(f"    Failed: {resp}")
        return None
    print(f"    Created: {space_id}")

    # Curated sample questions — mirror the AECO pattern.
    q_body = {
        "batch_actions": [
            {
                "action": "ADD",
                "curated_question": {
                    "question_text": q,
                    "question_type": "SAMPLE_QUESTION",
                },
            }
            for q in SAMPLE_QUESTIONS
        ]
    }
    q_resp = _api(
        "post",
        f"/api/2.0/data-rooms/{space_id}/curated-questions/batch-actions",
        q_body,
        profile=profile,
    )
    if q_resp is not None:
        print(f"    Added {len(SAMPLE_QUESTIONS)} sample questions")
    else:
        print(f"    WARN: sample questions failed (space still usable)")
    return space_id


def _space_still_exists(space_id: str, *, profile: str) -> bool:
    """Verify a state-file space_id is still live in the workspace."""
    resp = _api("get", f"/api/2.0/data-rooms/{space_id}", profile=profile)
    return bool(resp and (resp.get("space_id") or resp.get("id")))


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deploy the yard-pro dealer Genie space (UC6, P5)."
    )
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    parser.add_argument("--warehouse-id", default=DEFAULT_WAREHOUSE_ID)
    parser.add_argument("--space-name", default=DEFAULT_SPACE_NAME)
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Recreate the Genie space even if scripts/yard_pro/"
            "genie_state.json points at a live one. Destructive — "
            "curated questions and pinned conversations are lost."
        ),
    )
    args = parser.parse_args(argv)

    print("================================================================")
    print(" yard-pro: Dealer Genie space deploy")
    print("================================================================")
    print(f"  Profile:     {args.profile}")
    print(f"  Catalog:     {args.catalog}")
    print(f"  Warehouse:   {args.warehouse_id}")
    print(f"  Space name:  {args.space_name}")
    print()

    state = _load_state()
    existing_id = state.get("dealer_space_id")
    if existing_id and not args.force:
        if _space_still_exists(existing_id, profile=args.profile):
            print(f"  Already deployed: {existing_id}")
            print()
            _print_env_var_line(existing_id)
            return 0
        print(f"  State pointed at {existing_id}, but workspace says gone — recreating.")

    print("Step 1: verify gold table exists")
    if not _verify_gold_table_exists(
        profile=args.profile,
        catalog=args.catalog,
        warehouse_id=args.warehouse_id,
    ):
        return 1

    print()
    print("Step 2: check for row filter (warn-only)")
    _verify_row_filter_warning(
        profile=args.profile,
        catalog=args.catalog,
        warehouse_id=args.warehouse_id,
    )

    print()
    print("Step 3: create Genie space")
    space_id = _create_genie_space(
        profile=args.profile,
        catalog=args.catalog,
        warehouse_id=args.warehouse_id,
        name=args.space_name,
    )
    if not space_id:
        return 1

    state["dealer_space_id"] = space_id
    state["catalog"] = args.catalog
    state["table"] = GOLD_TABLE
    _save_state(state)

    print()
    print("== DONE ==")
    print(f"  Space:    {args.space_name}")
    print(f"  ID:       {space_id}")
    print(f"  Table:    {args.catalog}.{GOLD_TABLE}")
    print(f"  State:    {STATE_FILE}")
    print()
    _print_env_var_line(space_id)
    return 0


def _print_env_var_line(space_id: str) -> None:
    print("  Set in app.yml / databricks.yml / .env:")
    print()
    print(f"    YARD_PRO_DEALER_GENIE_SPACE_ID={space_id}")
    print()
    print("  Then redeploy the app:")
    print("    uv run apx build && databricks bundle deploy -t dev "
          f"--profile {DEFAULT_PROFILE}")


if __name__ == "__main__":
    sys.exit(main())
