"""TriviaQA T43 (common/zadania.py, studies/2026-10-lm-eval-benchmarks/benchmarks/triviaqa/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, RECIPE.md and the README type row (`gen +klastry`, clusters `question_id`);
the prompt (the template adds `?`, so a question ending in `?` gets `??`) and the decision scoring as the card writes
it: filter `remove_whitespace` (only `lstrip()`, then take_first), `exact_match` with `ignore_case` and
`ignore_punctuation` (dropped, no space put in), no article removal and no whitespace squeezing, a hit on any alias;
the card's row-0 examples plus invented edge cases. Clusters: `ewaluuj.klastry_probek` gives each row its
`question_id`, so the web and Wikipedia copies of one question are one cluster, and SE K over them (hand-computed) is
above SE A. With lm-eval installed (.venv-eval) the settings are read from the installed `triviaqa` YAML and the rows
are rescored by lm-eval's filter and metric. Run: python tests/test_triviaqa.py (or pytest).
"""
import string
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402
import ewaluuj as E  # noqa: E402  (common/ is on the path after wpis_benchmarku)
import metryki as M  # noqa: E402

Z = W.Z
DOC_TO_TEXT = "Question: {{question}}?\nAnswer:"
WIERSZ_0 = ["David Seville"]  # card: validation row 0, the only alias


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "mandarjoshi/trivia_qa", "rewizja": "0f7faf33a3908546c6fd5b73a660e0f8ff173c2f",
                  "nazwa_hf": "rc.nocontext", "split": "validation", "metric": "exact_match,remove_whitespace",
                  "lm_eval": "triviaqa", "rodzaj": "proba", "klucz": "exact_match", "filtr": "remove_whitespace",
                  "baza": "gen", "klastry": "question_id"}
    meta, karta = W.sprawdz_wpis("T43", oczekiwane, shoty=0, typ="gen +klastry")
    assert ("| Metryka decyzyjna | `exact_match` z filtrem `remove_whitespace`, 0-shot, średnia po wierszach "
            "pełnego splitu `validation`.") in karta
    assert "n: 17944 wierszy (parquet `rc.nocontext/validation` @ `0f7faf33`" in karta
    assert "wiersz T43: `gen +klastry`, klastry `question_id`" in karta
    assert "Razem 9960 klastrów po `question_id`: 7984 dwuwierszowych i 1976 jednowierszowych" in karta
    assert '`doc_to_text: "Question: {{question}}?\\nAnswer:"`, `doc_to_target: "{{answer.aliases}}"`' in karta
    assert "`Question: Who was the man behind The Chipmunks??\\nAnswer:`" in karta
    assert "robi tylko `lstrip()`, potem `take_first`" in karta
    assert "z `ignore_case: true` i `ignore_punctuation: true`" in karta
    assert "spacje nie są ujednolicane, przedimki nie są usuwane" in karta
    assert W.ZK.KATALOGI["T43"] == "triviaqa"


def prompt(pytanie):
    return DOC_TO_TEXT.replace("{{question}}", pytanie)


def normalizuj(tekst):
    return tekst.lower().translate(str.maketrans("", "", string.punctuation))


def exact_match(generacja, aliasy):
    pred = normalizuj(generacja.lstrip())  # remove_whitespace + take_first
    return float(any(pred == normalizuj(a) for a in aliasy))


def test_prompt_doubles_the_question_mark():
    assert prompt("Who was the man behind The Chipmunks?") == (
        "Question: Who was the man behind The Chipmunks??\nAnswer:")  # card, row 0
    assert prompt("Which city hosted the 1908 Olympics") == "Question: Which city hosted the 1908 Olympics?\nAnswer:"


@pytest.mark.parametrize("generacja, aliasy, wynik", [
    (" DAVID SEVILLE.", WIERSZ_0, 1.0),  # card: case and the full stop ignored
    ("david seville ", WIERSZ_0, 0.0),  # card: trailing space stays (lstrip only)
    (" Dave Seville", WIERSZ_0, 0.0),  # card
    (" David  Seville", WIERSZ_0, 0.0),  # double space not squeezed
    (" Beatles", ["The Beatles"], 0.0),  # card: no article removal (authors' script gives 1)
    (" the beatles", ["The Beatles"], 1.0),
    (" Tony", ["Tony (Manero).", "Tony Manero"], 0.0),  # card row 564: "(Manero)." -> "tony manero", no hit
    (" Tony Manero", ["Tony (Manero).", "Tony Manero"], 1.0),  # any alias counts
    (" St", ["St. Louis"], 0.0),  # generation cut at "." cannot hit an alias with a full stop inside
    ("", ["+-*/"], 1.0),  # card: the empty answer hits aliases made of punctuation only (rows 232, 10131)
])
def test_remove_whitespace_and_exact_match(generacja, aliasy, wynik):
    assert exact_match(generacja, aliasy) == wynik


@pytest.mark.parametrize("odwroc", [False, True])
def test_clusters_are_question_ids_whatever_the_sample_order(odwroc):
    # rows 0-9950 web part, 9951-17943 Wikipedia part (card); one question in both parts is one cluster
    wiersze = [(0, "tc_1", 1.0), (1, "tc_2", 1.0), (9951, "tc_1", 1.0), (9952, "tc_2", 0.0), (9953, "bb_9", 0.0)]
    probki = [{"doc_id": i, "doc": {"question_id": q}} for i, q, _ in wiersze]
    if odwroc:
        probki = probki[::-1]
    ids = dict(zip((p["doc_id"] for p in probki), E.klastry_probek(Z.ZADANIA["T43"], probki)))
    assert ids == {0: "tc_1", 1: "tc_2", 9951: "tc_1", 9952: "tc_2", 9953: "bb_9"}
    d = M.srednia_klastrowa([v for *_, v in wiersze], [ids[i] for i, *_ in wiersze])
    # mean 3/5; clusters tc_1 (n 2, mean 1), tc_2 (2, 1/2), bb_9 (1, 0): n_c (mean_c - 3/5) = 0.8, -0.2, -0.6
    # SE K = sqrt(3/2 * (0.64 + 0.04 + 0.36)) / 5 = sqrt(1.56) / 5 = 0.2497999; SE A = sqrt(0.3 / 5) = 0.2449490
    assert d["value"] == pytest.approx(0.6) and (d["k"], d["df"], d["metoda_se"]) == (3, 2, "K")
    assert d["se"] == pytest.approx(1.56 ** 0.5 / 5) and d["se_a"] == pytest.approx((0.3 / 5) ** 0.5)


@pytest.mark.skipif(not W.MA_LM_EVAL, reason="needs lm-eval (.venv-eval): reads the installed triviaqa YAML")
def test_installed_yaml_has_the_card_prompt_filter_and_metric():
    from lm_eval.api.metrics import exact_match_hf_evaluate
    from lm_eval.filters.extraction import WhitespaceFilter

    cfg = Z._yaml("triviaqa")
    assert cfg["doc_to_text"] == DOC_TO_TEXT and cfg["doc_to_target"] == "{{answer.aliases}}"
    assert cfg["generation_kwargs"]["until"] == ["\n", ".", ","]
    filtr = next(f for f in cfg["filter_list"] if f["name"] == "remove_whitespace")["filter"]
    assert filtr == [{"function": "remove_whitespace"}, {"function": "take_first"}]
    em, = cfg["metric_list"]
    assert em["metric"] == "exact_match" and "regexes_to_ignore" not in em
    assert em["ignore_case"] is True and em["ignore_punctuation"] is True
    for generacja, aliasy, wynik in [(" DAVID SEVILLE.", WIERSZ_0, 1.0), ("david seville ", WIERSZ_0, 0.0),
                                     (" Beatles", ["The Beatles"], 0.0), (" Tony Manero", ["Tony (Manero)."], 1.0),
                                     ("", ["+-*/"], 1.0)]:
        pred, = WhitespaceFilter().apply([[generacja]], [{}])[0]
        lm = max(exact_match_hf_evaluate([pred], [a], ignore_case=True, ignore_punctuation=True)["exact_match"]
                 for a in aliasy)
        assert lm == exact_match(generacja, aliasy) == wynik, generacja


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
