# Building Automation Integration — Technical Notes

## Scope

This document covers how building-automation system (BAS) data flows
into the AECO Hub digital twin: the supported protocols, the sensor
naming conventions, the data-modeling contracts between the BAS
gateway and the `dt_sensor_devices` / `dt_sensor_readings` tables, and
the operational expectations once a project is in the operate phase.

The Schuster Bau AG portfolio standardizes on KNX + BACnet for new
construction and exposes both via a building-level BAS gateway that
publishes to the AECO Hub via Databricks Lakeflow Connect (or the
`Zerobus` direct-write API for high-volume sites such as
`LOG-A9`).

## Supported protocols and adapters

| Protocol | Adapter | Typical use |
|----------|---------|-------------|
| BACnet/IP | Native gateway → MQTT bridge | HVAC controls, energy meters |
| KNX | KNX/IP router → MQTT bridge | Lighting, blinds, room sensors |
| Modbus TCP | Modbus → MQTT bridge | Energy meters, chillers |
| OPC UA | Direct ingestion | Industrial / warehouse projects |
| LoRaWAN | Network-server → HTTPS push | Battery-powered occupancy / leak sensors |

All adapters normalize to a common JSON envelope before reaching the
AECO Hub:

```json
{
  "sensor_code": "S-007-0142",
  "sensor_type": "zone_temp",
  "project_code": "LOG-A9",
  "building_id": 7,
  "space_id": 421,
  "reading_ts": "2026-04-20T14:32:00Z",
  "value": 21.4,
  "unit": "C"
}
```

This shape matches the `dt_sensor_readings` UC table 1:1.

## Sensor naming convention

The `sensor_code` is the primary key for sensor devices and must
remain stable for the life of the device. Schuster Bau AG's convention:

```
S-{building_id:03d}-{sequence:04d}
```

For example, the 142nd sensor installed in building 7 (`LOG-A9 Hall`)
gets `S-007-0142`. The sequence is assigned when the device is
commissioned and never recycled — even if the device is removed,
the sequence is retired to prevent silent data continuity errors when
a future device is installed in the same location.

## Sensor types

The AECO Hub recognizes the following `sensor_type` values (matching
the `AecoSensorType` enum):

| sensor_type | Unit | Typical range | Sample frequency |
|-------------|------|---------------|------------------|
| zone_temp | C | 18 – 28 | 5 min |
| supply_air_temp | C | 12 – 22 | 5 min |
| relative_humidity | %RH | 30 – 70 | 15 min |
| co2_concentration | ppm | 400 – 1500 | 15 min |
| people_count | count | 0 – 50 | 5 min |
| active_power | kW | 0 – 500 | 15 min |
| dimming_level | % | 0 – 100 | 15 min |
| damper_position | % | 0 – 100 | 15 min |
| access_event | event | n/a | event-driven |

Sensor types outside this list are accepted (the `value` field is
DOUBLE so any numeric reading is allowed) but require the FM team to
extend the AECO Hub enum before they appear in dashboards or Genie
queries.

## Data flow

```
BAS device (KNX / BACnet / Modbus / OPC UA / LoRaWAN)
    ↓ vendor protocol
BAS gateway (per building, on-site)
    ↓ MQTT (or HTTPS push for LoRaWAN)
Building-level integration broker
    ↓ Lakeflow Connect / Zerobus
Databricks Lakehouse (innovation_factory_catalog.aeco_hub.dt_sensor_readings)
    ↓ pre-aggregation pipeline
dt_energy_consumption (daily) / dt_space_utilization (daily)
    ↓ Genie / Lakeview / app
AECO Hub UI + Genie + Energy & Sustainability dashboard
```

The pre-aggregation pipeline is a Lakeflow Spark Declarative Pipeline
that materializes daily sums (energy) and daily averages (utilization)
so the FM dashboard never has to scan the raw readings table directly.

## Operational expectations

For an operating project, the AECO Hub considers a sensor "healthy"
when:

- It has reported within the last 4× its expected sample frequency
  (i.e. a 5-minute sensor must report at least every 20 minutes).
- Its values are within the expected range for its `sensor_type`.
  Out-of-range values are not rejected (could be a real anomaly) but
  are flagged in the operations dashboard.
- Its `last_seen_at` field on `dt_sensor_devices` is current.

A sensor that goes offline (no readings for > 4× the expected
interval) generates a maintenance order with priority `medium`. A
sensor reporting out-of-range values for > 30 minutes generates a
maintenance order with priority `high` and a `dt_issues` row with
`category='safety'` if the sensor type is fire-/safety-related.

## ABB integration (legacy)

For the QSP-2024 development and other operating projects with an
ABB AC500 controller backbone, the AECO Hub uses the
ABB-Ability-Building-Analyzer adapter, which polls the AC500
controllers via Modbus TCP and publishes to the project's MQTT
broker. The adapter is configured per controller; sensor inventory
must match between the ABB engineering tool and the AECO Hub
`dt_sensor_devices` registry — a mismatch produces orphaned readings
that are quarantined until reconciled.

When commissioning a new ABB-fronted building:

1. Export the sensor inventory from the ABB engineering tool as
   CSV.
2. Stage the CSV in the AECO Hub's bootstrap volume.
3. Run the AECO Hub commissioning script to create
   `dt_sensor_devices` rows with `sensor_code` derived from the
   ABB device tag.
4. Verify that the first 24 hours of readings flow into
   `dt_sensor_readings` and that the daily aggregate appears in
   `dt_energy_consumption`.

## Common integration issues

- **Time-zone drift.** BAS gateways often default to local time; the
  AECO Hub stores all `reading_ts` in UTC. The adapter must perform
  the conversion. Symptoms: readings appear shifted by 1–2 hours
  when daylight-saving boundaries are crossed.
- **Sensor address recycling.** A retired sensor's `sensor_code` is
  re-used for a new device in a different location. Symptom:
  occupancy readings on the energy dashboard look implausible
  because the underlying space changed without warning.
- **Missing unit normalization.** Some BACnet integrations report
  energy in Joules rather than kWh. The adapter must convert; if
  it doesn't, energy readings come in 3 600 000× too large.
- **Aggregation drift.** The pre-aggregation pipeline lags behind
  the real-time stream by 5–10 minutes. The Operations Intelligence
  Genie space queries the aggregates, so sub-10-minute questions
  may return stale numbers.

## Future extensions

Items not covered in v1 of the AECO Hub:

- Automatic sensor inventory reconciliation (today, manual via the
  commissioning script).
- Real-time anomaly detection on sensor streams (today, threshold-based
  in the pre-aggregation pipeline).
- Predictive maintenance from sensor patterns (planned for a later
  Lakeflow pipeline).
- Sensor-level access control (today, project-level).
