"""KLEJ NKJP-NER T29 (common/zadania.py, benchmarks/klej-ner/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, RECIPE.md and the README type row; the prompt, the six choices and the
label -> index map of the copied fork YAML (`klej_ner_mc.yaml`, read as text: no pyyaml in CI light) as the card
writes them; `acc` against the auxiliary `acc_norm` (loglik over the choice length in characters, the card's
23, 13, 11, 17, 4, 18) through `metryki.oceny_mc`; the baselines from the card's label counts through
`metryki.bazy_mc` (b = 705 / 2058, `Nazwa miejsca`). With lm-eval installed (.venv-eval) the copied YAML is parsed
with the repo loader. Run: python tests/test_klej_ner.py (or pytest).
"""
import ast
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402
import metryki as M  # noqa: E402  (common/ is on sys.path after wpis_benchmarku)

Z = W.Z
YAML = W.KORZEN / "benchmarks" / "klej-ner" / "lm_eval_tasks" / "polish_klej_ner" / "klej_ner_mc.yaml"
TEKST_YAML = YAML.read_text(encoding="utf-8")


def pole(nazwa):
    """The raw value of a top-level `nazwa:` line of the copied YAML."""
    trafienia = re.findall(rf"^{nazwa}: (.*)$", TEKST_YAML, re.M)
    assert len(trafienia) == 1, nazwa
    return trafienia[0]


PROMPT = json.loads(pole("doc_to_text"))  # a YAML double-quoted string with \" and \n only: JSON reads it the same
WYBORY = json.loads(pole("doc_to_choice"))
MAPA = ast.literal_eval(re.fullmatch(r'"\{\{(\{.*\})\.get\(target\)\}\}"', pole("doc_to_target")).group(1))
# test split label counts, card row "Dane: split w Space/repo"
ETYKIETY_TESTU = {"placeName": 705, "noEntity": 500, "persName": 372, "orgName": 237, "time": 143, "geogName": 101}


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "allegro/klej-nkjp-ner", "rewizja": "bfae4047738b985bc2ad533d339dd89c3f7de00d",
                  "split": "test", "metric": "acc,none", "rodzaj": "mc", "klasy_stale": True,
                  "task": "polish_klej_ner_multiple_choice", "klastry": "sentence",
                  "yaml": "klej-ner/lm_eval_tasks/polish_klej_ner/klej_ner_mc.yaml"}
    meta, karta = W.sprawdz_wpis("T29", oczekiwane, shoty=5, typ="mc +klastry +pl")
    assert "| Metryka decyzyjna | `acc`. `acc_norm` jest pomocnicza. |" in karta
    assert "split: test; n: 2058;" in karta
    assert ("Rozkład etykiet testu: 705 `placeName`, 500 `noEntity`, 372 `persName`, 237 `orgName`, 143 `time`, "
            "101 `geogName`.") in karta
    assert "`output_type: multiple_choice`, 5-shot." in karta
    # the card writes the prompt with \n as two characters and the quotes unescaped
    assert f"`doc_to_text`: `{PROMPT.replace(chr(10), chr(92) + 'n')}`" in karta
    assert f"`doc_to_choice`: `{json.dumps(WYBORY, ensure_ascii=False)}`" in karta
    assert f"`doc_to_target`: `{json.loads(pole('doc_to_target'))}`" in karta


def test_label_map_follows_the_choice_order():
    """Each label points at the choice the prompt names for it; the prompt lists the choices in the same order."""
    nazwy = {"noEntity": "Brak nazwanej jednostki", "placeName": "Nazwa miejsca", "persName": "Nazwa osoby",
             "orgName": "Nazwa organizacji", "time": "Czas", "geogName": "Nazwa geograficzna"}
    assert {etykieta: WYBORY[i] for etykieta, i in MAPA.items()} == nazwy
    assert sorted(MAPA.values()) == list(range(6)) and set(MAPA) == set(ETYKIETY_TESTU)
    assert f"Możliwe odpowiedzi: {', '.join(WYBORY)}.\nRodzaj:" in PROMPT
    zdanie = "Jan Kowalski mieszka w Gdańsku."
    assert PROMPT.replace("{{sentence}}", zdanie).startswith(f'Zdanie: "{zdanie}"\nJakiego rodzaju')


def probka(lls, gold):
    return {"filtered_resps": [[ll, False] for ll in lls], "arguments": [("ctx", " " + w) for w in WYBORY],
            "gold": gold}


def test_acc_and_char_normalised_acc_norm():
    karta = W.ZK.karta("T29").read_text(encoding="utf-8")
    dlugosci = [len(w) for w in WYBORY]
    assert dlugosci == [23, 13, 11, 17, 4, 18] and "w znakach (23, 13, 11, 17, 4, 18)" in karta
    # acc: max raw loglik -8 -> index 4 ("Czas"); acc_norm: -30/23=-1.304, -20/13=-1.538, -12/11=-1.091,
    # -25/17=-1.471, -8/4=-2.0, -27/18=-1.5 -> index 2 ("Nazwa osoby")
    o = M.oceny_mc(probka([-30, -20, -12, -25, -8, -27], gold=2), z_pmi=False)
    assert (o["pred_acc"], o["pred_acc_norm"], o["acc"], o["acc_norm"], o["k"]) == (4, 2, 0.0, 1.0, 6)
    # tie of raw logliks: the earlier choice wins
    assert M.oceny_mc(probka([-5, -5, -9, -9, -9, -9], gold=0), z_pmi=False)["acc"] == 1.0


def test_baselines_from_the_card_label_counts():
    """1/6 random, constant `Nazwa miejsca` (index 1) 705/2058 = 0.342566 -> card 0,3426."""
    oceny = [{"k": 6, "gold": MAPA[e], "pred_acc": 1} for e, n in ETYKIETY_TESTU.items() for _ in range(n)]
    assert len(oceny) == 2058
    bazy = M.bazy_mc(oceny, klasy_stale=True)
    assert bazy["chance_value"] == pytest.approx(1 / 6) and bazy["majority_value"] == pytest.approx(705 / 2058)
    karta = W.ZK.karta("T29").read_text(encoding="utf-8")
    assert "| Bazy: stała odpowiedź | `Nazwa miejsca` (indeks 1, druga opcja): 705 z 2058 = 0,3426." in karta
    assert "0 → 500, 2 → 372, 3 → 237, 4 → 143, 5 → 101" in karta
    assert "| Bazy: b | 0,3426 (stała odpowiedź; baza losowa 0,1667 jest niższa)." in karta


@pytest.mark.skipif(not W.MA_LM_EVAL, reason="needs lm-eval (.venv-eval): parses the copied YAML")
def test_copied_yaml_parses_to_the_text_read_above():
    cfg = Z.wczytaj_yaml(YAML)
    assert (cfg["doc_to_text"], cfg["doc_to_choice"]) == (PROMPT, WYBORY)
    assert cfg["output_type"] == "multiple_choice" and cfg["test_split"] == "test" and cfg["fewshot_split"] == "train"
    assert [m["metric"] for m in cfg["metric_list"]] == ["acc", "acc_norm"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
