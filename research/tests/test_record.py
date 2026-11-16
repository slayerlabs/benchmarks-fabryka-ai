"""ReCoRD T50 (common/zadania.py, benchmarks/record/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the prompt of lm-eval `record` `util.py` (first `passage` fragment + `\n\n`, then
every highlight as `  - {highlight}.\n`; options `  - {query}` with `@placeholder` replaced by each entity of the
sorted, de-duplicated `entities`, scored after the default space delimiter), the decision metric `f1` (SQuAD token F1
of the highest-likelihood entity, maximum over golds), the random-choice baseline (`baza="wybor_losowy"`), and the
clusters: questions on one `passage` form one cluster. Data: three invented questions, two on one passage.
Run: python tests/test_record.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z, E = C.Z, C.E
P1 = "Ann Lee won the race in Oslo.\n@highlight\nLee wins\n@highlight\nOslo race ends"
P2 = "Tim ate lunch with Bob."
DANE = [{"passage": P1, "query": "@placeholder won the race", "entities": ["Lee", "Oslo", "Ann Lee", "Lee"],
         "answers": ["Ann Lee"], "idx": {"passage": 0, "query": 0}},
        {"passage": P1, "query": "The race was in @placeholder", "entities": ["Oslo", "Lee"], "answers": ["Oslo"],
         "idx": {"passage": 0, "query": 1}},
        {"passage": P2, "query": "@placeholder ate lunch", "entities": ["Tim", "Bob"], "answers": ["Tim"],
         "idx": {"passage": 1, "query": 2}}]
KONTEKST1 = "Ann Lee won the race in Oslo.\n\n  - Lee wins.\n  - Oslo race ends.\n"
# chosen entity per question: Lee against gold "Ann Lee" -> P 1, R 1/2, F1 2/3; Oslo -> 1; Bob against Tim -> 0.
# f1 (2/3 + 1 + 0) / 3 = 5/9. Random entity: q1 (Ann Lee 1 + Lee 2/3 + Oslo 0) / 3 = 5/9, q2 1/2, q3 1/2 -> 14/27
WYBOR = {"   - Lee won the race", "   - The race was in Oslo", "   - Bob ate lunch"}


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T50"], ZK.karta("T50").read_text(encoding="utf-8")
    oczekiwane = {"repo": "aps/super_glue", "rewizja": "3de24cf8022e94f4ee4b9d55a6f539891524d646",
                  "nazwa_hf": "record", "split": "validation", "metric": "f1,none", "klucz": "f1", "task": "record",
                  "lm_eval": "record", "rodzaj": "proba", "baza": "wybor_losowy", "klastry": "passage"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0 and "shots" not in meta
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "`record`, split `validation`, 0-shot, metryka `f1`, zadanie lm-eval `record`" in karta
    assert "| Metryka decyzyjna | `f1` (lm-eval `f1,none`" in karta
    assert "`  - {punkt}.\\n`" in karta and "`\\n   - {query z encją}`" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T50"] == "record"


def test_prompt_sorted_unique_entities_f1_and_random_baseline(tmp_path, monkeypatch):
    roz, zadania = C.ocen_loglik("T50", {"record": DANE}, lambda ctx, kont: 0.0 if kont in WYBOR else -1.0,
                                 tmp_path, monkeypatch)
    assert [k for c, k in zadania if c == KONTEKST1 and "won" in k] == [
        "   - Ann Lee won the race", "   - Lee won the race", "   - Oslo won the race"]
    assert [k for c, k in zadania if c == "Tim ate lunch with Bob.\n\n"] == ["   - Bob ate lunch", "   - Tim ate lunch"]
    space = roz["dodatkowe"]["space"]
    assert space["glowna"]["metryka"] == "f1" and space["glowna"]["value"] == pytest.approx(5 / 9)
    assert space["bazy"]["chance_value"] == pytest.approx(14 / 27)
    assert roz["metric"] == "f1,none" and roz["value"] == pytest.approx(5 / 9) and roz["n_scored"] == 3


def test_clusters_are_passages():
    probki = [{"doc_id": i, "doc": d} for i, d in enumerate(DANE)]
    assert E.klastry_probek(Z.ZADANIA["T50"], probki) == [P1, P1, P2]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
