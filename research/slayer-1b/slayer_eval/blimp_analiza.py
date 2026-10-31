"""BLiMP: how far the Slayer - Pythia gap generalises (paradigms as clusters), multiple testing,
tokenizer effects. Pure functions; called by `blimp.py zbierz`, tested in tests/test_blimp.py.

The pair-level SE in blimp.py answers "is the gap real on these 67 000 pairs". Pairs of one paradigm
share a template, so for "is the gap real for paradigms of this kind" the unit is the paradigm:
SE over the 67 paradigm differences (clustered), a bootstrap over paradigms and a sign test.
"""
import math

from blimp import SEED, trafienie_pary, werdykt

NIEROZSTRZYGALNE = "nierozstrzygalne"  # a group with fewer than 3 paradigms gets no verdict
MIN_CZLONKOW = 3


def srednia(xs):
    return sum(xs) / len(xs)


def t_klastrowe(xs):
    """Mean of cluster values, SE = sd / sqrt(k), t = mean / SE; SE and t None for k < 2 or sd = 0."""
    k = len(xs)
    m = srednia(xs)
    if k < 2:
        return m, None, None
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (k - 1))
    se = sd / math.sqrt(k)
    return m, se, (m / se if se > 0 else None)


def werdykt_grupy(xs):
    """Verdict from the clustered t; below MIN_CZLONKOW members there is no verdict."""
    if len(xs) < MIN_CZLONKOW:
        return NIEROZSTRZYGALNE
    return werdykt(t_klastrowe(xs)[2])


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


def p_z(z):
    """Two-sided normal p-value; None (no variance) -> 1."""
    return 1.0 if z is None else math.erfc(abs(z) / math.sqrt(2))


def holm(p, alfa=0.05):
    """Holm step-down: {name: rejected?}."""
    kolej = sorted(p, key=lambda k: p[k])
    m, out, dalej = len(kolej), {}, True
    for i, k in enumerate(kolej):
        dalej = dalej and p[k] <= alfa / (m - i)
        out[k] = dalej
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


def analiza(docs, wa, wb, por_paradygmaty):
    """wa, wb: {id: row} of model a (Slayer) and b (Pythia); por_paradygmaty: pair-level per-paradigm entries."""
    gr = sorted({d["grupa"] for d in docs})
    zj = {d["grupa"]: d["zjawisko"] for d in docs}
    roz, roz_tok, ta_sama, rozna, lex, nielex = ({g: [] for g in gr} for _ in range(6))
    tok_a = tok_b = 0
    for d in docs:
        g, ra, rb = d["grupa"], wa[d["id"]], wb[d["id"]]
        r = trafienie_pary(d, ra) - trafienie_pary(d, rb)
        roz[g].append(r)
        roz_tok[g].append(trafienie_na_token(d, ra) - trafienie_na_token(d, rb))
        dn_a = ra["ntok"][1] - ra["ntok"][0]
        dn_b = rb["ntok"][1] - rb["ntok"][0]
        (ta_sama if dn_a == dn_b else rozna)[g].append(r)
        (lex if d["rekord"].get("lexically_identical") else nielex)[g].append(r)
        tok_a += ra["ntok"][0]
        tok_b += rb["ntok"][0]

    dp = [srednia(roz[g]) for g in gr]
    m, se, t = t_klastrowe(dp)
    posort = sorted(dp)
    m2, se2, t2 = t_klastrowe(posort[2:])
    dodatnie, ujemne = sum(x > 0 for x in dp), sum(x < 0 for x in dp)
    gen = {"k": len(dp), "roznica": m, "se_klastrowe": se, "z_klastrowe": t, "werdykt_klastrowy": werdykt(t),
           "ci95_bootstrap_paradygmatow": list(bootstrap_srednich(dp)),
           "znak": {"a_lepszy": dodatnie, "b_lepszy": ujemne, "remis": len(dp) - dodatnie - ujemne,
                    "p": test_znakow(dodatnie, ujemne)},
           "bez_2_najgorszych": {"roznica": m2, "se": se2, "t": t2, "werdykt": werdykt(t2)}}

    zjawiska = {}
    for z in sorted(set(zj.values())):
        xs = [srednia(roz[g]) for g in gr if zj[g] == z]
        mz, sz, tz = t_klastrowe(xs)
        zjawiska[z] = {"k": len(xs), "roznica": mz, "se": sz, "t": tz, "werdykt": werdykt_grupy(xs)}

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
    return {"generalizacja": gen, "zjawiska_klastrowe": zjawiska, "paradygmaty_dodatkowe": parad,
            "holm_odrzucone": sum(odrz.values()),
            "spearman_suma_na_token": spearman(dp, dtok),
            "na_token": na_token,
            "tokenizacja": {"stosunek_tokenow_a_do_b": tok_a / tok_b, "ta_sama_roznica_tokenow": neutr,
                            "rozna_roznica_tokenow": podzbior(rozna),
                            "czesc_luki_od_tokenizacji": (calosc["roznica"] - neutr["roznica"]
                                                          if neutr["roznica"] is not None else None)},
            "leksykalnie_identyczne": {"tak": podzbior(lex), "nie": podzbior(nielex)}}
