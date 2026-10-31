"""Sprawdza, czy raporty .md (i podane .html) mówią to samo co results/LICZBY.json.

Kod wyjścia 1, gdy:
 (a) liczba dziesiętna w polskim zapisie (0,330, −0,047) nie odpowiada żadnej wartości z LICZBY.json
     po zaokrągleniu do liczby cyfr w tekście ("pkt" i "%" porównuje z wartością × 100, "x SE" z |z|);
     plik w katalogu benchmarku z LICZBY.json["benchmarki"] (i linia z jego nazwą) porównuje z wartościami
     tego benchmarku, a gdy benchmark ma "skala": 100, także liczby bez "%" (tabele w %);
 (b) zdanie z oceną różnicy (lepszy, gorszy, luka, przewaga, poprawa, pogorszenie, istotny, prawdziwy)
     w akapicie z liczbami nie ma SE, z ani werdyktu (szum / prawdopodobne / pewne / w granicach);
 (c) słowo werdyktu („pewne”, „prawdopodobna”) stoi przy teście, którego żadne porównanie z tej
     rodziny nie ma w LICZBY.json tak mocnego werdyktu.
 (d)-(f) bramki raportów z metadanymi w LICZBY.json "raporty" (bramki_raportu): werdykt na zbiorze
     wieloparadygmatowym bez SE klastrowanego / Holma, werdykt grupy < 3 członków, różne tokenizery bez
     wyniku na token.
Wyjątek na linię: `<!-- liczba-spoza-wynikow: powód -->` wyłącza (a), `<!-- ocena-bez-se: powód -->` wyłącza (b).

Uruchom: python tools/liczby.py && python tools/sprawdz_raporty.py [plik.html ...]
"""
import bisect
import html
import json
import re
import sys
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
SILA = {"nierozstrzygalne": 0, "szum": 0, "prawdopodobne": 1, "pewne": 2}

# (plik, nagłówek sekcji albo None = cały plik, reguły, powód) — krótka lista, każdy wpis z powodem
WYLACZENIA = [
    ("slayer-1b/wygaszanie/PROGI.md", None, "abc", "progi zapisane przed pomiarem, nie wyniki"),
    ("slayer-1b/testy_danych_slayer/PROGI.md", None, "abc", "progi zapisane przed pomiarem, nie wyniki"),
    ("results/LICZBY.md", None, "abc", "plik wygenerowany przez liczby.py"),
    ("slayer-1b/wygaszanie/wyniki/porownanie.md", None, "abc", "plik wygenerowany przez porownaj.py z porownanie.json"),
    ("slayer-1b/testy_danych_slayer/README.md", None, "a", "plan przebiegu: koszty, czasy, rozmiary; wyników jeszcze nie ma"),
    ("slayer-1b/wygaszanie/README.md", "## Rozbieg i wybór K", "a", "log instancji i trenera (cena, tok/s, strata kroku), nie ma go w surowych JSON-ach"),
    ("common/README.md", None, "a", "liczby ze Space Arka (bench50, scores-history), nie z naszych surowych wyników"),
    ("benchmarks/blimp/THRESHOLDS.md", None, "abc", "thresholds written before the measurement, not results"),
]
# modele z HF przynoszą własne README (karty modeli), venv-y pliki .md pakietów
# English reports (prefix of the path): dot decimals ("0.792", "-2.87 points") and the test whose
# numbers a line may use without naming it (a table row of BLIMP.md does not repeat "BLiMP").
PLIKI_EN = {"benchmarks/blimp/": "blimp"}
POMIN_KATALOGI = {".git", ".venv", "venv", "node_modules", "__pycache__", "models"}

LICZBA = re.compile(r"(?<![\d,.\w])([−-]?)(\d+),(\d+)(?!,?\d)")
LICZBA_EN = re.compile(r"(?<![\d,.\w])([−-]?)(\d+)\.(\d+)(?!\.?\d)")
JEDNOSTKA_POMIN = re.compile(r"\s*(\$|h\b|s\b|s/|GB|tok\b|tok/|tok\.|mld|mln|bln|min\b|M\b)")
SKALOWANA = re.compile(r"\s*(pkt|%|p\.\s?p\.)")
SKALOWANA_EN = re.compile(r"\s*(points?\b|pts?\b|%)")
LISTA_SE = re.compile(r"((?:[−-]?\d+(?:,\d+)?\s*/\s*)*[−-]?\d+(?:,\d+)?)\s*SE\b")
Z_ROWNA = re.compile(r"\bz\s*=\s*([−-]?\d+(?:,\d+)?)")
Z_ROWNA_EN = re.compile(r"\b[zt]\s*=\s*([−-]?\d+(?:\.\d+)?)")  # t = clustered z (mean / SE over paradigms)
WERSJA_MODELU = re.compile(r"Slayer\s*$")  # "Slayer 1.06" is a model name, not a number
OCENA = re.compile(r"\b(lepsz\w*|gorsz\w*|lu(?:ka|ki|kę|ką|ce|k)\b|przewag\w*|popraw(?:a|y|ie|ę|ą)\b|"
                   r"pogorsz\w*|pogarsz\w*|istotn\w*|prawdziw\w*)", re.IGNORECASE)
DOWOD = re.compile(r"\bSE\b|\bz\s*=|szum|pewn|prawdopodobn|bez (?:wykrywalnej )?różnicy|w granicach|\|Δ\|",
                   re.IGNORECASE)
WERDYKT = [("pewne", re.compile(r"\bpewn(?:e|a|y|ą|ych)\b", re.IGNORECASE)),
           ("prawdopodobne", re.compile(r"\bprawdopodobn\w*", re.IGNORECASE))]
ZDANIE = re.compile(r"(?<=[.!?])\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ*„(])")
WYJATEK_A = "liczba-spoza-wynikow"
WYJATEK_B = "ocena-bez-se"
KLUCZ_BENCHMARKU = "benchmark:"


# ---------- czyste funkcje ----------

def parsuj_liczbe(tekst):
    """'−0,047' -> (-0.047, 3); '2,2807' -> (2.2807, 4). Minus typograficzny i ASCII."""
    m = re.fullmatch(r"\s*([−-]?)(\d+),(\d+)\s*", tekst)
    if not m:
        raise ValueError(f"nie liczba w polskim zapisie: {tekst!r}")
    znak = -1 if m.group(1) else 1
    return znak * float(f"{m.group(2)}.{m.group(3)}"), len(m.group(3))


def pasuje(x, cyfr, v):
    """Czy wartość v zaokrąglona do `cyfr` miejsc daje x (porównanie modułów: tekst pisze też „spadek o 0,047”)."""
    return abs(abs(v) - abs(x)) <= 0.5 * 10 ** (-cyfr) * (1 + 1e-9) + 1e-12


class Zbior:
    """Posortowane moduły wartości do szybkiego dopasowania po zaokrągleniu."""

    def __init__(self, wartosci):
        self.w = sorted(abs(v) for v in wartosci)

    def zawiera(self, x, cyfr):
        tol = 0.5 * 10 ** (-cyfr) * (1 + 1e-9) + 1e-12
        i = bisect.bisect_left(self.w, abs(x) - tol)
        return i < len(self.w) and self.w[i] <= abs(x) + tol


def test_sciezki(sciezka, aliasy):
    """Test, którego dotyczy ścieżka wartości ('.../siqa_cloze/acc/wartosc' -> 'siqa'), albo None."""
    for seg in sciezka.split("/"):
        seg = "med" if seg == "medmcqa" else seg
        for t in sorted(aliasy, key=len, reverse=True):
            if seg == t or seg.startswith(t + "_"):
                return t
    return None


def zbiory(liczby):
    """{test albo None: {'surowa'|'skalowana'|'z': Zbior}}; None = wartości bez testu (loss, wikitext)."""
    surowe, zety = {}, {}
    for sciezka, v in liczby["wartosci"].items():
        surowe.setdefault(test_sciezki(sciezka, liczby["aliasy"]), []).append(v)
    for p in liczby["porownania"]:
        t = p["test"] if p["test"] in liczby["aliasy"] else None
        for k in ("wartosc_a", "wartosc_b", "se_a", "se_b", "roznica", "se_niezalezne", "se_parowane"):
            if p.get(k) is not None:
                surowe.setdefault(t, []).append(p[k])
        for k in ("z_niezalezne", "z_parowane"):
            if p.get(k) is not None:
                zety.setdefault(t, []).append(p[k])
    out = {}
    for t in set(surowe) | set(zety):
        s = surowe.get(t, [])
        out[t] = {"surowa": s, "skalowana": [v * 100 for v in s], "z": zety.get(t, [])}
    # Tests with hundreds of values (BLiMP: 67 paradigms) only match lines that name them;
    # in the catch-all set they would let almost any 3-digit number pass.
    tylko_z_nazwa = set(liczby.get("tylko_z_nazwa", []))
    listy = {r: [v for t, d in out.items() if t not in tylko_z_nazwa for v in d[r]] for r in ("surowa", "skalowana", "z")}
    wszystkie = {r: Zbior(listy[r]) for r in listy}
    wynik = {t: {r: Zbior(d[r] + out.get(None, {}).get(r, [])) for r in d} for t, d in out.items()}
    wynik["*"] = wszystkie
    for nazwa, b in liczby.get("benchmarki", {}).items():
        v = list(b["wartosci"].values())
        skalowane = [x * b.get("skala", 1) for x in v]
        # "globalne": the benchmark's own values plus all global ones (its numbers live in both places)
        g = listy if b.get("globalne") else {"surowa": [], "skalowana": [], "z": []}
        wynik[KLUCZ_BENCHMARKU + nazwa] = {"surowa": Zbior(v + skalowane + g["surowa"]),
                                         "skalowana": Zbior([x * 100 for x in v] + g["skalowana"]), "z": Zbior(g["z"])}
    return wynik


def plik_en(plik):
    """(kropka, test_domyslny) dla pliku: raport po angielsku z PLIKI_EN albo (False, None)."""
    for prefiks, test in PLIKI_EN.items():
        if plik.startswith(prefiks):
            return True, test
    return False, None


def benchmark_pliku(plik, liczby):
    """Benchmark, do którego katalogu należy plik raportu, albo None."""
    for nazwa, b in liczby.get("benchmarki", {}).items():
        if any(plik.startswith(p) for p in b["pliki"]):
            return nazwa
    return None


def benchmarki_w_tekscie(tekst, liczby):
    return {n for n, b in liczby.get("benchmarki", {}).items()
            if any(re.search(rf"\b{re.escape(a)}", tekst, re.IGNORECASE) for a in b["aliasy"])}


def werdykt_z(z):
    a = abs(z)
    return "pewne" if a >= 3 else "prawdopodobne" if a >= 2 else "szum"


def ocena_bez_dowodu(zdanie, kontekst=""):
    """Zdanie ocenia różnicę, a ani ono, ani `kontekst` (pogrubiony wstęp akapitu) nie ma SE/z/werdyktu."""
    return bool(OCENA.search(zdanie)) and not DOWOD.search(zdanie) and not DOWOD.search(kontekst)


def zadeklarowany_werdykt(tekst):
    """Najmocniejsze słowo werdyktu w tekście: 'pewne', 'prawdopodobne' albo None."""
    for nazwa, wz in WERDYKT:
        if wz.search(tekst):
            return nazwa
    return None


def rodzaj_liczby(linia, start, koniec, kropka=False):
    """'z' (liczba przed „SE” albo po „z =”), 'skalowana' (pkt, %; w EN points/pts) albo 'surowa'."""
    if not kropka:
        for m in LISTA_SE.finditer(linia):
            if m.start(1) <= start and koniec <= m.end(1):
                return "z"
    for m in (Z_ROWNA_EN if kropka else Z_ROWNA).finditer(linia):
        if m.start(1) <= start < m.end(1):
            return "z"
    if (SKALOWANA_EN if kropka else SKALOWANA).match(linia, koniec):
        return "skalowana"
    return "surowa"


def bez_kodu(linia):
    """Usuwa `kod` i komentarze HTML (liczby w nich nie są twierdzeniami raportu)."""
    linia = re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), linia)
    return re.sub(r"<!--.*?-->", lambda m: " " * len(m.group(0)), linia)


def niepasujace_liczby(linia, zb, aliasy=None, benchmarki=(), kropka=False, test_domyslny=None):
    """Liczby z linii, których nie da się odtworzyć z LICZBY.json: [(tekst, rodzaj)].
    Gdy linia nazywa testy (ARC-E, SIQA...), liczba musi pasować do wartości tych testów albo
    wartości bez testu (loss, WikiText); linia bez nazwy testu porównuje ze wszystkimi
    (albo, w pliku z PLIKI_EN, z testem tego pliku). `benchmarki` (plik w katalogu benchmarku albo
    linia z jego nazwą) dokładają pule tych benchmarków. `kropka`: zapis dziesiętny z kropką (pliki EN)."""
    czysta = bez_kodu(linia)
    testy = [t for t in testy_w_tekscie(czysta, aliasy) if t in zb] if aliasy else []
    if not testy and test_domyslny is not None and test_domyslny in zb:  # zb has a None key too
        testy = [test_domyslny]
    pule = [zb[KLUCZ_BENCHMARKU + b] for b in benchmarki if KLUCZ_BENCHMARKU + b in zb]
    zle = []
    for m in (LICZBA_EN if kropka else LICZBA).finditer(czysta):
        if JEDNOSTKA_POMIN.match(czysta, m.end()) or (kropka and WERSJA_MODELU.search(czysta[:m.start()])):
            continue
        x, cyfr = parsuj_liczbe(m.group(0).replace(".", ",") if kropka else m.group(0))
        rodzaj = rodzaj_liczby(czysta, m.start(), m.end(), kropka)
        kandydaci = ([zb[t][rodzaj] for t in testy] or ([] if pule else [zb["*"][rodzaj]])) + [p[rodzaj] for p in pule]
        if not any(k.zawiera(x, cyfr) for k in kandydaci):
            zle.append((m.group(0), rodzaj))
    return zle


def testy_w_tekscie(tekst, aliasy):
    # (?<!\w): "BLiMP" must not match inside "MultiBLiMP"
    return {t for t, nazwy in aliasy.items()
            if any(re.search(r"(?<!\w)" + re.escape(n), tekst, re.IGNORECASE) for n in nazwy)}


def rodziny_kontekstu(tekst, plik=""):
    r = set()
    if re.search(r"Pythi", tekst):
        r.add("slayer_vs_pythia")
    if re.search(r"1\.0[03]\s*(→|->|do|a)", tekst) or "wersj" in tekst:
        r.add("wersje")
    if re.search(r"wygasz|A−B|A-B", tekst) or plik.startswith("slayer-1b/wygaszanie/"):
        r.add("wygaszanie")
    return r or {"slayer_vs_pythia", "wersje", "wygaszanie"}


def za_mocny_werdykt(klauzula, kontekst, liczby, plik="", zdanie=""):
    """[(test, zadeklarowany, najmocniejszy_w_danych)] dla testów, których dane nie dźwigają słowa werdyktu.
    Testy bierze z klauzuli, a gdy klauzula żadnego nie nazywa (komórka werdyktu w tabeli), z całego zdania."""
    deklaracja = zadeklarowany_werdykt(klauzula)
    if not deklaracja:
        return []
    rodziny = rodziny_kontekstu(kontekst + " " + klauzula, plik)
    testy = testy_w_tekscie(klauzula, liczby["aliasy"]) or testy_w_tekscie(zdanie, liczby["aliasy"])
    out = []
    for test in sorted(testy):
        sily = [SILA[p["werdykt"]] for p in liczby["porownania"]
                if p["test"] == test and p["rodzina"] in rodziny and p.get("werdykt")]
        if not sily:
            continue
        najm = max(sily)
        if SILA[deklaracja] > najm:
            out.append((test, deklaracja, [k for k, v in SILA.items() if v == najm][0]))
    return out


# ---------- przejście po plikach ----------

def jednostki(linie):
    """Akapity (lista (nr_linii, tekst)); wiersz tabeli, nagłówek i punkt listy zaczynają nowy akapit."""
    akapity, biezacy, w_kodzie = [], [], False
    for nr, linia in enumerate(linie, 1):
        s = linia.strip()
        if s.startswith("```"):
            w_kodzie = not w_kodzie
            if biezacy:
                akapity.append(biezacy)
            biezacy = []
            continue
        if w_kodzie:
            continue
        if not s:
            if biezacy:
                akapity.append(biezacy)
            biezacy = []
            continue
        if s.startswith(("|", "#", "- ", "* ")) or re.match(r"\d+\.\s", s):
            if biezacy:
                akapity.append(biezacy)
            biezacy = [(nr, linia)]
            if s.startswith(("|", "#")):
                akapity.append(biezacy)
                biezacy = []
            continue
        biezacy.append((nr, linia))
    if biezacy:
        akapity.append(biezacy)
    return akapity


def zdania(akapit):
    """[(nr_linii_startu, zdanie)] z akapitu sklejonego spacjami."""
    tekst, starty = "", []
    for nr, l in akapit:
        starty.append((len(tekst), nr))
        tekst += bez_kodu(l).strip() + " "
    out, poz = [], 0
    for kawalek in ZDANIE.split(tekst):
        i = tekst.find(kawalek, poz)
        nr = max(n for off, n in starty if off <= max(i, 0))
        out.append((nr, kawalek.strip()))
        poz = i + len(kawalek)
    return [(n, z) for n, z in out if z]


def wylaczone(plik, sekcja, regula):
    for p, s, reg, _ in WYLACZENIA:
        if p == plik and regula in reg and (s is None or (sekcja or "").startswith(s)):
            return True
    return False


def sprawdz_tekst(plik, linie, liczby, zb):
    bledy = []
    sekcja, sekcje = None, {}
    for nr, l in enumerate(linie, 1):
        if l.startswith("#"):
            sekcja = l.strip()
        sekcje[nr] = sekcja
    w_kodzie = False
    bench_pliku = benchmark_pliku(plik, liczby)
    for nr, l in enumerate(linie, 1):
        if l.strip().startswith("```"):
            w_kodzie = not w_kodzie
            continue
        if w_kodzie or WYJATEK_A in l or wylaczone(plik, sekcje[nr], "a"):
            continue
        bench = benchmarki_w_tekscie(bez_kodu(l), liczby) | ({bench_pliku} if bench_pliku else set())
        kropka, test_domyslny = plik_en(plik)
        for tekst, rodzaj in niepasujace_liczby(l, zb, liczby["aliasy"], sorted(bench), kropka=kropka,
                                                test_domyslny=test_domyslny):
            opis = {"z": "jako z (×SE)", "skalowana": "jako pkt/% (×100)", "surowa": "jako wartość"}[rodzaj]
            bledy.append((plik, nr, f"(a) {tekst} nie odpowiada żadnej liczbie z LICZBY.json {opis}"))
    for akapit in jednostki(linie):
        nr0 = akapit[0][0]
        tekst_akapitu = " ".join(bez_kodu(l) for _, l in akapit)
        surowy_akapit = " ".join(l for _, l in akapit)
        wstep = re.match(r"\s*(?:[-*]\s+|\d+\.\s+)?\*\*(.+?)\*\*", tekst_akapitu)
        wstep = wstep.group(1) if wstep else ""
        ma_liczby = bool(re.search(r"\d", tekst_akapitu))
        for nr, zd in zdania(akapit):
            if (ma_liczby and not wylaczone(plik, sekcje[nr0], "b") and WYJATEK_B not in surowy_akapit
                    and ocena_bez_dowodu(zd, wstep)):
                bledy.append((plik, nr, f"(b) ocena różnicy bez SE/z/werdyktu: „{zd[:90]}”"))
            if wylaczone(plik, sekcje[nr0], "c"):
                continue
            for klauzula in re.split(r"[;|]", zd):
                for test, dekl, dane in za_mocny_werdykt(klauzula, tekst_akapitu, liczby, plik, zd):
                    bledy.append((plik, nr, f"(c) „{dekl}” przy {test}, a najmocniejszy werdykt w LICZBY.json to „{dane}”"))
    return bledy


# ---------- bramki raportów z metadanymi (LICZBY.json "raporty"; starsze raporty ich nie mają) ----------

SLOWO_WERDYKTU = re.compile(r"\b(certain|probable|pewn\w*|prawdopodobn\w*)\b", re.IGNORECASE)
BEZ_WERDYKTU = {"nierozstrzygalne", "undetermined"}
NA_TOKEN = re.compile(r"\b(per[ -]token|per[ -]byte|na token|na bajt)\b", re.IGNORECASE)


def bramki_raportu(meta, linie, liczby):
    """Gates for a report on a multi-paradigm set (BLiMP, MultiBLiMP, MMLU):
    (d) a verdict word needs an SE/z clustered by paradigm in LICZBY.json, and a ranking of
        more than one paradigm needs a Holm field for every paradigm;
    (e) a group with < 3 members may only be "undetermined" at the paradigm level: in the metadata and in the
        clustered-verdict column of its table row (meta "kolumna_werdyktu_klastrowego"; the pair-level verdict
        in the same row is a claim about the pairs and stays); without that key, anywhere in the row;
    (f) models with different tokenizers need a per-token comparison in LICZBY.json and in the text."""
    plik, bledy = meta["plik"], []
    tekst = "\n".join(linie)
    por = {p["id"]: p for p in liczby["porownania"]}
    if meta.get("wieloparadygmatowy") and SLOWO_WERDYKTU.search(tekst):
        k = por.get(meta.get("porownanie_klastrowe") or "")
        if not k or k.get("se") is None or k.get("z") is None:
            bledy.append((plik, 0, "(d) werdykt na zbiorze wieloparadygmatowym bez SE/z klastrowanego po paradygmatach"))
        holm = meta.get("holm") or {}
        if meta.get("k_paradygmatow", 0) > 1 and (len(holm) < meta["k_paradygmatow"]
                                                   or not all(isinstance(v, bool) for v in holm.values())):
            bledy.append((plik, 0, "(d) ranking paradygmatów bez poprawki Holma dla każdego paradygmatu"))
    kolumna = meta.get("kolumna_werdyktu_klastrowego")
    for g in meta.get("grupy", []):
        if g["k"] >= 3:
            continue
        if g["werdykt"] not in BEZ_WERDYKTU:
            bledy.append((plik, 0, f"(e) grupa {g['nazwa']} ma {g['k']} członków, a werdykt „{g['werdykt']}”"))
        for nr, l in enumerate(linie, 1):
            if not l.startswith(f"| {g['etykieta']} |"):
                continue
            komorka = komorka_kolumny(linie, nr - 1, kolumna) if kolumna else l
            if komorka is None:
                bledy.append((plik, nr, f"(e) wiersz grupy {g['nazwa']} bez kolumny „{kolumna}” w nagłówku tabeli"))
            elif SLOWO_WERDYKTU.search(komorka) or not any(s in komorka for s in BEZ_WERDYKTU):
                bledy.append((plik, nr, f"(e) wiersz grupy {g['nazwa']} (k = {g['k']}) z werdyktem paradygmatów "
                                        f"innym niż undetermined: „{komorka.strip()}”"))
    if len(set((meta.get("tokenizery") or {}).values())) > 1:
        t = por.get(meta.get("porownanie_na_token") or "")
        if not t or t.get("z") is None or not NA_TOKEN.search(tekst):
            bledy.append((plik, 0, "(f) modele z różnymi tokenizerami, a raport nie ma wyniku na token/bajt"))
    return bledy


def komorki(l):
    return [c.strip() for c in l.strip().strip("|").split("|")]


def komorka_kolumny(linie, i, nazwa):
    """Cell of table row linie[i] under header `nazwa` (header = first line of the table block)."""
    j = i
    while j > 0 and linie[j - 1].lstrip().startswith("|"):
        j -= 1
    naglowek = komorki(linie[j])
    if nazwa not in naglowek:
        return None
    wiersz = komorki(linie[i])
    k = naglowek.index(nazwa)
    return wiersz[k] if k < len(wiersz) else ""


def bramka_generatora(meta, liczby, korzen=None):
    """(g) a generated report must equal, byte for byte, the generator output from LICZBY.json: a number,
    verdict or sentence edited by hand, or a stale report after new numbers, gives code 1."""
    import importlib.util
    korzen = korzen or KORZEN
    gen = meta.get("generator")
    if not gen:
        return []
    try:
        spec = importlib.util.spec_from_file_location("_generator_raportu", korzen / gen["modul"])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        wejscie = json.loads((korzen / gen["wejscie"]).read_text(encoding="utf-8"))
        oczekiwane = getattr(mod, gen["funkcja"])(liczby, wejscie)
    except Exception as e:  # a generator that cannot run from LICZBY.json is a failed gate, not a pass
        return [(meta["plik"], 0, f"(g) generator {gen['modul']} nie działa na LICZBY.json: {type(e).__name__}: {e}")]
    katalog = (korzen / meta["plik"]).parent
    bledy = []
    for nazwa, tresc in sorted(oczekiwane.items()):
        p = katalog / nazwa
        rel = str(p.relative_to(korzen))
        if not p.exists():
            bledy.append((rel, 0, f"(g) brak pliku generowanego przez {gen['modul']}"))
            continue
        jest = p.read_text(encoding="utf-8")
        if jest != tresc:
            a, b = jest.splitlines(), tresc.splitlines()
            nr = next((i for i, (x, y) in enumerate(zip(a, b), 1) if x != y), min(len(a), len(b)) + 1)
            bledy.append((rel, nr, f"(g) plik różni się od wyjścia {gen['modul']} z LICZBY.json (pierwsza różnica "
                                   f"w tej linii); przegeneruj: python benchmarks/blimp/blimp.py raport"))
    return bledy


def linie_html(tekst):
    tekst = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", tekst)
    tekst = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h\d|td|th)>", "\n", tekst)
    tekst = html.unescape(re.sub(r"<[^>]+>", " ", tekst))
    return [re.sub(r"[ \t]+", " ", l).strip() for l in tekst.splitlines()]


def pliki_md(korzen):
    for p in sorted(korzen.rglob("*.md")):
        katalogi = p.relative_to(korzen).parts[:-1]
        if not POMIN_KATALOGI & set(katalogi) and not any(k.startswith(".") for k in katalogi):
            yield p


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    sciezka_liczb = KORZEN / "results/LICZBY.json"
    if not sciezka_liczb.exists():
        print("brak results/LICZBY.json: najpierw python tools/liczby.py")
        return 2
    liczby = json.loads(sciezka_liczb.read_text())
    zb = zbiory(liczby)
    cele = [(str(p.relative_to(KORZEN)), p) for p in pliki_md(KORZEN)]
    cele += [(a, Path(a)) for a in argv]
    bledy = []
    for nazwa, p in cele:
        tekst = p.read_text(encoding="utf-8")
        linie = linie_html(tekst) if p.suffix.lower() in (".html", ".htm") else tekst.splitlines()
        bledy += sprawdz_tekst(nazwa, linie, liczby, zb)
    for meta in liczby.get("raporty", []):
        p = KORZEN / meta["plik"]
        if not p.exists():
            bledy.append((meta["plik"], 0, "(d) raport z metadanymi w LICZBY.json nie istnieje"))
            continue
        bledy += bramki_raportu(meta, p.read_text(encoding="utf-8").splitlines(), liczby)
        bledy += bramka_generatora(meta, liczby)
    for plik, nr, powod in bledy:
        print(f"{plik}:{nr}: {powod}")
    print(f"{len(cele)} plików, {len(bledy)} problemów")
    return 1 if bledy else 0


if __name__ == "__main__":
    sys.exit(main())
