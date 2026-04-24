"""Deploy Innovation Factory UC data to a target workspace.

Usage:
    cd /path/to/innovation-factory
    python scripts/deploy_to_workspace.py --profile fevm-felix-demo --catalog felix_demo_catalog
"""

import argparse
import json
import sys
import time

from databricks.sdk import WorkspaceClient


def execute_sql(ws, warehouse_id: str, sql: str, catalog: str = "felix_demo_catalog") -> dict:
    """Execute a SQL statement via the Statement Execution API."""
    resp = ws.api_client.do(
        "POST",
        "/api/2.0/sql/statements",
        body={
            "warehouse_id": warehouse_id,
            "statement": sql,
            "catalog": catalog,
            "wait_timeout": "50s",
        },
    )
    status = resp.get("status", {}).get("state", "UNKNOWN")
    if status == "FAILED":
        error = resp.get("status", {}).get("error", {})
        print(f"  FAILED: {error.get('message', 'Unknown error')}")
        return resp
    if status == "SUCCEEDED":
        return resp
    # Poll if PENDING/RUNNING
    stmt_id = resp.get("statement_id")
    for _ in range(60):
        time.sleep(2)
        resp = ws.api_client.do("GET", f"/api/2.0/sql/statements/{stmt_id}")
        status = resp.get("status", {}).get("state", "UNKNOWN")
        if status in ("SUCCEEDED", "FAILED", "CANCELED", "CLOSED"):
            break
    if status == "FAILED":
        error = resp.get("status", {}).get("error", {})
        print(f"  FAILED: {error.get('message', 'Unknown error')}")
    return resp


def create_hb_tables(ws, warehouse_id: str, catalog: str, schema: str = "hb_product_center"):
    """Create the HB Product Center tables."""
    fqn = f"{catalog}.{schema}"

    tables = [
        f"""CREATE TABLE IF NOT EXISTS {fqn}.hb_products (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            sku STRING, style_name STRING, color STRING, color_code STRING,
            size STRING, category STRING, collection STRING, season STRING,
            material STRING, price DOUBLE, status STRING,
            country_of_origin STRING, supplier_name STRING, created_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {fqn}.hb_recognition_jobs (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            job_type STRING, status STRING, user_role STRING,
            submitted_by STRING, image_count INT, completed_count INT,
            created_at TIMESTAMP, completed_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {fqn}.hb_quality_inspections (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            product_id INT, batch_number STRING, inspector STRING,
            manufacturing_partner STRING, overall_score DOUBLE,
            status STRING, notes STRING,
            created_at TIMESTAMP, completed_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {fqn}.hb_quality_defects (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            inspection_id INT, defect_type STRING, severity STRING,
            location_description STRING, confidence_score DOUBLE,
            image_url STRING, created_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {fqn}.hb_auth_verifications (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            product_id INT, requester_type STRING, requester_name STRING,
            requester_email STRING, status STRING, confidence_score DOUBLE,
            verification_method STRING, image_url STRING,
            region STRING, notes STRING,
            created_at TIMESTAMP, completed_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {fqn}.hb_auth_alerts (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            verification_id INT, alert_type STRING, severity STRING,
            region STRING, description STRING, investigated_by STRING,
            resolution STRING, created_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {fqn}.hb_supply_chain_events (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            product_id INT, event_type STRING, location STRING,
            partner_name STRING, country STRING, details STRING,
            event_date TIMESTAMP, created_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {fqn}.hb_sustainability_metrics (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            product_id INT, carbon_footprint_kg DOUBLE,
            water_usage_liters DOUBLE, recycled_content_pct DOUBLE,
            organic_material_pct DOUBLE, certifications STRING,
            compliance_status STRING, last_audit_date TIMESTAMP,
            created_at TIMESTAMP
        )""",
    ]

    for ddl in tables:
        table_name = ddl.split("IF NOT EXISTS ")[1].split(" (")[0]
        print(f"  Creating {table_name}...")
        resp = execute_sql(ws, warehouse_id, ddl, catalog)
        status = resp.get("status", {}).get("state", "UNKNOWN")
        if status != "SUCCEEDED":
            print(f"    ERROR creating table: {status}")
            return False
    return True


def seed_hb_data(ws, warehouse_id: str, catalog: str):
    """Generate and execute HB Product Center seed data."""
    # Import the seed data generator (reuse existing script)
    sys.path.insert(0, "scripts")
    from seed_uc_hb_data import build_sql

    stmts = build_sql()
    # Replace the hardcoded catalog with the target catalog
    for i, stmt in enumerate(stmts):
        stmt = stmt.replace("innovation_factory_catalog", catalog)
        print(f"  Inserting batch {i+1}/{len(stmts)}...")
        resp = execute_sql(ws, warehouse_id, stmt, catalog)
        status = resp.get("status", {}).get("state", "UNKNOWN")
        if status != "SUCCEEDED":
            print(f"    ERROR inserting data: {status}")
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Deploy Innovation Factory to a workspace")
    parser.add_argument("--profile", required=True, help="Databricks CLI profile name")
    parser.add_argument("--catalog", default="felix_demo_catalog", help="UC catalog name")
    parser.add_argument("--warehouse-id", default=None, help="SQL warehouse ID (auto-detected if omitted)")
    parser.add_argument("--skip-uc", action="store_true", help="Skip UC data seeding")
    args = parser.parse_args()

    print("=" * 60)
    print("Innovation Factory — UC Data Deployment")
    print("=" * 60)

    # Connect
    print(f"\n1. Connecting to workspace (profile: {args.profile})...")
    ws = WorkspaceClient(profile=args.profile)
    user = ws.current_user.me().user_name
    print(f"   Authenticated as: {user}")

    # Find warehouse
    if args.warehouse_id:
        warehouse_id = args.warehouse_id
    else:
        print("\n2. Finding SQL warehouse...")
        warehouses = list(ws.warehouses.list())
        if not warehouses:
            print("   ERROR: No SQL warehouses found!")
            sys.exit(1)
        warehouse_id = warehouses[0].id
        print(f"   Using: {warehouses[0].name} ({warehouse_id})")

    # Create schema
    print(f"\n3. Creating schema {args.catalog}.hb_product_center...")
    execute_sql(ws, warehouse_id, f"CREATE SCHEMA IF NOT EXISTS {args.catalog}.hb_product_center", args.catalog)
    print("   Done.")

    if not args.skip_uc:
        # Create tables
        print(f"\n4. Creating HB Product Center tables...")
        if not create_hb_tables(ws, warehouse_id, args.catalog):
            print("   Table creation failed!")
            sys.exit(1)
        print("   All tables created.")

        # Seed data
        print(f"\n5. Seeding HB Product Center data...")
        if not seed_hb_data(ws, warehouse_id, args.catalog):
            print("   Seeding failed!")
            sys.exit(1)
        print("   All data seeded.")

    # Verify
    print(f"\n6. Verifying...")
    tables = ["hb_products", "hb_recognition_jobs", "hb_quality_inspections",
              "hb_quality_defects", "hb_auth_verifications", "hb_auth_alerts",
              "hb_supply_chain_events", "hb_sustainability_metrics"]
    for t in tables:
        resp = execute_sql(ws, warehouse_id, f"SELECT COUNT(*) FROM {args.catalog}.hb_product_center.{t}", args.catalog)
        count = "?"
        if resp.get("result", {}).get("data_array"):
            count = resp["result"]["data_array"][0][0]
        print(f"   {t}: {count} rows")

    print("\n" + "=" * 60)
    print("UC data deployment complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
