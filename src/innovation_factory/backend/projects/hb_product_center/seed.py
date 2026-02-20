"""Seed script for Hugo Boss Intelligent Product Center.

Generates realistic Hugo Boss product data across categories, collections,
and seasons, along with recognition results, quality inspections, authenticity
verifications, supply chain events, and sustainability metrics.
"""

import random
from datetime import date, datetime, timedelta, timezone

from sqlmodel import Session, select

from .models import (
    AlertResolution,
    AlertSeverity,
    ChatContext,
    ComplianceStatus,
    DefectSeverity,
    DefectType,
    HbAuthAlert,
    HbAuthVerification,
    HbChatMessage,
    HbChatSession,
    HbProduct,
    HbProductImage,
    HbQualityDefect,
    HbQualityInspection,
    HbRecognitionJob,
    HbRecognitionResult,
    HbSupplyChainEvent,
    HbSustainabilityMetric,
    ImageType,
    InspectionStatus,
    ProductCategory,
    ProductCollection,
    ProductSeason,
    ProductStatus,
    RecognitionJobStatus,
    RecognitionJobType,
    RequesterType,
    SupplyChainEventType,
    UserRole,
    VerificationMethod,
    VerificationStatus,
)

_rng = random.Random(77)
TODAY = date.today()


def _past_dt(max_days: int = 180) -> datetime:
    delta = timedelta(days=_rng.randint(1, max_days), hours=_rng.randint(0, 23), minutes=_rng.randint(0, 59))
    return datetime.now(timezone.utc) - delta


def _past_date(max_days: int = 365) -> date:
    return TODAY - timedelta(days=_rng.randint(1, max_days))


# ---------------------------------------------------------------------------
# Static data pools
# ---------------------------------------------------------------------------

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

PRODUCT_TEMPLATES = [
    # (style_name, category, material_idx, price_range)
    ("Slim-Fit Suit in Virgin Wool", ProductCategory.suits, 0, (599, 899)),
    ("Regular-Fit Suit in Stretch Wool", ProductCategory.suits, 11, (499, 749)),
    ("Tuxedo in Wool Twill", ProductCategory.suits, 0, (899, 1299)),
    ("Sharp-Fit Cotton Shirt", ProductCategory.shirts, 3, (89, 159)),
    ("Slim-Fit Easy-Iron Shirt", ProductCategory.shirts, 1, (99, 169)),
    ("Casual Linen Shirt", ProductCategory.shirts, 6, (129, 199)),
    ("Crew-Neck Knit Sweater", ProductCategory.knitwear, 7, (149, 249)),
    ("Cashmere V-Neck Sweater", ProductCategory.knitwear, 10, (349, 499)),
    ("Merino Wool Cardigan", ProductCategory.knitwear, 0, (199, 299)),
    ("Padded Jacket with Down Fill", ProductCategory.outerwear, 9, (399, 599)),
    ("Wool-Blend Overcoat", ProductCategory.outerwear, 11, (499, 799)),
    ("Leather Bomber Jacket", ProductCategory.outerwear, 8, (699, 999)),
    ("Slim-Fit Stretch Chinos", ProductCategory.trousers, 1, (99, 179)),
    ("Regular-Fit Wool Trousers", ProductCategory.trousers, 0, (179, 299)),
    ("Italian Leather Oxford Shoes", ProductCategory.shoes, 8, (299, 449)),
    ("Suede Desert Boots", ProductCategory.shoes, 8, (249, 379)),
    ("Leather Belt with Logo Buckle", ProductCategory.accessories, 8, (89, 159)),
    ("Silk Pocket Square", ProductCategory.accessories, 2, (49, 89)),
    ("Wool-Blend Scarf", ProductCategory.accessories, 0, (79, 139)),
    ("BOSS Bottled Eau de Parfum", ProductCategory.fragrances, 3, (69, 129)),
    ("HUGO Man Eau de Toilette", ProductCategory.fragrances, 3, (59, 99)),
    ("Performance Stretch Polo", ProductCategory.sportswear, 9, (79, 129)),
    ("Slim-Fit Stretch Denim Jeans", ProductCategory.denim, 5, (129, 199)),
    ("Relaxed-Fit Selvedge Jeans", ProductCategory.denim, 3, (179, 279)),
]


def seed_hb_data(session: Session):
    """Seed Hugo Boss Product Center data."""
    existing = session.exec(select(HbProduct)).first()
    if existing:
        return

    products = _seed_products(session)
    _seed_product_images(session, products)
    recognition_jobs = _seed_recognition_jobs(session, products)
    _seed_recognition_results(session, recognition_jobs, products)
    inspections = _seed_quality_inspections(session, products)
    _seed_quality_defects(session, inspections)
    verifications = _seed_auth_verifications(session, products)
    _seed_auth_alerts(session, verifications)
    _seed_supply_chain_events(session, products)
    _seed_sustainability_metrics(session, products)
    _seed_chat_sessions(session)
    session.commit()
    print("  Seeded Hugo Boss Product Center data.")


def _seed_products(session: Session) -> list[HbProduct]:
    products = []
    collections = list(ProductCollection)
    seasons = list(ProductSeason)

    for i, (style, category, mat_idx, price_range) in enumerate(PRODUCT_TEMPLATES):
        color_name, color_code = _rng.choice(COLORS)
        size = _rng.choice(SIZES)
        collection = _rng.choice(collections)
        season = _rng.choice(seasons)
        supplier_name, country = _rng.choice(SUPPLIERS)
        price = round(_rng.uniform(*price_range), 2)
        sku = f"HB-{collection.value[:4].upper()}-{category.value[:3].upper()}-{1000 + i:04d}"

        product = HbProduct(
            sku=sku,
            style_name=style,
            color=color_name,
            color_code=color_code,
            size=size,
            category=category,
            collection=collection,
            season=season,
            material=MATERIALS[mat_idx],
            price=price,
            status=_rng.choice([ProductStatus.active] * 8 + [ProductStatus.discontinued, ProductStatus.sample]),
            country_of_origin=country,
            supplier_name=supplier_name,
            created_at=_past_dt(365),
        )
        session.add(product)
        products.append(product)

    # Generate additional color/size variants to reach ~50 products
    for _ in range(26):
        template_idx = _rng.randint(0, len(PRODUCT_TEMPLATES) - 1)
        style, category, mat_idx, price_range = PRODUCT_TEMPLATES[template_idx]
        color_name, color_code = _rng.choice(COLORS)
        size = _rng.choice(SIZES)
        collection = _rng.choice(collections)
        season = _rng.choice(seasons)
        supplier_name, country = _rng.choice(SUPPLIERS)
        price = round(_rng.uniform(*price_range), 2)
        variant_id = 2000 + len(products)
        sku = f"HB-{collection.value[:4].upper()}-{category.value[:3].upper()}-{variant_id:04d}"

        product = HbProduct(
            sku=sku,
            style_name=style,
            color=color_name,
            color_code=color_code,
            size=size,
            category=category,
            collection=collection,
            season=season,
            material=MATERIALS[mat_idx],
            price=price,
            status=ProductStatus.active,
            country_of_origin=country,
            supplier_name=supplier_name,
            created_at=_past_dt(300),
        )
        session.add(product)
        products.append(product)

    session.flush()
    return products


def _seed_product_images(session: Session, products: list[HbProduct]):
    for p in products:
        for img_type in [ImageType.master, ImageType.lifestyle]:
            session.add(HbProductImage(
                product_id=p.id,
                image_url=f"https://images.hugoboss.com/catalog/{p.sku.lower()}_{img_type.value}.jpg",
                image_type=img_type,
                uploaded_by="system",
                created_at=p.created_at,
            ))
        if _rng.random() < 0.3:
            session.add(HbProductImage(
                product_id=p.id,
                image_url=f"https://images.hugoboss.com/catalog/{p.sku.lower()}_sample.jpg",
                image_type=ImageType.sample,
                uploaded_by=_rng.choice(INSPECTORS),
                created_at=_past_dt(90),
            ))
    session.flush()


def _seed_recognition_jobs(session: Session, products: list[HbProduct]) -> list[HbRecognitionJob]:
    jobs = []
    for i in range(40):
        is_batch = _rng.random() < 0.25
        img_count = _rng.randint(5, 50) if is_batch else 1
        status = _rng.choice([RecognitionJobStatus.completed] * 7 + [RecognitionJobStatus.pending, RecognitionJobStatus.processing, RecognitionJobStatus.failed])
        completed_count = img_count if status == RecognitionJobStatus.completed else (_rng.randint(0, img_count) if status == RecognitionJobStatus.processing else 0)
        created = _past_dt(60)

        job = HbRecognitionJob(
            job_type=RecognitionJobType.batch if is_batch else RecognitionJobType.single,
            status=status,
            user_role=_rng.choice(list(UserRole)),
            submitted_by=_rng.choice(INSPECTORS + ["Store App", "Warehouse Scanner"]),
            image_count=img_count,
            completed_count=completed_count,
            created_at=created,
            completed_at=created + timedelta(seconds=_rng.randint(2, 30)) if status == RecognitionJobStatus.completed else None,
        )
        session.add(job)
        jobs.append(job)

    session.flush()
    return jobs


def _seed_recognition_results(session: Session, jobs: list[HbRecognitionJob], products: list[HbProduct]):
    for job in jobs:
        if job.status in (RecognitionJobStatus.pending, RecognitionJobStatus.failed):
            continue
        n_results = job.completed_count if job.completed_count > 0 else min(job.image_count, 3)
        for _ in range(min(n_results, 5)):
            matched = _rng.random() < 0.85
            product = _rng.choice(products) if matched else None
            confidence = round(_rng.uniform(0.82, 0.99), 3) if matched else round(_rng.uniform(0.15, 0.55), 3)
            session.add(HbRecognitionResult(
                job_id=job.id,
                product_id=product.id if product else None,
                image_url=f"https://uploads.hugoboss.com/recognition/{job.id}_{_rng.randint(1000,9999)}.jpg",
                confidence_score=confidence,
                detected_sku=product.sku if product else None,
                detected_color=product.color if product else _rng.choice(["Unknown", "Mixed"]),
                detected_size=product.size if product else None,
                detected_category=product.category.value if product else None,
                processing_time_ms=_rng.randint(120, 3500),
                created_at=job.created_at + timedelta(seconds=_rng.randint(1, 10)),
            ))
    session.flush()


def _seed_quality_inspections(session: Session, products: list[HbProduct]) -> list[HbQualityInspection]:
    inspections = []
    for i in range(35):
        product = _rng.choice(products)
        status = _rng.choice([InspectionStatus.approved] * 5 + [InspectionStatus.rejected, InspectionStatus.pending, InspectionStatus.in_review])
        score = round(_rng.uniform(70, 100), 1) if status in (InspectionStatus.approved, InspectionStatus.in_review) else round(_rng.uniform(30, 69), 1)
        created = _past_dt(120)

        inspection = HbQualityInspection(
            product_id=product.id,
            batch_number=f"BATCH-{_rng.randint(2024, 2026)}-{_rng.randint(1000, 9999)}",
            inspector=_rng.choice(INSPECTORS),
            manufacturing_partner=_rng.choice(MANUFACTURING_PARTNERS),
            overall_score=score,
            status=status,
            notes=f"Routine quality check for batch. {'All criteria met.' if score > 80 else 'Defects detected, review required.'}" if _rng.random() < 0.6 else None,
            created_at=created,
            completed_at=created + timedelta(hours=_rng.randint(1, 48)) if status != InspectionStatus.pending else None,
        )
        session.add(inspection)
        inspections.append(inspection)

    session.flush()
    return inspections


def _seed_quality_defects(session: Session, inspections: list[HbQualityInspection]):
    for insp in inspections:
        n_defects = 0 if insp.overall_score > 90 else (_rng.randint(1, 2) if insp.overall_score > 70 else _rng.randint(2, 5))
        for _ in range(n_defects):
            session.add(HbQualityDefect(
                inspection_id=insp.id,
                defect_type=_rng.choice(list(DefectType)),
                severity=_rng.choice([DefectSeverity.minor] * 4 + [DefectSeverity.moderate] * 3 + [DefectSeverity.major, DefectSeverity.critical]),
                location_description=_rng.choice([
                    "Left shoulder seam", "Right cuff area", "Front panel center",
                    "Back collar region", "Button placket", "Lapel edge",
                    "Hem area", "Sleeve attachment point", "Pocket lining",
                    "Zipper track", "Inner lining", "Waistband",
                ]),
                confidence_score=round(_rng.uniform(0.7, 0.99), 3),
                image_url=f"https://images.hugoboss.com/qc/defect_{insp.id}_{_rng.randint(100,999)}.jpg" if _rng.random() < 0.5 else None,
                created_at=insp.created_at + timedelta(minutes=_rng.randint(5, 120)),
            ))
    session.flush()


def _seed_auth_verifications(session: Session, products: list[HbProduct]) -> list[HbAuthVerification]:
    verifications = []
    for i in range(25):
        product = _rng.choice(products) if _rng.random() < 0.8 else None
        status = _rng.choice([VerificationStatus.verified] * 6 + [VerificationStatus.suspicious, VerificationStatus.counterfeit, VerificationStatus.pending])
        confidence = round(_rng.uniform(0.85, 0.99), 3) if status == VerificationStatus.verified else (round(_rng.uniform(0.3, 0.65), 3) if status in (VerificationStatus.suspicious, VerificationStatus.counterfeit) else None)
        created = _past_dt(90)

        verification = HbAuthVerification(
            product_id=product.id if product else None,
            requester_type=_rng.choice(list(RequesterType)),
            requester_name=_rng.choice(["Customer Service", "Retail Partner Berlin", "E-Commerce Team", "Marketplace Compliance", "Partner: Nordstrom", "Partner: Zalando", "Internal Audit"]),
            requester_email=f"verify-{_rng.randint(100,999)}@hugoboss.com",
            status=status,
            confidence_score=confidence,
            verification_method=_rng.choice(list(VerificationMethod)),
            image_url=f"https://uploads.hugoboss.com/auth/{_rng.randint(10000,99999)}.jpg" if _rng.random() < 0.7 else None,
            region=_rng.choice(REGIONS),
            notes="Flagged by automated scan." if status == VerificationStatus.suspicious else None,
            created_at=created,
            completed_at=created + timedelta(hours=_rng.randint(1, 72)) if status != VerificationStatus.pending else None,
        )
        session.add(verification)
        verifications.append(verification)

    session.flush()
    return verifications


def _seed_auth_alerts(session: Session, verifications: list[HbAuthVerification]):
    for v in verifications:
        if v.status not in (VerificationStatus.suspicious, VerificationStatus.counterfeit):
            continue
        alert_type = "Suspected Counterfeit" if v.status == VerificationStatus.counterfeit else "Quality Anomaly Detected"
        session.add(HbAuthAlert(
            verification_id=v.id,
            alert_type=alert_type,
            severity=AlertSeverity.critical if v.status == VerificationStatus.counterfeit else _rng.choice([AlertSeverity.medium, AlertSeverity.high]),
            region=v.region,
            description=f"{alert_type} for verification #{v.id}. Region: {v.region}. Method: {v.verification_method.value}.",
            investigated_by=_rng.choice(INSPECTORS) if _rng.random() < 0.6 else None,
            resolution=_rng.choice([AlertResolution.open, AlertResolution.investigating, AlertResolution.confirmed_counterfeit, AlertResolution.false_positive]),
            created_at=v.created_at + timedelta(minutes=_rng.randint(5, 60)),
        ))
    session.flush()


def _seed_supply_chain_events(session: Session, products: list[HbProduct]):
    event_flow = [
        SupplyChainEventType.manufactured,
        SupplyChainEventType.quality_checked,
        SupplyChainEventType.shipped,
        SupplyChainEventType.received_warehouse,
        SupplyChainEventType.inspected,
        SupplyChainEventType.distributed,
        SupplyChainEventType.received_store,
    ]
    for product in _rng.sample(products, min(35, len(products))):
        base_date = _past_dt(200)
        n_events = _rng.randint(3, len(event_flow))
        for j in range(n_events):
            loc, country = _rng.choice(LOCATIONS)
            evt_date = base_date + timedelta(days=j * _rng.randint(2, 14))
            session.add(HbSupplyChainEvent(
                product_id=product.id,
                event_type=event_flow[j],
                location=loc,
                partner_name=_rng.choice(MANUFACTURING_PARTNERS + ["Hugo Boss Logistics", "DHL Supply Chain", "Kuehne+Nagel"]),
                country=country,
                details=f"{event_flow[j].value.replace('_', ' ').title()} at {loc}",
                event_date=evt_date,
                created_at=evt_date,
            ))
        if _rng.random() < 0.3:
            sold_date = base_date + timedelta(days=n_events * 14 + _rng.randint(1, 30))
            loc, country = _rng.choice(LOCATIONS)
            session.add(HbSupplyChainEvent(
                product_id=product.id,
                event_type=SupplyChainEventType.sold,
                location=loc,
                partner_name="Hugo Boss Store " + loc.split(",")[0],
                country=country,
                details=f"Sold at retail store in {loc}",
                event_date=sold_date,
                created_at=sold_date,
            ))
    session.flush()


def _seed_sustainability_metrics(session: Session, products: list[HbProduct]):
    for product in products:
        session.add(HbSustainabilityMetric(
            product_id=product.id,
            carbon_footprint_kg=round(_rng.uniform(3.0, 45.0), 2),
            water_usage_liters=round(_rng.uniform(50, 2500), 1),
            recycled_content_pct=round(_rng.uniform(0, 60), 1),
            organic_material_pct=round(_rng.uniform(0, 80), 1),
            certifications=_rng.choice([
                {"OEKO-TEX": True, "GOTS": False},
                {"OEKO-TEX": True, "GOTS": True, "BCI": True},
                {"OEKO-TEX": True},
                {"GOTS": True, "RWS": True},
                {"BCI": True, "OEKO-TEX": True},
                None,
            ]),
            compliance_status=_rng.choice([ComplianceStatus.compliant] * 7 + [ComplianceStatus.pending_review, ComplianceStatus.non_compliant]),
            last_audit_date=_past_date(180) if _rng.random() < 0.7 else None,
            created_at=product.created_at,
        ))
    session.flush()


def _seed_chat_sessions(session: Session):
    contexts = list(ChatContext)
    roles = list(UserRole)

    for i in range(5):
        chat_session = HbChatSession(
            user_role=_rng.choice(roles),
            context=_rng.choice(contexts),
            created_at=_past_dt(30),
        )
        session.add(chat_session)
        session.flush()

        exchanges = [
            ("How can I identify this product?", "I can help you identify the product. Please upload an image and I'll analyze it against our product database."),
            ("What's the quality score for the latest batch?", "The latest batch BATCH-2025-4521 has an overall quality score of 92.3/100 with 2 minor defects detected."),
            ("Show me authenticity stats for EMEA region", "In the EMEA region, we've processed 156 verification requests this month. 94% verified authentic, 4% suspicious, 2% confirmed counterfeit."),
            ("What are the sustainability metrics for our suit line?", "The BOSS suit line has an average carbon footprint of 18.5 kg CO2, water usage of 850L, and 35% recycled content. All items are OEKO-TEX certified."),
            ("Track product HB-BOSS-SUI-1000", "Product HB-BOSS-SUI-1000 was manufactured in Izmir, shipped to Hamburg warehouse, inspected, and distributed to 3 retail locations."),
        ]
        exchange = exchanges[i % len(exchanges)]
        base_time = chat_session.created_at

        session.add(HbChatMessage(
            session_id=chat_session.id,
            role="user",
            content=exchange[0],
            created_at=base_time + timedelta(seconds=1),
        ))
        session.add(HbChatMessage(
            session_id=chat_session.id,
            role="assistant",
            content=exchange[1],
            created_at=base_time + timedelta(seconds=3),
        ))

    session.flush()
