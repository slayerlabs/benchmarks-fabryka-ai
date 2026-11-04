"""MedMCQA T45 (common/zadania.py, benchmarks/medmcqa/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the letter prompt of lm-eval `utils_medmcqa.py` (decision variant) and the cloze
variant next to it, the pick and acc on a stand-in model. Data: the first rows of common/tests/data/medmcqa.jsonl.
Run: python tests/test_medmcqa.py (or pytest).
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z
DANE = [json.loads(l) for l in (Z.DANE_TESTOWE / "medmcqa.jsonl").read_text().splitlines()[:3]]


def test_entry_matches_the_card():
    meta, karta = Z.ZADANIA["T45"], ZK.karta("T45").read_text(encoding="utf-8")
    oczekiwane = {"repo": "openlifescienceai/medmcqa", "rewizja": "91c6572c454088bf71b679ad90aa8dffcd0d5868",
                  "split": "validation", "metric": "acc,none"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0 and meta["cloze"]
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "split: `validation`" in karta and "0-shot, format liter" in karta
    assert ZK.rozbieznosci(meta, karta) == {}


# letters: q1 gold B (cop 1) -> B; q2 gold A -> B (miss); q3 gold C -> C. Cloze: always the first option.
LITERA = {"Which organ produces insulin?": " B", "Normal human body temperature in Celsius is about": " B",
          "Vitamin deficiency causing scurvy is vitamin": " C"}


def ll(ctx, kont):
    if ctx == "":
        return 0.0
    pytanie = ctx.split("Question: ")[1].split("\n")[0]
    if "\nChoices:\n" in ctx:
        return 0.0 if kont == LITERA[pytanie] else -1.0
    return 0.0 if kont == " " + next(d["opa"] for d in DANE if d["question"] == pytanie) else -1.0


def test_prompt_choices_picks_and_metric(tmp_path, monkeypatch):
    roz, zadania = C.ocen_loglik("T45", {"medmcqa": DANE}, ll, tmp_path, monkeypatch)
    litery = ("Question: Which organ produces insulin?\nChoices:\nA. Liver\nB. Pancreas\nC. Kidney\nD. Spleen\n"
              "Answer:")
    assert [k for c, k in zadania if c == litery] == [" A", " B", " C", " D"]
    assert [k for c, k in zadania if c == "Question: Which organ produces insulin?\nAnswer:"] == [
        " Liver", " Pancreas", " Kidney", " Spleen"]
    space, cloze = roz["dodatkowe"]["space"], roz["dodatkowe"]["cloze"]
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(2 / 3) and roz["n_scored"] == 3
    assert space["acc_norm"]["value"] == space["acc"]["value"]  # one-character options: acc_norm = acc (card)
    # cloze, informational: always opa -> only q2 (cop 0) right
    assert cloze["acc"]["value"] == pytest.approx(1 / 3)
    # golds 1, 0, 2: majority 1/3, random 1/4; letter B in 2 of 3 picks
    assert space["bazy"]["majority_value"] == pytest.approx(1 / 3) and space["bazy"]["chance_value"] == 0.25
    assert space["udzial_najczestszej_predykcji"] == pytest.approx(2 / 3)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
