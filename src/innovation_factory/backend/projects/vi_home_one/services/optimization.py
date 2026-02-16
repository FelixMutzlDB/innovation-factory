"""Optimization service for generating energy and cost saving suggestions."""
from datetime import datetime, timedelta
from sqlmodel import Session, select

from ..models import (
    VhHousehold,
    VhEnergyReading,
    VhEnergyDevice,
    DeviceType,
    OptimizationMode,
    VhOptimizationSuggestionOut,
)


def generate_optimization_suggestions(
    household: VhHousehold, session: Session,
) -> list[VhOptimizationSuggestionOut]:
    """Generate optimization suggestions based on household mode and energy data."""
    suggestions = []

    one_day_ago = datetime.utcnow() - timedelta(hours=24)
    readings_query = select(VhEnergyReading).where(
        VhEnergyReading.household_id == household.id,
        VhEnergyReading.timestamp >= one_day_ago
    ).order_by(VhEnergyReading.timestamp.desc())  # type: ignore[unresolved-attribute]
    readings = session.exec(readings_query).all()

    if not readings:
        return suggestions

    devices_query = select(VhEnergyDevice).where(VhEnergyDevice.household_id == household.id)
    devices = session.exec(devices_query).all()
    device_dict = {d.device_type: d for d in devices}

    total_consumption = sum(r.total_consumption_kwh for r in readings)
    total_grid_export = sum(r.grid_export_kwh for r in readings)
    avg_consumption = total_consumption / len(readings) if readings else 0

    if household.optimization_mode == OptimizationMode.energy_saver:
        high_consumption_hours = [r for r in readings if r.total_consumption_kwh > avg_consumption * 1.5]
        if high_consumption_hours:
            suggestions.append(VhOptimizationSuggestionOut(
                id="energy-saver-1", category="consumption",
                title="High Energy Consumption Detected",
                description=f"Detected {len(high_consumption_hours)} hours with consumption 50% above average.",
                potential_savings_kwh=round(len(high_consumption_hours) * 0.5, 2),
                potential_savings_eur=round(len(high_consumption_hours) * 0.5 * 0.32, 2),
            ))

        if DeviceType.heat_pump in device_dict:
            avg_hp = sum(r.heat_pump_consumption_kwh for r in readings) / len(readings)
            if avg_hp > 2.0:
                suggestions.append(VhOptimizationSuggestionOut(
                    id="energy-saver-2", category="climate",
                    title="Optimize Heat Pump Settings",
                    description="Heat pump consumption is higher than optimal. Consider lowering target temperature by 1C.",
                    potential_savings_kwh=round(total_consumption * 0.06, 2),
                    potential_savings_eur=round(total_consumption * 0.06 * 0.32, 2),
                ))

        if total_grid_export > 5.0:
            suggestions.append(VhOptimizationSuggestionOut(
                id="energy-saver-3", category="solar",
                title="Unused Solar Energy",
                description=f"You exported {round(total_grid_export, 1)} kWh to the grid in the last 24h.",
                potential_savings_kwh=round(total_grid_export * 0.5, 2),
                potential_savings_eur=round(total_grid_export * 0.5 * (0.32 - 0.082), 2),
            ))

        night_readings = [r for r in readings if 0 <= r.timestamp.hour < 6]
        if night_readings:
            avg_night = sum(r.household_consumption_kwh for r in night_readings) / len(night_readings)
            if avg_night > 0.3:
                suggestions.append(VhOptimizationSuggestionOut(
                    id="energy-saver-4", category="standby",
                    title="Reduce Standby Consumption",
                    description=f"Average nighttime consumption is {round(avg_night * 1000, 0)}W.",
                    potential_savings_kwh=round(avg_night * 0.4 * 365, 2),
                    potential_savings_eur=round(avg_night * 0.4 * 365 * 0.32, 2),
                ))

    else:  # Cost Saver Mode
        expensive_hour_readings = [r for r in readings if 6 <= r.timestamp.hour < 22]
        expensive_grid_import = sum(r.grid_import_kwh for r in expensive_hour_readings)

        if expensive_grid_import > 10.0:
            savings = expensive_grid_import * 0.3 * (0.32 - 0.24)
            suggestions.append(VhOptimizationSuggestionOut(
                id="cost-saver-1", category="tariff",
                title="Shift Load to Night Tariff",
                description=f"You consumed {round(expensive_grid_import, 1)} kWh from the grid during expensive hours.",
                potential_savings_kwh=None, potential_savings_eur=round(savings, 2),
            ))

        if household.has_ev:
            ev_charging_readings = [r for r in readings if r.ev_consumption_kwh > 0]
            day_charging = [r for r in ev_charging_readings if 6 <= r.timestamp.hour < 22]
            if day_charging:
                total_day_charging = sum(r.ev_consumption_kwh for r in day_charging)
                savings = total_day_charging * (0.32 - 0.24)
                suggestions.append(VhOptimizationSuggestionOut(
                    id="cost-saver-2", category="ev",
                    title="Optimize EV Charging Schedule",
                    description=f"You charged your EV {round(total_day_charging, 1)} kWh during expensive day hours.",
                    potential_savings_kwh=None, potential_savings_eur=round(savings, 2),
                ))

        if household.has_battery:
            peak_hours = [r for r in readings if 18 <= r.timestamp.hour < 21]
            if peak_hours:
                avg_battery_discharge = sum(r.battery_discharge_kwh for r in peak_hours) / len(peak_hours)
                if avg_battery_discharge < 0.5:
                    suggestions.append(VhOptimizationSuggestionOut(
                        id="cost-saver-3", category="battery",
                        title="Optimize Battery Discharge",
                        description="Your battery is not discharging enough during evening peak hours (18-21).",
                        potential_savings_kwh=None, potential_savings_eur=round(3 * 0.5 * (0.32 - 0.08), 2),
                    ))

        if household.has_pv and total_grid_export > 5.0:
            savings = total_grid_export * 0.3 * (0.32 - 0.082)
            suggestions.append(VhOptimizationSuggestionOut(
                id="cost-saver-4", category="solar",
                title="Increase Solar Self-Consumption",
                description=f"You're exporting {round(total_grid_export, 1)} kWh to grid at low rates.",
                potential_savings_kwh=None, potential_savings_eur=round(savings, 2),
            ))

    return suggestions
