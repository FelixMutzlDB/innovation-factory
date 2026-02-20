"""Seed Hugo Boss Product Center data into Unity Catalog tables.

Run via: python scripts/seed_uc_hb_data.py
Requires: DATABRICKS_CONFIG_PROFILE=e2-demo-field-eng (or equivalent auth)
"""

import random
from datetime import date, datetime, timedelta, timezone

CATALOG = "innovation_factory_catalog"
SCHEMA = "hb_product_center"
_rng = random.Random(77)
TODAY = date.today()


def _past_dt(max_days=180):
    delta = timedelta(days=_rng.randint(1, max_days), hours=_rng.randint(0, 23), minutes=_rng.randint(0, 59))
    return datetime.now(timezone.utc) - delta


def _past_date(max_days=365):
    return TODAY - timedelta(days=_rng.randint(1, max_days))


def ts(dt):
    if dt is None:
        return "NULL"
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return f"'{dt.isoformat()}'"
    return f"'{dt.strftime('%Y-%m-%d %H:%M:%S')}'"


def s(val):
    if val is None:
        return "NULL"
    return "'" + str(val).replace("'", "''") + "'"


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


def generate_products():
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
        products.append((sku, style, color_name, color_code, size, category, collection, season,
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
        vid = 2000 + len(products)
        sku = f"HB-{collection[:4].upper()}-{category[:3].upper()}-{vid:04d}"
        products.append((sku, style, color_name, color_code, size, category, collection, season,
                         MATERIALS[mat_idx], price, "active", country, supplier_name, _past_dt(300)))
    return products


def build_sql():
    products = generate_products()
    stmts = []

    # Products
    rows = []
    for p in products:
        sku, style, color, code, size, cat, coll, sea, mat, price, status, country, supplier, created = p
        rows.append(f"({s(sku)}, {s(style)}, {s(color)}, {s(code)}, {s(size)}, {s(cat)}, {s(coll)}, {s(sea)}, {s(mat)}, {price}, {s(status)}, {s(country)}, {s(supplier)}, {ts(created)})")
    stmts.append(f"INSERT INTO {CATALOG}.{SCHEMA}.hb_products (sku, style_name, color, color_code, size, category, collection, season, material, price, status, country_of_origin, supplier_name, created_at) VALUES\n" + ",\n".join(rows))

    # Recognition Jobs
    rows = []
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
        rows.append(f"({s(job_type)}, {s(status)}, {s(user_role)}, {s(submitted)}, {img_count}, {completed_count}, {ts(created)}, {ts(completed)})")
    stmts.append(f"INSERT INTO {CATALOG}.{SCHEMA}.hb_recognition_jobs (job_type, status, user_role, submitted_by, image_count, completed_count, created_at, completed_at) VALUES\n" + ",\n".join(rows))

    # Quality Inspections
    insp_data = []
    rows = []
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
        rows.append(f"({pid}, {s(batch)}, {s(inspector)}, {s(partner)}, {score}, {s(status)}, {s(notes)}, {ts(created)}, {ts(completed)})")
    stmts.append(f"INSERT INTO {CATALOG}.{SCHEMA}.hb_quality_inspections (product_id, batch_number, inspector, manufacturing_partner, overall_score, status, notes, created_at, completed_at) VALUES\n" + ",\n".join(rows))

    # Quality Defects
    rows = []
    defect_types = ["stitching_error", "color_variation", "fabric_flaw", "size_deviation", "label_error", "button_defect", "zipper_issue", "print_misalignment"]
    defect_severities = ["minor"] * 4 + ["moderate"] * 3 + ["major", "critical"]
    defect_locations = ["Left shoulder seam", "Right cuff area", "Front panel center", "Back collar region",
                        "Button placket", "Lapel edge", "Hem area", "Sleeve attachment point",
                        "Pocket lining", "Zipper track", "Inner lining", "Waistband"]
    for insp_idx, (pid, score, status, created) in enumerate(insp_data):
        n_defects = 0 if score > 90 else (_rng.randint(1, 2) if score > 70 else _rng.randint(2, 5))
        for _ in range(n_defects):
            dt = _rng.choice(defect_types)
            sev = _rng.choice(defect_severities)
            loc = _rng.choice(defect_locations)
            conf = round(_rng.uniform(0.7, 0.99), 3)
            img = f"https://images.hugoboss.com/qc/defect_{insp_idx+1}_{_rng.randint(100,999)}.jpg" if _rng.random() < 0.5 else None
            dc = created + timedelta(minutes=_rng.randint(5, 120))
            rows.append(f"({insp_idx+1}, {s(dt)}, {s(sev)}, {s(loc)}, {conf}, {s(img)}, {ts(dc)})")
    if rows:
        stmts.append(f"INSERT INTO {CATALOG}.{SCHEMA}.hb_quality_defects (inspection_id, defect_type, severity, location_description, confidence_score, image_url, created_at) VALUES\n" + ",\n".join(rows))

    # Auth Verifications
    ver_data = []
    rows = []
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
        img = f"https://uploads.hugoboss.com/auth/{_rng.randint(10000,99999)}.jpg" if _rng.random() < 0.7 else None
        ver_data.append((status, region, method, created))
        pid_val = str(pid) if pid else "NULL"
        conf_val = str(conf) if conf is not None else "NULL"
        rows.append(f"({pid_val}, {s(req_type)}, {s(req_name)}, {s(f'verify-{_rng.randint(100,999)}@hugoboss.com')}, {s(status)}, {conf_val}, {s(method)}, {s(img)}, {s(region)}, {s(notes_val)}, {ts(created)}, {ts(completed)})")
    stmts.append(f"INSERT INTO {CATALOG}.{SCHEMA}.hb_auth_verifications (product_id, requester_type, requester_name, requester_email, status, confidence_score, verification_method, image_url, region, notes, created_at, completed_at) VALUES\n" + ",\n".join(rows))

    # Auth Alerts
    rows = []
    for vi, (status, region, method, created) in enumerate(ver_data):
        if status not in ("suspicious", "counterfeit"):
            continue
        alert_type = "Suspected Counterfeit" if status == "counterfeit" else "Quality Anomaly Detected"
        sev = "critical" if status == "counterfeit" else _rng.choice(["medium", "high"])
        inv_by = _rng.choice(INSPECTORS) if _rng.random() < 0.6 else None
        res = _rng.choice(["open", "investigating", "confirmed_counterfeit", "false_positive"])
        ac = created + timedelta(minutes=_rng.randint(5, 60))
        rows.append(f"({vi+1}, {s(alert_type)}, {s(sev)}, {s(region)}, {s(f'{alert_type} for verification #{vi+1}. Region: {region}. Method: {method}.')}, {s(inv_by)}, {s(res)}, {ts(ac)})")
    if rows:
        stmts.append(f"INSERT INTO {CATALOG}.{SCHEMA}.hb_auth_alerts (verification_id, alert_type, severity, region, description, investigated_by, resolution, created_at) VALUES\n" + ",\n".join(rows))

    # Supply Chain Events
    event_flow = ["manufactured", "quality_checked", "shipped", "received_warehouse", "inspected", "distributed", "received_store"]
    rows = []
    sampled = _rng.sample(range(len(products)), min(35, len(products)))
    for pidx in sampled:
        pid = pidx + 1
        base = _past_dt(200)
        n_events = _rng.randint(3, len(event_flow))
        for j in range(n_events):
            loc, country = _rng.choice(LOCATIONS)
            evt_date = base + timedelta(days=j * _rng.randint(2, 14))
            partner = _rng.choice(MANUFACTURING_PARTNERS + ["Hugo Boss Logistics", "DHL Supply Chain", "Kuehne+Nagel"])
            details = f"{event_flow[j].replace('_', ' ').title()} at {loc}"
            rows.append(f"({pid}, {s(event_flow[j])}, {s(loc)}, {s(partner)}, {s(country)}, {s(details)}, {ts(evt_date)}, {ts(evt_date)})")
        if _rng.random() < 0.3:
            sold_date = base + timedelta(days=n_events * 14 + _rng.randint(1, 30))
            loc, country = _rng.choice(LOCATIONS)
            rows.append(f"({pid}, 'sold', {s(loc)}, {s('Hugo Boss Store ' + loc.split(',')[0])}, {s(country)}, {s(f'Sold at retail store in {loc}')}, {ts(sold_date)}, {ts(sold_date)})")
    stmts.append(f"INSERT INTO {CATALOG}.{SCHEMA}.hb_supply_chain_events (product_id, event_type, location, partner_name, country, details, event_date, created_at) VALUES\n" + ",\n".join(rows))

    # Sustainability Metrics
    rows = []
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
        rows.append(f"({pid}, {carbon}, {water}, {recycled}, {organic}, {s(certs)}, {s(compliance)}, {ts(audit)}, {ts(created)})")
    stmts.append(f"INSERT INTO {CATALOG}.{SCHEMA}.hb_sustainability_metrics (product_id, carbon_footprint_kg, water_usage_liters, recycled_content_pct, organic_material_pct, certifications, compliance_status, last_audit_date, created_at) VALUES\n" + ",\n".join(rows))

    return stmts


if __name__ == "__main__":
    stmts = build_sql()
    for i, stmt in enumerate(stmts):
        print(f"--- Statement {i+1} ---")
        print(stmt[:200] + "...")
        print()
