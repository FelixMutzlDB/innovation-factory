# COBie Handover Requirements

## Purpose

COBie (Construction-Operations Building Information Exchange) is the
structured asset dataset delivered at the end of the Build phase to
populate the AECO Hub's operate-phase tables. A complete COBie hand-off
removes the need for facility managers to re-key asset metadata into the
CMMS — every asset row, every space, every system reference flows from the
COBie spreadsheet into `dt_assets`, `dt_spaces`, and the maintenance
backlog.

This document is the project-team-facing summary of the AECO Hub's COBie
acceptance criteria. It covers the required sheets, the field-level
mapping into the AECO Hub data model, and the most common rejection
reasons.

## Required COBie sheets

The AECO Hub accepts COBie 2.4 in the standard 17-sheet template. At
minimum, the following sheets must be populated for hand-off acceptance:

| Sheet | AECO Hub mapping | Required |
|-------|-------------------|----------|
| Contact | dt_project_members | Yes |
| Facility | dt_projects (one row) | Yes |
| Floor | dt_floors | Yes |
| Space | dt_spaces | Yes |
| Type | (asset-type catalog, used for `dt_assets.category`) | Yes |
| Component | dt_assets | Yes |
| System | (system grouping for asset rollups) | Recommended |
| Spare | (spare-parts master, future Phase 6 enhancement) | Optional |
| Resource | (manpower / skill resource definitions) | Optional |
| Job | (preventive maintenance jobs → dt_maintenance_orders) | Yes |
| Document | dt_documents (with `document_type='cobie'`) | Yes |

The remaining COBie sheets — Coordinate, Connection, Spare, Resource,
Job, Issue, Impact, Assembly, Attribute, Zone — are accepted but not
mandatory for the AECO Hub data load.

## Field-level mapping (Component → dt_assets)

The Component sheet drives the `dt_assets` table. Required field mapping:

| COBie Component column | dt_assets column | Notes |
|------------------------|------------------|-------|
| Name | name | Unique within building |
| TypeName | (resolves category via Type lookup) | Type sheet must exist first |
| Space | space_id | Resolved by Space.Name match |
| SerialNumber | serial_number | Optional but strongly recommended |
| InstallationDate | install_date | ISO 8601 format |
| WarrantyDurationParts | warranty_expires (calculated) | install_date + duration |
| Manufacturer | manufacturer | Free-text |
| ModelNumber | model | Free-text |

Notably, the `category` column on `dt_assets` is derived from the
COBie Type.Category field, not from the Component sheet directly.
Acceptable Type.Category values map to the AECO Hub asset categories:

- `HVAC equipment` → `hvac`
- `Electrical equipment` → `electrical`
- `Plumbing fixture` → `plumbing`
- `Lighting fixture` → `lighting`
- `Security equipment` → `security`
- `Fire safety equipment` → `fire_safety`
- `Vertical transportation` → `elevator`
- `Appliance` → `appliance`
- `Furniture` → `furniture`
- `Sensor / controller` → `sensor`

Categories outside this list are accepted but stored as the closest
match with a `dt_issues` row recording the discrepancy for the FM team.

## Acceptance criteria

A COBie deliverable is accepted when:

1. All required sheets are present and non-empty.
2. Every Component row resolves to a Space row by name match
   (no orphaned components).
3. Every Component row resolves to a Type row by TypeName match
   (no orphaned types).
4. Every preventive-maintenance Job row references at least one
   Component or System.
5. Required fields on the Component sheet are populated for ≥90%
   of rows. Missing fields land as `dt_issues` rows for the FM team
   to resolve post-hand-off, but do not block acceptance.
6. SerialNumber uniqueness is checked across all components in the
   facility. Duplicates are flagged but allowed (some manufacturers
   reuse serial-like part numbers across sub-assemblies).

## Common rejection reasons

- **Orphaned components.** A Component row references a Space.Name that
  doesn't exist on the Space sheet. Almost always caused by manual
  edits to either sheet after the BIM extraction.
- **Type sheet empty.** Components are present but Types are not.
  Without Types, the `dt_assets.category` column cannot be populated.
- **Inconsistent units.** Mixed metric and imperial units within a
  single sheet. The AECO Hub assumes SI metric throughout.
- **Date format drift.** ISO 8601 expected; project teams sometimes
  submit `MM/DD/YYYY` (US) or `DD.MM.YYYY` (DE) which fails the
  loader's strict-date check.

## Loading process

Once the COBie spreadsheet is accepted, the AECO Hub loader (run by
the FM onboarding team) creates:

- 1 row in `dt_projects` (or updates the existing row if the project
  is already on the AECO Hub).
- N rows in `dt_floors` and `dt_spaces` (Floor + Space sheets).
- N rows in `dt_assets` (Component sheet, joined with Type for
  category).
- N rows in `dt_maintenance_orders` with `status='scheduled'` for
  every preventive Job (Job sheet).
- 1 row in `dt_documents` recording the COBie file itself with
  `document_type='cobie'` and `phase='operate'`.

The hand-off is considered complete when the project's phase
transitions from `build` to `operate` in `dt_project_phases`.
