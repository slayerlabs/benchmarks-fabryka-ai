"""ANLI round 3 T16 (common/zadania.py, benchmarks/anli-r3/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the prompt `{premise}\nQuestion: {hypothesis} True, False, or Neither?\nAnswer:`
with continuations in the order ` True`, ` Neither`, ` False` (not the order of the prompt; gold = `label`, 0 =
entailment = True, 1 = neutral = Neither, 2 = contradiction = False), the decision metric `acc` (not `acc_norm`) on a
stand-in model, and the clusters: questions sharing one `premise` form one cluster (`+klastry`, SE K).
Data: three invented pairs, two on one premise. Without lm-eval (CI job `light`) only the checks that do not run it.
Run: python tests/test_anli_r3.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402  (ZADANIA without lm-eval in the CI job `light`)
import ewaluuj as E  # noqa: E402  (common/ is on sys.path after wpis_benchmarku)

Z, ZK = W.Z, W.ZK
LM_EVAL = pytest.mark.skipif(not W.MA_LM_EVAL, reason="runs lm-eval: .venv-eval only")
P1, P2 = "Mia grew up in Lyon and moved to Rome.", "Kai owns two dogs."
DANE = [{"uid": "a", "premise": P1, "hypothesis": "Mia speaks Italian.", "label": 1, "reason": ""},
        {"uid": "b", "premise": P1, "hypothesis": "Mia never lived in France.", "label": 2, "reason": ""},
        {"uid": "c", "premise": P2, "hypothesis": "Kai has pets.", "label": 0, "reason": ""}]


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "facebook/anli", "rewizja": "8e4813d81f46d313dac7892e1c28076917cfcdf9",
                  "nazwa_hf": "plain_text", "split": "test_r3", "metric": "acc,none", "task": "anli_r3",
                  "rodzaj": "mc", "klastry": "premise", "pole_id": "uid"}
    meta, karta = W.sprawdz_wpis("T16", oczekiwane, shoty=0, typ="mc +klastry")
    assert meta["klasy_stale"]
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "`plain_text`, split `test_r3`, 0-shot, metryka `acc`, zadanie lm-eval `anli_r3`" in karta
    assert '`klastry="premise"`' in karta and "| Metryka decyzyjna | `acc`, 0-shot" in karta
    assert '`doc_to_text: "{{premise}}\\nQuestion: {{hypothesis}} True, False, or Neither?\\nAnswer:"`' in karta
    assert '`doc_to_choice: ["True", "Neither", "False"]`' in karta
    assert "`doc_to_target: \"{{['True', 'Neither', 'False'][label]}}\"`" in karta
    assert ZK.KATALOGI["T16"] == "anli-r3"


def test_config_is_the_card_template():
    (wariant, cfg), = Z.konfiguracje("T16")
    assert wariant == "space" and cfg["task"] == "slayer_anli_r3" and cfg["num_fewshot"] == 0
    assert cfg["doc_to_text"] == "{{premise}}\nQuestion: {{hypothesis}} True, False, or Neither?\nAnswer:"
    assert cfg["doc_to_choice"] == ["True", "Neither", "False"]
    assert cfg["doc_to_target"] == "{{['True', 'Neither', 'False'][label]}}"
    assert cfg["dataset_kwargs"]["revision"] == "8e4813d81f46d313dac7892e1c28076917cfcdf9"


# " True" 5 characters, " Neither" 8, " False" 6.
# a gold Neither: acc True (-6 > -7 > -8), acc_norm Neither (-8/8 = -1 > -7/6 > -6/5); b gold False, c gold True:
# the gold wins both (-1 > -3) -> acc 2/3, acc_norm 1
LL = {"Mia speaks": {" True": -6.0, " Neither": -8.0, " False": -7.0},
      "Mia never": {" True": -3.0, " Neither": -3.0, " False": -1.0},
      "Kai has": {" True": -1.0, " Neither": -3.0, " False": -3.0}}


def ll(ctx, kont):
    if ctx == "":
        return 0.0
    hipoteza = ctx.split("Question: ")[1]
    return next(v for k, v in LL.items() if hipoteza.startswith(k))[kont]


@LM_EVAL
def test_prompt_choice_order_and_decision_metric_acc(tmp_path, monkeypatch):
    import test_przebieg_c as C  # imports lm-eval, so only under LM_EVAL
    roz, zadania = C.ocen_loglik("T16", {"anli_r3": DANE}, ll, tmp_path, monkeypatch)
    for d in DANE:
        kontekst = f"{d['premise']}\nQuestion: {d['hypothesis']} True, False, or Neither?\nAnswer:"
        assert [k for c, k in zadania if c == kontekst] == [" True", " Neither", " False"]
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(2 / 3) and space["acc_norm"]["value"] == pytest.approx(1.0)
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(2 / 3) and roz["n_scored"] == 3


def test_clusters_are_premises():
    probki = [{"doc_id": i, "doc": d} for i, d in enumerate(DANE)]
    assert E.klastry_probek(Z.ZADANIA["T16"], probki) == [P1, P1, P2]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
