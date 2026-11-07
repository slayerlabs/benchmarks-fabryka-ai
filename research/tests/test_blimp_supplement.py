"""BLiMP Supplement T52 (common/zadania.py, benchmarks/blimp-supplement/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card (5 OSF files pinned by SHA-256), the requests of the authors' `_template_yaml`
(empty context, " " + sentence, gold = good sentence), the unweighted mean of the 5 subtasks on a stand-in model, and
the OSF loader refusing bytes with another SHA-256. Data: invented pairs, one per subtask (not from the dataset).
Run: python tests/test_blimp_supplement.py (or pytest).
"""
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z
PODTESTY = ["hypernym", "qa_congruence_easy", "qa_congruence_tricky", "subject_aux_inversion", "turn_taking"]


def test_entry_matches_the_card():
    meta, karta = Z.ZADANIA["T52"], ZK.karta("T52").read_text(encoding="utf-8")
    assert list(meta["pliki_osf"]) == PODTESTY and "rewizja" not in meta
    for p, (_, sha) in meta["pliki_osf"].items():
        assert f"`{p}.jsonl` `{sha}`" in karta, p  # card field "Dane: pliki"
    assert meta["repo"] == "osf.io/ad7qg" and "https://osf.io/ad7qg/" in karta
    assert meta["split"] == "train" and "split `train`" in karta
    assert meta["metric"] == "acc,none" and "| Metryka decyzyjna | `acc`, makrośrednia z 5 podzadań (bez wag)" in karta
    assert meta["wagi"] == "rowne" and "weight_by_size=False" in karta
    assert ZK.shoty(meta) == 0 and ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T52"] == "blimp-supplement"


def para(dobre, zle):
    return {"sentence_good": dobre, "sentence_bad": zle}


DANE = {"hypernym": [para("If she has a dog, she has a mammal.", "If she has a mammal, she has a dog.")],
        "qa_congruence_easy": [para("What did you get?\nI got a chair.", "What did you get?\nI got Sam.")],
        "qa_congruence_tricky": [para("Who ate?\nSam ate.", "Who ate?\nSam ate a pie."),
                                 para("Where is it?\nIt is here.", "Where is it?\nIt is red.")],
        "subject_aux_inversion": [para("Is the man who is tall happy?", "Is the man who tall is happy?")],
        "turn_taking": [para("Ann: Should you go?\nBob: No, I shouldn't.", "Ann: Should you go?\nBob: No, you shouldn't.")]}
# hit = good sentence more probable; tricky: 1 of 2, the others: hit, miss, hit, hit
TRAFIENIA = {d["sentence_good"]: hit for docs, hits in ((DANE["hypernym"], [1]), (DANE["qa_congruence_easy"], [0]),
                                                         (DANE["qa_congruence_tricky"], [1, 0]),
                                                         (DANE["subject_aux_inversion"], [1]), (DANE["turn_taking"], [1]))
             for d, hit in zip(docs, hits)}


def ll(ctx, kont):
    tekst = kont[1:]
    if tekst in TRAFIENIA:
        return -1.0 if TRAFIENIA[tekst] else -5.0
    return -3.0


def test_requests_and_unweighted_mean_of_subtasks(tmp_path, monkeypatch):
    roz, zadania = C.ocen_loglik("T52", DANE, ll, tmp_path, monkeypatch)
    pary = DANE["qa_congruence_easy"][0]
    assert ("", " " + pary["sentence_good"]) in zadania and ("", " " + pary["sentence_bad"]) in zadania
    assert all(c == "" and k.startswith(" ") for c, k in zadania)
    space = roz["dodatkowe"]["space"]
    # subtasks 1, 0, 1/2, 1, 1: unweighted 3.5 / 5 = 0.7; weighted by pairs it would be 4/6
    assert space["acc"]["value"] == pytest.approx(0.7) and roz["value"] == pytest.approx(0.7)
    assert roz["metric"] == "acc,none" and roz["n_scored"] == 6
    assert roz["zrodlo_danych"]["sha256"] == {p: s for p, (_, s) in Z.ZADANIA["T52"]["pliki_osf"].items()}


def test_osf_loader_accepts_the_pinned_bytes_and_refuses_others(tmp_path, monkeypatch):
    dane = b'{"sentence_good": "A b.", "sentence_bad": "B a."}\n'
    sha = hashlib.sha256(dane).hexdigest()
    pobrane = []

    def pobierz(url, timeout):
        pobrane.append(url)
        return SimpleNamespace(content=dane, raise_for_status=lambda: None)

    monkeypatch.setenv("OSF_CACHE", str(tmp_path))
    monkeypatch.setattr("requests.get", pobierz)
    assert Z.pobierz_osf("abcde", sha).read_bytes() == dane
    assert Z.pobierz_osf("abcde", sha).read_bytes() == dane  # second call from the cache
    assert pobrane == ["https://osf.io/download/abcde/"]
    with pytest.raises(ValueError, match="SHA-256"):
        Z.pobierz_osf("abcde", "0" * 64)
    assert not (tmp_path / f"{'0' * 64}.jsonl").exists()
    assert Z.dane_osf(osf="abcde", sha256=sha)["train"][0]["sentence_good"] == "A b."


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
