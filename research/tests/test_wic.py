"""WiC T13 (common/zadania.py, benchmarks/wic/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the prompt `Sentence 1: ...\nSentence 2: ...\nQuestion: Is the word '{word}' used
in the same way in the two sentences above?\nAnswer:` where the word is the slice `sentence1[start1:end1]` (not the
`word` field, which is the lemma), continuations ` no`, ` yes` (gold = `label`, 1 = yes), and the decision metric
`acc` (not `acc_norm`) on a stand-in model. Data: two invented pairs. Run: python tests/test_wic.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z
# "He sat on the " = 14 characters, "She " = 4: the slices are "bank" and "plays"; `word` holds the lemma
DANE = [{"idx": 0, "word": "bank", "sentence1": "He sat on the bank of the river.", "start1": 14, "end1": 18,
         "sentence2": "The river bank was muddy.", "start2": 10, "end2": 14, "label": 1},
        {"idx": 1, "word": "play", "sentence1": "She plays the piano.", "start1": 4, "end1": 9,
         "sentence2": "The play ended late.", "start2": 4, "end2": 8, "label": 0}]


def prompt(d, slowo):
    return (f"Sentence 1: {d['sentence1']}\nSentence 2: {d['sentence2']}\nQuestion: Is the word '{slowo}' used in the "
            "same way in the two sentences above?\nAnswer:")


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T13"], ZK.karta("T13").read_text(encoding="utf-8")
    oczekiwane = {"repo": "aps/super_glue", "rewizja": "3de24cf8022e94f4ee4b9d55a6f539891524d646",
                  "nazwa_hf": "wic", "split": "validation", "metric": "acc,none", "task": "wic", "rodzaj": "mc",
                  "pole_id": "idx"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0
    assert meta["klasy_stale"] and "klastry" not in meta
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "`wic`, split `validation`, 0-shot, metryka `acc`, zadanie lm-eval `wic`" in karta
    assert "| Metryka decyzyjna | `acc`, 0-shot" in karta
    assert ("`doc_to_text: \"Sentence 1: {{sentence1}}\\nSentence 2: {{sentence2}}\\nQuestion: Is the word "
            "'{{sentence1[start1:end1]}}' used in the same way in the two sentences above?\\nAnswer:\"`") in karta
    assert "`doc_to_choice: ['no', 'yes']`" in karta and "`doc_to_target: label`" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T13"] == "wic"


def test_config_is_the_card_template():
    (wariant, cfg), = Z.konfiguracje("T13")
    assert wariant == "space" and cfg["task"] == "slayer_wic" and cfg["num_fewshot"] == 0
    assert cfg["doc_to_text"] == ("Sentence 1: {{sentence1}}\nSentence 2: {{sentence2}}\nQuestion: Is the word "
                                  "'{{sentence1[start1:end1]}}' used in the same way in the two sentences above?\nAnswer:")
    assert cfg["doc_to_choice"] == ["no", "yes"] and cfg["doc_to_target"] == "label"
    assert cfg["dataset_kwargs"]["revision"] == "3de24cf8022e94f4ee4b9d55a6f539891524d646"


# " no" 3 characters, " yes" 4. doc 1 gold yes: acc no (-3 > -3.6), acc_norm yes (-3.6/4 = -0.9 > -3/3 = -1);
# doc 2 gold no: no wins both (-1 > -4) -> acc 1/2, acc_norm 1
LL = {"bank": {" no": -3.0, " yes": -3.6}, "plays": {" no": -1.0, " yes": -4.0}}


def test_prompt_word_slice_and_decision_metric_acc(tmp_path, monkeypatch):
    def ll(ctx, kont):
        return 0.0 if ctx == "" else LL["bank" if "'bank'" in ctx else "plays"][kont]

    roz, zadania = C.ocen_loglik("T13", {"wic": DANE}, ll, tmp_path, monkeypatch)
    assert [k for c, k in zadania if c == prompt(DANE[0], "bank")] == [" no", " yes"]
    assert [k for c, k in zadania if c == prompt(DANE[1], "plays")] == [" no", " yes"]  # slice, not the lemma "play"
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(1 / 2) and space["acc_norm"]["value"] == pytest.approx(1.0)
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(1 / 2) and roz["n_scored"] == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
