"""PAWS-X (en) T48 (common/zadania.py, benchmarks/paws-en/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the prompt of lm-eval `paws_en` @ 6d2abda4: empty context and two whole-sentence
continuations ` {sentence1}, right? No, {sentence2}` and ` {sentence1}, right? Yes, {sentence2}` (gold = `label`,
1 = Yes = paraphrase), the decision metric `acc` (not `acc_norm`) on a stand-in model, and the clusters: rows that
share a sentence form one cluster (rule `zdania_paws`). Data: three invented pairs.
Without lm-eval (CI job `light`) only the checks that do not run it.
Run: python tests/test_paws_en.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402  (ZADANIA without lm-eval in the CI job `light`)
import ewaluuj as E  # noqa: E402  (common/ is on sys.path after wpis_benchmarku)

Z, ZK = W.Z, W.ZK
LM_EVAL = pytest.mark.skipif(not W.MA_LM_EVAL, reason="runs lm-eval: .venv-eval only")
DANE = [{"id": 1, "sentence1": "Ola met Ben in Kraków.", "sentence2": "Ben met Ola in Kraków.", "label": 1},
        {"id": 2, "sentence1": "Ola met Ben in Kraków.", "sentence2": "In Kraków Ola met Ben.", "label": 0},
        {"id": 3, "sentence1": "The bus left early.", "sentence2": "The early bus left.", "label": 0}]


def opcje(d):
    return [f" {d['sentence1']}, right? No, {d['sentence2']}", f" {d['sentence1']}, right? Yes, {d['sentence2']}"]


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "google-research-datasets/paws-x", "rewizja": "4cd8187c404bda33cb1f62b49b001115862acf37",
                  "nazwa_hf": "en", "split": "test", "metric": "acc,none", "task": "paws_en", "rodzaj": "mc",
                  "pole_id": "id", "klastry": "zdania_paws"}
    meta, karta = W.sprawdz_wpis("T48", oczekiwane, shoty=0, typ="mc +klastry")
    assert meta["klasy_stale"]
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "konfiguracja `en`, split `test`, 0-shot, metryka `acc`, zadanie lm-eval `paws_en`" in karta
    assert "| Metryka decyzyjna | `acc`, 0-shot" in karta
    assert "`doc_to_text: ''`" in karta and "`doc_to_target: label`" in karta
    assert ("`doc_to_choice: '{{[sentence1+\", right? No, \"+sentence2, sentence1+\", right? Yes, \"+sentence2]}}'`"
            in karta)
    assert ZK.KATALOGI["T48"] == "paws-en"


def test_config_is_the_card_template():
    (wariant, cfg), = Z.konfiguracje("T48")
    assert wariant == "space" and cfg["task"] == "slayer_paws_en" and cfg["num_fewshot"] == 0
    assert cfg["doc_to_text"] == "" and cfg["doc_to_target"] == "label"
    assert cfg["doc_to_choice"] == '{{[sentence1+", right? No, "+sentence2, sentence1+", right? Yes, "+sentence2]}}'
    assert cfg["dataset_kwargs"]["revision"] == "4cd8187c404bda33cb1f62b49b001115862acf37"


# Option lengths: row 1 No 58, Yes 59 characters. Row 1 gold Yes: acc No (-10 > -10.1), acc_norm Yes
# (-10.1/59 = -0.1712 > -10/58 = -0.1724); rows 2 and 3 gold No: No wins both (-1 > -5) -> acc 2/3, acc_norm 1
def ll(ctx, kont):
    if kont == opcje(DANE[0])[0]:
        return -10.0
    if kont == opcje(DANE[0])[1]:
        return -10.1
    return -1.0 if ", right? No, " in kont else -5.0


@LM_EVAL
def test_empty_context_sentence_options_and_decision_metric_acc(tmp_path, monkeypatch):
    import test_przebieg_c as C  # imports lm-eval, so only under LM_EVAL
    assert [len(o) for o in opcje(DANE[0])] == [58, 59]
    roz, zadania = C.ocen_loglik("T48", {"paws_en": DANE}, ll, tmp_path, monkeypatch)
    assert {c for c, _ in zadania} == {""}
    for d in DANE:
        assert [k for k in dict.fromkeys(k for _, k in zadania) if k in opcje(d)] == opcje(d)
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(2 / 3) and space["acc_norm"]["value"] == pytest.approx(1.0)
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(2 / 3) and roz["n_scored"] == 3


def test_rows_sharing_a_sentence_share_a_cluster():
    probki = [{"doc_id": i, "doc": d} for i, d in enumerate(DANE)]
    assert E.klastry_probek(Z.ZADANIA["T48"], probki) == [0, 0, 2]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
