"""DROP T39 (common/zadania.py, benchmarks/drop/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the 0-shot prompt of lm-eval `drop` (`{passage} {question}`, nothing else), the
gold answers built by `utils.process_docs` (number, else spans, else date), the decision metric `f1` (DROP bag F1 after
removing articles and punctuation, maximum over golds) on a stand-in model that generates fixed answers, and the
clusters: questions on one `passage` form one cluster (`+klastry`, SE K). Data: three invented questions, two on
one passage. Run: python tests/test_drop.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z, E = C.Z, C.E
P1, P2 = "The Bears scored 3 touchdowns in Warsaw.", "Rain delayed the game by an hour."
BRAK_DATY = {"day": "", "month": "", "year": ""}
PUSTE = {"number": [], "date": [], "spans": []}


def doc(i, passage, question, number="", spans=()):
    return {"section_id": f"s{i}", "query_id": f"q{i}", "passage": passage, "question": question,
            "answer": {"number": number, "date": BRAK_DATY, "spans": list(spans)}, "validated_answers": PUSTE}


DANE = [doc(0, P1, "How many touchdowns did the Bears score?", number="3"),
        doc(1, P1, "Where did the Bears play?", spans=["Warsaw"]),
        doc(2, P2, "How long was the delay in minutes?", number="60")]
# q0 " 3" = 3 -> F1 1; q1 "the city of Warsaw" -> bag {city, of, warsaw} against {warsaw}: P 1/3, R 1 -> F1 1/2;
# q2 " 45" against 60: numbers differ -> 0. f1 (1 + 1/2 + 0) / 3 = 1/2, em 1/3
ODP = {"How many": " 3", "Where": " the city of Warsaw", "How long": " 45"}


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T39"], ZK.karta("T39").read_text(encoding="utf-8")
    oczekiwane = {"repo": "EleutherAI/drop", "rewizja": "619386fc7ffe6dace3cc6d3483c69b164ebf6bf3",
                  "split": "validation", "metric": "f1,none", "klucz": "f1", "task": "drop", "lm_eval": "drop",
                  "rodzaj": "proba", "baza": "gen", "klastry": "passage"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0 and "shots" not in meta
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "`validation`, 0-shot, metryka `f1`, zadanie lm-eval `drop`, typ `ciagla +klastry` z klastrami `passage`" in karta
    assert "| Metryka decyzyjna | `f1` (średnia F1 po pytaniach), 0-shot, pełny split `validation`" in karta
    assert '`doc_to_text: "{{passage}} {{question}}"`' in karta and '`target_delimiter: ""`' in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T39"] == "drop"


def test_config_comes_from_the_lm_eval_yaml_with_the_card_revision():
    (wariant, cfg), = Z.konfiguracje("T39")
    assert wariant == "space" and cfg["task"] == "slayer_drop" and cfg["num_fewshot"] == 0
    assert cfg["doc_to_text"] == "{{passage}} {{question}}" and cfg["target_delimiter"] == ""
    assert cfg["generation_kwargs"]["until"] == ["."]
    assert cfg["dataset_kwargs"]["revision"] == "619386fc7ffe6dace3cc6d3483c69b164ebf6bf3"


def test_zero_shot_prompt_and_decision_metric_f1(tmp_path, monkeypatch):
    def gen(ctx):
        return next(v for k, v in ODP.items() if k in ctx)

    lm = C.AtrapaLM(gen=gen)
    obs, d = C.ocen("T39", {"drop": DANE}, lm, tmp_path, monkeypatch)
    assert sorted(lm.konteksty) == sorted(f"{x['passage']} {x['question']}" for x in DANE)
    assert d["glowna"]["metryka"] == "f1" and d["glowna"]["value"] == pytest.approx(1 / 2)
    assert obs["metric"] == "f1,none" and obs["value"] == pytest.approx(1 / 2) and obs["n_scored"] == 3


def test_clusters_are_passages():
    probki = [{"doc_id": i, "doc": d} for i, d in enumerate(DANE)]
    assert E.klastry_probek(Z.ZADANIA["T39"], probki) == [P1, P1, P2]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
