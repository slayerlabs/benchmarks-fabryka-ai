"""WinoGrande scorer, no network and no weights.

Run: python tests/test_winogrande.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "benchmarks" / "winogrande"))
import score

DOC = {
    "sentence": "Sarah was a much better surgeon than Maria so _ always got the easier cases.",
    "option1": "Sarah",
    "option2": "Maria",
    "answer": "2",
}


def test_continuation_is_the_suffix_after_the_blank():
    assert score.continuation(DOC) == "always got the easier cases."


def test_both_options_share_that_continuation():
    left, right = score.contexts(DOC)
    assert left.endswith("Sarah") and right.endswith("Maria")
    assert score.continuation(DOC) == score.continuation(DOC)


def test_tie_takes_the_earlier_option():
    assert score.predict([-2.0, -2.0]) == 0


def test_higher_loglikelihood_wins():
    # gold is option 2; these logliks pick option 1, so this example is a miss
    assert score.acc(DOC, [-17.2, -18.0]) == 0.0


def test_podmiana_poprawnej_opcji_obniza_wynik():
    # Grzegorz. Pierwsza linia: złoto Maria, wygrywa Maria. Druga: złoto podmienione na Sarah.
    assert score.acc(DOC, [-18.0, -17.2]) == 1
    assert score.acc(dict(DOC, answer="1"), [-18.0, -17.2]) == 0


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
