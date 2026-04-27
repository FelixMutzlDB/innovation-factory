"""Seed script for AECO Hub.

Generates the "Schuster Bau AG" portfolio: 5 construction projects spanning
the design → build → operate → demolish lifecycle, with buildings, floors,
spaces, assets, members, milestones, documents, issues, sensor devices, and
the marketplace + relationships graph.

Phase 1 scope: core spatial hierarchy + lifecycle metadata. Heavy lifecycle
tables (BIM elements, full schedule, cost ledger, site reports) are seeded
sparsely here; Phase 2 expands them when their routers ship.

Idempotent: re-runs are safe — early-returns when ``DtProject`` already has
rows. Deterministic via a seeded ``random.Random`` so demo data is stable.
"""

import random
from datetime import date, datetime, timedelta, timezone
from typing import Optional, TypedDict

from sqlmodel import Session, select

from .models import (
    AecoAssetCategory,
    AecoBimDiscipline,
    AecoBimLod,
    AecoBuildingType,
    AecoDocumentType,
    AecoIntegrationStatus,
    AecoIssueCategory,
    AecoIssueSeverity,
    AecoIssueStatus,
    AecoLifecycleSegment,
    AecoMemberRole,
    AecoProjectPhase,
    AecoProjectStatus,
    AecoRelationshipType,
    AecoSensorType,
    AecoSpaceType,
    DtAsset,
    DtBimModel,
    DtBuilding,
    DtDocument,
    DtFloor,
    DtIssue,
    DtMarketplaceApp,
    DtMarketplacePartner,
    DtMilestone,
    DtPartnerIntegration,
    DtProject,
    DtProjectMember,
    DtProjectPhase,
    DtRelationship,
    DtSensorDevice,
    DtSpace,
)

_rng = random.Random(2026)
TODAY = date.today()


def _past_date(min_days: int, max_days: int) -> date:
    return TODAY - timedelta(days=_rng.randint(min_days, max_days))


def _future_date(min_days: int, max_days: int) -> date:
    return TODAY + timedelta(days=_rng.randint(min_days, max_days))


# ---------------------------------------------------------------------------
# Project portfolio definition (Schuster Bau AG)
# ---------------------------------------------------------------------------


class _BuildingSpec(TypedDict):
    name: str
    type: AecoBuildingType
    floors: int
    gfa: float
    year: Optional[int]


class _ProjectSpec(TypedDict):
    code: str
    name: str
    description: str
    client_name: str
    city: str
    country: str
    phase: AecoProjectPhase
    status: AecoProjectStatus
    progress_pct: float
    budget_eur: float
    actual_cost_eur: float
    buildings: list[_BuildingSpec]
    spaces_per_floor: int
    assets_per_building: int
    sensors_per_building: int


PORTFOLIO: list[_ProjectSpec] = [
    {
        "code": "QSP-2024",
        "name": "Quartier am Stadtpark",
        "description": (
            "Mixed-use neighborhood development with residential, retail, "
            "and shared courtyard. Fully occupied since 2024."
        ),
        "client_name": "Stadtpark Immobilien GmbH",
        "city": "Munich",
        "country": "DE",
        "phase": AecoProjectPhase.operate,
        "status": AecoProjectStatus.active,
        "progress_pct": 100.0,
        "budget_eur": 78_500_000.0,
        "actual_cost_eur": 81_300_000.0,
        "buildings": [
            {"name": "QSP-A Residential North", "type": AecoBuildingType.residential, "floors": 6, "gfa": 12_400.0, "year": 2024},
            {"name": "QSP-B Residential South", "type": AecoBuildingType.residential, "floors": 5, "gfa": 10_800.0, "year": 2024},
            {"name": "QSP-C Retail Plinth", "type": AecoBuildingType.retail, "floors": 2, "gfa": 4_900.0, "year": 2024},
        ],
        "spaces_per_floor": 14,
        "assets_per_building": 90,
        "sensors_per_building": 40,
    },
    {
        "code": "THC-2025",
        "name": "TechHub Campus Garching",
        "description": (
            "Two-building office campus for life-sciences tenants. Currently "
            "65% complete; envelope and MEP rough-in finished."
        ),
        "client_name": "Bayern Tech Estates AG",
        "city": "Garching",
        "country": "DE",
        "phase": AecoProjectPhase.build,
        "status": AecoProjectStatus.active,
        "progress_pct": 65.0,
        "budget_eur": 142_000_000.0,
        "actual_cost_eur": 91_400_000.0,
        "buildings": [
            {"name": "THC-1 East Wing", "type": AecoBuildingType.office, "floors": 6, "gfa": 18_200.0, "year": None},
            {"name": "THC-2 West Wing", "type": AecoBuildingType.office, "floors": 4, "gfa": 12_900.0, "year": None},
        ],
        "spaces_per_floor": 8,
        "assets_per_building": 30,
        "sensors_per_building": 6,
    },
    {
        "code": "KES-2026",
        "name": "Klinikum Erweiterung Süd",
        "description": (
            "Hospital extension wing with surgical theatres and inpatient "
            "wards. Schematic design at LOD 300; permit submission Q3."
        ),
        "client_name": "Klinikum Stuttgart gGmbH",
        "city": "Stuttgart",
        "country": "DE",
        "phase": AecoProjectPhase.design,
        "status": AecoProjectStatus.active,
        "progress_pct": 22.0,
        "budget_eur": 64_000_000.0,
        "actual_cost_eur": 4_100_000.0,
        "buildings": [
            {"name": "KES Hauptbau", "type": AecoBuildingType.healthcare, "floors": 5, "gfa": 9_600.0, "year": None},
        ],
        "spaces_per_floor": 8,
        "assets_per_building": 0,
        "sensors_per_building": 0,
    },
    {
        "code": "LOG-A9",
        "name": "Logistikzentrum A9",
        "description": (
            "Single high-bay warehouse with automated storage/retrieval and "
            "dense building-automation IoT footprint."
        ),
        "client_name": "Süddeutsche Logistik AG",
        "city": "Ingolstadt",
        "country": "DE",
        "phase": AecoProjectPhase.operate,
        "status": AecoProjectStatus.active,
        "progress_pct": 100.0,
        "budget_eur": 38_000_000.0,
        "actual_cost_eur": 37_200_000.0,
        "buildings": [
            {"name": "LOG-A9 Hall", "type": AecoBuildingType.industrial, "floors": 4, "gfa": 22_400.0, "year": 2022},
        ],
        "spaces_per_floor": 10,
        "assets_per_building": 60,
        "sensors_per_building": 70,
    },
    {
        "code": "AMS-RENO",
        "name": "Altbau Maximilianstraße",
        "description": (
            "Heritage renovation: partial demolition of rear annex, full "
            "MEP replacement, restoration of street facade."
        ),
        "client_name": "Maximilian Real Estate KG",
        "city": "Munich",
        "country": "DE",
        "phase": AecoProjectPhase.demolish,
        "status": AecoProjectStatus.active,
        "progress_pct": 38.0,
        "budget_eur": 12_500_000.0,
        "actual_cost_eur": 5_800_000.0,
        "buildings": [
            {"name": "Maximilianstraße 14", "type": AecoBuildingType.mixed_use, "floors": 4, "gfa": 3_900.0, "year": 1894},
        ],
        "spaces_per_floor": 7,
        "assets_per_building": 18,
        "sensors_per_building": 4,
    },
]


SPACE_TYPE_MIX = {
    AecoBuildingType.residential: [AecoSpaceType.apartment, AecoSpaceType.corridor, AecoSpaceType.bathroom, AecoSpaceType.kitchen, AecoSpaceType.common_area, AecoSpaceType.storage],
    AecoBuildingType.office: [AecoSpaceType.office, AecoSpaceType.meeting_room, AecoSpaceType.corridor, AecoSpaceType.bathroom, AecoSpaceType.technical, AecoSpaceType.common_area],
    AecoBuildingType.retail: [AecoSpaceType.retail_unit, AecoSpaceType.corridor, AecoSpaceType.storage, AecoSpaceType.bathroom],
    AecoBuildingType.mixed_use: [AecoSpaceType.apartment, AecoSpaceType.retail_unit, AecoSpaceType.office, AecoSpaceType.corridor, AecoSpaceType.bathroom, AecoSpaceType.storage],
    AecoBuildingType.industrial: [AecoSpaceType.warehouse_zone, AecoSpaceType.office, AecoSpaceType.corridor, AecoSpaceType.technical, AecoSpaceType.bathroom, AecoSpaceType.storage],
    AecoBuildingType.healthcare: [AecoSpaceType.patient_room, AecoSpaceType.operating_theatre, AecoSpaceType.office, AecoSpaceType.corridor, AecoSpaceType.bathroom, AecoSpaceType.technical],
}


MEMBER_TEMPLATES = [
    ("Anna Becker", "Schuster Bau AG", AecoMemberRole.project_manager),
    ("Tobias Lang", "Schuster Bau AG", AecoMemberRole.contractor),
    ("Dr. Petra Vogel", "Vogel Architekten", AecoMemberRole.architect),
    ("Markus Klein", "MEP-Planung Klein GmbH", AecoMemberRole.engineer),
    ("Sabine Hartmann", "Stadtpark Immobilien", AecoMemberRole.owner),
    ("Jan Wiegand", "Wiegand Bau-Subunternehmen", AecoMemberRole.supplier),
    ("Marie Schulze", "FM-Service Süd", AecoMemberRole.facility_manager),
]


PARTNERS = [
    ("Spacewell Connect", "Workplace and IoT-driven facility management.", AecoLifecycleSegment.operate),
    ("Crem Solutions", "Property and lease management software.", AecoLifecycleSegment.operate),
    ("dTwin Operations", "Operational digital-twin orchestration.", AecoLifecycleSegment.operate),
    ("Allplan BIM", "Architectural and engineering BIM authoring.", AecoLifecycleSegment.design),
    ("Archicad Studio", "BIM authoring for architects.", AecoLifecycleSegment.design),
    ("Vectorworks Design", "Multi-discipline design platform.", AecoLifecycleSegment.design),
    ("Solibri QA/QC", "Model-based clash detection and rule checking.", AecoLifecycleSegment.qa_qc),
    ("dRofus Briefing", "Room data sheets and equipment briefs.", AecoLifecycleSegment.requirements),
    ("Bluebeam Markup", "Construction document review and markups.", AecoLifecycleSegment.build),
    ("NEVARIS Cost", "Bill of quantities and cost management.", AecoLifecycleSegment.build),
    ("GoCanvas Field", "Mobile site reporting and inspections.", AecoLifecycleSegment.build),
    ("Cinema 4D Visuals", "High-fidelity rendering and walkthrough.", AecoLifecycleSegment.visualize),
]


def seed_aeco_data(session: Session) -> None:
    """Idempotent seed entry point — registered in ``backend/seed.py``."""
    existing = session.exec(select(DtProject)).first()
    if existing:
        return

    projects_by_code = _seed_projects(session)
    _seed_phase_history(session, projects_by_code)
    _seed_milestones(session, projects_by_code)
    _seed_members(session, projects_by_code)
    buildings_by_project = _seed_buildings(session, projects_by_code)
    floors_by_building = _seed_floors(session, buildings_by_project)
    spaces_by_building = _seed_spaces(session, projects_by_code, buildings_by_project, floors_by_building)
    _seed_assets(session, projects_by_code, buildings_by_project, spaces_by_building)
    _seed_sensors(session, projects_by_code, buildings_by_project, spaces_by_building)
    _seed_documents(session, projects_by_code)
    _seed_issues(session, projects_by_code, spaces_by_building)
    _seed_bim_models(session, projects_by_code, buildings_by_project)
    partners = _seed_marketplace_partners(session)
    apps = _seed_marketplace_apps(session, partners)
    _seed_partner_integrations(session, projects_by_code, apps)
    _seed_relationships(session, projects_by_code, buildings_by_project)
    session.commit()
    print("  Seeded AECO Hub data.")


# ---------------------------------------------------------------------------
# Per-table seeders
# ---------------------------------------------------------------------------


def _seed_projects(session: Session) -> dict[str, DtProject]:
    out: dict[str, DtProject] = {}
    for spec in PORTFOLIO:
        start = _past_date(400, 1200)
        target = start + timedelta(days=_rng.randint(540, 1080))
        actual_completion = None
        if spec["phase"] == AecoProjectPhase.operate and spec["progress_pct"] >= 100:
            actual_completion = start + timedelta(days=_rng.randint(540, 1000))
        project = DtProject(
            code=spec["code"],
            name=spec["name"],
            description=spec["description"],
            client_name=spec["client_name"],
            city=spec["city"],
            country=spec["country"],
            phase=spec["phase"],
            status=spec["status"],
            progress_pct=spec["progress_pct"],
            budget_eur=spec["budget_eur"],
            actual_cost_eur=spec["actual_cost_eur"],
            start_date=start,
            target_completion_date=target,
            actual_completion_date=actual_completion,
        )
        session.add(project)
        session.flush()
        out[spec["code"]] = project
    return out


def _seed_phase_history(session: Session, projects: dict[str, DtProject]) -> None:
    """One DtProjectPhase row per phase the project has actually entered."""
    phase_order = [AecoProjectPhase.design, AecoProjectPhase.build, AecoProjectPhase.operate, AecoProjectPhase.demolish]
    for spec in PORTFOLIO:
        project = projects[spec["code"]]
        current = spec["phase"]
        for phase in phase_order:
            session.add(DtProjectPhase(
                project_id=project.id,
                phase=phase,
                started_on=_past_date(60, 800),
                ended_on=_past_date(1, 60) if phase != current else None,
                notes=f"{phase.value.capitalize()} phase notes for {project.code}.",
            ))
            if phase == current:
                break


def _seed_milestones(session: Session, projects: dict[str, DtProject]) -> None:
    templates = [
        ("Permit submission", AecoProjectPhase.design),
        ("Foundation pour", AecoProjectPhase.build),
        ("Topping-out", AecoProjectPhase.build),
        ("MEP commissioning", AecoProjectPhase.build),
        ("Handover to operations", AecoProjectPhase.operate),
        ("First-year operations review", AecoProjectPhase.operate),
    ]
    for project in projects.values():
        for name, phase in templates:
            target = _past_date(1, 600) if _rng.random() < 0.6 else _future_date(1, 400)
            completed = target < TODAY and _rng.random() < 0.7
            session.add(DtMilestone(
                project_id=project.id,
                name=name,
                phase=phase,
                target_date=target,
                actual_date=target if completed else None,
                completed=completed,
                description=f"{name} for {project.name}",
            ))


def _seed_members(session: Session, projects: dict[str, DtProject]) -> None:
    for project in projects.values():
        for name, org, role in MEMBER_TEMPLATES:
            slug_org = org.lower().split()[0].replace(".", "")
            slug_name = name.lower().replace("dr.", "").replace(" ", ".").strip(".")
            session.add(DtProjectMember(
                project_id=project.id,
                name=name,
                organization=org,
                role=role,
                email=f"{slug_name}@{slug_org}.de",
            ))


def _seed_buildings(
    session: Session, projects: dict[str, DtProject]
) -> dict[str, list[DtBuilding]]:
    out: dict[str, list[DtBuilding]] = {}
    for spec in PORTFOLIO:
        project = projects[spec["code"]]
        bldgs: list[DtBuilding] = []
        for bldg_spec in spec["buildings"]:
            bldg = DtBuilding(
                project_id=project.id,
                name=bldg_spec["name"],
                building_type=bldg_spec["type"],
                floor_count=bldg_spec["floors"],
                gross_floor_area_sqm=bldg_spec["gfa"],
                year_built=bldg_spec["year"],
                address=f"{spec['city']}, {spec['country']}",
            )
            session.add(bldg)
            session.flush()
            bldgs.append(bldg)
        out[spec["code"]] = bldgs
    return out


def _seed_floors(
    session: Session, buildings: dict[str, list[DtBuilding]]
) -> dict[int, list[DtFloor]]:
    out: dict[int, list[DtFloor]] = {}
    for bldg_list in buildings.values():
        for bldg in bldg_list:
            floors: list[DtFloor] = []
            for level in range(bldg.floor_count):
                floor = DtFloor(
                    building_id=bldg.id,
                    name=f"L{level}" if level > 0 else "Ground",
                    level=level,
                    area_sqm=round(bldg.gross_floor_area_sqm / max(bldg.floor_count, 1), 1),
                )
                session.add(floor)
                session.flush()
                floors.append(floor)
            assert bldg.id is not None
            out[bldg.id] = floors
    return out


def _seed_spaces(
    session: Session,
    projects: dict[str, DtProject],
    buildings: dict[str, list[DtBuilding]],
    floors: dict[int, list[DtFloor]],
) -> dict[int, list[DtSpace]]:
    """Returns spaces keyed by building id (for downstream asset/sensor seeders)."""
    out: dict[int, list[DtSpace]] = {}
    for spec in PORTFOLIO:
        spaces_per_floor = spec["spaces_per_floor"]
        for bldg in buildings[spec["code"]]:
            assert bldg.id is not None
            mix = SPACE_TYPE_MIX.get(bldg.building_type, [AecoSpaceType.office])
            bldg_spaces: list[DtSpace] = []
            for floor in floors.get(bldg.id, []):
                for idx in range(spaces_per_floor):
                    space_type = _rng.choice(mix)
                    space = DtSpace(
                        floor_id=floor.id,
                        name=f"{floor.name}.{idx + 1:02d}",
                        space_type=space_type,
                        area_sqm=round(_rng.uniform(12.0, 80.0), 1),
                        capacity=_rng.randint(1, 40),
                        room_number=f"{bldg.id}-{floor.level}{idx + 1:02d}",
                    )
                    session.add(space)
                    bldg_spaces.append(space)
            session.flush()
            out[bldg.id] = bldg_spaces
    return out


def _seed_assets(
    session: Session,
    projects: dict[str, DtProject],
    buildings: dict[str, list[DtBuilding]],
    spaces_by_building: dict[int, list[DtSpace]],
) -> None:
    categories = list(AecoAssetCategory)
    for spec in PORTFOLIO:
        target = spec["assets_per_building"]
        if target <= 0:
            continue
        for bldg in buildings[spec["code"]]:
            assert bldg.id is not None
            building_spaces = spaces_by_building.get(bldg.id, [])
            for i in range(target):
                category = _rng.choice(categories)
                space = _rng.choice(building_spaces) if building_spaces else None
                session.add(DtAsset(
                    space_id=space.id if space else None,
                    building_id=bldg.id,
                    name=f"{category.value.upper()}-{bldg.id:03d}-{i + 1:03d}",
                    category=category,
                    manufacturer=_rng.choice(["Siemens", "ABB", "Bosch", "Schneider", "Vaillant"]),
                    model=f"M-{_rng.randint(1000, 9999)}",
                    serial_number=f"SN{_rng.randint(100000, 999999)}",
                    install_date=_past_date(180, 1500),
                ))


def _seed_sensors(
    session: Session,
    projects: dict[str, DtProject],
    buildings: dict[str, list[DtBuilding]],
    spaces_by_building: dict[int, list[DtSpace]],
) -> None:
    sensor_types = list(AecoSensorType)
    for spec in PORTFOLIO:
        target = spec["sensors_per_building"]
        if target <= 0:
            continue
        for bldg in buildings[spec["code"]]:
            assert bldg.id is not None
            building_spaces = spaces_by_building.get(bldg.id, [])
            for i in range(target):
                sensor_type = _rng.choice(sensor_types)
                space = _rng.choice(building_spaces) if building_spaces else None
                session.add(DtSensorDevice(
                    space_id=space.id if space else None,
                    building_id=bldg.id,
                    sensor_code=f"S-{bldg.id:03d}-{i + 1:04d}",
                    sensor_type=sensor_type,
                    manufacturer=_rng.choice(["ABB", "Siemens", "Schneider", "KNX-Solutions"]),
                    model=f"BA-{_rng.randint(100, 999)}",
                    install_date=_past_date(60, 800),
                    last_seen_at=datetime.now(timezone.utc) - timedelta(minutes=_rng.randint(0, 240)),
                ))


def _seed_documents(session: Session, projects: dict[str, DtProject]) -> None:
    doc_templates = [
        ("Master architectural plans", AecoDocumentType.bim, AecoProjectPhase.design),
        ("Structural calculations report", AecoDocumentType.report, AecoProjectPhase.design),
        ("MEP design narrative", AecoDocumentType.report, AecoProjectPhase.design),
        ("Building permit (Baugenehmigung)", AecoDocumentType.permit, AecoProjectPhase.design),
        ("General contractor agreement", AecoDocumentType.contract, AecoProjectPhase.build),
        ("Weekly site progress photos", AecoDocumentType.photo, AecoProjectPhase.build),
        ("As-built drawings package", AecoDocumentType.drawing, AecoProjectPhase.build),
        ("COBie handover dataset", AecoDocumentType.cobie, AecoProjectPhase.operate),
        ("Operating manual — HVAC", AecoDocumentType.report, AecoProjectPhase.operate),
        ("Annual fire-safety inspection", AecoDocumentType.report, AecoProjectPhase.operate),
    ]
    for project in projects.values():
        for title, dtype, phase in doc_templates:
            session.add(DtDocument(
                project_id=project.id,
                title=title,
                document_type=dtype,
                phase=phase,
                file_url=f"/volumes/aeco_hub/docs/{project.code.lower()}/{title.lower().replace(' ', '_')}.pdf",
                author=_rng.choice([m[0] for m in MEMBER_TEMPLATES]),
                version=f"{_rng.randint(1, 5)}.{_rng.randint(0, 9)}",
            ))


def _seed_issues(
    session: Session,
    projects: dict[str, DtProject],
    spaces_by_building: dict[int, list[DtSpace]],
) -> None:
    issue_templates = [
        ("Pipe-duct clash on level 3", AecoIssueCategory.clash, AecoIssueSeverity.major),
        ("Missing fire-rated penetration seal", AecoIssueCategory.safety, AecoIssueSeverity.critical),
        ("RFI: ceiling height in lobby", AecoIssueCategory.rfi, AecoIssueSeverity.minor),
        ("Concrete spalling in stair core", AecoIssueCategory.defect, AecoIssueSeverity.moderate),
        ("Owner-requested layout change", AecoIssueCategory.change_request, AecoIssueSeverity.moderate),
        ("Door swing conflicts with column", AecoIssueCategory.design_issue, AecoIssueSeverity.minor),
        ("HVAC duct routing requires re-coordination", AecoIssueCategory.clash, AecoIssueSeverity.moderate),
        ("Damaged window frame on facade", AecoIssueCategory.defect, AecoIssueSeverity.minor),
    ]
    statuses = list(AecoIssueStatus)
    all_spaces = [s for sp_list in spaces_by_building.values() for s in sp_list]
    for project in projects.values():
        for title, category, severity in issue_templates:
            status = _rng.choice(statuses)
            space = _rng.choice(all_spaces) if all_spaces else None
            resolved_at = (
                datetime.now(timezone.utc) - timedelta(days=_rng.randint(1, 200))
                if status in (AecoIssueStatus.resolved, AecoIssueStatus.closed)
                else None
            )
            session.add(DtIssue(
                project_id=project.id,
                title=title,
                description=f"{title} — raised during routine inspection on {project.name}.",
                category=category,
                severity=severity,
                status=status,
                raised_by=_rng.choice([m[0] for m in MEMBER_TEMPLATES]),
                assigned_to=_rng.choice([m[0] for m in MEMBER_TEMPLATES]),
                space_id=space.id if space else None,
                resolved_at=resolved_at,
            ))


def _seed_bim_models(
    session: Session,
    projects: dict[str, DtProject],
    buildings: dict[str, list[DtBuilding]],
) -> None:
    """One representative BIM model per discipline per building (lightweight Phase 1)."""
    disciplines = [AecoBimDiscipline.architectural, AecoBimDiscipline.structural, AecoBimDiscipline.mep]
    for spec in PORTFOLIO:
        project = projects[spec["code"]]
        if project.phase == AecoProjectPhase.demolish:
            continue
        for bldg in buildings[spec["code"]]:
            for disc in disciplines:
                lod = AecoBimLod.lod_300 if project.phase == AecoProjectPhase.design else AecoBimLod.lod_400
                session.add(DtBimModel(
                    project_id=project.id,
                    building_id=bldg.id,
                    name=f"{bldg.name} — {disc.value.upper()}",
                    discipline=disc,
                    lod=lod,
                    version=f"{_rng.randint(1, 4)}.{_rng.randint(0, 9)}",
                    file_url=f"/volumes/aeco_hub/bim/{project.code.lower()}/{bldg.id}_{disc.value}.ifc",
                    file_size_mb=round(_rng.uniform(45.0, 380.0), 1),
                    element_count=_rng.randint(800, 4500),
                    uploaded_by=_rng.choice([m[0] for m in MEMBER_TEMPLATES]),
                ))


def _seed_marketplace_partners(session: Session) -> list[DtMarketplacePartner]:
    out: list[DtMarketplacePartner] = []
    for name, desc, segment in PARTNERS:
        partner = DtMarketplacePartner(
            name=name,
            description=desc,
            website=f"https://{name.lower().replace(' ', '-').replace('/', '-')}.example.com",
            logo_url=f"/assets/aeco-tools/{name.lower().replace(' ', '-').replace('/', '-')}.svg",
            lifecycle_segment=segment,
        )
        session.add(partner)
        out.append(partner)
    session.flush()
    return out


def _seed_marketplace_apps(
    session: Session, partners: list[DtMarketplacePartner]
) -> list[DtMarketplaceApp]:
    out: list[DtMarketplaceApp] = []
    for partner in partners:
        for j in range(_rng.randint(1, 2)):
            app = DtMarketplaceApp(
                partner_id=partner.id,
                name=f"{partner.name} Connector",
                description=f"Integrate {partner.name} data into the AECO Hub digital twin.",
                lifecycle_segment=partner.lifecycle_segment,
                logo_url=partner.logo_url,
                is_featured=(j == 0 and _rng.random() < 0.4),
            )
            session.add(app)
            out.append(app)
    session.flush()
    return out


def _seed_partner_integrations(
    session: Session,
    projects: dict[str, DtProject],
    apps: list[DtMarketplaceApp],
) -> None:
    statuses = list(AecoIntegrationStatus)
    for project in projects.values():
        chosen = _rng.sample(apps, k=min(len(apps), _rng.randint(3, 5)))
        for app in chosen:
            status = _rng.choice(statuses)
            session.add(DtPartnerIntegration(
                project_id=project.id,
                app_id=app.id,
                status=status,
                activated_at=(
                    datetime.now(timezone.utc) - timedelta(days=_rng.randint(1, 400))
                    if status == AecoIntegrationStatus.connected
                    else None
                ),
                notes="",
            ))


def _seed_relationships(
    session: Session,
    projects: dict[str, DtProject],
    buildings: dict[str, list[DtBuilding]],
) -> None:
    """Seed a small graph of project-level relationships for the Phase 5 graph view."""
    for spec in PORTFOLIO:
        project = projects[spec["code"]]
        for bldg in buildings[spec["code"]]:
            session.add(DtRelationship(
                project_id=project.id,
                source_type="project",
                source_id=project.id,
                target_type="building",
                target_id=bldg.id,
                relationship_type=AecoRelationshipType.contains,
                label=f"{project.name} contains {bldg.name}",
            ))
