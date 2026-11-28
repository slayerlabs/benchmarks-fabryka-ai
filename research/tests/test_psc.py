"""PSC T27 (common/zadania.py, studies/2026-10-lm-eval-benchmarks/benchmarks/psc/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the 5-shot prompt of the copied OpenPL YAML `psc_mc.yaml` (5 bank demonstrations,
then the question; continuations ` Nie`, ` Tak`, gold = `label|int`, 1 = Tak), the decision metric: corpus binary F1
with positive class Tak, not `acc`, and the clusters: pairs with one `extract_text` form one cluster (SE from the
bootstrap over clusters). Data: invented texts; demonstrations go in as the YAML's train split
(test_polemo2.ocen_5shot). Without lm-eval (CI job `light`) only the checks that do not run it.
Run: python tests/test_psc.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402  (ZADANIA without lm-eval in the CI job `light`)
import ewaluuj as E  # noqa: E402  (common/ is on sys.path after wpis_benchmarku)

Z, ZK = W.Z, W.ZK
LM_EVAL = pytest.mark.skipif(not W.MA_LM_EVAL, reason="runs lm-eval: .venv-eval only")
WYBORY = ["Nie", "Tak"]
T1, T2 = "Sejm przyjął ustawę o szkołach.", "W Gdańsku otwarto nowy most."
DANE = [{"extract_text": T1, "summary_text": "Posłowie przegłosowali ustawę.", "label": 1},
        {"extract_text": T1, "summary_text": "Most w Gdańsku jest otwarty.", "label": 0},
        {"extract_text": T2, "summary_text": "Otwarto most w Gdańsku.", "label": 1},
        {"extract_text": T2, "summary_text": "Sejm przyjął budżet.", "label": 0}]
DEMO = [{"extract_text": f"Tekst przykładowy {i}.", "summary_text": f"Streszczenie {i}.", "label": i % 2}
        for i in range(7)]


def szablon(d):
    return (f'Tekst: "{d["extract_text"]}"\nPodsumowanie: "{d["summary_text"]}"\nPytanie: Czy podsumowanie dla '
            f'podanego tekstu jest poprawne?\nOdpowiedz krótko "Tak" lub "Nie". Prawidłowa odpowiedź:')


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "allegro/klej-psc", "rewizja": "9585582aef37e7747ef174b0ec3b74855da8bad2",
                  "split": "test", "metric": "f1,none", "klucz": "f1", "task": "polish_psc_multiple_choice",
                  "klastry": "extract_text", "yaml": "psc/lm_eval_tasks/polish_psc/psc_mc.yaml"}
    meta, karta = W.sprawdz_wpis("T27", oczekiwane, shoty=5, typ="f1-korpus +klastry +pl")
    assert meta["klasy_stale"]
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "psc_mc.yaml" in karta and '| Metryka decyzyjna | `f1` (korpusowe, binarne, klasa pozytywna "Tak" = 1)' in karta
    assert "split: `test`; n: 1078" in karta and "5-shot" in karta and "klastrach `extract_text`" in karta
    assert '`doc_to_choice: ["Nie", "Tak"]`' in karta and '`doc_to_target: "{{label|int}}"`' in karta
    assert '`Tekst: "{{extract_text}}"\\nPodsumowanie: "{{summary_text}}"\\n' in karta
    assert ZK.KATALOGI["T27"] == "psc"


# predictions Tak, Tak, Nie, Nie against gold 1, 0, 1, 0: acc 2/4 (= acc_norm, both options 3 characters);
# F1 for Tak: TP 1, FP 1, FN 1 -> 2*1 / (2*1 + 1 + 1) = 1/2
PRED = {"Posłowie": "Tak", "Most": "Tak", "Otwarto": "Nie", "Sejm": "Nie"}


@LM_EVAL
def test_five_shot_prompt_and_decision_metric_f1(tmp_path, monkeypatch):
    import test_polemo2 as P  # imports lm-eval, so only under LM_EVAL
    def ll(pytanie, kont):
        return -1.0 if kont.strip() == PRED[pytanie.split('"')[3].split()[0]] else -2.0

    roz, zadania, bank = P.ocen_5shot("T27", DANE, DEMO, ll, tmp_path, monkeypatch)
    for doc in DANE:
        kontekst = P.prompt_5shot(szablon, WYBORY, lambda d: d["label"], bank, doc)
        assert kontekst.count("Podsumowanie: ") == 6
        assert [k for c, k in zadania if c == kontekst] == [" Nie", " Tak"]
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(2 / 4) and space["acc_norm"]["value"] == pytest.approx(2 / 4)
    assert space["glowna"]["metryka"] == "f1" and space["glowna"]["value"] == pytest.approx(1 / 2)
    assert roz["metric"] == "f1,none" and roz["value"] == pytest.approx(1 / 2) and roz["n_scored"] == 4


def test_clusters_are_extract_texts():
    probki = [{"doc_id": i, "doc": d} for i, d in enumerate(DANE)]
    assert E.klastry_probek(Z.ZADANIA["T27"], probki) == [T1, T1, T2, T2]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
