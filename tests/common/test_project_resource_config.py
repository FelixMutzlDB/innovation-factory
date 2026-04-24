"""Tests for backend/projects/_project_config.py.

The shared config loader collapses three near-identical databricks_config
files onto one helper. These tests assert:

  1. Prefix wiring: ADTECH_DASHBOARD_ID populates DASHBOARD_ID.
  2. Fallback logic for workspace URL (explicit > DATABRICKS_HOST > empty).
  3. Empty defaults — never None, never raise.
  4. Per-project extras via .get("...") respect the prefix.
"""
from __future__ import annotations

import pytest

from innovation_factory.backend.projects._project_config import ProjectResourceConfig


@pytest.fixture
def clean_env(monkeypatch):
    """Strip every env var this module reads so tests are hermetic."""
    for k in [
        "WAREHOUSE_ID", "UC_CATALOG", "DATABRICKS_HOST",
        "ADTECH_WORKSPACE_URL", "ADTECH_DASHBOARD_ID",
        "ADTECH_GENIE_SPACE_ID", "ADTECH_MAS_ENDPOINT_NAME",
        "ADTECH_MAS_TILE_ID", "ADTECH_UC_SCHEMA",
        "ADTECH_ISSUE_RESOLUTION_KA_TILE_ID",
        "HB_DASHBOARD_ID", "HB_SC_DASHBOARD_ID",
    ]:
        monkeypatch.delenv(k, raising=False)


class TestDefaults:
    def test_all_empty_when_env_unset(self, clean_env):
        c = ProjectResourceConfig(prefix="ADTECH", default_schema="adtech_intelligence")
        assert c.warehouse_id == ""
        assert c.uc_catalog == ""
        assert c.workspace_url == ""
        assert c.dashboard_id == ""
        assert c.genie_space_id == ""
        assert c.mas_endpoint_name == ""
        assert c.mas_tile_id == ""

    def test_uc_schema_falls_back_to_default(self, clean_env):
        c = ProjectResourceConfig(prefix="ADTECH", default_schema="adtech_intelligence")
        assert c.uc_schema == "adtech_intelligence"


class TestPrefixWiring:
    def test_reads_prefixed_env(self, clean_env, monkeypatch):
        monkeypatch.setenv("ADTECH_DASHBOARD_ID", "dash-1")
        monkeypatch.setenv("ADTECH_GENIE_SPACE_ID", "gen-1")
        monkeypatch.setenv("ADTECH_MAS_ENDPOINT_NAME", "mas-endpoint-1")
        c = ProjectResourceConfig(prefix="ADTECH", default_schema="x")
        assert c.dashboard_id == "dash-1"
        assert c.genie_space_id == "gen-1"
        assert c.mas_endpoint_name == "mas-endpoint-1"

    def test_different_prefixes_do_not_cross_read(self, clean_env, monkeypatch):
        monkeypatch.setenv("ADTECH_DASHBOARD_ID", "ad-dash")
        monkeypatch.setenv("HB_DASHBOARD_ID", "hb-dash")
        ad = ProjectResourceConfig(prefix="ADTECH", default_schema="x")
        hb = ProjectResourceConfig(prefix="HB", default_schema="y")
        assert ad.dashboard_id == "ad-dash"
        assert hb.dashboard_id == "hb-dash"

    def test_shared_vars_are_unprefixed(self, clean_env, monkeypatch):
        monkeypatch.setenv("WAREHOUSE_ID", "wh-1")
        monkeypatch.setenv("UC_CATALOG", "catalog-1")
        c = ProjectResourceConfig(prefix="ADTECH", default_schema="x")
        assert c.warehouse_id == "wh-1"
        assert c.uc_catalog == "catalog-1"


class TestWorkspaceUrlFallback:
    def test_explicit_wins(self, clean_env, monkeypatch):
        monkeypatch.setenv("ADTECH_WORKSPACE_URL", "ws.example.com")
        monkeypatch.setenv("DATABRICKS_HOST", "https://other.example.com/")
        c = ProjectResourceConfig(prefix="ADTECH", default_schema="x")
        assert c.workspace_url == "ws.example.com"

    def test_databricks_host_fallback_strips_scheme_and_trailing_slash(
        self, clean_env, monkeypatch
    ):
        monkeypatch.setenv("DATABRICKS_HOST", "https://my.databricks.com/")
        c = ProjectResourceConfig(prefix="ADTECH", default_schema="x")
        assert c.workspace_url == "my.databricks.com"

    def test_empty_when_neither_set(self, clean_env):
        c = ProjectResourceConfig(prefix="ADTECH", default_schema="x")
        assert c.workspace_url == ""


class TestGetPerProjectExtras:
    def test_get_respects_prefix(self, clean_env, monkeypatch):
        monkeypatch.setenv("ADTECH_ISSUE_RESOLUTION_KA_TILE_ID", "tile-1")
        c = ProjectResourceConfig(prefix="ADTECH", default_schema="x")
        assert c.get("ISSUE_RESOLUTION_KA_TILE_ID") == "tile-1"

    def test_get_returns_default_when_unset(self, clean_env):
        c = ProjectResourceConfig(prefix="ADTECH", default_schema="x")
        assert c.get("MISSING_ONE") == ""
        assert c.get("MISSING_ONE", default="fallback") == "fallback"


class TestModuleShimsStillExpose:
    """Each project's databricks_config.py must keep exposing the same
    module-level names so existing `from ..databricks_config import X`
    imports don't break. These tests assert the public surface."""

    def test_adtech_module_names(self):
        from innovation_factory.backend.projects.adtech_intelligence import (
            databricks_config as m,
        )
        for name in (
            "WAREHOUSE_ID", "UC_CATALOG", "UC_SCHEMA", "WORKSPACE_URL",
            "DASHBOARD_ID", "GENIE_SPACE_ID", "MAS_ENDPOINT_NAME", "MAS_TILE_ID",
            "ISSUE_RESOLUTION_KA_TILE_ID", "ISSUE_RESOLUTION_KA_ENDPOINT",
            "CUSTOMER_RELATIONS_KA_TILE_ID", "CUSTOMER_RELATIONS_KA_ENDPOINT",
        ):
            assert hasattr(m, name), f"AdTech config missing {name!r}"

    def test_hb_module_names(self):
        from innovation_factory.backend.projects.hb_product_center import (
            databricks_config as m,
        )
        for name in (
            "WAREHOUSE_ID", "UC_CATALOG", "UC_SCHEMA", "WORKSPACE_URL",
            "MAS_ENDPOINT_NAME", "SC_DASHBOARD_ID", "AQ_DASHBOARD_ID",
            "SC_GENIE_SPACE_ID", "AQ_GENIE_SPACE_ID",
            "VS_ENDPOINT_NAME", "VS_INDEX_NAME", "VS_IMAGE_TABLE", "IMAGE_VOLUME_PATH",
        ):
            assert hasattr(m, name), f"HB config missing {name!r}"

    def test_mac_module_names(self):
        from innovation_factory.backend.projects.mol_asm_cockpit import (
            databricks_config as m,
        )
        for name in (
            "WAREHOUSE_ID", "UC_CATALOG", "UC_SCHEMA", "WORKSPACE_URL",
            "DASHBOARD_ID", "MAS_ENDPOINT_NAME",
        ):
            assert hasattr(m, name), f"MOL ASM config missing {name!r}"
