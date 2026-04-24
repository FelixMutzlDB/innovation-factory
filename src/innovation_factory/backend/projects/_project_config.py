"""Shared Databricks resource-config loader used by every project.

Each project has its own ``databricks_config.py`` exposing module-level
constants (``DASHBOARD_ID``, ``GENIE_SPACE_ID``, ``MAS_ENDPOINT_NAME``,
etc.). Before this module, the same ``os.getenv`` boilerplate was
copy-pasted across all three — with subtle divergence (HB had no
prefix on the shared-fallback comment; MOL didn't expose ``WORKSPACE_URL``).

``ProjectResourceConfig`` is instantiated once per project with the
env-var prefix (``"ADTECH"``, ``"HB"``, ``"MAC"``) and a default UC
schema. Every project file then re-exports the fields it needs as
module-level names so existing ``from ..databricks_config import X``
callers keep working.

Why not just ``dataclass`` fields? Because we read env vars at import
time (so changes require a restart), and we want the project files
readable at a glance. This class is a ~30-line helper, not a framework.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectResourceConfig:
    """Read Databricks resource IDs for one project from the environment.

    All fields default to ``""`` when unset so the app never raises on
    missing config — the UI checks ``configured`` booleans to decide
    whether to render an embed panel vs a "not configured" empty state.
    """

    prefix: str
    default_schema: str

    # ------------------------------------------------------------------
    # Shared (unprefixed) values
    # ------------------------------------------------------------------
    @property
    def warehouse_id(self) -> str:
        return os.getenv("WAREHOUSE_ID", "")

    @property
    def uc_catalog(self) -> str:
        return os.getenv("UC_CATALOG", "")

    # ------------------------------------------------------------------
    # Per-project values — each one is prefixed with the project's prefix
    # ------------------------------------------------------------------
    def _pv(self, name: str, default: str = "") -> str:
        return os.getenv(f"{self.prefix}_{name}", default)

    @property
    def uc_schema(self) -> str:
        return self._pv("UC_SCHEMA", self.default_schema)

    @property
    def workspace_url(self) -> str:
        # Priority: explicit <PREFIX>_WORKSPACE_URL → DATABRICKS_HOST → empty.
        explicit = self._pv("WORKSPACE_URL")
        if explicit:
            return explicit
        return os.getenv("DATABRICKS_HOST", "").replace("https://", "").rstrip("/")

    @property
    def dashboard_id(self) -> str:
        return self._pv("DASHBOARD_ID")

    @property
    def genie_space_id(self) -> str:
        return self._pv("GENIE_SPACE_ID")

    @property
    def mas_endpoint_name(self) -> str:
        return self._pv("MAS_ENDPOINT_NAME")

    @property
    def mas_tile_id(self) -> str:
        return self._pv("MAS_TILE_ID")

    def get(self, name: str, default: str = "") -> str:
        """Read an arbitrary prefixed env var — use for project-specific
        knobs that don't fit the shared field set (HB's SC/AQ dashboards,
        AdTech's two KAs, HB's vector-search config, etc.)."""
        return self._pv(name, default)
