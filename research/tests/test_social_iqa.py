"""Social IQa T46 (benchmarks/social-iqa/zbierz_wyniki.py) i liczby w results/social_iqa.json.

Bez sieci i bez wag: pierwsza warstwa sprawdza składanie pliku liczb na atrapie wyjścia `common/ewaluuj.py`
(każdy test nazywa mutację, którą łapie), druga przelicza liczby z opublikowanego pliku wyników niezależnie
od skryptu. Uruchom: python tests/test_social_iqa.py (albo pytest).
"""
import importlib.util
import inspect
import json
import sys
import tempfile
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
DIR = KORZEN / "benchmarks" / "social-iqa"
WYNIKI = DIR / "results" / "social_iqa.json"

spec = importlib.util.spec_from_file_location("zbierz_wyniki_siqa", DIR / "zbierz_wyniki.py")
Z = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Z)


def _przebieg(katalog, gold, acc, se, share, digest="0" * 64, sha="1" * 64):
    """Atrapa katalogu wyjściowego `ewaluuj.py`: metryki w JSON, goldy w pliku per pytanie."""
    katalog.mkdir(parents=True, exist_ok=True)
    (katalog / "probki").mkdir(exist_ok=True)
    (katalog / "probki" / "T46_space.jsonl").write_text(
        "\n".join(json.dumps({"target": g}) for g in gold) + "\n", encoding="utf-8")
    metryki = {m: {"value": v, "se": 0.01, "ci95": [v - 0.02, v + 0.02]}
               for m, v in (("acc", acc), ("acc_norm", acc), ("acc_pmi", acc), ("bpb_poprawnej", 1.5))}
    (katalog / "results_rozszerzone.json").write_text(json.dumps({
        "observations": [{
            "n_scored": len(gold), "n_population": 1954,
            "dodatkowe": {"space": {**metryki,
                                    "bazy": {"chance_value": 1 / 3},
                                    "udzial_najczestszej_predykcji": share}},
            "source_id_digest": digest, "results_sha256": sha,
        }]
    }), encoding="utf-8")
    return katalog


def _atrapa(tmp, gold=(0, 0, 1, 2), acc=0.75, se=0.01, share=0.5, digest="0" * 64, sha="1" * 64):
    return _przebieg(tmp / "przebieg", gold, acc, se, share, digest, sha)


def test_baza_stalej_odpowiedzi_to_udzial_najczestszego_golda(tmp_path):
    """Mutacja: baza liczona z predykcji modelu albo z zaokrąglenia zamiast z goldów."""
    d = Z.wczytaj(_atrapa(tmp_path, gold=(0, 0, 0, 2)))
    assert d["bazy"]["stala_odpowiedz"] == 0.75
    assert d["bazy"]["rozklad_gold"] == {"0": 3, "2": 1} or d["bazy"]["rozklad_gold"] == {0: 3, 2: 1}


def test_baza_losowa_idzie_z_przebiegu_nie_z_goldow(tmp_path):
    """Mutacja: wpisanie 1/k na sztywno zamiast wartości z `ewaluuj.py`."""
    d = Z.wczytaj(_atrapa(tmp_path))
    assert d["bazy"]["losowa"] == 1 / 3


def test_udzial_najczestszej_predykcji_nie_miesza_sie_z_baza(tmp_path):
    """Mutacja: podmiana `udzial_najczestszej_predykcji` na bazę większościową."""
    d = Z.wczytaj(_atrapa(tmp_path, gold=(0, 0, 0, 0), share=0.25))
    assert d["udzial_najczestszej_predykcji"] == 0.25
    assert d["bazy"]["stala_odpowiedz"] == 1.0


def test_metryki_i_ci_sa_przepisane_bez_zmian(tmp_path):
    """Mutacja: przeliczenie SE, obcięcie CI95 albo zgubienie metryki pomocniczej."""
    d = Z.wczytaj(_atrapa(tmp_path, acc=0.61))
    assert d["acc"] == {"value": 0.61, "se": 0.01, "ci95": [0.59, 0.63]}
    for m in ("acc_norm", "acc_pmi", "bpb_poprawnej"):
        assert m in d, m


def test_n_i_digest_y_idą_z_przebiegu(tmp_path):
    """Mutacja: wpisanie n=200 na sztywno albo zgubienie digestu i sha256 wyników."""
    d = Z.wczytaj(_atrapa(tmp_path, gold=(0, 1, 2), digest="ab" * 32, sha="cd" * 32))
    assert d["n"] == 3 and d["n_population"] == 1954
    assert d["source_id_digest"] == "ab" * 32
    assert d["results_sha256"] == "cd" * 32


def test_zbuduj_ma_panel_pelny_i_metadane_zbioru(tmp_path):
    """Mutacja: zamiana panelu z pełnym splitem, zgubienie rewizji modelu albo zbioru."""
    p = _przebieg(tmp_path / "panel", (0, 1, 2), 0.5, 0.01, 0.4)
    f = _przebieg(tmp_path / "pelny", (0, 0, 1, 2), 0.75, 0.01, 0.6)
    w = Z.zbuduj(p, f)
    assert w["panel_space"]["n"] == 3 and w["pelny_split"]["n"] == 4
    assert w["zbior"]["rewizja"] == "8835ceb9141d7896d9d968634a9b21ae440e3ec5"
    assert w["zbior"]["n_population"] == 1954
    assert w["model"]["rewizja"] == "ef81be58742544ad32e1afab38db011fec209609"


def test_main_zapisuje_plik_wskazany_argumentem(tmp_path):
    """Mutacja: zapis zawsze do `results/social_iqa.json`, ignorowanie trzeciego argumentu."""
    p = _przebieg(tmp_path / "panel", (0, 1, 2), 0.5, 0.01, 0.4)
    f = _przebieg(tmp_path / "pelny", (0, 0, 1, 2), 0.75, 0.01, 0.6)
    cel = tmp_path / "wynik.json"
    argv = sys.argv
    sys.argv = ["zbierz_wyniki.py", str(p), str(f), str(cel)]
    try:
        Z.main()
    finally:
        sys.argv = argv
    d = json.loads(cel.read_text(encoding="utf-8"))
    assert d["panel_space"]["n"] == 3 and d["pelny_split"]["n"] == 4


def test_opublikowany_plik_zgadza_sie_z_rewizjami_z_karty():
    """Mutacja: podmiana rewizji zbioru lub modelu w results/social_iqa.json bez zmiany karty."""
    d = json.loads(WYNIKI.read_text(encoding="utf-8"))
    assert d["zbior"]["repo"] == "allenai/social_i_qa"
    assert d["zbior"]["rewizja"] == "8835ceb9141d7896d9d968634a9b21ae440e3ec5"
    assert d["zbior"]["split"] == "validation"
    assert d["model"]["repo"] == "SlayerLab/Slayer1B-1.06"
    assert d["model"]["rewizja"] == "ef81be58742544ad32e1afab38db011fec209609"


def test_opublikowane_bazy_zgadzaja_sie_z_plikiem_per_pytanie():
    """Mutacja: baza większościowa policzona z innego pliku niż wyniki, które są w repo, albo zaokrąglona."""
    import gzip
    from collections import Counter
    d = json.loads(WYNIKI.read_text(encoding="utf-8"))
    for klucz, nazwa in (("panel_space", "social_iqa.jsonl.gz"), ("pelny_split", "social_iqa_full.jsonl.gz")):
        with gzip.open(DIR / "results" / "slayer-1.06" / nazwa, "rt", encoding="utf-8") as f:
            gold = [int(json.loads(l)["target"]) for l in f if l.strip()]
        c = Counter(gold)
        assert d[klucz]["n"] == len(gold), (klucz, len(gold))
        assert d[klucz]["bazy"]["stala_odpowiedz"] == max(c.values()) / len(gold), klucz
        assert d[klucz]["bazy"]["losowa"] == 1 / 3 or abs(d[klucz]["bazy"]["losowa"] - 1 / 3) < 1e-12


def test_opublikowany_wynik_jest_w_granicach_swojego_ci():
    """Mutacja: acc i CI95 z różnych przebiegów (np. po podmianie pliku wyników)."""
    d = json.loads(WYNIKI.read_text(encoding="utf-8"))
    for klucz in ("panel_space", "pelny_split"):
        acc = d[klucz]["acc"]
        assert acc["ci95"][0] <= acc["value"] <= acc["ci95"][1], (klucz, acc)


def test_se_zgadza_sie_z_rozkladem_dwumianowym():
    """Mutacja: SE policzone inną metodą niż A albo z innego n.

    `ewaluuj.py` liczy s odchyleniem próbkowym (dzielnik n − 1), więc SE = √(p(1−p)/(n−1)), nie √(p(1−p)/n).
    """
    import math
    d = json.loads(WYNIKI.read_text(encoding="utf-8"))
    for klucz in ("panel_space", "pelny_split"):
        acc = d[klucz]["acc"]
        p, n = acc["value"], d[klucz]["n"]
        assert abs(acc["se"] - math.sqrt(p * (1 - p) / (n - 1))) < 1e-9, (klucz, acc["se"])


if __name__ == "__main__":
    testy = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    zle = 0
    for n, f in testy:
        try:
            if "tmp_path" in inspect.signature(f).parameters:  # pytest fixture, bez pytest
                with tempfile.TemporaryDirectory() as d:
                    f(Path(d))
            else:
                f()
            print(f"PASS {n}")
        except AssertionError as e:
            zle += 1
            print(f"FAIL {n}: {e}")
    print(f"{len(testy) - zle}/{len(testy)}")
    sys.exit(1 if zle else 0)
