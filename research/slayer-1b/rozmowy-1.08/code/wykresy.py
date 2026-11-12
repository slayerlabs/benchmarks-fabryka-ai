"""Wykresy SVG badania z wyniki/LICZBY.json (bez matplotlib: ręcznie składane SVG).

python -I code/wykresy.py  -> charts/*.svg

Styl jak główne wykresy zespołu (tools/ewaluacja/raport.py, results/full-run-2026-11/charts/): paleta GitHuba
w zmiennych CSS z trybem ciemnym, Slayer wyróżniony kolorem --sl i grubszą kreską, modele odniesienia w --ref.
Bielik i LFM mają ten sam kolor, więc różnią się kształtem i wypełnieniem znacznika (kwadrat pełny, romb pusty).
Każdy znacznik ma <title> z wartością, każdy wykres legendę z nazwą modelu. Przedziały: średnia ± 1,96 SE.
"""
import json
from html import escape
from pathlib import Path

BADANIE = Path(__file__).resolve().parent.parent
MODELE = ["slayer", "bielik", "lfm"]
KOLOR = {"slayer": "var(--sl)", "bielik": "var(--ref)", "lfm": "var(--ref)"}
ZNAK = {"slayer": "circle", "bielik": "square", "lfm": "diamond"}  # druga cecha obok koloru
PUSTY = {"lfm"}  # znacznik pusty w środku: trzecia cecha, bo B i L dzielą kolor
GRUBOSC = {"slayer": 3, "bielik": 2, "lfm": 2}
TLO, TEKST, TEKST2, SIATKA = "var(--bg)", "var(--ink)", "var(--mut)", "var(--grid)"
ETYKIETA = {"pl_jezyk": "język polski", "pl_wiedza": "wiedza o Polsce", "wiedza_ogolna": "wiedza ogólna",
            "rozumowanie": "rozumowanie", "matematyka": "matematyka", "kod": "kod", "angielski": "angielski",
            "tekst_techniczny": "tekst techniczny", "razem": "razem"}
STYL = """<style>
svg{--bg:#ffffff;--ink:#1f2328;--mut:#59636e;--grid:#d1d9e0;--sl:#0969da;--ref:#59636e;--band:rgba(9,105,218,.1)}
@media (prefers-color-scheme:dark){svg{--bg:#0d1117;--ink:#f0f6fc;--mut:#9198a1;--grid:#3d444d;--sl:#4493f8;--ref:#c9d1d9;--band:rgba(68,147,248,.16)}}
text{font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;fill:var(--ink);font-variant-numeric:tabular-nums}
line{stroke-linecap:round}
</style>"""


def liczba(x, cyfr=3):
    return f"{x:.{cyfr}f}".replace(".", ",").replace("-", "−")


class Svg:
    def __init__(self, w, h, tytul, opis):
        self.w, self.h, self.el = w, h, []
        self.el.append(f"<rect x='0.5' y='0.5' width='{w - 1}' height='{h - 1}' rx='8' fill='{TLO}' stroke='{SIATKA}'/>")
        self.tekst(24, 32, tytul, 18, TEKST, waga=600)
        self.tekst(24, 52, opis, 12, TEKST2)
        self.tytul = tytul

    def tekst(self, x, y, s, rozmiar=12, kolor=TEKST2, kotwica="start", waga=400):
        self.el.append(f"<text x='{x:.1f}' y='{y:.1f}' text-anchor='{kotwica}' "
                       f"style='font-size:{rozmiar}px;fill:{kolor};font-weight:{waga}'>{escape(s)}</text>")

    def linia(self, x1, y1, x2, y2, kolor=SIATKA, grubosc=1, kreska=None):
        d = f" stroke-dasharray='{kreska}'" if kreska else ""
        self.el.append(f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='{kolor}' "
                       f"stroke-width='{grubosc}'{d}/>")

    def znacznik(self, m, x, y, podpowiedz, r=5):
        k = KOLOR[m]
        if k == "var(--sl)":  # wyróżnienie Slayera (wykres sędziów podmienia kolor na neutralny)
            r += 1.5
        if m in PUSTY:
            ring = f"stroke='{k}' stroke-width='2'"
            k = TLO
        else:
            ring = f"stroke='{TLO}' stroke-width='2'"
        if ZNAK[m] == "circle":
            ksztalt = f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{r}' fill='{k}' {ring}/>"
        elif ZNAK[m] == "square":
            ksztalt = f"<rect x='{x - r:.1f}' y='{y - r:.1f}' width='{2 * r}' height='{2 * r}' rx='1' fill='{k}' {ring}/>"
        else:
            pts = f"{x:.1f},{y - r - 1:.1f} {x + r + 1:.1f},{y:.1f} {x:.1f},{y + r + 1:.1f} {x - r - 1:.1f},{y:.1f}"
            ksztalt = f"<polygon points='{pts}' fill='{k}' {ring}/>"
        self.el.append(f"<g><title>{escape(podpowiedz)}</title>{ksztalt}"
                       f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{r + 6}' fill='transparent'/></g>")

    def legenda(self, x, y, nazwy):
        for j, m in enumerate(MODELE):
            self.znacznik(m, x + j * 150, y, nazwy[m])
            sl = m == "slayer"
            self.tekst(x + j * 150 + 12, y + 4, nazwy[m], 12, KOLOR[m] if sl else TEKST, waga=600 if sl else 400)

    def zapisz(self, nazwa):
        s = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {self.w} {self.h}' width='{self.w}' "
             f"height='{self.h}' role='img' aria-label='{escape(self.tytul)}'><title>{escape(self.tytul)}</title>"
             f"{STYL}\n" + "\n".join(self.el) + "\n</svg>\n")
        (BADANIE / "charts" / nazwa).write_text(s, encoding="utf-8")


def kropki_z_ci(nazwa, tytul, opis, dane, kategorie, nazwy, xmin, xmax, os_x, ticki, cyfr=2):
    """Wiersz na kategorię, trzy modele przesunięte w pionie, poziome odcinki = ±1,96 SE."""
    lewa, prawa, gora, wiersz = 170, 40, 100, 46
    w = 760
    h = gora + wiersz * len(kategorie) + 60
    s = Svg(w, h, tytul, opis)
    s.legenda(lewa, 74, nazwy)
    szer = w - lewa - prawa

    def X(v):
        return lewa + (min(max(v, xmin), xmax) - xmin) / (xmax - xmin) * szer
    dol = gora + wiersz * len(kategorie)
    for t in ticki:
        s.linia(X(t), gora - 6, X(t), dol, SIATKA)
        s.tekst(X(t), dol + 18, liczba(t, cyfr), 11, TEKST2, "middle")
    s.tekst(lewa + szer / 2, dol + 40, os_x, 12, TEKST2, "middle")
    for r, kat in enumerate(kategorie):
        y0 = gora + r * wiersz + wiersz / 2
        s.tekst(lewa - 12, y0 + 4, ETYKIETA[kat], 12, TEKST, "end")
        for j, m in enumerate(MODELE):
            o = dane[kat][m]
            y = y0 + (j - 1) * 11
            lo, hi = o["srednia"] - 1.96 * o["se"], o["srednia"] + 1.96 * o["se"]
            s.linia(X(lo), y, X(hi), y, KOLOR[m], GRUBOSC[m])
            s.znacznik(m, X(o["srednia"]), y, f"{nazwy[m]}, {ETYKIETA[kat]}: {liczba(o['srednia'])} "
                                              f"(SE {liczba(o['se'])}, n {o['n']})", r=4)
    s.zapisz(nazwa)


def male_wielokrotne(nazwa, tytul, opis, panele, nazwy):
    """Dwa panele obok siebie, każdy z własną osią (dwie metryki = dwa wykresy, nie dwie osie)."""
    w, gora, wiersz, etyk, panel = 1000, 120, 40, 130, 480
    nwier = max(len(p["kategorie"]) for p in panele)
    h = gora + wiersz * nwier + 70
    s = Svg(w, h, tytul, opis[0])
    s.tekst(24, 66, opis[1], 12, TEKST2)
    s.legenda(etyk + 24, 94, nazwy)
    szer = panel - etyk - 10
    for pi, p in enumerate(panele):
        x0 = 24 + pi * panel + etyk

        def X(v, x0=x0, p=p):
            return x0 + (min(max(v, p["xmin"]), p["xmax"]) - p["xmin"]) / (p["xmax"] - p["xmin"]) * (szer - 20)
        dol = gora + wiersz * len(p["kategorie"])
        for t in p["ticki"]:
            s.linia(X(t), gora - 6, X(t), dol, SIATKA)
            s.tekst(X(t), dol + 18, liczba(t, 1), 11, TEKST2, "middle")
        s.tekst(x0 + (szer - 20) / 2, dol + 40, p["os"], 12, TEKST2, "middle")
        for r, kat in enumerate(p["kategorie"]):
            y0 = gora + r * wiersz + wiersz / 2
            s.tekst(x0 - 10, y0 + 4, ETYKIETA[kat], 11, TEKST, "end")
            for j, m in enumerate(MODELE):
                o = p["dane"][kat][m]
                y = y0 + (j - 1) * 9
                lo, hi = o["srednia"] - 1.96 * o["se"], o["srednia"] + 1.96 * o["se"]
                s.linia(X(lo), y, X(hi), y, KOLOR[m], GRUBOSC[m])
                s.znacznik(m, X(o["srednia"]), y, f"{nazwy[m]}, {ETYKIETA[kat]}, {p['os']}: {liczba(o['srednia'])} "
                                                  f"(SE {liczba(o['se'])})", r=4)
    s.zapisz(nazwa)


def sedziowie(L, nazwy):
    wyg = L["sedziowie"]["wygrane"]
    pary = [("bielik_nad_slayer", "Bielik nad Slayerem"), ("lfm_nad_slayer", "LFM nad Slayerem"),
            ("lfm_nad_bielik", "LFM nad Bielikiem")]
    oceniajacy = [("sedzia1", "sędzia 1"), ("sedzia2", "sędzia 2"), ("lacznie", "łącznie")]
    w, lewa, gora, wiersz = 760, 200, 90, 70
    h = gora + wiersz * len(pary) + 60
    s = Svg(w, h, "Preferencje sędziów w parach (polecenia otwarte, seed 1 szablonu A)",
            "Odsetek wygranych drugiego modelu pary, remis = 0,5; odcinek = ±1,96 SE po poleceniach; linia 0,5 = brak preferencji")
    szer = w - lewa - 40

    def X(v):
        return lewa + min(max(v, 0), 1) * szer
    dol = gora + wiersz * len(pary)
    for t in (0, 0.25, 0.5, 0.75, 1):
        s.linia(X(t), gora - 6, X(t), dol, TEKST2 if t == 0.5 else SIATKA, 1, "4 3" if t == 0.5 else None)
        s.tekst(X(t), dol + 18, liczba(t, 2), 11, TEKST2, "middle")
    s.tekst(lewa + szer / 2, dol + 40, "odsetek wygranych drugiego modelu pary", 12, TEKST2, "middle")
    ksztalt = {"sedzia1": "slayer", "sedzia2": "bielik", "lacznie": "lfm"}  # tu kształt = sędzia, kolor neutralny
    for r, (k, et) in enumerate(pary):
        y0 = gora + r * wiersz + wiersz / 2
        s.tekst(lewa - 12, y0 + 4, et, 12, TEKST, "end")
        for j, (sk, se) in enumerate(oceniajacy):
            o = wyg[k]["razem"][sk]
            y = y0 + (j - 1) * 14
            s.linia(X(o["srednia"] - 1.96 * o["se"]), y, X(o["srednia"] + 1.96 * o["se"]), y, TEKST2, 2)
            m = ksztalt[sk]
            stary = KOLOR[m]
            KOLOR[m] = TEKST if sk == "lacznie" else TEKST2
            s.znacznik(m, X(o["srednia"]), y, f"{et}, {se}: {liczba(o['srednia'])} (SE {liczba(o['se'])}, n {o['n']})", r=4)
            KOLOR[m] = stary
            s.tekst(X(1) + 2, y + 4, "", 10)
    # legenda kształtów (sędziowie)
    for j, (sk, se) in enumerate(oceniajacy):
        m = ksztalt[sk]
        stary = KOLOR[m]
        KOLOR[m] = TEKST if sk == "lacznie" else TEKST2
        s.znacznik(m, lewa + j * 150, 70, se)
        KOLOR[m] = stary
        s.tekst(lewa + j * 150 + 12, 74, se, 12, TEKST)
    s.zapisz("sedziowie.svg")


def trudnosc(L):
    """Mapa pozycji: oś x = średnia poprawność trzech modeli (łatwość), oś y = rozstęp między modelami
    (rozróżnianie); panel na kategorię, jedna seria, więc bez legendy kolorów."""
    poz = L["pozycje"]
    kats = ["pl_jezyk", "pl_wiedza", "wiedza_ogolna", "rozumowanie", "matematyka", "kod", "angielski"]
    kol, pw, ph, lewa, gora = 4, 200, 170, 60, 80
    w = lewa + kol * (pw + 30)
    h = gora + 2 * (ph + 60)
    s = Svg(w, h, "Trudność i rozróżnianie pozycji (polecenia sprawdzalne)",
            "x: średnia poprawność 3 modeli (0 = wszyscy źle), y: rozstęp max − min (0 = pozycja nie rozróżnia); punkt = polecenie")
    for n, kat in enumerate(kats):
        x0 = lewa + (n % kol) * (pw + 30)
        y0 = gora + (n // kol) * (ph + 60)
        s.tekst(x0, y0 - 6, ETYKIETA[kat], 12, TEKST, waga=600)
        for t in (0, 0.5, 1):
            s.linia(x0 + t * pw, y0, x0 + t * pw, y0 + ph, SIATKA)
            s.linia(x0, y0 + ph - t * ph, x0 + pw, y0 + ph - t * ph, SIATKA)
            s.tekst(x0 + t * pw, y0 + ph + 14, liczba(t, 1), 10, TEKST2, "middle")
            s.tekst(x0 - 4, y0 + ph - t * ph + 3, liczba(t, 1), 10, TEKST2, "end")
        s.linia(x0 + pw * 0, y0 + ph - ph * 2 / 3, x0 + pw, y0 + ph - ph * 2 / 3, TEKST2, 1, "4 3")
        licznik = {}
        for pid, p in sorted(poz.items()):
            if p["kat"] != kat:
                continue
            v = [p[m] for m in MODELE]
            x, y = sum(v) / 3, max(v) - min(v)
            klucz = (round(x, 3), round(y, 3))
            licznik[klucz] = licznik.get(klucz, 0) + 1
            # nakładające się punkty: rządek do środka panelu (po 8), kolejne rządki nad nim, żeby było je widać
            c = licznik[klucz] - 1
            dx = (c % 8) * 4 * (-1 if x > 0.5 else 1)
            dy = -(c // 8) * 5 if y < 0.5 else (c // 8) * 5
            s.el.append(f"<g><title>{escape(pid)}: Slayer {liczba(v[0], 2)}, Bielik {liczba(v[1], 2)}, LFM {liczba(v[2], 2)}"
                        f"</title><circle cx='{x0 + x * pw + dx:.1f}' cy='{y0 + ph - y * ph + dy:.1f}' r='3' fill='{TEKST2}' "
                        f"fill-opacity='0.6' stroke='{TLO}' stroke-width='1.5'/></g>")
    s.tekst(lewa, h - 14, "Linia przerywana: próg rozstępu 2/3 z aneksu A1 (pozycja „rozróżnia”).", 11, TEKST2)
    s.zapisz("trudnosc.svg")


def main():
    L = json.loads((BADANIE / "wyniki/LICZBY.json").read_text(encoding="utf-8"))
    nazwy = L["modele"]
    (BADANIE / "charts").mkdir(exist_ok=True)
    op = L["opisy"]
    spr = ["pl_jezyk", "pl_wiedza", "wiedza_ogolna", "rozumowanie", "matematyka", "kod", "angielski", "razem"]
    kropki_z_ci("poprawnosc.svg", "Poprawność odpowiedzi według kategorii (szablon A, średnia 3 seedów)",
                "Kropka = średnia po poleceniach, odcinek = ±1,96 SE; wyżej = lepiej", op["poprawnosc"], spr, nazwy,
                0, 1, "odsetek poprawnych odpowiedzi", [0, 0.25, 0.5, 0.75, 1])
    wsz = spr[:-1] + ["tekst_techniczny", "razem"]
    kropki_z_ci("bpb.svg", "Bity na bajt odpowiedzi wzorcowej (BPB, szablon A)",
                "Kropka = średnia po poleceniach, odcinek = ±1,96 SE; niżej = model lepiej przewiduje wzorzec", op["bpb_A"],
                wsz, nazwy, 0, 1.2, "BPB (bit na bajt UTF-8)", [0, 0.3, 0.6, 0.9, 1.2])
    male_wielokrotne("koniec_powtorzenia.svg", "Naturalny koniec odpowiedzi i powtórzenia",
                     ("Lewy panel: odsetek odpowiedzi zakończonych przed limitem tokenów (wszystkie polecenia), wyżej = częściej.",
                      "Prawy panel: odsetek powtórzonych 3-gramów słów (polecenia otwarte), niżej = mniej powtórzeń. Odcinek = ±1,96 SE."),
                     [dict(dane=op["koniec"], kategorie=wsz, xmin=0, xmax=1, ticki=[0, 0.5, 1], os="naturalny koniec"),
                      dict(dane=op["rep3"], kategorie=["pl_jezyk", "angielski", "tekst_techniczny", "razem"],
                           xmin=0, xmax=0.6, ticki=[0, 0.2, 0.4, 0.6], os="powtórzone 3-gramy")], nazwy)
    sedziowie(L, nazwy)
    trudnosc(L)
    print("charts/: poprawnosc.svg bpb.svg koniec_powtorzenia.svg sedziowie.svg trudnosc.svg")


if __name__ == "__main__":
    main()
