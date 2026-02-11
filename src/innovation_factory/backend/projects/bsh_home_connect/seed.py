"""Seed script for bsh-home-connect project data."""
from datetime import date
from sqlmodel import Session, select

from .models import (
    BshDevice,
    DeviceCategory,
    BshCustomer,
    BshTechnician,
    BshCustomerDevice,
    BshKnowledgeArticle,
    BshDocument,
)


def seed_bsh_data(session: Session):
    """Seed all bsh-home-connect data."""
    if session.exec(select(BshDevice)).first():
        return

    print("  Seeding bsh-home-connect data...")
    _seed_devices(session)
    _seed_knowledge_base(session)
    _seed_documents(session)
    _seed_customers(session)
    _seed_technicians(session)
    _seed_customer_devices(session)
    session.commit()
    print("  bsh-home-connect data seeded.")


def _seed_devices(session: Session):
    devices_data = [
        {"model_number": "SMS8YCI03E", "brand": "Bosch", "category": DeviceCategory.dishwasher, "name": "Serie 8 Dishwasher", "description": "Fully integrated dishwasher with PerfectDry and Home Connect"},
        {"model_number": "SN87YX03CE", "brand": "Siemens", "category": DeviceCategory.dishwasher, "name": "iQ700 Dishwasher", "description": "Built-in dishwasher with Zeolith drying"},
        {"model_number": "HBG7764B1", "brand": "Bosch", "category": DeviceCategory.oven, "name": "Serie 8 Built-in Oven", "description": "Pyrolytic oven with PerfectBake sensor"},
        {"model_number": "HB776G1B1", "brand": "Siemens", "category": DeviceCategory.oven, "name": "iQ700 Built-in Oven", "description": "Pyrolytic oven with activeClean"},
        {"model_number": "KGN39AIAT", "brand": "Bosch", "category": DeviceCategory.refrigerator, "name": "Serie 6 Fridge-Freezer", "description": "NoFrost fridge-freezer with VitaFresh"},
        {"model_number": "KG39NAIAT", "brand": "Siemens", "category": DeviceCategory.refrigerator, "name": "iQ300 Fridge-Freezer", "description": "NoFrost fridge-freezer with hyperFresh"},
        {"model_number": "PXY875KW1E", "brand": "Bosch", "category": DeviceCategory.cooktop, "name": "Serie 8 Induction Hob", "description": "FlexInduction hob with PerfectFry sensor"},
        {"model_number": "CTL636ES6", "brand": "Bosch", "category": DeviceCategory.coffee_machine, "name": "Built-in Coffee Machine", "description": "Fully automatic with OneTouch DoubleCup"},
        {"model_number": "BFL634GS1", "brand": "Bosch", "category": DeviceCategory.microwave, "name": "Serie 8 Built-in Microwave", "description": "Microwave with grill and AutoPilot 20"},
        {"model_number": "DWF97RV60", "brand": "Bosch", "category": DeviceCategory.other, "name": "Serie 6 Wall-mounted Hood", "description": "Wall-mounted hood with EcoSilence Drive"},
    ]
    for d in devices_data:
        session.add(BshDevice(**d))
    session.flush()


def _seed_knowledge_base(session: Session):
    articles = [
        {"title": "Dishwasher Error Code E15 - Water in Base Tray", "content": "Error E15: Water detected in base pan. Switch off, check hoses, tilt 45 degrees to drain.", "category": DeviceCategory.dishwasher, "issue_type": "error_code"},
        {"title": "Dishwasher Not Draining - Pump Blockage", "content": "E24/E25 errors: Clean filters, check drain pump for blockages.", "category": DeviceCategory.dishwasher, "issue_type": "troubleshooting"},
        {"title": "Oven Not Heating - Heating Element Check", "content": "Check power supply, verify heating element glows red, test temperature sensor.", "category": DeviceCategory.oven, "issue_type": "troubleshooting"},
        {"title": "Refrigerator Not Cooling - Temperature Issues", "content": "Check temperature settings (4C fridge, -18C freezer), door seal, condenser coils.", "category": DeviceCategory.refrigerator, "issue_type": "troubleshooting"},
        {"title": "Coffee Machine Descaling - Complete Guide", "content": "Descale every 2-3 months. Use Bosch Descaling Tablets.", "category": DeviceCategory.coffee_machine, "issue_type": "maintenance"},
        {"title": "Induction Hob Not Working - Pan Detection", "content": "Ensure cookware has magnetic base, minimum 12cm diameter, flat bottom.", "category": DeviceCategory.cooktop, "issue_type": "troubleshooting"},
    ]
    for a in articles:
        session.add(BshKnowledgeArticle(**a))
    session.flush()


def _seed_documents(session: Session):
    devices = session.exec(select(BshDevice)).all()
    for device in devices:
        session.add(BshDocument(
            device_id=device.id,
            title=f"{device.brand} {device.name} User Manual",
            document_type="user_manual",
            content=f"User Manual for {device.brand} {device.name} ({device.model_number})",
            language="en", version="1.0",
        ))
        session.add(BshDocument(
            device_id=device.id,
            title=f"{device.brand} {device.name} Quick Start Guide",
            document_type="quick_start",
            content=f"Quick Start Guide for {device.brand} {device.name}",
            language="en", version="1.0",
        ))
    session.flush()


def _seed_customers(session: Session):
    customers = [
        {"databricks_user_id": "customer_001", "email": "sarah.johnson@example.com", "first_name": "Sarah", "last_name": "Johnson", "phone": "+44 20 7123 4567", "address": "15 Baker Street", "city": "London", "country": "UK"},
        {"databricks_user_id": "customer_002", "email": "michael.schmidt@example.com", "first_name": "Michael", "last_name": "Schmidt", "phone": "+49 30 1234567", "address": "Hauptstr. 42", "city": "Berlin", "country": "Germany"},
        {"databricks_user_id": "customer_003", "email": "emma.brown@example.com", "first_name": "Emma", "last_name": "Brown", "phone": "+44 161 123 4567", "address": "23 Oxford Road", "city": "Manchester", "country": "UK"},
        {"databricks_user_id": "customer_004", "email": "lucas.dubois@example.com", "first_name": "Lucas", "last_name": "Dubois", "phone": "+33 1 42 12 34 56", "address": "8 Rue de Rivoli", "city": "Paris", "country": "France"},
        {"databricks_user_id": "customer_005", "email": "sophia.rossi@example.com", "first_name": "Sophia", "last_name": "Rossi", "phone": "+39 02 1234 5678", "address": "Via Montenapoleone 10", "city": "Milan", "country": "Italy"},
        {"databricks_user_id": "customer_006", "email": "oliver.mueller@example.com", "first_name": "Oliver", "last_name": "Mueller", "phone": "+49 89 1234567", "address": "Marienplatz 5", "city": "Munich", "country": "Germany"},
        {"databricks_user_id": "customer_007", "email": "isabella.lopez@example.com", "first_name": "Isabella", "last_name": "Lopez", "phone": "+34 91 123 4567", "address": "Gran Via 28", "city": "Madrid", "country": "Spain"},
        {"databricks_user_id": "customer_008", "email": "james.wilson@example.com", "first_name": "James", "last_name": "Wilson", "phone": "+44 121 123 4567", "address": "45 High Street", "city": "Birmingham", "country": "UK"},
        {"databricks_user_id": "customer_009", "email": "mia.anderson@example.com", "first_name": "Mia", "last_name": "Anderson", "phone": "+46 8 123 456 78", "address": "Drottninggatan 55", "city": "Stockholm", "country": "Sweden"},
        {"databricks_user_id": "customer_010", "email": "noah.vandenberg@example.com", "first_name": "Noah", "last_name": "Van den Berg", "phone": "+31 20 123 4567", "address": "Prinsengracht 263", "city": "Amsterdam", "country": "Netherlands"},
    ]
    for c in customers:
        session.add(BshCustomer(**c))
    session.flush()


def _seed_technicians(session: Session):
    technicians = [
        {"databricks_user_id": "tech_001", "email": "david.clarke@bsh-service.com", "first_name": "David", "last_name": "Clarke", "specialization": "Cooling Systems", "certification_level": "Senior"},
        {"databricks_user_id": "tech_002", "email": "anna.weber@bsh-service.com", "first_name": "Anna", "last_name": "Weber", "specialization": "Cooking Appliances", "certification_level": "Expert"},
        {"databricks_user_id": "tech_003", "email": "carlos.martinez@bsh-service.com", "first_name": "Carlos", "last_name": "Martinez", "specialization": "Dishwashers", "certification_level": "Senior"},
        {"databricks_user_id": "tech_004", "email": "lisa.bergstrom@bsh-service.com", "first_name": "Lisa", "last_name": "Bergstrom", "specialization": "All Appliances", "certification_level": "Master"},
        {"databricks_user_id": "tech_005", "email": "thomas.petit@bsh-service.com", "first_name": "Thomas", "last_name": "Petit", "specialization": "Coffee Machines", "certification_level": "Expert"},
    ]
    for t in technicians:
        session.add(BshTechnician(**t))
    session.flush()


def _seed_customer_devices(session: Session):
    customers = session.exec(select(BshCustomer)).all()
    devices = session.exec(select(BshDevice)).all()

    registrations = [
        (customers[0].id, devices[0].id, "DW2023010001", date(2023, 3, 15), date(2025, 3, 14)),
        (customers[0].id, devices[2].id, "OV2023020015", date(2023, 4, 10), date(2025, 4, 9)),
        (customers[1].id, devices[4].id, "FR2022080032", date(2022, 8, 20), date(2024, 8, 19)),
        (customers[2].id, devices[7].id, "CM2024010005", date(2024, 1, 5), date(2026, 1, 4)),
        (customers[2].id, devices[6].id, "CT2023120098", date(2023, 12, 10), date(2025, 12, 9)),
        (customers[3].id, devices[1].id, "DW2023110045", date(2023, 11, 22), date(2025, 11, 21)),
        (customers[3].id, devices[8].id, "MW2024020012", date(2024, 2, 14), date(2026, 2, 13)),
        (customers[4].id, devices[3].id, "OV2023050078", date(2023, 5, 30), date(2025, 5, 29)),
        (customers[5].id, devices[9].id, "RH2023090021", date(2023, 9, 5), date(2025, 9, 4)),
        (customers[5].id, devices[0].id, "DW2024030067", date(2024, 3, 18), date(2026, 3, 17)),
        (customers[6].id, devices[5].id, "FR2023070055", date(2023, 7, 12), date(2025, 7, 11)),
        (customers[7].id, devices[0].id, "DW2022060091", date(2022, 6, 25), date(2024, 6, 24)),
        (customers[7].id, devices[4].id, "FR2022070044", date(2022, 7, 30), date(2024, 7, 29)),
        (customers[7].id, devices[2].id, "OV2022080033", date(2022, 8, 15), date(2024, 8, 14)),
        (customers[8].id, devices[7].id, "CM2023100087", date(2023, 10, 8), date(2025, 10, 7)),
        (customers[9].id, devices[6].id, "CT2024010103", date(2024, 1, 20), date(2026, 1, 19)),
        (customers[9].id, devices[8].id, "MW2024010111", date(2024, 1, 25), date(2026, 1, 24)),
    ]

    for cid, did, serial, purchase, warranty in registrations:
        session.add(BshCustomerDevice(
            customer_id=cid, device_id=did, serial_number=serial,
            purchase_date=purchase, warranty_expiry_date=warranty,
        ))
