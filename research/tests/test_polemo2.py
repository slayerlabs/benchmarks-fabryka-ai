"""PolEmo 2.0-IN T22 (common/zadania.py, benchmarks/polemo2/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the 5-shot prompt of the copied OpenPL YAML `polemo2_in_mc.yaml` (5 demonstrations
from the bank, METODOLOGIA "Przykłady few-shot", then the question; continuations = space + sentiment name, gold =
index of the label in `__label__meta_zero/minus_m/plus_m/amb`, an order other than the option texts), and the decision
metric `acc` (not `acc_norm`) on a stand-in model. Data: invented opinions.

GOTCHA: the local source (`zadania._zrodlo`, "lokalne") carries only a test file, while the YAML takes demonstrations
from its `training_split: train`; without a train file lm-eval stops with KeyError 'train'. `ocen_5shot` adds the demo
file as that split, so the bank is drawn as on HF. Also used by test_8tags, test_dyk and test_ppc.
Run: python tests/test_polemo2.py (or pytest).
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


def ocen_5shot(task_id, docs, demo, ll, tmp_path, monkeypatch):
    """`ll(question prompt, cont)` -> loglik; returns (results entry, requests, bank documents in prompt order)."""
    meta = Z.ZADANIA[task_id]
    zrodlo = Z._zrodlo

    def z_treningiem(t, m, rodzaj):
        pola = zrodlo(t, m, rodzaj)
        pola["dataset_kwargs"]["data_files"]["train"] = str(Z.DANE_TESTOWE / f"{m['task']}_demo.jsonl")
        return pola

    monkeypatch.setattr(Z, "_zrodlo", z_treningiem)
    roz, zadania = C.ocen_loglik(task_id, {meta["task"]: docs, f"{meta['task']}_demo": demo},
                                 lambda ctx, kont: 0.0 if ctx == "" else ll(ctx.rsplit("\n\n", 1)[-1], kont),
                                 tmp_path, monkeypatch)
    ids = [M.sha256_tekstu(json.dumps(d, sort_keys=True, ensure_ascii=False)) for d in demo]
    kolejnosc = M.ranking_banku(meta["benchmark_id"], meta["task"], ids)[:5]
    assert roz["dodatkowe"]["space"]["demonstracje"] == {meta["task"]: [ids[i] for i in kolejnosc]}
    return roz, zadania, [demo[i] for i in kolejnosc]


def prompt_5shot(szablon, wybory, zloty, bank, doc):
    """5 demonstrations (prompt + space + gold option) and the question, separated by an empty line."""
    return "\n\n".join([szablon(d) + " " + wybory[zloty(d)] for d in bank] + [szablon(doc)])


ETYKIETY = ["__label__meta_zero", "__label__meta_minus_m", "__label__meta_plus_m", "__label__meta_amb"]
WYBORY = ["Neutralny", "Negatywny", "Pozytywny", "Niejednoznaczny"]
DANE = [{"sentence": "Hotel ładny, ale obsługa różnie.", "target": "__label__meta_amb"},
        {"sentence": "Lekarz był niemiły i spóźniony.", "target": "__label__meta_minus_m"},
        {"sentence": "Świetna szkoła, polecam.", "target": "__label__meta_plus_m"}]
DEMO = [{"sentence": f"Opinia przykładowa {i}.", "target": ETYKIETY[i % 4]} for i in range(7)]


def szablon(d):
    return (f'Opinia: "{d["sentence"]}"\nOkreśl sentyment podanej opinii: Neutralny, Negatywny, Pozytywny, '
            f"Niejednoznaczny.\nSentyment:")


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T22"], ZK.karta("T22").read_text(encoding="utf-8")
    oczekiwane = {"repo": "allegro/klej-polemo2-in", "rewizja": "9843af31facd613eb091deaa4141df4331d4f918",
                  "split": "test", "metric": "acc,none", "task": "polemo2_in_multiple_choice",
                  "yaml": "polemo2/lm_eval_tasks/polemo2/polemo2_in_mc.yaml"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 5
    for k in ("repo", "rewizja", "task"):
        assert oczekiwane[k] in karta, k
    assert "polemo2_in_mc.yaml" in karta and "| Metryka decyzyjna | `acc` (trafność" in karta
    assert "split: `test`" in karta and "5-shot" in karta
    assert '`["Neutralny","Negatywny","Pozytywny","Niejednoznaczny"]`' in karta
    assert "`Opinia: \"{{sentence}}\"`" in karta and "`Sentyment:`" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T22"] == "polemo2"


# len: Neutralny 9, Negatywny 9, Pozytywny 9, Niejednoznaczny 15.
# q1 gold amb (Niejednoznaczny): acc Neutralny (-4 > -6), acc_norm Niejednoznaczny (-6/15 = -0.4 > -4/9 = -0.444);
# q2 gold minus_m -> Negatywny (index 1) and q3 gold plus_m -> Pozytywny (index 2) win both -> acc 2/3, acc_norm 1
LL = {"Hotel": {"Neutralny": -4.0, "Niejednoznaczny": -6.0}, "Lekarz": {"Negatywny": -1.0},
      "Świetna": {"Pozytywny": -1.0}}


def test_five_shot_prompt_and_decision_metric_acc(tmp_path, monkeypatch):
    def ll(pytanie, kont):
        return LL[pytanie.split('"')[1].split()[0]].get(kont.strip(), -9.0)

    roz, zadania, bank = ocen_5shot("T22", DANE, DEMO, ll, tmp_path, monkeypatch)
    for doc in DANE:
        kontekst = prompt_5shot(szablon, WYBORY, lambda d: ETYKIETY.index(d["target"]), bank, doc)
        assert kontekst.count("Opinia: ") == 6
        assert [k for c, k in zadania if c == kontekst] == [" " + w for w in WYBORY]
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(2 / 3) and space["acc_norm"]["value"] == pytest.approx(1.0)
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(2 / 3) and roz["n_scored"] == 3


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
