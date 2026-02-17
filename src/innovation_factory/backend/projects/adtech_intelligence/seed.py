"""Seed script for adtech-intelligence project data.

Generates realistic mock data for an ad-tech platform covering online and
outdoor (OOH / DOOH) advertising across Germany.
"""

import random
from datetime import date, datetime, timedelta, timezone

from sqlmodel import Session, select

from .models import (
    AnomalySeverity,
    AnomalyStatus,
    AnomalyType,
    AtAdInventory,
    AtAdvertiser,
    AtAnomaly,
    AtAnomalyRule,
    AtCampaign,
    AtCustomerContract,
    AtIssue,
    AtPerformanceMetric,
    AtPlacement,
    CampaignStatus,
    CampaignType,
    ContractStatus,
    InventoryStatus,
    InventoryType,
    IssueCategory,
    IssuePriority,
    IssueStatus,
    LocationType,
    PlacementStatus,
    RuleConditionType,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_rng = random.Random(42)  # deterministic seed for reproducibility

TODAY = date.today()


def _past_date(max_days: int = 365) -> date:
    return TODAY - timedelta(days=_rng.randint(1, max_days))


def _future_date(min_days: int = 30, max_days: int = 180) -> date:
    return TODAY + timedelta(days=_rng.randint(min_days, max_days))


# ---------------------------------------------------------------------------
# Static data pools
# ---------------------------------------------------------------------------

GERMAN_CITIES = [
    ("Berlin", "Berlin", 52.5200, 13.4050),
    ("Hamburg", "Hamburg", 53.5511, 9.9937),
    ("München", "Bayern", 48.1351, 11.5820),
    ("Köln", "Nordrhein-Westfalen", 50.9375, 6.9603),
    ("Frankfurt am Main", "Hessen", 50.1109, 8.6821),
    ("Stuttgart", "Baden-Württemberg", 48.7758, 9.1829),
    ("Düsseldorf", "Nordrhein-Westfalen", 51.2277, 6.7735),
    ("Leipzig", "Sachsen", 51.3397, 12.3731),
    ("Dortmund", "Nordrhein-Westfalen", 51.5136, 7.4653),
    ("Essen", "Nordrhein-Westfalen", 51.4556, 7.0116),
    ("Bremen", "Bremen", 53.0793, 8.8017),
    ("Dresden", "Sachsen", 51.0504, 13.7373),
    ("Hannover", "Niedersachsen", 52.3759, 9.7320),
    ("Nürnberg", "Bayern", 49.4521, 11.0767),
    ("Mannheim", "Baden-Württemberg", 49.4875, 8.4660),
]

ADVERTISERS = [
    ("AutoVista GmbH", "Automotive", "premium"),
    ("FreshMart AG", "Retail / FMCG", "enterprise"),
    ("TechPulse SE", "Technology", "premium"),
    ("WanderLust Reisen", "Travel & Tourism", "standard"),
    ("GreenEnergy Solutions", "Energy", "standard"),
    ("FinanzPlus Bank", "Finance", "enterprise"),
    ("StyleHaus Mode", "Fashion & Lifestyle", "premium"),
    ("MediCare Pharma", "Healthcare", "enterprise"),
    ("SportArena GmbH", "Sports & Entertainment", "standard"),
    ("BauWelt Immobilien", "Real Estate", "premium"),
    ("EduSmart Akademie", "Education", "standard"),
    ("FlavorKing Gastronomie", "Food & Beverage", "standard"),
    ("DigiMedia Verlag", "Media & Publishing", "premium"),
    ("LogiTrans Spedition", "Logistics", "standard"),
    ("CloudNine Software", "Technology", "enterprise"),
]

ACCOUNT_MANAGERS = [
    "Anna Schmidt", "Maximilian Weber", "Sophie Müller",
    "Lukas Fischer", "Emma Becker", "Jonas Wagner",
]

# Campaign name templates
CAMPAIGN_NAMES = [
    "{brand} Spring Launch", "{brand} Summer Special", "{brand} Herbstkampagne",
    "{brand} Winter Sale", "{brand} Brand Awareness Q{q}",
    "{brand} Product Launch — {product}", "{brand} City Takeover",
    "{brand} Crossmedia Blitz", "{brand} Digital First",
    "{brand} Premium Reach", "{brand} OOH Domination",
    "{brand} Video Reach", "{brand} Programmatic Push",
    "{brand} Regional Focus", "{brand} National Rollout",
]


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------


def seed_at_data(session: Session):
    """Seed all adtech-intelligence data."""
    if session.exec(select(AtAdvertiser)).first():
        return

    print("  Seeding adtech-intelligence data...")
    advertisers = _seed_advertisers(session)
    campaigns = _seed_campaigns(session, advertisers)
    inventory = _seed_inventory(session)
    placements = _seed_placements(session, campaigns, inventory)
    _seed_performance_metrics(session, placements)
    rules = _seed_anomaly_rules(session)
    _seed_anomalies(session, campaigns, placements, rules)
    _seed_issues(session, campaigns, advertisers)
    _seed_contracts(session, advertisers)
    session.commit()
    print("  adtech-intelligence data seeded.")


# -- Advertisers --------------------------------------------------------


def _seed_advertisers(session: Session) -> list[AtAdvertiser]:
    advs: list[AtAdvertiser] = []
    for name, industry, tier in ADVERTISERS:
        slug = name.split()[0].lower()
        adv = AtAdvertiser(
            name=name,
            industry=industry,
            contact_name=f"Kontakt {name.split()[0]}",
            contact_email=f"kontakt@{slug}.de",
            phone=f"+49 {_rng.randint(30, 89)} {_rng.randint(1000000, 9999999)}",
            website=f"https://www.{slug}.de",
            budget_tier=tier,
        )
        session.add(adv)
        advs.append(adv)
    session.flush()
    print("    Seeded advertisers.")
    return advs


# -- Campaigns ----------------------------------------------------------


def _seed_campaigns(
    session: Session, advertisers: list[AtAdvertiser]
) -> list[AtCampaign]:
    campaigns: list[AtCampaign] = []
    statuses = list(CampaignStatus)
    types = list(CampaignType)
    regions_pool = [c[0] for c in GERMAN_CITIES]

    for i in range(30):
        adv = _rng.choice(advertisers)
        ctype = _rng.choice(types)
        status = _rng.choice(statuses)
        budget = round(_rng.uniform(5_000, 500_000), 2)
        start = _past_date(180)
        end = start + timedelta(days=_rng.randint(14, 120))
        spent = round(budget * _rng.uniform(0.1, 0.95), 2) if status != CampaignStatus.draft else 0.0

        q = _rng.randint(1, 4)
        product = _rng.choice(["Produkt A", "Produkt B", "Neuheit 2025", "Service Pro"])
        name_tpl = _rng.choice(CAMPAIGN_NAMES)
        name = name_tpl.format(brand=adv.name.split()[0], q=q, product=product)

        num_regions = _rng.randint(1, 6)
        target_regions = _rng.sample(regions_pool, min(num_regions, len(regions_pool)))

        campaign = AtCampaign(
            advertiser_id=adv.id,
            name=name,
            description=f"Campaign for {adv.name} — {ctype.value} across {', '.join(target_regions[:3])}.",
            campaign_type=ctype,
            status=status,
            budget=budget,
            spent=spent,
            start_date=start,
            end_date=end,
            target_audience=_rng.choice([
                "Adults 25-45", "Young Professionals 18-35",
                "Families", "Business Decision Makers",
                "Tech Enthusiasts", "Urban Commuters",
            ]),
            target_regions=target_regions,
            kpi_targets={
                "impressions": _rng.randint(100_000, 10_000_000),
                "ctr": round(_rng.uniform(0.5, 3.0), 2),
                "conversions": _rng.randint(100, 10_000),
            },
        )
        session.add(campaign)
        campaigns.append(campaign)

    session.flush()
    print("    Seeded campaigns.")
    return campaigns


# -- Ad Inventory -------------------------------------------------------


def _seed_inventory(session: Session) -> list[AtAdInventory]:
    items: list[AtAdInventory] = []

    # Online inventory
    online_types = [
        (InventoryType.display_banner, "Display Banner", 50_000, 4.50),
        (InventoryType.video, "Video Pre-Roll", 30_000, 12.00),
        (InventoryType.native, "Native Content", 20_000, 8.00),
        (InventoryType.high_impact, "High Impact", 15_000, 25.00),
    ]
    online_properties = [
        "t-online.de", "watson.de", "desired.de", "familie.de",
        "GIGA.de", "kino.de", "sport1.de", "wetter.com",
        "n-tv.de", "stern.de",
    ]

    for prop in online_properties:
        for inv_type, label, impressions, cpm in online_types:
            item = AtAdInventory(
                name=f"{label} — {prop}",
                inventory_type=inv_type,
                location_type=LocationType.online,
                daily_impressions_est=impressions + _rng.randint(-10_000, 20_000),
                cpm_rate=round(cpm + _rng.uniform(-1, 3), 2),
                status=_rng.choice([InventoryStatus.available] * 8 + [InventoryStatus.booked, InventoryStatus.maintenance]),
                media_owner=prop.split(".")[0].capitalize(),
                format_spec={
                    "width": _rng.choice([300, 728, 970, 1920]),
                    "height": _rng.choice([250, 90, 250, 1080]),
                    "format": inv_type.value,
                },
            )
            session.add(item)
            items.append(item)

    # OOH / DOOH inventory
    ooh_configs = [
        (InventoryType.dooh_screen, LocationType.train_station, "Public Video Screen — {city} Hbf", 80_000, 18.0),
        (InventoryType.dooh_screen, LocationType.mall, "Mall Screen — {city} Einkaufszentrum", 40_000, 14.0),
        (InventoryType.billboard, LocationType.highway, "Mega-Board — A{road} {city}", 120_000, 8.0),
        (InventoryType.city_light, LocationType.pedestrian_zone, "City Light — {city} Fußgängerzone", 25_000, 6.0),
        (InventoryType.transit_poster, LocationType.bus_stop, "Transit Poster — {city} Bushalte", 15_000, 3.5),
        (InventoryType.dooh_screen, LocationType.subway, "U-Bahn Screen — {city}", 60_000, 16.0),
        (InventoryType.mega_poster, LocationType.pedestrian_zone, "Riesenposter — {city} Innenstadt", 200_000, 30.0),
        (InventoryType.city_light, LocationType.airport, "Airport Vitrine — {city} Flughafen", 90_000, 22.0),
    ]

    for city_name, region, lat, lng in GERMAN_CITIES:
        # Each city gets a subset of OOH formats
        num_formats = _rng.randint(3, len(ooh_configs))
        chosen = _rng.sample(ooh_configs, num_formats)
        for inv_type, loc_type, name_tpl, impressions, cpm in chosen:
            road = _rng.randint(1, 99)
            item = AtAdInventory(
                name=name_tpl.format(city=city_name, road=road),
                inventory_type=inv_type,
                location_type=loc_type,
                city=city_name,
                region=region,
                latitude=round(lat + _rng.uniform(-0.05, 0.05), 6),
                longitude=round(lng + _rng.uniform(-0.05, 0.05), 6),
                daily_impressions_est=impressions + _rng.randint(-5_000, 15_000),
                cpm_rate=round(cpm + _rng.uniform(-2, 5), 2),
                status=_rng.choice([InventoryStatus.available] * 7 + [InventoryStatus.booked] * 2 + [InventoryStatus.maintenance]),
                media_owner="Media Solutions",
                format_spec={
                    "width_cm": _rng.choice([120, 175, 356, 504]),
                    "height_cm": _rng.choice([175, 252, 252, 238]),
                    "digital": inv_type in (InventoryType.dooh_screen,),
                    "illuminated": _rng.choice([True, False]),
                },
            )
            session.add(item)
            items.append(item)

    session.flush()
    print(f"    Seeded {len(items)} inventory items.")
    return items


# -- Placements ---------------------------------------------------------


def _seed_placements(
    session: Session,
    campaigns: list[AtCampaign],
    inventory: list[AtAdInventory],
) -> list[AtPlacement]:
    placements: list[AtPlacement] = []

    for campaign in campaigns:
        if campaign.status == CampaignStatus.draft:
            continue
        # Assign 2-8 inventory slots per campaign
        slots = _rng.sample(inventory, min(_rng.randint(2, 8), len(inventory)))
        for inv in slots:
            p_start = campaign.start_date + timedelta(days=_rng.randint(0, 7))
            p_end = min(campaign.end_date, p_start + timedelta(days=_rng.randint(7, 60)))
            status_map = {
                CampaignStatus.active: PlacementStatus.active,
                CampaignStatus.paused: PlacementStatus.paused,
                CampaignStatus.completed: PlacementStatus.completed,
                CampaignStatus.cancelled: PlacementStatus.cancelled,
            }
            placement = AtPlacement(
                campaign_id=campaign.id,
                inventory_id=inv.id,
                start_date=p_start,
                end_date=p_end,
                daily_budget=round(campaign.budget / max(len(slots), 1) / max((p_end - p_start).days, 1), 2),
                status=status_map.get(campaign.status, PlacementStatus.scheduled),
            )
            session.add(placement)
            placements.append(placement)

    session.flush()
    print(f"    Seeded {len(placements)} placements.")
    return placements


# -- Performance Metrics ------------------------------------------------


def _seed_performance_metrics(
    session: Session, placements: list[AtPlacement]
) -> None:
    count = 0
    batch: list[AtPerformanceMetric] = []
    batch_size = 30  # PGLite (WASM) crashes with large INSERT statements

    for placement in placements:
        if placement.status in (PlacementStatus.cancelled,):
            continue
        # Generate daily metrics from start_date to min(end_date, today)
        current = placement.start_date
        end = min(placement.end_date, TODAY)
        while current <= end:
            impressions = _rng.randint(500, 50_000)
            clicks = int(impressions * _rng.uniform(0.005, 0.04))
            ctr = round(clicks / max(impressions, 1) * 100, 4)
            conversions = int(clicks * _rng.uniform(0.01, 0.15))
            spend = round(impressions / 1000 * placement.daily_budget * _rng.uniform(0.6, 1.2), 2)

            metric = AtPerformanceMetric(
                placement_id=placement.id,
                metric_date=current,
                impressions=impressions,
                clicks=clicks,
                ctr=ctr,
                conversions=conversions,
                spend=spend,
                viewability_rate=round(_rng.uniform(0.45, 0.95), 4),
            )
            batch.append(metric)
            count += 1

            if len(batch) >= batch_size:
                session.add_all(batch)
                session.flush()
                batch = []

            current += timedelta(days=1)

    if batch:
        session.add_all(batch)
        session.flush()

    print(f"    Seeded {count} performance metric rows.")


# -- Anomaly Rules ------------------------------------------------------


def _seed_anomaly_rules(session: Session) -> list[AtAnomalyRule]:
    rules_data = [
        ("CTR Drop Alert", "ctr", RuleConditionType.deviation, -30.0, 7,
         "Fires when CTR deviates more than 30% below the 7-day average."),
        ("Impression Spike", "impressions", RuleConditionType.deviation, 50.0, 3,
         "Fires when impressions spike >50% above the 3-day average."),
        ("Budget Overrun Warning", "spend", RuleConditionType.threshold, 110.0, 1,
         "Fires when daily spend exceeds 110% of daily budget."),
        ("Viewability Floor", "viewability_rate", RuleConditionType.threshold, 50.0, 1,
         "Fires when viewability drops below 50%."),
        ("Conversion Decline", "conversions", RuleConditionType.trend, -25.0, 14,
         "Fires when conversions trend downward by >25% over 14 days."),
        ("Performance Drop (Composite)", "spend", RuleConditionType.deviation, -40.0, 7,
         "Fires when composite performance score drops >40% over a week."),
        ("Inventory Under-Utilization", "impressions", RuleConditionType.threshold, 20.0, 7,
         "Fires when inventory delivers <20% of estimated daily impressions over 7 days."),
        ("High CPM Alert", "spend", RuleConditionType.threshold, 150.0, 3,
         "Fires when effective CPM exceeds 150% of booked rate."),
        ("Click Fraud Indicator", "ctr", RuleConditionType.deviation, 200.0, 1,
         "Fires when CTR spikes >200% above the daily norm — potential click fraud."),
        ("Weekend Dip Monitor", "impressions", RuleConditionType.trend, -50.0, 2,
         "Fires when weekend impressions drop >50% compared to weekdays."),
    ]
    rules: list[AtAnomalyRule] = []
    for name, metric, cond, thresh, lookback, desc in rules_data:
        rule = AtAnomalyRule(
            name=name,
            description=desc,
            metric_name=metric,
            condition_type=cond,
            threshold_value=thresh,
            lookback_days=lookback,
            enabled=True,
        )
        session.add(rule)
        rules.append(rule)
    session.flush()
    print("    Seeded anomaly rules.")
    return rules


# -- Anomalies ----------------------------------------------------------


def _seed_anomalies(
    session: Session,
    campaigns: list[AtCampaign],
    placements: list[AtPlacement],
    rules: list[AtAnomalyRule],
) -> None:
    active_campaigns = [c for c in campaigns if c.status in (CampaignStatus.active, CampaignStatus.completed)]
    active_placements = [p for p in placements if p.status in (PlacementStatus.active, PlacementStatus.completed)]

    anomaly_templates = [
        (AnomalyType.performance_drop, "Performance drop on {camp}",
         "Daily impressions fell {dev:.0f}% below the 7-day average for campaign '{camp}'. Investigate creative fatigue or audience saturation.",
         "impressions", AnomalySeverity.high),
        (AnomalyType.budget_overrun, "Budget overrun risk — {camp}",
         "Spend is trending {dev:.0f}% above daily budget for '{camp}'. Current pace will exhaust the budget {days}d early.",
         "spend", AnomalySeverity.critical),
        (AnomalyType.ctr_anomaly, "CTR anomaly detected — {camp}",
         "CTR dropped by {dev:.0f}% compared to the campaign average. Check targeting parameters and creative assets.",
         "ctr", AnomalySeverity.medium),
        (AnomalyType.impression_spike, "Unusual impression spike — {camp}",
         "Impressions surged {dev:.0f}% above normal levels. May indicate bot traffic or a viral share event.",
         "impressions", AnomalySeverity.medium),
        (AnomalyType.viewability_drop, "Viewability below threshold — {camp}",
         "Viewability rate fell to {actual:.1f}% (expected ≥ {expected:.1f}%). Ad placements may need repositioning.",
         "viewability_rate", AnomalySeverity.high),
        (AnomalyType.conversion_decline, "Conversion decline — {camp}",
         "Conversions dropped {dev:.0f}% over the past 14 days for '{camp}'. Landing page or funnel issues suspected.",
         "conversions", AnomalySeverity.high),
        (AnomalyType.inventory_underutilization, "Inventory under-utilized — {inv}",
         "Inventory '{inv}' delivered only {actual:.0f} of an estimated {expected:.0f} daily impressions.",
         "impressions", AnomalySeverity.low),
    ]

    statuses = [AnomalyStatus.new] * 5 + [AnomalyStatus.acknowledged] * 3 + [AnomalyStatus.investigating] * 2 + [AnomalyStatus.resolved, AnomalyStatus.dismissed]

    for i in range(50):
        tpl = _rng.choice(anomaly_templates)
        atype, title_tpl, desc_tpl, metric, severity = tpl
        camp = _rng.choice(active_campaigns) if active_campaigns else campaigns[0]
        plc = _rng.choice(active_placements) if active_placements else None
        rule = _rng.choice(rules)

        expected = round(_rng.uniform(1000, 80_000), 2)
        deviation = _rng.uniform(-60, 200)
        actual = round(expected * (1 + deviation / 100), 2)
        days = _rng.randint(3, 30)

        inv_name = "N/A"
        if plc and plc.inventory:
            inv_name = plc.inventory.name

        title = title_tpl.format(camp=camp.name, inv=inv_name)
        desc = desc_tpl.format(
            camp=camp.name, inv=inv_name, dev=abs(deviation),
            actual=actual, expected=expected, days=days,
        )

        status = _rng.choice(statuses)
        resolved_at = None
        resolved_by = None
        if status in (AnomalyStatus.resolved, AnomalyStatus.dismissed):
            resolved_at = datetime.now(timezone.utc) - timedelta(days=_rng.randint(0, 14))
            resolved_by = _rng.choice(ACCOUNT_MANAGERS)

        suggested = _generate_suggested_actions(atype)

        anomaly = AtAnomaly(
            campaign_id=camp.id,
            placement_id=plc.id if plc else None,
            rule_id=rule.id,
            anomaly_type=atype,
            severity=severity,
            title=title,
            description=desc,
            detected_at=datetime.now(timezone.utc) - timedelta(days=_rng.randint(0, 30), hours=_rng.randint(0, 23)),
            status=status,
            metric_name=metric,
            expected_value=expected,
            actual_value=actual,
            deviation_pct=round(deviation, 2),
            suggested_actions=suggested,
            resolved_at=resolved_at,
            resolved_by=resolved_by,
        )
        session.add(anomaly)

    session.flush()
    print("    Seeded 50 anomalies.")


def _generate_suggested_actions(atype: AnomalyType) -> list[str]:
    actions_map: dict[AnomalyType, list[str]] = {
        AnomalyType.performance_drop: [
            "Review creative assets for fatigue — consider A/B testing new variants.",
            "Check audience overlap with competing campaigns.",
            "Expand targeting parameters or refresh audience segments.",
            "Increase bid/budget if impression share is declining.",
        ],
        AnomalyType.budget_overrun: [
            "Reduce daily budget caps on highest-spend placements.",
            "Pause lowest-performing placements to redistribute budget.",
            "Contact the advertiser to discuss budget extension options.",
            "Switch to pacing mode to spread remaining budget evenly.",
        ],
        AnomalyType.ctr_anomaly: [
            "Audit ad creative — test new headlines and visuals.",
            "Review targeting: ensure audience relevance.",
            "Check for ad fatigue (high frequency + low CTR).",
            "Verify landing page load speed and mobile responsiveness.",
        ],
        AnomalyType.impression_spike: [
            "Investigate traffic sources for bot activity.",
            "Enable invalid traffic (IVT) filters if available.",
            "Review placement context — check for viral content placement.",
            "Cap impression frequency to control abnormal volume.",
        ],
        AnomalyType.viewability_drop: [
            "Reposition ad placements to above-the-fold inventory.",
            "Switch to viewability-optimised bidding strategy.",
            "Blacklist low-viewability domains or screens.",
            "Test alternative ad sizes known for higher viewability.",
        ],
        AnomalyType.conversion_decline: [
            "Audit the conversion funnel and landing page.",
            "A/B test call-to-action copy and button placement.",
            "Check tracking pixel integrity — ensure events fire correctly.",
            "Review attribution window settings.",
        ],
        AnomalyType.inventory_underutilization: [
            "Verify technical status of the screen/placement.",
            "Check for scheduling gaps or maintenance windows.",
            "Lower minimum CPM to attract more demand.",
            "Bundle underperforming inventory with premium slots.",
        ],
    }
    pool = actions_map.get(atype, ["Investigate further."])
    return _rng.sample(pool, min(_rng.randint(2, 4), len(pool)))


# -- Issues / Support Tickets -------------------------------------------


def _seed_issues(
    session: Session,
    campaigns: list[AtCampaign],
    advertisers: list[AtAdvertiser],
) -> None:
    issue_templates = [
        ("Ad not displaying on {loc}", IssueCategory.delivery, IssuePriority.high,
         "The ad for campaign '{camp}' is not rendering on {loc}. The screen/page shows a blank slot."),
        ("Incorrect targeting — wrong region", IssueCategory.targeting, IssuePriority.medium,
         "Campaign '{camp}' is being served in regions outside the target list. Expected: {regions}."),
        ("Creative rejected by platform", IssueCategory.creative, IssuePriority.medium,
         "The creative asset for '{camp}' was rejected due to non-compliance with format specifications."),
        ("Billing discrepancy — overcharge", IssueCategory.billing, IssuePriority.high,
         "Invoice for '{camp}' shows €{amount} more than the agreed budget. Please review."),
        ("Reporting delay — metrics missing", IssueCategory.reporting, IssuePriority.low,
         "Performance metrics for '{camp}' have not been updated for the past 48 hours."),
        ("DOOH screen offline — {loc}", IssueCategory.technical, IssuePriority.urgent,
         "The DOOH screen at {loc} has been offline since {date}. Campaign '{camp}' is affected."),
        ("Low viewability on mobile placements", IssueCategory.delivery, IssuePriority.medium,
         "Viewability for mobile placements in '{camp}' is consistently below 40%."),
        ("Click tracking broken", IssueCategory.technical, IssuePriority.urgent,
         "Click-through tracking for '{camp}' is returning 404 errors. Conversion attribution is impacted."),
        ("Inventory double-booked", IssueCategory.inventory, IssuePriority.high,
         "Inventory slot '{inv}' appears to be booked by two campaigns simultaneously."),
        ("Campaign pacing too aggressive", IssueCategory.delivery, IssuePriority.medium,
         "Campaign '{camp}' is spending budget 40% faster than expected. Pacing adjustment needed."),
    ]

    all_statuses = list(IssueStatus)

    for i in range(40):
        tpl = _rng.choice(issue_templates)
        title_tpl, category, priority, desc_tpl = tpl
        camp = _rng.choice(campaigns)
        adv = _rng.choice(advertisers)
        city = _rng.choice(GERMAN_CITIES)

        title = title_tpl.format(
            loc=f"{city[0]} Hbf", camp=camp.name,
            regions="Berlin, Hamburg", inv="Slot-" + str(_rng.randint(100, 999)),
        )
        desc = desc_tpl.format(
            camp=camp.name, loc=f"{city[0]} Hbf",
            regions="Berlin, Hamburg", amount=_rng.randint(500, 15_000),
            date=_past_date(7).isoformat(), inv="Slot-" + str(_rng.randint(100, 999)),
        )

        status = _rng.choice(all_statuses)
        resolution = None
        resolved_at = None
        if status in (IssueStatus.resolved, IssueStatus.closed):
            resolution = _rng.choice([
                "Root cause identified and fixed. Ad serving resumed.",
                "Billing corrected. Credit note issued to advertiser.",
                "Targeting parameters updated. Verified with QA.",
                "Technical team replaced the faulty hardware. Screen back online.",
                "Tracking pixel re-deployed. Conversions now recording correctly.",
            ])
            resolved_at = datetime.now(timezone.utc) - timedelta(days=_rng.randint(0, 14))

        issue = AtIssue(
            campaign_id=camp.id,
            advertiser_id=adv.id,
            title=title,
            description=desc,
            category=category,
            status=status,
            priority=priority,
            resolution=resolution,
            assigned_to=_rng.choice(ACCOUNT_MANAGERS),
            created_at=datetime.now(timezone.utc) - timedelta(days=_rng.randint(0, 60)),
            resolved_at=resolved_at,
        )
        session.add(issue)

    session.flush()
    print("    Seeded 40 issues.")


# -- Customer Contracts -------------------------------------------------


def _seed_contracts(
    session: Session, advertisers: list[AtAdvertiser]
) -> None:
    contract_types = ["annual", "project", "programmatic", "framework"]

    for i, adv in enumerate(advertisers):
        num = _rng.randint(1, 2)
        for j in range(num):
            start = _past_date(365)
            end = start + timedelta(days=_rng.choice([90, 180, 365]))
            ctype = _rng.choice(contract_types)
            value = round(_rng.uniform(10_000, 2_000_000), 2)
            status = ContractStatus.active if end >= TODAY else ContractStatus.expired

            contract = AtCustomerContract(
                advertiser_id=adv.id,
                contract_number=f"CTR-{2024 + j}-{1000 + i * 10 + j}",
                contract_type=ctype,
                start_date=start,
                end_date=end,
                total_value=value,
                status=status,
                terms_summary=f"{ctype.capitalize()} agreement for {adv.name}. "
                              f"Covers {'online + OOH' if ctype == 'annual' else ctype} media buying. "
                              f"Volume discount: {_rng.randint(5, 25)}%.",
                account_manager=_rng.choice(ACCOUNT_MANAGERS),
            )
            session.add(contract)

    session.flush()
    print("    Seeded customer contracts.")
