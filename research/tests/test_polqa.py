"""PolQA open book T30 (common/zadania.py, studies/2026-10-lm-eval-benchmarks/benchmarks/polqa/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, RECIPE.md and the README type row; the prompt of the copied fork YAML
(`polqa_open_book.yaml`) as the card writes it; the decision metric `utils.levenshtein` of the copied fork `utils.py`
on the card's own examples (threshold half the length of the GOLD answer, numbers compared as regex strings taken
before the trailing dot is cut, any gold of the list counts); `process_docs_open` dropping non-relevant rows and
repeated (passage, question) pairs, the filter behind n = 5 928. With lm-eval installed (.venv-eval) the copied YAML
is parsed with the repo loader. Run: python tests/test_polqa.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402

Z = W.Z
U =W.modul_forka("polqa/lm_eval_tasks/polish_polqa/utils.py")
YAML = W.ZK.STUDIUM / "benchmarks" / "polqa" / "lm_eval_tasks" / "polish_polqa" / "polqa_open_book.yaml"
PROMPT = "Kontekst: {{passage_text}} \\n Pytanie: {{question}} \\n Prawidłowa odpowiedź:"  # as written in YAML/card


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "ipipan/polqa", "rewizja": "d78d036ef08ab3b9f4d85a2893f4d3a0c95a6f37", "nazwa_hf": "pairs",
                  "split": "test", "metric": "levenshtein,none", "klucz": "levenshtein", "rodzaj": "gen",
                  "task": "polish_polqa_open_book", "yaml": "polqa/lm_eval_tasks/polish_polqa/polqa_open_book.yaml",
                  "rewizja_parquet": "0ba79f193fb3720dc0afa49d13c67abef786977f"}
    meta, karta = W.sprawdz_wpis("T30", oczekiwane, shoty=5, typ="gen +pl")
    assert "| Metryka decyzyjna | `levenshtein` (średnia trafień 0/1 po parach), 5-shot, pełny split `test`." in karta
    assert "n: 5 928 par (ustęp, pytanie) po `utils.process_docs_open`" in karta
    assert f"`doc_to_text`: `{PROMPT}`" in karta
    assert "pairs/test` @ `0ba79f19`" in karta
    tekst = YAML.read_text(encoding="utf-8")
    assert f'doc_to_text: "{PROMPT}"' in tekst
    assert "process_docs: !function utils.process_docs_open" in tekst and "doc_to_target: answers" in tekst
    assert "metric: !function utils.levenshtein" in tekst and "test_split: test" in tekst


def trafienie(predykcja, zlote):
    # the fork reads predictions[0][0] (card "Ocena": `_prediction = predictions[0][0].lower()`)
    return U.levenshtein([[predykcja]], zlote)


@pytest.mark.parametrize("predykcja, zlote, wynik", [
    ("tak", ["tak"], 1),
    (" tak", ["tak"], 1),  # leading space kept: distance 1 < 3/2
    ("tak.", ["tak"], 1),  # one trailing dot cut
    ("tak   ", ["tak"], 1),  # two trailing spaces cut -> "tak ", distance 1
    ("TAK", ["tak"], 1),
    ("ta", ["tak"], 1), ("takk", ["tak"], 1),  # distance 1 < 1.5: the threshold is half the GOLD length
    ("tak i nie", ["tak"], 0),  # distance 6
    ("", ["tak"], 0),  # distance = len(gold), never < len/2
    ("trzy", ["3"], 0),  # gold has a number -> only number equality counts
    ("3", ["3"], 1),
    ("3.", ["3"], 0),  # number taken before the dot is cut: "3." != "3"
    ("1939 r.", ["1939"], 1),
    ("1976", ["1976-1978"], 1),  # gold number regex stops at "-": "1976"
    ("Kraków", ["Warszawa", "Kraków"], 1),  # any gold of the list
    ("Gdańsk", ["Warszawa", "Kraków"], 0),
])
def test_levenshtein_metric_of_the_fork(predykcja, zlote, wynik):
    assert trafienie(predykcja, zlote) == wynik


class Wiersze:
    """The three `datasets.Dataset` methods `process_docs_open` calls, over a list of dicts."""

    def __init__(self, wiersze):
        self.wiersze = wiersze

    def remove_columns(self, kolumny):
        return Wiersze([{k: v for k, v in w.items() if k not in kolumny} for w in self.wiersze])

    def filter(self, f):
        return Wiersze([w for w in self.wiersze if f(w)])

    def map(self, f):
        return Wiersze([f(dict(w)) for w in self.wiersze])


def test_process_docs_open_drops_irrelevant_and_repeated_pairs():
    puste = dict.fromkeys(U.COLUMNS_TO_REMOVE, "")
    wiersz = lambda tekst, pytanie, rel, odp: {**puste, "passage_text": tekst, "question": pytanie,
                                               "relevant": rel, "answers": odp}
    docs = Wiersze([
        wiersz("Ustęp A", "Pytanie 1?", True, "['tak']"),
        wiersz("Ustęp A", "Pytanie 1?", True, "['tak']"),  # repeated pair -> out
        wiersz("Ustęp B", "Pytanie 1?", True, "['tak', 'owszem']"),  # same question, other passage -> in
        wiersz("Ustęp C", "Pytanie 1?", False, "['tak']"),  # not relevant -> out
        wiersz("Ustęp A", "Pytanie 2?", True, "['1939']"),
    ])
    wynik = U.process_docs_open(docs).wiersze
    # 5 rows -> 3: one repeat and one non-relevant row gone; answers parsed from the string to a list
    assert [(w["passage_text"], w["question"], w["answers"]) for w in wynik] == [
        ("Ustęp A", "Pytanie 1?", ["tak"]), ("Ustęp B", "Pytanie 1?", ["tak", "owszem"]),
        ("Ustęp A", "Pytanie 2?", ["1939"])]
    assert all(k not in w for w in wynik for k in U.COLUMNS_TO_REMOVE)


@pytest.mark.skipif(not W.MA_LM_EVAL, reason="needs lm-eval (.venv-eval): parses the copied YAML with !function")
def test_copied_yaml_parses_to_the_card_prompt():
    cfg = Z.wczytaj_yaml(YAML)
    assert cfg["doc_to_text"] == PROMPT.replace("\\n", "\n") and cfg["doc_to_target"] == "answers"
    assert cfg["output_type"] == "generate_until" and cfg["test_split"] == "test"
    assert cfg["generation_kwargs"]["until"] == ["\n", "</s>", "<|im_end|>"]
    assert cfg["generation_kwargs"]["max_gen_toks"] == 50 and cfg["generation_kwargs"]["do_sample"] is False
    assert [m["metric"] if isinstance(m["metric"], str) else m["metric"].__name__ for m in cfg["metric_list"]] == [
        "exact_match", "levenshtein"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
