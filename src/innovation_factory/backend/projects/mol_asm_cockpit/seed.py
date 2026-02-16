"""Seed script for the ASM Cockpit project.

Generates ~50 stations across CEE with 12 months of daily fact data for fuel
sales, non-fuel sales, loyalty, workforce, inventory, competitor prices,
price history, anomaly alerts, issues, and customer profiles.
"""

import random
from datetime import date, datetime, timedelta
from sqlmodel import Session, select

from .models import (
    MacRegion,
    MacStation,
    StationType,
    FuelType,
    NonfuelCategory,
    ShiftType,
    ProductCategory,
    MacFuelSale,
    MacNonfuelSale,
    MacLoyaltyMetric,
    MacWorkforceShift,
    MacInventory,
    MacCompetitorPrice,
    MacPriceHistory,
    MacAnomalyAlert,
    AlertSeverity,
    AlertStatus,
    MacIssue,
    IssueStatus,
    IssueCategory,
    MacCustomerProfile,
    MacCustomerContract,
    LoyaltyTier,
)

random.seed(42)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REGIONS = [
    ("Hungary West", "Hungary"),
    ("Hungary East", "Hungary"),
    ("Budapest Metro", "Hungary"),
    ("Croatia Coastal", "Croatia"),
    ("Croatia Inland", "Croatia"),
    ("Slovakia West", "Slovakia"),
    ("Slovakia East", "Slovakia"),
    ("Slovenia", "Slovenia"),
    ("Czech Republic", "Czech Republic"),
]

STATION_DATA: list[dict] = [
    # Budapest Metro
    {"code": "HU-BP-001", "name": "Budapest Andrássy", "city": "Budapest", "region": "Budapest Metro", "lat": 47.5025, "lon": 19.0636, "type": StationType.urban, "fc": True, "ev": True, "pumps": 8, "shop": 120},
    {"code": "HU-BP-002", "name": "Budapest Váci", "city": "Budapest", "region": "Budapest Metro", "lat": 47.4979, "lon": 19.0402, "type": StationType.urban, "fc": True, "ev": True, "pumps": 6, "shop": 95},
    {"code": "HU-BP-003", "name": "Budapest Üllői", "city": "Budapest", "region": "Budapest Metro", "lat": 47.4735, "lon": 19.0838, "type": StationType.urban, "fc": True, "ev": False, "pumps": 10, "shop": 110},
    {"code": "HU-BP-004", "name": "Budapest M0 South", "city": "Budapest", "region": "Budapest Metro", "lat": 47.3912, "lon": 19.0754, "type": StationType.highway, "fc": True, "ev": True, "pumps": 12, "shop": 150},
    {"code": "HU-BP-005", "name": "Budapest Budaörs", "city": "Budaörs", "region": "Budapest Metro", "lat": 47.4505, "lon": 18.9624, "type": StationType.suburban, "fc": True, "ev": False, "pumps": 8, "shop": 100},
    {"code": "HU-BP-006", "name": "Budapest Szentendre", "city": "Szentendre", "region": "Budapest Metro", "lat": 47.6696, "lon": 19.0713, "type": StationType.suburban, "fc": False, "ev": False, "pumps": 6, "shop": 70},
    # Hungary West
    {"code": "HU-W-001", "name": "Győr M1", "city": "Győr", "region": "Hungary West", "lat": 47.6875, "lon": 17.6504, "type": StationType.highway, "fc": True, "ev": True, "pumps": 10, "shop": 130},
    {"code": "HU-W-002", "name": "Sopron Center", "city": "Sopron", "region": "Hungary West", "lat": 47.6816, "lon": 16.5845, "type": StationType.urban, "fc": True, "ev": False, "pumps": 6, "shop": 85},
    {"code": "HU-W-003", "name": "Szombathely", "city": "Szombathely", "region": "Hungary West", "lat": 47.2307, "lon": 16.6218, "type": StationType.urban, "fc": False, "ev": False, "pumps": 6, "shop": 75},
    {"code": "HU-W-004", "name": "Veszprém", "city": "Veszprém", "region": "Hungary West", "lat": 47.0933, "lon": 17.9115, "type": StationType.suburban, "fc": True, "ev": False, "pumps": 8, "shop": 90},
    {"code": "HU-W-005", "name": "Székesfehérvár M7", "city": "Székesfehérvár", "region": "Hungary West", "lat": 47.1861, "lon": 18.4221, "type": StationType.highway, "fc": True, "ev": True, "pumps": 10, "shop": 140},
    {"code": "HU-W-006", "name": "Zalaegerszeg", "city": "Zalaegerszeg", "region": "Hungary West", "lat": 46.8417, "lon": 16.8416, "type": StationType.urban, "fc": False, "ev": False, "pumps": 6, "shop": 65},
    # Hungary East
    {"code": "HU-E-001", "name": "Debrecen M35", "city": "Debrecen", "region": "Hungary East", "lat": 47.5316, "lon": 21.6273, "type": StationType.highway, "fc": True, "ev": True, "pumps": 10, "shop": 130},
    {"code": "HU-E-002", "name": "Debrecen Center", "city": "Debrecen", "region": "Hungary East", "lat": 47.5318, "lon": 21.6261, "type": StationType.urban, "fc": True, "ev": False, "pumps": 6, "shop": 90},
    {"code": "HU-E-003", "name": "Miskolc", "city": "Miskolc", "region": "Hungary East", "lat": 48.1035, "lon": 20.7784, "type": StationType.urban, "fc": True, "ev": False, "pumps": 8, "shop": 85},
    {"code": "HU-E-004", "name": "Szeged M5", "city": "Szeged", "region": "Hungary East", "lat": 46.2530, "lon": 20.1414, "type": StationType.highway, "fc": True, "ev": True, "pumps": 10, "shop": 120},
    {"code": "HU-E-005", "name": "Nyíregyháza", "city": "Nyíregyháza", "region": "Hungary East", "lat": 47.9555, "lon": 21.7178, "type": StationType.suburban, "fc": False, "ev": False, "pumps": 6, "shop": 70},
    {"code": "HU-E-006", "name": "Kecskemét", "city": "Kecskemét", "region": "Hungary East", "lat": 46.8964, "lon": 19.6897, "type": StationType.suburban, "fc": True, "ev": False, "pumps": 8, "shop": 90},
    # Croatia Coastal
    {"code": "HR-C-001", "name": "Zagreb A1 South", "city": "Zagreb", "region": "Croatia Coastal", "lat": 45.7770, "lon": 15.9819, "type": StationType.highway, "fc": True, "ev": True, "pumps": 12, "shop": 145},
    {"code": "HR-C-002", "name": "Split Harbor", "city": "Split", "region": "Croatia Coastal", "lat": 43.5081, "lon": 16.4402, "type": StationType.urban, "fc": True, "ev": True, "pumps": 8, "shop": 100},
    {"code": "HR-C-003", "name": "Rijeka Marina", "city": "Rijeka", "region": "Croatia Coastal", "lat": 45.3271, "lon": 14.4422, "type": StationType.urban, "fc": True, "ev": False, "pumps": 6, "shop": 85},
    {"code": "HR-C-004", "name": "Dubrovnik", "city": "Dubrovnik", "region": "Croatia Coastal", "lat": 42.6507, "lon": 18.0944, "type": StationType.urban, "fc": True, "ev": True, "pumps": 6, "shop": 90},
    {"code": "HR-C-005", "name": "Zadar A1", "city": "Zadar", "region": "Croatia Coastal", "lat": 44.1194, "lon": 15.2314, "type": StationType.highway, "fc": True, "ev": False, "pumps": 10, "shop": 120},
    # Croatia Inland
    {"code": "HR-I-001", "name": "Zagreb Center", "city": "Zagreb", "region": "Croatia Inland", "lat": 45.8150, "lon": 15.9819, "type": StationType.urban, "fc": True, "ev": True, "pumps": 8, "shop": 105},
    {"code": "HR-I-002", "name": "Osijek", "city": "Osijek", "region": "Croatia Inland", "lat": 45.5511, "lon": 18.6939, "type": StationType.suburban, "fc": False, "ev": False, "pumps": 6, "shop": 70},
    {"code": "HR-I-003", "name": "Varaždin", "city": "Varaždin", "region": "Croatia Inland", "lat": 46.3057, "lon": 16.3366, "type": StationType.suburban, "fc": True, "ev": False, "pumps": 6, "shop": 80},
    # Slovakia West
    {"code": "SK-W-001", "name": "Bratislava D1", "city": "Bratislava", "region": "Slovakia West", "lat": 48.1486, "lon": 17.1077, "type": StationType.highway, "fc": True, "ev": True, "pumps": 10, "shop": 140},
    {"code": "SK-W-002", "name": "Bratislava Center", "city": "Bratislava", "region": "Slovakia West", "lat": 48.1462, "lon": 17.1073, "type": StationType.urban, "fc": True, "ev": True, "pumps": 8, "shop": 100},
    {"code": "SK-W-003", "name": "Trnava", "city": "Trnava", "region": "Slovakia West", "lat": 48.3774, "lon": 17.5871, "type": StationType.suburban, "fc": True, "ev": False, "pumps": 6, "shop": 80},
    {"code": "SK-W-004", "name": "Nitra", "city": "Nitra", "region": "Slovakia West", "lat": 48.3069, "lon": 18.0864, "type": StationType.suburban, "fc": False, "ev": False, "pumps": 6, "shop": 70},
    # Slovakia East
    {"code": "SK-E-001", "name": "Košice D1", "city": "Košice", "region": "Slovakia East", "lat": 48.7164, "lon": 21.2611, "type": StationType.highway, "fc": True, "ev": True, "pumps": 10, "shop": 130},
    {"code": "SK-E-002", "name": "Košice Center", "city": "Košice", "region": "Slovakia East", "lat": 48.7164, "lon": 21.2611, "type": StationType.urban, "fc": True, "ev": False, "pumps": 6, "shop": 85},
    {"code": "SK-E-003", "name": "Žilina", "city": "Žilina", "region": "Slovakia East", "lat": 49.2231, "lon": 18.7397, "type": StationType.urban, "fc": True, "ev": False, "pumps": 8, "shop": 90},
    {"code": "SK-E-004", "name": "Banská Bystrica", "city": "Banská Bystrica", "region": "Slovakia East", "lat": 48.7395, "lon": 19.1530, "type": StationType.suburban, "fc": False, "ev": False, "pumps": 6, "shop": 75},
    # Slovenia
    {"code": "SI-001", "name": "Ljubljana A1", "city": "Ljubljana", "region": "Slovenia", "lat": 46.0569, "lon": 14.5058, "type": StationType.highway, "fc": True, "ev": True, "pumps": 10, "shop": 135},
    {"code": "SI-002", "name": "Ljubljana Center", "city": "Ljubljana", "region": "Slovenia", "lat": 46.0511, "lon": 14.5051, "type": StationType.urban, "fc": True, "ev": True, "pumps": 8, "shop": 100},
    {"code": "SI-003", "name": "Maribor", "city": "Maribor", "region": "Slovenia", "lat": 46.5547, "lon": 15.6459, "type": StationType.urban, "fc": True, "ev": False, "pumps": 6, "shop": 85},
    {"code": "SI-004", "name": "Celje", "city": "Celje", "region": "Slovenia", "lat": 46.2288, "lon": 15.2602, "type": StationType.suburban, "fc": False, "ev": False, "pumps": 6, "shop": 70},
    # Czech Republic
    {"code": "CZ-001", "name": "Prague D1", "city": "Prague", "region": "Czech Republic", "lat": 50.0755, "lon": 14.4378, "type": StationType.highway, "fc": True, "ev": True, "pumps": 12, "shop": 150},
    {"code": "CZ-002", "name": "Prague Center", "city": "Prague", "region": "Czech Republic", "lat": 50.0875, "lon": 14.4213, "type": StationType.urban, "fc": True, "ev": True, "pumps": 8, "shop": 110},
    {"code": "CZ-003", "name": "Brno D1", "city": "Brno", "region": "Czech Republic", "lat": 49.1951, "lon": 16.6068, "type": StationType.highway, "fc": True, "ev": True, "pumps": 10, "shop": 130},
    {"code": "CZ-004", "name": "Brno Center", "city": "Brno", "region": "Czech Republic", "lat": 49.1951, "lon": 16.6068, "type": StationType.urban, "fc": True, "ev": False, "pumps": 6, "shop": 90},
    {"code": "CZ-005", "name": "Ostrava", "city": "Ostrava", "region": "Czech Republic", "lat": 49.8209, "lon": 18.2625, "type": StationType.suburban, "fc": True, "ev": False, "pumps": 8, "shop": 85},
    {"code": "CZ-006", "name": "Plzeň", "city": "Plzeň", "region": "Czech Republic", "lat": 49.7384, "lon": 13.3736, "type": StationType.suburban, "fc": False, "ev": False, "pumps": 6, "shop": 70},
]

COMPETITORS = ["Shell", "OMV", "Lukoil", "Orlen", "Avia"]

FUEL_BASE_PRICES: dict[str, tuple[float, float]] = {
    # (price_per_liter, cost_per_liter) in EUR
    "diesel": (1.52, 1.38),
    "premium_diesel": (1.68, 1.48),
    "regular_95": (1.55, 1.40),
    "premium_98": (1.72, 1.50),
    "lpg": (0.78, 0.68),
}

FUEL_DAILY_VOLUME: dict[str, tuple[float, float]] = {
    # (mean_liters, std) per station per day
    "diesel": (4200, 1200),
    "premium_diesel": (800, 350),
    "regular_95": (3500, 1000),
    "premium_98": (600, 250),
    "lpg": (500, 200),
}


# ---------------------------------------------------------------------------
# Seed Functions
# ---------------------------------------------------------------------------


def seed_mac_data(session: Session):
    """Seed all ASM Cockpit data."""
    if session.exec(select(MacRegion)).first():
        return

    # Disable psycopg3 prepared statements - PGLite WASM doesn't handle them correctly
    try:
        raw_conn = session.connection().connection.dbapi_connection
        raw_conn.prepare_threshold = None  # type: ignore[invalid-assignment]
    except Exception:
        pass  # Non-psycopg3 driver or different connection wrapper

    print("  Seeding ASM Cockpit data...")
    regions = _seed_regions(session)
    stations = _seed_stations(session, regions)
    _seed_daily_facts(session, stations)
    _seed_anomaly_alerts(session, stations)
    _seed_issues(session, stations)
    _seed_customer_profiles(session)
    session.commit()
    print("  ASM Cockpit data seeded.")


def _seed_regions(session: Session) -> dict[str, MacRegion]:
    """Create regions and return name->region mapping."""
    region_map: dict[str, MacRegion] = {}
    for name, country in REGIONS:
        r = MacRegion(name=name, country=country)
        session.add(r)
        region_map[name] = r
    session.flush()
    return region_map


def _seed_stations(session: Session, regions: dict[str, MacRegion]) -> list[MacStation]:
    """Create stations and return the list."""
    stations: list[MacStation] = []
    for sd in STATION_DATA:
        s = MacStation(
            station_code=sd["code"],
            name=sd["name"],
            city=sd["city"],
            region_id=regions[sd["region"]].id,
            latitude=sd["lat"],
            longitude=sd["lon"],
            station_type=sd["type"],
            has_fresh_corner=sd["fc"],
            has_ev_charging=sd["ev"],
            num_pumps=sd["pumps"],
            shop_area_sqm=sd["shop"],
            opened_date=date(random.randint(2005, 2022), random.randint(1, 12), 1),
        )
        session.add(s)
        stations.append(s)
    session.flush()
    return stations


def _seed_daily_facts(session: Session, stations: list[MacStation]):
    """Generate daily fact data for all stations (last 14 days for dev).

    Uses per-station flushing to keep INSERT statements small enough for PGLite.
    """
    today = date.today()
    start = today - timedelta(days=14)
    num_days = (today - start).days

    for day_offset in range(num_days):
        d = start + timedelta(days=day_offset)
        dow = d.weekday()  # 0=Mon
        is_weekend = dow >= 5
        month_factor = 1.0 + 0.12 * (1.0 if d.month in (6, 7, 8) else (-0.08 if d.month in (12, 1, 2) else 0.0))
        weekend_factor = 1.15 if is_weekend else 1.0

        for station in stations:
            type_factor = {"highway": 1.5, "urban": 1.0, "suburban": 0.75}[station.station_type.value]
            records: list = []

            # ---- Fuel Sales ----
            for ft in FuelType:
                mean_vol, std_vol = FUEL_DAILY_VOLUME[ft.value]
                vol = max(0, random.gauss(mean_vol * type_factor * month_factor * weekend_factor, std_vol))
                base_price, base_cost = FUEL_BASE_PRICES[ft.value]
                price = base_price * random.uniform(0.97, 1.03)
                cost = base_cost * random.uniform(0.97, 1.03)
                records.append(MacFuelSale(
                    station_id=station.id, sale_date=d, fuel_type=ft,
                    volume_liters=round(vol, 1),
                    revenue=round(vol * price, 2),
                    unit_price=round(price, 4),
                    margin=round(vol * (price - cost), 2),
                ))

            # ---- Non-Fuel Sales ----
            for cat in NonfuelCategory:
                base_qty = {"coffee": 120, "hot_food": 45, "cold_food": 30, "bakery": 55,
                            "beverages": 60, "tobacco": 25, "car_care": 8, "convenience": 35}[cat.value]
                if not station.has_fresh_corner and cat.value in ("hot_food", "cold_food", "bakery"):
                    base_qty = int(base_qty * 0.2)
                qty = max(0, int(random.gauss(base_qty * type_factor * weekend_factor, base_qty * 0.25)))
                avg_price = {"coffee": 2.5, "hot_food": 4.2, "cold_food": 3.5, "bakery": 2.0,
                             "beverages": 2.8, "tobacco": 5.5, "car_care": 12.0, "convenience": 3.0}[cat.value]
                margin_pct = {"coffee": 0.65, "hot_food": 0.55, "cold_food": 0.50, "bakery": 0.60,
                              "beverages": 0.40, "tobacco": 0.10, "car_care": 0.35, "convenience": 0.30}[cat.value]
                rev = round(qty * avg_price * random.uniform(0.9, 1.1), 2)
                records.append(MacNonfuelSale(
                    station_id=station.id, sale_date=d, category=cat,
                    quantity=qty, revenue=rev, margin=round(rev * margin_pct, 2),
                ))

            # ---- Workforce Shifts ----
            for st in ShiftType:
                planned = {"morning": 4, "afternoon": 3, "night": 2}[st.value]
                if station.station_type == StationType.highway:
                    planned += 1
                actual = planned + random.choice([-1, 0, 0, 0, 0, 1])
                actual = max(1, actual)
                ot = round(max(0, random.gauss(0.5, 0.8)), 1) if actual < planned else 0.0
                records.append(MacWorkforceShift(
                    station_id=station.id, shift_date=d, shift_type=st,
                    planned_headcount=planned, actual_headcount=actual, overtime_hours=ot,
                ))

            # ---- Inventory ----
            for pc in [ProductCategory.coffee, ProductCategory.hot_food, ProductCategory.bakery,
                       ProductCategory.beverages, ProductCategory.cold_food,
                       ProductCategory.tobacco, ProductCategory.car_care, ProductCategory.convenience]:
                base_stock = {"coffee": 200, "hot_food": 60, "bakery": 80, "beverages": 150,
                              "cold_food": 50, "tobacco": 100, "car_care": 40, "convenience": 120}[pc.value]
                stock = max(0, int(random.gauss(base_stock, base_stock * 0.2)))
                reorder = int(base_stock * 0.3)
                spoilage = 0
                if pc.value in ("hot_food", "bakery", "cold_food"):
                    spoilage = random.choices([0, 1, 2, 3, 5], weights=[50, 25, 15, 7, 3])[0]
                stock_out = 1 if stock < reorder * 0.5 else 0
                records.append(MacInventory(
                    station_id=station.id, record_date=d, product_category=pc,
                    stock_level=stock, reorder_point=reorder, spoilage_count=spoilage,
                    stock_out_events=stock_out,
                    delivery_scheduled=random.random() < 0.15,
                ))

            # ---- Competitor Prices ----
            chosen_comps = random.sample(COMPETITORS, 2)
            for comp in chosen_comps:
                for ft in [FuelType.diesel, FuelType.regular_95]:
                    base_price, _ = FUEL_BASE_PRICES[ft.value]
                    comp_price = base_price * random.uniform(0.96, 1.04)
                    records.append(MacCompetitorPrice(
                        station_id=station.id, price_date=d,
                        competitor_name=comp, fuel_type=ft,
                        price_per_liter=round(comp_price, 4),
                    ))

            # ---- Price History ----
            for ft in FuelType:
                base_price, base_cost = FUEL_BASE_PRICES[ft.value]
                records.append(MacPriceHistory(
                    station_id=station.id, price_date=d, fuel_type=ft,
                    price_per_liter=round(base_price * random.uniform(0.97, 1.03), 4),
                    cost_per_liter=round(base_cost * random.uniform(0.97, 1.03), 4),
                ))

            # Flush per station-day (~33 records) to keep INSERTs small for PGLite
            session.add_all(records)
            session.flush()

    # ---- Loyalty Metrics (monthly) ----
    for month_offset in range(12):
        m = date(today.year - 1 + (today.month + month_offset - 1) // 12,
                 (today.month + month_offset - 1) % 12 + 1, 1)
        for station in stations:
            base_members = int(station.shop_area_sqm * 8)
            session.add(MacLoyaltyMetric(
                station_id=station.id, month=m,
                active_members=int(random.gauss(base_members, base_members * 0.1)),
                new_signups=random.randint(5, 50),
                points_redeemed=random.randint(200, 2000),
                loyalty_revenue_share=round(random.uniform(0.08, 0.25), 3),
            ))
        session.flush()

    print("    Daily facts seeded (14 days).")


def _seed_anomaly_alerts(session: Session, stations: list[MacStation]):
    """Generate a mix of active and resolved anomaly alerts."""
    alert_templates = [
        ("Fuel volume drop", "fuel_volume", AlertSeverity.high,
         "Station {code} diesel volume dropped 28% vs 7-day moving average.",
         "Investigate local road closures or competitor price changes. Consider temporary promo pricing."),
        ("Hot food spoilage spike", "spoilage", AlertSeverity.medium,
         "Station {code} hot food spoilage increased to 12% (threshold: 8%).",
         "Reduce hot dog batch sizes by 15-20% during 8pm-6am. Review demand forecast accuracy."),
        ("Stock-out risk: Coffee beans", "stock_out", AlertSeverity.high,
         "Station {code} projected to run out of coffee beans within 24 hours based on current consumption.",
         "Advance replenishment order. Contact regional supply coordinator."),
        ("Understaffing alert", "workforce", AlertSeverity.critical,
         "Station {code} morning shift has 2 staff vs 4 planned for 3 consecutive days.",
         "Reassign staff from nearby station or activate on-call pool. Peak hours 7-9am at risk."),
        ("Competitor price undercut", "pricing", AlertSeverity.medium,
         "Competitor Shell undercuts diesel by 0.05 EUR/L at station {code} cluster.",
         "Test -0.02 EUR response. Elasticity model suggests minimal volume loss if gap stays under 0.04."),
        ("Bakery order deviation", "inventory", AlertSeverity.low,
         "Station {code} ordering 40% more bakery items than forecast suggests.",
         "Reduce next order by 10%. Current spoilage rate 15% vs target 5%."),
        ("Premium fuel margin opportunity", "pricing", AlertSeverity.low,
         "Station {code} premium 98 demand is price-inelastic. Current margin 0.18 EUR/L.",
         "Test +3 HUF on premium fuel. Elasticity model suggests margin +2.1% with minimal volume impact."),
        ("EV charging queue", "operations", AlertSeverity.medium,
         "Station {code} EV charger utilization at 92% during 16:00-20:00 peak.",
         "Consider adding second fast charger. Current wait time averaging 18 minutes."),
        ("Loyalty redemption surge", "loyalty", AlertSeverity.low,
         "Station {code} loyalty point redemptions up 45% this week.",
         "Ensure promotional stock is adequate. Check if campaign is driving the surge."),
        ("Fresh Corner revenue opportunity", "revenue", AlertSeverity.medium,
         "Station {code} coffee sales 30% below peer average despite similar traffic.",
         "Review coffee machine maintenance schedule. Consider staff training on upselling."),
    ]

    now = datetime.utcnow()
    for i, (title_tpl, metric, severity, desc_tpl, action) in enumerate(alert_templates):
        # Pick random stations for each alert type
        chosen = random.sample(stations, min(random.randint(2, 6), len(stations)))
        for station in chosen:
            status = random.choices(
                [AlertStatus.active, AlertStatus.acknowledged, AlertStatus.resolved, AlertStatus.dismissed],
                weights=[40, 25, 25, 10],
            )[0]
            detected = now - timedelta(hours=random.randint(1, 168))
            resolved = detected + timedelta(hours=random.randint(2, 48)) if status in (AlertStatus.resolved, AlertStatus.dismissed) else None
            session.add(MacAnomalyAlert(
                station_id=station.id,
                metric_type=metric,
                severity=severity,
                title=title_tpl,
                description=desc_tpl.format(code=station.station_code),
                suggested_action=action,
                status=status,
                detected_at=detected,
                resolved_at=resolved,
            ))
    session.flush()
    print("    Anomaly alerts seeded.")


def _seed_issues(session: Session, stations: list[MacStation]):
    """Generate historical operational issues."""
    issue_templates = [
        (IssueCategory.equipment, "Pump #{n} malfunction", "Fuel pump #{n} showing error code E-42. Intermittent dispensing failures reported by customers.", "Replaced faulty solenoid valve. Pump back in service after 4h downtime."),
        (IssueCategory.equipment, "POS terminal crash", "Point-of-sale terminal freezing during card payments. Reboot cycle every 30 minutes.", "Software update applied. Root cause: memory leak in payment module v3.2.1."),
        (IssueCategory.supply_chain, "Diesel delivery delayed", "Scheduled diesel delivery 12h overdue. Tank level at 15% capacity.", "Rerouted tanker from regional depot. Delivery completed with 6h additional delay."),
        (IssueCategory.supply_chain, "Coffee bean supply disruption", "Regular supplier out of stock on Arabica blend. Alternative sourcing needed.", "Temporary switch to secondary supplier. Quality acceptable. Permanent fix in 2 weeks."),
        (IssueCategory.quality, "Fresh Corner temperature alarm", "Walk-in cooler temperature rose to 8°C (threshold 4°C). Food safety risk.", "Compressor filter cleaned. Temperature restored in 45 min. No product loss."),
        (IssueCategory.quality, "Fuel quality complaint", "Customer reports engine knocking after refueling premium 98. Sample sent to lab.", "Lab results normal. Customer vehicle had pre-existing injector issue."),
        (IssueCategory.customer_complaint, "Long queue complaint", "Multiple Google reviews citing 10+ minute wait times during morning rush.", "Added express lane for coffee-only purchases. Staff scheduling adjusted for 7-9am peak."),
        (IssueCategory.customer_complaint, "Loyalty points not credited", "B2B fleet customer reports 3 months of missing loyalty points on account.", "System sync issue identified. Points manually credited. Backend fix deployed."),
        (IssueCategory.staffing, "Night shift no-show", "Night shift employee called in sick with no replacement available.", "Manager covered shift. Added 2 backup staff to on-call roster."),
        (IssueCategory.safety, "Fuel spill near pump 3", "Minor diesel spill (~5L) during customer refueling. Wet surface around pump area.", "Spill kit deployed. Area cleaned and dried. Pump inspection passed."),
        (IssueCategory.it_system, "Network outage", "Internet connectivity lost. Card payments and loyalty system offline.", "ISP issue resolved after 2h. Switched to backup 4G during downtime."),
    ]

    for _ in range(80):
        cat, title_tpl, desc, resolution = random.choice(issue_templates)
        station = random.choice(stations)
        status = random.choices(
            [IssueStatus.open, IssueStatus.in_progress, IssueStatus.resolved, IssueStatus.closed],
            weights=[15, 10, 40, 35],
        )[0]
        created = datetime.utcnow() - timedelta(days=random.randint(1, 180))
        resolved = created + timedelta(hours=random.randint(1, 72)) if status in (IssueStatus.resolved, IssueStatus.closed) else None
        n = random.randint(1, 12)
        session.add(MacIssue(
            station_id=station.id,
            category=cat,
            title=title_tpl.format(n=n),
            description=desc,
            resolution=resolution if status in (IssueStatus.resolved, IssueStatus.closed) else None,
            status=status,
            priority=random.randint(1, 5),
            created_at=created,
            resolved_at=resolved,
        ))
    session.flush()
    print("    Issues seeded.")


def _seed_customer_profiles(session: Session):
    """Seed B2B customer profiles and contracts."""
    customers_data = [
        {"company": "TransEuropa Logistics", "contact": "András Kovács", "email": "a.kovacs@transeuropa.hu", "fleet": 120, "tier": LoyaltyTier.platinum, "ctype": "Fleet Premium"},
        {"company": "Pannonia Freight", "contact": "Zoltán Nagy", "email": "z.nagy@pannoniafreight.hu", "fleet": 85, "tier": LoyaltyTier.gold, "ctype": "Fleet Standard"},
        {"company": "Adriatic Express", "contact": "Ivan Horvat", "email": "i.horvat@adriaticexp.hr", "fleet": 60, "tier": LoyaltyTier.gold, "ctype": "Fleet Standard"},
        {"company": "Danubia Transport", "contact": "Peter Novák", "email": "p.novak@danubia.sk", "fleet": 200, "tier": LoyaltyTier.platinum, "ctype": "Fleet Premium"},
        {"company": "Central Taxi Group", "contact": "Mária Tóth", "email": "m.toth@centraltaxi.hu", "fleet": 350, "tier": LoyaltyTier.platinum, "ctype": "Taxi Fleet"},
        {"company": "GreenGo Delivery", "contact": "Lukáš Horák", "email": "l.horak@greengo.cz", "fleet": 45, "tier": LoyaltyTier.silver, "ctype": "Fleet Standard"},
        {"company": "Alpine Couriers", "contact": "Maja Krajnc", "email": "m.krajnc@alpinecouriers.si", "fleet": 30, "tier": LoyaltyTier.silver, "ctype": "Fleet Standard"},
        {"company": "Visegrad Construction", "contact": "Miroslav Kuba", "email": "m.kuba@visegradcon.cz", "fleet": 75, "tier": LoyaltyTier.gold, "ctype": "Fleet Heavy"},
        {"company": "Budapest Bus Co.", "contact": "Gábor Fekete", "email": "g.fekete@bpbus.hu", "fleet": 180, "tier": LoyaltyTier.platinum, "ctype": "Municipal Fleet"},
        {"company": "EcoFarm Agri", "contact": "Jana Vlková", "email": "j.vlkova@ecofarm.sk", "fleet": 25, "tier": LoyaltyTier.bronze, "ctype": "Seasonal"},
        {"company": "Starline Rental Cars", "contact": "Tomáš Procházka", "email": "t.prochazka@starline.cz", "fleet": 500, "tier": LoyaltyTier.platinum, "ctype": "Rental Fleet"},
        {"company": "Zagorje Milk", "contact": "Ante Jurić", "email": "a.juric@zagorjemilk.hr", "fleet": 18, "tier": LoyaltyTier.bronze, "ctype": "Fleet Standard"},
    ]

    for cd in customers_data:
        cp = MacCustomerProfile(
            company_name=cd["company"],
            contact_name=cd["contact"],
            contact_email=cd["email"],
            fleet_size=cd["fleet"],
            loyalty_tier=cd["tier"],
            contract_type=cd["ctype"],
        )
        session.add(cp)
    session.flush()

    # Create contracts for each customer
    profiles = session.exec(select(MacCustomerProfile)).all()
    for profile in profiles:
        vol = profile.fleet_size * random.uniform(800, 2000)
        discount = {"bronze": 2.0, "silver": 4.0, "gold": 6.0, "platinum": 8.5}[profile.loyalty_tier.value]
        start = date(2024, random.randint(1, 6), 1)
        session.add(MacCustomerContract(
            customer_id=profile.id,
            contract_type=profile.contract_type or "Fleet Standard",
            monthly_volume_commitment=round(vol, 0),
            discount_pct=discount + random.uniform(-0.5, 0.5),
            start_date=start,
            end_date=date(start.year + 2, start.month, start.day),
            notes=f"Annual review. {profile.fleet_size} vehicles registered.",
        ))
    session.flush()
    print("    Customer profiles and contracts seeded.")
