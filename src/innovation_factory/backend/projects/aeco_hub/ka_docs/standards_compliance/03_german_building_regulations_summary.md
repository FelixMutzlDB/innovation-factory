# German Building Regulations Summary

## Disclaimer

This is a project-team-facing summary of the regulations that most
frequently come up during AECO Hub digital twin workflows for projects
in Germany. It is not legal advice and is not a substitute for the
authoritative texts (Bauordnungen, Bauvorlagenverordnungen,
DIN/VDI/EN standards). Project leads should always consult the
Bauamt of the relevant Bundesland for binding interpretations.

This document covers Bavaria (BayBO) and Baden-Württemberg (LBO BW)
because the Schuster Bau AG portfolio is concentrated there. Other
Bundesländer follow similar structures with Bundesland-specific
deviations.

## Regulatory hierarchy

The German building regulation stack, from most general to most
specific:

1. **Musterbauordnung (MBO)** — model building code, federally
   maintained. Bundesländer adopt it with deviations.
2. **Landesbauordnung (LBO / BayBO etc.)** — state building code,
   binding within the Bundesland.
3. **Bauvorlagenverordnung (BauVorlV)** — what must be submitted with
   the building permit application.
4. **Sonderbauverordnungen** — special-occupancy ordinances (assembly
   buildings, garages, hospitals, hotels, schools).
5. **DIN / VDI / EN standards** — referenced by the LBO for technical
   compliance (fire, structure, accessibility, energy).

The AECO Hub's `dt_documents.document_type='permit'` row should
reference the LBO permit number once issued.

## Permit submission (Bauantrag)

The Bauantrag is the formal building permit application. AECO Hub
projects must submit at least the following deliverables (per BauVorlV):

- **Lageplan** — site plan at scale 1:500 or 1:1000.
- **Bauzeichnungen** — floor plans, sections, elevations at 1:100.
- **Baubeschreibung** — written project description.
- **Berechnungen** — technical calculations (structural, thermal,
  occupancy, parking).
- **Statistical data sheet** — gross / net floor area, usage breakdown.
- **Brandschutznachweis** — fire-protection compliance report.
- **Energieausweis** (planned) — energy performance certificate.

For renovation projects (`AMS-RENO`-style), the Bauantrag is replaced
or supplemented by an `Antrag auf Baugenehmigung im
vereinfachten Verfahren` for non-structural changes, or the full
Bauantrag for structural changes.

## Fire protection (Brandschutz)

Fire protection is the most frequent source of late-stage issues on
AECO Hub projects. Key concepts:

- **Brandabschnitte** — fire compartments. Maximum permitted size
  depends on building class (Gebäudeklasse 1–5) and use.
- **Rettungswege** — escape routes. Two independent routes are
  required for occupied spaces above the ground floor in most
  classes.
- **Feuerwiderstandsdauer** — fire-resistance duration of separating
  construction. Common requirements: F30, F60, F90, F90-A (with
  A-grade material).
- **Rauchabschnitte** — smoke compartments, often required in
  hospitals (`KES-2026`) and assembly buildings.

For the AECO Hub, BIM coordination must verify that:

- All fire-rated walls in the IFC model carry a `FireRating` property
  matching the Brandschutznachweis.
- Penetrations through fire-rated walls are tagged in the model and
  match the seal schedule (a frequent source of `dt_issues` rows
  with `category='safety'`).
- Door swings on escape routes are open in the direction of egress
  (often surfaces as a `category='design_issue'` in the AECO Hub).

## Accessibility (Barrierefreiheit)

Public buildings must meet DIN 18040-1 (public buildings) or
DIN 18040-2 (apartments). Key thresholds:

- **Tür** — clear opening width ≥ 90 cm for accessible doors.
- **Bewegungsfläche** — turning radius for wheelchairs ≥ 150 cm
  diameter.
- **Schwellen** — thresholds ≤ 2 cm.
- **Aufzug** — accessible elevator required for buildings with
  occupied floors > 13 m above ground.

The AECO Hub flags rooms tagged as `accessible: true` in
`dt_room_requirements` when their geometry violates DIN 18040.

## Energy performance (EnEV / GEG)

The Gebäudeenergiegesetz (GEG, 2020) replaced the EnEV. Key points
for AECO Hub projects:

- All new buildings must meet the `KfW-55` standard or better
  (`KfW-40` for projects seeking subsidies).
- The Energieausweis must be issued at occupancy and reissued every
  10 years.
- Renewable-energy heating share: ≥65% from renewable sources for
  new heating systems installed after 2024.

The AECO Hub `dt_energy_consumption` table is the primary feed for
the annual Energieausweis renewal — facility managers extract a
12-month sum and compare against the as-designed envelope.

## Building classes (Gebäudeklassen)

The Gebäudeklasse drives most BayBO / LBO BW thresholds. Quick
reference:

| Class | Description | Height (top floor floor-level) |
|-------|-------------|-------------------------------|
| GK 1 | Detached single dwelling, no commercial | ≤ 7 m |
| GK 2 | Up to 2 dwellings, no commercial | ≤ 7 m |
| GK 3 | Other buildings | ≤ 7 m |
| GK 4 | Multi-storey | ≤ 13 m |
| GK 5 | High-rise (Hochhaus) | > 13 m |

The QSP-2024 mixed-use development is GK 4. The TechHub Campus
Garching east wing is GK 4; the west wing is GK 3. Klinikum
Erweiterung Süd is GK 4 with Sonderbau treatment.

## Site reports (Bautagesberichte)

For active construction sites, daily site reports must be kept and
made available on request. The AECO Hub `dt_site_reports` table
stores a `report_type='daily'` row per business day for
in-construction projects, with workforce count, weather, and a
narrative summary. These satisfy the
`Bautagesbericht`-keeping obligation for VOB/B contracts.

## Common compliance pitfalls in AECO Hub workflows

- **Permit drift.** The BIM model evolves after permit submission
  and the Baugenehmigung no longer matches the as-designed model.
  Track every change-order row (`dt_change_orders`) for permit
  impact; trigger an Änderungsantrag if cumulative changes exceed
  the §66 BayBO threshold.
- **Brandschutznachweis stale.** The Brandschutznachweis was issued
  before MEP coordination and the duct routing now violates the
  fire-rated separations. Regenerate the Nachweis after any
  significant MEP rework.
- **DIN 18040 surprises.** Rooms originally not flagged as
  accessible are reclassified during Operate phase as a tenant
  requirement; geometry is non-compliant. Catch in `dt_room_requirements`
  before the requirement flips.
- **Energieausweis lapse.** The EnEV/GEG certificate expired 10
  years after issuance and the FM team forgot to renew. The AECO
  Hub will flag this as a `dt_issues` row when the certificate
  document's `created_at` exceeds 10 years for an operating project.
