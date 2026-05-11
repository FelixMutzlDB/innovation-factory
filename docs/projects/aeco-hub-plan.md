# AECO Hub — Project Plan

> Innovation Factory accelerator for the AECO (Architecture, Engineering, Construction, Operations) industry.
> Built on the Databricks Lakehouse + Lakebase.
>
> **Customer inspiration (obfuscated CI):** Nemetschek Group — apply brand-adjacent colors, typography, and imagery without using protected marks. The multi-vendor AECO tooling ecosystem (Allplan, Archicad, Bluebeam, Solibri, Vectorworks, etc.) maps to the Nemetschek portfolio.

---

## 1. Vision

A **building lifecycle digital twin platform** that acts as the system of record for
construction projects — from architectural design through construction, operations,
and eventual demolition. The AECO Hub demonstrates how a multi-vendor AECO tooling
ecosystem can feed a unified digital twin powered by Databricks.

**Key value proposition:** Replace siloed project data with a single, living digital
twin that connects BIM geometry, construction progress, IoT sensor feeds, and
facility management — all on the Databricks Lakehouse.

---

## 2. AECO Tooling Ecosystem

The UI showcases the AECO tooling ecosystem as integration touchpoints within the
digital twin. Each tool is represented as a logo tile that contextually links to the
relevant lifecycle phase.

### Tool → Lifecycle Mapping

| Phase | Tools | Data Flow Into Twin |
|-------|-------|---------------------|
| **Design** | Allplan, Archicad, Vectorworks | IFC models, floor plans, 3D geometry |
| **QA/QC** | Solibri | Clash detection reports, rule validation results |
| **Requirements** | dRofus | Room data sheets, equipment specifications |
| **Build** | Bluebeam, NEVARIS, GoCanvas, 123erfasst | Markups, cost estimates, site reports, progress |
| **Operate** | Spacewell, Crem Solutions, dTwin | IoT data, space utilization, lease management |
| **Visualize** | Cinema 4D | Renderings, walkthroughs, marketing assets |

### UI Concept: Tool Navigator

A horizontal tool bar with logo buttons. Clicking a tool opens a drawer showing:
- What data this tool contributes to the twin
- Current integration status (connected / simulated / planned)
- Sample data from the tool for the active project

> Tool names are referenced as third-party trademarks of their respective owners. The
> AECO Hub UI uses these as integration placeholders for demo purposes only — text
> labels are the default; logo assets ship only after internal review.

---

## 3. Data Model

### Naming Convention

All tables use the `dt_` prefix (digital twin), following the Innovation Factory
convention.

### Enum Prefixing

To avoid OpenAPI schema collisions with other accelerators, **all project enums use
the `Aeco` prefix** (e.g. `AecoProjectPhase`, `AecoIssueSeverity`, `AecoIssueStatus`,
`AecoSensorType`, `AecoMaintenancePriority`).

### UC Schema

`innovation_factory_catalog.aeco_hub`

### Lakebase Tables (PostgreSQL)

#### Core Entities

```
dt_projects              — Construction projects (the top-level entity)
dt_buildings             — Buildings within a project (a project may have multiple)
dt_floors                — Floors/levels within a building
dt_spaces                — Rooms/zones within a floor
dt_assets                — Equipment and systems installed in spaces
dt_project_members       — People and organizations involved in a project
```

#### Lifecycle Tracking

```
dt_project_phases        — Phase history (design → build → operate → demolish)
dt_milestones            — Key dates and deliverables per phase
dt_documents             — BIM files, reports, permits, COBie handovers
dt_issues                — Cross-discipline issues (clashes, RFIs, defects)
```

#### Design Phase

```
dt_bim_models            — IFC model metadata (version, discipline, LOD, file ref)
dt_model_elements        — Key elements extracted from BIM (walls, doors, systems)
dt_clash_reports         — Clash detection / QA-QC results
dt_room_requirements     — Room data sheets / equipment requirements
```

#### Build Phase

```
dt_cost_items            — Bill of quantities / cost breakdown
dt_schedule_activities   — Construction schedule tasks with progress
dt_site_reports          — Daily logs, inspections, safety observations
dt_change_orders         — Design changes and their cost/schedule impact
```

#### Operate Phase

```
dt_sensor_readings       — IoT time-series data (temp, humidity, CO2, energy)
dt_sensor_devices        — Sensor/actuator registry with metadata
dt_maintenance_orders    — Work orders for preventive/reactive maintenance
dt_energy_consumption    — Aggregated energy data (hourly/daily per meter)
dt_space_utilization     — Occupancy and desk booking analytics
dt_lease_contracts       — Tenant/lease information (FM domain)
```

#### Marketplace

```
dt_marketplace_partners  — Partner companies offering solutions
dt_marketplace_apps      — Apps/integrations available in the marketplace
dt_partner_integrations  — Which apps are active on which projects
```

#### Relationships (Graph View)

```
dt_relationships         — Generic edge table: source_type, source_id, target_type, target_id, relationship_type
```

Relationship types: `contains`, `feeds_data_to`, `depends_on`, `maintained_by`,
`designed_by`, `supplied_by`, `monitors`, `controls`

### UC Tables (for Genie / Dashboard analytics)

Mirror the key Lakebase tables into UC for SQL analytics:
- `dt_projects`, `dt_buildings`, `dt_sensor_readings`, `dt_energy_consumption`,
  `dt_cost_items`, `dt_schedule_activities`, `dt_issues`

---

## 4. Sample Data Specification

### Example Customer: "Schuster Bau AG"

A fictional mid-size German general contractor managing a portfolio of 5 projects.

### Projects

| # | Name | Type | Phase | City | Status |
|---|------|------|-------|------|--------|
| 1 | Quartier am Stadtpark | Mixed-use (residential + retail) | **Operating** | Munich | 3 buildings, 180 units, fully occupied |
| 2 | TechHub Campus Garching | Office campus | **Constructing** | Garching | 2 buildings, 65% complete |
| 3 | Klinikum Erweiterung Süd | Hospital extension | **Design** | Stuttgart | Schematic design, BIM LOD 300 |
| 4 | Logistikzentrum A9 | Industrial warehouse | **Operating** | Ingolstadt | Single building, heavy IoT |
| 5 | Altbau Maximilianstraße | Heritage renovation | **Demolition/Reno** | Munich | Partial demolition + renovation |

### Data Volume per Project

| Data Type | Operating Project | Constructing | Design | Reno/Demo |
|-----------|-------------------|--------------|--------|-----------|
| Buildings | 3 | 2 | 1 | 1 |
| Floors | 15 | 10 | 5 | 4 |
| Spaces/Rooms | 200 | 80 | 40 | 30 |
| Assets | 500 | 100 | 0 | 50 |
| Sensors | 300 | 20 | 0 | 10 |
| Sensor readings | ~500K (1 year) | ~10K (recent) | 0 | ~5K |
| BIM elements | 2000 | 1500 | 800 | 600 |
| Cost items | 150 | 200 | 50 | 80 |
| Schedule activities | 80 | 120 | 20 | 40 |
| Site reports | 200 | 150 | 0 | 30 |
| Issues | 30 | 50 | 15 | 20 |
| Documents | 40 | 60 | 20 | 15 |

**Total Lakebase rows:** ~15K (excluding sensor readings)
**Total UC rows (sensor_readings):** ~515K (via PySpark seeding)

### IoT Simulation (Building Automation)

For operating projects, simulate building-automation-style IoT signals:

| Sensor Type | Signal | Unit | Range | Frequency |
|-------------|--------|------|-------|-----------|
| Room temperature | zone_temp | C | 18-28 | 5 min |
| Supply air temp | supply_air_temp | C | 12-22 | 5 min |
| Humidity | relative_humidity | %RH | 30-70 | 15 min |
| CO2 | co2_concentration | ppm | 400-1500 | 15 min |
| Occupancy | people_count | count | 0-50 | 5 min |
| Energy meter | active_power | kW | 0-500 | 15 min |
| Lighting | dimming_level | % | 0-100 | 15 min |
| HVAC damper | damper_position | % | 0-100 | 15 min |
| Door access | access_event | event | - | event-driven |

---

## 5. Frontend Design

### Navigation Structure

```
/projects/aeco-hub/
├── home                    — Portfolio overview: project cards with phase badges
├── projects/$projectId/
│   ├── overview            — Project dashboard: KPIs, timeline, phase indicator
│   ├── twin                — Twin view: building → floor → room drilldown (tree + graph)
│   ├── design              — BIM models, clash reports, room requirements
│   ├── build               — Schedule, cost tracking, site reports, change orders
│   ├── operate             — Live IoT dashboard, energy, maintenance, space utilization
│   ├── documents           — Document library with lifecycle phase filter
│   └── issues              — Cross-discipline issue tracker
├── relationships           — Graph visualization of project entity relationships
├── marketplace             — Partner ecosystem browser
├── tools                   — AECO tool navigator
└── agent                   — AI chat agent (MAS with Genie + KA)
```

### UI Style Concept

- **Dark sidebar** with construction-amber accent (`#F59E0B`)
- **Card-based layouts** for project portfolio (consistent with the existing Innovation Factory gallery)
- **Phase timeline** as a horizontal stepper with colored segments (Design=blue, Build=orange, Operate=green, Demo=red)
- **Building drilldown**: Site → Building → Floor → Room (breadcrumb navigation)
- **IoT dashboards** using Recharts (already in the project) for live-looking sensor data
- **Graph view** using a force-directed layout (`react-force-graph-2d`) for relationship exploration
- **Tool bar**: Horizontal strip of AECO tool logos (or text labels) as pill buttons

### Key UI Components

| Component | Library | Purpose |
|-----------|---------|---------|
| Project cards | shadcn Card | Portfolio overview |
| Phase stepper | Custom (Tailwind) | Lifecycle phase indicator |
| Building tree | shadcn Accordion + Tree | Spatial hierarchy drilldown |
| IoT charts | Recharts (existing) | Sensor data line/area charts |
| Graph view | react-force-graph-2d | Entity relationship visualization |
| Data tables | shadcn Table | Issues, documents, cost items |
| Tool navigator | Custom (logos + Drawer) | AECO ecosystem showcase |
| Dashboard embed | iframe | AI/BI dashboard for energy analytics |

---

## 6. Backend Architecture

### Router Structure

```
src/innovation_factory/backend/projects/aeco_hub/
├── __init__.py
├── databricks_config.py         — Resource IDs (Genie, Dashboard, MAS)
├── models.py                    — SQLModel entities (dt_* tables, Aeco-prefixed enums)
├── router.py                    — Aggregates all sub-routers
├── seed.py                      — PGlite-safe seed (~1K rows, no sensor data)
├── seed_uc_tables.py            — PySpark seed for sensor readings (~500K rows)
├── routers/
│   ├── projects.py              — CRUD for dt_projects, dt_buildings, dt_floors, dt_spaces
│   ├── design.py                — BIM models, clash reports, room requirements
│   ├── build.py                 — Cost items, schedule, site reports, change orders
│   ├── operate.py               — Sensor readings, energy, maintenance, space utilization
│   ├── documents.py             — Document management with phase filtering
│   ├── issues.py                — Issue tracker
│   ├── marketplace.py           — Partner ecosystem
│   ├── relationships.py         — Graph data API (paginated, capped)
│   ├── tools.py                 — AECO tool metadata
│   └── chat.py                  — MAS agent endpoint
└── services/
    ├── chat_service.py          — MAS streaming (reuse platform streaming utility)
    └── iot_service.py           — Sensor data aggregation helpers
```

### API Endpoints (Key)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/projects` | List all construction projects with phase/status |
| GET | `/projects/{id}` | Project detail with KPIs |
| GET | `/projects/{id}/buildings` | Buildings in a project |
| GET | `/projects/{id}/buildings/{bid}/floors` | Floors in a building |
| GET | `/projects/{id}/twin` | Full spatial hierarchy for twin view |
| GET | `/projects/{id}/design/models` | BIM model metadata |
| GET | `/projects/{id}/design/clashes` | Clash detection results |
| GET | `/projects/{id}/build/schedule` | Schedule activities with progress |
| GET | `/projects/{id}/build/costs` | Cost breakdown |
| GET | `/projects/{id}/operate/sensors` | Sensor devices and latest readings |
| GET | `/projects/{id}/operate/energy` | Energy consumption aggregates |
| GET | `/projects/{id}/operate/maintenance` | Maintenance work orders |
| GET | `/projects/{id}/issues` | Issues with status/severity filter |
| GET | `/projects/{id}/documents` | Documents with phase filter |
| GET | `/relationships` | Graph edges for visualization (paginated, capped) |
| GET | `/marketplace` | Partner apps |
| GET | `/tools` | AECO tool metadata |
| POST | `/chat/sessions` | Create chat session |
| POST | `/chat/sessions/{id}/messages` | Stream MAS response |

All routes specify `response_model` and `operation_id` for TypeScript client generation.

---

## 7. Databricks Resources

Created via the `bootstrap.py` orchestrator pattern (D4) and existing `scripts/`
helpers — no ad-hoc resource creation.

### Genie Spaces (2)

1. **AECO Project Analytics** (`aeco_hub_project_analytics_genie`)
   Tables: dt_projects, dt_buildings, dt_cost_items, dt_schedule_activities, dt_issues
   - "What is the total cost of TechHub Campus?"
   - "Show projects behind schedule"
   - "Compare cost overruns across projects"

2. **AECO Operations Intelligence** (`aeco_hub_operations_intelligence_genie`)
   Tables: dt_sensor_readings, dt_energy_consumption, dt_maintenance_orders, dt_space_utilization
   - "What is the average energy consumption per floor?"
   - "Show rooms with CO2 above 1000 ppm"
   - "List overdue maintenance orders"

### AI/BI Dashboard (1)

**AECO Energy & Sustainability Dashboard** — embedded in the Operate view
- Energy consumption trends (line chart, hourly/daily)
- Carbon footprint estimates
- Space utilization heatmap
- Maintenance KPIs (MTTR, backlog, completion rate)

### Knowledge Assistant (1)

**AECO Standards & Compliance KA** (`aeco_hub_standards_compliance_ka`)
Volume: `aeco_hub/compliance_docs`
Synthetic source documents (generated in Phase 4):
- IFC standards primer (~3 pages)
- COBie handover requirements (~4 pages)
- Building regulations summary (German example, ~5 pages)
- Building automation integration technical notes (~4 pages)

### Multi-Agent Supervisor (1)

**AECO Hub Supervisor** (`aeco_hub_supervisor`) — Orchestrates:
- Genie: `aeco_hub_project_analytics_genie` (data questions)
- Genie: `aeco_hub_operations_intelligence_genie` (IoT/energy questions)
- KA: `aeco_hub_standards_compliance_ka` (regulatory/standards questions)

> Naming follows the D3 convention: snake_case sub-agent names; `_supervisor` suffix
> on the supervisor.

---

## 8. Lakebase Branch Strategy

Create a **development branch** from production for isolated development:

```bash
databricks postgres create-branch projects/innovation-factory dev-aeco-hub \
  --json '{"spec": {"source_branch": "projects/innovation-factory/branches/production", "no_expiry": true}}' \
  -p fevm-felix-demo
```

Development workflow:
1. All schema changes and seed data go to the `dev-aeco-hub` branch
2. App dev server connects to this branch via `DATABASE_URL` override
3. Once stable, merge to production by updating `app.yml` env vars
4. Delete the dev branch after merge

---

## 9. Implementation Phases

### Phase 1: Foundation (3-4 days)

- [ ] Create git branch `feature/aeco-hub`
- [ ] Define all SQLModel entities in `models.py` (Aeco-prefixed enums)
- [ ] Create Lakebase dev branch (`dev-aeco-hub`) and tables
- [ ] Implement `seed.py` (PGlite-safe, ~1K rows)
- [ ] Create project router skeleton with CRUD for projects/buildings/floors/spaces
- [ ] Create frontend route structure and project overview page
- [ ] Wire up router in `backend/router.py`
- [ ] Phase 1 unit tests (models, seed, router smoke tests)

### Phase 2: Core Features (3-4 days)

- [ ] Implement design routers (BIM models, clash reports, room requirements)
- [ ] Implement build routers (schedule, costs, site reports, change orders)
- [ ] Implement operate routers (sensors, energy, maintenance, space utilization)
- [ ] Create document and issue routers
- [ ] Build frontend pages for each lifecycle phase
- [ ] Create the Building Twin drilldown view (site → building → floor → room, tree + graph)
- [ ] Phase 2 unit tests for new routers and aggregation logic

### Phase 3: IoT & Analytics (2-3 days)

- [ ] Create `seed_uc_tables.py` for sensor readings (~500K rows via PySpark)
- [ ] Create IoT dashboard with Recharts (live-looking sensor data, energy trends)
- [ ] Create Genie Spaces (Project Analytics + Operations Intelligence)
- [ ] Create AI/BI Dashboard (Energy & Sustainability)
- [ ] Embed dashboard in Operate view
- [ ] Integration smoke test: query each Genie space

### Phase 4: AI & Ecosystem (2-3 days)

- [ ] Generate synthetic compliance docs and upload to UC Volume
- [ ] Create Knowledge Assistant (Standards & Compliance)
- [ ] Create Multi-Agent Supervisor (`aeco_hub_supervisor`)
- [ ] Implement chat endpoint using shared streaming utility
- [ ] Build the AECO Tool Navigator UI
- [ ] Build the Marketplace view
- [ ] Integration smoke test: MAS routes correctly across sub-agents

### Phase 5: Graph & Polish (1-2 days)

- [ ] Implement relationships API (paginated, capped) and seed graph edges
- [ ] Build force-directed graph visualization (`react-force-graph-2d`, lazy-loaded)
- [ ] Implement the phase timeline stepper component
- [ ] Polish responsive layout, loading states, error boundaries
- [ ] Regression tests for SQL safety, oversized chat input, graph pagination caps

### Phase 6: Deploy & Cleanup (1 day)

- [ ] Merge Lakebase dev branch to production
- [ ] Deploy to Databricks Apps
- [ ] Run validation tests (full success-criteria pass)
- [ ] Clean up temporary Databricks artifacts (test jobs, temp notebooks, unused branches)
- [ ] Update `development-guide.md` with AECO-specific lessons learned
- [ ] Update CLAUDE.md current state and TODO.md

---

## 10. Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Graph visualization | `react-force-graph-2d` (lazy-loaded) | Lightweight, interactive, handles 1K+ nodes |
| IoT data storage | UC tables (PySpark seed) | Too large for PGlite; Genie needs UC access |
| Building hierarchy | Lakebase (relational) | Fits naturally into parent-child FK relationships |
| Tool logos | SVG files in `ui/assets/aeco-tools/`; text-fallback by default | Trademark-safe default |
| Phase indicator | Custom Tailwind component | No good shadcn equivalent; simple to build |
| Sensor simulation | Deterministic random (seeded) | Reproducible demo data |
| Enum prefix | `Aeco` | Avoids OpenAPI schema collisions |
| Resource bootstrap | `bootstrap.py` orchestrator (D4 pattern) | Reproducible, idempotent |

---

## 11. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| PGlite crashes with seed data | Medium | Keep PGlite seed under 1K rows; IoT goes to UC only |
| Graph view performance with many nodes | Low | Project-scoped edges; pagination; cap node count |
| Third-party tool trademarks | Medium | Default to text labels; logo assets only ship after internal review |
| IoT dashboard performance | Low | Pre-aggregate in UC; use 15-min intervals |
| MAS endpoint provisioning time | Medium | Create early in Phase 4; test with direct Genie first |
| `react-force-graph-2d` bundle size | Low | ~200KB; lazy-load on the relationships route |

---

## 12. Success Criteria

- [ ] 5 projects visible in portfolio view with correct phase indicators
- [ ] Building drilldown navigates from site → building → floor → room
- [ ] IoT dashboard shows live-looking sensor data with trends
- [ ] Energy dashboard embedded from AI/BI
- [ ] Genie answers project analytics questions correctly
- [ ] MAS supervisor routes to correct sub-agent based on question type
- [ ] Graph view shows meaningful relationships between entities
- [ ] Marketplace shows partner ecosystem
- [ ] Tool navigator displays all AECO tools grouped by lifecycle phase
- [ ] All endpoints return proper error codes (no raw 500s)
- [ ] Every API route specifies `response_model` and `operation_id`
- [ ] PGlite seed runs without memory issues
- [ ] No SQL injection vulnerabilities (use safe query patterns)

---

## 13. Test Plan

Per CLAUDE.md working mode: tests are designed up front, regression tests are
mandatory for security fixes, and no P0/P1 fix is "done" without a named automated
regression test.

### Unit tests (`pytest`, no external deps)

| File | Coverage |
|------|----------|
| `tests/projects/aeco_hub/test_models.py` | SQLModel schema validation, enum values, FK relationships |
| `tests/projects/aeco_hub/test_seed.py` | PGlite seed runs in-memory; row counts match spec |
| `tests/projects/aeco_hub/test_routers.py` | FastAPI TestClient against in-memory DB; every route exposes `response_model` + `operation_id` |
| `tests/projects/aeco_hub/test_iot_service.py` | Sensor aggregation logic with synthetic input |
| `tests/projects/aeco_hub/test_relationships.py` | Graph API edge filtering and pagination cap |

### Integration tests (`pytest -m integration`, live Databricks)

| File | Coverage |
|------|----------|
| `tests/integration/test_aeco_hub_genie.py` | Smoke: each Genie space answers a known question with non-empty result |
| `tests/integration/test_aeco_hub_ka.py` | Smoke: KA returns sources for a known compliance question |
| `tests/integration/test_aeco_hub_mas.py` | Routing: project-analytics, ops, and standards questions reach the correct sub-agent |

### Regression tests (named after the bug they prevent)

| Test | Prevents |
|------|----------|
| `test_no_raw_sql_in_uc_queries` | Reintroduction of f-string SQL in UC paths |
| `test_chat_endpoint_rejects_oversized_message` | DoS via huge message payload |
| `test_relationships_pagination_caps_at_max` | Graph API returning unbounded result set |
| `test_dt_enum_prefixed` | Schema collision with other accelerators |

### UI / E2E (manual via `apx dev start` + browser)

- Portfolio → project → twin drilldown navigates correctly
- Phase stepper renders correct colors per project status
- IoT chart re-renders with new data
- MAS chat streams responses
- Tool navigator drawer opens for each tool
- Error boundary catches a forced API failure on the `operate` route

---

## 14. Future Extensions (Backlog)

Items deliberately out of scope for v1, captured for follow-up:

- **3D BIM viewer** — Replace tree+graph twin with three.js / xeokit-based IFC viewer
  (significant scope; consider as a separate page or plugin)
- **Live IoT ingest** — Replace seeded sensor data with Zerobus or DLT pipeline driven
  by a synthetic device simulator
- **Document AI extraction** — auto-parse uploaded BIM/PDF documents into
  `dt_documents` metadata via `ai_parse_document`
- **Real-time collaboration** — multi-user cursor / comments on a shared twin view
- **Mobile site app** — PWA for site reports and RFI capture from the field
- **Embodied carbon (LCA)** — calculate embodied carbon from BIM elements + cost
  items and add it to the Sustainability dashboard
- **Logo-asset pack** — internal-review process and shipped logo assets for the Tool
  Navigator (defaults to text labels in v1)

---

## 15. Decisions Locked In

For audit / handover:

- **Naming:** "AECO Hub" throughout; no third-party brand name appears in copy
- **Twin depth:** tree + force-directed graph (no 3D viewer in v1; see §14)
- **Compliance docs:** synthetic, generated in Phase 4
- **Lakebase dev branch:** approved (`dev-aeco-hub`)
- **Scope:** all six phases in scope (~12-17 days)
- **New frontend dep:** `react-force-graph-2d` (~200KB, lazy-loaded)
- **Resource bootstrap:** `bootstrap.py` orchestrator (D4 pattern)
- **Enum prefix:** `Aeco`
- **MAS naming:** snake_case sub-agents; `_supervisor` suffix on supervisor (D3)
