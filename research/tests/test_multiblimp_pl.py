"""MultiBLiMP PL T04 (common/zadania.py, benchmarks/multiblimp-pl/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the requests (empty context, space + whole sentence), the pick on a tie and the
metric in percent on a stand-in model. Data: the first rows of common/tests/data/multiblimp_pl.jsonl.
Run: python tests/test_multiblimp_pl.py (or pytest).
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

M, Z = C.M, C.Z
DANE = [json.loads(l) for l in (Z.DANE_TESTOWE / "multiblimp_pl.jsonl").read_text(encoding="utf-8").splitlines()[:3]]


def test_entry_matches_the_card():
    meta, karta = Z.ZADANIA["T04"], ZK.karta("T04").read_text(encoding="utf-8")
    oczekiwane = {"repo": "jumelet/multiblimp", "rewizja": "de923efa8d2483d6b13364ee68e65308e990a991",
                  "split": "pol/data.tsv", "plik_hf": "pol/data.tsv", "metric": "accuracy", "unit": "percent"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0
    for k in ("repo", "rewizja", "split"):
        assert oczekiwane[k] in karta, k
    assert "(`accuracy`)" in karta and "`unit: percent`" in karta and "0-shot: pusty kontekst" in karta
    assert ZK.rozbieznosci(meta, karta) == {}


def test_requests_tie_rule_and_percent(tmp_path, monkeypatch):
    dobre, zle = [d["sen"] for d in DANE], [d["wrong_sen"] for d in DANE]
    # row 1: correct sentence more likely (hit); row 2: tie (lm-eval argmax keeps the first option, the correct one:
    # hit; the paper counts a tie as a miss, card "Ocena"); row 3: wrong sentence more likely (miss)
    ll = {" " + dobre[0]: -10.0, " " + zle[0]: -12.0, " " + dobre[1]: -9.0, " " + zle[1]: -9.0,
          " " + dobre[2]: -15.0, " " + zle[2]: -11.0}
    roz, zadania = C.ocen_loglik("T04", {"multiblimp_pl": DANE}, lambda ctx, kont: ll[kont], tmp_path, monkeypatch)
    assert {c for c, _ in zadania} == {""}  # no prompt: the sentence pair alone
    assert [k for _, k in zadania[:2]] in ([" " + dobre[0], " " + zle[0]], [" " + dobre[1], " " + zle[1]],
                                           [" " + dobre[2], " " + zle[2]])
    assert sorted(set(k for _, k in zadania)) == sorted(ll)
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(2 / 3) and space["acc"]["n"] == 3
    assert "acc_pmi" not in space  # empty context: PMI is identically 0, not reported
    assert roz["metric"] == "accuracy" and roz["unit"] == "percent" and roz["value"] == pytest.approx(200 / 3)
    assert space["bazy"]["chance_value"] == 0.5 and space["bazy"]["majority_value"] is None  # klasy_stale False


def test_choices_are_correct_then_wrong():
    assert Z.multiblimp_choices(DANE[0]) == [DANE[0]["sen"], DANE[0]["wrong_sen"]]
    with pytest.raises(KeyError):
        Z.multiblimp_choices({"zdanie": "x"})


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
