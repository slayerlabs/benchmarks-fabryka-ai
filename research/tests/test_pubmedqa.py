"""PubMedQA T44 (common/zadania.py, benchmarks/pubmedqa/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the prompt of lm-eval `preprocess_pubmedqa.py` and the three continuations, the
gold given as text (`final_decision`) and acc with the baselines on a stand-in model. Data: the first rows of
common/tests/data/pubmedqa.jsonl. Run: python tests/test_pubmedqa.py (or pytest).
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z
DANE = [json.loads(l) for l in (Z.DANE_TESTOWE / "pubmedqa.jsonl").read_text().splitlines()[:3]]


def test_entry_matches_the_card():
    meta, karta = Z.ZADANIA["T44"], ZK.karta("T44").read_text(encoding="utf-8")
    oczekiwane = {"repo": "bigbio/pubmed_qa", "rewizja": "15578e80ef02c2c9636d33fdd7eb6b05b987ba60",
                  "nazwa_hf": "pubmed_qa_labeled_fold0_source", "split": "test", "metric": "acc,none"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0 and meta["klasy_stale"]
    for k in ("repo", "rewizja", "nazwa_hf"):
        assert oczekiwane[k] in karta, k
    assert "split: `test` konfiguracji `pubmed_qa_labeled_fold0_source`" in karta and "0-shot" in karta
    assert ZK.rozbieznosci(meta, karta) == {}


def test_prompt_choices_picks_and_metric(tmp_path, monkeypatch):
    # golds yes, no, maybe; the model says yes, yes, maybe -> 2 of 3
    wybor = {DANE[0]["QUESTION"]: " yes", DANE[1]["QUESTION"]: " yes", DANE[2]["QUESTION"]: " maybe"}

    def ll(ctx, kont):
        if ctx == "":
            return 0.0
        return 0.0 if kont == wybor[ctx.split("\nQuestion: ")[1].split("\n")[0]] else -1.0

    roz, zadania = C.ocen_loglik("T44", {"pubmedqa": DANE}, ll, tmp_path, monkeypatch)
    prompt = ("Abstract: A cohort of 200 adults trained three times a week for six months.\n"
              "Resting heart rate decreased by 6 beats per minute on average.\n"
              "Question: Does regular exercise lower resting heart rate?\nAnswer:")
    assert [k for c, k in zadania if c == prompt] == [" yes", " no", " maybe"]
    assert not any("Yes." in c for c, _ in zadania)  # LONG_ANSWER (the conclusions) never in the prompt
    space = roz["dodatkowe"]["space"]
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(2 / 3) and roz["n_scored"] == 3
    # three classes each gold once -> majority 1/3; predictions yes twice -> share 2/3
    assert space["bazy"]["chance_value"] == pytest.approx(1 / 3)
    assert space["bazy"]["majority_value"] == pytest.approx(1 / 3)
    assert space["udzial_najczestszej_predykcji"] == pytest.approx(2 / 3)


def test_text_gold_maps_to_the_option_index():
    probka = {"arguments": [("c", " yes"), ("c", " no"), ("c", " maybe")], "target": "maybe",
              "filtered_resps": [(-3.0, False), (-2.0, False), (-1.0, False)]}
    assert C.M.oceny_mc(probka, z_pmi=False)["gold"] == 2 and C.M.oceny_mc(probka, z_pmi=False)["acc"] == 1.0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
