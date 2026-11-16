"""IFEval T36 (common/zadania.py, benchmarks/ifeval/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, RECIPE.md and the README type row (`ifeval`); the card's own counts (541
prompts, 834 instructions by prompt and by group); the type `ifeval` baseline b (`ewaluuj.bazy_proby` with
`baza="pusta"`: the empty answer only, never the most frequent "gold", which in IFEval is the unused
`doc_to_target: 0`). The instruction checkers live in lm-eval, so with lm-eval installed (.venv-eval) the installed
YAML is checked against the card's prompt and generation settings, and its `process_results` gives 0 in all four
metrics to an empty or blank answer and 1 to `OK` under `punctuation:no_comma`. Run: python tests/test_ifeval.py
(or pytest).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402
import ewaluuj as E  # noqa: E402  (research/common, on the path through wpis_benchmarku)

Z = W.Z
METRYKI = ("prompt_level_strict_acc", "inst_level_strict_acc", "prompt_level_loose_acc", "inst_level_loose_acc")


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "google/IFEval", "rewizja": "966cd89545d6b6acfd7638bc708b98261ca58e84", "nazwa_hf": None,
                  "split": "train", "metric": "prompt_level_strict_acc,none", "lm_eval": "ifeval", "rodzaj": "proba",
                  "klucz": "prompt_level_strict_acc", "baza": "pusta", "filtr": None, "klastry": None}
    meta, karta = W.sprawdz_wpis("T36", oczekiwane, shoty=0, typ="ifeval")
    assert ("| Metryka decyzyjna | `prompt_level_strict_acc` (odsetek promptów z wszystkimi instrukcjami spełnionymi "
            "w kryterium strict), 0-shot, pełny split `train`.") in karta
    assert "`zad.eval_docs` @ `966cd895`: 541)" in karta
    assert "`doc_to_text: prompt` (sam tekst pola `prompt`, bez prefiksu" in karta
    assert "`until: []`, `do_sample: false`, `temperature: 0.0`, `max_gen_toks: 1280`" in karta
    assert "Pusta odpowiedź: 0 z 541 = 0 w `prompt_level_strict_acc`" in karta


def test_card_counts_add_up():
    """541 prompts = 305 + 179 + 57; instructions 305 + 2*179 + 3*57 = 834 = sum of the nine groups."""
    karta = W.ZK.karta("T36").read_text(encoding="utf-8")
    assert "Prompty mają 834 instrukcje: 305 promptów z jedną, 179 z dwiema, 57 z trzema" in karta
    assert 305 + 179 + 57 == 541 and 305 + 2 * 179 + 3 * 57 == 834
    grupy = {"keywords": 163, "detectable_format": 157, "length_constraints": 143, "change_case": 89, "startend": 67,
             "punctuation": 66, "combination": 65, "detectable_content": 53, "language": 31}
    assert ", ".join(f"`{g}` {n}" for g, n in grupy.items()) in karta and sum(grupy.values()) == 834
    assert "(`agg_inst_level_acc` spłaszcza listy, mianownik 834)" in karta


class WezPierwsza:
    """lm-eval's `take_first`, the only filter of the default `none` ensemble every generate_until task has."""
    def apply(self, resps, docs):
        return [r[0] for r in resps]


class AtrapaIFEval:
    """Strict rule as in the card: a non-blank answer that passes every instruction; the one instruction here is
    "no comma". `doc_to_target` is the YAML's unused 0: the text "0" passes, so a `gen` baseline would pick it."""
    _filters = [type("Zespol", (), {"name": "none", "filters": [WezPierwsza]})()]
    doc_to_target = staticmethod(lambda d: 0)

    @staticmethod
    def process_results(doc, results):
        odp = results[0]
        return {"prompt_level_strict_acc": float(bool(odp.strip()) and "," not in odp)}


def test_empty_answer_baseline_ignores_the_unused_target():
    docs = [{"key": i, "prompt": f"Write {i} without commas", "instruction_id_list": ["punctuation:no_comma"],
             "kwargs": [{}]} for i in range(3)]
    bazy, szczegoly = E.bazy_proby(AtrapaIFEval(), Z.ZADANIA["T36"], docs)
    # b = empty answer only: "" fails the strict rule on every prompt -> 0; chance N/A, taken as 0
    assert bazy["majority_value"] == 0.0 and bazy["chance_value"] == 0.0
    assert szczegoly == {"baza": "pusta", "pusta": 0.0}
    # the same rows under `gen` would add the "most frequent gold" "0", which passes no_comma -> 1.0
    bazy_gen, _ = E.bazy_proby(AtrapaIFEval(), {**Z.ZADANIA["T36"], "baza": "gen"}, docs)
    assert bazy_gen["majority_value"] == 1.0


@pytest.mark.skipif(not W.MA_LM_EVAL, reason="needs lm-eval (.venv-eval): reads the installed ifeval YAML and checkers")
def test_installed_yaml_and_strict_rule(monkeypatch):
    import nltk
    monkeypatch.setattr(nltk, "download", lambda *a, **k: True)  # offline, as in test_przebieg_c
    cfg = Z._yaml("ifeval")
    assert cfg["doc_to_text"] == "prompt" and cfg["test_split"] == "train" and cfg["num_fewshot"] == 0
    assert cfg["generation_kwargs"] == {"until": [], "do_sample": False, "temperature": 0.0, "max_gen_toks": 1280}
    assert [m["metric"] for m in cfg["metric_list"]] == list(METRYKI)
    doc = {"key": 1, "prompt": "Say hi without commas.", "instruction_id_list": ["punctuation:no_comma"],
           "kwargs": [{}]}
    for pusta in ("", "  \n"):
        wynik = cfg["process_results"](doc, [pusta])
        assert [wynik[m] if not isinstance(wynik[m], list) else wynik[m][0] for m in METRYKI] == [0, 0, 0, 0]
    assert cfg["process_results"](doc, ["OK"])["prompt_level_strict_acc"] == 1
    assert cfg["process_results"](doc, ["OK, hi"])["prompt_level_strict_acc"] == 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
