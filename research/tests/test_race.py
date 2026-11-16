"""RACE (high) T40 (common/zadania.py, benchmarks/race/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, RECIPE.md and the README type row; `doc_to_text`, `doc_to_choice` and
`doc_to_target` of the copied `preprocess_race.py` (lm-eval 6d2abda4 = 0.4.9.1) on an invented article: earlier
questions with their correct option as context, a fill-in question ending in "  _  ." cut to its last 5 characters
(`question[-5:]`, not the `question[:-5]` of lm-eval 0.4.13), the last question bare and the only one scored; the
baselines from the card's answer counts through `metryki.bazy_mc` (b = 271 / 1045). With lm-eval installed
(.venv-eval) the installed `race` YAML is checked for the card's split, choice of scored text and metric.
Run: python tests/test_race.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402
import metryki as M  # noqa: E402  (common/ is on sys.path after wpis_benchmarku)

Z = W.Z
KOPIA = W.KORZEN / "benchmarks" / "race" / "lm_eval_tasks" / "preprocess_race.py"
P = W.modul_forka("race/lm_eval_tasks/preprocess_race.py")
DOC = {"article": "Tom has a dog called Rex.", "problems": repr([
    {"question": "Tom has a  _  .", "options": ["cat", "dog", "fish", "bird"], "answer": "B"},
    {"question": "What is the dog called?", "options": ["Max", "Bob", "Rex", "Ted"], "answer": "C"},
    {"question": "Who owns the dog?", "options": ["Tom", "Ann", "Bob", "Eve"], "answer": "A"},
])}


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "EleutherAI/race", "rewizja": "66ca2e6374282f5e35b11559e87185db911a6900",
                  "nazwa_hf": "high", "split": "test", "metric": "acc,none", "rodzaj": "mc", "klasy_stale": True,
                  "task": "race"}
    meta, karta = W.sprawdz_wpis("T40", oczekiwane, shoty=0, typ="mc")
    assert "| Metryka decyzyjna | `acc`, 0-shot, średnia po 1 045 pytaniach pełnego splitu `test`." in karta
    assert "n: 1 045 dokumentów (artykułów), czyli 1 045 ocenianych pytań" in karta
    assert ("jeśli `question[-6:] == \"  _  .\"`, to `question[-5:] + tekst_poprawnej_opcji + \"\\n\"`, inaczej "
            "`\"Question: \" + question + \"\\n\" + \"Answer: \" + tekst_poprawnej_opcji + \"\\n\"`") in karta
    assert "kontynuacje to `\" \" + tekst opcji` (pełny tekst, nie litera)" in karta
    kopia = KOPIA.read_text(encoding="utf-8")
    assert 'text += problem["question"][-5:] + get_answer_option(problem) + "\\n"' in kopia


def test_prompt_choices_and_target_of_the_copy():
    # earlier fill-in question: "Tom has a  _  ."[-5:] = " _  ." + "dog"; lm-eval 0.4.13 would give "Tom has a dog"
    assert P.doc_to_text(DOC) == ("Article: Tom has a dog called Rex.\n\n"
                                  " _  .dog\n"
                                  "Question: What is the dog called?\nAnswer: Rex\n"
                                  "Who owns the dog?")
    assert P.doc_to_choice(DOC) == ["Tom", "Ann", "Bob", "Eve"] and P.doc_to_target(DOC) == 0


def test_single_question_article_has_no_earlier_context():
    doc = {"article": "A.", "problems": repr([{"question": "Q?", "options": ["a", "b", "c", "d"], "answer": "D"}])}
    assert P.doc_to_text(doc) == "Article: A.\n\nQ?" and P.doc_to_target(doc) == 3


def test_baselines_from_the_card_answer_counts():
    """Gold of the last questions A 271, B 259, C 271, D 244: random 0.25, constant 271/1045 = 0.259330."""
    oceny = [{"k": 4, "gold": g, "pred_acc": 0} for g, n in enumerate([271, 259, 271, 244]) for _ in range(n)]
    assert len(oceny) == 1045
    bazy = M.bazy_mc(oceny, klasy_stale=True)
    assert bazy["chance_value"] == 0.25 and bazy["majority_value"] == pytest.approx(0.259330, abs=5e-7)
    karta = W.ZK.karta("T40").read_text(encoding="utf-8")
    assert "Poprawne odpowiedzi ostatnich pytań: A 271, B 259, C 271, D 244." in karta
    assert "b = max(0,25; 0,259330) = 0,259330 = 271/1 045" in karta


@pytest.mark.skipif(not W.MA_LM_EVAL, reason="needs lm-eval (.venv-eval): reads the installed race YAML")
def test_installed_yaml_matches_the_card():
    cfg = Z._yaml("race")
    assert (cfg["dataset_path"], cfg["dataset_name"], cfg["test_split"]) == ("EleutherAI/race", "high", "test")
    assert cfg["output_type"] == "multiple_choice" and "target_delimiter" not in cfg and not cfg.get("num_fewshot")
    assert [m["metric"] for m in cfg["metric_list"]] == ["acc"]
    assert cfg["doc_to_choice"](DOC) == P.doc_to_choice(DOC) and cfg["doc_to_target"](DOC) == P.doc_to_target(DOC)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
