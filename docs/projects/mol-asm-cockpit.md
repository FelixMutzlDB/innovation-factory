# ASM Cockpit (mol-asm-cockpit)

## Purpose

Interactive Area Sales Manager cockpit for retail fuel station networks (MOL Group). Enables station performance monitoring, fuel/non-fuel sales analysis, loyalty tracking, workforce management, competitor pricing, anomaly detection, and AI-powered issue resolution. Designed for the CEE (Central and Eastern Europe) retail fuel market.

## Architecture Overview

### Backend (`src/innovation_factory/backend/projects/mol_asm_cockpit/`)

| File | Description |
|------|-------------|
| `models.py` | SQLModel tables (mac_*) and Pydantic schemas |
| `seed.py` | Seeds regions, stations, daily facts (14 days), anomalies, issues, customer profiles |
| `seed_uc_tables.py` | PySpark script for full-scale Unity Catalog table seeding |
| `databricks_config.py` | Dashboard, MAS, and warehouse IDs from environment |
| `create_dashboard.py` | Script to create AI/BI dashboard via Lakeview API |
| `dashboard_definition.json` | Full dashboard JSON definition |
| `router.py` | Main FastAPI router |
| `routers/stations.py` | Region and station endpoints with KPI aggregation |
| `routers/sales.py` | Fuel, non-fuel, and loyalty metric endpoints |
| `routers/inventory.py` | Inventory, competitor pricing, price history |
| `routers/workforce.py` | Workforce shifts, issues, customer profiles, contracts |
| `routers/anomalies.py` | Anomaly alert CRUD |
| `routers/dashboard.py` | Dashboard embed URL endpoint |
| `routers/chat.py` | MAS chat proxy with message history |
| `ka_docs/issue_resolution/` | 25 knowledge documents for issue resolution KA |
| `ka_docs/customer_relations/` | 15 knowledge documents for customer relations KA |

### Frontend (`src/innovation_factory/ui/routes/projects/mol-asm-cockpit/`)

| File | Description |
|------|-------------|
| `route.tsx` | Layout with sidebar navigation |
| `home.tsx` | Main dashboard with station KPIs and charts |
| `stations/index.tsx` | Station listing with filters |
| `stations/$stationCode.tsx` | Station detail page |
| `explorer.tsx` | Genie space data exploration |
| `agent.tsx` | AI assistant chat interface |
| `anomalies/index.tsx` | Anomaly alert monitoring |

### Data Model

Key tables: `mac_regions`, `mac_stations`, `mac_fuel_sales`, `mac_nonfuel_sales`, `mac_loyalty_metrics`, `mac_workforce_shifts`, `mac_inventory`, `mac_competitor_prices`, `mac_price_history`, `mac_anomaly_alerts`, `mac_issues`, `mac_customer_profiles`, `mac_customer_contracts`, `mac_chat_sessions`, `mac_chat_messages`.

Station types: highway, urban, suburban, rural. Fuel types: diesel, premium_diesel, regular_95, premium_98, lpg.

### API Routes (prefix: `/api/projects/mol-asm-cockpit/`)

**Stations**: GET /stations/regions, GET /stations, GET /stations/kpis, GET /stations/{id}
**Sales**: GET /sales/fuel, GET /sales/nonfuel, GET /sales/loyalty
**Inventory**: GET /inventory, GET /inventory/competitor-prices, GET /inventory/price-history
**Workforce**: GET /workforce/shifts, GET /workforce/issues, GET /workforce/customers, GET /workforce/customers/{id}/contracts
**Anomalies**: GET /anomalies, GET /anomalies/{id}, PATCH /anomalies/{id}
**Dashboard**: GET /dashboard/embed
**Chat**: POST /chat/send, GET /chat/history/{session_id}

## Setup Instructions

1. Run `uv run apx dev start`
2. Configure Databricks resources in `.env` for AI features
3. For full-scale data, run `seed_uc_tables.py` on a Databricks cluster
4. For knowledge assistant, upload `ka_docs/` to a Unity Catalog volume

## Configuration Options

| Variable | Description |
|----------|-------------|
| `MAC_DASHBOARD_ID` | AI/BI Dashboard ID for embedding |
| `MAC_MAS_ENDPOINT_NAME` | Multi-Agent Supervisor endpoint name |
| `WAREHOUSE_ID` | SQL Warehouse ID for dashboard queries (shared) |

## Common Development Tasks

- **Add a new station metric**: Add column to relevant model, update seed.py, add to KPI aggregation in `routers/stations.py`
- **Add knowledge documents**: Add .txt files to `ka_docs/issue_resolution/` or `ka_docs/customer_relations/`, then upload to volume
- **Create/update dashboard**: Edit `dashboard_definition.json`, run `create_dashboard.py`
- **Scale up seed data**: Modify `seed_uc_tables.py` for cluster-based seeding with PySpark
