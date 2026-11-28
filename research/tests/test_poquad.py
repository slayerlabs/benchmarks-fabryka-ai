"""PoQuAD open book T31 (common/zadania.py, studies/2026-10-lm-eval-benchmarks/benchmarks/poquad/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, RECIPE.md and the README type row (`gen +klastry +pl`, clusters `context`); the
prompt of the copied fork YAML (`poquad_open_book.yaml`) as the card writes it; `utils.doc_to_target` (first gold
with a leading space) and the decision metric `utils.levenshtein` of the copied fork `utils.py` on the card's
examples (the cut of the LAST character of the prediction, the leading space counted in the threshold, numbers as
regex strings, the unreachable gold `A`); the cluster ids `ewaluuj.klastry_probek` gives from the `context` field.
With lm-eval installed (.venv-eval) the copied YAML is parsed with the repo loader. Run: python tests/test_poquad.py
(or pytest).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402
import ewaluuj as E  # noqa: E402  (common/ is on sys.path after wpis_benchmarku)
import metryki as M  # noqa: E402

Z = W.Z
U =W.modul_forka("poquad/lm_eval_tasks/polish_poquad/utils.py")
YAML = W.ZK.STUDIUM / "benchmarks" / "poquad" / "lm_eval_tasks" / "polish_poquad" / "poquad_open_book.yaml"
PROMPT = ("Tytuł: {{title}} \\n Kontekst: {{context}} \\n Pytanie: {{question}} \\n "
          "Prawidłowa odpowiedź (krótki cytat z Kontekstu):")  # as written in YAML/card


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "clarin-pl/poquad", "rewizja": "a60f228d836fbbf990d11b4590c60b3e7f2aec2d",
                  "nazwa_hf": "poquad", "split": "validation", "metric": "levenshtein,none", "klucz": "levenshtein",
                  "rodzaj": "gen", "klastry": "context", "task": "polish_poquad_open_book",
                  "yaml": "poquad/lm_eval_tasks/polish_poquad/poquad_open_book.yaml",
                  "rewizja_parquet": "c76799436661006876ca3a2bf2ef2268b2179ac9"}
    meta, karta = W.sprawdz_wpis("T31", oczekiwane, shoty=5, typ="gen +klastry +pl")
    assert ("| Metryka decyzyjna | `levenshtein`, 5-shot, średnia po pytaniach pełnego splitu `validation`. "
            "Zgadza się z wpisem `T31` (`metric=\"levenshtein,none\"`, `klucz=\"levenshtein\"`, `shoty=5`, "
            "`klastry=\"context\"`)") in karta
    assert "n: 5 764 (parquet `poquad/validation/0000.parquet` @ `c7679943`, 5 764 wiersze" in karta
    assert "5 764 pytania pochodzą z 1 449 kontekstów" in karta
    assert f'`doc_to_text: "{PROMPT}"`' in karta
    assert 'zwraca `" " + answers.text[0]`' in karta
    tekst = YAML.read_text(encoding="utf-8")
    assert f'doc_to_text: "{PROMPT}"' in tekst and "doc_to_target: !function utils.doc_to_target" in tekst
    assert "test_split: validation" in tekst and "metric: !function utils.levenshtein" in tekst
    assert "process_docs" not in tekst  # card: no process_docs, nothing is dropped


def test_doc_to_target_is_the_first_gold_with_a_space():
    assert U.doc_to_target({"answers": {"text": ["w Krakowie", "Kraków"], "answer_start": [3, 9]}}) == " w Krakowie"
    assert U.doc_to_target({"answers": {"text": [], "answer_start": []}}) == " bez odpowiedzi"


def trafienie(predykcja, zlota):
    # one reference per question: doc_to_target(doc), with its leading space
    return U.levenshtein([predykcja], [U.doc_to_target({"answers": {"text": [zlota]}})])


@pytest.mark.parametrize("predykcja, zlota, wynik", [
    (" Warszawa", "Warszawa", 1),  # "warszawa" cut to "warszaw": distance 1 < 9/2
    ("Warszawa.", "Warszawa", 1),  # the cut takes the dot
    (" Kraków", "Warszawa", 0),
    ("A", "A", 0),  # card: copy of the gold `A` misses, the cut leaves "" and distance 1 is not < 2/2
    (" kxyaZ", "kota", 1),  # cut to "kxya", distance 2 < len(" kota")/2 = 2.5; without the space 2 < 2 would miss
    (" kxyzZ", "kota", 0),  # distance 3
    ("1975.", "1975", 0),  # number taken before the cut: "1975." != "1975"
    (" 1975", "1975", 1),
    ("0.5", "0,5", 1),  # comma turned into a dot on both sides
    ("01", "1", 0), ("1 000", "1000", 0),  # string equality of the numbers, no tolerance
    ("", "trzy", 0),
])
def test_levenshtein_metric_of_the_fork(predykcja, zlota, wynik):
    assert trafienie(predykcja, zlota) == wynik


def test_clusters_are_the_context_field():
    """+klastry `context`: questions on one passage share a cluster; 4 questions on 2 passages -> 2 clusters."""
    docs = [{"title": "T", "context": "Ustęp A.", "question": "P1?"}, {"title": "T", "context": "Ustęp B.", "question": "P2?"},
            {"title": "T", "context": "Ustęp A.", "question": "P3?"}, {"title": "T", "context": "Ustęp A.", "question": "P4?"}]
    probki = [{"doc_id": i, "doc": d} for i, d in enumerate(docs)]
    klastry = E.klastry_probek(Z.ZADANIA["T31"], probki)
    assert klastry == ["Ustęp A.", "Ustęp B.", "Ustęp A.", "Ustęp A."]
    wynik = M.srednia_klastrowa([1, 0, 1, 0], klastry)
    assert wynik["value"] == 0.5 and wynik["n"] == 4


@pytest.mark.skipif(not W.MA_LM_EVAL, reason="needs lm-eval (.venv-eval): parses the copied YAML with !function")
def test_copied_yaml_parses_to_the_card_prompt():
    cfg = Z.wczytaj_yaml(YAML)
    assert cfg["doc_to_text"] == PROMPT.replace("\\n", "\n")
    assert cfg["doc_to_target"].__name__ == "doc_to_target" and cfg["test_split"] == "validation"
    assert cfg["generation_kwargs"]["until"] == ["\n", "</s>", "<|im_end|>"]
    assert cfg["generation_kwargs"]["max_gen_toks"] == 50 and cfg["generation_kwargs"]["do_sample"] is False
    assert [m["metric"] if isinstance(m["metric"], str) else m["metric"].__name__ for m in cfg["metric_list"]] == [
        "exact_match", "levenshtein"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
