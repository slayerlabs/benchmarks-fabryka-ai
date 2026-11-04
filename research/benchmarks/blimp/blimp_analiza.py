"""BLiMP: how far the Slayer - Pythia gap generalises (paradigms as clusters), multiple testing,
tokenizer effects. Pure functions; called by `blimp.py zbierz`, tested in tests/test_blimp.py.

The pair-level SE in blimp.py answers "is the gap real on these 67 000 pairs". Pairs of one paradigm
share a template, so for "is the gap real for paradigms of this kind" the unit is the paradigm:
SE over the 67 paradigm differences (clustered), a bootstrap over paradigms and a sign test. The paradigm
level is the binding one (METODOLOGIA.md, type `para +klastry`); the pair level is information about these pairs.
SE K, the t distribution and Holm come from tools/statystyka.py (one implementation for every benchmark).
"""
import math
import re
import sys
from pathlib import Path

from blimp import SEED, trafienie_pary, werdykt

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from statystyka import (P_PEWNE, P_PRAWDOPODOBNE, klastrowe_wazone, p_t, p_z, po_holmie,  # noqa: E402,F401
                        werdykt_p)
from statystyka import holm as holm_p  # noqa: E402

NIEROZSTRZYGALNE = "nierozstrzygalne"  # a group with fewer than 3 paradigms gets no verdict
MIN_CZLONKOW = 3


def srednia(xs):
    return sum(xs) / len(xs)


def klastry(xs):
    """Mean of the paradigm values, SE K over them (equal weights: every paradigm has its own value), t at
    df = k - 1, two-sided p from the t distribution and its verdict (statystyka.klastrowe_wazone; k < 3 gives
    "nierozstrzygalne", SE = 0 no t)."""
    if not xs:
        return {"k": 0, "roznica": None, "se": None, "t": None, "df": None, "p": None, "werdykt": None}
    r = klastrowe_wazone([(1, x) for x in xs])
    return {"k": r["k"], "roznica": r["roznica"], "se": r["se"], "t": r["t"], "df": r["df"], "p": r["p_t"],
            "werdykt": r["werdykt"]}


def werdykt_grupy(xs):
    """Verdict from the p of the clustered t (df = k - 1); below MIN_CZLONKOW members there is no verdict."""
    if len(xs) < MIN_CZLONKOW:
        return NIEROZSTRZYGALNE
    return klastry(xs)["werdykt"]


# What "the same words" means changes the word-order side of the split a lot, so three readings are kept:
WORKI = {
    # main reading: lower case, every character other than a letter, digit, _, ' or whitespace removed, split on spaces
    "bez_interpunkcji": lambda s: sorted(re.sub(r"[^\w\s']", "", s.lower()).split()),
    # the raw text split on whitespace (punctuation stays glued to its word, case kept)
    "split": lambda s: sorted(s.split()),
    # words and punctuation marks as separate tokens, case kept
    "interpunkcja_osobno": lambda s: sorted(re.findall(r"\w+|[^\w\s]", s)),
}
WOREK_GLOWNY = "bez_interpunkcji"


def ten_sam_worek_slow(a, b, definicja=WOREK_GLOWNY):
    """Good and bad sentence use the same words (as a multiset, by WORKI[definicja]): only word order differs."""
    f = WORKI[definicja]
    return f(a) == f(b)


def bootstrap_srednich(xs, powtorzen=10000, seed=SEED):
    import numpy as np
    rng = np.random.default_rng(seed)
    a = np.array(xs, dtype=float)
    sr = a[rng.integers(0, len(a), size=(powtorzen, len(a)))].mean(axis=1)
    lo, hi = np.percentile(sr, [2.5, 97.5])
    return float(lo), float(hi)


def test_znakow(dodatnie, ujemne):
    """Two-sided exact sign test (ties dropped)."""
    n = dodatnie + ujemne
    k = min(dodatnie, ujemne)
    ogon = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * ogon)


def holm(p, alfa=P_PRAWDOPODOBNE):
    """Holm step-down over {name: p}: {name: rejected?}, rejected = Holm-adjusted p <= alfa (statystyka.holm);
    alfa defaults to the repo threshold, p of |z| = 2 (0.0455); p = None is outside the family and never rejected."""
    nazwy = list(p)
    return {k: a is not None and a <= alfa for k, a in zip(nazwy, holm_p([p[k] for k in nazwy]))}


def zjawiska_po_holmie(zjawiska, por_zjawiska=None):
    """Holm over the phenomena table, one family per level (METODOLOGIA.md, core rule 4).
    zjawiska: {phenomenon: {"k", "p_t"}} (paradigm level; k < MIN_CZLONKOW is outside the family);
    por_zjawiska: {phenomenon: {"z"}} (pair level, p from z). -> {phenomenon: {"p_holm", "werdykt_holm",
    "po_holmie"} for paradigms, the same with suffix "_pary" for pairs}; the verdict after Holm is read from
    the adjusted p (p thresholds of |z| = 2 and 3)."""
    nazwy = sorted(zjawiska)
    kl = po_holmie([zjawiska[z]["p_t"] if zjawiska[z]["k"] >= MIN_CZLONKOW else None for z in nazwy])
    out = {z: dict(h) for z, h in zip(nazwy, kl)}
    if por_zjawiska is not None:
        for z, h in zip(nazwy, po_holmie([p_z(por_zjawiska[z]["z"]) for z in nazwy])):
            out[z].update({f"{k}_pary": v for k, v in h.items()})
    return out


def rangi(xs):
    """Ranks with ties averaged (1-based)."""
    kolej = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(kolej):
        j = i
        while j + 1 < len(kolej) and xs[kolej[j + 1]] == xs[kolej[i]]:
            j += 1
        for t in range(i, j + 1):
            r[kolej[t]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = rangi(a), rangi(b)
    ma, mb = srednia(ra), srednia(rb)
    licz = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    mian = sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)
    if mian == 0:
        return None  # a constant input (or a single item) has no rank order
    return licz / math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))


def podzbior(po_grupie):
    """Pair-weighted mean of paired differences over a subset, SE stratified by paradigm."""
    N = sum(len(x) for x in po_grupie.values())
    if N == 0:
        return {"n": 0, "roznica": None, "se": None, "z": None, "werdykt": None}
    m = sum(sum(x) for x in po_grupie.values()) / N
    var = 0.0
    for x in po_grupie.values():
        n = len(x)
        if n > 1:
            mx = srednia(x)
            var += sum((v - mx) ** 2 for v in x) / (n - 1) / n * (n / N) ** 2
    se = math.sqrt(var)
    z = m / se if se > 0 else None
    return {"n": N, "roznica": m, "se": se, "z": z, "werdykt": werdykt(z)}


def trafienie_na_token(doc, wiersz):
    if doc["opcje"][0] == doc["opcje"][1]:
        return 1
    ll, nt = wiersz["ll"], wiersz["ntok"]
    return 1 if ll[0] / nt[0] >= ll[1] / nt[1] else 0


def analiza(docs, wa, wb, por_paradygmaty, por_zjawiska=None):
    """wa, wb: {id: row} of model a (Slayer) and b (Pythia); por_paradygmaty, por_zjawiska: pair-level
    per-paradigm and per-phenomenon entries (blimp.porownanie_parowane); the latter adds Holm on pairs."""
    gr = sorted({d["grupa"] for d in docs})
    zj = {d["grupa"]: d["zjawisko"] for d in docs}
    roz, roz_tok, ta_sama, rozna = ({g: [] for g in gr} for _ in range(4))
    worki = {df: ({g: [] for g in gr}, {g: [] for g in gr}) for df in WORKI}  # definition -> (same, other)
    flaga = {}
    tok_a = tok_b = 0
    for d in docs:
        g, ra, rb = d["grupa"], wa[d["id"]], wb[d["id"]]
        r = trafienie_pary(d, ra) - trafienie_pary(d, rb)
        roz[g].append(r)
        roz_tok[g].append(trafienie_na_token(d, ra) - trafienie_na_token(d, rb))
        dn_a = ra["ntok"][1] - ra["ntok"][0]
        dn_b = rb["ntok"][1] - rb["ntok"][0]
        (ta_sama if dn_a == dn_b else rozna)[g].append(r)
        sam = ten_sam_worek_slow(*d["opcje"])
        if d["opcje"][0] != d["opcje"][1]:  # identical good and bad sentence: no contrast at all, in neither side
            for df, (tak, nie) in worki.items():
                (tak if ten_sam_worek_slow(*d["opcje"], df) else nie)[g].append(r)
        if d["rekord"].get("lexically_identical"):
            flaga.setdefault(g, []).append(sam)
        tok_a += ra["ntok"][0]
        tok_b += rb["ntok"][0]

    dp = [srednia(roz[g]) for g in gr]
    kl = klastry(dp)
    kl2 = klastry(sorted(dp)[2:])
    dodatnie, ujemne = sum(x > 0 for x in dp), sum(x < 0 for x in dp)
    gen = {"k": len(dp), "roznica": kl["roznica"], "se_klastrowe": kl["se"], "z_klastrowe": kl["t"],
           "df": kl["df"], "p_t": kl["p"], "werdykt_klastrowy": kl["werdykt"],
           "ci95_bootstrap_paradygmatow": list(bootstrap_srednich(dp)),
           "znak": {"a_lepszy": dodatnie, "b_lepszy": ujemne, "remis": len(dp) - dodatnie - ujemne,
                    "p": test_znakow(dodatnie, ujemne)},
           "bez_2_najgorszych": {"roznica": kl2["roznica"], "se": kl2["se"], "t": kl2["t"], "df": kl2["df"],
                                 "p_t": kl2["p"], "werdykt": kl2["werdykt"]}}

    zjawiska = {}
    for z in sorted(set(zj.values())):
        xs = [srednia(roz[g]) for g in gr if zj[g] == z]
        k = klastry(xs)
        zjawiska[z] = {"k": k["k"], "roznica": k["roznica"], "se": k["se"], "t": k["t"], "df": k["df"],
                       "p_t": k["p"], "werdykt": werdykt_grupy(xs)}
    for z, h in zjawiska_po_holmie(zjawiska, por_zjawiska).items():
        zjawiska[z].update(h)

    def worek_opis(po_grupie):
        r = podzbior(po_grupie)
        sr = [srednia(x) for x in po_grupie.values() if x]
        k = klastry(sr)
        r.update({"k_paradygmatow": k["k"], "srednia_paradygmatow": k["roznica"], "se_paradygmatow": k["se"],
                  "t_paradygmatow": k["t"], "df_paradygmatow": k["df"], "p_t_paradygmatow": k["p"],
                  "werdykt_paradygmatow": k["werdykt"],
                  "srednia_abs_paradygmatow": srednia([abs(x) for x in sr]) if sr else None})
        return r

    p = {g: p_z(por_paradygmaty[g]["z"]) for g in gr}
    odrz = holm(p)
    dtok = [srednia(roz_tok[g]) for g in gr]
    parad = {}
    for g, dt in zip(gr, dtok):
        ts = ta_sama[g]
        parad[g] = {"roznica_na_token": dt, "p": p[g], "holm": odrz[g], "n_ta_sama_tokenizacja": len(ts),
                    "roznica_ta_sama_tokenizacja": srednia(ts) if ts else None}

    na_token = podzbior(roz_tok)
    calosc = podzbior(roz)
    neutr = podzbior(ta_sama)
    przewagi = [g for g in gr if por_paradygmaty[g]["werdykt"] == "pewne" and por_paradygmaty[g]["roznica"] > 0]
    return {"progi_p": {"pewne": P_PEWNE, "prawdopodobne": P_PRAWDOPODOBNE},
            "generalizacja": gen, "zjawiska_klastrowe": zjawiska, "paradygmaty_dodatkowe": parad,
            "holm_odrzucone": sum(odrz.values()),
            "spearman_suma_na_token": spearman(dp, dtok),
            "na_token": na_token,
            "przewagi_a_pewne": len(przewagi),
            "przewagi_a_odwrocone_na_token": [g for g in przewagi if parad[g]["roznica_na_token"] < 0],
            "ten_sam_worek_slow": {"tak": worek_opis(worki[WOREK_GLOWNY][0]), "nie": worek_opis(worki[WOREK_GLOWNY][1]),
                                   "wrazliwosc": {df: {"tak": worek_opis(t), "nie": worek_opis(n)}
                                                  for df, (t, n) in worki.items()},
                                   "flaga_lexically_identical_paradygmaty": len(flaga),
                                   "flaga_bez_tego_samego_worka": sum(not all(v) for v in flaga.values())},
            "tokenizacja": {"stosunek_tokenow_a_do_b": tok_a / tok_b, "ta_sama_roznica_tokenow": neutr,
                            "rozna_roznica_tokenow": podzbior(rozna),
                            "czesc_luki_od_tokenizacji": (calosc["roznica"] - neutr["roznica"]
                                                          if neutr["roznica"] is not None else None)}}
