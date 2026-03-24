"""Migrate UC tables to a new workspace by executing SQL via Statement Execution API."""

import json
import os
import subprocess
import sys
import time

PROFILE = "fe-sandbox-felix-demo-sandbox"
WAREHOUSE_ID = "8af6100313039ba2"
CATALOG = "felix_demo_sandbox_catalog"

def execute_sql(statement: str, max_poll_seconds: int = 300) -> dict:
    """Execute SQL via Databricks Statement Execution API with polling."""
    payload = {
        "warehouse_id": WAREHOUSE_ID,
        "statement": statement,
        "wait_timeout": "50s",
    }
    result = subprocess.run(
        ["databricks", "api", "post", "/api/2.0/sql/statements",
         "--json", json.dumps(payload),
         "--profile", PROFILE],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[:500]}")
        return {"status": {"state": "FAILED"}}
    resp = json.loads(result.stdout)
    state = resp.get("status", {}).get("state", "UNKNOWN")

    # Poll if still pending/running
    statement_id = resp.get("statement_id")
    elapsed = 0
    while state in ("PENDING", "RUNNING") and elapsed < max_poll_seconds and statement_id:
        time.sleep(5)
        elapsed += 5
        poll_result = subprocess.run(
            ["databricks", "api", "get", f"/api/2.0/sql/statements/{statement_id}",
             "--profile", PROFILE],
            capture_output=True, text=True, timeout=30,
        )
        if poll_result.returncode == 0:
            resp = json.loads(poll_result.stdout)
            state = resp.get("status", {}).get("state", "UNKNOWN")

    if state == "FAILED":
        err = resp.get("status", {}).get("error", {}).get("message", "Unknown error")
        print(f"  SQL FAILED: {err[:300]}")
    return resp


def create_hb_tables():
    """Create HB Product Center tables."""
    print("\n=== Creating HB Product Center tables ===")
    tables = [
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.hb_product_center.hb_products (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            sku STRING, style_name STRING, color STRING, color_code STRING,
            size STRING, category STRING, collection STRING, season STRING,
            material STRING, price DOUBLE, status STRING, country_of_origin STRING,
            supplier_name STRING, created_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.hb_product_center.hb_recognition_jobs (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            job_type STRING, status STRING, user_role STRING, submitted_by STRING,
            image_count INT, completed_count INT, created_at TIMESTAMP, completed_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.hb_product_center.hb_quality_inspections (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            product_id BIGINT, batch_number STRING, inspector STRING,
            manufacturing_partner STRING, overall_score DOUBLE, status STRING,
            notes STRING, created_at TIMESTAMP, completed_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.hb_product_center.hb_quality_defects (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            inspection_id BIGINT, defect_type STRING, severity STRING,
            location_description STRING, confidence_score DOUBLE,
            image_url STRING, created_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.hb_product_center.hb_auth_verifications (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            product_id BIGINT, requester_type STRING, requester_name STRING,
            requester_email STRING, status STRING, confidence_score DOUBLE,
            verification_method STRING, image_url STRING, region STRING,
            notes STRING, created_at TIMESTAMP, completed_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.hb_product_center.hb_auth_alerts (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            verification_id BIGINT, alert_type STRING, severity STRING,
            region STRING, description STRING, investigated_by STRING,
            resolution STRING, created_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.hb_product_center.hb_supply_chain_events (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            product_id BIGINT, event_type STRING, location STRING,
            partner_name STRING, country STRING, details STRING,
            event_date TIMESTAMP, created_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.hb_product_center.hb_sustainability_metrics (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            product_id BIGINT, carbon_footprint_kg DOUBLE, water_usage_liters DOUBLE,
            recycled_content_pct DOUBLE, organic_material_pct DOUBLE,
            certifications STRING, compliance_status STRING,
            last_audit_date DATE, created_at TIMESTAMP
        )""",
    ]
    for i, ddl in enumerate(tables):
        tname = ddl.split("IF NOT EXISTS")[1].split("(")[0].strip()
        print(f"  Creating table {tname}...")
        resp = execute_sql(ddl)
        state = resp.get("status", {}).get("state", "UNKNOWN")
        print(f"    -> {state}")


def seed_hb_data():
    """Seed HB Product Center data using the existing seed script."""
    print("\n=== Seeding HB Product Center data ===")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from seed_uc_hb_data import build_sql
    stmts = build_sql()
    stmts = [s.replace("innovation_factory_catalog", CATALOG) for s in stmts]
    for i, stmt in enumerate(stmts):
        tname = stmt.split("INTO")[1].split("(")[0].strip() if "INTO" in stmt else f"Statement {i+1}"
        print(f"  Inserting into {tname}...")
        resp = execute_sql(stmt, max_poll_seconds=300)
        state = resp.get("status", {}).get("state", "UNKNOWN")
        print(f"    -> {state}")


def create_mol_tables():
    """Create MOL ASM Cockpit tables."""
    print("\n=== Creating MOL ASM Cockpit tables ===")
    tables = [
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.asm_cockpit.stations (
            id INT, station_code STRING, name STRING, city STRING,
            region STRING, country STRING, latitude DOUBLE, longitude DOUBLE,
            station_type STRING, has_fresh_corner BOOLEAN, has_ev_charging BOOLEAN,
            num_pumps INT, shop_area_sqm DOUBLE
        )""",
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.asm_cockpit.fuel_sales (
            station_id INT, sale_date DATE, fuel_type STRING,
            volume_liters DOUBLE, revenue DOUBLE, unit_price DOUBLE, margin DOUBLE
        )""",
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.asm_cockpit.nonfuel_sales (
            station_id INT, sale_date DATE, category STRING,
            quantity INT, revenue DOUBLE, margin DOUBLE
        )""",
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.asm_cockpit.workforce_shifts (
            station_id INT, shift_date DATE, shift_type STRING,
            planned_headcount INT, actual_headcount INT, overtime_hours DOUBLE
        )""",
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.asm_cockpit.inventory (
            station_id INT, record_date DATE, product_category STRING,
            stock_level INT, reorder_point INT, spoilage_count INT,
            stock_out_events INT, delivery_scheduled BOOLEAN
        )""",
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.asm_cockpit.competitor_prices (
            station_id INT, price_date DATE, competitor_name STRING,
            fuel_type STRING, price_per_liter DOUBLE
        )""",
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.asm_cockpit.price_history (
            station_id INT, price_date DATE, fuel_type STRING,
            price_per_liter DOUBLE, cost_per_liter DOUBLE
        )""",
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.asm_cockpit.loyalty_metrics (
            station_id INT, month DATE, active_members INT,
            new_signups INT, points_redeemed INT, loyalty_revenue_share DOUBLE
        )""",
        f"""CREATE TABLE IF NOT EXISTS {CATALOG}.asm_cockpit.anomaly_alerts (
            id INT, station_id INT, metric_type STRING, severity STRING,
            title STRING, description STRING, suggested_action STRING,
            status STRING, detected_at TIMESTAMP
        )""",
    ]
    for ddl in tables:
        tname = ddl.split("IF NOT EXISTS")[1].split("(")[0].strip()
        print(f"  Creating table {tname}...")
        resp = execute_sql(ddl)
        state = resp.get("status", {}).get("state", "UNKNOWN")
        print(f"    -> {state}")


def seed_mol_stations():
    """Seed MOL stations data (small, insert via SQL)."""
    print("\n=== Seeding MOL ASM Cockpit station data ===")
    from src.innovation_factory.backend.projects.mol_asm_cockpit.seed_uc_tables import STATIONS
    rows = []
    for s in STATIONS:
        vals = ", ".join([
            str(s[0]), f"'{s[1]}'", f"'{s[2]}'", f"'{s[3]}'", f"'{s[4]}'",
            f"'{s[5]}'", str(s[6]), str(s[7]), f"'{s[8]}'",
            str(s[9]).lower(), str(s[10]).lower(), str(s[11]), str(s[12])
        ])
        rows.append(f"({vals})")
    stmt = f"INSERT INTO {CATALOG}.asm_cockpit.stations VALUES\n" + ",\n".join(rows)
    resp = execute_sql(stmt)
    print(f"  Stations: {resp.get('status', {}).get('state', 'UNKNOWN')}")


if __name__ == "__main__":
    print("Starting UC data migration to fe-sandbox-felix-demo-sandbox...")

    create_hb_tables()
    seed_hb_data()
    create_mol_tables()

    print("\n=== Migration complete ===")
    print("NOTE: MOL ASM Cockpit fact data (fuel_sales, nonfuel_sales, etc.) requires")
    print("PySpark and must be seeded via a notebook or job on the target workspace.")
    print("The stations reference table has been seeded.")
