"""Deploy AdTech + HB agents (Genies, KAs, MAS) to fevm-felix-demo.

Phase-based; each phase is idempotent where possible. State persists in
scripts/fevm_agents_state.json so phases can be re-run individually.

Usage:
    python scripts/deploy_agents_fevm.py <phase|all>

Phases:
    1  - Schemas + volumes (adtech_intelligence)
    2  - Upload KA docs (local -> volumes)
    3  - Seed AdTech UC tables
    4  - UC function identify_product
    5  - Create Genie Spaces (HB SC, HB AQ, AdTech)
    6  - Create Knowledge Assistants (Issue Resolution, Customer Relations)
    7  - Create Multi-Agent Supervisors (AdTech MAS, HB MAS)
    8  - Print summary / resource IDs
    9  - Migrate dashboards from a source workspace (AdTech, HB Quality, HB SC)
"""

import json
import os
import random
import re
import subprocess
import sys
import time
from datetime import date, datetime, timedelta

# Local import — uc_schema is a sibling module in scripts/
sys.path.insert(0, os.path.dirname(__file__))
import uc_schema  # noqa: E402
import seed_uc_aeco_data  # noqa: E402

PROFILE = "fevm-felix-demo"
HOST = "https://fevm-felix-demo.cloud.databricks.com"
CATALOG = "felix_demo_catalog"
WAREHOUSE_ID = "f7cdb11888c4799e"
STATE_FILE = os.path.join(os.path.dirname(__file__), "fevm_agents_state.json")
REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
KA_DOCS_ROOT = os.path.join(REPO_ROOT, "src", "innovation_factory", "backend",
                            "projects", "adtech_intelligence", "ka_docs")
AECO_KA_DOCS_ROOT = os.path.join(REPO_ROOT, "src", "innovation_factory", "backend",
                                  "projects", "aeco_hub", "ka_docs")

# Phase 9 — Dashboard migration defaults. These can be overridden via env vars
# if we ever need to point at a different source. The catalog rewrite maps any
# `innovation_factory_catalog.` prefix in serialized_dashboard SQL to the
# current target catalog.
DASHBOARD_SOURCE_PROFILE = os.getenv("DASHBOARD_SOURCE_PROFILE", "DEFAULT")
DASHBOARD_SOURCE_CATALOG = os.getenv(
    "DASHBOARD_SOURCE_CATALOG", "innovation_factory_catalog"
)
DASHBOARD_PARENT_PATH = os.getenv(
    "DASHBOARD_PARENT_PATH", "/Workspace/Users/felix.mutzl@databricks.com"
)
DASHBOARD_SOURCES = [
    # key,        source dashboard id,                    destination display_name
    ("adtech",    "01f10966118d1943b95d82e441e35342",     "AdTech Intelligence - Demand & Inventory"),
    ("hb_aq",     "01f110ce1d7d1fbc8832730291f05ef0",     "HB IPC - Quality Control"),
    ("hb_sc",     "01f110d62bfb1ba9ae6d99f9dc1b0f0b",     "HB Supply Chain Hub - Modern Edition"),
]


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# HTTP helpers via databricks CLI (handles auth transparently)
# ---------------------------------------------------------------------------

def _api(method, path, body=None, timeout=300):
    cmd = ["databricks", "api", method.lower(), path, "--profile", PROFILE]
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


def _sql(statement, max_poll=600, catalog=None):
    body = {
        "warehouse_id": WAREHOUSE_ID,
        "statement": statement,
        "wait_timeout": "50s",
    }
    if catalog:
        body["catalog"] = catalog
    resp = _api("post", "/api/2.0/sql/statements", body, timeout=120)
    if not resp:
        return {"status": {"state": "FAILED"}}
    state = resp.get("status", {}).get("state", "UNKNOWN")
    stmt_id = resp.get("statement_id")
    elapsed = 0
    while state in ("PENDING", "RUNNING") and elapsed < max_poll and stmt_id:
        time.sleep(3)
        elapsed += 3
        resp = _api("get", f"/api/2.0/sql/statements/{stmt_id}", timeout=60)
        if not resp:
            break
        state = resp.get("status", {}).get("state", "UNKNOWN")
    if state == "FAILED":
        err = resp.get("status", {}).get("error", {}).get("message", "?")
        print(f"    SQL FAILED: {err[:400]}")
    return resp


# ===========================================================================
# PHASE 1: Schemas + volumes
# ===========================================================================

def phase_1_schemas_volumes(state):
    print("  Creating adtech_intelligence schema...")
    _sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.adtech_intelligence")

    for vol in [
        f"{CATALOG}.adtech_intelligence.customer_relations_docs",
        f"{CATALOG}.adtech_intelligence.issue_resolution_docs",
    ]:
        print(f"  Creating volume {vol}...")
        resp = _sql(f"CREATE VOLUME IF NOT EXISTS {vol}")
        print(f"    -> {resp.get('status', {}).get('state', '?')}")

    print("  Creating aeco_hub schema...")
    _sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.aeco_hub")
    for vol in [
        f"{CATALOG}.aeco_hub.compliance_docs",
        f"{CATALOG}.aeco_hub.bim_models",
    ]:
        print(f"  Creating volume {vol}...")
        resp = _sql(f"CREATE VOLUME IF NOT EXISTS {vol}")
        print(f"    -> {resp.get('status', {}).get('state', '?')}")


# ===========================================================================
# PHASE 2: Upload KA docs
# ===========================================================================

def phase_2_upload_ka_docs(state):
    # AdTech Intelligence KA docs
    mappings = [
        (KA_DOCS_ROOT, "issue_resolution", "adtech_intelligence", "issue_resolution_docs"),
        (KA_DOCS_ROOT, "customer_relations", "adtech_intelligence", "customer_relations_docs"),
        (AECO_KA_DOCS_ROOT, "standards_compliance", "aeco_hub", "compliance_docs"),
    ]
    for root, local_subdir, schema, volume in mappings:
        local_dir = os.path.join(root, local_subdir)
        if not os.path.isdir(local_dir):
            print(f"  WARNING: {local_dir} not found, skipping")
            continue
        for fname in sorted(os.listdir(local_dir)):
            local_path = os.path.join(local_dir, fname)
            if not os.path.isfile(local_path):
                continue
            remote_path = f"dbfs:/Volumes/{CATALOG}/{schema}/{volume}/{fname}"
            print(f"  Uploading {fname} -> {schema}.{volume}/")
            res = subprocess.run(
                ["databricks", "fs", "cp", local_path, remote_path,
                 "--profile", PROFILE, "--overwrite"],
                capture_output=True, text=True, timeout=120,
            )
            if res.returncode != 0:
                print(f"    FAIL: {res.stderr[:300]}")
            else:
                print(f"    OK")


# ===========================================================================
# PHASE 3: Seed AdTech UC tables
# ===========================================================================

def phase_3_seed_adtech_tables(state):
    """Create-or-replace the AdTech tables and seed demo rows.

    DDL comes from the canonical :mod:`uc_schema` module — the same
    definitions every other seeder uses. ``CREATE TABLE IF NOT EXISTS``
    preserves existing rows on idempotent re-runs; in phase 3 we want
    fresh tables (this is the seed path, not a migration), so we drop
    first.
    """
    random.seed(42)
    SC = f"{CATALOG}.adtech_intelligence"

    # The canonical DDL uses CREATE IF NOT EXISTS; for seeding we want a
    # clean slate so drop + create. uc_schema has the column definitions
    # we trust.
    for key in uc_schema.tables_for_schema("adtech_intelligence"):
        table_fq = f"{CATALOG}.{key}"
        print(f"  DDL {table_fq}...")
        _sql(f"DROP TABLE IF EXISTS {table_fq}")
        resp = _sql(uc_schema.create_table_sql(CATALOG, key))
        print(f"    -> {resp.get('status', {}).get('state', '?')}")

    # --- Seed data ---
    industries = ["Automotive", "Fashion", "Tech", "Finance", "Retail", "Travel",
                  "Food & Beverage", "Gaming", "Healthcare", "Entertainment"]
    tiers = ["standard", "premium", "enterprise"]
    brands = ["Aurora Motors", "LuxFashion Co", "TechVault", "NordBank",
              "UrbanRetail", "SkyWays Travel", "SavorBites", "GameForge",
              "VitalCare Health", "CineStream", "GreenGrid", "PixelPeak",
              "SummitFinance", "Pulse Fitness", "Nimbus Electronics"]

    advertisers_rows = []
    for i, b in enumerate(brands, start=1):
        ind = random.choice(industries)
        email = f"ads@{b.lower().replace(' ', '').replace('&', '').replace('co', '')}.com"
        tier = random.choice(tiers)
        advertisers_rows.append(
            f"({i}, '{b}', '{ind}', 'Manager {i}', '{email}', '{tier}', "
            f"TIMESTAMP '2025-{random.randint(1,9):02d}-{random.randint(1,28):02d} 10:00:00')"
        )
    _sql(f"INSERT INTO {SC}.advertisers VALUES " + ",\n".join(advertisers_rows))
    print(f"  Inserted {len(advertisers_rows)} advertisers")

    # Campaigns
    camp_types = ["online", "outdoor", "hybrid"]
    statuses = ["active", "paused", "completed", "draft"]
    audiences = ["18-34 urban", "25-54 commuters", "families", "professionals",
                 "gamers", "travelers", "tech enthusiasts"]
    camp_rows = []
    for cid in range(1, 61):
        adv_id = random.randint(1, len(brands))
        camp_type = random.choice(camp_types)
        status = random.choices(statuses, weights=[5, 2, 3, 1])[0]
        budget = round(random.uniform(25000, 500000), 2)
        spent = round(budget * random.uniform(0.1, 0.95), 2) if status != "draft" else 0.0
        start = date(2026, random.randint(1, 3), random.randint(1, 28))
        end = start + timedelta(days=random.randint(30, 180))
        aud = random.choice(audiences)
        name = f"{brands[adv_id-1]} {camp_type.title()} Q{random.randint(1,4)}"
        camp_rows.append(
            f"({cid}, {adv_id}, '{name}', '{camp_type}', '{status}', {budget}, {spent}, "
            f"DATE '{start}', DATE '{end}', '{aud}')"
        )
    _sql(f"INSERT INTO {SC}.campaigns VALUES " + ",\n".join(camp_rows))
    print(f"  Inserted {len(camp_rows)} campaigns")

    # Ad inventory
    inv_types = ["display", "video", "billboard", "transit", "native", "audio"]
    loc_types = ["online", "indoor", "outdoor", "airport", "highway", "mall"]
    formats = ["banner_300x250", "video_pre_roll", "billboard_48x14",
               "transit_side", "native_feed", "audio_30s"]
    inv_statuses = ["available", "sold_out", "maintenance"]
    cities = ["Berlin", "Munich", "Hamburg", "Cologne", "Frankfurt", "Vienna",
              "Zurich", "Milan", "Madrid", "Paris", "Amsterdam", "Copenhagen"]
    regions = ["DACH", "Southern Europe", "Western Europe", "Northern Europe"]
    inv_rows = []
    for iid in range(1, 41):
        it = random.choice(inv_types)
        lt = random.choice(loc_types)
        city = random.choice(cities)
        region = random.choice(regions)
        fmt = random.choice(formats)
        impressions = random.randint(5000, 500000)
        cpm = round(random.uniform(3.5, 45.0), 2)
        status = random.choices(inv_statuses, weights=[7, 2, 1])[0]
        owner = random.choice(["MediaPark", "UrbanOOH", "DigitalNet", "OutVision"])
        inv_rows.append(
            f"({iid}, 'Slot {iid}', '{it}', '{lt}', '{city}', '{region}', "
            f"{impressions}, {cpm}, '{status}', '{fmt}', '{owner}')"
        )
    _sql(f"INSERT INTO {SC}.ad_inventory VALUES " + ",\n".join(inv_rows))
    print(f"  Inserted {len(inv_rows)} inventory items")

    # Performance metrics
    perf_rows = []
    row_id = 1
    for cid in range(1, 61):
        inv_id = random.randint(1, 40)
        for day_off in range(0, random.randint(15, 45), 2):
            d = date(2026, 1, 1) + timedelta(days=day_off)
            imp = random.randint(1000, 50000)
            clicks = int(imp * random.uniform(0.005, 0.055))
            ctr = round(clicks / imp, 4) if imp else 0.0
            conv = int(clicks * random.uniform(0.01, 0.08))
            spend = round(imp / 1000 * random.uniform(4, 20), 2)
            via = round(random.uniform(0.55, 0.95), 3)
            perf_rows.append(
                f"({row_id}, {cid}, {inv_id}, DATE '{d}', {imp}, {clicks}, "
                f"{ctr}, {conv}, {spend}, {via})"
            )
            row_id += 1
    # insert in batches
    batch = 400
    for i in range(0, len(perf_rows), batch):
        _sql(f"INSERT INTO {SC}.performance_metrics VALUES " + ",\n".join(perf_rows[i:i+batch]))
    print(f"  Inserted {len(perf_rows)} performance metrics")

    # Anomalies
    anomaly_types = ["low_ctr", "high_spend", "low_viewability", "no_impressions", "spike_conversions"]
    severities = ["low", "medium", "high", "critical"]
    a_statuses = ["new", "investigating", "resolved", "dismissed"]
    metric_names = ["ctr", "spend", "viewability_rate", "impressions", "conversions"]
    anom_rows = []
    for aid in range(1, 36):
        cid = random.randint(1, 60)
        at = random.choice(anomaly_types)
        sev = random.choices(severities, weights=[3, 4, 2, 1])[0]
        status = random.choices(a_statuses, weights=[3, 2, 4, 1])[0]
        mn = random.choice(metric_names)
        exp = round(random.uniform(0.05, 5000), 3)
        act = round(exp * random.uniform(0.2, 3.5), 3)
        dev = round((act - exp) / exp * 100, 2) if exp else 0
        detected = datetime(2026, random.randint(1, 4), random.randint(1, 28),
                            random.randint(0, 23), random.randint(0, 59))
        anom_rows.append(
            f"({aid}, {cid}, '{at}', '{sev}', '{at.replace('_', ' ').title()} on campaign {cid}', "
            f"'Detected {at.replace('_', ' ')} with {dev}% deviation from expected.', "
            f"'{status}', '{mn}', {exp}, {act}, {dev}, "
            f"TIMESTAMP '{detected.strftime('%Y-%m-%d %H:%M:%S')}')"
        )
    _sql(f"INSERT INTO {SC}.anomalies VALUES " + ",\n".join(anom_rows))
    print(f"  Inserted {len(anom_rows)} anomalies")

    # Issues
    cats = ["delivery", "billing", "tracking", "creative", "contract", "technical"]
    i_statuses = ["open", "in_progress", "resolved", "closed"]
    priorities = ["low", "medium", "high", "urgent"]
    issue_titles = {
        "delivery": ["Impressions not delivering", "Under-delivery on placement",
                     "Ad not showing in rotation"],
        "billing": ["Invoice mismatch", "Duplicate charge", "Missing line item"],
        "tracking": ["Pixel not firing", "Conversion attribution off",
                     "Analytics gap"],
        "creative": ["Wrong creative served", "Asset quality issue",
                     "Creative approval delay"],
        "contract": ["Contract renewal question", "Pricing clarification",
                     "Scope change request"],
        "technical": ["API error", "Dashboard loading slowly",
                      "Export failure"],
    }
    issue_rows = []
    for iid in range(1, 41):
        adv = random.randint(1, len(brands))
        camp = random.randint(1, 60)
        cat = random.choice(cats)
        title = random.choice(issue_titles[cat])
        status = random.choices(i_statuses, weights=[3, 2, 4, 3])[0]
        pri = random.choices(priorities, weights=[2, 4, 3, 1])[0]
        assigned = random.choice(["Alex Kumar", "Sam Rivera", "Jordan Park",
                                  "Morgan Chen", "Riley Schmidt"])
        created = datetime(2026, random.randint(1, 4), random.randint(1, 28), 10, 0)
        resolved = "NULL" if status in ("open", "in_progress") else \
                   f"TIMESTAMP '{(created + timedelta(days=random.randint(1, 14))).strftime('%Y-%m-%d %H:%M:%S')}'"
        desc = f"Advertiser reported {title.lower()} related to campaign {camp}."
        issue_rows.append(
            f"({iid}, {camp}, {adv}, '{title}', '{desc}', '{cat}', '{status}', "
            f"'{pri}', '{assigned}', "
            f"TIMESTAMP '{created.strftime('%Y-%m-%d %H:%M:%S')}', {resolved})"
        )
    _sql(f"INSERT INTO {SC}.issues VALUES " + ",\n".join(issue_rows))
    print(f"  Inserted {len(issue_rows)} issues")

    # Customer contracts
    c_statuses = ["active", "pending", "expired", "cancelled"]
    pay_terms = ["net30", "net60", "prepaid", "quarterly"]
    contract_rows = []
    for cid in range(1, 26):
        adv = random.randint(1, len(brands))
        start = date(2025, random.randint(1, 12), random.randint(1, 28))
        end = start + timedelta(days=random.randint(180, 730))
        value = round(random.uniform(100000, 2_000_000), 2)
        status = random.choices(c_statuses, weights=[6, 1, 2, 1])[0]
        pt = random.choice(pay_terms)
        signed = datetime.combine(start - timedelta(days=random.randint(5, 30)),
                                  datetime.min.time()).replace(hour=14)
        contract_rows.append(
            f"({cid}, {adv}, 'CON-{2025000 + cid}', DATE '{start}', DATE '{end}', "
            f"{value}, '{status}', '{pt}', TIMESTAMP '{signed.strftime('%Y-%m-%d %H:%M:%S')}')"
        )
    _sql(f"INSERT INTO {SC}.customer_contracts VALUES " + ",\n".join(contract_rows))
    print(f"  Inserted {len(contract_rows)} contracts")


# ===========================================================================
# PHASE 3A: Seed AECO Hub UC tables
# ===========================================================================

def phase_3a_seed_aeco_tables(state):
    """Drop+recreate the AECO Hub UC tables and seed the Schuster Bau AG
    portfolio + ~500K synthetic sensor readings.

    Uses :mod:`seed_uc_aeco_data` for the SQL — same pattern as AdTech, but
    sensor readings are generated server-side via ``INSERT … SELECT FROM
    range()`` so the warehouse does the heavy lifting.
    """
    for key in uc_schema.tables_for_schema("aeco_hub"):
        table_fq = f"{CATALOG}.{key}"
        print(f"  DDL {table_fq}...")
        _sql(f"DROP TABLE IF EXISTS {table_fq}")
        resp = _sql(uc_schema.create_table_sql(CATALOG, key))
        print(f"    -> {resp.get('status', {}).get('state', '?')}")

    target_rows = int(os.getenv("AECO_SENSOR_ROWS", "500000"))
    stmts = seed_uc_aeco_data.build_sql(catalog=CATALOG, target_sensor_rows=target_rows)
    print(f"  Running {len(stmts)} insert statements (~{target_rows:,} sensor readings)...")
    for i, stmt in enumerate(stmts, 1):
        # max_poll bumped because the server-side range() inserts can take
        # tens of seconds for the larger sensor-reading shards.
        resp = _sql(stmt, max_poll=900)
        state_str = resp.get("status", {}).get("state", "?")
        # Brief progress feedback — full SQL is long, just show table name
        head = stmt.split("\n", 1)[0][:80]
        print(f"    [{i}/{len(stmts)}] {state_str}: {head}...")


# ===========================================================================
# PHASE 4: UC function identify_product
# ===========================================================================

def phase_4_uc_function(state):
    func_sql = f"""CREATE OR REPLACE FUNCTION {CATALOG}.hb_product_center.identify_product(
  image_description STRING COMMENT 'A textual description of the product to identify, including visual features like color, style, material, category'
)
RETURNS TABLE (
  product_id BIGINT, sku STRING, style_name STRING, color STRING,
  category STRING, collection STRING, material STRING, price DOUBLE, confidence STRING
)
COMMENT 'Identifies HB products based on visual description. Returns matching products from the catalog with confidence levels.'
RETURN
  SELECT id AS product_id, sku, style_name, color, category, collection, material, price,
    CASE
      WHEN LOWER(image_description) LIKE CONCAT('%', LOWER(style_name), '%')
        OR LOWER(image_description) LIKE CONCAT('%', LOWER(category), '%') THEN 'high'
      WHEN LOWER(image_description) LIKE CONCAT('%', LOWER(color), '%')
        OR LOWER(image_description) LIKE CONCAT('%', LOWER(material), '%') THEN 'medium'
      ELSE 'low'
    END AS confidence
  FROM {CATALOG}.hb_product_center.hb_products
  WHERE LOWER(image_description) LIKE CONCAT('%', LOWER(style_name), '%')
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
    resp = _sql(func_sql)
    print(f"    -> {resp.get('status', {}).get('state', '?')}")

    print("  Testing function...")
    test = _sql(f"SELECT * FROM {CATALOG}.hb_product_center.identify_product('dark blue wool suit')")
    rows = test.get("result", {}).get("data_array", [])
    print(f"    Returned {len(rows)} rows")


# ===========================================================================
# PHASE 5: Genie spaces
# ===========================================================================

def phase_5_genie_spaces(state):
    spaces = state.setdefault("genies", {})
    specs = [
        ("hb_sc", "HB Supply Chain Intelligence",
         "Supply chain analytics for HB products - track events, logistics, "
         "sustainability metrics across the global supply chain.",
         [f"{CATALOG}.hb_product_center.hb_supply_chain_events",
          f"{CATALOG}.hb_product_center.hb_products",
          f"{CATALOG}.hb_product_center.hb_sustainability_metrics"],
         ["What are the top 10 supply chain partners by event count?",
          "Show the distribution of supply chain events by type",
          "Which countries have the most supply chain activity?",
          "What is the average carbon footprint by product category?",
          "Show products with non-compliant sustainability status",
          "Which products have the highest water usage?"]),
        ("hb_aq", "HB Authenticity & Quality Control",
         "Authenticity verification and quality control analytics for HB products.",
         [f"{CATALOG}.hb_product_center.hb_auth_verifications",
          f"{CATALOG}.hb_product_center.hb_auth_alerts",
          f"{CATALOG}.hb_product_center.hb_quality_inspections",
          f"{CATALOG}.hb_product_center.hb_quality_defects",
          f"{CATALOG}.hb_product_center.hb_products"],
         ["How many authenticity verifications were performed this month?",
          "What percentage of verifications resulted in suspicious or counterfeit findings?",
          "Show the distribution of quality inspection scores",
          "What are the most common defect types?",
          "Which manufacturing partners have the highest quality scores?",
          "Show active authentication alerts by severity"]),
        ("adtech", "AdTech Intelligence Explorer",
         "Explore advertising technology data including advertisers, campaigns, "
         "inventory, performance metrics, anomalies, and customer contracts.",
         [f"{CATALOG}.adtech_intelligence.advertisers",
          f"{CATALOG}.adtech_intelligence.campaigns",
          f"{CATALOG}.adtech_intelligence.ad_inventory",
          f"{CATALOG}.adtech_intelligence.performance_metrics",
          f"{CATALOG}.adtech_intelligence.anomalies",
          f"{CATALOG}.adtech_intelligence.issues",
          f"{CATALOG}.adtech_intelligence.customer_contracts"],
         ["Which advertisers have the highest campaign budgets?",
          "Show the distribution of campaigns by status",
          "What is the average CTR across all active campaigns?",
          "Show anomalies by severity level",
          "Which campaigns have the most open issues?",
          "What is the total contract value by advertiser?"]),
        ("aeco_project_analytics", "AECO Project Analytics",
         "Project portfolio analytics for the AECO Hub digital twin — "
         "construction projects, buildings, costs, schedule, and issues.",
         [f"{CATALOG}.aeco_hub.dt_projects",
          f"{CATALOG}.aeco_hub.dt_buildings",
          f"{CATALOG}.aeco_hub.dt_cost_items",
          f"{CATALOG}.aeco_hub.dt_schedule_activities",
          f"{CATALOG}.aeco_hub.dt_issues"],
         ["What is the total cost of TechHub Campus?",
          "Show projects behind schedule",
          "Compare cost overruns across projects",
          "Which projects have the most critical issues?",
          "What is the average progress percentage by phase?",
          "Show the top 5 most expensive cost categories"]),
        ("aeco_operations_intelligence", "AECO Operations Intelligence",
         "Operations and IoT analytics for AECO Hub — sensor readings, energy "
         "consumption, maintenance, and space utilization.",
         [f"{CATALOG}.aeco_hub.dt_sensor_readings",
          f"{CATALOG}.aeco_hub.dt_energy_consumption",
          f"{CATALOG}.aeco_hub.dt_maintenance_orders",
          f"{CATALOG}.aeco_hub.dt_space_utilization"],
         ["What is the average energy consumption per building over the last 30 days?",
          "Show buildings with CO2 readings above 1000 ppm",
          "List overdue maintenance orders by priority",
          "What is the average space occupancy by project?",
          "Which sensor types report the highest variance?",
          "Show the daily energy cost trend"]),
    ]
    for key, name, desc, tables, questions in specs:
        if spaces.get(key):
            print(f"  {name}: already exists -> {spaces[key]}")
            continue
        body = {
            "display_name": name,
            "description": desc,
            "warehouse_id": WAREHOUSE_ID,
            "table_identifiers": tables,
            "run_as_type": "VIEWER",
        }
        print(f"  Creating Genie space: {name}...")
        resp = _api("post", "/api/2.0/data-rooms/", body)
        if resp and (resp.get("space_id") or resp.get("id")):
            sid = resp.get("space_id") or resp.get("id")
            spaces[key] = sid
            print(f"    Created: {sid}")
            # Add sample questions via batch
            q_body = {
                "batch_actions": [
                    {"action": "ADD", "curated_question": {"question_text": q,
                                                             "question_type": "SAMPLE_QUESTION"}}
                    for q in questions
                ]
            }
            q_resp = _api("post", f"/api/2.0/data-rooms/{sid}/curated-questions/batch-actions", q_body)
            if q_resp is not None:
                print(f"    Added {len(questions)} sample questions")
            else:
                print(f"    WARN: sample questions failed")
        else:
            print(f"    Failed: {resp}")
        save_state(state)


# ===========================================================================
# PHASE 6: Knowledge Assistants
# ===========================================================================

def phase_6_knowledge_assistants(state):
    kas = state.setdefault("kas", {})

    specs = [
        ("issue_resolution", "Issue Resolution Assistant",
         "Answers questions about resolving advertising technology issues, "
         "troubleshooting ad delivery, billing, tracking, and technical incidents.",
         f"/Volumes/{CATALOG}/adtech_intelligence/issue_resolution_docs"),
        ("customer_relations", "Customer Relations Assistant",
         "Answers questions about customer relationships, contract management, "
         "campaign history, and account profiles.",
         f"/Volumes/{CATALOG}/adtech_intelligence/customer_relations_docs"),
        ("aeco_standards_compliance", "AECO Standards & Compliance Assistant",
         "Answers questions about IFC standards, COBie handover requirements, "
         "German building regulations, and building automation integration "
         "for AECO Hub digital twin projects.",
         f"/Volumes/{CATALOG}/aeco_hub/compliance_docs"),
    ]
    for key, name, desc, volume_path in specs:
        if kas.get(key, {}).get("tile_id"):
            print(f"  {name}: already exists -> {kas[key]['tile_id']}")
            continue
        body = {"display_name": name, "description": desc}
        print(f"  Creating KA: {name}...")
        resp = _api("post", "/api/2.1/knowledge-assistants", body)
        if not resp:
            print(f"    Failed: no response")
            continue
        tile_id = resp.get("id") or (resp.get("name", "").split("/")[-1] if resp.get("name") else None)
        endpoint = resp.get("endpoint_name")
        if not tile_id:
            print(f"    Failed: no id in response: {resp}")
            continue
        print(f"    Created KA: tile_id={tile_id}, endpoint={endpoint}")
        kas[key] = {"tile_id": tile_id, "endpoint_name": endpoint, "name": name,
                    "volume_path": volume_path}
        save_state(state)

        # Add the knowledge source (files in volume)
        source_body = {
            "display_name": f"{name} - Documents",
            "description": f"Documents for {name}",
            "source_type": "files",
            "files": {"path": volume_path},
        }
        print(f"    Adding knowledge source...")
        src_resp = _api("post",
                         f"/api/2.1/knowledge-assistants/{tile_id}/knowledge-sources",
                         source_body)
        if src_resp:
            src_id = src_resp.get("id") or (src_resp.get("name", "").split("/")[-1] if src_resp.get("name") else None)
            kas[key]["source_id"] = src_id
            print(f"      Source created: {src_id}")
        else:
            print(f"      Source creation failed")
        save_state(state)

        # Sync the source
        print(f"    Syncing sources...")
        sync_resp = _api("post",
                         f"/api/2.1/knowledge-assistants/{tile_id}/knowledge-sources:sync",
                         {})
        print(f"      Sync initiated: {sync_resp is not None}")


def _wait_for_ka_online(tile_id, max_wait=900):
    elapsed = 0
    while elapsed < max_wait:
        resp = _api("get", f"/api/2.1/knowledge-assistants/{tile_id}")
        if resp:
            status = resp.get("endpoint_status") or \
                     resp.get("knowledge_assistant", {}).get("endpoint_status") or "?"
            print(f"    [{elapsed}s] status={status}")
            if status == "ONLINE":
                return resp
            if status in ("FAILED", "OFFLINE"):
                return resp
        time.sleep(30)
        elapsed += 30
    return None


# ===========================================================================
# PHASE 7: Multi-Agent Supervisors
# ===========================================================================

def phase_7_multi_agent_supervisors(state):
    mas = state.setdefault("mas", {})
    genies = state.get("genies", {})
    kas = state.get("kas", {})

    def _build_agent(name, description, kind, value):
        cfg = {"name": name.replace(" ", "_"), "description": description}
        if kind == "genie":
            cfg["agent_type"] = "genie"
            cfg["genie_space"] = {"id": value}
        elif kind == "ka_endpoint":
            cfg["agent_type"] = "serving_endpoint"
            cfg["serving_endpoint"] = {"name": value}
        elif kind == "uc_function":
            parts = value.split(".")
            cfg["agent_type"] = "unity_catalog_function"
            cfg["unity_catalog_function"] = {"uc_path": {
                "catalog": parts[0], "schema": parts[1], "name": parts[2]
            }}
        return cfg

    def _extract_mas(resp):
        if not resp:
            return None, None
        tile_id = resp.get("supervisor_agent_id") or resp.get("id") or \
                  (resp.get("name", "").split("/")[-1] if resp.get("name") else None)
        endpoint = resp.get("endpoint_name")
        if tile_id and not endpoint:
            short = tile_id.split("-")[0]
            endpoint = f"mas-{short}-endpoint"
        return tile_id, endpoint

    # ---------------------------------------------------------------------
    # Naming convention (D3): every sub-agent uses snake_case_lowercase.
    # The MAS framework derives its tool names from these, and the LLM
    # routes by referencing them in ``instructions`` by the exact machine
    # name so the tool_call output is deterministic.
    # MAS display_name always ends with "Supervisor" so both supervisors
    # read consistently in the Agent Bricks UI.
    # ---------------------------------------------------------------------

    def _delete_existing_mas_by_name(display_name: str) -> None:
        """If a MAS with this display_name exists, delete it.

        GET responses don't echo the `agents` array, so we can't reliably
        update-in-place — idempotency = delete + recreate.
        """
        resp = _api("get", "/api/2.1/supervisor-agents?page_size=100")
        if not resp:
            return
        for entry in resp.get("supervisor_agents", []):
            if entry.get("display_name") == display_name:
                tid = entry.get("supervisor_agent_id")
                if tid:
                    print(f"    Deleting existing {display_name} ({tid})...")
                    _api("delete", f"/api/2.1/supervisor-agents/{tid}")

    # --- AdTech MAS -------------------------------------------------------
    adtech_agents = []
    if kas.get("issue_resolution", {}).get("endpoint_name"):
        adtech_agents.append(_build_agent(
            "issue_resolution",
            "Answers questions about resolving advertising technology issues, "
            "troubleshooting ad delivery, billing, tracking, and technical "
            "incidents. Use `issue_resolution` for any how-to-resolve or "
            "troubleshooting question.",
            "ka_endpoint", kas["issue_resolution"]["endpoint_name"]))
    if kas.get("customer_relations", {}).get("endpoint_name"):
        adtech_agents.append(_build_agent(
            "customer_relations",
            "Answers questions about customer relationships, contract "
            "management, campaign history, and account profiles. Use "
            "`customer_relations` for customer and contract questions.",
            "ka_endpoint", kas["customer_relations"]["endpoint_name"]))
    if genies.get("adtech"):
        adtech_agents.append(_build_agent(
            "data_explorer",
            "Explores and queries advertising data including campaigns, "
            "performance metrics, inventory, anomalies, and issues. Use "
            "`data_explorer` for any data analysis or SQL query needs.",
            "genie", genies["adtech"]))

    # Recreate if the stored phase_7_version doesn't match the current
    # source (D3 introduced the snake_case sub-agent naming — old MASes
    # created before D3 land with mixed-case names and need to be
    # rebuilt). Bump this string when the phase-7 config changes shape.
    PHASE_7_VERSION = "D3-snake-case-subagents+aeco-hub"
    needs_rebuild = state.get("phase_7_version") != PHASE_7_VERSION

    if adtech_agents and (needs_rebuild or not mas.get("adtech", {}).get("tile_id")):
        adtech_display = "AdTech Intelligence Supervisor"
        _delete_existing_mas_by_name(adtech_display)
        body = {
            "display_name": adtech_display,
            "description": (
                "Orchestrates issue resolution, customer relations, and data "
                "exploration for AdTech Intelligence."
            ),
            "instructions": (
                "You are the AdTech Intelligence Supervisor. Route requests "
                "to exactly one sub-agent by name:\n"
                "- `issue_resolution` — technical troubleshooting / how-to.\n"
                "- `customer_relations` — customer / contract questions.\n"
                "- `data_explorer` — data analysis / SQL / metrics."
            ),
            "agents": adtech_agents,
        }
        print(f"  Creating MAS: {adtech_display}...")
        resp = _api("post", "/api/2.1/supervisor-agents", body)
        print(f"    Response: {json.dumps(resp, indent=2)[:500] if resp else 'None'}")
        tile_id, endpoint = _extract_mas(resp)
        if tile_id:
            mas["adtech"] = {"tile_id": tile_id, "endpoint_name": endpoint,
                              "name": adtech_display}
            save_state(state)
            print(f"    OK: tile_id={tile_id}, endpoint={endpoint}")

    # --- HB MAS -----------------------------------------------------------
    hb_agents = []
    if genies.get("hb_sc"):
        hb_agents.append(_build_agent(
            "supply_chain",
            "Answers questions about supply chain events, logistics, product "
            "journeys from manufacturing to retail, sustainability metrics "
            "(carbon footprint, water usage, recycled content), compliance "
            "status, and partner performance. Use `supply_chain` for these.",
            "genie", genies["hb_sc"]))
    if genies.get("hb_aq"):
        hb_agents.append(_build_agent(
            "quality_and_authenticity",
            "Answers questions about product authenticity verifications, "
            "counterfeit detection alerts, quality control inspections, "
            "defect analysis, manufacturing partner quality scores, "
            "verification methods, and brand protection. Use "
            "`quality_and_authenticity` for these.",
            "genie", genies["hb_aq"]))
    hb_agents.append(_build_agent(
        "product_identifier",
        "Identifies HB products from visual descriptions. Given a description "
        "of a product (color, style, material, category), searches the "
        "product catalog and returns matching products with confidence "
        "levels. Use `product_identifier` for product-lookup requests.",
        "uc_function", f"{CATALOG}.hb_product_center.identify_product"))

    if hb_agents and (needs_rebuild or not mas.get("hb", {}).get("tile_id")):
        hb_display = "HB Product Center Supervisor"
        _delete_existing_mas_by_name(hb_display)
        # Also purge the legacy display name used before D3.
        _delete_existing_mas_by_name("HB Product Center Intelligence")
        body = {
            "display_name": hb_display,
            "description": (
                "HB Product Center Supervisor — orchestrates supply chain "
                "analytics, quality & authenticity insights, and product "
                "identification."
            ),
            "instructions": (
                "You are the HB Product Center Supervisor. Route each user "
                "request to exactly one sub-agent by name:\n"
                "- `supply_chain` — logistics, partners, sustainability, "
                "manufacturing-to-retail journey questions.\n"
                "- `quality_and_authenticity` — quality inspections, defects, "
                "authenticity verifications, counterfeit alerts, brand "
                "protection.\n"
                "- `product_identifier` — product lookup by visual / textual "
                "description."
            ),
            "agents": hb_agents,
        }
        print(f"  Creating MAS: {hb_display}...")
        resp = _api("post", "/api/2.1/supervisor-agents", body)
        print(f"    Response: {json.dumps(resp, indent=2)[:500] if resp else 'None'}")
        tile_id, endpoint = _extract_mas(resp)
        if tile_id:
            mas["hb"] = {"tile_id": tile_id, "endpoint_name": endpoint,
                          "name": hb_display}
            save_state(state)
            print(f"    OK: tile_id={tile_id}, endpoint={endpoint}")

    # --- AECO Hub MAS -----------------------------------------------------
    aeco_agents = []
    if genies.get("aeco_project_analytics"):
        aeco_agents.append(_build_agent(
            "project_analytics",
            "Answers questions about construction projects, buildings, costs, "
            "schedule, and issues across the AECO Hub portfolio. Use "
            "`project_analytics` for any portfolio-level analytics question.",
            "genie", genies["aeco_project_analytics"]))
    if genies.get("aeco_operations_intelligence"):
        aeco_agents.append(_build_agent(
            "operations_intelligence",
            "Answers questions about IoT sensor readings, energy consumption, "
            "maintenance orders, and space utilization for operating projects. "
            "Use `operations_intelligence` for facility-management and IoT "
            "questions.",
            "genie", genies["aeco_operations_intelligence"]))
    if kas.get("aeco_standards_compliance", {}).get("endpoint_name"):
        aeco_agents.append(_build_agent(
            "standards_compliance",
            "Answers questions about IFC standards, COBie hand-over, German "
            "building regulations, and building-automation integration. Use "
            "`standards_compliance` for any standards or regulation question.",
            "ka_endpoint",
            kas["aeco_standards_compliance"]["endpoint_name"]))

    if aeco_agents and (needs_rebuild or not mas.get("aeco", {}).get("tile_id")):
        aeco_display = "AECO Hub Supervisor"
        _delete_existing_mas_by_name(aeco_display)
        body = {
            "display_name": aeco_display,
            "description": (
                "AECO Hub Supervisor — orchestrates project analytics, "
                "operations intelligence, and standards & compliance for the "
                "building-lifecycle digital twin."
            ),
            "instructions": (
                "You are the AECO Hub Supervisor. Route each user request to "
                "exactly one sub-agent by name:\n"
                "- `project_analytics` — portfolio, project, building, cost, "
                "schedule, issue questions.\n"
                "- `operations_intelligence` — IoT, energy, maintenance, "
                "space-utilization questions for operating projects.\n"
                "- `standards_compliance` — IFC, COBie, building regulations, "
                "BAS integration questions."
            ),
            "agents": aeco_agents,
        }
        print(f"  Creating MAS: {aeco_display}...")
        resp = _api("post", "/api/2.1/supervisor-agents", body)
        print(f"    Response: {json.dumps(resp, indent=2)[:500] if resp else 'None'}")
        tile_id, endpoint = _extract_mas(resp)
        if tile_id:
            mas["aeco"] = {"tile_id": tile_id, "endpoint_name": endpoint,
                           "name": aeco_display}
            save_state(state)
            print(f"    OK: tile_id={tile_id}, endpoint={endpoint}")

    # Stamp the phase version so re-runs skip the delete+recreate unless
    # the config changes shape again.
    state["phase_7_version"] = PHASE_7_VERSION
    save_state(state)


# ===========================================================================
# PHASE 8: Print summary
# ===========================================================================

def phase_8_summary(state):
    print("\n" + "=" * 70)
    print("Resource Summary")
    print("=" * 70)
    print("\nGenie Spaces:")
    for k, v in state.get("genies", {}).items():
        print(f"  {k}: {v}")
    print("\nKnowledge Assistants:")
    for k, v in state.get("kas", {}).items():
        print(f"  {k}: {json.dumps(v)}")
    print("\nMulti-Agent Supervisors:")
    for k, v in state.get("mas", {}).items():
        print(f"  {k}: {json.dumps(v)}")
    print("\nEnv vars to add to app.yml:")
    print(f"  HB_SC_GENIE_SPACE_ID={state.get('genies', {}).get('hb_sc', '')}")
    print(f"  HB_AQ_GENIE_SPACE_ID={state.get('genies', {}).get('hb_aq', '')}")
    print(f"  ADTECH_GENIE_SPACE_ID={state.get('genies', {}).get('adtech', '')}")
    print(f"  ADTECH_ISSUE_RESOLUTION_KA_TILE_ID={state.get('kas', {}).get('issue_resolution', {}).get('tile_id', '')}")
    print(f"  ADTECH_ISSUE_RESOLUTION_KA_ENDPOINT={state.get('kas', {}).get('issue_resolution', {}).get('endpoint_name', '')}")
    print(f"  ADTECH_CUSTOMER_RELATIONS_KA_TILE_ID={state.get('kas', {}).get('customer_relations', {}).get('tile_id', '')}")
    print(f"  ADTECH_CUSTOMER_RELATIONS_KA_ENDPOINT={state.get('kas', {}).get('customer_relations', {}).get('endpoint_name', '')}")
    print(f"  ADTECH_MAS_ENDPOINT_NAME={state.get('mas', {}).get('adtech', {}).get('endpoint_name', '')}")
    print(f"  HB_MAS_ENDPOINT_NAME={state.get('mas', {}).get('hb', {}).get('endpoint_name', '')}")
    print("\nDashboards:")
    for k, v in state.get("dashboards", {}).items():
        print(f"  {k}: {v}")
    dbs = state.get("dashboards", {})
    print(f"  HB_SC_DASHBOARD_ID={dbs.get('hb_sc', '')}")
    print(f"  HB_AQ_DASHBOARD_ID={dbs.get('hb_aq', '')}")
    print(f"  ADTECH_DASHBOARD_ID={dbs.get('adtech', '')}")


# ===========================================================================
# PHASE 9A: Create AECO Hub Energy & Sustainability dashboard (from JSON)
# ===========================================================================

def phase_9a_create_aeco_dashboard(state):
    """Create the AECO Hub Energy & Sustainability dashboard from the local
    JSON template. Idempotent — skipped when state already has the id.

    Differs from phase 9 in that we author the dashboard locally instead of
    migrating from a source workspace, so we don't need cross-workspace auth.
    """
    dashboards = state.setdefault("dashboards", {})
    if dashboards.get("aeco_energy"):
        print(f"  Already created -> {dashboards['aeco_energy']}")
        return

    json_path = os.path.join(
        REPO_ROOT, "src", "innovation_factory", "backend",
        "projects", "aeco_hub", "dashboard_energy.json",
    )
    if not os.path.isfile(json_path):
        print(f"  ERROR: dashboard JSON not found at {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        serialized = f.read()

    # Replace template placeholders with the target workspace's values.
    serialized = serialized.replace("{{CATALOG}}", CATALOG)
    serialized = serialized.replace("{{WAREHOUSE_ID}}", WAREHOUSE_ID)

    body = {
        "display_name": "AECO Hub — Energy & Sustainability",
        "warehouse_id": WAREHOUSE_ID,
        "serialized_dashboard": serialized,
    }
    print("  Creating dashboard...")
    resp = _api("post", "/api/2.0/lakeview/dashboards", body)
    if not resp or not resp.get("dashboard_id"):
        print(f"    FAIL: {resp}")
        return
    dashboard_id = resp["dashboard_id"]
    dashboards["aeco_energy"] = dashboard_id
    save_state(state)
    print(f"    Created: {dashboard_id}")

    # Publish so the iframe embed works.
    pub = _api("post", f"/api/2.0/lakeview/dashboards/{dashboard_id}/published",
               {"embed_credentials": True})
    if pub is not None:
        print(f"    Published with embed credentials")
    else:
        print(f"    WARN: publish failed; embed iframe will 404")


# ===========================================================================
# PHASE 9: Dashboard migration (source workspace → current target)
# ===========================================================================

def rewrite_catalog_in_serialized(serialized: str, src_catalog: str, tgt_catalog: str) -> str:
    """Rewrite every reference to the source catalog's tables to the target
    catalog. Conservative — only matches ``src_catalog.`` at word boundaries
    to avoid accidentally modifying unrelated strings.
    """
    pattern = r"\b" + re.escape(src_catalog) + r"(?=\.)"
    return re.sub(pattern, tgt_catalog, serialized)


def _src_api(method, path, body=None, timeout=120, profile=None):
    """API call against the source workspace (defaults to DASHBOARD_SOURCE_PROFILE)."""
    profile = profile or DASHBOARD_SOURCE_PROFILE
    cmd = ["databricks", "api", method.lower(), path, "--profile", profile]
    if body is not None:
        cmd.extend(["--json", json.dumps(body)])
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if res.returncode != 0:
        print(f"    SRC API ERROR {method} {path}: {res.stderr[:400]}")
        return None
    if not res.stdout.strip():
        return {}
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError:
        print(f"    Could not parse: {res.stdout[:300]}")
        return None


def phase_9_migrate_dashboards(state):
    """Migrate dashboards from DASHBOARD_SOURCE_PROFILE to the current target.

    For each entry in DASHBOARD_SOURCES:
      1. GET /api/2.0/lakeview/dashboards/{id} on source
      2. Rewrite ``DASHBOARD_SOURCE_CATALOG.`` → ``CATALOG.`` in serialized_dashboard
      3. POST /api/2.0/lakeview/dashboards on target (current workspace)
      4. POST /api/2.0/lakeview/dashboards/{new_id}/published with embed_credentials
    """
    dashboards = state.setdefault("dashboards", {})
    for key, src_id, dest_name in DASHBOARD_SOURCES:
        if dashboards.get(key):
            print(f"  {dest_name}: already migrated -> {dashboards[key]}")
            continue
        print(f"\n  Fetching source dashboard {src_id} ({dest_name})...")
        src = _src_api("get", f"/api/2.0/lakeview/dashboards/{src_id}")
        if not src or not src.get("serialized_dashboard"):
            print(f"    FAIL: source not found or empty")
            continue

        serialized = src["serialized_dashboard"]
        rewritten = rewrite_catalog_in_serialized(
            serialized, DASHBOARD_SOURCE_CATALOG, CATALOG
        )
        n_replaced = serialized.count(DASHBOARD_SOURCE_CATALOG + ".") - rewritten.count(
            DASHBOARD_SOURCE_CATALOG + "."
        )
        print(f"    Rewrote {n_replaced} catalog reference(s)")

        body = {
            "display_name": dest_name,
            "parent_path": DASHBOARD_PARENT_PATH,
            "serialized_dashboard": rewritten,
            "warehouse_id": WAREHOUSE_ID,
        }
        print(f"    Creating on target workspace ({PROFILE})...")
        created = _api("post", "/api/2.0/lakeview/dashboards", body)
        new_id = created.get("dashboard_id") if created else None
        if not new_id:
            print(f"    FAIL creating: {created}")
            continue
        print(f"    Created: {new_id}")

        print(f"    Publishing with embed_credentials=true...")
        pub = _api(
            "post",
            f"/api/2.0/lakeview/dashboards/{new_id}/published",
            {"warehouse_id": WAREHOUSE_ID, "embed_credentials": True},
        )
        if pub is None:
            print(f"    WARN: publish call returned None (dashboard may still be unpublished)")
        else:
            print(f"    Published")

        dashboards[key] = new_id
        save_state(state)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

PHASES = {
    "1": ("Schemas + volumes", phase_1_schemas_volumes),
    "2": ("Upload KA docs", phase_2_upload_ka_docs),
    "3": ("Seed AdTech UC tables", phase_3_seed_adtech_tables),
    "3a": ("Seed AECO Hub UC tables", phase_3a_seed_aeco_tables),
    "4": ("UC function identify_product", phase_4_uc_function),
    "5": ("Create Genie Spaces", phase_5_genie_spaces),
    "6": ("Create Knowledge Assistants", phase_6_knowledge_assistants),
    "7": ("Create Multi-Agent Supervisors", phase_7_multi_agent_supervisors),
    "8": ("Summary", phase_8_summary),
    "9": ("Migrate dashboards from source workspace", phase_9_migrate_dashboards),
    "9a": ("Create AECO Hub Energy dashboard (from JSON)", phase_9a_create_aeco_dashboard),
}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    state = load_state()
    arg = sys.argv[1]
    if arg == "all":
        for num in sorted(PHASES.keys(), key=int):
            name, fn = PHASES[num]
            print(f"\n{'=' * 70}\nPhase {num}: {name}\n{'=' * 70}")
            try:
                fn(state)
            except Exception as exc:
                import traceback
                print(f"  PHASE {num} ERROR: {exc}")
                traceback.print_exc()
            save_state(state)
    elif arg in PHASES:
        name, fn = PHASES[arg]
        print(f"\n{'=' * 70}\nPhase {arg}: {name}\n{'=' * 70}")
        fn(state)
        save_state(state)
    else:
        print(f"Unknown phase: {arg}")
        sys.exit(1)
