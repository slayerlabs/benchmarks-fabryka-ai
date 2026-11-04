"""common/zadania.py ZADANIA against tasks_50.json of the Space, field by field, for every task the run counts.

Reference: tests/dane/tasks_50_space_2d3d73f.json, the projection of `rows[]` of tasks_50.json at Space revision
2d3d73f5 (header: source URL, revision, git blob oid). Run: python tests/test_zgodnosc_space.py (or pytest).
"""
import json
import sys
from pathlib import Path

import pytest

KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "common"))
import zadania as Z  # noqa: E402

SPACE = json.loads((KORZEN / "tests" / "dane" / "tasks_50_space_2d3d73f.json").read_text(encoding="utf-8"))
WIERSZE = {r["id"]: r for r in SPACE["rows"]}
POZA_PRZEBIEGIEM = {"T37"}  # LLMzSzŁ: the Space task file is unpublished (benchmarks/llmzszl/README.md)
POLA = ("benchmark_id", "task", "family", "language", "split", "metric", "unit", "higher_is_better")


def test_projection_is_the_pinned_space_file():
    assert SPACE["rewizja_space"] == "2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9" in SPACE["zrodlo"]
    assert len(WIERSZE) == 50 and SPACE["protocol"] == "bench50-v0.3.1"


def test_zadania_cover_every_space_task_but_t37():
    assert set(Z.ZADANIA) == set(WIERSZE) - POZA_PRZEBIEGIEM


@pytest.mark.parametrize("task_id", sorted(Z.ZADANIA))
def test_entry_matches_space(task_id):
    meta, wiersz = Z.ZADANIA[task_id], WIERSZE[task_id]
    rozne = {p: (meta.get(p), wiersz[p]) for p in POLA if meta.get(p) != wiersz[p]}
    shots = meta.get("shots", meta.get("shoty", 0))  # (c) entries: `shots`, Polish YAML entries: `shoty`
    if shots != wiersz["shots"]:
        rozne["shots"] = (shots, wiersz["shots"])
    rewizje = {s["repo_id"]: s["revision"] for s in wiersz["source_revisions"]}
    if rewizje.get(meta["repo"]) != meta["rewizja"]:
        rozne["repo@rewizja"] = (f"{meta['repo']}@{meta['rewizja']}", rewizje)
    assert not rozne, rozne
    for wariant, cfg in Z.konfiguracje(task_id):  # the shot count the run passes to lm-eval
        assert (cfg.get("num_fewshot") or 0) == wiersz["shots"], (wariant, cfg.get("num_fewshot"))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
