"""Trzy obliczenia z METODOLOGII, wspólne dla tools/liczby.py i generatorów raportów (czyste funkcje, bez numpy).

- SE K (klastrowane) przy klastrach nierównej wielkości, z testem t przy df = k − 1 (`se_k`, `klastrowe_wazone`);
- porównanie parowane ze stałym predyktorem b dla kontroli typu `mc` (`wobec_stalej`);
- Holm step-down z flagą „po Holmie: tak/nie” per wiersz tabeli (`holm`, `po_holmie`).

Progi werdyktu: |z| >= 3 „pewne”, 2–3 „prawdopodobne”, < 2 „szum”; t i p Holma czytane przez p tych samych z.
Generator w benchmarks/<nazwa>/ importuje ten plik po dodaniu research/tools do sys.path.
"""
import math

PROG_PEWNE = 3.0
PROG_PRAWDOPODOBNE = 2.0
P_PEWNE = math.erfc(PROG_PEWNE / math.sqrt(2))  # 0.0027, dwustronne p dla |z| = 3
P_PRAWDOPODOBNE = math.erfc(PROG_PRAWDOPODOBNE / math.sqrt(2))  # 0.0455, dwustronne p dla |z| = 2
NIEROZSTRZYGALNE = "nierozstrzygalne"
MIN_KLASTROW = 3


def werdykt(z):
    """Werdykt z |z|: >= 3 pewne, 2-3 prawdopodobne, < 2 szum; None, gdy z nieznane."""
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return None
    a = abs(z)
    if a >= PROG_PEWNE:
        return "pewne"
    if a >= PROG_PRAWDOPODOBNE:
        return "prawdopodobne"
    return "szum"


def p_z(z):
    """Dwustronne p rozkładu normalnego; None, gdy z nieznane."""
    return None if z is None else math.erfc(abs(z) / math.sqrt(2))


def werdykt_p(p):
    """Werdykt z dwustronnego p: <= p(|z| = 3) pewne, <= p(|z| = 2) prawdopodobne, inaczej szum."""
    if p is None:
        return NIEROZSTRZYGALNE
    return "pewne" if p <= P_PEWNE else "prawdopodobne" if p <= P_PRAWDOPODOBNE else "szum"


def _beta_cf(a, b, x):
    """Ułamek łańcuchowy niekompletnej funkcji beta (Numerical Recipes, betacf)."""
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > 1e-300 else 1e-300)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        for aa in (m * (b - m) * x / ((qam + m2) * (a + m2)), -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))):
            d = 1 + aa * d
            d = 1 / (d if abs(d) > 1e-300 else 1e-300)
            c = 1 + aa / c
            c = c if abs(c) > 1e-300 else 1e-300
            h *= d * c
        if abs(d * c - 1) < 1e-14:
            break
    return h


def p_t(t, df):
    """Dwustronne p rozkładu t Studenta z df stopniami swobody."""
    if t == 0:
        return 1.0
    x = df / (df + t * t)
    if x <= 0:
        return 0.0
    a, b = df / 2, 0.5
    ln = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x < (a + 1) / (a + b + 2):
        return math.exp(ln) * _beta_cf(a, b, x) / a
    return 1.0 - math.exp(ln) * _beta_cf(b, a, 1 - x) / b


def werdykt_t(t, df):
    """Werdykt t z df: te same progi co z, czytane jako dwustronne p (p <= p(|z| = 3) pewne, <= p(|z| = 2)
    prawdopodobne), żeby t z małą liczbą klastrów nie dostało werdyktu mocniejszego niż jego p."""
    return werdykt_p(p_t(t, df))


def klastrowe_wazone(grupy):
    """grupy: [(n, średnia w klastrze)]. Średnia ważona n i SE K po klastrach:
    √(k/(k−1) · Σ_c (n_c (d_c − d̄))²) / n, czyli √(k/(k−1) · Σ_c (Σ_{i∈c} (xᵢ − x̄))²) / n; t = średnia / SE,
    df = k − 1. Przy k < 3 werdykt „nierozstrzygalne” (t i p bez werdyktu); SE = 0 daje t i werdykt None."""
    N, G = sum(n for n, _ in grupy), len(grupy)
    m = sum(n * d for n, d in grupy) / N
    if G < 2:  # one cluster: no spread between clusters
        return {"roznica": m, "se": None, "t": None, "df": G - 1, "p_t": None, "werdykt": NIEROZSTRZYGALNE, "k": G}
    se = math.sqrt(sum((n * (d - m)) ** 2 for n, d in grupy) * G / (G - 1)) / N
    if se == 0:  # every group the same: no spread to read a t from
        return {"roznica": m, "se": se, "t": None, "df": G - 1, "p_t": None,
                "werdykt": NIEROZSTRZYGALNE if G < MIN_KLASTROW else None, "k": G}
    t = m / se
    p = p_t(t, G - 1)
    return {"roznica": m, "se": se, "t": t, "df": G - 1, "p_t": p,
            "werdykt": NIEROZSTRZYGALNE if G < MIN_KLASTROW else werdykt_p(p), "k": G}


def se_k(wartosci, klastry, b=0.0):
    """SE K średniej po pozycjach: wartosci[i] to wynik (albo różnica) pozycji i, klastry[i] jej klaster.
    Zwraca klastrowe_wazone dla x̄ − b (t = (x̄ − b) / SE K, df = k − 1) oraz n pozycji i średnią x̄."""
    if len(wartosci) != len(klastry) or not wartosci:
        raise ValueError("wartosci i klastry: ta sama niezerowa długość")
    sumy, liczby = {}, {}
    for x, c in zip(wartosci, klastry):
        sumy[c] = sumy.get(c, 0.0) + x
        liczby[c] = liczby.get(c, 0) + 1
    r = klastrowe_wazone([(liczby[c], sumy[c] / liczby[c] - b) for c in sorted(sumy, key=str)])
    r.update({"n": len(wartosci), "srednia": r["roznica"] + b, "b": b})
    return r


def wobec_stalej(wyniki, poprawne, klastry=None):
    """Kontrola `mc`: wynik modelu wobec stałego predyktora, który zawsze wybiera najczęstszą poprawną opcję
    (remis: najmniejsza etykieta), parowanie po pozycjach: dᵢ = xᵢ − cᵢ, cᵢ = 1, gdy poprawna opcja pozycji i
    to ta stała. SE = s(d) / √n (SE A parowane), a z `klastry` SE K różnic z t przy df = k − 1.
    Zwraca b, stałą, różnicę, SE, z (albo t, df, p) i werdykt; SE = 0 daje werdykt „nierozstrzygalne”."""
    n = len(wyniki)
    if n != len(poprawne) or n < 2:
        raise ValueError("wyniki i poprawne: ta sama długość, co najmniej 2")
    licz = {}
    for g in poprawne:
        licz[g] = licz.get(g, 0) + 1
    stala = min(licz, key=lambda g: (-licz[g], g))
    c = [1.0 if g == stala else 0.0 for g in poprawne]
    d = [x - y for x, y in zip(wyniki, c)]
    b = sum(c) / n
    out = {"n": n, "stala": stala, "b": b, "wynik": sum(wyniki) / n}
    if klastry is not None:
        r = se_k(d, klastry)
        out.update({"roznica": r["roznica"], "se": r["se"], "t": r["t"], "df": r["df"], "p": r["p_t"],
                    "werdykt": r["werdykt"] or NIEROZSTRZYGALNE, "k": r["k"], "metoda": "K"})
        return out
    m = sum(d) / n
    se = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1) / n)
    z = m / se if se > 0 else None
    out.update({"roznica": m, "se": se, "z": z, "p": p_z(z), "werdykt": werdykt(z) or NIEROZSTRZYGALNE,
                "metoda": "A parowane"})
    return out


def holm(ps):
    """Holm step-down: p poprawione (rosnąco max po rangach (m − r) · p, obcięte do 1), w kolejności ps.
    p = None (wiersz „nierozstrzygalne”) nie wchodzi do rodziny i zostaje None."""
    idx = sorted((i for i, p in enumerate(ps) if p is not None), key=lambda i: (ps[i], i))
    m, out, mx = len(idx), [None] * len(ps), 0.0
    for r, i in enumerate(idx):
        mx = max(mx, min(1.0, (m - r) * ps[i]))
        out[i] = mx
    return out


def po_holmie(ps):
    """Kolumna „po Holmie” tabeli porównań: per wiersz p Holma, werdykt z niego (progi p jak dla |z| = 2 i 3)
    i flaga „tak” (p Holma <= p(|z| = 2)) albo „nie”; wiersz bez p dostaje „nie” i „nierozstrzygalne”."""
    return [{"p_holm": a, "werdykt_holm": werdykt_p(a), "po_holmie": "tak" if a is not None and a <= P_PRAWDOPODOBNE
             else "nie"} for a in holm(ps)]
