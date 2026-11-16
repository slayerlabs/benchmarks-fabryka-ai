"""PROST T20 (common/zadania.py, benchmarks/prost/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card (dataset revision and the parquet revision), the lm-eval `prost` prompt
`{context}\nQuestion: {ex_question}\nAnswer:` with continuations = space + the text of fields A, B, C, D (gold =
`label`), and the decision metric `acc_norm` (not `acc`) on a stand-in model. Data: two invented questions.
Without lm-eval (CI job `light`) only the checks that do not run it.
Run: python tests/test_prost.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402  (ZADANIA without lm-eval in the CI job `light`)
import ewaluuj as E  # noqa: E402  (common/ is on sys.path after wpis_benchmarku)

Z, ZK = W.Z, W.ZK
LM_EVAL = pytest.mark.skipif(not W.MA_LM_EVAL, reason="runs lm-eval: .venv-eval only")
OPCJE = {"A": "ball", "B": "brick", "C": "box", "D": "toaster"}
DANE = [{"context": "A ball, a brick, a box and a toaster sit on a table.", "ex_question": "Which is the heaviest?",
         "question": "The [MASK] is the heaviest.", **OPCJE, "label": 3, "name": "mass", "group": "g"},
        {"context": "Four things lie on a slope.", "ex_question": "Which rolls the easiest?",
         "question": "The [MASK] rolls the easiest.", **OPCJE, "label": 0, "name": "rolling", "group": "g"}]


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "corypaik/prost", "rewizja": "b3efebf08969fc19335ba894353316878b6fa493",
                  "rewizja_parquet": "0e475b574d98e7d79de2064252dd2fb75bcaa0a8", "nazwa_hf": "default",
                  "split": "test", "metric": "acc_norm,none", "klucz": "acc_norm", "task": "prost", "rodzaj": "mc"}
    meta, karta = W.sprawdz_wpis("T20", oczekiwane, shoty=0, typ="mc")
    assert meta["klasy_stale"] and "klastry" not in meta
    for k in ("repo", "rewizja", "rewizja_parquet"):
        assert oczekiwane[k] in karta, k
    assert "split `test`, 0-shot, metryka `acc_norm`, prompt zadania lm-eval" in karta
    assert "| Metryka decyzyjna | `acc_norm`, 0-shot" in karta
    assert '`doc_to_text: "{{context}}\\nQuestion: {{ex_question}}\\nAnswer:"`' in karta
    assert '`doc_to_choice: "{{[A, B, C, D]}}"`' in karta and "`doc_to_target: label`" in karta
    assert ZK.KATALOGI["T20"] == "prost"


def test_config_is_the_card_template():
    (wariant, cfg), = Z.konfiguracje("T20")
    assert wariant == "space" and cfg["task"] == "slayer_prost" and cfg["num_fewshot"] == 0
    assert cfg["doc_to_text"] == "{{context}}\nQuestion: {{ex_question}}\nAnswer:"
    assert cfg["doc_to_choice"] == "{{[A, B, C, D]}}" and cfg["doc_to_target"] == "label"


# lengths with the leading space: " ball" 5, " brick" 6, " box" 4, " toaster" 8.
# q1 gold toaster: acc ball (-6 is the highest), acc_norm toaster (-8/8 = -1 > -7/6 = -1.17 > -6/5 = -1.2 > -9/4);
# q2 gold ball: ball wins both (-1 against -5) -> acc 1/2, acc_norm 1
LL = {"A ba": {" ball": -6.0, " brick": -7.0, " box": -9.0, " toaster": -8.0},
      "Four": {" ball": -1.0, " brick": -5.0, " box": -5.0, " toaster": -5.0}}


@LM_EVAL
def test_prompt_choices_and_decision_metric_acc_norm(tmp_path, monkeypatch):
    import test_przebieg_c as C  # imports lm-eval, so only under LM_EVAL
    roz, zadania = C.ocen_loglik("T20", {"prost": DANE}, lambda ctx, kont: 0.0 if ctx == "" else LL[ctx[:4]][kont],
                                 tmp_path, monkeypatch)
    for d in DANE:
        kontekst = f"{d['context']}\nQuestion: {d['ex_question']}\nAnswer:"
        assert [k for c, k in zadania if c == kontekst] == [" ball", " brick", " box", " toaster"]
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(1 / 2) and space["acc_norm"]["value"] == pytest.approx(1.0)
    assert roz["metric"] == "acc_norm,none" and roz["value"] == pytest.approx(1.0) and roz["n_scored"] == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
