"""SST-2 T21 (common/zadania.py, studies/2026-10-lm-eval-benchmarks/benchmarks/sst2/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card (GLUE `sst2`, split `validation`: the `test` labels are -1), the prompt
`{sentence}\nQuestion: Is this sentence positive or negative?\nAnswer:` with continuations ` negative`, ` positive`
(gold = `label`, 1 = positive), and the decision metric `acc` on a stand-in model that always answers positive.
Data: three invented sentences. Without lm-eval (CI job `light`) only the checks that do not run it.
Run: python tests/test_sst2.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402  (ZADANIA without lm-eval in the CI job `light`)
import ewaluuj as E  # noqa: E402  (common/ is on sys.path after wpis_benchmarku)

Z, ZK = W.Z, W.ZK
LM_EVAL = pytest.mark.skipif(not W.MA_LM_EVAL, reason="runs lm-eval: .venv-eval only")
DANE = [{"idx": 0, "sentence": "a warm , funny film", "label": 1},
        {"idx": 1, "sentence": "dull and far too long", "label": 0},
        {"idx": 2, "sentence": "the plot never takes off", "label": 0}]


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "nyu-mll/glue", "rewizja": "bcdcba79d07bc864c1c254ccfcedcce55bcc9a8c",
                  "nazwa_hf": "sst2", "split": "validation", "metric": "acc,none", "task": "sst2", "rodzaj": "mc",
                  "pole_id": "idx"}
    meta, karta = W.sprawdz_wpis("T21", oczekiwane, shoty=0, typ="mc")
    assert meta["klasy_stale"] and "klastry" not in meta
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "| Dane: split w Space/repo | split: `validation`; n: 872;" in karta and "0-shot" in karta
    assert "| Metryka decyzyjna | `acc` (pole `metric`" in karta and "wpis `T21` w `common/zadania.py`: `acc,none`" in karta
    assert "`doc_to_text` = `{{sentence}}\\nQuestion: Is this sentence positive or negative?\\nAnswer:`" in karta
    assert '`doc_to_choice` = `["negative", "positive"]`' in karta and "`doc_to_target` = `label`" in karta
    assert ZK.KATALOGI["T21"] == "sst2"


def test_config_is_the_card_template():
    (wariant, cfg), = Z.konfiguracje("T21")
    assert wariant == "space" and cfg["task"] == "slayer_sst2" and cfg["num_fewshot"] == 0
    assert cfg["doc_to_text"] == "{{sentence}}\nQuestion: Is this sentence positive or negative?\nAnswer:"
    assert cfg["doc_to_choice"] == ["negative", "positive"] and cfg["doc_to_target"] == "label"
    assert cfg["dataset_kwargs"]["revision"] == "bcdcba79d07bc864c1c254ccfcedcce55bcc9a8c"


# the model answers positive everywhere; golds 1, 0, 0 -> acc 1/3 (= acc_norm: both options 9 characters)
@LM_EVAL
def test_prompt_choices_and_decision_metric_acc(tmp_path, monkeypatch):
    import test_przebieg_c as C  # imports lm-eval, so only under LM_EVAL
    roz, zadania = C.ocen_loglik("T21", {"sst2": DANE}, lambda ctx, kont: -1.0 if kont == " positive" else -2.0,
                                 tmp_path, monkeypatch)
    for d in DANE:
        kontekst = f"{d['sentence']}\nQuestion: Is this sentence positive or negative?\nAnswer:"
        assert [k for c, k in zadania if c == kontekst] == [" negative", " positive"]
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(1 / 3) and space["acc_norm"]["value"] == pytest.approx(1 / 3)
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(1 / 3) and roz["n_scored"] == 3


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
