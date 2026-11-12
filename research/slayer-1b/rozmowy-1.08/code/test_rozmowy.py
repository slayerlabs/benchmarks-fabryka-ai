"""Testy logiki bez wag: ocena, szablony, scorer logprob na atrapie z deterministycznymi logitami, pętla generacji.

python -I code/test_rozmowy.py   (kod wyjścia 0 = wszystko przechodzi)
"""
import math
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generuj  # noqa: E402
import modele  # noqa: E402
import ocena  # noqa: E402
import szablony  # noqa: E402


class Atrapa:
    """Tokenizer znakowy (id = ord), BOS = 1, EOS = 3; logity zależne od pozycji i poprzedniego tokenu."""
    eos = {3}
    limit = 4096
    klucz = "atrapa"

    def encode(self, t):
        return [1] + [ord(c) for c in t]

    def decode(self, ids):
        return "".join(chr(i) for i in ids if i > 3)

    def logity_pelne(self, ids):
        V = 400
        T = len(ids)
        x = torch.zeros(T, V)
        for i, t in enumerate(ids):
            x[i] = torch.sin(torch.arange(V, dtype=torch.float32) * (0.37 + 0.01 * (t % 7)) + i)
        return x

    def start(self, ids, B=1):
        self.ids = [list(ids) for _ in range(B)]
        return torch.stack([self.logity_pelne(r)[-1] for r in self.ids])

    def krok(self, toks):
        for r, t in zip(self.ids, toks):
            r.append(t)
        return torch.stack([self.logity_pelne(r)[-1] for r in self.ids])


def test_logprob_pozycje():
    m = Atrapa()
    ctx, ciag = "ab", " cd"
    lp, n, zg = modele.logprob_ciagu(m, ctx, ciag)
    ids = m.encode(ctx + ciag)
    ls = torch.log_softmax(m.logity_pelne(ids).double(), -1)
    ref = sum(float(ls[i - 1, ids[i]]) for i in range(len(m.encode(ctx)), len(ids)))
    assert n == 3 and zg and abs(lp - ref) < 1e-9, (lp, ref)
    # przesunięcie o 1 pozycję daje inną wartość (test zapala się na błędzie pozycji)
    zle = sum(float(ls[i, ids[i]]) for i in range(len(m.encode(ctx)), len(ids) - 1))
    assert abs(lp - zle) > 1e-3


def test_spacja_konca_kontekstu():
    m = Atrapa()
    ids, n_ctx, _ = modele.czesc_ciagu(m, "ab ", "cd")
    assert m.decode(ids[n_ctx:]) == " cd"


def test_bpb():
    assert abs(ocena.bpb(-math.log(2) * 8, 4) - 2.0) < 1e-12


def test_krotka_zdanie():
    assert ocena.ocen_krotka(" Mikołaj Kopernik.\nPolecenie", ["Kopernik"], []) == 1
    assert ocena.ocen_krotka(" Kopernikowski", ["Kopernik"], []) == 0
    assert ocena.ocen_krotka(" Tak, ale nie", ["tak"], ["nie"]) == 0
    assert ocena.ocen_krotka("\n\n Skłodowska-Curie", ["Skłodowska-Curie"], []) == 1
    assert ocena.ocen_zdanie(" Poszedłem do domu.", ["Poszedłem do domu."]) == 1
    assert ocena.ocen_zdanie(" Poszedłem do domu i spałem.", ["Poszedłem do domu."]) == 0


def test_liczba():
    assert ocena.wyciagnij_liczbe("2 · 3 = 6, potem 6 + 1. Wynik: 7") == 7
    assert ocena.wyciagnij_liczbe("Wynik: 12 500 zł") == 12500
    assert ocena.wyciagnij_liczbe("Wynik: 3,5") == 3.5
    assert ocena.wyciagnij_liczbe("najpierw 4, potem 9") == 9
    assert ocena.wyciagnij_liczbe("Wynik: -2") == -2
    assert ocena.wyciagnij_liczbe("brak") is None
    assert ocena.ocen_liczba("Wynik: 7", 7) == 1 and ocena.ocen_liczba("Wynik: 8", 7) == 0


def test_kod():
    odp = "\n```python\ndef f(x):\n    return x + 1\n```\nreszta"
    assert ocena.wyciagnij_kod(odp) == "def f(x):\n    return x + 1"
    assert ocena.ocen_kod(odp, "assert f(1) == 2")[0] == 1
    assert ocena.ocen_kod(odp, "assert f(1) == 3")[0] == 0
    assert ocena.uruchom_testy("while True: pass", "", limit_s=2)[0] == 0
    siec = "import socket\ns = socket.create_connection(('1.1.1.1', 80), timeout=3)"
    assert ocena.uruchom_testy(siec, "")[0] == 0, "sieć powinna być zablokowana"


def test_powtorzenia():
    assert ocena.powtorzone_3gramy("a b c a b c") == 0.25
    assert ocena.distinct_n("a b a b") == 2 / 3
    assert ocena.przeciek_rozumowania("x <think> y") == 1
    assert ocena.format_gsm8k("12-5=<<12-5=7>>7\n#### 7") == 1 and ocena.format_gsm8k("Wynik: 7") == 0


def test_szablony():
    poz = dict(kat="matematyka", typ="liczba", polecenie="Ile to 2+2?", wzorzec="2 + 2 = 4. Wynik: 4")
    shot = dict(kat="matematyka", typ="liczba", polecenie="Ile to 1+1?", wzorzec="Wynik: 2")
    a = szablony.prompt("A", poz, [shot])
    assert a == "Polecenie: Ile to 1+1?\nOdpowiedź: Wynik: 2\n\nPolecenie: Ile to 2+2?\nOdpowiedź:"
    assert szablony.ciag_wzorca("A", poz) == " 2 + 2 = 4. Wynik: 4"
    b = szablony.prompt("B", poz, [shot])
    assert b.endswith("### Zadanie\nIle to 2+2?\n### Rozwiązanie") and szablony.ciag_wzorca("B", poz).startswith("\n")
    assert szablony.utnij(" 4\nPolecenie: dalej", szablony.stopy("A", "matematyka")) == (" 4", True)
    en = dict(kat="angielski", typ="otwarte", polecenie="Write.", wzorzec="Text")
    assert szablony.prompt("A", en, []) == "Task: Write.\nAnswer:" and szablony.ciag_wzorca("A", en) == "\nText"


def test_petla_generacji():
    m = Atrapa()
    dek = generuj.DEKODOWANIA_A
    w1, _, _ = generuj.generuj_batch(m, "xyz", dek, 5, 12, ["\nPolecenie:"])
    w2, _, _ = generuj.generuj_batch(m, "xyz", dek, 5, 12, ["\nPolecenie:"])
    assert [w["surowa"] for w in w1] == [w["surowa"] for w in w2], "ten sam seed -> ta sama próbka"
    # greedy w batchu = greedy samodzielnie
    g, _, _ = generuj.generuj_batch(m, "xyz", [dek[3]], 5, 12, ["\nPolecenie:"])
    assert g[0]["surowa"] == w1[3]["surowa"]
    assert len({w["surowa"] for w in w1[:3]}) > 1, "różne seedy dają różne próbki"


def test_jakosc():
    import jakosc
    w = {"a": {"slayer": [1, 1, 1], "bielik": [1, 1, 1], "lfm": [1, 1, 1]},
         "b": {"slayer": [0, 0, 0], "bielik": [1, 1, 1], "lfm": [0, 1, 0]},
         "c": {"slayer": [0, 0, 0], "bielik": [0, 0, 0], "lfm": [0, 0, 0]},
         "d": {"slayer": [0, 1, 0], "bielik": [1, 0, 1], "lfm": [0, 1, 0]}}
    q = jakosc.jakosc_pozycji(w)
    assert [q[k]["klasa"] for k in "abcd"] == ["zawsze_dobrze", "rozroznia", "zawsze_zle", "nie_rozroznia"]
    assert abs(q["b"]["trudnosc"] - 4 / 9) < 1e-12 and abs(q["b"]["zakres"] - 1) < 1e-12
    assert abs(jakosc.pearson([1, 2, 3, 4], [2, 4, 6, 8]) - 1) < 1e-12 and jakosc.pearson([1, 1, 1], [1, 2, 3]) is None
    assert abs(jakosc.spearman([1, 2, 3, 4], [1, 4, 9, 16]) - 1) < 1e-12
    assert jakosc.rangi([3, 1, 3]) == [2.5, 1.0, 2.5]
    assert jakosc.kendall_tau([1, 2, 3], [1, 2, 3]) == 1 and jakosc.kendall_tau([1, 2, 3], [3, 2, 1]) == -1
    assert abs(jakosc.snr([0.2, 0.4, 0.6], [0.01, 0.01, 0.01]) - 4) < 1e-9
    # odwrócona kolejność wejścia nie zmienia klas (reguła repo o selektorach zależnych od kolejności)
    q2 = jakosc.jakosc_pozycji(dict(reversed(list(w.items()))))
    assert all(q2[k]["klasa"] == q[k]["klasa"] for k in w)


if __name__ == "__main__":
    testy = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in testy:
        t()
        print("OK", t.__name__)
    print(f"{len(testy)} testów OK")
