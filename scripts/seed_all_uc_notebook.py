# Databricks notebook source
# MAGIC %md
# MAGIC # Innovation Factory - UC Data Seed
# MAGIC Seeds all Unity Catalog tables for HB Product Center and MOL ASM Cockpit.

# COMMAND ----------

import os
import random
from datetime import date, datetime, timedelta, timezone

CATALOG = os.getenv("UC_CATALOG", "innovation_factory_catalog")

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.hb_product_center")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.mac")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.adtech_intelligence")
print(f"Using catalog: {CATALOG}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## HB Product Center Data

# COMMAND ----------

SCHEMA = "hb_product_center"
_rng = random.Random(77)
TODAY = date.today()

def _past_dt(max_days=180):
    delta = timedelta(days=_rng.randint(1, max_days), hours=_rng.randint(0, 23), minutes=_rng.randint(0, 59))
    return datetime.now(timezone.utc) - delta

def _past_date(max_days=365):
    return TODAY - timedelta(days=_rng.randint(1, max_days))

COLORS = [
    ("Black", "001"), ("Navy", "404"), ("Dark Blue", "402"), ("Medium Blue", "428"),
    ("White", "100"), ("Light Grey", "051"), ("Charcoal", "010"), ("Beige", "260"),
    ("Khaki", "250"), ("Burgundy", "605"), ("Dark Green", "305"), ("Camel", "262"),
    ("Light Blue", "450"), ("Pink", "630"), ("Red", "610"), ("Brown", "202"),
]
SIZES = ["44", "46", "48", "50", "52", "54", "56", "S", "M", "L", "XL", "XXL", "38", "40", "42"]
MATERIALS = [
    "100% Virgin Wool", "98% Cotton 2% Elastane", "100% Silk",
    "100% Cotton", "80% Wool 20% Cashmere", "97% Cotton 3% Elastane",
    "100% Linen", "60% Cotton 40% Polyester", "100% Leather",
    "95% Polyester 5% Elastane", "100% Cashmere", "70% Wool 30% Polyester",
]
SUPPLIERS = [
    ("Marzotto Group", "Italy"), ("Zegna Baruffa", "Italy"),
    ("Loro Piana", "Italy"), ("Scabal", "Belgium"),
    ("Dormeuil", "France"), ("Albini Group", "Italy"),
    ("Tessitura Monti", "Italy"), ("Südwolle Group", "Germany"),
    ("Piacenza Cashmere", "Italy"), ("Lanificio Cerruti", "Italy"),
    ("TAL Apparel", "Vietnam"), ("Crystal Group", "Vietnam"),
]
MANUFACTURING_PARTNERS = [
    "HB Manufacturing Izmir", "HB Manufacturing Radomsko",
    "Partner: Valentino Fashion Group", "Partner: Progroup Metzingen",
    "HB Manufacturing Morrovalle", "Partner: TAL Apparel Hanoi",
    "Partner: Crystal Group HCMC", "HB Manufacturing Cleveland",
]
INSPECTORS = [
    "Anna Müller", "Stefan Weber", "Lucia Rossi", "Marco Bianchi",
    "Elena Petrova", "Thomas Schmidt", "Yuki Tanaka", "Pierre Dupont",
]
LOCATIONS = [
    ("Metzingen, Germany", "Germany"), ("Istanbul, Turkey", "Turkey"),
    ("Radomsko, Poland", "Poland"), ("Morrovalle, Italy", "Italy"),
    ("Hanoi, Vietnam", "Vietnam"), ("Ho Chi Minh City, Vietnam", "Vietnam"),
    ("Shanghai, China", "China"), ("Hamburg, Germany", "Germany"),
    ("Rotterdam, Netherlands", "Netherlands"), ("New York, USA", "USA"),
    ("London, UK", "UK"), ("Paris, France", "France"),
    ("Milan, Italy", "Italy"), ("Tokyo, Japan", "Japan"),
    ("Dubai, UAE", "UAE"), ("Munich, Germany", "Germany"),
]
REGIONS = ["EMEA", "Americas", "Asia Pacific", "Middle East"]
CATEGORIES = ["suits", "shirts", "knitwear", "outerwear", "trousers", "shoes", "accessories", "fragrances", "sportswear", "denim"]
COLLECTIONS = ["boss", "hugo", "boss_orange", "boss_athleisure"]
SEASONS = ["spring_summer_2025", "fall_winter_2025", "spring_summer_2024", "fall_winter_2024", "resort_2025"]

PRODUCT_TEMPLATES = [
    ("Slim-Fit Suit in Virgin Wool", "suits", 0, (599, 899)),
    ("Regular-Fit Suit in Stretch Wool", "suits", 11, (499, 749)),
    ("Tuxedo in Wool Twill", "suits", 0, (899, 1299)),
    ("Sharp-Fit Cotton Shirt", "shirts", 3, (89, 159)),
    ("Slim-Fit Easy-Iron Shirt", "shirts", 1, (99, 169)),
    ("Casual Linen Shirt", "shirts", 6, (129, 199)),
    ("Crew-Neck Knit Sweater", "knitwear", 7, (149, 249)),
    ("Cashmere V-Neck Sweater", "knitwear", 10, (349, 499)),
    ("Merino Wool Cardigan", "knitwear", 0, (199, 299)),
    ("Padded Jacket with Down Fill", "outerwear", 9, (399, 599)),
    ("Wool-Blend Overcoat", "outerwear", 11, (499, 799)),
    ("Leather Bomber Jacket", "outerwear", 8, (699, 999)),
    ("Slim-Fit Stretch Chinos", "trousers", 1, (99, 179)),
    ("Regular-Fit Wool Trousers", "trousers", 0, (179, 299)),
    ("Italian Leather Oxford Shoes", "shoes", 8, (299, 449)),
    ("Suede Desert Boots", "shoes", 8, (249, 379)),
    ("Leather Belt with Logo Buckle", "accessories", 8, (89, 159)),
    ("Silk Pocket Square", "accessories", 2, (49, 89)),
    ("Wool-Blend Scarf", "accessories", 0, (79, 139)),
    ("BOSS Bottled Eau de Parfum", "fragrances", 3, (69, 129)),
    ("HUGO Man Eau de Toilette", "fragrances", 3, (59, 99)),
    ("Performance Stretch Polo", "sportswear", 9, (79, 129)),
    ("Slim-Fit Stretch Denim Jeans", "denim", 5, (129, 199)),
    ("Relaxed-Fit Selvedge Jeans", "denim", 3, (179, 279)),
]

from pyspark.sql.types import *

# Generate products
products = []
for i, (style, category, mat_idx, price_range) in enumerate(PRODUCT_TEMPLATES):
    color_name, color_code = _rng.choice(COLORS)
    size = _rng.choice(SIZES)
    collection = _rng.choice(COLLECTIONS)
    season = _rng.choice(SEASONS)
    supplier_name, country = _rng.choice(SUPPLIERS)
    price = round(_rng.uniform(*price_range), 2)
    sku = f"HB-{collection[:4].upper()}-{category[:3].upper()}-{1000 + i:04d}"
    status = _rng.choice(["active"] * 8 + ["discontinued", "sample"])
    products.append((i+1, sku, style, color_name, color_code, size, category, collection, season,
                     MATERIALS[mat_idx], price, status, country, supplier_name, _past_dt(365)))

for j in range(26):
    ti = _rng.randint(0, len(PRODUCT_TEMPLATES) - 1)
    style, category, mat_idx, price_range = PRODUCT_TEMPLATES[ti]
    color_name, color_code = _rng.choice(COLORS)
    size = _rng.choice(SIZES)
    collection = _rng.choice(COLLECTIONS)
    season = _rng.choice(SEASONS)
    supplier_name, country = _rng.choice(SUPPLIERS)
    price = round(_rng.uniform(*price_range), 2)
    vid = len(products) + 1
    sku = f"HB-{collection[:4].upper()}-{category[:3].upper()}-{2000 + vid:04d}"
    products.append((vid, sku, style, color_name, color_code, size, category, collection, season,
                     MATERIALS[mat_idx], price, "active", country, supplier_name, _past_dt(300)))

product_schema = StructType([
    StructField("id", IntegerType()), StructField("sku", StringType()),
    StructField("style_name", StringType()), StructField("color", StringType()),
    StructField("color_code", StringType()), StructField("size", StringType()),
    StructField("category", StringType()), StructField("collection", StringType()),
    StructField("season", StringType()), StructField("material", StringType()),
    StructField("price", DoubleType()), StructField("status", StringType()),
    StructField("country_of_origin", StringType()), StructField("supplier_name", StringType()),
    StructField("created_at", TimestampType()),
])
spark.createDataFrame(products, product_schema).write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.hb_products")
print(f"HB Products: {len(products)} rows")

# COMMAND ----------

# Recognition Jobs
rj_rows = []
for i in range(40):
    is_batch = _rng.random() < 0.25
    img_count = _rng.randint(5, 50) if is_batch else 1
    statuses = ["completed"] * 7 + ["pending", "processing", "failed"]
    status = _rng.choice(statuses)
    completed_count = img_count if status == "completed" else (_rng.randint(0, img_count) if status == "processing" else 0)
    created = _past_dt(60)
    completed = created + timedelta(seconds=_rng.randint(2, 30)) if status == "completed" else None
    job_type = "batch" if is_batch else "single"
    user_roles = ["store_associate", "warehouse_staff", "buyer", "brand_protection", "sustainability_team", "admin"]
    user_role = _rng.choice(user_roles)
    submitted = _rng.choice(INSPECTORS + ["Store App", "Warehouse Scanner"])
    rj_rows.append((i+1, job_type, status, user_role, submitted, img_count, completed_count, created, completed))

rj_schema = StructType([
    StructField("id", IntegerType()), StructField("job_type", StringType()),
    StructField("status", StringType()), StructField("user_role", StringType()),
    StructField("submitted_by", StringType()), StructField("image_count", IntegerType()),
    StructField("completed_count", IntegerType()), StructField("created_at", TimestampType()),
    StructField("completed_at", TimestampType()),
])
spark.createDataFrame(rj_rows, rj_schema).write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.hb_recognition_jobs")
print(f"Recognition Jobs: {len(rj_rows)} rows")

# COMMAND ----------

# Quality Inspections
insp_data = []
qi_rows = []
for i in range(35):
    pid = _rng.randint(1, len(products))
    insp_statuses = ["approved"] * 5 + ["rejected", "pending", "in_review"]
    status = _rng.choice(insp_statuses)
    score = round(_rng.uniform(70, 100), 1) if status in ("approved", "in_review") else round(_rng.uniform(30, 69), 1)
    created = _past_dt(120)
    completed = created + timedelta(hours=_rng.randint(1, 48)) if status != "pending" else None
    batch = f"BATCH-{_rng.randint(2024, 2026)}-{_rng.randint(1000, 9999)}"
    inspector = _rng.choice(INSPECTORS)
    partner = _rng.choice(MANUFACTURING_PARTNERS)
    notes = f"Routine quality check for batch. {'All criteria met.' if score > 80 else 'Defects detected, review required.'}" if _rng.random() < 0.6 else None
    insp_data.append((pid, score, status, created))
    qi_rows.append((i+1, pid, batch, inspector, partner, score, status, notes, created, completed))

qi_schema = StructType([
    StructField("id", IntegerType()), StructField("product_id", IntegerType()),
    StructField("batch_number", StringType()), StructField("inspector", StringType()),
    StructField("manufacturing_partner", StringType()), StructField("overall_score", DoubleType()),
    StructField("status", StringType()), StructField("notes", StringType()),
    StructField("created_at", TimestampType()), StructField("completed_at", TimestampType()),
])
spark.createDataFrame(qi_rows, qi_schema).write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.hb_quality_inspections")
print(f"Quality Inspections: {len(qi_rows)} rows")

# COMMAND ----------

# Quality Defects
defect_types = ["stitching_error", "color_variation", "fabric_flaw", "size_deviation", "label_error", "button_defect", "zipper_issue", "print_misalignment"]
defect_severities = ["minor"] * 4 + ["moderate"] * 3 + ["major", "critical"]
defect_locations = ["Left shoulder seam", "Right cuff area", "Front panel center", "Back collar region",
                    "Button placket", "Lapel edge", "Hem area", "Sleeve attachment point",
                    "Pocket lining", "Zipper track", "Inner lining", "Waistband"]
qd_rows = []
did = 1
for insp_idx, (pid, score, status, created) in enumerate(insp_data):
    n_defects = 0 if score > 90 else (_rng.randint(1, 2) if score > 70 else _rng.randint(2, 5))
    for _ in range(n_defects):
        dt = _rng.choice(defect_types)
        sev = _rng.choice(defect_severities)
        loc = _rng.choice(defect_locations)
        conf = round(_rng.uniform(0.7, 0.99), 3)
        img = f"https://images.hb.example/qc/defect_{insp_idx+1}_{_rng.randint(100,999)}.jpg" if _rng.random() < 0.5 else None
        dc = created + timedelta(minutes=_rng.randint(5, 120))
        qd_rows.append((did, insp_idx+1, dt, sev, loc, conf, img, dc))
        did += 1

qd_schema = StructType([
    StructField("id", IntegerType()), StructField("inspection_id", IntegerType()),
    StructField("defect_type", StringType()), StructField("severity", StringType()),
    StructField("location_description", StringType()), StructField("confidence_score", DoubleType()),
    StructField("image_url", StringType()), StructField("created_at", TimestampType()),
])
spark.createDataFrame(qd_rows, qd_schema).write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.hb_quality_defects")
print(f"Quality Defects: {len(qd_rows)} rows")

# COMMAND ----------

# Auth Verifications
ver_data = []
av_rows = []
requester_types = ["internal", "customer", "partner", "marketplace"]
ver_statuses_pool = ["verified"] * 6 + ["suspicious", "counterfeit", "pending"]
ver_methods = ["image_analysis", "nfc_scan", "barcode_verification", "serial_number_check", "ai_comparison"]
for i in range(25):
    pid = _rng.randint(1, len(products)) if _rng.random() < 0.8 else None
    status = _rng.choice(ver_statuses_pool)
    conf = round(_rng.uniform(0.85, 0.99), 3) if status == "verified" else (round(_rng.uniform(0.3, 0.65), 3) if status in ("suspicious", "counterfeit") else None)
    created = _past_dt(90)
    completed = created + timedelta(hours=_rng.randint(1, 72)) if status != "pending" else None
    req_type = _rng.choice(requester_types)
    req_name = _rng.choice(["Customer Service", "Retail Partner Berlin", "E-Commerce Team", "Marketplace Compliance", "Partner: Nordstrom", "Partner: Zalando", "Internal Audit"])
    method = _rng.choice(ver_methods)
    region = _rng.choice(REGIONS)
    notes_val = "Flagged by automated scan." if status == "suspicious" else None
    img = f"https://uploads.hb.example/auth/{_rng.randint(10000,99999)}.jpg" if _rng.random() < 0.7 else None
    ver_data.append((status, region, method, created))
    av_rows.append((i+1, pid, req_type, req_name, f"verify-{_rng.randint(100,999)}@example.com", status, conf, method, img, region, notes_val, created, completed))

av_schema = StructType([
    StructField("id", IntegerType()), StructField("product_id", IntegerType()),
    StructField("requester_type", StringType()), StructField("requester_name", StringType()),
    StructField("requester_email", StringType()), StructField("status", StringType()),
    StructField("confidence_score", DoubleType()), StructField("verification_method", StringType()),
    StructField("image_url", StringType()), StructField("region", StringType()),
    StructField("notes", StringType()), StructField("created_at", TimestampType()),
    StructField("completed_at", TimestampType()),
])
spark.createDataFrame(av_rows, av_schema).write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.hb_auth_verifications")
print(f"Auth Verifications: {len(av_rows)} rows")

# COMMAND ----------

# Auth Alerts
aa_rows = []
aid = 1
for vi, (status, region, method, created) in enumerate(ver_data):
    if status not in ("suspicious", "counterfeit"):
        continue
    alert_type = "Suspected Counterfeit" if status == "counterfeit" else "Quality Anomaly Detected"
    sev = "critical" if status == "counterfeit" else _rng.choice(["medium", "high"])
    inv_by = _rng.choice(INSPECTORS) if _rng.random() < 0.6 else None
    res = _rng.choice(["open", "investigating", "confirmed_counterfeit", "false_positive"])
    ac = created + timedelta(minutes=_rng.randint(5, 60))
    aa_rows.append((aid, vi+1, alert_type, sev, region, f"{alert_type} for verification #{vi+1}. Region: {region}. Method: {method}.", inv_by, res, ac))
    aid += 1

aa_schema = StructType([
    StructField("id", IntegerType()), StructField("verification_id", IntegerType()),
    StructField("alert_type", StringType()), StructField("severity", StringType()),
    StructField("region", StringType()), StructField("description", StringType()),
    StructField("investigated_by", StringType()), StructField("resolution", StringType()),
    StructField("created_at", TimestampType()),
])
spark.createDataFrame(aa_rows, aa_schema).write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.hb_auth_alerts")
print(f"Auth Alerts: {len(aa_rows)} rows")

# COMMAND ----------

# Supply Chain Events
event_flow = ["manufactured", "quality_checked", "shipped", "received_warehouse", "inspected", "distributed", "received_store"]
sc_rows = []
eid = 1
sampled = _rng.sample(range(len(products)), min(35, len(products)))
for pidx in sampled:
    pid = pidx + 1
    base = _past_dt(200)
    n_events = _rng.randint(3, len(event_flow))
    for j in range(n_events):
        loc, country = _rng.choice(LOCATIONS)
        evt_date = base + timedelta(days=j * _rng.randint(2, 14))
        partner = _rng.choice(MANUFACTURING_PARTNERS + ["HB Logistics", "DHL Supply Chain", "Kuehne+Nagel"])
        details = f"{event_flow[j].replace('_', ' ').title()} at {loc}"
        sc_rows.append((eid, pid, event_flow[j], loc, partner, country, details, evt_date, evt_date))
        eid += 1
    if _rng.random() < 0.3:
        sold_date = base + timedelta(days=n_events * 14 + _rng.randint(1, 30))
        loc, country = _rng.choice(LOCATIONS)
        sc_rows.append((eid, pid, "sold", loc, f"HB Store {loc.split(',')[0]}", country, f"Sold at retail store in {loc}", sold_date, sold_date))
        eid += 1

sc_schema = StructType([
    StructField("id", IntegerType()), StructField("product_id", IntegerType()),
    StructField("event_type", StringType()), StructField("location", StringType()),
    StructField("partner_name", StringType()), StructField("country", StringType()),
    StructField("details", StringType()), StructField("event_date", TimestampType()),
    StructField("created_at", TimestampType()),
])
spark.createDataFrame(sc_rows, sc_schema).write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.hb_supply_chain_events")
print(f"Supply Chain Events: {len(sc_rows)} rows")

# COMMAND ----------

# Sustainability Metrics
sm_rows = []
compliance_pool = ["compliant"] * 7 + ["pending_review", "non_compliant"]
cert_options = [
    '{"OEKO-TEX": true, "GOTS": false}',
    '{"OEKO-TEX": true, "GOTS": true, "BCI": true}',
    '{"OEKO-TEX": true}',
    '{"GOTS": true, "RWS": true}',
    '{"BCI": true, "OEKO-TEX": true}',
    None,
]
for i in range(len(products)):
    pid = i + 1
    carbon = round(_rng.uniform(3.0, 45.0), 2)
    water = round(_rng.uniform(50, 2500), 1)
    recycled = round(_rng.uniform(0, 60), 1)
    organic = round(_rng.uniform(0, 80), 1)
    certs = _rng.choice(cert_options)
    compliance = _rng.choice(compliance_pool)
    audit = _past_date(180) if _rng.random() < 0.7 else None
    created = products[i][-1]
    audit_dt = datetime.combine(audit, datetime.min.time()) if audit else None
    sm_rows.append((i+1, pid, carbon, water, recycled, organic, certs, compliance, audit_dt, created))

sm_schema = StructType([
    StructField("id", IntegerType()), StructField("product_id", IntegerType()),
    StructField("carbon_footprint_kg", DoubleType()), StructField("water_usage_liters", DoubleType()),
    StructField("recycled_content_pct", DoubleType()), StructField("organic_material_pct", DoubleType()),
    StructField("certifications", StringType()), StructField("compliance_status", StringType()),
    StructField("last_audit_date", TimestampType()), StructField("created_at", TimestampType()),
])
spark.createDataFrame(sm_rows, sm_schema).write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.hb_sustainability_metrics")
print(f"Sustainability Metrics: {len(sm_rows)} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## MOL ASM Cockpit Data

# COMMAND ----------

SCHEMA = "mac"
random.seed(42)

REGIONS_MOL = [
    ("Hungary West", "Hungary"), ("Hungary East", "Hungary"), ("Budapest Metro", "Hungary"),
    ("Croatia Coastal", "Croatia"), ("Croatia Inland", "Croatia"),
    ("Slovakia West", "Slovakia"), ("Slovakia East", "Slovakia"),
    ("Slovenia", "Slovenia"), ("Czech Republic", "Czech Republic"),
]

STATIONS = [
    (1, "HU-BP-001", "Budapest Andrássy", "Budapest", "Budapest Metro", "Hungary", 47.5025, 19.0636, "urban", True, True, 8, 120.0),
    (2, "HU-BP-002", "Budapest Váci", "Budapest", "Budapest Metro", "Hungary", 47.4979, 19.0402, "urban", True, True, 6, 95.0),
    (3, "HU-BP-003", "Budapest Üllői", "Budapest", "Budapest Metro", "Hungary", 47.4735, 19.0838, "urban", True, False, 10, 110.0),
    (4, "HU-BP-004", "Budapest M0 South", "Budapest", "Budapest Metro", "Hungary", 47.3912, 19.0754, "highway", True, True, 12, 150.0),
    (5, "HU-BP-005", "Budapest Budaörs", "Budaörs", "Budapest Metro", "Hungary", 47.4505, 18.9624, "suburban", True, False, 8, 100.0),
    (6, "HU-BP-006", "Budapest Szentendre", "Szentendre", "Budapest Metro", "Hungary", 47.6696, 19.0713, "suburban", False, False, 6, 70.0),
    (7, "HU-W-001", "Győr M1", "Győr", "Hungary West", "Hungary", 47.6875, 17.6504, "highway", True, True, 10, 130.0),
    (8, "HU-W-002", "Sopron Center", "Sopron", "Hungary West", "Hungary", 47.6816, 16.5845, "urban", True, False, 6, 85.0),
    (9, "HU-W-003", "Szombathely", "Szombathely", "Hungary West", "Hungary", 47.2307, 16.6218, "urban", False, False, 6, 75.0),
    (10, "HU-W-004", "Veszprém", "Veszprém", "Hungary West", "Hungary", 47.0933, 17.9115, "suburban", True, False, 8, 90.0),
    (11, "HU-W-005", "Székesfehérvár M7", "Székesfehérvár", "Hungary West", "Hungary", 47.1861, 18.4221, "highway", True, True, 10, 140.0),
    (12, "HU-W-006", "Zalaegerszeg", "Zalaegerszeg", "Hungary West", "Hungary", 46.8417, 16.8416, "urban", False, False, 6, 65.0),
    (13, "HU-E-001", "Debrecen M35", "Debrecen", "Hungary East", "Hungary", 47.5316, 21.6273, "highway", True, True, 10, 130.0),
    (14, "HU-E-002", "Debrecen Center", "Debrecen", "Hungary East", "Hungary", 47.5318, 21.6261, "urban", True, False, 6, 90.0),
    (15, "HU-E-003", "Miskolc", "Miskolc", "Hungary East", "Hungary", 48.1035, 20.7784, "urban", True, False, 8, 85.0),
    (16, "HU-E-004", "Szeged M5", "Szeged", "Hungary East", "Hungary", 46.2530, 20.1414, "highway", True, True, 10, 120.0),
    (17, "HU-E-005", "Nyíregyháza", "Nyíregyháza", "Hungary East", "Hungary", 47.9555, 21.7178, "suburban", False, False, 6, 70.0),
    (18, "HU-E-006", "Kecskemét", "Kecskemét", "Hungary East", "Hungary", 46.8964, 19.6897, "suburban", True, False, 8, 90.0),
    (19, "HR-C-001", "Zagreb A1 South", "Zagreb", "Croatia Coastal", "Croatia", 45.7770, 15.9819, "highway", True, True, 12, 145.0),
    (20, "HR-C-002", "Split Harbor", "Split", "Croatia Coastal", "Croatia", 43.5081, 16.4402, "urban", True, True, 8, 100.0),
    (21, "HR-C-003", "Rijeka Marina", "Rijeka", "Croatia Coastal", "Croatia", 45.3271, 14.4422, "urban", True, False, 6, 85.0),
    (22, "HR-C-004", "Dubrovnik", "Dubrovnik", "Croatia Coastal", "Croatia", 42.6507, 18.0944, "urban", True, True, 6, 90.0),
    (23, "HR-C-005", "Zadar A1", "Zadar", "Croatia Coastal", "Croatia", 44.1194, 15.2314, "highway", True, False, 10, 120.0),
    (24, "HR-I-001", "Zagreb Center", "Zagreb", "Croatia Inland", "Croatia", 45.8150, 15.9819, "urban", True, True, 8, 105.0),
    (25, "HR-I-002", "Osijek", "Osijek", "Croatia Inland", "Croatia", 45.5511, 18.6939, "suburban", False, False, 6, 70.0),
    (26, "HR-I-003", "Varaždin", "Varaždin", "Croatia Inland", "Croatia", 46.3057, 16.3366, "suburban", True, False, 6, 80.0),
    (27, "SK-W-001", "Bratislava D1", "Bratislava", "Slovakia West", "Slovakia", 48.1486, 17.1077, "highway", True, True, 10, 140.0),
    (28, "SK-W-002", "Bratislava Center", "Bratislava", "Slovakia West", "Slovakia", 48.1462, 17.1073, "urban", True, True, 8, 100.0),
    (29, "SK-W-003", "Trnava", "Trnava", "Slovakia West", "Slovakia", 48.3774, 17.5871, "suburban", True, False, 6, 80.0),
    (30, "SK-W-004", "Nitra", "Nitra", "Slovakia West", "Slovakia", 48.3069, 18.0864, "suburban", False, False, 6, 70.0),
    (31, "SK-E-001", "Košice D1", "Košice", "Slovakia East", "Slovakia", 48.7164, 21.2611, "highway", True, True, 10, 130.0),
    (32, "SK-E-002", "Košice Center", "Košice", "Slovakia East", "Slovakia", 48.7164, 21.2611, "urban", True, False, 6, 85.0),
    (33, "SK-E-003", "Žilina", "Žilina", "Slovakia East", "Slovakia", 49.2231, 18.7397, "urban", True, False, 8, 90.0),
    (34, "SK-E-004", "Banská Bystrica", "Banská Bystrica", "Slovakia East", "Slovakia", 48.7395, 19.1530, "suburban", False, False, 6, 75.0),
    (35, "SI-001", "Ljubljana A1", "Ljubljana", "Slovenia", "Slovenia", 46.0569, 14.5058, "highway", True, True, 10, 135.0),
    (36, "SI-002", "Ljubljana Center", "Ljubljana", "Slovenia", "Slovenia", 46.0511, 14.5051, "urban", True, True, 8, 100.0),
    (37, "SI-003", "Maribor", "Maribor", "Slovenia", "Slovenia", 46.5547, 15.6459, "urban", True, False, 6, 85.0),
    (38, "SI-004", "Celje", "Celje", "Slovenia", "Slovenia", 46.2288, 15.2602, "suburban", False, False, 6, 70.0),
    (39, "CZ-001", "Prague D1", "Prague", "Czech Republic", "Czech Republic", 50.0755, 14.4378, "highway", True, True, 12, 150.0),
    (40, "CZ-002", "Prague Center", "Prague", "Czech Republic", "Czech Republic", 50.0875, 14.4213, "urban", True, True, 8, 110.0),
    (41, "CZ-003", "Brno D1", "Brno", "Czech Republic", "Czech Republic", 49.1951, 16.6068, "highway", True, True, 10, 130.0),
    (42, "CZ-004", "Brno Center", "Brno", "Czech Republic", "Czech Republic", 49.1951, 16.6068, "urban", True, False, 6, 90.0),
    (43, "CZ-005", "Ostrava", "Ostrava", "Czech Republic", "Czech Republic", 49.8209, 18.2625, "suburban", True, False, 8, 85.0),
    (44, "CZ-006", "Plzeň", "Plzeň", "Czech Republic", "Czech Republic", 49.7384, 13.3736, "suburban", False, False, 6, 70.0),
]

station_schema = StructType([
    StructField("id", IntegerType()), StructField("station_code", StringType()),
    StructField("name", StringType()), StructField("city", StringType()),
    StructField("region", StringType()), StructField("country", StringType()),
    StructField("latitude", DoubleType()), StructField("longitude", DoubleType()),
    StructField("station_type", StringType()), StructField("has_fresh_corner", BooleanType()),
    StructField("has_ev_charging", BooleanType()), StructField("num_pumps", IntegerType()),
    StructField("shop_area_sqm", DoubleType()),
])
spark.createDataFrame(STATIONS, station_schema).write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.stations")
print("Stations seeded.")

# COMMAND ----------

FUEL_TYPES = ["diesel", "premium_diesel", "regular_95", "premium_98", "lpg"]
NONFUEL_CATS = ["coffee", "hot_food", "cold_food", "bakery", "beverages", "tobacco", "car_care", "convenience"]
SHIFT_TYPES = ["morning", "afternoon", "night"]
COMPETITORS = ["Shell", "OMV", "Lukoil", "Orlen", "Avia"]

FUEL_BASE = {"diesel": (1.52, 1.38), "premium_diesel": (1.68, 1.48), "regular_95": (1.55, 1.40), "premium_98": (1.72, 1.50), "lpg": (0.78, 0.68)}
FUEL_VOL = {"diesel": (4200, 1200), "premium_diesel": (800, 350), "regular_95": (3500, 1000), "premium_98": (600, 250), "lpg": (500, 200)}

today = date.today()
start = today - timedelta(days=365)
num_days = (today - start).days

fuel_rows, nonfuel_rows, workforce_rows, inv_rows, comp_rows, price_rows = [], [], [], [], [], []

for day_off in range(num_days):
    d = start + timedelta(days=day_off)
    dow = d.weekday()
    is_wknd = dow >= 5
    m_factor = 1.0 + 0.12 * (1.0 if d.month in (6,7,8) else (-0.08 if d.month in (12,1,2) else 0.0))
    w_factor = 1.15 if is_wknd else 1.0

    for s in STATIONS:
        sid = s[0]
        stype = s[8]
        has_fc = s[9]
        t_factor = {"highway": 1.5, "urban": 1.0, "suburban": 0.75}[stype]

        for ft in FUEL_TYPES:
            mean_v, std_v = FUEL_VOL[ft]
            vol = max(0, random.gauss(mean_v * t_factor * m_factor * w_factor, std_v))
            bp, bc = FUEL_BASE[ft]
            price = bp * random.uniform(0.97, 1.03)
            cost = bc * random.uniform(0.97, 1.03)
            fuel_rows.append((sid, d, ft, round(vol,1), round(vol*price,2), round(price,4), round(vol*(price-cost),2)))

        for cat in NONFUEL_CATS:
            bq = {"coffee":120,"hot_food":45,"cold_food":30,"bakery":55,"beverages":60,"tobacco":25,"car_care":8,"convenience":35}[cat]
            if not has_fc and cat in ("hot_food","cold_food","bakery"):
                bq = int(bq * 0.2)
            qty = max(0, int(random.gauss(bq * t_factor * w_factor, bq * 0.25)))
            ap = {"coffee":2.5,"hot_food":4.2,"cold_food":3.5,"bakery":2.0,"beverages":2.8,"tobacco":5.5,"car_care":12.0,"convenience":3.0}[cat]
            mp = {"coffee":0.65,"hot_food":0.55,"cold_food":0.50,"bakery":0.60,"beverages":0.40,"tobacco":0.10,"car_care":0.35,"convenience":0.30}[cat]
            rev = round(qty * ap * random.uniform(0.9, 1.1), 2)
            nonfuel_rows.append((sid, d, cat, qty, rev, round(rev*mp,2)))

        for st in SHIFT_TYPES:
            planned = {"morning":4,"afternoon":3,"night":2}[st]
            if stype == "highway": planned += 1
            actual = max(1, planned + random.choice([-1,0,0,0,0,1]))
            ot = round(max(0, random.gauss(0.5, 0.8)), 1) if actual < planned else 0.0
            workforce_rows.append((sid, d, st, planned, actual, ot))

        for pc in NONFUEL_CATS:
            bs = {"coffee":200,"hot_food":60,"bakery":80,"beverages":150,"cold_food":50,"tobacco":100,"car_care":40,"convenience":120}[pc]
            stock = max(0, int(random.gauss(bs, bs*0.2)))
            rp = int(bs*0.3)
            spoil = random.choices([0,1,2,3,5], weights=[50,25,15,7,3])[0] if pc in ("hot_food","bakery","cold_food") else 0
            so = 1 if stock < rp*0.5 else 0
            inv_rows.append((sid, d, pc, stock, rp, spoil, so, random.random() < 0.15))

        for comp in random.sample(COMPETITORS, 2):
            for ft in ["diesel","regular_95"]:
                bp, _ = FUEL_BASE[ft]
                cp = bp * random.uniform(0.96, 1.04)
                comp_rows.append((sid, d, comp, ft, round(cp, 4)))

        for ft in FUEL_TYPES:
            bp, bc = FUEL_BASE[ft]
            price_rows.append((sid, d, ft, round(bp*random.uniform(0.97,1.03),4), round(bc*random.uniform(0.97,1.03),4)))

print(f"Generated rows: fuel={len(fuel_rows)}, nonfuel={len(nonfuel_rows)}, workforce={len(workforce_rows)}, inv={len(inv_rows)}, comp={len(comp_rows)}, price={len(price_rows)}")

# COMMAND ----------

spark.createDataFrame(fuel_rows, "station_id INT, sale_date DATE, fuel_type STRING, volume_liters DOUBLE, revenue DOUBLE, unit_price DOUBLE, margin DOUBLE").write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.fuel_sales")
print("Fuel sales written.")

spark.createDataFrame(nonfuel_rows, "station_id INT, sale_date DATE, category STRING, quantity INT, revenue DOUBLE, margin DOUBLE").write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.nonfuel_sales")
print("Non-fuel sales written.")

spark.createDataFrame(workforce_rows, "station_id INT, shift_date DATE, shift_type STRING, planned_headcount INT, actual_headcount INT, overtime_hours DOUBLE").write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.workforce_shifts")
print("Workforce shifts written.")

spark.createDataFrame(inv_rows, "station_id INT, record_date DATE, product_category STRING, stock_level INT, reorder_point INT, spoilage_count INT, stock_out_events INT, delivery_scheduled BOOLEAN").write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.inventory")
print("Inventory written.")

spark.createDataFrame(comp_rows, "station_id INT, price_date DATE, competitor_name STRING, fuel_type STRING, price_per_liter DOUBLE").write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.competitor_prices")
print("Competitor prices written.")

spark.createDataFrame(price_rows, "station_id INT, price_date DATE, fuel_type STRING, price_per_liter DOUBLE, cost_per_liter DOUBLE").write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.price_history")
print("Price history written.")

# COMMAND ----------

# Loyalty metrics (monthly)
loyalty_rows = []
for mo in range(12):
    m = date(today.year - 1 + (today.month + mo - 1) // 12, (today.month + mo - 1) % 12 + 1, 1)
    for s in STATIONS:
        bm = int(s[12] * 8)
        loyalty_rows.append((s[0], m, int(random.gauss(bm, bm*0.1)), random.randint(5,50), random.randint(200,2000), round(random.uniform(0.08,0.25),3)))
spark.createDataFrame(loyalty_rows, "station_id INT, month DATE, active_members INT, new_signups INT, points_redeemed INT, loyalty_revenue_share DOUBLE").write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.loyalty_metrics")
print("Loyalty metrics written.")

# Anomaly alerts
alert_templates = [
    ("Fuel volume drop", "fuel_volume", "high", "Diesel volume dropped 28% vs 7-day moving average.", "Investigate local road closures or competitor price changes."),
    ("Hot food spoilage spike", "spoilage", "medium", "Hot food spoilage increased to 12% (threshold: 8%).", "Reduce hot dog batch sizes by 15-20% during 8pm-6am."),
    ("Stock-out risk: Coffee", "stock_out", "high", "Projected to run out of coffee beans within 24 hours.", "Advance replenishment order."),
    ("Understaffing alert", "workforce", "critical", "Morning shift has 2 staff vs 4 planned for 3 consecutive days.", "Reassign staff or activate on-call pool."),
    ("Competitor price undercut", "pricing", "medium", "Competitor undercuts diesel by 0.05 EUR/L.", "Test -0.02 EUR response."),
]
alert_rows = []
a_id = 1
now = datetime.now(timezone.utc)
for title, metric, sev, desc, action in alert_templates:
    for s in random.sample(STATIONS, min(5, len(STATIONS))):
        status = random.choice(["active","active","acknowledged","resolved"])
        det = now - timedelta(hours=random.randint(1,168))
        alert_rows.append((a_id, s[0], metric, sev, title, f"Station {s[1]}: {desc}", action, status, det))
        a_id += 1

spark.createDataFrame(alert_rows, "id INT, station_id INT, metric_type STRING, severity STRING, title STRING, description STRING, suggested_action STRING, status STRING, detected_at TIMESTAMP").write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.anomaly_alerts")
print("Anomaly alerts written.")

print("\n=== All UC tables seeded successfully ===")
