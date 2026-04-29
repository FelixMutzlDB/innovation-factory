"""Grant the deployed app's service principal CREATE on schema public.

Lakebase Postgres branches give the *human* who runs ``databricks bundle
deploy`` ``CAN_CONNECT_AND_CREATE``, but the app at runtime connects as
its assigned service principal (per ``databricks apps get`` →
``service_principal_client_id``). The SP only gets a connect-level
credential by default and cannot ``CREATE`` in the ``public`` schema, so
``SQLModel.metadata.create_all`` fails the first time a deploy adds new
tables (per the Phase 6 AECO Hub incident).

Run this once per workspace, after ``databricks bundle deploy`` and
``databricks apps`` have created/updated the SP. Idempotent.

Usage:
    python scripts/grant_lakebase_app_permissions.py [--profile fevm-felix-demo]

The script connects to the production Lakebase branch as the human user
(via ``databricks postgres generate-database-credential``) and runs:

    GRANT CREATE ON SCHEMA public TO "<sp-client-id>";

The human user must own / have grant rights on the ``public`` schema —
in practice every Lakebase branch's creator does.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from urllib.parse import quote


DEFAULT_PROFILE = "fevm-felix-demo"
DEFAULT_APP_NAME = "innovation-factory"
DEFAULT_BRANCH = "projects/innovation-factory/branches/production"
DEFAULT_ENDPOINT = (
    "projects/innovation-factory/branches/production/endpoints/primary"
)


def _run_json(cmd: list[str]) -> dict:
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd)}\n{res.stderr}")
    return json.loads(res.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--app-name", default=DEFAULT_APP_NAME)
    parser.add_argument("--branch", default=DEFAULT_BRANCH,
                        help="Lakebase branch to grant against")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT,
                        help="Lakebase endpoint to fetch a token from")
    parser.add_argument("--user",
                        help="Human user identity to connect as. "
                             "Defaults to the current databricks-cli user.")
    args = parser.parse_args()

    print(f"Profile: {args.profile}")
    print(f"App: {args.app_name}")

    # Discover the app's SP client_id
    app = _run_json([
        "databricks", "apps", "get", args.app_name,
        "-p", args.profile, "--output", "json",
    ])
    sp_client_id = app.get("service_principal_client_id")
    if not sp_client_id:
        sys.exit("could not find service_principal_client_id on the app")
    print(f"App SP client_id: {sp_client_id}")

    # Branch sanity check
    branch = _run_json([
        "databricks", "postgres", "get-branch", args.branch,
        "-p", args.profile, "--output", "json",
    ])
    state = branch.get("status", {}).get("current_state")
    print(f"Branch {args.branch} state: {state}")
    if state != "READY":
        sys.exit(f"branch is not READY (state={state}); aborting")

    # Get a database credential as the connecting human user
    cred = _run_json([
        "databricks", "postgres", "generate-database-credential", args.endpoint,
        "-p", args.profile, "--output", "json",
    ])
    token = cred.get("token")
    if not token:
        sys.exit("no token in generate-database-credential response")

    # Find the human user identity if not passed explicitly
    user = args.user
    if not user:
        me = _run_json([
            "databricks", "current-user", "me",
            "-p", args.profile, "--output", "json",
        ])
        user = me.get("userName") or me.get("user_name")
        if not user:
            sys.exit("could not auto-detect current user; pass --user")
    print(f"Connecting as: {user}")

    # Endpoint host
    ep = _run_json([
        "databricks", "postgres", "get-endpoint", args.endpoint,
        "-p", args.profile, "--output", "json",
    ])
    host = ep.get("status", {}).get("hosts", {}).get("host")
    if not host:
        sys.exit("could not resolve endpoint host")
    print(f"Endpoint host: {host}")

    # Connect + grant
    import psycopg
    conn = psycopg.connect(
        host=host,
        port=5432,
        dbname="databricks_postgres",
        user=user,
        password=token,
        sslmode="require",
        autocommit=True,
    )
    cur = conn.cursor()

    cur.execute(
        "SELECT has_schema_privilege(%s, 'public', 'CREATE')",
        (sp_client_id,),
    )
    before = cur.fetchone()[0]
    print(f"Before: SP has CREATE on public = {before}")

    if not before:
        # quote_ident isn't available via SQL alone here; the SP client_id
        # is a UUID so it's safe to interpolate after explicit char-class
        # validation.
        if not all(c.isalnum() or c == "-" for c in sp_client_id):
            sys.exit(f"unexpected character in SP client_id: {sp_client_id!r}")
        cur.execute(f'GRANT CREATE ON SCHEMA public TO "{sp_client_id}"')
        print("Granted CREATE on schema public.")

    cur.execute(
        "SELECT has_schema_privilege(%s, 'public', 'CREATE')",
        (sp_client_id,),
    )
    after = cur.fetchone()[0]
    print(f"After: SP has CREATE on public = {after}")
    if not after:
        sys.exit("grant did not take effect")

    print("\nDone — future bundle deploys can now create new tables on startup.")


if __name__ == "__main__":
    main()
