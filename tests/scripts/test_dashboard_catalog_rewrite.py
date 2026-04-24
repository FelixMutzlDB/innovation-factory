"""Unit test for the dashboard catalog rewrite helper.

When we migrate a Lakeview dashboard from one workspace to another, every
fully-qualified table reference in the serialized JSON must move from the
source catalog to the target catalog. The helper rewrites those references
(only at word boundaries followed by a dot), without touching unrelated
strings that happen to contain the same substring.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys


def _load_module():
    """Load scripts/deploy_agents_fevm.py without running its main block."""
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "deploy_agents_fevm.py"
    spec = importlib.util.spec_from_file_location("deploy_agents_fevm", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["deploy_agents_fevm"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestRewriteCatalog:
    def test_replaces_fqn_table_refs(self):
        mod = _load_module()
        serialized = (
            'SELECT * FROM innovation_factory_catalog.hb_product_center.hb_products '
            'JOIN innovation_factory_catalog.adtech_intelligence.campaigns'
        )
        out = mod.rewrite_catalog_in_serialized(
            serialized, "innovation_factory_catalog", "felix_demo_catalog"
        )
        assert "felix_demo_catalog.hb_product_center.hb_products" in out
        assert "felix_demo_catalog.adtech_intelligence.campaigns" in out
        assert "innovation_factory_catalog" not in out

    def test_leaves_unrelated_strings_alone(self):
        mod = _load_module()
        serialized = (
            '"description": "This dashboard is for innovation_factory purposes"'
        )
        out = mod.rewrite_catalog_in_serialized(
            serialized, "innovation_factory_catalog", "felix_demo_catalog"
        )
        assert out == serialized, "bare mentions without `.` must not be rewritten"

    def test_preserves_json_structure(self):
        mod = _load_module()
        serialized = '{"query": "SELECT col FROM innovation_factory_catalog.s.t"}'
        out = mod.rewrite_catalog_in_serialized(
            serialized, "innovation_factory_catalog", "felix_demo_catalog"
        )
        # Must still be parseable as JSON.
        import json as _json
        parsed = _json.loads(out)
        assert "felix_demo_catalog.s.t" in parsed["query"]

    def test_idempotent_when_already_target(self):
        mod = _load_module()
        serialized = 'SELECT * FROM felix_demo_catalog.s.t'
        out = mod.rewrite_catalog_in_serialized(
            serialized, "innovation_factory_catalog", "felix_demo_catalog"
        )
        assert out == serialized

    def test_only_touches_fqn_before_dot(self):
        """Edge: a literal `innovation_factory_catalog` without a `.` — say,
        as a word in a description — must not be rewritten."""
        mod = _load_module()
        serialized = (
            'CREATE CATALOG innovation_factory_catalog; '
            'USE innovation_factory_catalog.hb_product_center;'
        )
        out = mod.rewrite_catalog_in_serialized(
            serialized, "innovation_factory_catalog", "felix_demo_catalog"
        )
        # First reference: no `.` → left alone
        assert "CREATE CATALOG innovation_factory_catalog;" in out
        # Second reference: `.` → rewritten
        assert "USE felix_demo_catalog.hb_product_center;" in out
