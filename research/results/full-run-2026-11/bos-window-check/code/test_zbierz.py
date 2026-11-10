"""Testy logiki zbierz.py i warunek_kontroli.py na atrapie wynikow. Uruchomienie: python -m pytest test_zbierz.py -q"""
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

KOD = Path(__file__).parent
spec = importlib.util.spec_from_file_location("zbierz", KOD / "zbierz.py")
Z = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Z)

MET = {"T51": "acc", "T05": "acc_norm", "T17": "acc", "T06": "acc_norm", "T07": "acc", "T14": "acc", "T03": "byte_perplexity"}
STARE = {"T51": 0.55, "T05": 0.47, "T17": 0.56, "T06": 0.7, "T07": 0.54, "T14": 0.67, "T03": 2.4}
SE_ST, SE_NW, SE_A = 0.03, 0.04, 0.05
ZNACZNIK = "2026-11-10T10:10:41"


def obs(v, metric, n=100):
    k = metric.split(",")[0]
    return {"observations": [{"value": v, "state": "ok", "metric": metric, "n_scored": n, "results_sha256": "r", "runner_sha256": "x",
                              "reference": {"chance_value": 0.25, "majority_value": 0.3},
                              "dodatkowe": {"space": {k: {"value": v, "n": n, "se": SE_NW, "se_a": SE_A, "metoda_se": "K"},
                                                      "bpb_poprawnej": {"value": 2.0}, "udzial_najczestszej_predykcji": 0.5}}}]}


def zapis(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d), encoding="utf-8")


def zapis_jsonl(p, w):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(x) + "\n" for x in w), encoding="utf-8")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def zbuduj(tmp, roznice=None, kontrola=0.7095, arc=0.42, stare_wpisy=False, kody=None, stan_kontroli="ok"):
    """Drzewo wejsc; roznice = {zadanie: nowa - stara}. T06 w parach: 100 pytan, 10 trafien wiecej po BOS."""
    roznice = roznice or {}
    sur, fr = tmp / "sur", tmp / "fr"
    man = fr / "manifest.jsonl"
    wiersze = [{"model": "pythia-1b-v0", "zadanie": t, "wartosc": STARE[t], "se": SE_ST, "n": 100, "metryka": MET[t] + ",none",
                "results_sha256": "r"} for t in MET]
    wiersze += [{"model": "slayer1b-1.07-hf", "zadanie": t, "wartosc": v, "se": 0.02, "n": 100, "metryka": "m", "results_sha256": "s"}
                for t, v in (("T51", 0.65), ("T03", 1.8))]
    zapis_jsonl(man, wiersze)
    zapis(fr / "wsc273" / "pythia-1b-v0" / "results_rozszerzone.json", obs(0.67, "acc,none"))
    wynik_kontroli = obs(kontrola, "acc_norm,none")
    wynik_kontroli["observations"][0]["state"] = stan_kontroli
    zapis(sur / "kontrola" / "piqa" / "pythia-1b-v0" / "results_rozszerzone.json", wynik_kontroli)
    zapis_jsonl(sur / "kontrola" / "piqa" / "pythia-1b-v0" / "probki" / "T06_space.jsonl",
                [{"doc_id": i, "acc_norm": 0.0, "arguments": []} for i in range(100)])
    wpisy = [{"wariant": "KONTROLA", "zadanie": "T06", "start": "2026-11-10T10:11:00", "kod": 0}]
    for t, kat in Z.KATALOG.items():
        if t == "T02":
            continue
        war = "okno" if t == "T03" else "bos"
        d = sur / war / kat / "pythia-1b-v0"
        zapis(d / "results_rozszerzone.json", obs(STARE[t] + roznice.get(t, 0.01), MET[t] + ",none"))
        pr = [{"doc_id": i, "acc_norm": float(i < 10), "arguments": [["c", "x"]]} for i in range(100)]
        zapis_jsonl(d / "probki" / f"{t}_space.jsonl", pr)
        if war == "bos":
            zapis_jsonl(d / "bos.jsonl", [{"t": "z", "n": 1, "w": 1, "d": 3} for _ in range(100)] + [{"t": "m", "n": 1}])
        wpisy.append({"wariant": war.upper(), "zadanie": t, "start": "2026-11-10T10:12:00", "kod": 0})
    a = sur / "kontrola-arc" / "arc-challenge" / "eurollm-1.7b"
    zapis(a / "results_rozszerzone.json", obs(arc, "acc_norm,none"))
    ctx = "Question: q2\nAnswer: a\n\nQuestion: spoza\nAnswer: b\n\nQuestion: q1\nAnswer:"
    zapis_jsonl(a / "probki" / "T02_space.jsonl", [{"doc_id": 0, "doc": {"question": "q1"}, "arguments": [[ctx, " a"]]},
                                                   {"doc_id": 1, "doc": {"question": "q2"}, "arguments": [["Question: q2\nAnswer:", " a"]]}])
    wpisy.append({"wariant": "KONTROLA-ARC", "zadanie": "T02", "start": "2026-11-10T10:30:00", "kod": 0})
    if stare_wpisy:
        wpisy = [{**w, "start": "2026-11-10T10:00:00"} for w in wpisy]
    wpisy = [{**w, "kod": (kody or {}).get((w["wariant"], w["zadanie"]), 0)} for w in wpisy]
    zapis_jsonl(sur / "kolejka.jsonl", wpisy)
    (sur / "NOWY_START").write_text(ZNACZNIK + "\n")
    return sur, man


def uruchom(tmp, popsuj=None, **k):
    sur, man = zbuduj(tmp, **k)
    wej = tmp / "sha_wejsc.json"
    zapis(wej, {"manifest": sha(man), "wsc273_stary": sha(man.parent / "wsc273" / "pythia-1b-v0" / "results_rozszerzone.json"),
                "surowe": {str(p.relative_to(sur)): sha(p) for p in sur.rglob("*") if p.is_file()}})
    if popsuj:
        popsuj(sur, man)
    wy = tmp / "LICZBY.json"
    stary = sys.argv
    sys.argv = ["zbierz.py", str(sur), str(man), str(wy), str(wej)]
    try:
        Z.main()
    finally:
        sys.argv = stary
    return json.loads(wy.read_text(encoding="utf-8"))


@pytest.mark.parametrize("z,oczek", [(3.0, "pewne"), (-3.0, "pewne"), (2.99, "prawdopodobne"), (2.0, "prawdopodobne"), (-2.0, "prawdopodobne"),
                                     (1.99, "szum"), (0.0, "szum")])
def test_progi_werdyktu(z, oczek):
    assert Z.werdykt_z(z) == oczek


@pytest.mark.parametrize("d,oczek", [(0.0399, "maly"), (0.0401, "duzy"), (-0.0401, "duzy")])
def test_prog_wplywu(tmp_path, d, oczek):
    assert uruchom(tmp_path, roznice={"T07": d})["wplyw"] == oczek


def test_kazdy_z_szesciu_liczy_sie_a_t03_nie(tmp_path):
    assert uruchom(tmp_path, roznice={"T03": 0.5})["wplyw"] == "maly"
    (tmp_path / "b").mkdir()
    assert uruchom(tmp_path / "b", roznice={"T14": 0.05})["wplyw"] == "duzy"


def test_se_roznicy_niezalezne(tmp_path):
    p = uruchom(tmp_path)["pary"]["T51"]
    assert p["se_roznicy"] == pytest.approx(math.hypot(SE_ST, SE_NW))
    assert p["z"] == pytest.approx(0.01 / math.hypot(SE_ST, SE_NW))


def test_se_w_parach_t06(tmp_path):
    w = uruchom(tmp_path)["pary"]["T06"]["w_parach"]
    assert w["n"] == 100 and w["zmienione_pytania"] == 10
    assert w["srednia_roznica_bos_minus_kontrola"] == pytest.approx(0.1)
    assert w["se"] == pytest.approx(math.sqrt(0.09 * 100 / 99 / 100), rel=1e-9)


def test_filtr_znacznika_pomija_stare_wpisy(tmp_path):
    L = uruchom(tmp_path, stare_wpisy=True)
    assert L["kontrola"] is None and L["pomiar_wazny"] is False and L["pary"]["T51"]["stan"] == "brak wyniku"
    assert L["wpisy_kolejki"]["przed_znacznikiem_pominiete"] == 9


def test_filtr_znacznika_bierze_nowe(tmp_path):
    L = uruchom(tmp_path)
    assert L["pomiar_wazny"] is True and L["pary"]["T51"]["nowa"] is not None
    assert L["wpisy_kolejki"]["przed_znacznikiem_pominiete"] == 0


@pytest.mark.parametrize("v,oczek", [(0.7095, True), (0.70946, True), (0.7094, False), (0.71, False), (0.7096, False)])
def test_warunek_kontroli_w_zbierz(tmp_path, v, oczek):
    assert uruchom(tmp_path, kontrola=v)["pomiar_wazny"] is oczek


@pytest.mark.parametrize("v,oczek", [(0.7095, "tak"), (0.70946, "tak"), (0.7094, "nie"), (0.71, "nie")])
def test_warunek_kontroli_skrypt(tmp_path, v, oczek):
    p = tmp_path / "r.json"
    zapis(p, obs(v, "acc_norm,none"))
    w = subprocess.run([sys.executable, str(KOD / "warunek_kontroli.py"), str(p)], capture_output=True, text=True)
    assert w.stdout.strip() == oczek


def test_warunek_kontroli_brak_pliku(tmp_path):
    w = subprocess.run([sys.executable, str(KOD / "warunek_kontroli.py"), str(tmp_path / "x.json")], capture_output=True, text=True)
    assert w.stdout.strip() == "nie"


def test_sha_wejsc_zapala_sie_na_podmianie(tmp_path):
    sur, man = zbuduj(tmp_path)
    wej = tmp_path / "s.json"
    zapis(wej, {"manifest": sha(man), "wsc273_stary": sha(man.parent / "wsc273" / "pythia-1b-v0" / "results_rozszerzone.json"),
                "surowe": {str(p.relative_to(sur)): sha(p) for p in sur.rglob("*") if p.is_file()}})
    with (sur / "bos" / "piqa" / "pythia-1b-v0" / "results_rozszerzone.json").open("a") as f:
        f.write(" ")
    with pytest.raises(SystemExit) as e:
        Z.sprawdz_wejscia(wej, sur, man, man.parent / "wsc273" / "pythia-1b-v0" / "results_rozszerzone.json")
    assert e.value.code == 1


def test_sha_wejsc_zapala_sie_na_dodatkowym_pliku(tmp_path):
    sur, man = zbuduj(tmp_path)
    wej = tmp_path / "s.json"
    zapis(wej, {"manifest": sha(man), "wsc273_stary": sha(man.parent / "wsc273" / "pythia-1b-v0" / "results_rozszerzone.json"),
                "surowe": {str(p.relative_to(sur)): sha(p) for p in sur.rglob("*") if p.is_file()}})
    (sur / "nowy.txt").write_text("x")
    with pytest.raises(SystemExit):
        Z.sprawdz_wejscia(wej, sur, man, man.parent / "wsc273" / "pythia-1b-v0" / "results_rozszerzone.json")


def test_kontrola_arc_liczbowy_i_zastrzezenie(tmp_path):
    c = uruchom(tmp_path, arc=0.4347)["kontrola_arc"]
    assert c["warunek_liczbowy_spelniony"] is True and "nierozstrzygnieta" in c["werdykt_kontroli"] and "przechodzi" not in c
    (tmp_path / "b").mkdir()
    c2 = uruchom(tmp_path / "b", arc=0.4348)["kontrola_arc"]
    assert c2["warunek_liczbowy_spelniony"] is False


def test_demonstracje_rozklad_i_spoza_testu(tmp_path):
    d = uruchom(tmp_path)["kontrola_arc"]["demonstracje"]
    assert d == {"pytan": 2, "rozklad_liczby_demonstracji": {"0": 1, "2": 1}, "demonstracje_spoza_testu": 1}


def test_se_klastrowe_t07_t14(tmp_path):
    p = uruchom(tmp_path)["pary"]["T07"]["se_klastrowe"]
    assert p["se_roznicy_po_pozycjach"] == pytest.approx(math.hypot(SE_A, SE_ST))
    assert p["z_po_pozycjach"] == pytest.approx(0.01 / math.hypot(SE_A, SE_ST))
    assert p["metoda_se"] == "K"


def test_t03_i_arc_easy_i_wsc(tmp_path):
    L = uruchom(tmp_path, roznice={"T03": -0.7})
    assert L["t03_slayer"]["nowa_roznica_pythia_minus_slayer"] == pytest.approx(1.7 - 1.8)
    assert L["t03_slayer"]["stara_roznica_pythia_minus_slayer"] == pytest.approx(0.6)
    a = L["arc_easy"]
    assert a["roznica"] == pytest.approx(0.65 - 0.56)
    assert a["trafien_nad_progiem_z_2"] == pytest.approx((0.09 - 2 * math.hypot(0.02, SE_NW)) * 100)
    assert L["wsc273_poboczne_poza_protokolem"]["roznica"]["bpb_poprawnej"] == pytest.approx(0.0)


def dopisz(p, tekst):
    with Path(p).open("a") as f:
        f.write(tekst)


POPSUJ = {
    "manifest": lambda sur, man: dopisz(man, '{"model": "x", "zadanie": "y"}\n'),
    "stary_wsc": lambda sur, man: dopisz(man.parent / "wsc273" / "pythia-1b-v0" / "results_rozszerzone.json", " "),
    "surowy": lambda sur, man: dopisz(sur / "bos" / "piqa" / "pythia-1b-v0" / "results_rozszerzone.json", " "),
}


@pytest.mark.parametrize("cel", POPSUJ)
def test_main_nie_liczy_przy_niezgodnym_sha(tmp_path, cel):
    with pytest.raises(SystemExit) as e:
        uruchom(tmp_path, popsuj=POPSUJ[cel])
    assert e.value.code == 1
    assert not (tmp_path / "LICZBY.json").exists()


def test_para_z_kodem_bledu_nie_liczy_sie(tmp_path):
    L = uruchom(tmp_path, kody={("BOS", "T51"): 1})
    assert L["pary"]["T51"]["stan"] == "brak wyniku" and L["wplyw"] == "niekompletne"


def test_kontrola_z_kodem_bledu_uniewaznia_pomiar(tmp_path):
    L = uruchom(tmp_path, kody={("KONTROLA", "T06"): 1})
    assert L["kontrola"] is None and L["pomiar_wazny"] is False and L["wplyw"] == "nierozstrzygniete"


def test_stara_roznica_arc_easy(tmp_path):
    assert uruchom(tmp_path)["arc_easy"]["stara_roznica"] == pytest.approx(0.65 - 0.55)


@pytest.mark.parametrize("value,metric,chance,oczek", [
    (1.5, "byte_perplexity,none", None, True), (1.0, "byte_perplexity,none", None, False), (0.9, "byte_perplexity,none", None, False),
    (1.0, "acc,none", 0.25, False), (0.5, "acc,none", None, True), (0.21, "acc,none", 0.25, True), (0.19, "acc,none", 0.25, False)])
def test_kontrola_sensu(value, metric, chance, oczek):
    assert Z.kontrola_sensu({"value": value, "metric": metric, "chance": chance}) is oczek


def test_pole_sensowny_pary(tmp_path):
    L = uruchom(tmp_path, roznice={"T51": -0.4, "T03": -1.5})
    assert L["pary"]["T51"]["sensowny"] is False and L["pary"]["T03"]["sensowny"] is False and L["pary"]["T05"]["sensowny"] is True


def test_pole_sensowny_kontrola_i_arc(tmp_path):
    L = uruchom(tmp_path, kontrola=0.1, arc=0.1)
    assert L["kontrola"]["sensowny"] is False and L["kontrola_arc"]["sensowny"] is False


def test_bos_kontrola_zliczenia(tmp_path):
    d = tmp_path / "k"
    zapis_jsonl(d / "bos.jsonl", [{"t": "z", "n": 1, "w": 1, "d": 3}, {"t": "z", "n": 1, "w": 1, "d": 4}, {"t": "z", "n": 2, "w": 1, "d": 4},
                                  {"t": "z", "n": 1, "w": 0, "d": 4}, {"t": "m", "n": 1}, {"t": "m", "n": 1}, {"t": "m", "n": 2}])
    zapis_jsonl(d / "probki" / "T51_space.jsonl", [{"arguments": [["c", "x"], ["c", "y"]]}, {"arguments": [["c", "z"], ["c", "v"]]}])
    b = Z.bos_kontrola(d, "T51")
    assert (b["zadan_w_dzienniku"], b["zadan_w_probkach"], b["zgodne"]) == (4, 4, True)
    assert b["zadan_z_jednym_bos"] == 2 and b["procent_jeden_bos"] == pytest.approx(50.0)
    assert b["wywolan_modelu"] == 3 and b["wywolan_z_jednym_bos"] == 2


def test_warunek_kontroli_skrypt_wymaga_stanu_ok(tmp_path):
    p = tmp_path / "r.json"
    d = obs(0.7095, "acc_norm,none")
    d["observations"][0]["state"] = "invalid"
    zapis(p, d)
    w = subprocess.run([sys.executable, str(KOD / "warunek_kontroli.py"), str(p)], capture_output=True, text=True)
    assert w.stdout.strip() == "nie"


def test_warunek_kontroli_zbierz_wymaga_stanu_ok(tmp_path):
    assert uruchom(tmp_path, stan_kontroli="invalid")["pomiar_wazny"] is False
