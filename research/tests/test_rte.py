"""RTE (SuperGLUE) T15 (common/zadania.py, benchmarks/rte/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card (lm-eval task `sglue_rte`, not the GLUE `rte`), the prompt
`{premise}\nQuestion: {hypothesis} True or False?\nAnswer:` (no full stop added after the hypothesis) with continuations
` True`, ` False` (gold = `label`, 0 = entailment = True), and the decision metric `acc` (not `acc_norm`) on a
stand-in model. Data: two invented pairs. Run: python tests/test_rte.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z
DANE = [{"idx": 0, "premise": "The museum opened in 1990.", "hypothesis": "The museum is closed.", "label": 1},
        {"idx": 1, "premise": "Rain fell all day in Oslo.", "hypothesis": "It rained in Oslo.", "label": 0}]


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T15"], ZK.karta("T15").read_text(encoding="utf-8")
    oczekiwane = {"repo": "aps/super_glue", "rewizja": "3de24cf8022e94f4ee4b9d55a6f539891524d646",
                  "nazwa_hf": "rte", "split": "validation", "metric": "acc,none", "task": "sglue_rte", "rodzaj": "mc",
                  "pole_id": "idx"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0
    assert meta["klasy_stale"] and "klastry" not in meta
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "`rte`, split `validation`, 0-shot, metryka `acc`, zadanie lm-eval `sglue_rte`" in karta
    assert "| Metryka decyzyjna | `acc`, 0-shot" in karta
    assert '`doc_to_text: "{{premise}}\\nQuestion: {{hypothesis}} True or False?\\nAnswer:"`' in karta
    assert "`doc_to_choice: ['True', 'False']`" in karta and "`doc_to_target: label`" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T15"] == "rte"


def test_config_is_the_card_template():
    (wariant, cfg), = Z.konfiguracje("T15")
    assert wariant == "space" and cfg["task"] == "slayer_rte" and cfg["num_fewshot"] == 0
    assert cfg["doc_to_text"] == "{{premise}}\nQuestion: {{hypothesis}} True or False?\nAnswer:"
    assert cfg["doc_to_choice"] == ["True", "False"] and cfg["doc_to_target"] == "label"
    assert cfg["dataset_kwargs"]["revision"] == "3de24cf8022e94f4ee4b9d55a6f539891524d646"


# " True" 5 characters, " False" 6. doc 1 gold False: acc True (-5 > -5.5), acc_norm False (-5.5/6 = -0.92 > -1);
# doc 2 gold True: True wins both (-1 > -3) -> acc 1/2, acc_norm 1
LL = {"The ": {" True": -5.0, " False": -5.5}, "Rain": {" True": -1.0, " False": -3.0}}


def test_prompt_choices_and_decision_metric_acc(tmp_path, monkeypatch):
    roz, zadania = C.ocen_loglik("T15", {"sglue_rte": DANE},
                                 lambda ctx, kont: 0.0 if ctx == "" else LL[ctx[:4]][kont], tmp_path, monkeypatch)
    assert [k for c, k in zadania if c == "The museum opened in 1990.\nQuestion: The museum is closed. True or False?"
            "\nAnswer:"] == [" True", " False"]
    assert [k for c, k in zadania if c == "Rain fell all day in Oslo.\nQuestion: It rained in Oslo. True or False?"
            "\nAnswer:"] == [" True", " False"]
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(1 / 2) and space["acc_norm"]["value"] == pytest.approx(1.0)
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(1 / 2) and roz["n_scored"] == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
