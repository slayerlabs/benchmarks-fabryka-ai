"""BLiMP: how far the Slayer - Pythia gap generalises (paradigms as clusters), multiple testing,
tokenizer effects. Pure functions; called by `blimp.py zbierz`, tested in tests/test_blimp.py.

The pair-level SE in blimp.py answers "is the gap real on these 67 000 pairs". Pairs of one paradigm
share a template, so for "is the gap real for paradigms of this kind" the unit is the paradigm:
SE over the 67 paradigm differences (clustered), a bootstrap over paradigms and a sign test.
"""
import math

from blimp import PROG_PEWNE, PROG_PRAWDOPODOBNE, SEED, trafienie_pary, werdykt

NIEROZSTRZYGALNE = "nierozstrzygalne"  # a group with fewer than 3 paradigms gets no verdict
MIN_CZLONKOW = 3
# the THRESHOLDS.md z thresholds as two-sided p, so a t with few degrees of freedom is held to the same error rate
P_PEWNE = math.erfc(PROG_PEWNE / math.sqrt(2))  # 0.0027
P_PRAWDOPODOBNE = math.erfc(PROG_PRAWDOPODOBNE / math.sqrt(2))  # 0.0455


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


def _beta_cf(a, b, x):
    """Continued fraction of the incomplete beta (modified Lentz)."""
    tiny = 1e-300
    c, d = 1.0, 1.0 - (a + b) * x / (a + 1)
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 1000):
        for num in (m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m)),
                    -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))):
            d = 1.0 + num * d
            d = 1.0 / (d if abs(d) > tiny else tiny)
            c = 1.0 + num / c
            c = c if abs(c) > tiny else tiny
            h *= d * c
        if abs(d * c - 1.0) < 1e-15:
            break
    return h


def beta_reg(a, b, x):
    """Regularised incomplete beta I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    ln = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x < (a + 1) / (a + b + 2):
        return math.exp(ln) * _beta_cf(a, b, x) / a
    return 1.0 - math.exp(ln) * _beta_cf(b, a, 1 - x) / b


def p_t(t, df):
    """Two-sided p of Student's t with df degrees of freedom; None (no variance) -> 1."""
    if t is None:
        return 1.0
    return beta_reg(df / 2, 0.5, df / (df + t * t))


def werdykt_p(p):
    """THRESHOLDS.md verdict read as a p-value: p <= p(|z| = 3) certain, <= p(|z| = 2) probable."""
    return "pewne" if p <= P_PEWNE else "prawdopodobne" if p <= P_PRAWDOPODOBNE else "szum"


def klastry(xs):
    """Clustered mean, SE, t, df = k - 1, two-sided p from the t distribution, and its verdict."""
    if not xs:
        return {"k": 0, "roznica": None, "se": None, "t": None, "df": None, "p": None, "werdykt": None}
    m, se, t = t_klastrowe(xs)
    df = len(xs) - 1
    p = p_t(t, df) if df > 0 else None
    return {"k": len(xs), "roznica": m, "se": se, "t": t, "df": df, "p": p,
            "werdykt": werdykt_p(p) if p is not None else None}


def werdykt_grupy(xs):
    """Verdict from the p of the clustered t (df = k - 1); below MIN_CZLONKOW members there is no verdict."""
    if len(xs) < MIN_CZLONKOW:
        return NIEROZSTRZYGALNE
    return klastry(xs)["werdykt"]


def ten_sam_worek_slow(a, b):
    """Good and bad sentence use the same words (as a multiset), so they differ only in word order."""
    def worek(s):
        return sorted(s.lower().rstrip(".?").split())
    return worek(a) == worek(b)


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


def analiza(docs, wa, wb, por_paradygmaty):
    """wa, wb: {id: row} of model a (Slayer) and b (Pythia); por_paradygmaty: pair-level per-paradigm entries."""
    gr = sorted({d["grupa"] for d in docs})
    zj = {d["grupa"]: d["zjawisko"] for d in docs}
    roz, roz_tok, ta_sama, rozna, worek, inny = ({g: [] for g in gr} for _ in range(6))
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
            (worek if sam else inny)[g].append(r)
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
            "ten_sam_worek_slow": {"tak": worek_opis(worek), "nie": worek_opis(inny),
                                   "flaga_lexically_identical_paradygmaty": len(flaga),
                                   "flaga_bez_tego_samego_worka": sum(not all(v) for v in flaga.values())},
            "tokenizacja": {"stosunek_tokenow_a_do_b": tok_a / tok_b, "ta_sama_roznica_tokenow": neutr,
                            "rozna_roznica_tokenow": podzbior(rozna),
                            "czesc_luki_od_tokenizacji": (calosc["roznica"] - neutr["roznica"]
                                                          if neutr["roznica"] is not None else None)}}
