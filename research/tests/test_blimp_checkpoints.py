"""BLiMP over checkpoints and weight averaging (benchmarks/blimp/checkpoints.py, average_weights.py), dummy data only.
Run: python tests/test_blimp_checkpoints.py (or pytest)."""
import math
import sys
from pathlib import Path

import pytest

KORZEN = Path(__file__).resolve().parent.parent
KAT = KORZEN / "benchmarks" / "blimp"
sys.path.insert(0, str(KAT))
import blimp as B  # noqa: E402
import checkpoints as K  # noqa: E402

PROBKA = KORZEN / "common" / "tests" / "data" / "blimp.jsonl"


def docs():
    return B.wczytaj(PROBKA)


def wyniki(trafione, eps=1.0):
    return {i: {"id": i, "ll": [-1.0, -1.0 - eps] if t else [-1.0 - eps, -1.0]} for i, t in trafione.items()}


def test_nachylenie_ols():
    x = [1.0, 2.0, 4.0]
    assert math.isclose(K.nachylenie(x, [3.0, 5.0, 9.0]), 2.0)
    assert math.isclose(sum(K.wagi_ols(x)), 0.0, abs_tol=1e-12)
    assert math.isclose(K.mld(13848), 13848 * 2 ** 20 / 1e9)


def H_rosnace():
    """3 paradigms x 10 pairs, 3 models: model c hits the first 3 + c (+ paradigm offset) pairs."""
    return {f"g{g}": [[1 if i < 3 + c + g else 0 for i in range(10)] for c in range(3)] for g in range(3)}


def test_nachylenie_statystyki_wartosc_i_klastr():
    st = K.nachylenie_statystyki([0.0, 1.0, 2.0], H_rosnace(), boot=200)
    assert math.isclose(st["nachylenie"], 0.1)  # +1 pair of 10 per unit of x in every paradigm
    assert st["t"] is None and st["werdykt_klastr"] is None  # identical paradigm slopes: no variance, no verdict
    assert st["k"] == 3 and st["df"] == 2
    assert st["ci95"][0] <= 0.1 + 1e-9 <= st["ci95"][1] + 1e-9


def test_nachylenie_bootstrap_te_same_pary_dla_modeli():
    # identical hits in every model: slope 0 with zero spread only if the resample is shared across models
    H = {"g": [[1, 0, 1, 0, 1, 1, 0, 0, 1, 0]] * 3}
    st = K.nachylenie_statystyki([0.0, 1.0, 5.0], H, boot=300)
    assert st["nachylenie"] == 0.0 and st["se"] == 0.0


def test_nachylenie_odwrocona_kolejnosc_modeli():
    H = H_rosnace()
    a = K.nachylenie_statystyki([0.0, 1.0, 2.0], H, boot=100)
    Hr = {g: list(reversed(v)) for g, v in H.items()}
    b = K.nachylenie_statystyki([2.0, 1.0, 0.0], Hr, boot=100)
    assert math.isclose(a["nachylenie"], b["nachylenie"])


def test_werdykt_luki():
    base = {"nachylenie": 0.01, "werdykt": "pewne", "werdykt_klastr": "prawdopodobne", "ci95": [0.005, 0.02]}
    assert K.werdykt_luki(base) == "potwierdzone"
    assert K.werdykt_luki({**base, "werdykt_klastr": "szum"}) == "nierozstrzygniete"
    assert K.werdykt_luki({**base, "werdykt": "szum", "ci95": [-0.001, 0.02]}) == "obalone"
    assert K.werdykt_luki({**base, "nachylenie": -0.01, "ci95": [-0.02, -0.005]}) == "obalone"


def test_porownanie_klastrowe():
    Ha = {"a": [1, 1, 1, 1], "b": [1, 1, 0, 0], "c": [1, 0, 0, 0]}
    Hb = {"a": [1, 1, 0, 0], "b": [1, 1, 0, 0], "c": [0, 0, 0, 0]}
    r = K.porownanie_klastrowe(Ha, Hb)
    assert math.isclose(r["roznica"], 0.25) and r["df"] == 2 and r["k"] == 3
    assert math.isclose(r["se_klastr"], math.sqrt(((0.25) ** 2 + 0.25 ** 2 + 0) / 2) / math.sqrt(3))
    assert K.porownanie_klastrowe({"a": [1], "b": [0]}, {"a": [0], "b": [0]})["werdykt_klastr"] == "nierozstrzygalne"


def test_zmiany_wynikow_i_identyczne_zdania():
    d = docs()
    ids = [x["id"] for x in d]
    a = wyniki({i: True for i in ids})
    b = wyniki({i: k != 0 for k, i in enumerate(ids)}, eps=1e-6)
    r = K.zmiany_wynikow(d, a, b)
    assert r["zmienione_pary"] == 1 and r["w_progu"]
    assert math.isclose(r["max_abs_ll"], 1.0)  # hit [-1, -2] vs near-tie miss [-1 - 1e-6, -1]
    # a pair with identical sentences never counts as a change (tie = correct)
    same = [x for x in d if x["opcje"][0] == x["opcje"][1]]
    if same:
        c = dict(a); c[same[0]["id"]] = {"id": same[0]["id"], "ll": [-2.0, -1.0]}
        assert K.zmiany_wynikow(d, a, c)["zmienione_pary"] == 0


def test_kontrola_gpu_parami(tmp_path):
    import gzip
    import json
    d = docs()
    ids = [x["id"] for x in d]
    rows = {"A": {i: True for i in ids}, "B": {i: True for i in ids}, "C": {i: k > 1 for k, i in enumerate(ids)}}
    for g, t in rows.items():
        (tmp_path / g).mkdir()
        with gzip.open(tmp_path / g / "k13848.jsonl.gz", "wt") as f:
            for r in wyniki(t).values():
                f.write(json.dumps(r) + "\n")
    out = K.kontrola_gpu(d, tmp_path)
    by = {(r["a"], r["b"]): r["zmienione_pary"] for r in out}
    assert by == {("A", "B"): 0, ("A", "C"): 2, ("B", "C"): 2}
    assert K.kontrola_gpu(d, tmp_path / "brak") == []


def test_heldout_porownanie():
    okna = lambda xs: {"okna": [{"komponent": "web", "start": i, "loss": v} for i, v in enumerate(xs)]}
    r = K.heldout_porownanie(okna([1.0, 2.0, 3.0, 4.0]), okna([1.1, 2.0, 3.2, 4.1]))
    assert math.isclose(r["roznica"], -0.1)
    assert r["n_okien"] == 4 and r["z"] < 0
    # paired window by window: diffs -0.1, 0, -0.2, -0.1 (a shifted pairing keeps the mean but not this SE)
    d = [-0.1, 0.0, -0.2, -0.1]
    assert math.isclose(r["se"], math.sqrt(sum((v + 0.1) ** 2 for v in d) / 3) / 2)
    assert math.isclose(r["roznica_bity_na_token"], -0.1 / math.log(2)) and "roznica_bpb_na_token" not in r
    with pytest.raises(ValueError):
        K.heldout_porownanie(okna([1.0, 2.0]), {"okna": [{"komponent": "en", "start": 0, "loss": 1}, {"komponent": "web", "start": 1, "loss": 1}]})


def test_stale_protokolu():
    """CHECKPOINTS_THRESHOLDS.md and its amendments; a change here is a protocol change, not a fix."""
    assert K.GLOWNE == [7150, 8600, 10010, 13848]
    assert K.SREDNIE == {"avg3": [13750, 13800, 13848], "avg5": [13650, 13700, 13750, 13800, 13848],
                         "avg10": [13400, 13450, 13500, 13550, 13600, 13650, 13700, 13750, 13800, 13848]}
    assert K.SREDNIE_Q2 == ("avg3", "avg5")
    assert K.WYGASZANIE_VS_106 == -0.0504 and K.HELDOUT_1_06 == 2.33104 and K.HELDOUT_TOL == 0.0005
    assert K.PROG_SREDNIA == -0.01 and K.PROG_URZADZENIE == 30 and K.BOOT == 2000
    assert K.TOKENY_NA_KROK == 256 * 4096
    assert K.VAL_SHA == "86ebed396365110cfce1305d0647dbc0122031239af13e17c08ef62ba173b2d3"


def test_rosnie_wymaga_klastra_pewnego_albo_prawdopodobnego():
    base = {"nachylenie": 0.01, "holm": True}
    assert K.rosnie({**base, "werdykt_klastr": "pewne"}) and K.rosnie({**base, "werdykt_klastr": "prawdopodobne"})
    for w in ("szum", "nierozstrzygalne", None):
        assert not K.rosnie({**base, "werdykt_klastr": w})
    assert not K.rosnie({**base, "holm": False, "werdykt_klastr": "pewne"})
    assert not K.rosnie({**base, "nachylenie": -0.01, "werdykt_klastr": "pewne"})


def test_nachylenie_statystyki_se_klastra_rozne_nachylenia():
    # 3 paradigms x 10 pairs, models at x = 0, 1: paradigm slopes 0.1, 0.2, 0.4 (pairs hit: 3->4, 3->5, 3->7)
    H = {"a": [[1] * 3 + [0] * 7, [1] * 4 + [0] * 6], "b": [[1] * 3 + [0] * 7, [1] * 5 + [0] * 5],
         "c": [[1] * 3 + [0] * 7, [1] * 7 + [0] * 3]}
    st = K.nachylenie_statystyki([0.0, 1.0], H, boot=50)
    s = [0.1, 0.2, 0.4]
    m = sum(s) / 3
    se = math.sqrt(sum((v - m) ** 2 for v in s) / 2) / math.sqrt(3)
    assert math.isclose(st["nachylenie"], m) and math.isclose(st["se_klastr"], se) and math.isclose(st["t"], m / se)
    assert st["df"] == 2


def test_nachylenie_reszty_i_zastrzezenia():
    r = K.nachylenie_reszty([0.0, 1.0, 2.0, 3.0], [0.0, 1.0, 1.0, 3.0])
    # by hand: sxx = 5, sxy = 4.5, slope 0.9, intercept -0.1, fitted -0.1, 0.8, 1.7, 2.6
    assert math.isclose(r["nachylenie"], 0.9)
    res = [0.1, 0.2, -0.7, 0.4]
    se = math.sqrt(sum(v * v for v in res) / 2 / 5.0)
    assert math.isclose(r["se_reszty"], se) and math.isclose(r["t"], 0.9 / se) and r["df"] == 2
    mocny = {"nachylenie": 0.01, "werdykt": "pewne", "werdykt_klastr": "pewne"}
    assert K.zastrzezenia_luki(mocny, {"werdykt": "pewne"}) == []
    assert K.zastrzezenia_luki({**mocny, "nachylenie": -0.01}, {"werdykt": "szum"}) == [
        "bez_ostatniego_punktu_brak_wzrostu", "trend_nieodroznialny_od_wahan_miedzy_checkpointami"]
    assert K.zastrzezenia_luki({**mocny, "werdykt_klastr": "szum"}, {"werdykt": None})[0] == "bez_ostatniego_punktu_brak_wzrostu"


def test_wklad_paradygmatow():
    Ha = {"a": [1, 1], "b": [1, 0], "c": [0, 0]}
    Hb = {"a": [0, 0], "b": [0, 0], "c": [1, 1]}
    r = K.wklad_paradygmatow(Ha, Hb, ile=1)
    assert r["top"] == [{"grupa": "a", "wklad": 1 / 3}]
    assert math.isclose(r["suma_top"] + r["bez_top"], (1 + 0.5 - 1) / 3)
    # a fall: the top paradigms are the ones that fall most, not the one with the largest rise
    s = K.wklad_paradygmatow(Hb, Ha, ile=1)
    assert s["top"] == [{"grupa": "a", "wklad": -1 / 3}] and math.isclose(s["suma_top"] + s["bez_top"], -0.5 / 3)
    d = K.wklad_paradygmatow({"a": [1], "b": [0], "c": [0]}, {"a": [0], "b": [1], "c": [1]}, ile=2)
    assert [t["grupa"] for t in d["top"]] == ["b", "c"]


def test_przerwane_przebiegi():
    log = ('{"etap": "pobranie", "krok": 1430}\n{"step": 1430, "x": 1}\n[blimp] 64/128  1s\r[blimp] 128/128  2s\n'
           '{"step": 5720}\n[blimp] 64/128  1s\r[blimp] 96/128  2s\n')
    assert K.przerwane_przebiegi(log) == [{"krok": 5720, "pary": 96, "wszystkie": 128, "udzial": 0.75}]
    assert K.przerwane_przebiegi("") == []


def okna_(xs, komp=None):
    return {"loss": sum(xs) / len(xs), "okna": [{"komponent": (komp or ["web"] * len(xs))[i], "start": i, "loss": v}
                                                for i, v in enumerate(xs)]}


def test_heldout_komponenty_i_odniesienie(tmp_path):
    k = ["web", "core", "web", "core"]
    r = K.heldout_komponenty(okna_([1.0, 2.0, 3.0, 4.0], k), okna_([1.5, 2.0, 3.5, 3.0], k))
    assert math.isclose(r["web"]["roznica"], -0.5) and math.isclose(r["core"]["roznica"], 0.5) and r["web"]["n_okien"] == 2
    import json
    for n, xs in {"1.06": [2.0, 2.0], "A": [1.9, 1.95], "B": [1.95, 2.0]}.items():
        (tmp_path / f"heldout_{n}.json").write_text(json.dumps(okna_(xs)))
    ref = K.odniesienie_wygaszania(tmp_path)
    assert math.isclose(ref["loss_1.06"], 2.0) and math.isclose(ref["A_vs_1.06"]["roznica"], -0.075)
    assert math.isclose(ref["A_vs_B"]["roznica"], -0.05)
    assert K.odniesienie_wygaszania(tmp_path / "brak") is None


def kr_atrapa():
    return {"kontrola_urzadzenia": {"w_progu": True}, "kontrola_gpu": [{"w_progu": True}], "konwersja_13848_max_abs": 0.0,
            "sha_ckpt_zgodne": True, "nachylenie": {"werdykt_luki": "potwierdzone"},
            "srednie": {"avg3": {"sklad_zgodny_z_protokolem": True, "sha_ckpt_zgodne": True}},
            "heldout": {"kontrola_1.06": True, "val_sha256_zgodne": True, "odniesienia_zgodne_z_protokolem": True,
                        "werdykt_substytut": "potwierdzone"}}


@pytest.mark.parametrize("zepsuj, q1, q2", [
    (lambda k: None, "potwierdzone", "potwierdzone"),
    (lambda k: k["heldout"].update({"kontrola_1.06": False}), "potwierdzone", "nieustalone"),
    (lambda k: k["heldout"].update({"val_sha256_zgodne": False}), "potwierdzone", "nieustalone"),
    (lambda k: k["heldout"].pop("val_sha256_zgodne"), "potwierdzone", "nieustalone"),
    (lambda k: k["heldout"].update({"odniesienia_zgodne_z_protokolem": False}), "potwierdzone", "nieustalone"),
    (lambda k: k.update({"konwersja_13848_max_abs": 1e-3}), "nieustalone", "nieustalone"),
    (lambda k: k.update({"kontrola_urzadzenia": {"w_progu": False}}), "nieustalone", "nieustalone"),
    (lambda k: k["kontrola_gpu"].append({"w_progu": False}), "nieustalone", "nieustalone"),
    (lambda k: k.update({"kontrola_gpu": []}), "nieustalone", "nieustalone"),  # no copies = no control
    (lambda k: k["srednie"]["avg3"].update({"sha_ckpt_zgodne": False}), "potwierdzone", "nieustalone"),
    (lambda k: k.update({"sha_ckpt_zgodne": False}), "nieustalone", "nieustalone"),
    (lambda k: k["srednie"]["avg3"].update({"sklad_zgodny_z_protokolem": False}), "potwierdzone", "nieustalone"),
])
def test_kontrole_blokuja_werdykt(zepsuj, q1, q2):
    k = kr_atrapa()
    zepsuj(k)
    out = K.zastosuj_kontrole(k)
    assert out["nachylenie"]["werdykt_luki"] == q1 and out["heldout"]["werdykt_substytut"] == q2
    if q2 == "nieustalone":
        assert out["heldout"]["werdykt_przed_kontrola"] == "potwierdzone"


def test_sklad_srednich_z_logu(tmp_path):
    import json
    (tmp_path / "averages.jsonl").write_text(
        json.dumps({"model": "avg3", "kroki": [13848, 13800, 13750], "sha256_safetensors": "x"}) + "\n"
        + json.dumps({"model": "avg5", "kroki": [13848, 13800, 13750, 13700, 13600]}) + "\n")
    pob = [{"repo": "SlayerLab/Slayer1B-1.06-checkpoints", "krok": s, "zgodny_z_lfs": True} for s in (13848, 13800, 13750)]
    r = K.sklad_srednich(tmp_path, pob)
    assert r["avg3"]["kroki"] == [13750, 13800, 13848] and r["avg3"]["sklad_zgodny_z_protokolem"] and r["avg3"]["sha_ckpt_zgodne"]
    assert r["avg5"]["sklad_zgodny_z_protokolem"] is False and r["avg5"]["sha_ckpt_zgodne"] is False
    assert K.sklad_srednich(tmp_path / "brak", pob) == {}


def test_werdykt_sredniej_progi():
    assert K.werdykt_sredniej({"avg3": {"roznica": -0.03, "z": -10.0}}) == "potwierdzone"
    assert K.werdykt_sredniej({"avg3": {"roznica": -0.02, "z": -10.0}}) == "obalone"  # share < 0.5
    assert K.werdykt_sredniej({"avg3": {"roznica": -0.03, "z": -2.5}}) == "obalone"  # |z| < 3
    assert K.werdykt_sredniej({"avg3": {"roznica": -0.01, "z": -9.0}, "avg10": {"roznica": -0.026, "z": -4.0}}) == "potwierdzone"
    # amendment 1: the verdict over avg3/avg5 ignores avg10
    assert K.werdykt_sredniej({"avg3": {"roznica": -0.01, "z": -9.0}, "avg10": {"roznica": -0.026, "z": -4.0}},
                              K.SREDNIE_Q2) == "obalone"


def test_average_weights_atrapa(tmp_path):
    torch = pytest.importorskip("torch")
    import average_weights as S
    from safetensors.torch import load_file, save_file
    wz = {"tok.weight": torch.zeros(4, 2), "a.weight": torch.zeros(3)}
    save_file(wz, str(tmp_path / "model.safetensors"))
    (tmp_path / "config.json").write_text("{}")
    (tmp_path / "tokenizer.json").write_text("{}")
    pliki = []
    for i, st in enumerate([30, 20, 10]):
        p = tmp_path / f"c{st}.pt"
        torch.save({"step": st, "opt": torch.zeros(2), "model": {
            "_orig_mod.tok.weight": torch.full((4, 2), float(i)), "_orig_mod.head.weight": torch.full((4, 2), float(i)),
            "_orig_mod.a.weight": torch.full((3,), 10.0 * i) + 0.1}}, p)
        pliki.append(str(p))
    S.main(["--wzor", str(tmp_path), "--wyjscie", str(tmp_path), "--zapisz", "1,3", *pliki])
    a1 = load_file(str(tmp_path / "avg1" / "model.safetensors"))
    a3 = load_file(str(tmp_path / "avg3" / "model.safetensors"))
    assert torch.equal(a1["tok.weight"], torch.zeros(4, 2))
    assert torch.allclose(a3["tok.weight"], torch.ones(4, 2)) and torch.allclose(a3["a.weight"], torch.full((3,), 10.1))
    assert a3["a.weight"].dtype == torch.float32 and "head.weight" not in a3
    import json
    cfg = json.loads((tmp_path / "avg3" / "config.json").read_text())
    assert cfg["srednia_krokow"] == [30, 20, 10] and cfg["step"] == 30


def test_sample_gpu_podsumowanie():
    import sample_gpu
    s = sample_gpu.podsumuj([(0, 50.0, 1000.0, 10.0), (2, 100.0, 3000.0, 30.0)])
    assert s == {"gpu_util_sr": 75.0, "gpu_mem_max_MiB": 3000.0, "cpu_util_sr": 20.0, "probek": 2}
    assert sample_gpu.podsumuj([])["gpu_util_sr"] is None


def test_liczby_porownania_krzywej_klastr_i_luka():
    sys.path.insert(0, str(KORZEN / "tools"))
    import liczby as Lz
    st = {"nachylenie": 0.01, "se": 0.002, "se_klastr": 0.004, "k": 67, "df": 66, "p_klastr": 0.02,
          "werdykt_klastr": "prawdopodobne"}
    kr = {"punkty": [{"etykieta": "k13848", "luka_pythia": {"roznica": -0.03, "se": 0.0015}}],
          "nachylenie": st, "nachylenie_zjawiska": {"binding": {**st, "k": 2, "df": 1, "werdykt_klastr": "nierozstrzygalne"}},
          "kroki": [{"od": 7150, "do": 13848, "roznica": 0.02, "se": 0.004, **{k: st[k] for k in ("se_klastr", "k", "df", "p_klastr", "werdykt_klastr")}}]}
    por = {p["id"]: p for p in Lz.porownania_krzywej(kr)}
    luka = por["k13848_vs_pythia/blimp_krzywa_luka/acc"]
    assert math.isclose(luka["z"], -20.0) and luka["werdykt"] == "pewne" and luka["test"] == "blimp"
    n = por["krzywa/blimp_krzywa_nachylenie/acc"]
    assert math.isclose(n["roznica"], 0.01) and math.isclose(n["z"], 5.0) and n["werdykt"] == "pewne"
    k = por["krzywa/blimp_krzywa_nachylenie_klastr/acc"]
    assert k["werdykt"] == "prawdopodobne" and k["df"] == 66  # verdict from the t p-value, not from |t| = 2.5
    assert por["krzywa/blimp_krzywa_nachylenie_klastr_binding/acc"]["werdykt"] == "nierozstrzygalne"
    meta = Lz.raporty_krzywej(kr)[0]
    assert meta["grupy"][0]["werdykt"] == "nierozstrzygalne" and meta["generator"]["wejscie"] == "benchmarks/blimp/results/checkpoints.json"


def test_average_weights_odrzuca_zle_wejscie():
    torch = pytest.importorskip("torch")
    import average_weights as S
    acc = S.Srednia({"tok.weight": torch.zeros(2, 2)})
    with pytest.raises(ValueError):
        acc.dodaj({"tok.weight": torch.zeros(3, 2)})
    with pytest.raises(ValueError):
        acc.dodaj({"inne": torch.zeros(2, 2)})
    with pytest.raises(ValueError):
        acc.dodaj({"tok.weight": torch.zeros(2, 2), "head.weight": torch.ones(2, 2)})


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
