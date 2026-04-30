"""Unit tests for scripts/snapshot_diff.py.

Validates the normalization rules so a future contributor can add a
new volatile-field strip without breaking the existing diff cases.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def mod():
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "snapshot_diff.py"
    spec = importlib.util.spec_from_file_location("snapshot_diff", path)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class TestNormalize:
    def test_strips_uids(self, mod):
        snap = 'uid=2_15 button "Toggle Sidebar"'
        out = mod.normalize(snap)
        assert "2_15" not in out
        assert "<UID>" in out

    def test_strips_live_iot_decimals(self, mod):
        snap = 'StaticText "20.6"\nStaticText "642.1"'
        out = mod.normalize(snap)
        assert "20.6" not in out
        assert "642.1" not in out
        assert "<NUM>" in out

    def test_strips_iso_timestamps(self, mod):
        snap = 'generated_at="2026-04-29T07:58:00Z"'
        out = mod.normalize(snap)
        assert "2026-04-29T07:58:00Z" not in out
        assert "<TIMESTAMP>" in out

    def test_strips_dates(self, mod):
        snap = 'StaticText "2026-06-23"'
        out = mod.normalize(snap)
        assert "2026-06-23" not in out
        assert "<DATE>" in out

    def test_strips_recharts_axis_labels(self, mod):
        snap = 'StaticText "Mar 31"\nStaticText "Apr 12"\nStaticText "Dec 1"'
        out = mod.normalize(snap)
        for tick in ("Mar 31", "Apr 12", "Dec 1"):
            assert tick not in out
        assert out.count("<MONTH-DAY>") == 3

    def test_strips_synthetic_sensor_codes(self, mod):
        snap = 'StaticText "S-007-0142"\nStaticText "S-001-0099"'
        out = mod.normalize(snap)
        assert "S-007-0142" not in out
        assert "<SENSOR-CODE>" in out

    def test_preserves_stable_copy(self, mod):
        """Headings, button labels, project names must NOT be normalized
        — drift in those should fail the diff."""
        snap = 'heading "AECO Hub"\nStaticText "Logistikzentrum A9"\nStaticText "Operate"'
        out = mod.normalize(snap)
        assert "AECO Hub" in out
        assert "Logistikzentrum A9" in out
        assert "Operate" in out

    def test_strips_trailing_whitespace(self, mod):
        snap = "line one  \nline two\t\n"
        out = mod.normalize(snap)
        assert "line one\nline two\n" == out


class TestDiffSnapshots:
    def test_clean_match_returns_empty(self, mod, tmp_path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("uid=1_2 heading 'AECO Hub'\n")
        b.write_text("uid=9_8 heading 'AECO Hub'\n")  # diff UID, same content
        assert mod.diff_snapshots(a, b) == []

    def test_real_drift_emits_diff(self, mod, tmp_path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("heading 'AECO Hub'\n")
        b.write_text("heading 'AECO Renamed Hub'\n")
        diff = mod.diff_snapshots(a, b)
        assert diff, "expected non-empty diff for renamed heading"
        joined = "".join(diff)
        assert "AECO Hub" in joined
        assert "AECO Renamed Hub" in joined

    def test_volatile_drift_alone_is_clean(self, mod, tmp_path):
        """Only a UID change → still clean (the whole point of the
        normalizer)."""
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("uid=2_15 button\nuid=2_16 button\n")
        b.write_text("uid=8_99 button\nuid=8_100 button\n")
        assert mod.diff_snapshots(a, b) == []
