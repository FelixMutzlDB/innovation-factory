# Innovation Factory

**Making Data Intelligence tangible — one prototype at a time.**

The Innovation Factory is a framework for rapid prototyping and innovation fostering built on the [Databricks](https://www.databricks.com/) platform. It serves as a living gallery of solution accelerators — fully functional, end-to-end applications that demonstrate how Databricks capabilities such as AI/BI Dashboards, Genie Spaces, Multi-Agent Supervisors, Lakebase, and Foundation Model APIs come together to solve real-world business problems.

Rather than presenting Data Intelligence as an abstract concept, the Innovation Factory makes it *tangible*: each accelerator is a working prototype that stakeholders can see, touch, and interact with — bridging the gap between what's technically possible and what's concretely valuable.

![Innovation Factory — Project Gallery](docs/images/gallery.png)

---

## Why the Innovation Factory Exists

Solution accelerators have traditionally been documentation-heavy artifacts — increasingly just **markdown files** in a repository. While useful as reference material, they rarely convey the full potential of a platform to non-technical stakeholders. A markdown file describing "how to build a real-time anomaly detection pipeline" doesn't carry the same weight as *showing* one in action.

The Innovation Factory flips this model:

- **From docs to demos.** Each accelerator is a deployable, interactive application — not a static notebook or README.
- **From concept to conviction.** Stakeholders experience Data Intelligence first-hand, making it far easier to align on investment and adoption.
- **From weeks to days.** Built on the [`apx`](https://github.com/databricks-solutions/apx) toolkit, new prototypes can be scaffolded, developed, and deployed in days rather than weeks.

The ambition is clear: **lower the barrier between "what if" and "here it is"** — fostering a culture of rapid innovation where ideas are validated through working software, not slide decks.

---

## What's Inside

The Innovation Factory ships as a single Databricks App containing a curated gallery of accelerators. Each project is a self-contained, full-stack application with its own data model, backend logic, and polished UI.

### Current Accelerators

| Accelerator | Domain | Highlights |
|---|---|---|
| **ViDistrictOne** | Smart Energy | Neighborhood-level energy monitoring, PV & battery optimization, EV charging, maintenance alerts |
| **BSH Remote Assist** | Home Appliances | AI-powered service ticket resolution, device management, knowledge search, technician workflows |
| **AdTech Intelligence** | Advertising & Media | AI/BI dashboards, Genie-powered inventory exploration, multi-agent issue resolution, anomaly detection |

Each accelerator demonstrates a different facet of the Databricks platform — from Genie Spaces for natural-language data exploration to Multi-Agent Supervisors orchestrating complex workflows.

![Accelerator Detail — AdTech Intelligence](docs/images/accelerator-detail.png)

### Build a New Idea

Beyond the pre-built accelerators, the Innovation Factory includes a guided **idea builder** — a conversational flow that helps users define a new accelerator concept and produces a structured coding agent prompt ready for implementation.

![Build a New Idea — Guided Chat](docs/images/build-idea.png)

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Innovation Factory App                     │
├──────────────────────────────────────────────────────────────┤
│  FastAPI Backend                                             │
│  ├── /api/projects          → Gallery & project metadata     │
│  ├── /api/ideas             → Idea builder sessions & chat   │
│  ├── /api/projects/<slug>/  → Per-accelerator APIs           │
│  └── /                      → Serves built React frontend    │
├──────────────────────────────────────────────────────────────┤
│  PostgreSQL (Lakebase)                                       │
│  ├── Platform tables (projects, users)                       │
│  └── Per-accelerator tables (domain-specific)                │
├──────────────────────────────────────────────────────────────┤
│  React Frontend (Vite + TanStack Router)                     │
│  ├── Gallery view           → Browse all accelerators        │
│  ├── /projects/<slug>/      → Accelerator-specific UIs       │
│  └── /build-idea            → Guided idea builder            │
├──────────────────────────────────────────────────────────────┤
│  Databricks Platform Services                                │
│  ├── Genie Spaces           → Natural-language data queries  │
│  ├── AI/BI Dashboards       → Embedded analytics             │
│  ├── Multi-Agent Supervisor → Orchestrated AI workflows      │
│  └── Foundation Model APIs  → LLM-powered features           │
└──────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11+, FastAPI, SQLModel, Pydantic |
| **Database** | PostgreSQL — PGlite (local dev), Lakebase Autoscaling (production) |
| **Frontend** | React 19, TypeScript, Vite, TanStack Router & Query |
| **UI Components** | shadcn/ui, Radix UI, Tailwind CSS, Recharts |
| **API Client** | Auto-generated TypeScript client from OpenAPI schema |
| **Platform** | Databricks SDK, Databricks Apps, Unity Catalog |
| **Toolkit** | [`apx`](https://github.com/databricks-solutions/apx) — full-stack Databricks App framework |

---

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- A Databricks workspace (for deployment and platform features)

### Development

Start all development servers (backend, frontend, and OpenAPI watcher):

```bash
uv run apx dev start
```

This launches the backend, frontend dev server, and an OpenAPI watcher that auto-regenerates the TypeScript API client on every code change.

### Monitoring & Logs

```bash
# View recent logs
uv run apx dev logs

# Stream logs in real-time
uv run apx dev logs -f

# Check server status
uv run apx dev status

# Stop all servers
uv run apx dev stop
```

### Code Quality

Run TypeScript and Python checks:

```bash
uv run apx dev check
```

### Build & Deploy

```bash
# Production build
uv run apx build

# Deploy to Databricks
databricks bundle deploy -p <your-profile>
```

---

## Adding a New Accelerator

Each accelerator follows a consistent structure:

```
src/innovation_factory/
├── backend/projects/<slug>/
│   ├── router.py       # FastAPI routes
│   ├── models.py       # SQLModel entities
│   ├── service.py      # Business logic
│   └── seed.py         # Sample data
└── ui/routes/projects/<slug>/
    ├── route.tsx        # Layout & navigation
    └── <pages>.tsx      # Feature pages
```

1. **Define the project** in the seed data with a name, description, and slug.
2. **Build the backend** — models, routes, and services under `backend/projects/<slug>/`.
3. **Build the frontend** — TanStack Router file-based routes under `ui/routes/projects/<slug>/`.
4. **Wire it up** — mount the project router in `backend/router.py`.

The `apx` toolkit handles the rest: OpenAPI client generation, hot reload, and production builds.

---

## Philosophy

The Innovation Factory is built on a simple conviction: **the best way to communicate the value of a data platform is to show it in action.** Every accelerator is a conversation starter — a working prototype that invites stakeholders to imagine what's possible for their own domain.

Solution accelerators shouldn't live in markdown files. They should live in browsers.

---

<p align="center">Built with <a href="https://github.com/databricks-solutions/apx">apx</a> on <a href="https://www.databricks.com/">Databricks</a></p>
