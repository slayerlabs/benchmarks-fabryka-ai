"""Belebele (pol_Latn) T24 (common/zadania.py, benchmarks/belebele-pl/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the 5-shot prompt of the copied OpenPL YAML `belebele_mc.yaml` (5 demonstrations
from the bank drawn from the test split itself, then the question; continuations = space + letter ` A`..` D`, gold =
index of `correct_answer_num` in "1".."4"), and the decision metric `acc`. `acc_norm` equals `acc` (all options are
1 character, card "Ocena"), so the test checks the equality. The bank rule itself (bank out of scoring, panel
variant) is covered in test_przebieg_c.py. Data: 7 invented documents. Run: python tests/test_belebele_pl.py.
"""
import json
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z, M = C.Z, C.M
LITERY = ["A", "B", "C", "D"]
DANE = [{"flores_passage": f"Fragment numer {i}.", "question": f"Pytanie {i}?", "mc_answer1": "jeden",
         "mc_answer2": "dwa", "mc_answer3": "trzy", "mc_answer4": "cztery", "correct_answer_num": str(i % 4 + 1)}
        for i in range(7)]
BANK = [3, 4, 5, 0, 2]  # M.ranking_banku order of DANE (first 5); documents 1 and 6 are scored


def szablon(d):
    return (f'Fragment: "{d["flores_passage"]}"\nPytanie: "{d["question"]}"\nMożliwe odpowiedzi:\n'
            f'A - {d["mc_answer1"]}\nB - {d["mc_answer2"]}\nC - {d["mc_answer3"]}\nD - {d["mc_answer4"]}\n'
            f"Prawidłowa odpowiedź:")


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T24"], ZK.karta("T24").read_text(encoding="utf-8")
    oczekiwane = {"repo": "facebook/belebele", "rewizja": "7899cdfa4e1e0d733fd77c848e2c273cb1d32be2",
                  "nazwa_hf": "pol_Latn", "split": "test", "metric": "acc,none", "task": "polish_belebele_mc",
                  "yaml": "belebele-pl/lm_eval_tasks/polish_belebele/belebele_mc.yaml"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 5
    for k in ("repo", "rewizja", "nazwa_hf", "task"):
        assert oczekiwane[k] in karta, k
    assert "belebele_mc.yaml" in karta and "| Metryka decyzyjna | `acc` (pole `metric`" in karta
    assert "split: `test`" in karta and "5-shot" in karta and "dokumentów splitu `test`" in karta
    assert ('`Fragment: "{{flores_passage}}"\\nPytanie: "{{question}}"\\nMożliwe odpowiedzi:\\nA - {{mc_answer1}}'
            '\\nB - {{mc_answer2}}\\nC - {{mc_answer3}}\\nD - {{mc_answer4}}\\nPrawidłowa odpowiedź:`') in karta
    assert '`doc_to_choice` = `["A", "B", "C", "D"]`' in karta and '`" A"`…`" D"`' in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T24"] == "belebele-pl"


# the model answers B everywhere; scored doc 1 gold "2" = B hit, doc 6 gold "3" = C miss -> acc 1/2 = acc_norm
def test_five_shot_prompt_and_decision_metric_acc(tmp_path, monkeypatch):
    roz, zadania = C.ocen_loglik("T24", {"polish_belebele_mc": DANE}, lambda ctx, kont: -1.0 if kont == " B" else -2.0,
                                 tmp_path, monkeypatch)
    ids = [M.sha256_tekstu(json.dumps(d, sort_keys=True, ensure_ascii=False)) for d in DANE]
    assert M.ranking_banku("belebele", "polish_belebele_mc", ids)[:5] == BANK
    space = roz["dodatkowe"]["space"]
    assert space["demonstracje"] == {"polish_belebele_mc": [ids[i] for i in BANK]}
    demonstracje = [szablon(DANE[i]) + " " + LITERY[int(DANE[i]["correct_answer_num"]) - 1] for i in BANK]
    for i in (1, 6):
        kontekst = "\n\n".join(demonstracje + [szablon(DANE[i])])
        assert [k for c, k in zadania if c == kontekst] == [" A", " B", " C", " D"]
    assert {c.rsplit("\n\n", 1)[-1] for c, _ in zadania if c} == {szablon(DANE[1]), szablon(DANE[6])}
    assert space["acc"]["value"] == pytest.approx(1 / 2) and space["acc_norm"]["value"] == pytest.approx(1 / 2)
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(1 / 2) and roz["n_scored"] == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
