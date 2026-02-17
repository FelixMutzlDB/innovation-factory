"""Master seed script for the innovation-factory platform."""
from sqlmodel import Session, select
from .runtime import Runtime
from .models import Project
from .projects.vi_home_one.seed import seed_vh_data
from .projects.bsh_home_connect.seed import seed_bsh_data
from .projects.mol_asm_cockpit.seed import seed_mac_data
from .projects.adtech_intelligence.seed import seed_at_data
from .logger import logger


def check_and_seed_if_empty(runtime: Runtime):
    """Check if database is empty and seed if needed."""
    with runtime.get_session() as session:
        try:
            project = session.exec(select(Project)).first()
            if project:
                logger.info("Database already contains data - skipping seed")
                return
        except Exception as e:
            logger.error(f"Error checking database: {e}")

        logger.info("Database is empty - running seed script")
        print("\nStarting database seeding for innovation-factory...")

        _seed_projects(session)
        seed_vh_data(session)
        seed_bsh_data(session)
        seed_mac_data(session)
        seed_at_data(session)

        # Ensure everything is committed (sub-seed functions may return early
        # if their data already exists, skipping their own commit calls)
        session.commit()

        print("\nDatabase seeding completed successfully!\n")


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
    ]

    for project_data in projects_data:
        existing = session.exec(
            select(Project).where(Project.slug == project_data["slug"])
        ).first()
        if not existing:
            session.add(Project(**project_data))

    session.flush()
    print("  Seeded platform projects.")
