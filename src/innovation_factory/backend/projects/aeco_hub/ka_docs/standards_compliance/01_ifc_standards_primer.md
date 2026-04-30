# IFC Standards Primer for AECO Hub Projects

## Overview

The Industry Foundation Classes (IFC) is the open, vendor-neutral data
schema used by the AECO Hub digital twin for exchanging Building Information
Model (BIM) data across design tools, contractors, and facility management
platforms. This primer is a working reference for project teams onboarding
to the AECO Hub: it covers the IFC versions supported, the level-of-detail
(LOD) framework, model coordination expectations, and the BIM file
acceptance checklist applied at each stage gate.

## Supported IFC versions

The AECO Hub accepts IFC4 (`IFC4_REFERENCE_VIEW_2.0`,
`IFC4_DESIGN_TRANSFER_VIEW_1.0`) and IFC4.3 (the infrastructure-extended
schema) as primary deliverables. Legacy IFC2x3 is accepted only for renovation
projects whose existing federated models pre-date the IFC4 cutover. New
projects starting after January 2024 must deliver IFC4 or later.

When uploading models, the BIM Manager must record:

- `discipline` — one of `architectural`, `structural`, `mep`, `electrical`,
  `plumbing`, `hvac`, or `civil` (matches the `dt_bim_models.discipline`
  column in the digital twin).
- `lod` — see the LOD framework below.
- `version` — the project-specific revision identifier (e.g. `2.3`).
- `coordinate_system` — explicit CRS string. The AECO Hub assumes
  ETRS89 / UTM zone 32N for German projects unless overridden.

## Level of Detail (LOD) framework

The AECO Hub uses the BIMForum LOD specification. Each phase has a
target LOD that gates the design hand-off:

| Phase | Target LOD | Geometry expectation | Information expectation |
|-------|------------|----------------------|-------------------------|
| Schematic Design | LOD 100 | Symbolic / massing only | Approximate cost ranges, narrative descriptions |
| Design Development | LOD 200 | Generic placeholders, approximate sizes | Type-level performance specs |
| Construction Documents | LOD 300 | Specific sizing, location, orientation | Exact specs with manufacturer-class assumptions |
| Construction | LOD 400 | Fabrication-ready geometry | Complete fabrication, assembly, and installation specs |
| As-Built / FM Handover | LOD 500 | Verified field-installed condition | Verified spec aligned with COBie record |

Models below the target LOD for the active phase are flagged at upload
and require sign-off from the project's BIM Manager before being accepted
into the federated model.

## Federated model coordination

A federated model is the merged container of all discipline models for a
building. The AECO Hub generates the federation lazily — each
`dt_bim_models` row remains a single discipline file, but clash detection
and analytical queries operate across all referenced models for the
selected building.

Model coordination expectations:

- **Origin and units** — every IFC file must use the same project base
  point. Origin offsets discovered at federation time are flagged as a
  `clash` issue with severity `major`.
- **Naming** — element names should follow the project's BIM Execution
  Plan (BEP). For Schuster Bau AG projects, room names use the
  `BUILDING-FLOOR-ROOMNUMBER` pattern (e.g. `QSP-A-203`). The AECO Hub
  will fall back to the IFC GlobalId if the name is missing.
- **Property sets** — every model element should carry the IFC standard
  property sets plus the Schuster Bau AG custom set
  `Pset_SchusterBau_Operations` for elements that will be tracked in the
  operate phase.

## Acceptance checklist (per upload)

Before approving a BIM model for the federated set, the BIM Manager
runs the following checklist. Failed items require remediation; partial
fails can be approved with a recorded exception in `dt_issues`.

1. **Schema validity** — the IFC file parses cleanly with the
   `bSI Validation Service` (or equivalent). No critical errors.
2. **Discipline match** — the discipline declared at upload matches the
   `IFC project name` and the predominant element types in the file.
3. **LOD compliance** — geometry granularity matches the project's
   active phase target.
4. **Coordinate system** — CRS string matches the project default; no
   origin offset > 0.5 m relative to the building's anchor point.
5. **Element count sanity** — the file's element count is within
   ±25% of the project's per-discipline benchmark. Outliers are flagged
   for visual review.
6. **Naming compliance** — at least 95% of named spaces / rooms match
   the BEP naming pattern.
7. **Pset coverage** — all required property sets are present on the
   discipline's primary element types.

## Common rejection reasons

The most frequent BIM rejection causes seen across the Schuster Bau AG
portfolio:

- IFC2x3 file submitted for a project specifying IFC4 (rejected, ask
  for re-export).
- Model origin offset by 1 km — almost always a missed survey
  reference (rejected; clash detector would otherwise generate
  thousands of false positives).
- LOD 200 element placement in an LOD 300 deliverable — typically
  ductwork or piping that wasn't routed during the discipline's
  internal coordination round (approve with exception, route a
  follow-up issue to the discipline lead).
- Missing Pset_SchusterBau_Operations on assets that will be
  tracked in operate phase (approve, but block the operate-phase
  hand-off until remediated).

## References

This primer is a project-specific summary. For authoritative content
see the buildingSMART IFC4 specification, the BIMForum LOD
specification, and the German VDI 2552 series for BIM execution
guidance. The AECO Hub does not redistribute those texts.
