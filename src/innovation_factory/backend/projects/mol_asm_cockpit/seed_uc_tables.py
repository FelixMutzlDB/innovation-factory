"""Seed Unity Catalog tables with mock retail station data for Genie/Dashboard.

Run on a Databricks cluster (requires PySpark). Example:
    %run /Workspace/.../mol_asm_cockpit/seed_uc_tables

Or set the catalog/schema via environment variables:
    MAC_UC_CATALOG, MAC_UC_SCHEMA
"""
import os
import random
from datetime import date, timedelta
from pyspark.sql import SparkSession  # type: ignore[unresolved-import]
from pyspark.sql.types import *  # type: ignore[unresolved-import]

random.seed(42)
spark = SparkSession.builder.getOrCreate()

CATALOG = os.getenv("MAC_UC_CATALOG", "home_felix_mutzl")
SCHEMA = os.getenv("MAC_UC_SCHEMA", "mac")

# --- Regions and Stations ---
REGIONS = [
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

# Insert stations
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

# --- Generate daily fact data ---
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

        for pc in ["coffee","hot_food","bakery","beverages","cold_food","tobacco","car_care","convenience"]:
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

# Write all tables
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
from datetime import datetime
alert_templates = [
    ("Fuel volume drop", "fuel_volume", "high", "Diesel volume dropped 28% vs 7-day moving average.", "Investigate local road closures or competitor price changes."),
    ("Hot food spoilage spike", "spoilage", "medium", "Hot food spoilage increased to 12% (threshold: 8%).", "Reduce hot dog batch sizes by 15-20% during 8pm-6am."),
    ("Stock-out risk: Coffee", "stock_out", "high", "Projected to run out of coffee beans within 24 hours.", "Advance replenishment order."),
    ("Understaffing alert", "workforce", "critical", "Morning shift has 2 staff vs 4 planned for 3 consecutive days.", "Reassign staff or activate on-call pool."),
    ("Competitor price undercut", "pricing", "medium", "Competitor undercuts diesel by 0.05 EUR/L.", "Test -0.02 EUR response."),
]
alert_rows = []
aid = 1
now = datetime.utcnow()
for title, metric, sev, desc, action in alert_templates:
    for s in random.sample(STATIONS, min(5, len(STATIONS))):
        status = random.choice(["active","active","acknowledged","resolved"])
        det = now - timedelta(hours=random.randint(1,168))
        alert_rows.append((aid, s[0], metric, sev, title, f"Station {s[1]}: {desc}", action, status, det))
        aid += 1

spark.createDataFrame(alert_rows, "id INT, station_id INT, metric_type STRING, severity STRING, title STRING, description STRING, suggested_action STRING, status STRING, detected_at TIMESTAMP").write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.anomaly_alerts")
print("Anomaly alerts written.")

print("\n=== All UC tables seeded successfully ===")
