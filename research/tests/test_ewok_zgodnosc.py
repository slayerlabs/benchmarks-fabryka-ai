"""Etap C (METODOLOGIA.md): nasz kod EWoK (benchmarks/ewok/ewok.py) a kod autorów EWoK, gpt2-xl, 16 rekordów.

Plik `common/tests/data/ewok_zgodnosc.json` trzyma tylko numery wierszy `ewok-core-1.0` i log P per (kontekst,
zdanie) z kodu autorów (fp32) i z naszego kodu. Tekstu rekordów nie ma (TERMS_OF_USE EWoK). Wylosowane seedem
20261103 przez `benchmarks/ewok/reference/compare.py`.

- test_decyzje_z_pliku: bez sieci i bez wag, sprawdza zgodność decyzji i ocen zapisanych liczb (≥ 99%).
- test_przeliczenie_naszym_kodem: liczy nasze log P od nowa, gdy wagi gpt2-xl i zbiór są w lokalnym cache HF.
  Bez nich test się pomija, nie łączy się z siecią.

Uruchom: python tests/test_ewok_zgodnosc.py (albo pytest).
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks" / "ewok"))
import ewok as E  # noqa: E402

SAMPLE = json.loads((ROOT / "common" / "tests" / "data" / "ewok_zgodnosc.json").read_text(encoding="utf-8"))
MODEL, MODEL_REV = "openai-community/gpt2-xl", "15ea56dee5df4983c59b2538573817e1667135e2"
THRESHOLD = 0.99


def decisions(ll):
    """ll in the order (C1,T1), (C1,T2), (C2,T1), (C2,T2): the two decisions of the EWoK rule (sign of a difference)."""
    sign = lambda x: (x > 0) - (x < 0)
    return [sign(ll[0] - ll[2]), sign(ll[3] - ll[1])]


def authors_score(ll):
    # the authors' inspect_results.Rmd: tie = 0.5 (count_equal_as_half = TRUE)
    return sum(1.0 if d > 0 else 0.5 if d == 0 else 0.0 for d in decisions(ll)) / 2


def our_score(ll):
    return E.evaluate({"ll": [[ll[0], ll[1]], [ll[2], ll[3]]]})["ewok"]


def agreement(a, b):
    da = [d for ll in a for d in decisions(ll)]
    db = [d for ll in b for d in decisions(ll)]
    return sum(x == y for x, y in zip(da, db)) / len(da)


def test_probka_ma_10_do_20_rekordow_bez_tekstu():
    r = SAMPLE["records"]
    assert 10 <= len(r) <= 20
    assert all(set(x) == {"hf_row", "authors", "ours"} for x in r)


def test_decyzje_z_pliku():
    r = SAMPLE["records"]
    assert agreement([x["authors"] for x in r], [x["ours"] for x in r]) >= THRESHOLD
    # without ties our score (tie = 0) and the authors' score (tie = 0.5) must be equal
    for x in r:
        if 0 not in decisions(x["authors"]) + decisions(x["ours"]):
            assert our_score(x["ours"]) == authors_score(x["authors"])


def _local():
    """(model dir, records) from the HF cache or None; never connects to the network."""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    try:
        from huggingface_hub import try_to_load_from_cache
        # partial snapshot (only *.json, *.safetensors, *.txt), so look for a single file
        weights = try_to_load_from_cache(MODEL, "model.safetensors", revision=MODEL_REV)
        if not isinstance(weights, str):
            return None
        path = os.path.dirname(weights)
        recs = E.load_records()
    except Exception:
        return None
    return path, recs


def test_przeliczenie_naszym_kodem():
    local = _local()
    if local is None:
        print("pominięto test_przeliczenie_naszym_kodem: brak gpt2-xl albo ewok-core-1.0 w lokalnym cache HF")
        return
    import torch
    from hipoteza_formatu import licz_logliki, para
    path, recs = local
    m = E.build_model(path, "cuda" if torch.cuda.is_available() else "cpu")
    r = SAMPLE["records"]
    pairs = [para(m, recs[x["hf_row"]][c], " " + recs[x["hf_row"]][t])
             for x in r for c in ("Context1", "Context2") for t in ("Target1", "Target2")]
    ll = [v for v, _ in licz_logliki(m, pairs, batch=8)]
    new = [ll[4 * i:4 * i + 4] for i in range(len(r))]
    assert agreement([x["authors"] for x in r], new) >= THRESHOLD
    # the same code gives the numbers in the file (differences only from the order of operations on GPU/CPU)
    assert max(abs(a - b) for x, n in zip(r, new) for a, b in zip(x["ours"], n)) < 1e-2


if __name__ == "__main__":
    for name, f in list(globals().items()):
        if name.startswith("test_"):
            f()
    print("OK")
