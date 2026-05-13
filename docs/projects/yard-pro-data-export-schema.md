# yard-pro — Data Export Schema (GDPR Art. 20)

> Stable JSON Schema for the **GDPR Art. 20 (data portability)** export.
> Endpoint: `GET /api/projects/yard-pro/yards/{yard_id}/export/portability`
> Implementation: `services/gdpr_service.py::export_yard_portability`
> Regression test: `tests/projects/yard_pro/test_gdpr_art20_portability_export.py`
> Schema version (current): **`1.0.0`** — bumped via `gdpr_service.DATA_EXPORT_SCHEMA_VERSION`.

This document is the **contract** between the yard-pro service and any
future provider importing a household's data. A contributor who breaks
the schema breaks the regression test by name; the test's failure
message points back to this doc.

The GDPR Art. 15 (right of access) endpoint
(`GET /yards/{yard_id}/export/access`) returns the **same underlying
snapshot** without the versioned envelope — see §3 for the diff.

---

## 1. Top-level envelope

```jsonc
{
  "schema_version": "1.0.0",          // string — semver-shaped; bumped on shape break
  "article": "GDPR Art. 20",          // string — the right being exercised
  "generated_at": "2026-05-13T…Z",    // string (ISO 8601) — server clock at export
  "yard": { … }                       // YpYardSnapshot — see §2
}
```

| Field             | Type             | Required | Notes |
|-------------------|------------------|----------|-------|
| `schema_version`  | string           | yes      | Matches `gdpr_service.DATA_EXPORT_SCHEMA_VERSION`. Importers should refuse unknown majors. |
| `article`         | string           | yes      | Always `"GDPR Art. 20"` for this endpoint. |
| `generated_at`    | string (ISO8601) | yes      | UTC. Used for SAR audit logging. |
| `yard`            | object           | yes      | The snapshot itself — see §2. |

---

## 2. `yard` — `YpYardSnapshot`

The same shape returned by the Art. 15 endpoint at the top level.

```jsonc
{
  "yard_id": 1,
  "yards": [ { /* yp_yards row */ } ],
  "tables": {
    "yp_action_log":          [ /* row */, … ],
    "yp_calendar_entries":    [ … ],
    "yp_coach_feedback":      [ … ],
    "yp_coach_messages":      [ … ],
    "yp_coach_sessions":      [ … ],
    "yp_consumables":         [ … ],
    "yp_dealer_relationships":[ … ],
    "yp_diagnoses":           [ … ],
    "yp_nudge_dismissals":    [ … ],
    "yp_plants":              [ … ],
    "yp_tool_readiness":      [ … ],
    "yp_tools":               [ … ]
  },
  "photos": { … },
  "coach_transcripts_external": { … }
}
```

| Field                          | Type                  | Required | Source / notes |
|--------------------------------|-----------------------|----------|----------------|
| `yard_id`                      | int                   | yes      | Echoes the path param. |
| `yards`                        | list[object]          | yes      | List with the single `yp_yards` row (always length 1 — RLS guarantees the yard exists). Column-named keys, JSON-safe values. |
| `tables`                       | object (str → list)   | yes      | One key per `yp_*` table that has a `yard_id` column OR an `_INDIRECT_REFS` mapping. Keys are sorted alphabetically. Values are lists of row dicts (may be empty). |
| `photos`                       | object                | yes      | UC Volume photo URIs — see §2.1. |
| `coach_transcripts_external`   | object                | yes      | Pointer to the consent-gated Delta transcript mirror — see §2.2. |

### Enumeration rule (load-bearing)

The `tables` keys are **derived at request time** from
`SQLModel.metadata.tables` filtered to the `yp_*` prefix. A future
`yp_*` table is auto-included; the regression test exercises this and
fails if the enumeration walk drifts from the delete cascade.

Indirect-reference tables (no direct `yard_id` column):

| Child table          | FK column   | Parent table        | Parent PK |
|----------------------|-------------|---------------------|-----------|
| `yp_coach_messages`  | `session_id`| `yp_coach_sessions` | `id`      |
| `yp_tool_readiness`  | `tool_id`   | `yp_tools`          | `id`      |

These are inlined identically to direct tables — importers don't need
to know the indirection.

### Row dict shape

Each row dict is keyed by the SQLAlchemy column name. Values are
JSON-safe:

- `datetime` / `date` → ISO 8601 string (`.isoformat()`).
- enums → their `.value` (string).
- `dict` / `list` columns (JSON storage) → recursively serialized.
- `None` → JSON `null`.

No nested SQLAlchemy objects or proxies are ever emitted.

### 2.1. `photos` — `YpYardExportPhotos`

```jsonc
{
  "volume_path": "/Volumes/main/yard_pro/photos/1/",  // or "" when unconfigured
  "uris": [
    "/Volumes/main/yard_pro/photos/1/leaf-2026-05-09.jpg",
    "/Volumes/main/yard_pro/photos/1/lawn-2026-05-10.png"
  ]
}
```

| Field         | Type         | Required | Notes |
|---------------|--------------|----------|-------|
| `volume_path` | string       | yes      | UC Volume prefix; empty string in local dev or when `PHOTOS_VOLUME_PATH` is unset. |
| `uris`        | list[string] | yes      | Volume paths to each photo. May be empty. |

**RT-024 invariant:** image bytes are **NEVER** inlined here, base64-
encoded, or otherwise rendered inline. The export carries URIs only;
SAR responders fetch the bytes out-of-band via the Volume API and ship
them as a separate signed-URL ZIP attachment.

### 2.2. `coach_transcripts_external`

```jsonc
{
  "source": "yard_pro_bronze.coach_transcripts",
  "consent_gated": true,
  "retention_unconsented_days": 30,
  "retention_consented_months": 13,
  "note": "Transcript content is mirrored to Delta via Lakehouse Sync from yp_coach_messages above. Inlined Lakebase rows are the authoritative export for SAR purposes."
}
```

| Field                          | Type    | Required | Notes |
|--------------------------------|---------|----------|-------|
| `source`                       | string  | yes      | The UC table where the analytical mirror lives. |
| `consent_gated`                | bool    | yes      | `true` — rows with `consent_flag=false` are excluded from analytics (plan §8). |
| `retention_unconsented_days`   | int     | yes      | Hard-delete window for `consent_flag=false` rows (plan §5). |
| `retention_consented_months`   | int     | yes      | Hard-delete window for `consent_flag=true` rows (plan §5). |
| `note`                         | string  | yes      | Human-readable explanation; importers may ignore. |

The **authoritative** transcript export comes from the
`yp_coach_messages` rows inlined under `tables`. This block is
informational — it documents where the OEM-side analytical rollups
live so a SAR responder knows about both copies.

---

## 3. Diff vs Art. 15 (`/export/access`)

The Art. 15 endpoint returns the **flat snapshot** without the
versioned envelope:

```jsonc
{
  "article": "GDPR Art. 15",
  "generated_at": "…",
  "yard_id": 1,
  "yards":   [ … ],   // same shape as yard.yards
  "tables":  { … },   // same shape as yard.tables
  "photos":  { … },   // same shape as yard.photos
  "coach_transcripts_external": { … }
}
```

Art. 15 is for **SAR fulfillment** (human-readable, internally consumed
by the privacy operator who packages the response to the data
subject). Art. 20 is for **machine ingest** (a future provider takes
the JSON and rehydrates a yard).

The `yard` sub-object in Art. 20 is byte-equivalent to the Art. 15 top-
level minus `article` and `generated_at`.

---

## 4. Schema versioning policy

- **Patch bumps** (`1.0.0` → `1.0.1`) — additive, backwards-compatible
  changes (new optional field, new `tables.*` entry from a new `yp_*`
  table). Importers MUST ignore unknown keys.
- **Minor bumps** (`1.0.0` → `1.1.0`) — additive, backwards-compatible
  changes that require importer awareness (e.g. a new top-level key
  that older importers should pass through).
- **Major bumps** (`1.0.0` → `2.0.0`) — breaking changes (renamed key,
  removed table, changed value type). Importers MUST refuse unknown
  majors; the changelog below documents the migration path.

### Changelog

| Version | Date       | Change |
|---------|------------|--------|
| `1.0.0` | 2026-05-13 | Initial schema (P2 ship). |

---

## 5. Async-job mode (production fulfillment)

Plan §8 mandates that the production Art. 15/20 endpoints enqueue an
**async job** that produces a signed-URL ZIP with a 30-day SLA. P2
ships the **synchronous JSON** variant — the load-bearing piece is the
snapshot builder, which the async wrapper will reuse unchanged.

When the async wrapper lands, the schema does not change. The endpoint
response will become a `202 Accepted` with a `job_id`; polling
`GET /yards/{yard_id}/export/access?job_id=…` returns the same JSON
shape once the job completes.

---

## 6. RLS

Both endpoints enforce RLS via `assert_yard_owned_by_caller` (defined
in `routers/yards.py`). Cross-tenant access returns 404 — same
convention as the rest of the yard-pro surface (404, not 403, to leak
as little as possible about other households' yard IDs).
