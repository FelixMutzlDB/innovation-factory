"""yard-pro KA corpus shape tests.

Plan §7 declares the KA corpus risk #1: the demo's coach turn dies in
turn one if retrieval fires against a generic gardening corpus. P0
acceptance is "20 hand-authored seed answers minimum" (plan §12) with
recognizable ``doc_type`` tags so ``scripts/yard_pro/deploy_ka.py`` can
build the Vector Search payloads correctly.

These tests are intentionally cheap (no Databricks dependencies) so
they run on every CI matrix combination.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

KA_ROOT = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "innovation_factory"
    / "backend"
    / "projects"
    / "yard_pro"
    / "ka_docs"
)

VALID_DOC_TYPES = {"plant_care", "almanac", "consumables", "playbook"}

# Matches the YAML-ish frontmatter Phase A introduces; we limit ourselves
# to plain `key: value` lines (no nested YAML, lessons §12 — KISS).
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _list_corpus_docs() -> list[Path]:
    return sorted(
        p for p in KA_ROOT.rglob("*.md")
        if p.name != "INDEX.md"
    )


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Same minimal parser the deploy script uses — keep them in sync."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    meta_text = match.group(1)
    out: dict[str, str] = {}
    for line in meta_text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


class TestCorpusShape:
    def test_corpus_root_exists(self):
        assert KA_ROOT.is_dir(), f"KA corpus root missing: {KA_ROOT}"

    def test_index_exists(self):
        """INDEX.md is the deploy script's authoritative table of contents."""
        assert (KA_ROOT / "INDEX.md").is_file(), "ka_docs/INDEX.md is required"

    def test_at_least_twenty_seed_answers(self):
        """Plan §7 risk callout + §12 P0 list: ≥ 20 hand-authored docs."""
        docs = _list_corpus_docs()
        assert len(docs) >= 20, (
            f"yard-pro KA corpus has only {len(docs)} docs; plan §7 + §12 "
            f"require ≥ 20 hand-authored seed answers. Risk callout #1."
        )

    def test_each_doc_carries_doc_type(self):
        """Every doc must carry a recognizable ``doc_type`` tag in
        frontmatter so deploy_ka.py can build correct Vector Search
        index payloads."""
        for doc in _list_corpus_docs():
            text = doc.read_text(encoding="utf-8")
            meta = _parse_frontmatter(text)
            assert "doc_type" in meta, (
                f"{doc.relative_to(KA_ROOT)} missing 'doc_type' frontmatter key"
            )
            assert meta["doc_type"] in VALID_DOC_TYPES, (
                f"{doc.relative_to(KA_ROOT)} has unknown doc_type "
                f"{meta['doc_type']!r}; expected one of {sorted(VALID_DOC_TYPES)}"
            )

    def test_each_doc_has_advisory_closer(self):
        """Plan §8 (AI security): every doc closes with an explicit
        advisory disclaimer so the coach response retains the
        'advisory only' framing even on near-verbatim returns."""
        for doc in _list_corpus_docs():
            text = doc.read_text(encoding="utf-8").lower()
            assert "advisory" in text, (
                f"{doc.relative_to(KA_ROOT)} is missing the 'advisory' "
                f"disclaimer required by plan §8."
            )

    @pytest.mark.parametrize("subdir,expected_doc_type", [
        ("plant_care", "plant_care"),
        ("regional_almanac", "almanac"),
        ("consumables", "consumables"),
        ("diagnostic_playbooks", "playbook"),
    ])
    def test_subdirs_have_consistent_doc_type(self, subdir, expected_doc_type):
        """Files in each subdirectory should declare the matching doc_type
        — sanity check against silent miscategorization."""
        folder = KA_ROOT / subdir
        if not folder.is_dir():
            pytest.skip(f"{subdir} folder absent")
        for doc in sorted(folder.glob("*.md")):
            meta = _parse_frontmatter(doc.read_text(encoding="utf-8"))
            assert meta.get("doc_type") == expected_doc_type, (
                f"{doc.relative_to(KA_ROOT)} declares doc_type="
                f"{meta.get('doc_type')!r}; expected {expected_doc_type!r} "
                f"(directory convention)"
            )


class TestIndexAndCorpusInSync:
    """Catch the failure mode where a doc is added or removed but
    INDEX.md isn't updated. ``deploy_ka.py`` reads INDEX.md, so drift
    would silently exclude content from the Vector Search index.
    """

    def _index_paths(self) -> list[tuple[str, str]]:
        index_text = (KA_ROOT / "INDEX.md").read_text(encoding="utf-8")
        row_re = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([a-z_]+)\s*\|")
        out: list[tuple[str, str]] = []
        for line in index_text.splitlines():
            m = row_re.match(line.strip())
            if m:
                out.append((m.group(1), m.group(2)))
        return out

    def test_index_lists_at_least_twenty_docs(self):
        rows = self._index_paths()
        assert len(rows) >= 20, (
            f"INDEX.md lists only {len(rows)} docs; ≥ 20 required."
        )

    def test_every_indexed_path_exists(self):
        for rel_path, _ in self._index_paths():
            assert (KA_ROOT / rel_path).is_file(), (
                f"INDEX.md references missing file: {rel_path}"
            )

    def test_every_doc_listed_in_index(self):
        listed = {p for p, _ in self._index_paths()}
        for doc in _list_corpus_docs():
            rel = doc.relative_to(KA_ROOT).as_posix()
            assert rel in listed, (
                f"{rel} exists on disk but is missing from INDEX.md — "
                f"deploy_ka.py will skip it."
            )

    def test_index_doc_types_are_recognized(self):
        for path, doc_type in self._index_paths():
            assert doc_type in VALID_DOC_TYPES, (
                f"INDEX.md declares doc_type {doc_type!r} for {path}; "
                f"expected one of {sorted(VALID_DOC_TYPES)}"
            )
