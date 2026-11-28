"""The benchmark registry: names, packs, and selection. No evaluation stack needed."""

from pathlib import Path

import pytest

from codesota import catalog

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT.parent / "research" / "studies" / "2026-10-lm-eval-benchmarks" / "benchmarks"


def test_every_research_benchmark_directory_is_in_the_catalog_and_nothing_else() -> None:
    directories = {p.name for p in RESEARCH.iterdir() if p.is_dir() and not p.name.startswith("_")}
    assert set(catalog.CATALOG) == directories


def test_implemented_benchmarks_are_fully_specified() -> None:
    implemented = [b for b in catalog.CATALOG.values() if b.status != "not-implemented"]
    assert {b.id for b in implemented} == {b.id for b in catalog.IMPLEMENTED}
    for b in implemented:
        assert b.dataset is not None and b.scoring is not None, b.id
        assert b.dataset.n_population > 0, b.id
        assert len(b.dataset.revision) == 40, b.id
        assert b.evidence, b.id
        assert b.legacy_id, b.id
    for b in catalog.CATALOG.values():
        if b.status == "not-implemented":
            assert b.dataset is None and b.scoring is None and not b.evidence, b.id


def test_statuses() -> None:
    by_status = {s: sorted(b.id for b in catalog.CATALOG.values() if b.status == s) for s in catalog.STATUSES}
    assert by_status["verified"] == ["arc-easy", "lambada", "piqa", "winogrande"]
    assert len(by_status["needs-reference-check"]) == 9
    assert "hellaswag" in by_status["needs-reference-check"]  # reference reproduced 10-shot, protocol is 0-shot


def test_every_implemented_benchmark_has_a_size_and_the_size_packs_partition_them() -> None:
    implemented = {b.id for b in catalog.CATALOG.values() if b.status != "not-implemented"}
    assert set(catalog.COST) == implemented
    groups = catalog.packs()
    sizes = [set(groups.get(s, ())) for s in catalog.SIZES]
    assert set().union(*sizes) == implemented
    assert sum(len(s) for s in sizes) == len(implemented)
    assert "wsc273" in groups["small"] and "arc-easy" in groups["medium"] and groups["big"] == ("hellaswag",)
    assert catalog.Cost(10, catalog.SMALL_BELOW - 1).size == "small"
    assert catalog.Cost(10, catalog.SMALL_BELOW).size == "medium"
    assert catalog.Cost(10, catalog.BIG_FROM).size == "big"
    assert [b.id for b in catalog.select("@small,@big")][-1] == "hellaswag"


def test_legacy_ids_are_unique() -> None:
    legacy = [b.legacy_id for b in catalog.CATALOG.values() if b.legacy_id]
    assert len(legacy) == len(set(legacy))


def test_select_by_id_alias_and_legacy_id() -> None:
    assert [b.id for b in catalog.select("arc-easy")] == ["arc-easy"]
    assert [b.id for b in catalog.select("ARC_EASY, arce,T51")] == ["arc-easy"]
    assert [b.id for b in catalog.select(["wg", "t07", "piqa"])] == ["winogrande", "piqa"]


def test_select_packs_keep_order_and_drop_duplicates() -> None:
    verified = [b.id for b in catalog.select("@verified")]
    assert verified == ["arc-easy", "lambada", "piqa", "winogrande"]
    mixed = [b.id for b in catalog.select("piqa,@verified,hs")]
    assert mixed == ["piqa", "arc-easy", "lambada", "winogrande", "hellaswag"]
    assert len(catalog.select("all")) == len(catalog.CATALOG)
    assert len(catalog.select("@full-run-2026-11")) == 15
    assert {b.language for b in catalog.select("@pl")} == {"PL"}


def test_unknown_names_are_all_reported() -> None:
    with pytest.raises(catalog.SelectionError, match="unknown benchmark or pack: nope, @nothing"):
        catalog.select("arc-easy,nope,@nothing")
    with pytest.raises(catalog.SelectionError, match="no benchmark selected"):
        catalog.select(" , ")


def test_benchmarks_md_is_generated_from_the_catalog() -> None:
    assert (ROOT / "BENCHMARKS.md").read_text(encoding="utf-8") == catalog.markdown()
