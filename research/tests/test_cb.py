"""CommitmentBank T12 (common/zadania.py, benchmarks/cb/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the prompt `{premise}\nQuestion: {hypothesis}. True, False, or Neither?\nAnswer:`
with continuations ` True`, ` False`, ` Neither` (gold = `label`, 0 = True, 1 = False, 2 = Neither), and the decision
metric `acc` (not `acc_norm`) on a stand-in model with fixed log-likelihoods. Data: two invented pairs.
Without lm-eval (CI job `light`) only the checks that do not run it.
Run: python tests/test_cb.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402  (ZADANIA without lm-eval in the CI job `light`)
import ewaluuj as E  # noqa: E402  (common/ is on sys.path after wpis_benchmarku)

Z, ZK = W.Z, W.ZK
LM_EVAL = pytest.mark.skipif(not W.MA_LM_EVAL, reason="runs lm-eval: .venv-eval only")
DANE = [{"idx": 0, "premise": "Ann said the shop might be closed.", "hypothesis": "the shop is closed", "label": 2},
        {"idx": 1, "premise": "Tom never left the house.", "hypothesis": "Tom went out", "label": 1}]


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "aps/super_glue", "rewizja": "3de24cf8022e94f4ee4b9d55a6f539891524d646",
                  "nazwa_hf": "cb", "split": "validation", "metric": "acc,none", "task": "cb", "rodzaj": "mc",
                  "pole_id": "idx"}
    meta, karta = W.sprawdz_wpis("T12", oczekiwane, shoty=0, typ="mc")
    assert meta["klasy_stale"] and "klastry" not in meta  # card: 56 distinct premises, `+klastry` not needed
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "`cb`, split `validation`, n = 56, 0-shot, metryka `acc`, zadanie lm-eval `cb`" in karta
    assert "| Metryka decyzyjna | `acc`, 0-shot" in karta
    assert '`doc_to_text: "{{premise}}\\nQuestion: {{hypothesis}}. True, False, or Neither?\\nAnswer:"`' in karta
    assert "`doc_to_choice: ['True', 'False', 'Neither']`" in karta and "`doc_to_target: label`" in karta
    assert ZK.KATALOGI["T12"] == "cb"


def test_config_is_the_card_template():
    (wariant, cfg), = Z.konfiguracje("T12")
    assert wariant == "space" and cfg["task"] == "slayer_cb" and cfg["num_fewshot"] == 0
    assert cfg["doc_to_text"] == "{{premise}}\nQuestion: {{hypothesis}}. True, False, or Neither?\nAnswer:"
    assert cfg["doc_to_choice"] == ["True", "False", "Neither"] and cfg["doc_to_target"] == "label"
    assert cfg["dataset_kwargs"]["revision"] == "3de24cf8022e94f4ee4b9d55a6f539891524d646"


# lengths with the leading space: " True" 5, " False" 6, " Neither" 8.
# doc 1 gold Neither: acc True (-6 > -7 > -8), acc_norm Neither (-8/8 = -1 > -7/6 = -1.17 > -6/5 = -1.2);
# doc 2 gold False: False wins both (-1 > -3) -> acc 1/2, acc_norm 1
LL = {"Ann ": {" True": -6.0, " False": -7.0, " Neither": -8.0}, "Tom ": {" True": -3.0, " False": -1.0, " Neither": -3.0}}


@LM_EVAL
def test_prompt_choices_and_decision_metric_acc(tmp_path, monkeypatch):
    import test_przebieg_c as C  # imports lm-eval, so only under LM_EVAL
    roz, zadania = C.ocen_loglik("T12", {"cb": DANE}, lambda ctx, kont: 0.0 if ctx == "" else LL[ctx[:4]][kont],
                                 tmp_path, monkeypatch)
    assert [k for c, k in zadania if c == "Ann said the shop might be closed.\nQuestion: the shop is closed. True, "
            "False, or Neither?\nAnswer:"] == [" True", " False", " Neither"]
    assert [k for c, k in zadania if c == "Tom never left the house.\nQuestion: Tom went out. True, False, or Neither?"
            "\nAnswer:"] == [" True", " False", " Neither"]
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(1 / 2) and space["acc_norm"]["value"] == pytest.approx(1.0)
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(1 / 2) and roz["n_scored"] == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
