"""Master seed script for the innovation-factory platform.

Each project's seed runs in its own transaction (committed independently)
so a failure in one project — e.g. AECO Hub's tables don't exist yet on a
fresh deploy — can't roll back another project's inserts. The earlier
behaviour was a single big ``session.commit()`` at the end, which on
Phase 6 deploy caused the platform Project row for ``aeco-hub`` to roll
back when ``seed_aeco_data`` raised on the missing ``dt_projects`` table.

Each individual seed function is idempotent (it checks for existing rows
before inserting), so re-running the master seed is safe.
"""
import time
from typing import Callable

from sqlalchemy.exc import InterfaceError, OperationalError
from sqlmodel import Session, select

from .logger import logger

# Transient DB connection errors worth retrying. The local-dev PGlite server
# occasionally drops a fresh connection mid-seed ("server closed the
# connection unexpectedly") — every seed opens a new NullPool connection, and
# a few in the startup burst lose the race with PGlite settling. Observed in
# CI: 2 of 7 project seeds failed this way while the other 5 (and the DDL)
# succeeded on the same server, leaving those pages dataless. Prod Lakebase
# connections are stable, so these retries effectively never fire there.
_TRANSIENT_DB_ERRORS = (OperationalError, InterfaceError)
from .models import Project
from .projects.adtech_intelligence.seed import seed_at_data
from .projects.aeco_hub.seed import seed_aeco_data
from .projects.bsh_home_connect.seed import seed_bsh_data
from .projects.hb_product_center.seed import seed_hb_data
from .projects.mol_asm_cockpit.seed import seed_mac_data
from .projects.vi_home_one.seed import seed_vh_data
from .projects.yard_pro.seed import seed_yp_data
from .runtime import Runtime


# (label, seed function). Order doesn't matter functionally — each runs in
# its own transaction — but matches the historical sequence for easier
# log scanning.
_PROJECT_SEEDS: list[tuple[str, Callable[[Session], None]]] = [
    ("ViDistrictOne", seed_vh_data),
    ("BSH Home Connect", seed_bsh_data),
    ("MOL ASM Cockpit", seed_mac_data),
    ("AdTech Intelligence", seed_at_data),
    ("HB Product Center", seed_hb_data),
    ("AECO Hub", seed_aeco_data),
    ("yard-pro", seed_yp_data),
]


def _safe_seed(
    label: str,
    fn: Callable[[Session], None],
    session: Session,
    *,
    max_attempts: int = 4,
) -> bool:
    """Run a seed function and commit its transaction independently.

    Returns ``True`` on success, ``False`` on failure (already rolled back).
    Transient DB connection errors are retried with backoff (seeds are
    idempotent, so re-running is safe); any other exception fails fast so a
    genuine seed bug isn't silently retried. Either way the exception is
    captured so subsequent seeds in the master loop continue.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            fn(session)
            session.commit()
            return True
        except _TRANSIENT_DB_ERRORS as e:
            # Rollback the broken transaction so the retry (or the next seed)
            # gets fresh transaction state — without this, subsequent .exec()
            # calls raise InFailedSqlTransaction on the same session.
            session.rollback()
            if attempt < max_attempts:
                backoff = 0.25 * (2 ** (attempt - 1))  # 0.25s, 0.5s, 1s
                logger.warning(
                    f"Seed for {label} hit a transient DB error "
                    f"(attempt {attempt}/{max_attempts}), retrying in "
                    f"{backoff:.2f}s: {e}"
                )
                time.sleep(backoff)
                continue
            logger.error(
                f"Seed for {label} failed after {max_attempts} attempts "
                f"(continuing with others): {e}"
            )
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Seed for {label} failed (continuing with others): {e}")
            return False
    return False


def check_and_seed_if_empty(runtime: Runtime):
    """Run the master seed.

    The platform ``if_projects`` row + each per-project seed run in their
    own transactions. All seeds are idempotent — they no-op when their
    data is already present — so this can be called on every app start.
    """
    print("\nStarting database seeding for innovation-factory...")
    with runtime.get_session() as session:
        # Platform-level Project rows always run first — landing-page cards
        # depend on these. _seed_projects only flushes; we commit here.
        if _safe_seed("platform projects", _seed_projects, session):
            logger.info("Platform projects seeded.")

        # Each project seeds its own data in an isolated transaction.
        for label, fn in _PROJECT_SEEDS:
            if _safe_seed(label, fn, session):
                logger.info(f"  {label} seed OK.")

    print("Database seeding completed.\n")


def _seed_projects(session: Session):
    """Seed the projects table."""
    projects_data = [
        {
            "slug": "vi-home-one",
            "name": "ViDistrictOne",
            "description": "Smart neighborhood energy management system by Viessmann. Monitor and optimize energy consumption, PV generation, battery storage, and EV charging across a residential district.",
            "company": "Viessmann",
            "icon": "Zap",
            "color": "#22c55e",
        },
        {
            "slug": "bsh-home-connect",
            "name": "BSH Remote Assist",
            "description": "AI-powered appliance support platform for BSH kitchen appliances. Troubleshoot issues, manage service tickets, and get instant help from AI-assisted diagnostics.",
            "company": "BSH Home Appliances",
            "icon": "Wrench",
            "color": "#3b82f6",
        },
        {
            "slug": "mol-asm-cockpit",
            "name": "ASM Cockpit",
            "description": "Interactive cockpit for Area Sales Managers to explore retail station performance, get AI-powered issue resolution, and monitor anomalies across fuel, non-fuel, loyalty, supply, and workforce operations.",
            "company": "Retail Network",
            "icon": "Layers",
            "color": "#f59e0b",
         },
         {
            "slug": "adtech-intelligence",
            "name": "AdTech Intelligence",
            "description": "AI-powered advertising operations platform. Explore demand and inventory across online and outdoor channels, resolve issues with an intelligent agent, and monitor anomalies in campaign performance.",
            "company": "Media Solutions",
            "icon": "Radio",
            "color": "#8b5cf6",
        },
        {
            "slug": "hb-product-center",
            "name": "HB Product Center",
            "description": "Intelligent Product Center for visual product recognition, AI-powered quality control, authenticity verification, and supply chain intelligence across the HB value chain.",
            "company": "HB",
            "icon": "ScanSearch",
            "color": "#1a1a1a",
        },
        {
            "slug": "aeco-hub",
            "name": "AECO Hub",
            "description": "Building lifecycle digital-twin platform for the AECO industry. Connects BIM geometry, construction progress, IoT sensor feeds, and facility management on a single Databricks Lakehouse.",
            "company": "AECO",
            "icon": "Building2",
            "color": "#F59E0B",
        },
        {
            "slug": "yard-pro",
            "name": "yard-pro",
            "description": "AI gardening companion that turns connected-tool telemetry and yard imagery into a season-by-season care plan. KA-grounded seasonal coach + snap-and-diagnose vision + personalized calendar.",
            "company": "Outdoor Power Equipment",
            "icon": "Sprout",
            "color": "#D9541F",
        },
    ]

    for project_data in projects_data:
        existing = session.exec(
            select(Project).where(Project.slug == project_data["slug"])
        ).first()
        if not existing:
            session.add(Project(**project_data))

    session.flush()
    print("  Seeded platform projects.")
