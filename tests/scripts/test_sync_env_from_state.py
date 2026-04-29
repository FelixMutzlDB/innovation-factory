"""Unit tests for scripts/sync_env_from_state.py.

Validates the marker-replacement logic without touching the real
``fevm_agents_state.json`` or the actual env files. Mocks the state
file via tmp paths so a state change can never accidentally rewrite
the user's ``.env``.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def mod():
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "sync_env_from_state.py"
    spec = importlib.util.spec_from_file_location("sync_env_from_state", path)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_build_env_vars_orders_dashboards_first(mod):
    state = {
        "dashboards": {"adtech": "dash-1", "hb_sc": "dash-2"},
        "genies": {"adtech": "gen-1"},
        "kas": {},
        "mas": {"adtech": {"tile_id": "t-1", "endpoint_name": "ep-1"}},
    }
    pairs = mod.build_env_vars(state)
    keys = [k for k, _ in pairs]
    assert keys[0].endswith("_DASHBOARD_ID")  # dashboards first
    assert "ADTECH_DASHBOARD_ID" in keys
    assert "ADTECH_GENIE_SPACE_ID" in keys
    assert "ADTECH_MAS_TILE_ID" in keys


def test_replace_block_inside_markers(mod):
    text = (
        "before line\n"
        "# AECO_AUTOGEN_BEGIN: resource-ids\n"
        "OLD_VAR=stale\n"
        "# AECO_AUTOGEN_END\n"
        "after line\n"
    )
    new_block = (
        "# AECO_AUTOGEN_BEGIN: resource-ids\n"
        "NEW_VAR=fresh\n"
        "# AECO_AUTOGEN_END"
    )
    out = mod.replace_block(text, "", new_block)
    assert "OLD_VAR" not in out
    assert "NEW_VAR=fresh" in out
    assert out.startswith("before line")
    assert out.endswith("after line\n")


def test_replace_block_raises_when_markers_missing(mod):
    """The script must NOT silently append. A misplaced manual block
    creates duplicates that bite at deploy time."""
    text = "no markers here at all\n"
    with pytest.raises(mod.MissingMarkers):
        mod.replace_block(text, "", "# AECO_AUTOGEN_BEGIN: resource-ids\nx=1\n# AECO_AUTOGEN_END")


def test_replace_block_respects_indent(mod):
    text = (
        "config:\n"
        "  env:\n"
        "          # AECO_AUTOGEN_BEGIN: resource-ids\n"
        "          - name: OLD\n"
        "            value: stale\n"
        "          # AECO_AUTOGEN_END\n"
    )
    new_block = mod.render_yaml_block(
        [("FOO", "bar")], indent="          "
    )
    out = mod.replace_block(text, "          ", new_block)
    assert "OLD" not in out
    assert "FOO" in out
    assert "          - name: FOO" in out


def test_check_mode_returns_drift_signal(mod, tmp_path, monkeypatch):
    """``--check`` should not write but should report drift."""
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({
        "dashboards": {"adtech": "new-dash"},
        "genies": {}, "kas": {}, "mas": {},
    }))
    monkeypatch.setattr(mod, "STATE_FILE", state_file)
    target = tmp_path / "app.yml"
    target.write_text(
        "env:\n"
        "  # AECO_AUTOGEN_BEGIN: resource-ids\n"
        "  - name: ADTECH_DASHBOARD_ID\n"
        "    value: old-dash\n"
        "  # AECO_AUTOGEN_END\n"
    )
    changed, payload, error = mod.sync_file(target, "yaml", indent="  ")
    assert error is None
    assert changed is True
    assert payload is not None
    assert "new-dash" in payload
    assert "old-dash" not in payload


def test_render_yaml_quotes_empty_values(mod):
    """Empty values must render as `value: ""` so the YAML stays valid."""
    block = mod.render_yaml_block([("FOO", "")], indent="  ")
    assert '  - name: FOO' in block
    assert '  value: ""' in block
