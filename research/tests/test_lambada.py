"""LAMBADA T17 (common/zadania.py, benchmarks/lambada/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the requests of lm-eval `lambada_openai` (context = text up to the last space,
target = one space + the last piece after it, also when that piece carries a quote or a line break, card "Znane
rozbieżności"), and the decision metric `acc` = greedy hit, not the highest log-likelihood, on a stand-in model.
Data: invented passages, not from the dataset. Run: python tests/test_lambada.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z
DANE = [{"text": "Tom gave the key to Ann. Later that night she opened the door with the key"},
        {"text": "He looked at her and said, \"Nadia"},
        {"text": "It was the end of\n\nPower"}]
# expected (context, target) pairs: the space before the last piece belongs to the target
PARY = [("Tom gave the key to Ann. Later that night she opened the door with the", " key"),
        ("He looked at her and said,", " \"Nadia"),
        ("It was the end", " of\n\nPower")]


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T17"], ZK.karta("T17").read_text(encoding="utf-8")
    oczekiwane = {"repo": "EleutherAI/lambada_openai", "rewizja": "900124bf3b8235c6daf21033af9948b3f07346c4",
                  "nazwa_hf": "default", "split": "test", "metric": "acc,none", "lm_eval": "lambada_openai"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0
    for k in ("repo", "rewizja", "lm_eval"):
        assert oczekiwane[k] in karta, k
    assert "| Metryka decyzyjna | `acc`" in karta and "split: test" in karta and "0-shot" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T17"] == "lambada"


def ocen(ll, tmp_path, monkeypatch):
    """`ll(ctx, cont)` -> (loglik, greedy); returns (dodatkowe['space'], requests in order)."""
    zadania = []
    lm = C.AtrapaLM(ll=lambda ctx, kont: (zadania.append((ctx, kont)), ll(ctx, kont))[1])
    _, d = C.ocen("T17", {"lambada_openai": DANE}, lm, tmp_path, monkeypatch)
    return d, zadania


def test_requests_split_at_the_last_space(tmp_path, monkeypatch):
    _, zadania = ocen(lambda ctx, kont: (-1.0, False), tmp_path, monkeypatch)
    assert zadania == PARY


def test_acc_is_the_greedy_hit_not_the_loglik(tmp_path, monkeypatch):
    # passage 1: greedy hit at a low log-likelihood; passages 2 and 3: high log-likelihood, not greedy -> acc 1/3
    ll = {" key": (-9.0, True), " \"Nadia": (-0.1, False), " of\n\nPower": (-0.2, False)}
    d, _ = ocen(lambda ctx, kont: ll[kont], tmp_path, monkeypatch)
    assert d["glowna"]["metryka"] == "acc" and d["glowna"]["value"] == pytest.approx(1 / 3)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
