"""Comprehensive phase-based migration script for migrating a Databricks App
and all backing resources from e2-demo-field-eng to fe-sandbox-felix-demo-sandbox.

Usage:
    python scripts/migrate_full.py <phase|all>
    python scripts/migrate_full.py 0        # Run pre-flight checks
    python scripts/migrate_full.py all      # Run all phases sequentially
"""

import json
import os
import subprocess
import sys
import tempfile
import time

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OLD_PROFILE = "e2-demo-field-eng"
NEW_PROFILE = "fe-sandbox-felix-demo-sandbox"
OLD_HOST = "https://e2-demo-field-eng.cloud.databricks.com"
NEW_HOST = "https://fe-sandbox-felix-demo-sandbox.cloud.databricks.com"
OLD_WAREHOUSE_ID = "862f1d757f0424f7"
NEW_WAREHOUSE_ID = "8af6100313039ba2"
OLD_CATALOG = "felix_demo_sandbox_catalog"
NEW_CATALOG = "innovation_factory_catalog"
STATE_FILE = os.path.join(os.path.dirname(__file__), "migration_state.json")
TEMP_DIR = "/tmp/migration_volumes"
PARENT_PATH = "/Workspace/Users/felix.mutzl@databricks.com"

VOLUME_MAPPINGS = [
    # (old_catalog, old_schema, old_volume, new_schema, new_volume)
    ("innovation_factory_catalog", "adtech_intelligence", "customer_relations_docs", "adtech_intelligence", "customer_relations_docs"),
    ("innovation_factory_catalog", "adtech_intelligence", "issue_resolution_docs", "adtech_intelligence", "issue_resolution_docs"),
    ("innovation_factory_catalog", "hb_product_center", "images", "hb_product_center", "images"),
    ("innovation_factory_catalog", "hb_product_center", "quality_documents", "hb_product_center", "quality_documents"),
    ("innovation_factory_catalog", "mac", "raw_data", "mac", "raw_data"),
    ("saschas", "image_similarity", "images", "image_similarity", "images"),
]

# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"completed_phases": [], "resources": {}}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_token(profile):
    """Get an auth token for a Databricks CLI profile."""
    result = subprocess.run(
        ["databricks", "auth", "token", "--profile", profile],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Auth failed for profile {profile}: {result.stderr[:300]}")
    return json.loads(result.stdout)["access_token"]


def api_request(profile, method, path, json_body=None):
    """Generic REST API call via the Databricks CLI."""
    cmd = ["databricks", "api", method.lower(), path, "--profile", profile]
    if json_body:
        cmd.extend(["--json", json.dumps(json_body)])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        print("  API TIMEOUT")
        return None
    if result.returncode != 0:
        print(f"  API ERROR: {result.stderr[:500]}")
        return None
    if result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"  Could not parse response: {result.stdout[:300]}")
            return None
    return {}


def execute_sql(profile, warehouse_id, statement, max_poll=300):
    """Execute SQL via the Statement Execution API with polling."""
    payload = {
        "warehouse_id": warehouse_id,
        "statement": statement,
        "wait_timeout": "50s",
    }
    result = subprocess.run(
        ["databricks", "api", "post", "/api/2.0/sql/statements",
         "--json", json.dumps(payload),
         "--profile", profile],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        print(f"  SQL CLI ERROR: {result.stderr[:500]}")
        return {"status": {"state": "FAILED"}}
    resp = json.loads(result.stdout)
    state = resp.get("status", {}).get("state", "UNKNOWN")

    statement_id = resp.get("statement_id")
    elapsed = 0
    while state in ("PENDING", "RUNNING") and elapsed < max_poll and statement_id:
        time.sleep(5)
        elapsed += 5
        poll_result = subprocess.run(
            ["databricks", "api", "get", f"/api/2.0/sql/statements/{statement_id}",
             "--profile", profile],
            capture_output=True, text=True, timeout=30,
        )
        if poll_result.returncode == 0:
            resp = json.loads(poll_result.stdout)
            state = resp.get("status", {}).get("state", "UNKNOWN")

    if state == "FAILED":
        err = resp.get("status", {}).get("error", {}).get("message", "Unknown error")
        print(f"  SQL FAILED: {err[:300]}")
    return resp


def list_volume_files_recursive(profile, catalog, schema, volume, prefix=""):
    """Recursively list files in a UC volume via the Files API."""
    path = f"/Volumes/{catalog}/{schema}/{volume}"
    if prefix:
        path = f"{path}/{prefix}"
    resp = api_request(profile, "GET", f"/api/2.0/fs/directories{path}")
    if resp is None:
        return []
    contents = resp.get("contents", [])
    files = []
    for item in contents:
        item_path = item.get("path", "")
        # Relative path within the volume
        vol_root = f"/Volumes/{catalog}/{schema}/{volume}/"
        rel = item_path[len(vol_root):] if item_path.startswith(vol_root) else item_path
        if item.get("is_directory", False):
            files.extend(list_volume_files_recursive(profile, catalog, schema, volume, prefix=rel))
        else:
            files.append(rel)
    return files


# ---------------------------------------------------------------------------
# Phase 0: Pre-flight Checks
# ---------------------------------------------------------------------------

def phase_0_preflight(state):
    """Pre-flight Checks"""
    print("  Checking CLI auth for OLD profile...")
    try:
        tok_old = get_token(OLD_PROFILE)
        print(f"    OLD profile OK (token starts with {tok_old[:10]}...)")
    except Exception as e:
        print(f"    FAIL: {e}")
        return

    print("  Checking CLI auth for NEW profile...")
    try:
        tok_new = get_token(NEW_PROFILE)
        print(f"    NEW profile OK (token starts with {tok_new[:10]}...)")
    except Exception as e:
        print(f"    FAIL: {e}")
        return

    print("  Checking warehouse on new workspace...")
    wh = api_request(NEW_PROFILE, "GET", f"/api/2.0/sql/warehouses/{NEW_WAREHOUSE_ID}")
    if wh and wh.get("id"):
        print(f"    Warehouse '{wh.get('name', 'unknown')}' found, state={wh.get('state', 'unknown')}")
    else:
        print("    WARNING: Could not verify warehouse")

    print("  Checking catalog on new workspace...")
    cat_resp = execute_sql(NEW_PROFILE, NEW_WAREHOUSE_ID, f"SHOW CATALOGS LIKE '{NEW_CATALOG}'")
    cat_state = cat_resp.get("status", {}).get("state", "UNKNOWN")
    if cat_state == "SUCCEEDED":
        rows = cat_resp.get("result", {}).get("data_array", [])
        if rows:
            print(f"    Catalog '{NEW_CATALOG}' exists")
        else:
            print(f"    WARNING: Catalog '{NEW_CATALOG}' not found")
    else:
        print(f"    Catalog check: {cat_state}")

    print("  Detecting budget policy (non-critical)...")
    bp = api_request(NEW_PROFILE, "GET", "/api/2.0/settings/types/shield-default-budget-policy-id/names/default")
    if bp and bp.get("setting", {}).get("typed_value"):
        print(f"    Budget policy found: {bp}")
        state["resources"]["budget_policy"] = bp
    else:
        print("    No budget policy detected (OK)")

    print("  Pre-flight checks complete.")


# ---------------------------------------------------------------------------
# Phase 1: Create Schemas
# ---------------------------------------------------------------------------

def phase_1_schemas(state):
    """Create Schemas"""
    schemas = [
        f"CREATE SCHEMA IF NOT EXISTS {NEW_CATALOG}.adtech_intelligence",
        f"CREATE SCHEMA IF NOT EXISTS {NEW_CATALOG}.hb_product_center",
        f"CREATE SCHEMA IF NOT EXISTS {NEW_CATALOG}.mac",
        f"CREATE SCHEMA IF NOT EXISTS {NEW_CATALOG}.image_similarity",
    ]
    for stmt in schemas:
        schema_name = stmt.split(".")[-1]
        print(f"  Creating schema {schema_name}...")
        resp = execute_sql(NEW_PROFILE, NEW_WAREHOUSE_ID, stmt)
        sql_state = resp.get("status", {}).get("state", "UNKNOWN")
        print(f"    -> {sql_state}")


# ---------------------------------------------------------------------------
# Phase 2: Create Volumes
# ---------------------------------------------------------------------------

def phase_2_volumes(state):
    """Create Volumes"""
    volumes = [
        f"CREATE VOLUME IF NOT EXISTS {NEW_CATALOG}.adtech_intelligence.customer_relations_docs",
        f"CREATE VOLUME IF NOT EXISTS {NEW_CATALOG}.adtech_intelligence.issue_resolution_docs",
        f"CREATE VOLUME IF NOT EXISTS {NEW_CATALOG}.hb_product_center.images",
        f"CREATE VOLUME IF NOT EXISTS {NEW_CATALOG}.hb_product_center.quality_documents",
        f"CREATE VOLUME IF NOT EXISTS {NEW_CATALOG}.mac.raw_data",
        f"CREATE VOLUME IF NOT EXISTS {NEW_CATALOG}.image_similarity.images",
    ]
    for stmt in volumes:
        vol_name = stmt.split(".")[-1]
        print(f"  Creating volume {vol_name}...")
        resp = execute_sql(NEW_PROFILE, NEW_WAREHOUSE_ID, stmt)
        sql_state = resp.get("status", {}).get("state", "UNKNOWN")
        print(f"    -> {sql_state}")


# ---------------------------------------------------------------------------
# Phase 3: Upload Volume Files
# ---------------------------------------------------------------------------

def phase_3_upload_volumes(state):
    """Upload Volume Files"""
    os.makedirs(TEMP_DIR, exist_ok=True)
    total_uploaded = 0
    total_failed = 0

    for old_cat, old_schema, old_volume, new_schema, new_volume in VOLUME_MAPPINGS:
        print(f"\n  --- {old_cat}.{old_schema}.{old_volume} -> {NEW_CATALOG}.{new_schema}.{new_volume} ---")

        # List files from old workspace
        print(f"  Listing files from old workspace...")
        files = list_volume_files_recursive(OLD_PROFILE, old_cat, old_schema, old_volume)
        if not files:
            print(f"    No files found (or listing failed). Trying CLI fallback...")
            # Fallback: use databricks fs ls
            ls_result = subprocess.run(
                ["databricks", "fs", "ls",
                 f"dbfs:/Volumes/{old_cat}/{old_schema}/{old_volume}",
                 "--profile", OLD_PROFILE],
                capture_output=True, text=True, timeout=60,
            )
            if ls_result.returncode == 0 and ls_result.stdout.strip():
                for line in ls_result.stdout.strip().split("\n"):
                    parts = line.strip().split()
                    if len(parts) >= 1:
                        fname = parts[-1]
                        if fname and not fname.endswith("/"):
                            files.append(fname)
                        elif fname and fname.endswith("/"):
                            # It's a directory; we'll do a simple listing
                            subdir_name = fname.rstrip("/")
                            sub_result = subprocess.run(
                                ["databricks", "fs", "ls",
                                 f"dbfs:/Volumes/{old_cat}/{old_schema}/{old_volume}/{subdir_name}",
                                 "--profile", OLD_PROFILE],
                                capture_output=True, text=True, timeout=60,
                            )
                            if sub_result.returncode == 0:
                                for sub_line in sub_result.stdout.strip().split("\n"):
                                    sub_parts = sub_line.strip().split()
                                    if sub_parts:
                                        sub_name = sub_parts[-1]
                                        if sub_name and not sub_name.endswith("/"):
                                            files.append(f"{subdir_name}/{sub_name}")
            if not files:
                print(f"    Still no files found. Skipping.")
                continue

        print(f"  Found {len(files)} file(s)")

        for file_path in files:
            local_dir = os.path.join(TEMP_DIR, old_schema, old_volume, os.path.dirname(file_path))
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(TEMP_DIR, old_schema, old_volume, file_path)

            old_dbfs = f"dbfs:/Volumes/{old_cat}/{old_schema}/{old_volume}/{file_path}"
            new_dbfs = f"dbfs:/Volumes/{NEW_CATALOG}/{new_schema}/{new_volume}/{file_path}"

            # Download
            dl = subprocess.run(
                ["databricks", "fs", "cp", old_dbfs, local_path, "--profile", OLD_PROFILE],
                capture_output=True, text=True, timeout=300,
            )
            if dl.returncode != 0:
                print(f"    DOWNLOAD FAIL: {file_path} -> {dl.stderr[:200]}")
                total_failed += 1
                continue

            # Upload
            ul = subprocess.run(
                ["databricks", "fs", "cp", local_path, new_dbfs, "--profile", NEW_PROFILE],
                capture_output=True, text=True, timeout=300,
            )
            if ul.returncode != 0:
                print(f"    UPLOAD FAIL: {file_path} -> {ul.stderr[:200]}")
                total_failed += 1
                continue

            print(f"    OK: {file_path}")
            total_uploaded += 1

    print(f"\n  Volume upload complete: {total_uploaded} uploaded, {total_failed} failed")
    state["resources"]["volume_files_uploaded"] = total_uploaded
    state["resources"]["volume_files_failed"] = total_failed


# ---------------------------------------------------------------------------
# Phase 4: Seed UC Tables (Small - via SQL)
# ---------------------------------------------------------------------------

def phase_4_seed_small_tables(state):
    """Seed UC Tables (Small - via SQL)"""

    # ---- HB Product Center tables ----
    print("\n  === Creating HB Product Center tables ===")
    hb_ddls = [
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.hb_product_center.hb_products (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            sku STRING, style_name STRING, color STRING, color_code STRING,
            size STRING, category STRING, collection STRING, season STRING,
            material STRING, price DOUBLE, status STRING, country_of_origin STRING,
            supplier_name STRING, created_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.hb_product_center.hb_recognition_jobs (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            job_type STRING, status STRING, user_role STRING, submitted_by STRING,
            image_count INT, completed_count INT, created_at TIMESTAMP, completed_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.hb_product_center.hb_quality_inspections (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            product_id BIGINT, batch_number STRING, inspector STRING,
            manufacturing_partner STRING, overall_score DOUBLE, status STRING,
            notes STRING, created_at TIMESTAMP, completed_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.hb_product_center.hb_quality_defects (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            inspection_id BIGINT, defect_type STRING, severity STRING,
            location_description STRING, confidence_score DOUBLE,
            image_url STRING, created_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.hb_product_center.hb_auth_verifications (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            product_id BIGINT, requester_type STRING, requester_name STRING,
            requester_email STRING, status STRING, confidence_score DOUBLE,
            verification_method STRING, image_url STRING, region STRING,
            notes STRING, created_at TIMESTAMP, completed_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.hb_product_center.hb_auth_alerts (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            verification_id BIGINT, alert_type STRING, severity STRING,
            region STRING, description STRING, investigated_by STRING,
            resolution STRING, created_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.hb_product_center.hb_supply_chain_events (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            product_id BIGINT, event_type STRING, location STRING,
            partner_name STRING, country STRING, details STRING,
            event_date TIMESTAMP, created_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.hb_product_center.hb_sustainability_metrics (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            product_id BIGINT, carbon_footprint_kg DOUBLE, water_usage_liters DOUBLE,
            recycled_content_pct DOUBLE, organic_material_pct DOUBLE,
            certifications STRING, compliance_status STRING,
            last_audit_date DATE, created_at TIMESTAMP
        )""",
    ]
    for ddl in hb_ddls:
        tname = ddl.split("IF NOT EXISTS")[1].split("(")[0].strip()
        print(f"    Creating {tname}...")
        resp = execute_sql(NEW_PROFILE, NEW_WAREHOUSE_ID, ddl)
        print(f"      -> {resp.get('status', {}).get('state', 'UNKNOWN')}")

    # Seed HB data using the existing seed script
    print("\n  === Seeding HB Product Center data ===")
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from seed_uc_hb_data import build_sql
        stmts = build_sql()
        for i, stmt in enumerate(stmts):
            tname = stmt.split("INTO")[1].split("(")[0].strip() if "INTO" in stmt else f"Statement {i+1}"
            print(f"    Inserting into {tname}...")
            resp = execute_sql(NEW_PROFILE, NEW_WAREHOUSE_ID, stmt, max_poll=300)
            print(f"      -> {resp.get('status', {}).get('state', 'UNKNOWN')}")
    except ImportError:
        print("    WARNING: Could not import seed_uc_hb_data. Skipping HB data seed.")
    except Exception as e:
        print(f"    ERROR during HB seed: {e}")

    # Additional HB tables that build_sql doesn't cover
    print("\n  === Creating additional HB tables ===")
    extra_hb = [
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.hb_product_center.hb_recognition_results (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            job_id BIGINT, product_id BIGINT, confidence_score DOUBLE,
            image_url STRING, status STRING, created_at TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.hb_product_center.product_stock (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            product_id BIGINT, warehouse_location STRING, quantity INT,
            last_updated TIMESTAMP
        )""",
    ]
    for ddl in extra_hb:
        tname = ddl.split("IF NOT EXISTS")[1].split("(")[0].strip()
        print(f"    Creating {tname}...")
        resp = execute_sql(NEW_PROFILE, NEW_WAREHOUSE_ID, ddl)
        print(f"      -> {resp.get('status', {}).get('state', 'UNKNOWN')}")

    # ---- MAC / MOL ASM Cockpit tables (empty, data via Phase 5) ----
    print("\n  === Creating MAC (MOL ASM Cockpit) tables ===")
    mac_ddls = [
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.mac.stations (
            id INT, station_code STRING, name STRING, city STRING,
            region STRING, country STRING, latitude DOUBLE, longitude DOUBLE,
            station_type STRING, has_fresh_corner BOOLEAN, has_ev_charging BOOLEAN,
            num_pumps INT, shop_area_sqm DOUBLE
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.mac.fuel_sales (
            station_id INT, sale_date DATE, fuel_type STRING,
            volume_liters DOUBLE, revenue DOUBLE, unit_price DOUBLE, margin DOUBLE
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.mac.nonfuel_sales (
            station_id INT, sale_date DATE, category STRING,
            quantity INT, revenue DOUBLE, margin DOUBLE
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.mac.workforce_shifts (
            station_id INT, shift_date DATE, shift_type STRING,
            planned_headcount INT, actual_headcount INT, overtime_hours DOUBLE
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.mac.inventory (
            station_id INT, record_date DATE, product_category STRING,
            stock_level INT, reorder_point INT, spoilage_count INT,
            stock_out_events INT, delivery_scheduled BOOLEAN
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.mac.competitor_prices (
            station_id INT, price_date DATE, competitor_name STRING,
            fuel_type STRING, price_per_liter DOUBLE
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.mac.price_history (
            station_id INT, price_date DATE, fuel_type STRING,
            price_per_liter DOUBLE, cost_per_liter DOUBLE
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.mac.loyalty_metrics (
            station_id INT, month DATE, active_members INT,
            new_signups INT, points_redeemed INT, loyalty_revenue_share DOUBLE
        )""",
        f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.mac.anomaly_alerts (
            id INT, station_id INT, metric_type STRING, severity STRING,
            title STRING, description STRING, suggested_action STRING,
            status STRING, detected_at TIMESTAMP
        )""",
    ]
    for ddl in mac_ddls:
        tname = ddl.split("IF NOT EXISTS")[1].split("(")[0].strip()
        print(f"    Creating {tname}...")
        resp = execute_sql(NEW_PROFILE, NEW_WAREHOUSE_ID, ddl)
        print(f"      -> {resp.get('status', {}).get('state', 'UNKNOWN')}")

    # ---- AdTech Intelligence tables (attempt export from old workspace) ----
    print("\n  === AdTech Intelligence UC tables ===")
    adtech_tables = [
        "advertisers", "campaigns", "ad_inventory", "placements",
        "performance_metrics", "anomaly_rules", "anomalies", "issues",
        "customer_contracts",
    ]
    for table in adtech_tables:
        print(f"\n    Migrating {table}...")
        # Try to SELECT from old workspace
        # Old workspace uses innovation_factory_catalog too
        old_catalog = "innovation_factory_catalog"
        select_sql = f"SELECT * FROM {old_catalog}.adtech_intelligence.{table}"
        print(f"      Querying old workspace...")
        old_resp = execute_sql(OLD_PROFILE, OLD_WAREHOUSE_ID, select_sql, max_poll=120)
        old_state = old_resp.get("status", {}).get("state", "UNKNOWN")

        if old_state != "SUCCEEDED":
            print(f"      Table not found on old workspace or query failed ({old_state}). Skipping.")
            print(f"      NOTE: This table will need to be seeded separately (e.g., via Lakebase auto-seed on app startup).")
            continue

        # Get schema and data
        columns = old_resp.get("manifest", {}).get("schema", {}).get("columns", [])
        data = old_resp.get("result", {}).get("data_array", [])
        if not columns or not data:
            print(f"      No data or schema returned. Skipping.")
            continue

        col_names = [c["name"] for c in columns]
        col_types = [c.get("type_name", "STRING") for c in columns]
        print(f"      Got {len(data)} rows, {len(col_names)} columns")

        # Create table on new workspace
        col_defs = []
        for cname, ctype in zip(col_names, col_types):
            # Map Databricks type names to SQL types
            type_map = {
                "INT": "INT", "BIGINT": "BIGINT", "LONG": "BIGINT",
                "DOUBLE": "DOUBLE", "FLOAT": "FLOAT", "DECIMAL": "DECIMAL(38,10)",
                "STRING": "STRING", "BOOLEAN": "BOOLEAN",
                "DATE": "DATE", "TIMESTAMP": "TIMESTAMP",
                "BINARY": "BINARY", "ARRAY": "STRING", "MAP": "STRING", "STRUCT": "STRING",
            }
            sql_type = type_map.get(ctype.upper(), "STRING")
            col_defs.append(f"`{cname}` {sql_type}")

        create_sql = f"CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.adtech_intelligence.{table} ({', '.join(col_defs)})"
        print(f"      Creating table...")
        cr = execute_sql(NEW_PROFILE, NEW_WAREHOUSE_ID, create_sql)
        print(f"        -> {cr.get('status', {}).get('state', 'UNKNOWN')}")

        # Insert data in batches
        batch_size = 500
        for batch_start in range(0, len(data), batch_size):
            batch = data[batch_start:batch_start + batch_size]
            value_rows = []
            for row in batch:
                vals = []
                for val, ctype in zip(row, col_types):
                    if val is None:
                        vals.append("NULL")
                    elif ctype.upper() in ("INT", "BIGINT", "LONG", "DOUBLE", "FLOAT", "DECIMAL"):
                        vals.append(str(val))
                    elif ctype.upper() == "BOOLEAN":
                        vals.append(str(val).lower())
                    else:
                        vals.append("'" + str(val).replace("'", "''") + "'")
                value_rows.append(f"({', '.join(vals)})")

            insert_sql = f"INSERT INTO {NEW_CATALOG}.adtech_intelligence.{table} VALUES\n" + ",\n".join(value_rows)
            ir = execute_sql(NEW_PROFILE, NEW_WAREHOUSE_ID, insert_sql, max_poll=120)
            ir_state = ir.get("status", {}).get("state", "UNKNOWN")
            print(f"      Inserted batch {batch_start}-{batch_start+len(batch)}: {ir_state}")

    print("\n  Phase 4 complete.")


# ---------------------------------------------------------------------------
# Phase 5: Seed UC Tables (Large - via PySpark notebook)
# ---------------------------------------------------------------------------

def phase_5_seed_large_tables(state):
    """Seed UC Tables (Large - via PySpark)"""
    notebook_path = os.path.join(os.path.dirname(__file__), "seed_all_uc_notebook.py")
    if not os.path.exists(notebook_path):
        print(f"  WARNING: Notebook not found at {notebook_path}")
        print("  Skipping notebook upload.")
        return

    # Upload notebook to new workspace
    print("  Uploading seed notebook to new workspace...")
    upload_result = subprocess.run(
        ["databricks", "workspace", "import", notebook_path,
         f"{PARENT_PATH}/seed_all_uc_notebook",
         "--format", "SOURCE", "--language", "PYTHON",
         "--profile", NEW_PROFILE, "--overwrite"],
        capture_output=True, text=True, timeout=60,
    )
    if upload_result.returncode != 0:
        print(f"  Upload failed: {upload_result.stderr[:500]}")
        print("  Manual step: Upload scripts/seed_all_uc_notebook.py to the new workspace.")
        return
    print("  Notebook uploaded successfully.")

    # Create and run a job (try serverless first)
    print("  Creating seed job...")
    job_body = {
        "name": "Migration: Seed UC Tables",
        "tasks": [{
            "task_key": "seed_uc",
            "notebook_task": {
                "notebook_path": f"{PARENT_PATH}/seed_all_uc_notebook",
                "source": "WORKSPACE",
            },
            "environment_key": "default",
        }],
        "environments": [{"environment_key": "default", "spec": {"client": "1"}}],
    }

    job_resp = api_request(NEW_PROFILE, "POST", "/api/2.0/jobs/create", job_body)
    if not job_resp or not job_resp.get("job_id"):
        print("  Serverless job creation failed. Trying with new_cluster...")
        job_body = {
            "name": "Migration: Seed UC Tables",
            "tasks": [{
                "task_key": "seed_uc",
                "notebook_task": {
                    "notebook_path": f"{PARENT_PATH}/seed_all_uc_notebook",
                    "source": "WORKSPACE",
                },
                "new_cluster": {
                    "spark_version": "15.4.x-scala2.12",
                    "node_type_id": "i3.xlarge",
                    "num_workers": 0,
                    "spark_conf": {"spark.master": "local[*]"},
                },
                "timeout_seconds": 3600,
            }],
        }
        job_resp = api_request(NEW_PROFILE, "POST", "/api/2.0/jobs/create", job_body)
        if not job_resp or not job_resp.get("job_id"):
            print("  Job creation failed. Please create and run the notebook job manually.")
            print(f"  Notebook path: {PARENT_PATH}/seed_all_uc_notebook")
            return

    job_id = job_resp["job_id"]
    print(f"  Job created: {job_id}")
    state["resources"]["seed_job_id"] = job_id

    # Run the job
    print("  Starting job run...")
    run_resp = api_request(NEW_PROFILE, "POST", "/api/2.0/jobs/run-now", {"job_id": job_id})
    if not run_resp or not run_resp.get("run_id"):
        print("  Could not start job run. Please run manually.")
        print(f"  Job ID: {job_id}")
        return

    run_id = run_resp["run_id"]
    print(f"  Run started: {run_id}")
    print(f"  Monitor at: {NEW_HOST}/#job/{job_id}/run/{run_id}")

    # Poll for completion
    print("  Waiting for job completion (max 30 min)...")
    max_wait = 1800
    elapsed = 0
    while elapsed < max_wait:
        time.sleep(30)
        elapsed += 30
        run_status = api_request(NEW_PROFILE, "GET", f"/api/2.0/jobs/runs/get?run_id={run_id}")
        if not run_status:
            continue
        life_cycle = run_status.get("state", {}).get("life_cycle_state", "UNKNOWN")
        result_state = run_status.get("state", {}).get("result_state", "")
        print(f"    [{elapsed}s] {life_cycle} {result_state}")
        if life_cycle in ("TERMINATED", "SKIPPED", "INTERNAL_ERROR"):
            if result_state == "SUCCESS":
                print("  Job completed successfully!")
            else:
                print(f"  Job ended with state: {result_state}")
                msg = run_status.get("state", {}).get("state_message", "")
                if msg:
                    print(f"  Message: {msg[:500]}")
            break
    else:
        print("  Job still running after 30 minutes. Check manually.")
        print(f"  Run URL: {NEW_HOST}/#job/{job_id}/run/{run_id}")


# ---------------------------------------------------------------------------
# Phase 6: Create Image Similarity Resources
# ---------------------------------------------------------------------------

def phase_6_image_similarity(state):
    """Create Image Similarity Resources"""

    # Create the embeddings table with CDF
    print("  Creating image_embeddings table...")
    create_sql = f"""CREATE TABLE IF NOT EXISTS {NEW_CATALOG}.image_similarity.image_embeddings (
        id STRING NOT NULL,
        image_uri STRING NOT NULL,
        file_name STRING,
        category STRING,
        embedding ARRAY<FLOAT>,
        embedding_dim INT,
        ingested_at TIMESTAMP
    ) TBLPROPERTIES (delta.enableChangeDataFeed = true)"""
    resp = execute_sql(NEW_PROFILE, NEW_WAREHOUSE_ID, create_sql)
    print(f"    -> {resp.get('status', {}).get('state', 'UNKNOWN')}")

    # Create VS endpoint
    print("  Creating vector search endpoint...")
    vs_resp = api_request(NEW_PROFILE, "POST", "/api/2.0/vector-search/endpoints", {
        "name": "image_similarity_endpoint",
        "endpoint_type": "STANDARD",
    })
    if vs_resp and vs_resp.get("name"):
        print(f"    Endpoint creation initiated: {vs_resp.get('name')}")
        state["resources"]["vs_endpoint_name"] = vs_resp.get("name", "image_similarity_endpoint")
    elif vs_resp and "already exists" in str(vs_resp):
        print("    Endpoint already exists.")
        state["resources"]["vs_endpoint_name"] = "image_similarity_endpoint"
    else:
        print(f"    Endpoint creation response: {vs_resp}")
        state["resources"]["vs_endpoint_name"] = "image_similarity_endpoint"

    # Wait for endpoint to become ONLINE
    print("  Waiting for endpoint to become ONLINE (max 10 min)...")
    max_wait = 600
    elapsed = 0
    endpoint_online = False
    while elapsed < max_wait:
        time.sleep(15)
        elapsed += 15
        ep_status = api_request(NEW_PROFILE, "GET", "/api/2.0/vector-search/endpoints/image_similarity_endpoint")
        if ep_status:
            ep_state = ep_status.get("endpoint_status", {}).get("state", ep_status.get("status", "UNKNOWN"))
            print(f"    [{elapsed}s] Endpoint state: {ep_state}")
            if ep_state == "ONLINE":
                endpoint_online = True
                break
        else:
            print(f"    [{elapsed}s] Could not get endpoint status")

    if endpoint_online:
        print("  Endpoint is ONLINE!")
        state["resources"]["vs_endpoint_status"] = "ONLINE"
    else:
        print("  Endpoint not yet ONLINE. It may still be provisioning.")
        state["resources"]["vs_endpoint_status"] = "PROVISIONING"

    print("\n  NEXT STEPS:")
    print("  Run `python scripts/setup_vector_search.py` after updating its constants")
    print("  to use the new catalog/workspace. The script will compute CLIP embeddings")
    print("  and create the VS index.")


# ---------------------------------------------------------------------------
# Phase 7: Create UC Function
# ---------------------------------------------------------------------------

def phase_7_uc_function(state):
    """Create UC Function"""
    create_func_sql = f"""CREATE OR REPLACE FUNCTION {NEW_CATALOG}.hb_product_center.identify_product(
  image_description STRING COMMENT 'A textual description of the product to identify, including visual features like color, style, material, category'
)
RETURNS TABLE (
  product_id BIGINT,
  sku STRING,
  style_name STRING,
  color STRING,
  category STRING,
  collection STRING,
  material STRING,
  price DOUBLE,
  confidence STRING
)
COMMENT 'Identifies Hugo Boss products based on visual description. Returns matching products from the catalog with confidence levels.'
RETURN
  SELECT
    id as product_id,
    sku,
    style_name,
    color,
    category,
    collection,
    material,
    price,
    CASE
      WHEN LOWER(image_description) LIKE CONCAT('%', LOWER(style_name), '%')
        OR LOWER(image_description) LIKE CONCAT('%', LOWER(category), '%')
      THEN 'high'
      WHEN LOWER(image_description) LIKE CONCAT('%', LOWER(color), '%')
        OR LOWER(image_description) LIKE CONCAT('%', LOWER(material), '%')
      THEN 'medium'
      ELSE 'low'
    END as confidence
  FROM {NEW_CATALOG}.hb_product_center.hb_products
  WHERE
    LOWER(image_description) LIKE CONCAT('%', LOWER(style_name), '%')
    OR LOWER(image_description) LIKE CONCAT('%', LOWER(category), '%')
    OR LOWER(image_description) LIKE CONCAT('%', LOWER(color), '%')
    OR LOWER(image_description) LIKE CONCAT('%', LOWER(material), '%')
    OR LOWER(image_description) LIKE CONCAT('%', LOWER(collection), '%')
  ORDER BY
    CASE
      WHEN LOWER(image_description) LIKE CONCAT('%', LOWER(style_name), '%') THEN 1
      WHEN LOWER(image_description) LIKE CONCAT('%', LOWER(category), '%') THEN 2
      WHEN LOWER(image_description) LIKE CONCAT('%', LOWER(color), '%') THEN 3
      ELSE 4
    END
  LIMIT 5"""

    print("  Creating UC function identify_product...")
    resp = execute_sql(NEW_PROFILE, NEW_WAREHOUSE_ID, create_func_sql)
    func_state = resp.get("status", {}).get("state", "UNKNOWN")
    print(f"    -> {func_state}")

    # Test the function
    print("  Testing UC function...")
    test_sql = f"SELECT * FROM {NEW_CATALOG}.hb_product_center.identify_product('dark blue wool suit')"
    test_resp = execute_sql(NEW_PROFILE, NEW_WAREHOUSE_ID, test_sql)
    test_state = test_resp.get("status", {}).get("state", "UNKNOWN")
    print(f"    Test result: {test_state}")
    if test_state == "SUCCEEDED":
        data = test_resp.get("result", {}).get("data_array", [])
        print(f"    Returned {len(data)} rows")
        for row in data[:3]:
            print(f"      -> {row}")
    else:
        print("    Test failed - function may work once HB products table is populated.")


# ---------------------------------------------------------------------------
# Phase 8: Create Lakebase
# ---------------------------------------------------------------------------

def phase_8_lakebase(state):
    """Create Lakebase"""
    print("  Creating Lakebase database via REST API...")
    lb_resp = api_request(NEW_PROFILE, "POST", "/api/2.0/lakebase/databases", {
        "name": "innovation-factory",
        "compute_type": "autoscale",
    })

    if lb_resp and (lb_resp.get("name") or lb_resp.get("id")):
        print(f"  Lakebase creation initiated: {json.dumps(lb_resp, indent=2)[:500]}")
        state["resources"]["lakebase"] = lb_resp

        # Extract connection info if available
        pghost = lb_resp.get("connection_info", {}).get("host", "")
        pguser = lb_resp.get("connection_info", {}).get("user", "")
        endpoint_name = lb_resp.get("endpoint_name", "")
        if pghost:
            state["resources"]["lakebase_pghost"] = pghost
        if pguser:
            state["resources"]["lakebase_pguser"] = pguser
        if endpoint_name:
            state["resources"]["lakebase_endpoint_name"] = endpoint_name

        print(f"  PGHOST: {pghost or 'not yet available'}")
        print(f"  PGUSER: {pguser or 'not yet available'}")
        print(f"  ENDPOINT_NAME: {endpoint_name or 'not yet available'}")
    else:
        print(f"  Lakebase creation response: {lb_resp}")
        print("\n  MANUAL STEPS:")
        print("  Use Databricks CLI or MCP to create Lakebase autoscale instance:")
        print("    Name: innovation-factory")
        print("    Type: autoscale")
        print("\n  After creation, capture:")
        print("    - PGHOST")
        print("    - PGUSER (Service Principal client ID)")
        print("    - ENDPOINT_NAME")
        print("  The app auto-seeds all 50+ Lakebase tables on startup.")
        print("  Update databricks.yml and app.yml with the new values.")


# ---------------------------------------------------------------------------
# Phase 9: Create Genie Spaces
# ---------------------------------------------------------------------------

def phase_9_genie_spaces(state):
    """Create Genie Spaces"""

    # 1. HB Supply Chain Intelligence
    print("  Creating Genie Space: HB Supply Chain Intelligence...")
    sc_body = {
        "display_name": "HB Supply Chain Intelligence",
        "description": "Supply chain analytics for Hugo Boss products - track events, logistics, sustainability metrics across the global supply chain.",
        "warehouse_id": NEW_WAREHOUSE_ID,
        "table_identifiers": [
            f"{NEW_CATALOG}.hb_product_center.hb_supply_chain_events",
            f"{NEW_CATALOG}.hb_product_center.hb_products",
            f"{NEW_CATALOG}.hb_product_center.hb_sustainability_metrics",
        ],
        "sample_questions": [
            {"question": "What are the top 10 supply chain partners by event count?"},
            {"question": "Show the distribution of supply chain events by type"},
            {"question": "Which countries have the most supply chain activity?"},
            {"question": "What is the average carbon footprint by product category?"},
            {"question": "Show products with non-compliant sustainability status"},
            {"question": "What is the timeline of supply chain events over the last 6 months?"},
            {"question": "Which products have the highest water usage?"},
            {"question": "Show the recycled content percentage distribution across products"},
        ],
    }
    sc_resp = api_request(NEW_PROFILE, "POST", "/api/2.0/genie/spaces", sc_body)
    if sc_resp and (sc_resp.get("space_id") or sc_resp.get("id")):
        sc_id = sc_resp.get("space_id", sc_resp.get("id"))
        print(f"    Created: {sc_id}")
        state["resources"]["hb_sc_genie_id"] = sc_id
    else:
        print(f"    Response: {sc_resp}")

    # 2. HB Authenticity & Quality Control
    print("  Creating Genie Space: HB Authenticity & Quality Control...")
    aq_body = {
        "display_name": "HB Authenticity & Quality Control",
        "description": "Authenticity verification and quality control analytics for Hugo Boss products.",
        "warehouse_id": NEW_WAREHOUSE_ID,
        "table_identifiers": [
            f"{NEW_CATALOG}.hb_product_center.hb_auth_verifications",
            f"{NEW_CATALOG}.hb_product_center.hb_auth_alerts",
            f"{NEW_CATALOG}.hb_product_center.hb_quality_inspections",
            f"{NEW_CATALOG}.hb_product_center.hb_quality_defects",
            f"{NEW_CATALOG}.hb_product_center.hb_products",
        ],
        "sample_questions": [
            {"question": "How many authenticity verifications were performed this month?"},
            {"question": "What percentage of verifications resulted in suspicious or counterfeit findings?"},
            {"question": "Show the distribution of quality inspection scores"},
            {"question": "What are the most common defect types?"},
            {"question": "Which manufacturing partners have the highest quality scores?"},
            {"question": "Show active authentication alerts by severity"},
            {"question": "What verification methods are most commonly used?"},
            {"question": "Which regions have the most authentication alerts?"},
        ],
    }
    aq_resp = api_request(NEW_PROFILE, "POST", "/api/2.0/genie/spaces", aq_body)
    if aq_resp and (aq_resp.get("space_id") or aq_resp.get("id")):
        aq_id = aq_resp.get("space_id", aq_resp.get("id"))
        print(f"    Created: {aq_id}")
        state["resources"]["hb_aq_genie_id"] = aq_id
    else:
        print(f"    Response: {aq_resp}")

    # 3. AdTech Intelligence Explorer
    print("  Creating Genie Space: AdTech Intelligence Explorer...")
    at_body = {
        "display_name": "AdTech Intelligence Explorer",
        "description": "Explore advertising technology data including advertisers, campaigns, inventory, performance metrics, anomalies, and customer contracts.",
        "warehouse_id": NEW_WAREHOUSE_ID,
        "table_identifiers": [
            f"{NEW_CATALOG}.adtech_intelligence.advertisers",
            f"{NEW_CATALOG}.adtech_intelligence.campaigns",
            f"{NEW_CATALOG}.adtech_intelligence.ad_inventory",
            f"{NEW_CATALOG}.adtech_intelligence.performance_metrics",
            f"{NEW_CATALOG}.adtech_intelligence.anomalies",
            f"{NEW_CATALOG}.adtech_intelligence.issues",
            f"{NEW_CATALOG}.adtech_intelligence.customer_contracts",
        ],
        "sample_questions": [
            {"question": "Which advertisers have the highest campaign budgets?"},
            {"question": "Show the distribution of campaigns by status"},
            {"question": "What is the average CTR across all active campaigns?"},
            {"question": "Show anomalies by severity level"},
            {"question": "Which campaigns have the most open issues?"},
            {"question": "What is the total contract value by advertiser?"},
            {"question": "Show the top performing campaigns by impressions"},
            {"question": "What are the most common issue categories?"},
        ],
    }
    at_resp = api_request(NEW_PROFILE, "POST", "/api/2.0/genie/spaces", at_body)
    if at_resp and (at_resp.get("space_id") or at_resp.get("id")):
        at_id = at_resp.get("space_id", at_resp.get("id"))
        print(f"    Created: {at_id}")
        state["resources"]["adtech_genie_id"] = at_id
    else:
        print(f"    Response: {at_resp}")


# ---------------------------------------------------------------------------
# Phase 10: Create Dashboards
# ---------------------------------------------------------------------------

def _counter(name, dataset, expr, display, title, x, y, w=2, h=3):
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": dataset, "fields": [{"name": expr, "expression": expr}], "disaggregated": False}}],
            "spec": {"version": 2, "widgetType": "counter", "encodings": {"value": {"fieldName": expr, "displayName": display}}},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def _bar(name, dataset, x_field, x_expr, y_field, y_expr, title, x, y, w=3, h=5):
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": dataset, "fields": [{"name": x_field, "expression": x_expr}, {"name": y_field, "expression": y_expr}], "disaggregated": False}}],
            "spec": {"version": 3, "widgetType": "bar", "encodings": {"x": {"fieldName": x_field, "scale": {"type": "categorical"}, "displayName": title.split(" by ")[-1] if " by " in title else x_field}, "y": {"fieldName": y_field, "scale": {"type": "quantitative"}, "displayName": "Count"}}},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def _pie(name, dataset, color_field, color_expr, angle_field, angle_expr, title, x, y, w=3, h=5):
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": dataset, "fields": [{"name": color_field, "expression": color_expr}, {"name": angle_field, "expression": angle_expr}], "disaggregated": False}}],
            "spec": {"version": 3, "widgetType": "pie", "encodings": {"angle": {"fieldName": angle_field, "displayName": "Count"}, "color": {"fieldName": color_field, "scale": {"type": "categorical"}, "displayName": title}}},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def _table_w(name, dataset, columns, x, y, w=6, h=6):
    fields = [{"name": c[0], "expression": f"`{c[0]}`"} for c in columns]
    cols = [{"fieldName": c[0], "displayName": c[1]} for c in columns]
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": dataset, "fields": fields, "disaggregated": True}}],
            "spec": {"version": 2, "widgetType": "table", "encodings": {"columns": cols}},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def _create_and_publish_dashboard(profile, name, dashboard_json, warehouse_id, parent_path):
    """Create and publish a dashboard, return dashboard_id."""
    serialized = json.dumps(dashboard_json)
    body = {
        "display_name": name,
        "parent_path": parent_path,
        "serialized_dashboard": serialized,
        "warehouse_id": warehouse_id,
    }
    resp = api_request(profile, "POST", "/api/2.0/lakeview/dashboards", body)
    if not resp or not resp.get("dashboard_id"):
        print(f"    FAIL creating dashboard '{name}': {resp}")
        return None
    did = resp["dashboard_id"]
    print(f"    Created: {name} -> {did}")

    # Publish
    pub = api_request(profile, "POST", f"/api/2.0/lakeview/dashboards/{did}/published", {
        "warehouse_id": warehouse_id,
        "embed_credentials": True,
    })
    if pub is not None:
        print(f"    Published: {did}")
    else:
        print(f"    Publish warning for {did}")
    return did


def phase_10_dashboards(state):
    """Create Dashboards"""
    SC = f"{NEW_CATALOG}.hb_product_center"

    # 1. HB Supply Chain Hub (imported definition)
    print("  Creating HB Supply Chain Intelligence dashboard...")
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from create_dashboards import SUPPLY_CHAIN_DASHBOARD, AUTH_QUALITY_DASHBOARD
        sc_id = _create_and_publish_dashboard(NEW_PROFILE, "HB Supply Chain Intelligence", SUPPLY_CHAIN_DASHBOARD, NEW_WAREHOUSE_ID, PARENT_PATH)
        if sc_id:
            state["resources"]["hb_sc_dashboard_id"] = sc_id
    except ImportError:
        print("    WARNING: Could not import from create_dashboards.py. Building inline...")
        supply_chain_dashboard = {
            "pages": [
                {
                    "name": "sc_overview",
                    "displayName": "Supply Chain Overview",
                    "layout": [
                        _counter("ctr-events", "ds_sc_events", "COUNT(`id`)", "Total Events", "Total Events", 0, 0),
                        _counter("ctr-countries", "ds_sc_events", "COUNT(DISTINCT `country`)", "Countries", "Countries", 2, 0),
                        _counter("ctr-partners", "ds_sc_events", "COUNT(DISTINCT `partner_name`)", "Partners", "Partners", 4, 0),
                        _bar("bar-by-type", "ds_sc_events", "event_type", "`event_type`", "COUNT(id)", "COUNT(`id`)", "Events by Type", 0, 3),
                        _bar("bar-by-country", "ds_sc_events", "country", "`country`", "COUNT(id)", "COUNT(`id`)", "Events by Country", 3, 3),
                        _bar("bar-timeline", "ds_sc_events", "month", 'DATE_TRUNC("MONTH", `event_date`)', "COUNT(id)", "COUNT(`id`)", "Events Over Time", 0, 8, w=6),
                        _table_w("tbl-partners", "ds_top_partners", [("partner_name", "Partner"), ("event_count", "Events"), ("countries", "Countries")], 0, 13),
                    ],
                },
                {
                    "name": "sustainability",
                    "displayName": "Sustainability",
                    "layout": [
                        _counter("ctr-carbon", "ds_sustainability", "AVG(`carbon_footprint_kg`)", "Avg Carbon (kg)", "Avg Carbon", 0, 0),
                        _counter("ctr-recycled", "ds_sustainability", "AVG(`recycled_content_pct`)", "Avg Recycled %", "Avg Recycled", 2, 0),
                        _counter("ctr-compliant", "ds_sustainability", "SUM(CASE WHEN `compliance_status` = 'compliant' THEN 1 ELSE 0 END)", "Compliant", "Compliant", 4, 0),
                        _bar("bar-carbon-cat", "ds_sustainability", "category", "`category`", "AVG(carbon_footprint_kg)", "AVG(`carbon_footprint_kg`)", "Carbon by Category", 0, 3),
                        _pie("pie-compliance", "ds_sustainability", "compliance_status", "`compliance_status`", "COUNT(id)", "COUNT(`id`)", "Compliance Status", 3, 3),
                    ],
                },
            ],
            "datasets": [
                {"name": "ds_sc_events", "displayName": "Supply Chain Events", "query": f"SELECT * FROM {SC}.hb_supply_chain_events"},
                {"name": "ds_sustainability", "displayName": "Sustainability", "query": f"SELECT s.*, p.category, p.style_name FROM {SC}.hb_sustainability_metrics s JOIN {SC}.hb_products p ON s.product_id = p.id"},
                {"name": "ds_top_partners", "displayName": "Top Partners", "query": f"SELECT partner_name, COUNT(*) as event_count, COUNT(DISTINCT country) as countries FROM {SC}.hb_supply_chain_events GROUP BY partner_name ORDER BY event_count DESC LIMIT 15"},
            ],
        }
        sc_id = _create_and_publish_dashboard(NEW_PROFILE, "HB Supply Chain Intelligence", supply_chain_dashboard, NEW_WAREHOUSE_ID, PARENT_PATH)
        if sc_id:
            state["resources"]["hb_sc_dashboard_id"] = sc_id

    # 2. HB Quality Control
    print("  Creating HB Authenticity & Quality Control dashboard...")
    try:
        from create_dashboards import AUTH_QUALITY_DASHBOARD
        aq_id = _create_and_publish_dashboard(NEW_PROFILE, "HB Authenticity & Quality Control", AUTH_QUALITY_DASHBOARD, NEW_WAREHOUSE_ID, PARENT_PATH)
        if aq_id:
            state["resources"]["hb_aq_dashboard_id"] = aq_id
    except ImportError:
        auth_quality_dashboard = {
            "pages": [
                {
                    "name": "authenticity",
                    "displayName": "Authenticity",
                    "layout": [
                        _counter("ctr-verifications", "ds_auth", "COUNT(`id`)", "Total Verifications", "Verifications", 0, 0),
                        _counter("ctr-verified", "ds_auth", "SUM(CASE WHEN `status` = 'verified' THEN 1 ELSE 0 END)", "Verified", "Verified", 2, 0),
                        _counter("ctr-alerts", "ds_alerts", "COUNT(`id`)", "Alerts", "Alerts", 4, 0),
                        _pie("pie-auth-status", "ds_auth", "status", "`status`", "COUNT(id)", "COUNT(`id`)", "Verification Status", 0, 3),
                        _bar("bar-auth-region", "ds_auth", "region", "`region`", "COUNT(id)", "COUNT(`id`)", "Verifications by Region", 3, 3),
                        _bar("bar-auth-method", "ds_auth", "verification_method", "`verification_method`", "COUNT(id)", "COUNT(`id`)", "Verification Methods", 0, 8, w=6),
                    ],
                },
                {
                    "name": "quality",
                    "displayName": "Quality Control",
                    "layout": [
                        _counter("ctr-inspections", "ds_inspections", "COUNT(`id`)", "Inspections", "Inspections", 0, 0),
                        _counter("ctr-avg-score", "ds_inspections", "AVG(`overall_score`)", "Avg Score", "Avg Score", 2, 0),
                        _counter("ctr-defects", "ds_defects", "COUNT(`id`)", "Defects", "Defects", 4, 0),
                        _pie("pie-insp-status", "ds_inspections", "status", "`status`", "COUNT(id)", "COUNT(`id`)", "Inspection Status", 0, 3),
                        _bar("bar-defect-type", "ds_defects", "defect_type", "`defect_type`", "COUNT(id)", "COUNT(`id`)", "Defects by Type", 3, 3),
                        _bar("bar-partner-quality", "ds_inspections", "manufacturing_partner", "`manufacturing_partner`", "AVG(overall_score)", "AVG(`overall_score`)", "Quality by Partner", 0, 8),
                        _pie("pie-defect-severity", "ds_defects", "severity", "`severity`", "COUNT(id)", "COUNT(`id`)", "Defect Severity", 3, 8),
                    ],
                },
            ],
            "datasets": [
                {"name": "ds_auth", "displayName": "Auth Verifications", "query": f"SELECT * FROM {SC}.hb_auth_verifications"},
                {"name": "ds_alerts", "displayName": "Auth Alerts", "query": f"SELECT * FROM {SC}.hb_auth_alerts"},
                {"name": "ds_inspections", "displayName": "Quality Inspections", "query": f"SELECT * FROM {SC}.hb_quality_inspections"},
                {"name": "ds_defects", "displayName": "Quality Defects", "query": f"SELECT * FROM {SC}.hb_quality_defects"},
            ],
        }
        aq_id = _create_and_publish_dashboard(NEW_PROFILE, "HB Authenticity & Quality Control", auth_quality_dashboard, NEW_WAREHOUSE_ID, PARENT_PATH)
        if aq_id:
            state["resources"]["hb_aq_dashboard_id"] = aq_id

    # 3. AdTech Intelligence Dashboard
    print("  Creating AdTech Intelligence dashboard...")
    adtech_dashboard = {
        "pages": [
            {
                "name": "overview",
                "displayName": "Demand & Inventory Overview",
                "layout": [
                    _counter("ctr-campaigns", "ds_campaigns", "COUNT(*)", "Total Campaigns", "Campaigns", 0, 0),
                    _counter("ctr-inventory", "ds_inventory", "COUNT(*)", "Total Inventory", "Inventory Items", 2, 0),
                    _counter("ctr-anomalies", "ds_anomalies", "COUNT(*)", "Active Anomalies", "Anomalies", 4, 0),
                    _bar("bar-camp-status", "ds_campaigns", "status", "`status`", "COUNT(*)", "COUNT(*)", "Campaigns by Status", 0, 3),
                    _bar("bar-inv-type", "ds_inventory", "ad_format", "`ad_format`", "COUNT(*)", "COUNT(*)", "Inventory by Format", 3, 3),
                    _pie("pie-anomaly-sev", "ds_anomalies", "severity", "`severity`", "COUNT(*)", "COUNT(*)", "Anomalies by Severity", 0, 8),
                    _bar("bar-camp-budget", "ds_campaigns", "name", "`name`", "budget", "`budget`", "Campaigns by Budget", 3, 8),
                ],
            },
        ],
        "datasets": [
            {"name": "ds_campaigns", "displayName": "Campaigns", "query": f"SELECT * FROM {NEW_CATALOG}.adtech_intelligence.campaigns"},
            {"name": "ds_inventory", "displayName": "Ad Inventory", "query": f"SELECT * FROM {NEW_CATALOG}.adtech_intelligence.ad_inventory"},
            {"name": "ds_anomalies", "displayName": "Anomalies", "query": f"SELECT * FROM {NEW_CATALOG}.adtech_intelligence.anomalies"},
        ],
    }
    at_id = _create_and_publish_dashboard(NEW_PROFILE, "AdTech Intelligence - Demand & Inventory", adtech_dashboard, NEW_WAREHOUSE_ID, PARENT_PATH)
    if at_id:
        state["resources"]["adtech_dashboard_id"] = at_id


# ---------------------------------------------------------------------------
# Phase 11: Create Knowledge Assistants
# ---------------------------------------------------------------------------

def phase_11_knowledge_assistants(state):
    """Create Knowledge Assistants"""

    # 1. Issue Resolution KA
    print("  Creating Knowledge Assistant: Issue Resolution...")
    ir_body = {
        "display_name": "Issue Resolution Assistant",
        "description": "Helps resolve advertising technology issues using documentation from the issue resolution knowledge base.",
        "data_sources": [{
            "type": "VOLUME",
            "volume_path": f"/Volumes/{NEW_CATALOG}/adtech_intelligence/issue_resolution_docs",
        }],
    }
    ir_resp = api_request(NEW_PROFILE, "POST", "/api/2.0/agent-bricks/knowledge-assistants", ir_body)
    if ir_resp and (ir_resp.get("tile_id") or ir_resp.get("id")):
        tile_id = ir_resp.get("tile_id", ir_resp.get("id"))
        endpoint = ir_resp.get("endpoint_name", "")
        print(f"    Created: tile_id={tile_id}, endpoint={endpoint}")
        state["resources"]["issue_resolution_ka_tile_id"] = tile_id
        state["resources"]["issue_resolution_ka_endpoint"] = endpoint
    else:
        print(f"    Response: {ir_resp}")

    # 2. Customer Relations KA
    print("  Creating Knowledge Assistant: Customer Relations...")
    cr_body = {
        "display_name": "Customer Relations Assistant",
        "description": "Assists with customer relations inquiries using the customer relations documentation.",
        "data_sources": [{
            "type": "VOLUME",
            "volume_path": f"/Volumes/{NEW_CATALOG}/adtech_intelligence/customer_relations_docs",
        }],
    }
    cr_resp = api_request(NEW_PROFILE, "POST", "/api/2.0/agent-bricks/knowledge-assistants", cr_body)
    if cr_resp and (cr_resp.get("tile_id") or cr_resp.get("id")):
        tile_id = cr_resp.get("tile_id", cr_resp.get("id"))
        endpoint = cr_resp.get("endpoint_name", "")
        print(f"    Created: tile_id={tile_id}, endpoint={endpoint}")
        state["resources"]["customer_relations_ka_tile_id"] = tile_id
        state["resources"]["customer_relations_ka_endpoint"] = endpoint
    else:
        print(f"    Response: {cr_resp}")


# ---------------------------------------------------------------------------
# Phase 12: Create Multi-Agent Supervisors
# ---------------------------------------------------------------------------

def phase_12_multi_agent_supervisors(state):
    """Create Multi-Agent Supervisors"""
    resources = state.get("resources", {})

    # 1. AdTech MAS
    print("  Creating MAS: AdTech Intelligence Supervisor...")
    ir_tile = resources.get("issue_resolution_ka_tile_id", "")
    cr_tile = resources.get("customer_relations_ka_tile_id", "")
    at_genie = resources.get("adtech_genie_id", "")

    if not ir_tile or not cr_tile or not at_genie:
        print("    WARNING: Missing required resource IDs from previous phases.")
        print(f"      issue_resolution_ka_tile_id: {ir_tile or 'MISSING'}")
        print(f"      customer_relations_ka_tile_id: {cr_tile or 'MISSING'}")
        print(f"      adtech_genie_id: {at_genie or 'MISSING'}")
        if not ir_tile and not cr_tile and not at_genie:
            print("    Skipping AdTech MAS creation.")
        else:
            print("    Attempting creation with available IDs...")

    adtech_mas_body = {
        "display_name": "AdTech Intelligence Supervisor",
        "description": "Orchestrates issue resolution, customer relations, and data exploration for AdTech Intelligence.",
        "agents": [],
        "instructions": "You are the AdTech Intelligence Assistant. Route technical issues and troubleshooting to the Issue Resolution Specialist. Route customer and contract questions to the Customer Relations Specialist. Route data queries and analytics to the Data Explorer.",
    }
    if ir_tile:
        adtech_mas_body["agents"].append({
            "display_name": "Issue Resolution Specialist",
            "description": "Answers questions about resolving advertising technology issues, troubleshooting delivery problems, fixing tracking issues, and handling technical incidents.",
            "knowledge_assistant_tile_id": ir_tile,
        })
    if cr_tile:
        adtech_mas_body["agents"].append({
            "display_name": "Customer Relations Specialist",
            "description": "Answers questions about customer relationships, contract management, advertiser communications, and account management.",
            "knowledge_assistant_tile_id": cr_tile,
        })
    if at_genie:
        adtech_mas_body["agents"].append({
            "display_name": "Data Explorer",
            "description": "Explores and queries advertising data including campaigns, performance metrics, inventory, anomalies, and issues. Use for any data analysis or SQL query needs.",
            "genie_space_id": at_genie,
        })

    if adtech_mas_body["agents"]:
        at_mas_resp = api_request(NEW_PROFILE, "POST", "/api/2.0/agent-bricks/agents", adtech_mas_body)
        if at_mas_resp and (at_mas_resp.get("tile_id") or at_mas_resp.get("id")):
            tile_id = at_mas_resp.get("tile_id", at_mas_resp.get("id"))
            endpoint = at_mas_resp.get("endpoint_name", "")
            print(f"    Created: tile_id={tile_id}, endpoint={endpoint}")
            state["resources"]["adtech_mas_tile_id"] = tile_id
            state["resources"]["adtech_mas_endpoint_name"] = endpoint
        else:
            print(f"    Response: {at_mas_resp}")

    # 2. HB Product Center MAS
    print("  Creating MAS: HB Product Center Intelligence...")
    sc_genie = resources.get("hb_sc_genie_id", "")
    aq_genie = resources.get("hb_aq_genie_id", "")

    if not sc_genie or not aq_genie:
        print("    WARNING: Missing Genie space IDs from Phase 9.")
        print(f"      hb_sc_genie_id: {sc_genie or 'MISSING'}")
        print(f"      hb_aq_genie_id: {aq_genie or 'MISSING'}")

    hb_mas_body = {
        "display_name": "HB Product Center Intelligence",
        "description": "Hugo Boss Product Center Intelligence Agent - orchestrates supply chain analytics, authenticity & quality insights, and product identification.",
        "agents": [],
        "instructions": "You are the Hugo Boss Product Center Intelligence Assistant. Route supply chain, logistics, and sustainability questions to the Supply Chain Analyst. Route quality control, defect, inspection, and authenticity questions to the Quality & Auth Analyst. Route product identification requests to the Product Identifier. For general questions, use your best judgment on which agent to route to. Always provide clear, professional responses.",
    }
    if sc_genie:
        hb_mas_body["agents"].append({
            "display_name": "Supply Chain Analyst",
            "description": "Answers questions about supply chain events, logistics, product journeys from manufacturing to retail, sustainability metrics, carbon footprint, water usage, recycled content, compliance status, and partner performance.",
            "genie_space_id": sc_genie,
        })
    if aq_genie:
        hb_mas_body["agents"].append({
            "display_name": "Quality & Auth Analyst",
            "description": "Answers questions about product authenticity verifications, counterfeit detection alerts, quality control inspections, defect analysis, manufacturing partner quality scores, verification methods, and brand protection.",
            "genie_space_id": aq_genie,
        })
    hb_mas_body["agents"].append({
        "display_name": "Product Identifier",
        "description": "Identifies Hugo Boss products from visual descriptions. Given a description of a product (color, style, material, category), searches the product catalog and returns matching products with confidence levels.",
        "uc_function_name": f"{NEW_CATALOG}.hb_product_center.identify_product",
    })

    hb_mas_resp = api_request(NEW_PROFILE, "POST", "/api/2.0/agent-bricks/agents", hb_mas_body)
    if hb_mas_resp and (hb_mas_resp.get("tile_id") or hb_mas_resp.get("id")):
        tile_id = hb_mas_resp.get("tile_id", hb_mas_resp.get("id"))
        endpoint = hb_mas_resp.get("endpoint_name", "")
        print(f"    Created: tile_id={tile_id}, endpoint={endpoint}")
        state["resources"]["hb_mas_tile_id"] = tile_id
        state["resources"]["hb_mas_endpoint_name"] = endpoint
    else:
        print(f"    Response: {hb_mas_resp}")


# ---------------------------------------------------------------------------
# Phase 13: Update Config Files
# ---------------------------------------------------------------------------

def phase_13_update_configs(state):
    """Update Config Files"""
    resources = state.get("resources", {})

    print("\n  === Resource IDs to update ===\n")
    print("  Genie Spaces:")
    print(f"    HB_SC_GENIE_SPACE_ID = {resources.get('hb_sc_genie_id', 'NOT SET')}")
    print(f"    HB_AQ_GENIE_SPACE_ID = {resources.get('hb_aq_genie_id', 'NOT SET')}")
    print(f"    ADTECH_GENIE_SPACE_ID = {resources.get('adtech_genie_id', 'NOT SET')}")
    print()
    print("  Dashboards:")
    print(f"    HB_SC_DASHBOARD_ID = {resources.get('hb_sc_dashboard_id', 'NOT SET')}")
    print(f"    HB_AQ_DASHBOARD_ID = {resources.get('hb_aq_dashboard_id', 'NOT SET')}")
    print(f"    ADTECH_DASHBOARD_ID = {resources.get('adtech_dashboard_id', 'NOT SET')}")
    print()
    print("  Knowledge Assistants:")
    print(f"    ISSUE_RESOLUTION_KA_TILE_ID = {resources.get('issue_resolution_ka_tile_id', 'NOT SET')}")
    print(f"    ISSUE_RESOLUTION_KA_ENDPOINT = {resources.get('issue_resolution_ka_endpoint', 'NOT SET')}")
    print(f"    CUSTOMER_RELATIONS_KA_TILE_ID = {resources.get('customer_relations_ka_tile_id', 'NOT SET')}")
    print(f"    CUSTOMER_RELATIONS_KA_ENDPOINT = {resources.get('customer_relations_ka_endpoint', 'NOT SET')}")
    print()
    print("  Multi-Agent Supervisors:")
    print(f"    ADTECH_MAS_TILE_ID = {resources.get('adtech_mas_tile_id', 'NOT SET')}")
    print(f"    ADTECH_MAS_ENDPOINT_NAME = {resources.get('adtech_mas_endpoint_name', 'NOT SET')}")
    print(f"    HB_MAS_TILE_ID = {resources.get('hb_mas_tile_id', 'NOT SET')}")
    print(f"    HB_MAS_ENDPOINT_NAME = {resources.get('hb_mas_endpoint_name', 'NOT SET')}")
    print()
    print("  Lakebase:")
    print(f"    PGHOST = {resources.get('lakebase_pghost', 'NOT SET')}")
    print(f"    PGUSER = {resources.get('lakebase_pguser', 'NOT SET')}")
    print(f"    ENDPOINT_NAME = {resources.get('lakebase_endpoint_name', 'NOT SET')}")
    print()

    # Attempt programmatic config updates
    repo_root = os.path.dirname(os.path.dirname(__file__))

    # Update databricks_config.py files with new resource IDs
    config_files = [
        os.path.join(repo_root, "src", "innovation_factory", "backend", "projects", "hb_product_center", "databricks_config.py"),
        os.path.join(repo_root, "src", "innovation_factory", "backend", "projects", "adtech_intelligence", "databricks_config.py"),
        os.path.join(repo_root, "src", "innovation_factory", "backend", "projects", "mol_asm_cockpit", "databricks_config.py"),
    ]

    replacements = {}
    # Build replacement map from old known IDs to new IDs
    if resources.get("hb_sc_genie_id"):
        replacements["hb_sc_genie_id"] = resources["hb_sc_genie_id"]
    if resources.get("hb_aq_genie_id"):
        replacements["hb_aq_genie_id"] = resources["hb_aq_genie_id"]
    if resources.get("adtech_genie_id"):
        replacements["adtech_genie_id"] = resources["adtech_genie_id"]
    if resources.get("hb_sc_dashboard_id"):
        replacements["hb_sc_dashboard_id"] = resources["hb_sc_dashboard_id"]
    if resources.get("hb_aq_dashboard_id"):
        replacements["hb_aq_dashboard_id"] = resources["hb_aq_dashboard_id"]
    if resources.get("adtech_dashboard_id"):
        replacements["adtech_dashboard_id"] = resources["adtech_dashboard_id"]

    for cfg_path in config_files:
        if not os.path.exists(cfg_path):
            print(f"  Config file not found: {cfg_path}")
            continue
        print(f"  Reading {cfg_path}...")
        with open(cfg_path) as f:
            content = f.read()
        original = content

        # Replace old host references
        content = content.replace(OLD_HOST, NEW_HOST)
        # Replace old warehouse ID
        content = content.replace(OLD_WAREHOUSE_ID, NEW_WAREHOUSE_ID)
        # Replace old catalog
        content = content.replace(OLD_CATALOG, NEW_CATALOG)
        # Replace old profile
        content = content.replace(f'"{OLD_PROFILE}"', f'"{NEW_PROFILE}"')
        content = content.replace(f"'{OLD_PROFILE}'", f"'{NEW_PROFILE}'")

        if content != original:
            with open(cfg_path, "w") as f:
                f.write(content)
            print(f"    Updated: {cfg_path}")
        else:
            print(f"    No changes needed: {cfg_path}")

    # Update databricks.yml
    dby_path = os.path.join(repo_root, "databricks.yml")
    if os.path.exists(dby_path):
        print(f"  Reading {dby_path}...")
        with open(dby_path) as f:
            content = f.read()
        original = content
        content = content.replace(OLD_HOST, NEW_HOST)
        content = content.replace(OLD_WAREHOUSE_ID, NEW_WAREHOUSE_ID)
        content = content.replace(OLD_CATALOG, NEW_CATALOG)
        if content != original:
            with open(dby_path, "w") as f:
                f.write(content)
            print(f"    Updated: {dby_path}")
        else:
            print(f"    No changes needed: {dby_path}")

    # Update app.yml
    ay_path = os.path.join(repo_root, "app.yml")
    if os.path.exists(ay_path):
        print(f"  Reading {ay_path}...")
        with open(ay_path) as f:
            content = f.read()
        original = content
        content = content.replace(OLD_HOST, NEW_HOST)
        content = content.replace(OLD_WAREHOUSE_ID, NEW_WAREHOUSE_ID)
        content = content.replace(OLD_CATALOG, NEW_CATALOG)
        if content != original:
            with open(ay_path, "w") as f:
                f.write(content)
            print(f"    Updated: {ay_path}")
        else:
            print(f"    No changes needed: {ay_path}")

    # Update seed_all_uc_notebook.py catalog reference
    nb_path = os.path.join(repo_root, "scripts", "seed_all_uc_notebook.py")
    if os.path.exists(nb_path):
        print(f"  Reading {nb_path}...")
        with open(nb_path) as f:
            content = f.read()
        original = content
        content = content.replace(OLD_CATALOG, NEW_CATALOG)
        # Also update asm_cockpit -> mac schema reference
        content = content.replace('"asm_cockpit"', '"mac"')
        content = content.replace("'asm_cockpit'", "'mac'")
        if content != original:
            with open(nb_path, "w") as f:
                f.write(content)
            print(f"    Updated: {nb_path}")
        else:
            print(f"    No changes needed: {nb_path}")

    print("\n  Config update phase complete.")
    print("  IMPORTANT: Review all changes manually before deploying.")


# ---------------------------------------------------------------------------
# Phase 14: Validation Tests
# ---------------------------------------------------------------------------

def phase_14_validation(state):
    """Validation Tests"""
    resources = state.get("resources", {})
    results = []

    def check(name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        results.append((name, passed, detail))
        print(f"  [{status}] {name}" + (f" - {detail}" if detail else ""))

    # 1. SQL COUNT(*) on key tables
    print("\n  --- Table row counts ---")
    tables_to_check = [
        (f"{NEW_CATALOG}.hb_product_center.hb_products", "HB Products"),
        (f"{NEW_CATALOG}.hb_product_center.hb_supply_chain_events", "HB Supply Chain Events"),
        (f"{NEW_CATALOG}.hb_product_center.hb_quality_inspections", "HB Quality Inspections"),
        (f"{NEW_CATALOG}.hb_product_center.hb_auth_verifications", "HB Auth Verifications"),
        (f"{NEW_CATALOG}.mac.stations", "MAC Stations"),
        (f"{NEW_CATALOG}.mac.fuel_sales", "MAC Fuel Sales"),
    ]
    for table_fqn, label in tables_to_check:
        resp = execute_sql(NEW_PROFILE, NEW_WAREHOUSE_ID, f"SELECT COUNT(*) FROM {table_fqn}")
        sql_state = resp.get("status", {}).get("state", "UNKNOWN")
        if sql_state == "SUCCEEDED":
            data = resp.get("result", {}).get("data_array", [])
            count = data[0][0] if data else 0
            check(f"{label} count", int(count) > 0, f"{count} rows")
        else:
            check(f"{label} count", False, f"Query state: {sql_state}")

    # 2. Volume file listing
    print("\n  --- Volume verification ---")
    vol_checks = [
        (NEW_CATALOG, "adtech_intelligence", "customer_relations_docs"),
        (NEW_CATALOG, "adtech_intelligence", "issue_resolution_docs"),
        (NEW_CATALOG, "hb_product_center", "images"),
        (NEW_CATALOG, "hb_product_center", "quality_documents"),
        (NEW_CATALOG, "mac", "raw_data"),
        (NEW_CATALOG, "image_similarity", "images"),
    ]
    for cat, schema, vol in vol_checks:
        files = list_volume_files_recursive(NEW_PROFILE, cat, schema, vol)
        check(f"Volume {schema}/{vol}", len(files) > 0, f"{len(files)} files")

    # 3. UC function test
    print("\n  --- UC Function ---")
    func_resp = execute_sql(NEW_PROFILE, NEW_WAREHOUSE_ID,
                            f"SELECT * FROM {NEW_CATALOG}.hb_product_center.identify_product('dark blue wool suit')")
    func_state = func_resp.get("status", {}).get("state", "UNKNOWN")
    func_rows = func_resp.get("result", {}).get("data_array", [])
    check("UC function identify_product", func_state == "SUCCEEDED" and len(func_rows) > 0,
          f"{len(func_rows)} results" if func_state == "SUCCEEDED" else func_state)

    # 4. VS endpoint status
    print("\n  --- Vector Search ---")
    ep = api_request(NEW_PROFILE, "GET", "/api/2.0/vector-search/endpoints/image_similarity_endpoint")
    if ep:
        ep_state = ep.get("endpoint_status", {}).get("state", ep.get("status", "UNKNOWN"))
        check("VS endpoint image_similarity_endpoint", ep_state == "ONLINE", ep_state)
    else:
        check("VS endpoint image_similarity_endpoint", False, "Not found")

    # 5. Genie spaces
    print("\n  --- Genie Spaces ---")
    for key, label in [("hb_sc_genie_id", "HB SC Genie"), ("hb_aq_genie_id", "HB AQ Genie"), ("adtech_genie_id", "AdTech Genie")]:
        gid = resources.get(key, "")
        if gid:
            g_resp = api_request(NEW_PROFILE, "GET", f"/api/2.0/genie/spaces/{gid}")
            check(label, g_resp is not None and g_resp.get("space_id", g_resp.get("id")), gid)
        else:
            check(label, False, "ID not in state")

    # 6. Dashboards
    print("\n  --- Dashboards ---")
    for key, label in [("hb_sc_dashboard_id", "HB SC Dashboard"), ("hb_aq_dashboard_id", "HB AQ Dashboard"), ("adtech_dashboard_id", "AdTech Dashboard")]:
        did = resources.get(key, "")
        if did:
            d_resp = api_request(NEW_PROFILE, "GET", f"/api/2.0/lakeview/dashboards/{did}")
            check(label, d_resp is not None and d_resp.get("dashboard_id"), did)
        else:
            check(label, False, "ID not in state")

    # Summary
    total = len(results)
    passed = sum(1 for _, p, _ in results if p)
    failed = total - passed
    print(f"\n  === Validation Summary ===")
    print(f"  Total: {total}  Passed: {passed}  Failed: {failed}")
    if failed > 0:
        print("\n  Failed checks:")
        for name, p, detail in results:
            if not p:
                print(f"    - {name}: {detail}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    state = load_state()

    if len(sys.argv) < 2:
        print("Usage: python scripts/migrate_full.py <phase|all>")
        print("Phases: 0-14, or 'all'")
        print()
        print("  0  - Pre-flight Checks")
        print("  1  - Create Schemas")
        print("  2  - Create Volumes")
        print("  3  - Upload Volume Files")
        print("  4  - Seed UC Tables (Small - via SQL)")
        print("  5  - Seed UC Tables (Large - via PySpark)")
        print("  6  - Create Image Similarity Resources")
        print("  7  - Create UC Function")
        print("  8  - Create Lakebase")
        print("  9  - Create Genie Spaces")
        print("  10 - Create Dashboards")
        print("  11 - Create Knowledge Assistants")
        print("  12 - Create Multi-Agent Supervisors")
        print("  13 - Update Config Files")
        print("  14 - Validation Tests")
        sys.exit(1)

    arg = sys.argv[1]

    phases = {
        "0": phase_0_preflight,
        "1": phase_1_schemas,
        "2": phase_2_volumes,
        "3": phase_3_upload_volumes,
        "4": phase_4_seed_small_tables,
        "5": phase_5_seed_large_tables,
        "6": phase_6_image_similarity,
        "7": phase_7_uc_function,
        "8": phase_8_lakebase,
        "9": phase_9_genie_spaces,
        "10": phase_10_dashboards,
        "11": phase_11_knowledge_assistants,
        "12": phase_12_multi_agent_supervisors,
        "13": phase_13_update_configs,
        "14": phase_14_validation,
    }

    if arg == "all":
        for num in sorted(phases.keys(), key=lambda x: int(x)):
            func = phases[num]
            print(f"\n{'='*60}")
            print(f"Phase {num}: {func.__doc__}")
            print(f"{'='*60}")
            try:
                func(state)
            except Exception as e:
                print(f"\n  PHASE {num} ERROR: {e}")
                import traceback
                traceback.print_exc()
            state["completed_phases"] = list(set(state.get("completed_phases", []) + [int(num)]))
            save_state(state)
        print(f"\n{'='*60}")
        print("All phases complete. State saved to migration_state.json")
        print(f"{'='*60}")
    elif arg in phases:
        func = phases[arg]
        print(f"\n{'='*60}")
        print(f"Phase {arg}: {func.__doc__}")
        print(f"{'='*60}")
        try:
            func(state)
        except Exception as e:
            print(f"\n  PHASE {arg} ERROR: {e}")
            import traceback
            traceback.print_exc()
        state["completed_phases"] = list(set(state.get("completed_phases", []) + [int(arg)]))
        save_state(state)
    else:
        print(f"Unknown phase: {arg}")
        print("Valid phases: 0-14, or 'all'")
        sys.exit(1)
