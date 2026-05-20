"""Seed a demo session for the 2026-05-19 yard-pro live demo.

What this does (against the deployed Lakebase branch):

1. Rebinds the seeded yard's owner from the local-dev placeholder
   ``martin@yard-pro.local`` to the live demo presenter (Felix's
   Databricks Apps identity), so ``get_caller_yard`` resolves
   when Felix opens the cockpit. Idempotent — re-runs are a no-op
   once the rebind is in place.

2. Inserts a new ``yp_diagnoses`` row that mirrors a real photo
   Felix took of his yard the morning of the demo (drought-stressed
   lawn + healthy apple tree). ``status='pending'`` so the demo can
   walk through the Art. 22 review-and-confirm rail before
   accepting the label.

3. Inserts a related ``yp_calendar_entries`` row — the kind of
   action the coach would schedule if Felix accepted the lawn
   drought-stress diagnosis. Scheduled for tomorrow morning so the
   "Today & Upcoming" card shows it cleanly.

The script is idempotent on each step (looks for an existing row
keyed by created_at + top_label or scheduled_at + title before
inserting). Safe to re-run.

Usage:
    uv run python scripts/yard_pro/seed_demo_session.py --profile fevm-felix-demo

Auth model: connects as the running human user (Felix) via the same
``databricks postgres generate-database-credential`` pattern that
``grant_lakebase_app_permissions.py`` uses, since the app SP only
holds connect-level rights by default.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone


DEFAULT_PROFILE = "fevm-felix-demo"
DEFAULT_BRANCH = "projects/innovation-factory/branches/production"
DEFAULT_ENDPOINT = (
    "projects/innovation-factory/branches/production/endpoints/primary"
)
# Databricks Apps proxies the caller's identity in ``X-Forwarded-User``
# as ``<user_id>@<workspace_id>`` — NOT the email. So a rebind to the
# email won't satisfy ``get_caller_yard``. The default below is Felix's
# id on the fevm-felix-demo workspace; override with --user-key when
# running the script for a different presenter. To find your own value:
#
#   databricks current-user me --output json | jq '"\(.id)@\(<workspace_id>)"'
#
# (Easier: open the deployed app, hit /api/projects/<any>/<anything>,
# read the 401/500 error parameters — the user_key value is in the SQL.)
DEFAULT_NEW_USER_KEY = "2788320273611182@7474658643170817"

# Diagnosis matches the real photo Felix took on 2026-05-17:
#   drought-stressed lawn with patchy brown areas; healthy apple
#   tree foliage in the foreground. Vision endpoint is in
#   DEPLOYMENT_FAILED so we hand-author the predictions JSON to
#   mirror what yard-pro-vision-v1 would produce.
DEMO_DIAGNOSIS = {
    "photo_uri": "uc-volume:///Volumes/felix_demo_catalog/yard_pro/photos/1/2026-05-17-yard-overview.jpg",
    "model_version": "yard-pro-vision-v1-stub",
    "predictions": {
        "labels": [
            {"name": "lawn_drought_stress", "confidence": 0.84},
            {"name": "lawn_thatch_buildup", "confidence": 0.52},
            {"name": "apple_tree_healthy", "confidence": 0.78},
            {"name": "weed_pressure_low", "confidence": 0.41},
        ],
    },
    "top_label": "lawn_drought_stress",
    "top_confidence": 0.84,
    "status": "pending",  # Art. 22 review-and-confirm — not yet accepted
    "created_at": "2026-05-17 18:30:00+00",
}

DEMO_CALENDAR = {
    "title": "Stress-relief deep watering — drought-stressed lawn",
    "description": (
        "Coach-suggested follow-up to the 2026-05-17 lawn-drought-stress "
        "diagnosis. Water deeply (1 inch / 25mm) early morning, raise mower "
        "height to 7cm, hold off on fertilizer until 2026-05-25."
    ),
    "scheduled_at": "2026-05-19 06:30:00+00",
    "status": "planned",
}

# Dealer relationship — Martin's yard opts in to share anonymized data
# with the local Stihl dealer. The dealer panel's "Anonymized customers"
# table reads from yp_dealer_relationships (Lakebase) joined with the
# anonymized aggregates from yard_pro_gold.dealer_customer_summary (UC).
# Without this row, Klaus's view is empty.
#
# dealer_id matches _LOCAL_DEV_FALLBACK_DEALER_ID in dealer.py since the
# Apps proxy doesn't set X-Forwarded-Dealer in the demo path.
DEMO_DEALER_RELATIONSHIP = {
    "dealer_id": "dealer_stuttgart_nord",
    "consent_state": "granted",
}


def _run_json(cmd: list[str]) -> dict:
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd)}\n{res.stderr}")
    return json.loads(res.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument(
        "--user-key",
        default=DEFAULT_NEW_USER_KEY,
        help=(
            "Workspace user-id @ workspace-id (the value the Databricks Apps "
            "proxy puts in X-Forwarded-User). Override for a different "
            "presenter / workspace."
        ),
    )
    args = parser.parse_args()
    new_user_key = args.user_key

    print(f"Profile: {args.profile}")

    branch = _run_json([
        "databricks", "postgres", "get-branch", args.branch,
        "-p", args.profile, "--output", "json",
    ])
    state = branch.get("status", {}).get("current_state")
    if state != "READY":
        sys.exit(f"branch is not READY (state={state})")

    cred = _run_json([
        "databricks", "postgres", "generate-database-credential", args.endpoint,
        "-p", args.profile, "--output", "json",
    ])
    token = cred.get("token")
    if not token:
        sys.exit("no token from generate-database-credential")

    me = _run_json([
        "databricks", "current-user", "me",
        "-p", args.profile, "--output", "json",
    ])
    user = me.get("userName") or me.get("user_name")
    if not user:
        sys.exit("could not auto-detect current user")
    print(f"Connecting as: {user}")

    ep = _run_json([
        "databricks", "postgres", "get-endpoint", args.endpoint,
        "-p", args.profile, "--output", "json",
    ])
    host = ep.get("status", {}).get("hosts", {}).get("host")
    if not host:
        sys.exit("could not resolve endpoint host")
    print(f"Host: {host}")

    import psycopg

    conn = psycopg.connect(
        host=host,
        port=5432,
        dbname="databricks_postgres",
        user=user,
        password=token,
        sslmode="require",
        autocommit=False,
    )
    cur = conn.cursor()

    # 1. Rebind any seeded yard to the demo presenter (idempotent — only
    #    flips yards whose user_key isn't already the target).
    cur.execute(
        "UPDATE yp_yards SET user_key = %s WHERE user_key <> %s RETURNING id, user_key",
        (new_user_key, new_user_key),
    )
    rebind = cur.fetchall()
    if rebind:
        for row in rebind:
            print(f"Rebound yard id={row[0]} owner -> {new_user_key}")
    else:
        print(f"No rebind needed (yard already owned by {new_user_key})")

    # Find the yard for the demo user
    cur.execute("SELECT id FROM yp_yards WHERE user_key = %s", (new_user_key,))
    row = cur.fetchone()
    if row is None:
        sys.exit(f"No yp_yards row owned by {new_user_key} — seed may not have run")
    yard_id = row[0]
    print(f"Demo yard_id: {yard_id}")

    # 2. Insert the demo diagnosis (idempotent on created_at + top_label)
    cur.execute(
        """
        SELECT id FROM yp_diagnoses
        WHERE yard_id = %s
          AND top_label = %s
          AND created_at = %s
        """,
        (yard_id, DEMO_DIAGNOSIS["top_label"], DEMO_DIAGNOSIS["created_at"]),
    )
    if cur.fetchone():
        print("Demo diagnosis already present — skipping insert.")
    else:
        cur.execute(
            """
            INSERT INTO yp_diagnoses
                (yard_id, photo_uri, model_version, predictions,
                 top_label, top_confidence, status, created_at)
            VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                yard_id,
                DEMO_DIAGNOSIS["photo_uri"],
                DEMO_DIAGNOSIS["model_version"],
                json.dumps(DEMO_DIAGNOSIS["predictions"]),
                DEMO_DIAGNOSIS["top_label"],
                DEMO_DIAGNOSIS["top_confidence"],
                DEMO_DIAGNOSIS["status"],
                DEMO_DIAGNOSIS["created_at"],
            ),
        )
        new_id = cur.fetchone()[0]
        print(f"Inserted yp_diagnoses id={new_id}")

    # 3. Insert the related calendar entry
    cur.execute(
        """
        SELECT id FROM yp_calendar_entries
        WHERE yard_id = %s
          AND title = %s
          AND scheduled_at = %s
        """,
        (yard_id, DEMO_CALENDAR["title"], DEMO_CALENDAR["scheduled_at"]),
    )
    if cur.fetchone():
        print("Demo calendar entry already present — skipping insert.")
    else:
        # created_at is set by SQLModel's default_factory at the Python
        # layer — the DB column itself is NOT NULL with no DB-side default,
        # so direct INSERTs must supply it. Use the diagnosis timestamp
        # so the demo story (diagnose → schedule) holds together.
        cur.execute(
            """
            INSERT INTO yp_calendar_entries
                (yard_id, title, description, scheduled_at, status, etag,
                 created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                yard_id,
                DEMO_CALENDAR["title"],
                DEMO_CALENDAR["description"],
                DEMO_CALENDAR["scheduled_at"],
                DEMO_CALENDAR["status"],
                "demo-2026-05-19",
                DEMO_DIAGNOSIS["created_at"],
            ),
        )
        new_id = cur.fetchone()[0]
        print(f"Inserted yp_calendar_entries id={new_id}")

    # 4. Insert a granted dealer relationship so Klaus's view in the
    #    dealer panel actually shows a customer row. Idempotent on
    #    (yard_id, dealer_id).
    cur.execute(
        """
        SELECT id, consent_state FROM yp_dealer_relationships
        WHERE yard_id = %s AND dealer_id = %s
        """,
        (yard_id, DEMO_DEALER_RELATIONSHIP["dealer_id"]),
    )
    existing_rel = cur.fetchone()
    if existing_rel:
        if existing_rel[1] != DEMO_DEALER_RELATIONSHIP["consent_state"]:
            cur.execute(
                """
                UPDATE yp_dealer_relationships
                   SET consent_state = %s, consent_at = NOW()
                 WHERE id = %s
                """,
                (DEMO_DEALER_RELATIONSHIP["consent_state"], existing_rel[0]),
            )
            print(
                f"Updated yp_dealer_relationships id={existing_rel[0]} "
                f"consent_state -> {DEMO_DEALER_RELATIONSHIP['consent_state']}"
            )
        else:
            print(
                f"Dealer relationship already granted (id={existing_rel[0]}) — skipping."
            )
    else:
        cur.execute(
            """
            INSERT INTO yp_dealer_relationships
                (yard_id, dealer_id, consent_state, consent_at, created_at)
            VALUES (%s, %s, %s, NOW(), NOW())
            RETURNING id
            """,
            (
                yard_id,
                DEMO_DEALER_RELATIONSHIP["dealer_id"],
                DEMO_DEALER_RELATIONSHIP["consent_state"],
            ),
        )
        new_id = cur.fetchone()[0]
        print(f"Inserted yp_dealer_relationships id={new_id} (granted)")

    conn.commit()
    cur.close()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
