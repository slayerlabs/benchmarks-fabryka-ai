"""BLiMP (slayer_eval/blimp.py + the `blimp` task of hipoteza_formatu.py), no network, no weights.
Run: python tests/test_blimp.py (or pytest)."""
import importlib.util
import math
import os
import sys
from pathlib import Path

KAT = Path(__file__).resolve().parent.parent / "slayer_eval"
sys.path.insert(0, str(KAT))
import blimp as B  # noqa: E402

PROBKA = KAT / "testy" / "dane" / "blimp.jsonl"


def docs():
    return B.wczytaj(PROBKA)


def wyniki(trafione):
    """{id: row} with log-likelihoods giving the requested hit (True) or miss (False) per id."""
    return {i: {"id": i, "ll": [-1.0, -2.0] if t else [-2.0, -1.0]} for i, t in trafione.items()}


def test_wczytaj_sortuje_paradygmaty_i_sklada_s_selection():
    d = docs()
    assert len(d) == 9
    assert [x["grupa"] for x in d][:4] == ["adjunct_island"] * 4  # sorted by paradigm, file order inside
    assert [x["id"] for x in d][:2] == ["blimp_adjunct_island/0", "blimp_adjunct_island/1"]
    assert all(x["gold"] == 0 and x["opcje"][0] == x["rekord"]["sentence_good"] for x in d)
    zj = {x["grupa"]: x["zjawisko"] for x in d}
    assert zj["animate_subject_passive"] == "argument_structure"  # HF "s-selection" -> paper group
    assert zj["regular_plural_subject_verb_agreement_1"] == "subject_verb_agreement"


def test_para_jak_lm_eval_pusty_kontekst_bos_i_spacja():
    import pytest
    pytest.importorskip("torch")
    os.environ["BLIMP_DIR"] = str(PROBKA)
    import hipoteza_formatu as H

    class Stub:
        prefiks, prefiks_pusty = [], [0]

        def encode(self, s):
            return [ord(c) for c in s]

    dane = H.dokumenty("blimp")
    assert len(dane) == 9 and "rekord" not in dane[0]
    ctx, konty = H.ZADANIA["blimp"][1](dane[0])
    ce, co = H.para(Stub(), ctx, konty[0])
    assert ce == [0]  # exactly one unscored BOS/EOT
    assert co == [ord(c) for c in " " + dane[0]["opcje"][0]]  # target delimiter " " goes to the sentence


def test_remis_liczy_sie_jako_trafienie():
    assert B.trafienie([-3.0, -3.0]) == 1 and B.trafienie([-3.0, -2.9]) == 0


def test_identyczne_zdania_to_remis_niezaleznie_od_szumu():
    d = {"opcje": ["Same sentence.", "Same sentence."]}
    assert B.trafienie_pary(d, {"ll": [-74.41427, -74.41425]}) == 1  # float noise must not make it an error
    assert B.trafienie_pary({"opcje": ["a", "b"]}, {"ll": [-74.41427, -74.41425]}) == 0


def test_p_wartosci_panelu():
    d = docs()
    w = wyniki({x["id"]: True for x in d})
    p = B.panel(d, "pair_id", budzet=7)
    assert B.p_wartosci_panelu(d, w, p, 1.0, powtorzen=100) == 1.0  # all correct -> every panel gives 1.0
    assert B.p_wartosci_panelu(d, w, p, 0.5, powtorzen=100) == 0.0


def test_panel_przydzial_grupy():
    d = docs()
    p = B.panel(d, "pair_id", budzet=7)
    licz = {}
    for x in p:
        licz[x["grupa"]] = licz.get(x["grupa"], 0) + 1
    # 2 per member first (6), the 7th slot: largest deficit 7/3-2, tie -> first member task name
    assert licz == {"adjunct_island": 3, "animate_subject_passive": 2, "regular_plural_subject_verb_agreement_1": 2}
    assert [x["id"] for x in B.panel(list(reversed(d)), "pair_id", budzet=7)] == [x["id"] for x in p]
    assert len(B.panel(d, "sha256", budzet=200)) == 9  # min(budget, N)


def test_panel_kolejnosc_po_hashu():
    d = [x for x in docs() if x["grupa"] == "adjunct_island"]
    klucze = sorted(B.klucz_wyboru("blimp", "blimp_adjunct_island", str(x["rekord"]["pair_id"])) for x in d)
    p = B.panel(d, "pair_id", budzet=2)
    assert [B.klucz_wyboru("blimp", "blimp_adjunct_island", str(x["rekord"]["pair_id"])) for x in p] == klucze[:2]


def test_wartosc_grupy_rowne_wagi_czlonkow():
    assert math.isclose(B.wartosc_grupy([1, 1, 0, 1, 1], ["a", "a", "a", "b", "b"]), (2 / 3 + 1) / 2)
    # the Space T01 value 0.8407960199 = 338/402: 66 members x 3 pairs, 1 member x 2 pairs
    assert math.isclose(338 / 402, 0.8407960199004975)


def test_statystyki_i_porownanie_parowane():
    d = docs()
    ids = [x["id"] for x in d]
    a = wyniki({i: True for i in ids})
    b = wyniki({i: not i.startswith("blimp_adjunct") for i in ids})
    sa, sb = B.statystyki_modelu(a, d, bootstrap=False), B.statystyki_modelu(b, d, bootstrap=False)
    assert sa["acc"] == 1.0 and math.isclose(sb["acc"], 2 / 3)  # equal paradigm weights, not 5/9
    assert sb["paradygmaty"]["adjunct_island"]["acc"] == 0.0
    assert set(sb["zjawiska"]) == {"argument_structure", "island_effects", "subject_verb_agreement"}
    assert sa["baza_losowa"] == 0.5 and sa["baza_wiekszosciowa"] is None
    por = B.porownanie_parowane(a, b, d)
    assert math.isclose(por["ogolem"]["roznica"], 1 / 3)
    assert por["paradygmaty"]["adjunct_island"]["se"] == 0.0 and por["paradygmaty"]["adjunct_island"]["z"] is None
    assert por["paradygmaty"]["animate_subject_passive"]["roznica"] == 0.0


def test_porownanie_odwrocona_kolejnosc_wejscia():
    d = docs()
    a = wyniki({x["id"]: i % 2 == 0 for i, x in enumerate(d)})
    b = wyniki({x["id"]: i % 3 == 0 for i, x in enumerate(d)})
    p1 = B.porownanie_parowane(a, b, d)
    p2 = B.porownanie_parowane(a, b, list(reversed(d)))
    assert math.isclose(p1["ogolem"]["roznica"], p2["ogolem"]["roznica"])
    assert math.isclose(p1["ogolem"]["se"], p2["ogolem"]["se"])


def test_liczby_porownania_blimp_parowane():
    sys.path.insert(0, str(KAT.parent / "narzedzia"))
    import liczby as Lz
    d = docs()
    ids = [x["id"] for x in d]
    a = wyniki({i: True for i in ids})
    b = wyniki({i: not i.startswith("blimp_adjunct") for i in ids})
    bl = {"modele": {"1.06": B.statystyki_modelu(a, d, bootstrap=False), "pythia-1b": B.statystyki_modelu(b, d, bootstrap=False)},
          "porownanie": {"a": "1.06", "b": "pythia-1b", **B.porownanie_parowane(a, b, d)}}
    por = Lz.porownania_blimp(bl)
    assert len(por) == 1 + 3 + 3  # overall + phenomena + paradigms
    assert {p["test"] for p in por} == {"blimp"} and all(p["rodzina"] == "slayer_vs_pythia" for p in por)
    og = por[0]
    assert og["zadanie"] == "blimp" and math.isclose(og["roznica"], 1 / 3) and og["se"] == og["se_parowane"]


def test_werdykt_progi():
    assert B.werdykt(3.0) == "pewne" and B.werdykt(-2.5) == "prawdopodobne" and B.werdykt(1.99) == "szum"
    assert B.werdykt(None) is None


def test_se_i_bootstrap():
    x = [1] * 80 + [0] * 20
    assert math.isclose(B.se_warstwowe([x]), math.sqrt(0.8 * 0.2 * 100 / 99 / 100))  # sample variance / n
    lo, hi = B.bootstrap_ci([x, x], powtorzen=2000)
    assert lo < 0.8 < hi and (lo, hi) == B.bootstrap_ci([x, x], powtorzen=2000)
    lo_w, hi_w = B.wilson(800, 1000)
    assert math.isclose(lo_w, 0.77408, abs_tol=1e-5) and math.isclose(hi_w, 0.82362, abs_tol=1e-5)  # Wilson, z=1.96


def test_wpis_t01_w_zadaniach():
    if importlib.util.find_spec("lm_eval") is None:
        import pytest
        pytest.skip("lm_eval not installed (zadania.py imports it)")
    import zadania as Z
    (wariant, cfg), = Z.konfiguracje("T01", "lokalne")
    assert wariant == "space" and cfg["doc_to_text"] == "" and cfg["target_delimiter"] == " "
    assert cfg["doc_to_target"] == 0 and cfg["dataset_kwargs"]["data_files"]["test"].endswith("blimp.jsonl")
    (_, hf), = Z.konfiguracje("T01", "hf")
    assert hf["dataset_path"] == "parquet" and B.REWIZJA in hf["dataset_kwargs"]["data_files"]["test"]


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
