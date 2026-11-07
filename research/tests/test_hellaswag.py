"""HellaSwag scorer on a checked-in sample. No network and no weights.

Run from research/: python tests/test_hellaswag.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "benchmarks" / "hellaswag"))
import hellaswag

SAMPLE = ROOT / "common" / "tests" / "data" / "hellaswag.jsonl"


def load_sample():
    return [json.loads(line) for line in SAMPLE.read_text().splitlines() if line.strip()]


def test_preprocess_matches_lm_eval():
    # Three spaces stay as two: replace does not run again.
    assert hellaswag.preprocess("a   b") == "a  b"
    assert hellaswag.preprocess("A man [title] rides [header] fast") == "A man. rides fast"


def test_query_capitalizes_only_ctx_b():
    doc = load_sample()[0]
    query, choices = hellaswag.query_and_choices(dict(doc, ctx_b="rIDES"))
    assert query == "Cycling: A man Rides"
    assert choices == ["the bike home.", "a sandwich.", "the bus.", "a book."]


def test_wikihow_brackets_are_cleaned_on_the_sample():
    doc = load_sample()[1]
    query, choices = hellaswag.query_and_choices(doc)
    assert query == "Cooking. : Someone Chops"
    # The bracket is gone. The space that stood before it stays and counts in acc_norm.
    assert choices[0] == " onions"
    assert "header" not in choices[0] and "title" not in query


def test_acc_norm_divides_by_choice_characters():
    # Totals: ab wins (-3 > -8). Per character: abcdefgh wins (-1.0 > -1.5).
    doc = {"activity_label": "X", "ctx_a": "Y", "ctx_b": "z", "endings": ["ab", "abcdefgh", "c", "d"], "label": "1"}
    row = hellaswag.score_question(doc, [-3.0, -8.0, -9.0, -9.0])
    assert row["lengths"] == [2, 8, 1, 1]
    assert row["pred"] == 0 and row["acc"] == 0.0
    assert row["pred_norm"] == 1 and row["acc_norm"] == 1.0


def test_tie_keeps_the_earlier_ending():
    doc = load_sample()[0]
    row = hellaswag.score_question(doc, [-1.0, -1.0, -1.0, -1.0])
    assert row["pred"] == 0 and row["pred_norm"] == 0
    assert row["acc"] == 1.0 and row["acc_norm"] == 1.0


def test_summarize_baselines_on_the_sample():
    docs = load_sample()
    rows = [hellaswag.score_question(docs[0], [-1.0, -2.0, -3.0, -4.0]),
            hellaswag.score_question(docs[1], [-8.0, -3.0, -9.0, -9.0])]
    # Second row: acc picks "ab" (index 1). acc_norm picks "abcdefgh" (index 2), which is gold.
    assert rows[1]["pred"] == 1 and rows[1]["pred_norm"] == 2
    summary = hellaswag.summarize(rows)
    assert summary["n"] == 2
    assert summary["random"] == 0.25
    assert summary["majority_index"] == 0 and summary["majority"] == 0.5
    assert summary["acc_norm"] == 1.0
    assert summary["most_frequent_prediction"] == 0.5


def test_rejects_a_short_loglikelihood_list():
    try:
        hellaswag.score_question(load_sample()[0], [-1.0, -2.0])
    except ValueError:
        return
    raise AssertionError("expected ValueError")


if __name__ == "__main__":
    failed = 0
    for name, fn in list(globals().items()):
        if not name.startswith("test_"):
            continue
        try:
            fn()
            print("ok", name)
        except Exception as exc:
            failed += 1
            print("FAIL", name, type(exc).__name__, exc)
    if failed:
        sys.exit(1)
    print("OK")
