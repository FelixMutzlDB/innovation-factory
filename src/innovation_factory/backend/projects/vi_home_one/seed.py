"""Seed script for vi-home-one project data."""
import math
import random
from datetime import datetime, date, timedelta
from sqlmodel import Session, select

from .models import (
    VhNeighborhood,
    VhHousehold,
    VhEnergyDevice,
    DeviceType,
    VhEnergyReading,
    VhEnergyProvider,
    VhMaintenanceAlert,
    AlertSeverity,
    VhKnowledgeArticle,
    OptimizationMode,
)


def seed_vh_data(session: Session):
    """Seed all vi-home-one data."""
    # Check if already seeded
    if session.exec(select(VhNeighborhood)).first():
        return

    print("  Seeding vi-home-one data...")
    neighborhood = _seed_neighborhood(session)
    households = _seed_households(session, neighborhood.id)  # type: ignore[invalid-argument-type]
    _seed_energy_devices(session, households)
    _seed_energy_readings(session, households)
    _seed_energy_providers(session)
    _seed_maintenance_alerts(session, households)
    _seed_knowledge_base(session)
    session.commit()
    print("  vi-home-one data seeded.")


def _seed_neighborhood(session: Session) -> VhNeighborhood:
    neighborhood = VhNeighborhood(name="ViDistrictOne", location="Stuttgart, Germany", total_households=5)
    session.add(neighborhood)
    session.flush()
    return neighborhood


def _seed_households(session: Session, neighborhood_id: int) -> list[VhHousehold]:
    households_data = [
        {"owner_name": "Felix", "address": "Musterstr. 1, 70173 Stuttgart", "optimization_mode": OptimizationMode.energy_saver, "has_pv": True, "has_battery": True, "has_ev": True, "has_heat_pump": True},
        {"owner_name": "Frank", "address": "Musterstr. 2, 70173 Stuttgart", "optimization_mode": OptimizationMode.cost_saver, "has_pv": True, "has_battery": True, "has_ev": True, "has_heat_pump": True},
        {"owner_name": "Patrick", "address": "Musterstr. 3, 70173 Stuttgart", "optimization_mode": OptimizationMode.energy_saver, "has_pv": True, "has_battery": True, "has_ev": False, "has_heat_pump": True},
        {"owner_name": "Martin", "address": "Musterstr. 4, 70173 Stuttgart", "optimization_mode": OptimizationMode.cost_saver, "has_pv": False, "has_battery": False, "has_ev": True, "has_heat_pump": True},
        {"owner_name": "Manuel", "address": "Musterstr. 5, 70173 Stuttgart", "optimization_mode": OptimizationMode.energy_saver, "has_pv": True, "has_battery": True, "has_ev": True, "has_heat_pump": True},
    ]
    households = []
    for hh_data in households_data:
        hh = VhHousehold(neighborhood_id=neighborhood_id, **hh_data)
        session.add(hh)
        session.flush()
        households.append(hh)
    return households


def _seed_energy_devices(session: Session, households: list[VhHousehold]):
    devices_config = [
        (0, [(DeviceType.heat_pump, "Viessmann", "Vitocal 250-A", 8.0), (DeviceType.pv_system, "Viessmann", "Vitovolt 300", 10.0), (DeviceType.battery, "Viessmann", "VitoCharge VX3", 10.0), (DeviceType.ev, "Tesla", "Model 3", 60.0), (DeviceType.grid_meter, "Viessmann", "GridBox", None)]),
        (1, [(DeviceType.heat_pump, "Viessmann", "Vitocal 200-S", 10.0), (DeviceType.pv_system, "Viessmann", "Vitovolt 300", 8.0), (DeviceType.battery, "Viessmann", "VitoCharge VX3", 8.0), (DeviceType.ev, "BMW", "iX3", 80.0), (DeviceType.grid_meter, "Viessmann", "GridBox", None)]),
        (2, [(DeviceType.heat_pump, "Viessmann", "Vitocal 250-A", 8.0), (DeviceType.pv_system, "Viessmann", "Vitovolt 300", 12.0), (DeviceType.battery, "Viessmann", "VitoCharge VX3", 15.0), (DeviceType.grid_meter, "Viessmann", "GridBox", None)]),
        (3, [(DeviceType.heat_pump, "Viessmann", "Vitocal 200-S", 10.0), (DeviceType.ev, "VW", "ID.4", 77.0), (DeviceType.grid_meter, "Viessmann", "GridBox", None)]),
        (4, [(DeviceType.heat_pump, "Viessmann", "Vitocal 250-A", 8.0), (DeviceType.pv_system, "Viessmann", "Vitovolt 300", 10.0), (DeviceType.battery, "Viessmann", "VitoCharge VX3", 10.0), (DeviceType.ev, "Audi", "e-tron", 95.0), (DeviceType.grid_meter, "Viessmann", "GridBox", None)]),
    ]
    installation_date = date(2023, 1, 1)
    for idx, devices in devices_config:
        hh = households[idx]
        for dtype, brand, model, capacity in devices:
            device = VhEnergyDevice(
                household_id=hh.id, device_type=dtype, brand=brand, model=model,
                capacity_kw=capacity,
                installation_date=installation_date,
                serial_number=f"{dtype.value.upper()}-2023-{hh.id:03d}",
            )
            session.add(device)
    session.flush()


def _calc_pv(hour: int, day_of_year: int, capacity_kw: float) -> float:
    if hour < 6 or hour >= 20:
        return 0.0
    hours_from_noon = abs(hour - 12)
    daily_curve = math.cos(hours_from_noon * math.pi / 12) ** 2
    seasonal = 0.3 + 0.7 * math.cos((day_of_year - 172) * 2 * math.pi / 365)
    cloud = 0.6 + 0.4 * random.random()
    return max(0, capacity_kw * daily_curve * seasonal * cloud)


def _calc_hp(hour: int, day_of_year: int, capacity_kw: float) -> float:
    seasonal = 0.8 + 0.4 * math.cos((day_of_year - 172) * 2 * math.pi / 365)
    if 6 <= hour < 9 or 18 <= hour < 23:
        time_factor = 1.2
    elif 0 <= hour < 6:
        time_factor = 0.8
    else:
        time_factor = 1.0
    return 0.5 + capacity_kw * 0.3 * seasonal * time_factor


def _calc_household(hour: int, base_load: float) -> float:
    if 7 <= hour < 9:
        peak = 2.0
    elif 18 <= hour < 22:
        peak = 2.5
    elif 0 <= hour < 6:
        peak = 0.5
    else:
        peak = 1.0
    return base_load * peak * (0.8 + 0.4 * random.random())


def _calc_ev(hour: int, has_ev: bool) -> float:
    if not has_ev:
        return 0.0
    if 18 <= hour or hour < 6:
        if random.random() < 0.3:
            return random.uniform(3.0, 7.0)
    return 0.0


def _seed_energy_readings(session: Session, households: list[VhHousehold]):
    start_date = datetime.now() - timedelta(days=1)
    configs = [
        {"base_load": 0.5, "mult": 1.0},
        {"base_load": 0.6, "mult": 1.5},
        {"base_load": 0.5, "mult": 1.0},
        {"base_load": 0.5, "mult": 1.0},
        {"base_load": 0.5, "mult": 1.0},
    ]
    count = 0
    for idx, household in enumerate(households):
        cfg = configs[idx]
        devices = session.exec(select(VhEnergyDevice).where(VhEnergyDevice.household_id == household.id)).all()
        device_dict = {d.device_type: d for d in devices}
        pv_cap = device_dict[DeviceType.pv_system].capacity_kw if DeviceType.pv_system in device_dict else 0
        bat_cap = device_dict[DeviceType.battery].capacity_kw if DeviceType.battery in device_dict else 0
        hp_cap = device_dict[DeviceType.heat_pump].capacity_kw if DeviceType.heat_pump in device_dict else 0
        bat_level = bat_cap * 0.5  # type: ignore[unsupported-operator]

        for hour_offset in range(24):
            ts = start_date + timedelta(hours=hour_offset)
            hour = ts.hour
            doy = ts.timetuple().tm_yday

            pv_gen = _calc_pv(hour, doy, pv_cap) if household.has_pv else 0.0  # type: ignore[invalid-argument-type]
            hp_cons = _calc_hp(hour, doy, hp_cap)  # type: ignore[invalid-argument-type]
            hh_cons = _calc_household(hour, cfg["base_load"]) * cfg["mult"]
            ev_cons = _calc_ev(hour, household.has_ev)
            total_cons = hp_cons + hh_cons + ev_cons

            bat_charge = bat_discharge = grid_import = grid_export = 0.0
            if household.has_battery:
                if pv_gen > total_cons:
                    surplus = pv_gen - total_cons
                    can_charge = min(surplus, bat_cap - bat_level, bat_cap * 0.2)  # type: ignore[unsupported-operator]
                    bat_charge = can_charge
                    bat_level += bat_charge
                    grid_export = surplus - bat_charge
                else:
                    deficit = total_cons - pv_gen
                    can_discharge = min(deficit, bat_level, bat_cap * 0.2)  # type: ignore[unsupported-operator]
                    bat_discharge = can_discharge
                    bat_level -= bat_discharge
                    grid_import = deficit - bat_discharge
            else:
                if pv_gen > total_cons:
                    grid_export = pv_gen - total_cons
                else:
                    grid_import = total_cons - pv_gen

            session.add(VhEnergyReading(
                household_id=household.id, timestamp=ts,
                pv_generation_kwh=round(pv_gen, 3), battery_charge_kwh=round(bat_charge, 3),
                battery_discharge_kwh=round(bat_discharge, 3), battery_level_kwh=round(bat_level, 3),
                grid_import_kwh=round(grid_import, 3), grid_export_kwh=round(grid_export, 3),
                ev_consumption_kwh=round(ev_cons, 3), heat_pump_consumption_kwh=round(hp_cons, 3),
                household_consumption_kwh=round(hh_cons, 3), total_consumption_kwh=round(total_cons, 3),
            ))
            count += 1
    print(f"    Seeded {count} energy readings")


def _seed_energy_providers(session: Session):
    providers = [
        {"name": "E.ON", "base_rate_eur": 12.50, "kwh_rate_eur": 0.32, "night_rate_eur": 0.24, "feed_in_rate_eur": 0.082},
        {"name": "Vattenfall", "base_rate_eur": 11.80, "kwh_rate_eur": 0.31, "night_rate_eur": 0.23, "feed_in_rate_eur": 0.085},
        {"name": "EnBW", "base_rate_eur": 13.20, "kwh_rate_eur": 0.33, "night_rate_eur": 0.25, "feed_in_rate_eur": 0.080},
        {"name": "RWE", "base_rate_eur": 12.00, "kwh_rate_eur": 0.30, "night_rate_eur": 0.22, "feed_in_rate_eur": 0.083},
    ]
    for p in providers:
        session.add(VhEnergyProvider(**p))


def _seed_maintenance_alerts(session: Session, households: list[VhHousehold]):
    for hh in households[:3]:
        devices = session.exec(select(VhEnergyDevice).where(
            VhEnergyDevice.household_id == hh.id,
            VhEnergyDevice.device_type.in_([DeviceType.heat_pump, DeviceType.pv_system])  # type: ignore[unresolved-attribute]
        )).all()
        for device in devices:
            if device.device_type == DeviceType.heat_pump:
                session.add(VhMaintenanceAlert(
                    device_id=device.id, alert_type="filter_cleaning",
                    severity=AlertSeverity.medium,
                    message="Heat pump filter requires cleaning.",
                    predicted_date=date.today() + timedelta(days=14),
                ))
            elif device.device_type == DeviceType.pv_system:
                session.add(VhMaintenanceAlert(
                    device_id=device.id, alert_type="panel_cleaning",
                    severity=AlertSeverity.low,
                    message="PV panels show 5% efficiency drop. Cleaning recommended.",
                    predicted_date=date.today() + timedelta(days=30),
                ))


def _seed_knowledge_base(session: Session):
    articles = [
        {"device_type": DeviceType.heat_pump, "title": "Heat Pump Efficiency Drop - Common Causes", "content": "Check filters, refrigerant levels, outdoor unit clearance.", "category": "troubleshooting", "tags": "efficiency,filter"},
        {"device_type": DeviceType.pv_system, "title": "Solar Panel Output Reduced - Troubleshooting Guide", "content": "Check for dirt, shading, inverter status.", "category": "troubleshooting", "tags": "solar,cleaning"},
        {"device_type": DeviceType.battery, "title": "Battery Not Charging - Diagnosis Steps", "content": "Check BMS, temperature, charge settings.", "category": "troubleshooting", "tags": "battery,charging"},
        {"device_type": DeviceType.ev, "title": "EV Charging Optimization - Smart Charging Tips", "content": "Night tariff, PV priority, load balancing.", "category": "optimization", "tags": "ev,charging"},
        {"device_type": None, "title": "Optimization Modes Explained", "content": "Energy Saver vs Cost Saver mode.", "category": "optimization", "tags": "modes,optimization"},
    ]
    for a in articles:
        session.add(VhKnowledgeArticle(**a))
