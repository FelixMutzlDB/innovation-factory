# BSH Remote Assist (bsh-home-connect)

## Purpose

AI-powered appliance support platform for Bosch/Siemens kitchen appliances. Enables device registration, support ticket management, knowledge base search, and AI-assisted troubleshooting via chat.

## Architecture Overview

### Backend (`src/innovation_factory/backend/projects/bsh_home_connect/`)

| File | Description |
|------|-------------|
| `models.py` | SQLModel tables (bsh_*) and Pydantic schemas |
| `seed.py` | Seeds devices, knowledge articles, documents, customers, technicians |
| `router.py` | Main FastAPI router |
| `routers/users.py` | Customer and technician profile endpoints |
| `routers/devices.py` | Device catalog and customer device registration |
| `routers/tickets.py` | Ticket CRUD, notes, media upload, shipping label generation |
| `routers/chat.py` | AI chat for ticket support (SSE streaming) |
| `routers/knowledge.py` | Knowledge article search and device documents |
| `services/chat_service.py` | RAG chat with device and knowledge context |

### Frontend (`src/innovation_factory/ui/routes/projects/bsh-home-connect/`)

Pages for device management, ticket workflow, knowledge base, and AI chat interface.

### Data Model

Key tables: `bsh_customers`, `bsh_technicians`, `bsh_devices`, `bsh_customer_devices`, `bsh_tickets`, `bsh_ticket_notes`, `bsh_ticket_media`, `bsh_knowledge_articles`, `bsh_documents`, `bsh_chat_sessions`, `bsh_chat_messages`.

Device categories: washing_machine, dryer, dishwasher, oven, cooktop, refrigerator, coffee_machine.

### API Routes (prefix: `/api/projects/bsh-home-connect/`)

**Users**: GET /customers/me, PUT /customers/me, GET /technicians/me
**Devices**: GET /devices, GET /customers/me/devices, POST /customers/me/devices
**Tickets**: POST /tickets, GET /tickets, GET /tickets/{id}, PATCH /tickets/{id}, POST /tickets/{id}/notes, POST /tickets/{id}/media, POST /tickets/{id}/shipping-label
**Chat**: POST /tickets/{id}/chat, GET /tickets/{id}/chat/history
**Knowledge**: GET /knowledge/search, GET /knowledge/device/{id}, GET /documents/{id}

## Setup Instructions

1. Run `uv run apx dev start` — seed data auto-loads
2. No external Databricks services needed — uses mock chat responses

## Configuration Options

No project-specific environment variables. Uses shared platform config.

## Common Development Tasks

- **Add new device models**: Update `seed.py` with new `BshDevice` entries
- **Extend ticket workflow**: Modify status enum in models.py and add logic in `routers/tickets.py`
- **Add knowledge articles**: Insert into `bsh_knowledge_articles` via seed.py
- **Connect to real LLM**: Replace mock responses in `services/chat_service.py`
