"""Czyste funkcje niezależnej ewaluacji Slayera (common/). Uruchom: python tests/test_slayer_eval.py (albo pytest)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
import metryki as M  # noqa: E402
import trace_pytan as T  # noqa: E402


def probka(lls, gold, konty=(" A", " B", " C", " D"), bezw=None, ctx="Q:"):
    """Rekord jak z --log_samples lm-eval; z `bezw` dokłada połowę bezwarunkową (acc_mutual_info)."""
    args = [(ctx, c) for c in konty]
    resp = [(ll, False) for ll in lls]
    if bezw is not None:
        args += [("", c) for c in konty]
        resp += [(ll, False) for ll in bezw]
    return {"arguments": args, "filtered_resps": resp, "target": gold, "doc_id": 0, "doc": {}}


def test_rozbior_dzieli_logliki_warunkowe_i_bezwarunkowe():
    lls, bezw, konty, gold = M.rozbierz_mc(probka([-1, -2, -3, -4], 2, bezw=[-5, -6, -7, -8]))
    assert lls == [-1, -2, -3, -4] and bezw == [-5, -6, -7, -8] and gold == 2 and len(konty) == 4


def test_pusty_kontekst_nie_daje_pmi():
    # MultiBLiMP: kontekst pusty, PMI tożsamościowo 0 — trafienie 100% byłoby artefaktem
    _, bezw, _, _ = M.rozbierz_mc(probka([-1, -2], 0, konty=(" a", " b"), bezw=[-1, -2], ctx=""))
    assert bezw is None


def test_cel_tekstowy_mapowany_na_indeks():
    p = probka([-1, -2, -3], "maybe", konty=(" yes", " no", " maybe"))
    assert M.rozbierz_mc(p, z_pmi=False)[3] == 2


def test_pmi_odwraca_stala_litere():
    # model zawsze woli „A" (wysoki prior litery), PMI odejmuje prior i trafia w C
    o = M.oceny_mc(probka([-1.0, -3.0, -1.5, -3.0], 2, bezw=[-0.5, -3.0, -2.5, -3.0]))
    assert o["acc"] == 0.0 and o["acc_pmi"] == 1.0


def test_acc_norm_dzieli_przez_znaki_bez_separatora():
    o = M.oceny_mc(probka([-4.0, -6.0], 1, konty=(" ab", " abcdef")), z_pmi=False)
    assert o["acc"] == 0.0 and o["acc_norm"] == 1.0  # -4/2=-2 < -6/6=-1


def test_bpb_poprawnej_liczy_bajty_z_separatorem():
    o = M.oceny_mc(probka([-math.log(2) * 8, -1.0], 0, konty=(" ąb", " c")), z_pmi=False)
    assert abs(o["bpb_poprawnej"] - 8 / 4) < 1e-9  # " ąb" = 4 bajty UTF-8


def test_bazy_stala_predykcja_i_wiekszosc():
    oceny = [{"k": 4, "gold": g, "pred_acc": 0} for g in (0, 0, 1, 2)]
    b = M.bazy_mc(oceny, klasy_stale=True)
    assert b["chance_value"] == 0.25 and b["majority_value"] == 0.5
    assert b["majority_prediction_share"] == 1.0 and b["constant_prediction"] is True
    assert M.bazy_mc(oceny, klasy_stale=False)["majority_value"] is None


def test_srednia_se_i_ci():
    w = M.srednia_z_niepewnoscia([1, 0] * 100)
    assert w["value"] == 0.5 and w["n"] == 200
    assert abs(w["se"] - 0.5 / math.sqrt(200)) < 0.002
    assert w["ci95"][0] < 0.5 < w["ci95"][1]


def test_perplexity_bajtowa_i_tokenowa():
    ll = [-math.log(2) * 10, -math.log(2) * 30]
    pp = M.perplexity(ll, [2, 6], [10, 30], tokeny=[5, 15])
    assert abs(pp["bits_per_byte"]["value"] - 1.0) < 1e-9
    assert abs(pp["byte_perplexity"]["value"] - 2.0) < 1e-9
    assert abs(pp["token_perplexity"]["value"] - 4.0) < 1e-9


def test_ranking_panelu_nie_zalezy_od_kolejnosci_wejscia():
    ids = [f"q{i}" for i in range(50)]
    wybrane = {ids[i] for i in M.ranking_panel("arc", "arc_challenge", ids, 10)}
    odwrocone = ids[::-1]
    wybrane_odw = {odwrocone[i] for i in M.ranking_panel("arc", "arc_challenge", odwrocone, 10)}
    assert wybrane == wybrane_odw and len(wybrane) == 10


def test_obserwacja_procentowa_i_schemat():
    meta = {"metric": "accuracy", "unit": "percent", "higher_is_better": True}
    dig = {"source_id": "a" * 64, "results": "b" * 64, "runner": "c" * 64}
    o = M.obserwacja("T04", meta, "m", "p", {"value": 0.99, "n": 200, "ci95": [0.975, 1.0]},
                     {"chance_value": 0.5, "majority_value": None, "majority_prediction_share": None,
                      "constant_prediction": None}, 3272, 200, dig)
    assert abs(o["value"] - 99.0) < 1e-9 and o["reference"]["chance_value"] == 50.0
    zle = M.obserwacja("T44", meta, "m", "p", {"n": 0}, None, None, None, {}, state="blocked_access", reason="HF")
    wyniki = {k: [] for k in M.WYMAGANE_GORA}
    wyniki["observations"] = [o, zle]
    assert M.bledy_schematu(wyniki) == []
    wyniki["observations"] = [{**o, "results_sha256": None}]
    assert M.bledy_schematu(wyniki)


def test_wiersz_historii_puste_zamiast_zgadywania():
    rozsz = [{"task_id": "T03", "dodatkowe": {"space": {"byte_perplexity": {"value": 1.84634},
                                                        "token_perplexity": {"value": 30.123456}}}},
             {"task_id": "T04", "dodatkowe": {"space": {"acc": {"value": 0.99}}}}]
    w = M.wiersz_historii(rozsz, "1.06", 13848, 13848 * 2 ** 20, "f" * 64, "E")
    assert list(w) == M.KOLUMNY_HISTORII
    assert w["wikitext2_byte_ppl"] == "1.8463" and w["wikitext2_token_ppl"] == "30.1235"
    assert w["multiblimp_pl"] == "99.00" and w["eff"] == "" and w["arc_easy"] == "" and w["eval_gpu"] == "E"


def test_trace_wybory_dlugosci_i_pozycje():
    # poprawna B jest najdłuższa; acc wybiera najkrótszą A, acc_norm/bpb przechodzą na B
    p = probka([-3.0, -6.0, -9.0], 1, konty=(" ab", " abcdefghij", " abcde"), bezw=[-1.0, -9.0, -8.0])
    w = T.trace_pytania(p, licz_tokeny=lambda t: len(t.split()) or 1, id_pytania="q1")
    assert w["wybor"]["acc"] == "A" and w["wybor"]["acc_norm"] == "B" and w["wybor"]["bpb"] == "B"
    assert w["wybor_najkrotsza"]["acc"] and w["poprawna_najdluzsza"]
    assert w["opcje"][1]["tekst_bajty"] == 11 and w["opcje"][1]["pmi"] == 3.0
    r = T.rozklad_wyborow([w])
    assert r["reguly"]["acc"]["pozycje"] == {"A": 1} and r["reguly"]["acc_norm"]["trafnosc"] == 1.0


def _wiersz(i, trafione):
    return {"id": i, "wybor": {"acc_norm": "A" if trafione else "B"}, "trafione": {"acc_norm": trafione}}


def test_porownanie_checkpointow_przejscia_i_kolejnosc_wejscia():
    v1 = [_wiersz("q1", False), _wiersz("q2", True), _wiersz("q3", False)]
    v2 = [_wiersz("q3", True), _wiersz("q2", False), _wiersz("q1", True), _wiersz("q9", True)]
    wynik = T.porownaj_checkpointy([("1.05", v1), ("1.06", v2)])
    prz = wynik["przejscia"][0]
    assert prz["zle_na_dobre"] == 2 and prz["dobre_na_zle"] == 1
    assert prz["id_zle_na_dobre"] == ["q1", "q3"] and prz["id_dobre_na_zle"] == ["q2"]
    assert wynik["wersje"][0]["n"] == 3  # q9 tylko w jednej wersji — poza porównaniem


def test_mcnemar_dokladny():
    assert T.mcnemar_dokladny(0, 0) == 1.0
    assert abs(T.mcnemar_dokladny(0, 6) - 2 / 64) < 1e-12
    assert T.mcnemar_dokladny(3, 3) == 1.0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
