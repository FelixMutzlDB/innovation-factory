# AdTech Intelligence (adtech-intelligence)

## Purpose

AI-powered advertising operations platform for managing online and outdoor (OOH/DOOH) advertising campaigns across Germany. Features demand/inventory exploration, campaign management, rule-based anomaly detection, issue tracking, and AI agents (Multi-Agent Supervisor + Knowledge Assistant) powered by Databricks Agent Bricks.

## Architecture Overview

### Backend (`src/innovation_factory/backend/projects/adtech_intelligence/`)

| File | Description |
|------|-------------|
| `models.py` | SQLModel tables (at_*) and Pydantic schemas |
| `seed.py` | Seeds advertisers, campaigns, inventory, placements, metrics, anomaly rules, anomalies, issues, contracts |
| `router.py` | Main router + `/databricks-resources` endpoint for frontend |
| `databricks_config.py` | Centralized Databricks resource IDs from environment variables |
| `routers/campaigns.py` | Campaign CRUD, placements, dashboard summary |
| `routers/inventory.py` | Ad inventory listing and filtering |
| `routers/anomalies.py` | Anomaly CRUD and anomaly rule management |
| `routers/issues.py` | Issue tracking CRUD |
| `routers/chat.py` | MAS and KA chat endpoints (SSE streaming) |
| `services/chat_service.py` | Databricks serving endpoint integration for MAS and KA |
| `services/anomaly_service.py` | Rule-based anomaly detection engine |

### Frontend (`src/innovation_factory/ui/routes/projects/adtech-intelligence/`)

Pages for dashboard (embedded AI/BI), campaign management, inventory browser, anomaly monitoring, issue resolution, and AI agent chat interfaces.

### Data Model

Key tables: `at_advertisers`, `at_campaigns`, `at_ad_inventory`, `at_placements`, `at_performance_metrics`, `at_anomaly_rules`, `at_anomalies`, `at_issues`, `at_customer_contracts`, `at_chat_sessions`, `at_chat_messages`.

Campaign types: online_display, online_video, ooh_billboard, ooh_transit, dooh_screen. Inventory types: website, app, billboard, transit, digital_screen.

### API Routes (prefix: `/api/projects/adtech-intelligence/`)

**Dashboard**: GET /dashboard/summary
**Campaigns**: GET /campaigns, POST /campaigns, GET /campaigns/{id}, PATCH /campaigns/{id}, GET /campaigns/{id}/placements, POST /campaigns/{id}/placements
**Inventory**: GET /inventory, GET /inventory/{id}
**Anomalies**: GET /anomalies/counts, GET /anomalies, GET /anomalies/{id}, PATCH /anomalies/{id}, GET /anomaly-rules
**Issues**: GET /issues, POST /issues, GET /issues/{id}, PATCH /issues/{id}
**Chat**: POST /chat (MAS), POST /mas-chat, GET /chat/history/{session_id}
**Config**: GET /databricks-resources

## Setup Instructions

1. Run `uv run apx dev start`
2. Configure Databricks resource IDs in `.env` (see Configuration below)
3. For AI features (MAS/KA chat, dashboard embedding), ensure the Databricks resources are deployed and accessible

## Configuration Options

All configured via environment variables (read by `databricks_config.py`):

| Variable | Description |
|----------|-------------|
| `ADTECH_WORKSPACE_URL` | Databricks workspace URL (e.g., `e2-demo-field-eng.cloud.databricks.com`) |
| `UC_CATALOG` | Unity Catalog catalog name (shared) |
| `ADTECH_UC_SCHEMA` | Unity Catalog schema name |
| `ADTECH_DASHBOARD_ID` | AI/BI Dashboard ID for embedding |
| `ADTECH_GENIE_SPACE_ID` | Genie Space ID for data exploration |
| `ADTECH_ISSUE_RESOLUTION_KA_TILE_ID` | Issue Resolution KA tile ID |
| `ADTECH_ISSUE_RESOLUTION_KA_ENDPOINT` | Issue Resolution KA serving endpoint |
| `ADTECH_CUSTOMER_RELATIONS_KA_TILE_ID` | Customer Relations KA tile ID |
| `ADTECH_CUSTOMER_RELATIONS_KA_ENDPOINT` | Customer Relations KA endpoint |
| `ADTECH_MAS_TILE_ID` | Multi-Agent Supervisor tile ID |
| `ADTECH_MAS_ENDPOINT_NAME` | MAS serving endpoint name |
| `WAREHOUSE_ID` | SQL Warehouse ID (shared) |

## Common Development Tasks

- **Add anomaly detection rules**: Insert into `at_anomaly_rules` via seed.py; detection runs in `services/anomaly_service.py`
- **Connect new KA/MAS agents**: Add endpoint name to `databricks_config.py` and `.env`; implement in `services/chat_service.py`
- **Modify dashboard**: Update dashboard via Databricks UI, copy new dashboard ID to env
- **Add new campaign types**: Update `AtCampaignType` enum and seed data
