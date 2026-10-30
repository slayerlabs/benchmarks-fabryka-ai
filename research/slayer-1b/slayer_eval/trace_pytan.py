"""Trace per pytanie i porównanie checkpointów — diagnostyka ARC-C bez dopasowywania do benchmarku.

Trace mówi, CO model wybiera i dlaczego (pozycja, długość opcji, normalizacja), a nie zmienia
promptu ani metryki głównej. Porównanie checkpointów: ta sama lista pytań na kilku wersjach,
przejścia błędne→dobre i dobre→błędne między kolejnymi wersjami, z dokładnym testem McNemara.
"""

import json
import math
from collections import Counter

from metryki import LN2, argmax, rozbierz_mc

LITERY = "ABCDEFGH"


def trace_pytania(probka, licz_tokeny, z_pmi=True, id_pytania=None):
    """Jeden wiersz trace: opcje z logprob (suma, na bajt, na token), długości i wybory czterech reguł."""
    lls, bezw, konty, gold = rozbierz_mc(probka, z_pmi)
    bajty = [max(len(c.encode("utf-8")), 1) for c in konty]
    znaki = [max(len(c.lstrip(" ")), 1) for c in konty]
    tokeny = [max(licz_tokeny(c), 1) for c in konty]
    opcje = []
    for i, c in enumerate(konty):
        o = {"pozycja": LITERY[i], "tekst_bajty": bajty[i], "tokeny": tokeny[i],
             "logprob": lls[i], "logprob_na_bajt": lls[i] / bajty[i], "logprob_na_token": lls[i] / tokeny[i]}
        if bezw is not None:
            o["logprob_bezwarunkowy"] = bezw[i]
            o["pmi"] = lls[i] - bezw[i]
        opcje.append(o)
    wybory = {"acc": argmax(lls),
              "acc_norm": argmax([ll / z for ll, z in zip(lls, znaki)]),
              "bpb": argmax([ll / b for ll, b in zip(lls, bajty)])}
    if bezw is not None:
        wybory["pmi"] = argmax([a - b for a, b in zip(lls, bezw)])
    najkrotsza = min(range(len(bajty)), key=lambda i: (bajty[i], i))
    najdluzsza = max(range(len(bajty)), key=lambda i: (bajty[i], -i))
    return {"id": id_pytania if id_pytania is not None else probka.get("doc_id"),
            "poprawna": gold, "poprawna_litera": LITERY[gold], "k": len(lls),
            "bpb_poprawnej": -lls[gold] / (LN2 * bajty[gold]),
            "opcje": opcje,
            "wybor": {m: LITERY[w] for m, w in wybory.items()},
            "trafione": {m: w == gold for m, w in wybory.items()},
            "wybor_najkrotsza": {m: w == najkrotsza for m, w in wybory.items()},
            "wybor_najdluzsza": {m: w == najdluzsza for m, w in wybory.items()},
            "poprawna_najkrotsza": gold == najkrotsza, "poprawna_najdluzsza": gold == najdluzsza}


def rozklad_wyborow(wiersze):
    """Per reguła: trafność, rozkład pozycji A-D, udział najkrótszej i najdłuższej opcji; plus te same udziały dla poprawnych."""
    n = len(wiersze)
    reguly = sorted({m for w in wiersze for m in w["wybor"]})
    wynik = {"n": n,
             "poprawne_pozycje": dict(sorted(Counter(w["poprawna_litera"] for w in wiersze).items())),
             "poprawna_najkrotsza": sum(w["poprawna_najkrotsza"] for w in wiersze) / n,
             "poprawna_najdluzsza": sum(w["poprawna_najdluzsza"] for w in wiersze) / n,
             "reguly": {}}
    for m in reguly:
        ws = [w for w in wiersze if m in w["wybor"]]
        wynik["reguly"][m] = {
            "trafnosc": sum(w["trafione"][m] for w in ws) / len(ws),
            "pozycje": dict(sorted(Counter(w["wybor"][m] for w in ws).items())),
            "najkrotsza": sum(w["wybor_najkrotsza"][m] for w in ws) / len(ws),
            "najdluzsza": sum(w["wybor_najdluzsza"][m] for w in ws) / len(ws)}
    return wynik


def mcnemar_dokladny(b, c):
    """Dwustronne p dokładnego testu McNemara dla b przejść w jedną i c w drugą stronę."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    ogon = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * ogon)


def porownaj_checkpointy(traces, regula="acc_norm"):
    """`traces`: [(etykieta, [wiersze trace])] w kolejności treningu.

    Liczy tylko pytania obecne we wszystkich wersjach. Dla każdej pary kolejnych wersji:
    ile pytań przeszło z błędnych na dobre i odwrotnie (z id), p McNemara i trafność obu.
    """
    mapy = [(et, {w["id"]: w for w in ws}) for et, ws in traces]
    wspolne = sorted(set.intersection(*(set(m) for _, m in mapy)), key=str)
    wersje = [{"wersja": et, "n": len(wspolne),
               "trafnosc": sum(m[i]["trafione"][regula] for i in wspolne) / max(len(wspolne), 1)}
              for et, m in mapy]
    przejscia = []
    for (et_a, a), (et_b, b) in zip(mapy, mapy[1:]):
        na_dobre = [i for i in wspolne if not a[i]["trafione"][regula] and b[i]["trafione"][regula]]
        na_zle = [i for i in wspolne if a[i]["trafione"][regula] and not b[i]["trafione"][regula]]
        zmiana_wyboru = sum(a[i]["wybor"][regula] != b[i]["wybor"][regula] for i in wspolne)
        przejscia.append({"z": et_a, "do": et_b, "regula": regula,
                          "zle_na_dobre": len(na_dobre), "dobre_na_zle": len(na_zle),
                          "zmiana_wyboru": zmiana_wyboru,
                          "p_mcnemar": mcnemar_dokladny(len(na_dobre), len(na_zle)),
                          "id_zle_na_dobre": na_dobre, "id_dobre_na_zle": na_zle})
    return {"regula": regula, "wersje": wersje, "przejscia": przejscia}


def wczytaj_trace(sciezka):
    with open(sciezka, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
