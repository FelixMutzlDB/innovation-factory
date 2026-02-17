"""Seed the Lakebase PostgreSQL database with the same data as local PGlite.

Usage:
    cd /path/to/innovation-factory
    .venv/bin/python scripts/seed_lakebase.py
"""

import os
import sys

# Add project src to path so imports work
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, "src"))

from urllib.parse import quote

from databricks.sdk import WorkspaceClient
from sqlalchemy import Enum as SAEnum, create_engine, event
from sqlmodel import SQLModel, Session, select, text

# ---- Lakebase connection details ----
PGHOST = "ep-solitary-morning-d1fm39qw.database.us-west-2.cloud.databricks.com"
PGDATABASE = "databricks_postgres"
PGPORT = 5432
PGSSLMODE = "require"
DATABRICKS_PROFILE = "e2-demo-field-eng"
ENDPOINT_NAME = "projects/ff37da7a-d6dc-4703-94e9-0201881be663/branches/br-tiny-hall-d1o2yr5i/endpoints/ep-solitary-morning-d1fm39qw"


def main():
    print("=" * 60)
    print("Lakebase Database Seeder")
    print("=" * 60)

    # Initialize Databricks SDK
    print(f"\n1. Connecting to Databricks workspace (profile: {DATABRICKS_PROFILE})...")
    ws = WorkspaceClient(profile=DATABRICKS_PROFILE)
    user = ws.current_user.me().user_name
    print(f"   Authenticated as: {user}")

    # Endpoint
    endpoint_name = ENDPOINT_NAME
    print(f"\n2. Using Lakebase endpoint: {endpoint_name}")

    # Import all models so SQLModel.metadata knows about them
    print("\n3. Importing all database models...")
    from innovation_factory.backend.models import Project  # noqa: F401
    from innovation_factory.backend.projects.vi_home_one.models import (  # noqa: F401
        VhNeighborhood, VhHousehold, VhEnergyDevice, VhEnergyReading,
        VhConsumptionBreakdown, VhEnergyProvider, VhMaintenanceAlert,
        VhTicket, VhTicketMedia, VhChatSession, VhChatMessage, VhKnowledgeArticle,
    )
    from innovation_factory.backend.projects.bsh_home_connect.models import (  # noqa: F401
        BshCustomer, BshTechnician, BshDevice, BshCustomerDevice,
        BshTicket, BshTicketNote, BshTicketMedia, BshKnowledgeArticle,
        BshDocument, BshChatSession, BshChatMessage,
    )
    from innovation_factory.backend.projects.adtech_intelligence.models import (  # noqa: F401
        AtAdvertiser, AtCampaign, AtAdInventory, AtPlacement,
        AtPerformanceMetric, AtAnomalyRule, AtAnomaly, AtIssue,
        AtCustomerContract, AtChatSession, AtChatMessage,
    )
    from innovation_factory.backend.projects.mol_asm_cockpit.models import (  # noqa: F401
        MacRegion, MacStation, MacFuelSale, MacNonfuelSale,
        MacLoyaltyMetric, MacWorkforceShift, MacInventory,
        MacCompetitorPrice, MacPriceHistory, MacAnomalyAlert,
        MacIssue, MacCustomerProfile, MacCustomerContract,
        MacChatSession, MacChatMessage,
    )
    print("   All models imported (including MOL ASM Cockpit).")

    # Build the SQLAlchemy engine with Lakebase credential injection
    print(f"\n4. Creating database engine for {PGHOST}/{PGDATABASE}...")
    assert user is not None
    encoded_user = quote(user, safe="")
    engine_url = f"postgresql+psycopg://{encoded_user}:@{PGHOST}:{PGPORT}/{PGDATABASE}?sslmode={PGSSLMODE}"

    engine = create_engine(
        engine_url,
        pool_recycle=45 * 60,
        connect_args={"sslmode": "require"},
        pool_size=4,
    )

    # Register the credential injection callback
    def before_connect(dialect, conn_rec, cargs, cparams):
        cred = ws.postgres.generate_database_credential(endpoint=endpoint_name)
        cparams["password"] = cred.token

    event.listen(engine, "do_connect", before_connect)

    # Test connection
    print("   Testing connection...")
    with Session(engine) as session:
        result = session.exec(text("SELECT 1"))  # type: ignore[arg-type]
        result.close()
    print("   Connection successful!")

    # Disable native PostgreSQL ENUMs (Lakebase doesn't allow CREATE TYPE)
    print("\n5. Creating database tables...")
    for table in SQLModel.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, SAEnum):
                column.type.native_enum = False

    # Drop all tables first to ensure clean slate
    print("   Dropping existing tables for clean re-seed...")
    SQLModel.metadata.drop_all(engine)
    print("   Dropped. Re-creating tables...")
    SQLModel.metadata.create_all(engine)
    print("   Tables re-created.")

    # Seed the data
    print("\n6. Seeding data...")
    from innovation_factory.backend.seed import _seed_projects
    from innovation_factory.backend.projects.vi_home_one.seed import seed_vh_data
    from innovation_factory.backend.projects.bsh_home_connect.seed import seed_bsh_data
    from innovation_factory.backend.projects.adtech_intelligence.seed import seed_at_data
    from innovation_factory.backend.projects.mol_asm_cockpit.seed import seed_mac_data

    with Session(engine) as session:
        print("   Seeding projects...")
        _seed_projects(session)
        print("   Seeding ViHome data...")
        seed_vh_data(session)
        print("   Seeding BSH data...")
        seed_bsh_data(session)
        print("   Seeding MOL ASM Cockpit data...")
        seed_mac_data(session)
        print("   Seeding AdTech data...")
        seed_at_data(session)
        session.commit()
        print("\n   Seeding completed successfully!")

    # Verify
    print("\n7. Verifying seeded data...")
    with Session(engine) as session:
        from innovation_factory.backend.models import Project
        projects = session.exec(select(Project)).all()
        print(f"   Projects: {len(projects)}")
        for p in projects:
            print(f"     - {p.name} ({p.slug})")

        # Count some key tables
        adv_count = session.exec(text("SELECT COUNT(*) FROM at_advertisers")).one()[0]
        camp_count = session.exec(text("SELECT COUNT(*) FROM at_campaigns")).one()[0]
        inv_count = session.exec(text("SELECT COUNT(*) FROM at_ad_inventory")).one()[0]
        issue_count = session.exec(text("SELECT COUNT(*) FROM at_issues")).one()[0]
        anom_count = session.exec(text("SELECT COUNT(*) FROM at_anomalies")).one()[0]
        print(f"\n   AdTech: {adv_count} advertisers, {camp_count} campaigns, "
              f"{inv_count} inventory, {issue_count} issues, {anom_count} anomalies")

        vh_hh = session.exec(text("SELECT COUNT(*) FROM vh_households")).one()[0]
        vh_read = session.exec(text("SELECT COUNT(*) FROM vh_energy_readings")).one()[0]
        print(f"   ViHome: {vh_hh} households, {vh_read} energy readings")

        bsh_dev = session.exec(text("SELECT COUNT(*) FROM bsh_devices")).one()[0]
        bsh_tick = session.exec(text("SELECT COUNT(*) FROM bsh_tickets")).one()[0]
        print(f"   BSH: {bsh_dev} devices, {bsh_tick} tickets")

        mac_st = session.exec(text("SELECT COUNT(*) FROM mac_stations")).one()[0]
        mac_fuel = session.exec(text("SELECT COUNT(*) FROM mac_fuel_sales")).one()[0]
        mac_issues = session.exec(text("SELECT COUNT(*) FROM mac_issues")).one()[0]
        mac_anom = session.exec(text("SELECT COUNT(*) FROM mac_anomaly_alerts")).one()[0]
        print(f"   MOL ASM: {mac_st} stations, {mac_fuel} fuel sales, "
              f"{mac_issues} issues, {mac_anom} anomaly alerts")

    print("\n" + "=" * 60)
    print("Done! Lakebase database is now seeded.")
    print("=" * 60)


if __name__ == "__main__":
    main()
