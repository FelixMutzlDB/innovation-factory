# ViDistrictOne (vi-home-one)

## Purpose

Smart neighborhood energy management system by Viessmann. Manages households with heat pumps, PV panels, batteries, and EVs; supports energy optimization, provider comparison, maintenance alerts, and support tickets with AI chat.

## Architecture Overview

### Backend (`src/innovation_factory/backend/projects/vi_home_one/`)

| File | Description |
|------|-------------|
| `models.py` | SQLModel table definitions (vh_*) and Pydantic I/O schemas |
| `seed.py` | Development seed data for neighborhoods, households, devices, readings |
| `router.py` | Main FastAPI router aggregating all sub-routers |
| `routers/neighborhoods.py` | Neighborhood listing and summary endpoints |
| `routers/households.py` | Household CRUD, cockpit view, optimization mode |
| `routers/energy.py` | Energy readings and current consumption data |
| `routers/optimization.py` | AI-powered optimization suggestions |
| `routers/providers.py` | Energy provider comparison and switching |
| `routers/maintenance.py` | Predictive maintenance alerts |
| `routers/tickets.py` | Support tickets with media upload |
| `routers/chat.py` | AI chat for ticket-based support (SSE streaming) |
| `services/chat_service.py` | RAG-based chat with knowledge base lookup |
| `services/optimization.py` | Energy and cost optimization logic |

### Frontend (`src/innovation_factory/ui/routes/projects/vi-home-one/`)

TanStack Router file-based routing with pages for neighborhood overview, household cockpit, energy monitoring, tickets, and AI chat.

### Data Model

Key tables: `vh_neighborhoods`, `vh_households`, `vh_energy_devices`, `vh_energy_readings`, `vh_consumption_breakdown`, `vh_energy_providers`, `vh_maintenance_alerts`, `vh_tickets`, `vh_ticket_media`, `vh_chat_sessions`, `vh_chat_messages`, `vh_knowledge_articles`.

Devices support types: heat_pump, pv_system, battery, ev, grid_meter.

### API Routes (prefix: `/api/projects/vi-home-one/`)

**Neighborhoods**: GET /neighborhoods, GET /neighborhoods/{id}/summary
**Households**: GET /households/{id}, PUT /households/{id}/optimization-mode, GET /households/{id}/cockpit
**Energy**: GET /energy/households/{id}/readings, GET /energy/households/{id}/current
**Optimization**: GET /optimization/households/{id}/suggestions
**Providers**: GET /providers, GET /providers/compare
**Maintenance**: GET /maintenance/households/{id}/alerts, POST /maintenance/alerts/{id}/acknowledge
**Tickets**: GET /tickets, POST /tickets, GET /tickets/{id}, PATCH /tickets/{id}, POST /tickets/{id}/media
**Chat**: POST /chat/tickets/{id}/chat, GET /chat/tickets/{id}/history

## Setup Instructions

1. Ensure the development server is running: `uv run apx dev start`
2. Seed data is automatically loaded on first startup
3. No external Databricks services required — uses mock RAG responses for demo

## Configuration Options

Uses shared platform configuration (no project-specific env vars). Chat and optimization services run locally with mock data.

## Common Development Tasks

- **Add a new device type**: Add to `VhEnergyDevice.device_type` enum in models.py, update seed.py, and add optimization logic in `services/optimization.py`
- **Modify energy calculations**: Update `services/optimization.py` (suggestions based on optimization mode and readings)
- **Add knowledge articles**: Insert into `vh_knowledge_articles` via seed.py (used by chat RAG)
- **Change chat behavior**: Modify `services/chat_service.py` — currently uses mock responses
