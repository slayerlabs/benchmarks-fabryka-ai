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


MODELE_DIR = modele.MODELE  # tokenizery z katalogów wag (bez wczytywania wag)


def _tokenizer_hf(klucz):
    from transformers import AutoTokenizer
    kat = MODELE_DIR / modele.REJESTR[klucz][0]
    if not (kat / "tokenizer.json").exists():
        print(f"  NOT RUN {klucz}: brak {kat}")
        return None
    return AutoTokenizer.from_pretrained(str(kat))


def test_bos_z_tokenizera_hf():
    """encode() Bielika i LFM zaczyna się od BOS tokenizera, a reszta = kodowanie bez tokenów specjalnych."""
    for klucz in ("bielik", "lfm"):
        tok = _tokenizer_hf(klucz)
        if tok is None:
            continue
        m = modele.HfLM.__new__(modele.HfLM)
        m.tok = tok
        t = "Polecenie: Ile to 2 + 2?\nOdpowiedź:"
        ids = m.encode(t)
        assert tok.bos_token_id is not None and ids[0] == tok.bos_token_id, (klucz, ids[:3])
        assert ids[1:] == tok(t, add_special_tokens=False)["input_ids"] == m.encode_bez_bos(t), klucz


def test_bos_z_tokenizera_slayer():
    """encode() Slayera: start id = <|endoftext|> z tokenizer.json (id 0, protokół), potem kodowanie bez specjalnych."""
    kat = MODELE_DIR / modele.REJESTR["slayer"][0]
    if not (kat / "tokenizer.json").exists():
        print(f"  NOT RUN slayer: brak {kat}")
        return
    import slayer_model
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(str(kat / "tokenizer.json"))
    rdzen = slayer_model.Slayer.__new__(slayer_model.Slayer)
    rdzen.tok, rdzen.bos = tok, slayer_model.Slayer.BOS
    m = modele.SlayerLM.__new__(modele.SlayerLM)
    m.m = rdzen
    t = "Polecenie: Ile to 2 + 2?\nOdpowiedź:"
    ids = m.encode(t)
    assert ids[0] == tok.token_to_id("<|endoftext|>") == 0, ids[:3]
    assert ids[1:] == tok.encode(t, add_special_tokens=False).ids == m.encode_bez_bos(t)


def test_eos_zbiory():
    """Zbiory EOS z protokołu (sekcja 0) i ich nazwy w tokenizerach."""
    assert modele.EOS == {"slayer": {0}, "bielik": {2, 4}, "lfm": {2, 7}}
    nazwy = {"bielik": {2: "</s>", 4: "<|im_end|>"}, "lfm": {2: "<|endoftext|>", 7: "<|im_end|>"}}
    for klucz, oczek in nazwy.items():
        tok = _tokenizer_hf(klucz)
        if tok is not None:
            assert {i: tok.convert_ids_to_tokens(i) for i in modele.EOS[klucz]} == oczek, klucz


def test_seed_i_top_p():
    """Seed wiersza = 1 000 003 · seed + numer pozycji; top-p 0,9 odcina ogon; temperatura 0,7."""
    assert generuj.SEED_BAZA == 1_000_003
    assert [(d["temperatura"], d["top_p"], d["seed"]) for d in generuj.DEKODOWANIA_A] == \
        [(0.7, 0.9, 1), (0.7, 0.9, 2), (0.7, 0.9, 3), (0.0, 1.0, 0)]
    # top-p: p = 0,5 / 0,3 / 0,15 / 0,05 -> zostają tokeny 0-2 (skumulowane p przed nimi <= 0,9), token 3 odcięty
    logity = torch.log(torch.tensor([0.5, 0.3, 0.15, 0.05]))
    g = torch.Generator().manual_seed(7)
    wyb = [generuj.wybierz_token(logity, dict(temperatura=1.0, top_p=0.9), g) for _ in range(3000)]
    assert 3 not in wyb and {0, 1, 2} <= set(wyb)
    # seed z numerem pozycji: próbka wiersza = próbka z generatora o seedzie 1 000 003 · seed + nr
    m = Atrapa()
    dek = generuj.DEKODOWANIA_A[0]
    prompt = m.encode("xyz")
    for nr in (0, 5, 17):
        generuj.generuj_batch(m, "xyz", [dek], nr, 1, ["\nPolecenie:"])
        wybrany = m.ids[0][len(prompt)]  # atrapa dopisuje do wiersza token przekazany do krok()
        logity0 = Atrapa().start(prompt)[0]
        oczek = generuj.wybierz_token(logity0, dek, torch.Generator().manual_seed(1_000_003 * 1 + nr))
        assert wybrany == oczek, (nr, wybrany, oczek)
    a, _, _ = generuj.generuj_batch(m, "xyz", [dek], 0, 8, ["\nPolecenie:"])
    b, _, _ = generuj.generuj_batch(m, "xyz", [dek], 1, 8, ["\nPolecenie:"])
    assert a[0]["surowa"] != b[0]["surowa"], "inny numer pozycji -> inna próbka"


def test_tolerancja_liczby():
    """Tolerancja oceny liczby 0,005 (protokół, sekcja 4)."""
    assert ocena.ocen_liczba("Wynik: 10,004", 10) == 1
    assert ocena.ocen_liczba("Wynik: 10,01", 10) == 0
    assert ocena.ocen_liczba("Wynik: 10,4", 10) == 0


def test_holm_wszystkie_kategorie():
    """Holm z m = wszystkie kategorie z metryką, także te z SE = 0 (p nieokreślone liczy się jak 1)."""
    import analiza
    h = analiza.holm_m([0.01, None, None, None])
    assert abs(h[0] - 0.04) < 1e-12 and h[1:] == [None, None, None]
    ph = analiza.holm_m([0.01, 0.02, 0.5, None])
    assert abs(ph[0] - 0.04) < 1e-12 and abs(ph[1] - 0.06) < 1e-12 and abs(ph[2] - 1.0) < 1e-12 and ph[3] is None
    # odwrócona kolejność wejścia daje te same wartości per pozycja
    odw = analiza.holm_m([None, 0.5, 0.02, 0.01])[::-1]
    assert odw[3] is None and all(abs(x - y) < 1e-12 for x, y in zip(odw[:3], ph[:3]))


if __name__ == "__main__":
    testy = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in testy:
        t()
        print("OK", t.__name__)
    print(f"{len(testy)} testów OK")
