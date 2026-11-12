"""PAPER.md z wyniki/LICZBY.json (każda liczba wyniku pochodzi stamtąd; strażnik repo: tools/sprawdz_raporty.py).

python -I code/paper.py  -> PAPER.md

Stałe protokołu (progi, seedy, limity) stoją w liniach z komentarzem `liczba-spoza-wynikow`.
Przykładowe rozmowy: po jednym poleceniu na kategorię, random.Random(SEED_PRZYKLADOW).sample(posortowane id, 1).
"""
import gzip
import json
import random
import sys
from pathlib import Path

BADANIE = Path(__file__).resolve().parent.parent
MODELE = ["slayer", "bielik", "lfm"]
KR = {"slayer": "S", "bielik": "B", "lfm": "L"}
KAT = ["pl_jezyk", "pl_wiedza", "wiedza_ogolna", "rozumowanie", "matematyka", "kod", "angielski", "tekst_techniczny"]
SPR = KAT[:-1]
ET = {"pl_jezyk": "język polski", "pl_wiedza": "wiedza o Polsce", "wiedza_ogolna": "wiedza ogólna",
      "rozumowanie": "rozumowanie", "matematyka": "matematyka", "kod": "kod (Python)", "angielski": "angielski",
      "tekst_techniczny": "tekst techniczny", "razem": "razem"}
PARY = ["slayer-bielik", "slayer-lfm", "bielik-lfm"]
PARA_ET = {"slayer-bielik": "S−B", "slayer-lfm": "S−L", "bielik-lfm": "B−L", "lfm-slayer": "L−S", "lfm-bielik": "L−B"}
SEED_PRZYKLADOW = 20261114
POZA = "<!-- liczba-spoza-wynikow: stała protokołu -->"


def czytaj_jsonl(p):
    """jsonl albo jsonl.gz (w repo leżą wersje .gz surowych wyników; rozpakowane są gitignorowane)."""
    p = Path(p)
    tekst = gzip.decompress(p.read_bytes()).decode("utf-8") if p.suffix == ".gz" else p.read_text(encoding="utf-8")
    return [json.loads(x) for x in tekst.splitlines() if x.strip()]


def tresc(L):
    """Treść PAPER.md z LICZBY.json (i plików zestawu do przykładów)."""
    N = L["modele"]

    def f(x, c=3):
        if x is None:
            return "—"
        s = f"{x:.{c}f}"
        if s.lstrip("-").strip("0.") == "":
            s = s.lstrip("-")
        return s.replace(".", ",").replace("-", "−")


    def fp(p):
        return "—" if p is None else f(p, 4)


    def ms(o, c=3):
        return f"{f(o['srednia'], c)} ({f(o['se'], c)})"


    def por(met, kat, para):
        return L["porownania"][met][kat][para]


    def zz(r):
        """„różnica (SE …, z = …, werdykt)” z werdyktem z samego z; Holm osobno po średniku."""
        if r.get("z") is None:
            return f"{f(r['roznica'])} (SE {f(r['se'])}, nierozstrzygalne: SE = 0)"
        s = f"{f(r['roznica'])} (SE {f(r['se'])}, z = {f(r['z'], 2)}, {r['werdykt']}"
        if r.get("p_holm") is not None:
            s += f"; po Holmie: {r['werdykt_holm']}"
        return s + ")"


    def jsonl(p):
        return czytaj_jsonl(p)


    def hip(hid):
        return next(h for h in L["hipotezy"] if h["id"] == hid)


    def wiersz_h(hid, kat):
        return next(r for r in hip(hid)["wiersze"] if r["kategoria"] == kat)


    out = []
    o = out.append


    def tabela(nag, wiersze):
        o("| " + " | ".join(nag) + " |")
        o("|" + "---|" * len(nag))
        for w in wiersze:
            o("| " + " | ".join(str(x) for x in w) + " |")
        o("")


    op = L["opisy"]
    sb_raz = por("poprawnosc", "razem", "slayer-bielik")
    sl_raz = por("poprawnosc", "razem", "slayer-lfm")
    sed = L["sedziowie"]
    h91, h92 = sed["hipotezy"]["H9.1"], sed["hipotezy"]["H9.2"]
    aud = L["audyt"]
    kw = L["kontrola_wzorcow"]
    kn = L["kontrola_narzedzia"]

    # ---------------------------------------------------------------- nagłówek i streszczenie
    o("# Slayer 1.08 w rozmowie: swobodna generacja i prawdopodobieństwo odpowiedzi wobec Bielika 1.5B i LFM2.5 1.2B")
    o("")
    o("Plik generuje `code/paper.py` z `wyniki/LICZBY.json` (ten z kolei `code/analiza.py` z surowych wyników); nie "
      "edytuj go ręcznie. Protokół: `PROTOKOL.md` (commit `99bfeab`), aneks `PROTOKOL_ANEKS.md` (commit `3ad7739`), "
      "oba zapisane przed odczytem metryk. Pomiar 12.11.2026, jeden przebieg, wynik wstępny w rozumieniu METODOLOGII "
      "(„Siła dowodu”): przed użyciem na zewnątrz potrzebuje przeliczenia `needs-recheck`.")
    o("")
    o("## Streszczenie")
    o("")
    o(f"Na 240 nowych poleceniach po polsku i angielsku Slayer 1.08 odpowiada poprawnie rzadziej niż Bielik 1.5B "
      f"(łącznie {f(op['poprawnosc']['razem']['slayer']['srednia'])} wobec {f(op['poprawnosc']['razem']['bielik']['srednia'])}, "
      f"różnica {zz(sb_raz)}), najmocniej w matematyce i języku polskim, i przypisuje wzorcowym odpowiedziom "
      f"mniejsze prawdopodobieństwo (wyższe BPB) we wszystkich 8 kategoriach. Od LFM2.5 Slayer różni się mniej "
      f"(poprawność łącznie {zz(sl_raz)}): ma niższe BPB polskiego tekstu i więcej trafień w wiedzy o Polsce, a "
      f"niższą poprawność w matematyce i angielskim. Najsilniejszy sygnał swoistej wady Slayera to bardzo niskie prawdopodobieństwo "
      f"końca dokumentu po zakończonej odpowiedzi (sonda EOS); powtórzeń i przecieków znaczników z pilota ten pomiar "
      f"nie potwierdził.")
    o("")

    # ---------------------------------------------------------------- 1. pytania i hipotezy
    o("## 1. Pytania i hipotezy")
    o("")
    o("Pytania z protokołu (sekcja 1): **P1** w których kategoriach Slayer 1.08 (S) różni się od Bielika 1.5B (B) i "
      "LFM2.5 1.2B (L) w poprawności swobodnej generacji i w prawdopodobieństwie wzorcowej odpowiedzi; **P2** czy S ma "
      "swoiste wady generacji (brak końca, powtórzenia, przecieki znaczników); **P3** co z tego wynika dla danych do "
      "dalszego treningu (interpretacja, oznaczona jako taka).")
    o("")
    o("Hipotezy pochodzą z pilota (45 poleceń, jedna próbka, bez protokołu, poza repo); pilot jest tylko źródłem "
      "hipotez, jego liczb tu nie używam. Pełne brzmienie "
      "i reguła werdyktu: `PROTOKOL.md`, sekcja 1. Skrót:")
    o("")
    tabela(["id", "twierdzenie", "metryka", "kategorie"], [
        ["H1.1, H1.2", "S kończy odpowiedź naturalnie rzadziej niż B i L", "odsetek naturalnych końców", "8"],
        ["H1.3, H1.4", "po zakończonej odpowiedzi z „\\n” S daje EOS niższe prawdopodobieństwo niż B i L", "log10 p(EOS)", "6"],
        ["H2.1, H2.2", "S powtarza się częściej niż B i L", "rep3 (powtórzone 3-gramy)", "kategorie z poleceniami otwartymi"],
        ["H3.1, H3.2", "S wie mniej niż B: niższa poprawność, wyższe BPB", "poprawność, BPB", "pl_wiedza, wiedza_ogolna"],
        ["H4.1–H4.4", "S słabszy niż B i L w matematyce i rozumowaniu", "poprawność, BPB", "matematyka, rozumowanie"],
        ["H5.1, H5.2", "S rzadziej pisze kod przechodzący testy niż B i L", "poprawność", "kod"],
        ["H6.1", "BPB polszczyzny S nie jest wyższe od B o więcej niż margines (równoważność)", "BPB", "pl_jezyk, tekst_techniczny"],
        ["H6.2", "BPB polszczyzny S niższe niż L", "BPB", "pl_jezyk, pl_wiedza, tekst_techniczny"],
        ["H7", "S przecieka znacznikami rozumowania (`<think>` i podobne)", "odsetek przecieków", "łącznie"],
        ["H8", "L pisze matematykę w formacie GSM8K częściej niż S i B", "odsetek formatu", "matematyka"],
        ["H9.1, H9.2", "sędziowie wolą B od S i L od S", "odsetek wygranych", "42 polecenia otwarte"],
        ["H10", "angielski: BPB S wyższe niż L", "BPB", "angielski"],
    ])
    o("Reguła werdyktu (protokół, sekcja 1): różnica parowana po poleceniach, SE = sd/√n po poleceniach, z = różnica/SE; "
      "|z| od 3 „pewne”, od 2 do 3 „prawdopodobne”, poniżej 2 „szum”. Poprawka Holma w rodzinie hipoteza × para × "
      "metryka po kategoriach. Teza jest potwierdzona, gdy znak się zgadza i po Holmie jest co najmniej "
      "„prawdopodobna”, obalona przy znaku przeciwnym i tej samej sile, w pozostałych przypadkach nierozstrzygnięta. "
      "Wynik pod progiem nie znaczy „brak różnicy”.")
    o("")

    # ---------------------------------------------------------------- 2. metoda
    o("## 2. Metoda")
    o("")
    o("**Zestaw.** 240 poleceń, 8 kategorii po 30, napisanych od zera przez model Claude według `dane/SPEC.md`; tylko do "
      "oceny, nie do treningu. Typy: krótka odpowiedź, korekta zdania, liczba, funkcja Pythona z ukrytymi testami (198 "
      "poleceń sprawdzalnych automatycznie) i 42 polecenia otwarte (pisanie, tekst techniczny), oceniane przez "
      "sędziów. Skład: `PROTOKOL.md`, sekcja 2; wszystkie polecenia z odpowiedziami: [`ROZMOWY.md`](ROZMOWY.md).")
    o("")
    o("**Modele.** Wszystkie w float32 na Mac M5 Pro (MPS), torch 2.15.0, transformers 5.2.2:")
    o("")
    tabela(["model", "repozytorium HF", "rewizja", "uwaga"], [
        ["Slayer 1.08 (S)", "SlayerLab/Slayer1B-1.08", "`ea0945b1`", "checkpoint w toku treningu serii; forward `common/slayer_model.py`"],
        ["Bielik 1.5B (B)", "speakleash/Bielik-1.5B-v3", "`4b250496`", "po pełnym treningu"],
        ["LFM2.5 1.2B (L)", "LiquidAI/LFM2.5-1.2B-Base", "`7453bca9`", "po pełnym treningu"],
    ])
    o("Wagi leżą poza repo, ich sha256 jest w nagłówku każdego surowego pliku (`wyniki/surowe/*.jsonl.gz`).")
    o("")
    o("**Prompt i dekodowanie.** Few-shot z 3 przykładami tej samej kategorii. Szablon A (główny) „Polecenie: / "
      "Odpowiedź:” (angielski „Task: / Answer:”), szablon B (kontrola) „### Zadanie / ### Rozwiązanie”. W szablonie A "
      "trzy próbki (temperatura 0,7, top-p 0,9, seedy 1–3) i greedy, w szablonie B greedy. " + POZA)
    o("Odpowiedź kończy się na tokenie końca dokumentu (EOS), na znaczniku następnego polecenia albo na limicie tokenów.")
    o("")
    o("**Metryki** (`code/ocena.py`, protokół sekcja 4): (a) poprawność automatyczna, wartość polecenia = średnia 3 "
      "próbek; (b) BPB wzorca = −Σ log p(tokenów wzorca | prompt) / (ln 2 · bajty UTF-8), na bajt, bo tokenizery są "
      "różne; (c) naturalny koniec przed limitem tokenów i (c2) sonda EOS: log10 p(EOS) po tekście „Pytanie: … "
      "Odpowiedź: <wzorzec>\\n” bez przykładów; (d) rep3 = udział 3-gramów słów powtórzonych w tej samej odpowiedzi; "
      "(e) ślepa ocena parami przez dwóch sędziów (osobne agenty Claude), A / B / remis.")
    o("")
    o("**Statystyka.** Różnice parowane po poleceniach (te same polecenia dla wszystkich modeli), SE po poleceniach "
      "(próbki jednego polecenia uśrednione przed różnicą), z, werdykt i Holm jak w sekcji 1. Bootstrap po poleceniach "
      "jako kontrola wrażliwości (10 000 losowań, seed 20261112). " + POZA)
    o("")
    o(f"**Moc (MDE).** Najmniejsza różnica wykrywalna z mocą 80% pod Holmem przy 8 kategoriach to (z_Holm + z_moc) · SE, "
      f"z_Holm = {f(L['mde']['z_holm_m8'], 3)}, z_moc = {f(L['mde']['z_moc80'], 3)}, SE z danych. Różnica mniejsza od MDE "
      f"w danej kategorii mogła istnieć i nie zostać wykryta:")
    o("")
    md = L["mde"]["kategorie"]
    tabela(["kategoria", "MDE poprawności S−B", "S−L", "B−L", "MDE BPB S−B", "S−L", "B−L"],
           [[ET[k]] + [f(md[k]["poprawnosc"][p]["mde80"]) if "poprawnosc" in md[k] else "—" for p in PARY]
            + [f(md[k]["bpb_A"][p]["mde80"]) for p in PARY] for k in KAT])
    o("Poprawność w jednej kategorii (n = 24 albo 30) wykrywa tylko różnice rzędu kilkunastu do kilkudziesięciu punktów "
      "procentowych; BPB jest dokładniejsze o rząd wielkości. Dlatego w wiedzy i rozumowaniu BPB jest główną metryką, a "
      "„szum” w poprawności nie przeczy wynikowi BPB.")
    o("")

    # ---------------------------------------------------------------- 3. kontrola narzędzia i skażenia
    o("## 3. Kontrola narzędzia i skażenia")
    o("")
    ac, ob = kn["arc_challenge"], kn["openbookqa"]
    o(f"**Narzędzie.** Tym samym kodem log p, który liczy BPB, policzyłam dla Slayera 1.08 `ARC-Challenge` (n = {ac['n']}) "
      f"i `OpenBookQA` (n = {ob['n']}) z promptami karty modelu. Wynik: acc {f(ac['acc']['nasz'], 6)} i acc_norm "
      f"{f(ac['acc_norm']['nasz'], 6)} wobec {f(ac['acc']['referencja'], 6)} i {f(ac['acc_norm']['referencja'], 6)} w "
      f"`EVALUATION.json`; `OpenBookQA` acc {f(ob['acc']['nasz'], 3)} i acc_norm {f(ob['acc_norm']['nasz'], 3)}, "
      f"identycznie jak referencja. Warunek odtworzenia (różnica do 0,02) spełniony dla wszystkich czterech wartości. "
      + "<!-- liczba-spoza-wynikow: próg etapu B -->")
    o("Dla Bielika i LFM opublikowanych liczb w tym ustawieniu nie ma; ich ścieżkę sprawdza test spójności log p z "
      "pełnym forwardem i próba dymna (greedy w batchu 4 wobec batchu 1: 0 różnic na 10 pozycjach każdego modelu). To "
      "test spójności, nie odtworzenie cudzej liczby.")
    o("")
    sk = L["skazenie"]
    o(f"**Skażenie.** Wspólne 13-gramy słów (polecenie + wzorzec + testy) z `GSM8K`, `ARC`, `OpenBookQA`, `HumanEval`, "
      f"`MBPP`: {sum(sk['13'].values())} trafień na 240 poleceń. Przy 8-gramach {sum(sk['8'].values())} trafienia w dwóch "
      f"pozycjach (`kod-15`, `kod-28`), wyłącznie ciągi liczb i liter z danych testów, nie treść. Skan nie łapie "
      f"tłumaczeń ani parafraz, a krótkie polecenia (rozumowanie) mają mniej niż 13 słów, więc wynik 0 nie wyklucza "
      f"skażenia treścią.")
    o("")

    # ---------------------------------------------------------------- 4. jakość pytań
    o("## 4. Jakość pytań")
    o("")
    o("**A1. Trudność i rozróżnianie** (aneks A1). Polecenie rozróżnia modele, gdy rozstęp średnich poprawności trzech "
      "modeli wynosi co najmniej 2/3. Polecenia, na których wszyscy zawsze mylą się albo zawsze trafiają, nic nie mówią "
      "o różnicach:")
    o("")
    a1 = L["jakosc"]["a1"]
    tabela(["kategoria", "n", "rozróżnia", "nie rozróżnia", "zawsze dobrze", "zawsze źle"],
           [[ET[k], a1[k]["n"], a1[k]["rozroznia"], a1[k]["nie_rozroznia"], a1[k]["zawsze_dobrze"], a1[k]["zawsze_zle"]]
            for k in SPR])
    o(f"Kod jest najsłabiej zbudowaną kategorią: {a1['kod']['zawsze_zle']} z 30 poleceń żaden model nie rozwiązał ani razu, "
      f"więc kategoria mierzy głównie, czy model pisze jakikolwiek działający kod. W rozumowaniu "
      f"{a1['rozumowanie']['nie_rozroznia']} z 30 poleceń nie rozróżnia modeli. Mapa wszystkich pozycji:")
    o("")
    o("![Trudność i rozróżnianie pozycji](charts/trudnosc.svg)")
    o("")
    o("**A2. Rzetelność.** SNR = wariancja między modelami / wariancja między seedami (dla BPB: między szablonami A i B). "
      "Zgodność seedów = średnia korelacja Pearsona wyników 0/1 między parami seedów:")
    o("")
    a2 = L["jakosc"]["a2"]


    def kor(x):
        return "nieokreślona" if x is None else f(x, 2)


    tabela(["kategoria", "SNR poprawności", "SNR BPB (wobec szablonu)", "zgodność seedów S", "B", "L"],
           [[ET[k], f(a2[k]["snr_poprawnosc"]["snr"], 1) if "snr_poprawnosc" in a2[k] else "—",
             f(a2[k]["snr_bpb_wzgledem_szablonu"]["snr"], 1)]
            + [kor(a2[k][m].get("seedy_pearson_srednia")) if "seedy_pearson_srednia" in a2[k][m] else "—" for m in MODELE]
            for k in KAT])
    o(f"W wiedzy ogólnej SNR BPB wynosi {f(a2['wiedza_ogolna']['snr_bpb_wzgledem_szablonu']['snr'], 1)}: zmiana szablonu "
      f"przesuwa średnie BPB bardziej, niż różnią się modele, więc różnice BPB w tej kategorii zależą od szablonu "
      f"(werdykty niżej podaję razem ze znakiem w szablonie B). W rozumowaniu SNR poprawności wynosi "
      f"{f(a2['rozumowanie']['snr_poprawnosc']['snr'], 1)}, czyli różnice modeli ledwo wychodzą ponad zmienność seedów.")
    o("")
    o("**A3. Trafność zewnętrzna** (opisowa, 3 modele). Ranking naszej metryki wobec testów przebiegu centralnego "
      "`results/full-run-2026-11/` (tau Kendalla przy 3 modelach przyjmuje tylko 4 wartości):")
    o("")
    a3 = L["jakosc"]["a3"]
    rows = []
    for k in KAT:
        if not a3[k]["testy"]:
            rows.append([ET[k], "NOT RUN (brak testu dla trzech modeli)", "—", "—", "—", "—", "—"])
            continue
        for t, x in a3[k]["testy"].items():
            c = 1 if x["wartosci"]["slayer"] > 2 else 3
            rows.append([ET[k], f"`{t}`", f(x["wartosci"]["slayer"], c), f(x["wartosci"]["bielik"], c), f(x["wartosci"]["lfm"], c),
                         f(x["kendall_tau"], 3), sum(v["zgodny_znak"] for v in x["roznice_par"].values())])
    tabela(["kategoria", "test centralny", "S", "B", "L", "tau Kendalla", "zgodne znaki par (z 3)"], rows)
    o("Zgodność jest słaba poza matematyką i `arc-challenge`. W języku polskim kierunek jest odwrotny: w teście par "
      "minimalnych Slayer ma najwyższy wynik, a w naszej generacji najniższy. Test par minimalnych mierzy, który z dwóch "
      "gotowych zdań model uważa za bardziej prawdopodobny, a nasze polecenia każą samemu wyprodukować formę; to różne "
      "umiejętności, więc rozbieżność nie unieważnia żadnego z wyników, ale zakazuje przenosić wniosek z jednego na "
      "drugi.")
    o("")
    o(f"**A4. Kontrola wzorców.** Osobny agent bez dostępu do wyników sprawdził {kw['n']} losowych pozycji (10% "
      f"sprawdzalnych): {kw['poprawne']} wzorców poprawnych, {kw['bledne']} błędnych, {kw['niejednoznaczne']} "
      f"niejednoznacznych; górna granica 95% odsetka błędnych wzorców w całym zestawie (Clopper-Pearson) to "
      f"{f(kw['bledne_gorna_ci95'], 3)}. Wskazał {kw['ryzyko_oceny']} reguł oceny, które mogą odrzucić poprawną albo "
      f"przyjąć błędną odpowiedź: " + ", ".join(f"`{i}`" for i in kw["ryzyko_id"]) + ".")
    o("")
    wr = L["wrazliwosc_regul"]
    o(f"**Wrażliwość na te reguły (eksploracyjna).** Ocena wszystkich odpowiedzi trzech modeli z poprawionymi 6 "
      f"regułami zmienia {wr['liczba_zmienionych_ocen']} ocen, więc wynik główny (reguły protokołu bez zmian) i wynik "
      f"wrażliwości są identyczne; żaden werdykt nie zależy od tych reguł.")
    o("")
    o(f"**Audyt oceny automatycznej.** Próbę {aud['n']} ocen automatycznych (3 na komórkę model × kategoria sprawdzalna, losowanie "
      f"`random.Random({aud['seed']})`, plik `dane/audyt_proba.jsonl`) oceniłam ręcznie z powodem każdej oceny "
      f"(`dane/audyt_oceny.jsonl`). Zgodność z oceną automatyczną {f(aud['zgodnosc'], 3)}: "
      f"{aud['falszywe_trafienia']} fałszywych trafień, {aud['falszywe_odrzucenia']} fałszywych odrzuceń. Górna granica "
      f"95% odsetka błędów oceny (Clopper-Pearson) to {f(aud['bledy_gorna_ci95'], 3)}, poniżej progu 10% ze zlecenia, "
      f"więc żaden werdykt kategorii nie jest oznaczony jako zależny od błędu oceny. Audyt nie był ślepy: znałam ocenę "
      f"automatyczną i sama pisałam reguły (ograniczenia, sekcja 9). " + "<!-- liczba-spoza-wynikow: próg 10% ze zlecenia -->")
    o("")

    # ---------------------------------------------------------------- 5. wyniki
    o("## 5. Wyniki per kategoria")
    o("")
    o("Średnia po poleceniach, w nawiasie SE. Poprawność: odsetek poprawnych (średnia 3 próbek szablonu A), wyżej lepiej. "
      "BPB: bity na bajt wzorca w szablonie A, niżej lepiej.")
    o("")
    tabela(["kategoria", "poprawność S", "B", "L", "BPB S", "B", "L"],
           [[ET[k]] + [ms(op["poprawnosc"][k][m]) if k in op["poprawnosc"] else "—" for m in MODELE]
            + [ms(op["bpb_A"][k][m]) for m in MODELE] for k in KAT + ["razem"]])
    o("![Poprawność według kategorii](charts/poprawnosc.svg)")
    o("")
    o("![BPB według kategorii](charts/bpb.svg)")
    o("")
    o("**Tokenizery.** BPB jest liczone na bajt, ale modele dzielą tekst inaczej; obok NLL na token i bajty na token "
      "(łącznie, szablon A):")
    o("")
    tabela(["model", "NLL na token", "bajty na token"],
           [[N[m], ms(op["nll_na_token_A"]["razem"][m]), ms(op["bajty_na_token_A"]["razem"][m])] for m in MODELE])
    o("")
    o("**Koniec odpowiedzi, powtórzenia, puste odpowiedzi.**")
    o("")
    tabela(["kategoria", "naturalny koniec S", "B", "L", "rep3 S", "B", "L", "pusta odpowiedź S", "B", "L"],
           [[ET[k]] + [ms(op["koniec"][k][m]) for m in MODELE]
            + [ms(op["rep3"][k][m]) if k in op["rep3"] else "—" for m in MODELE]
            + [ms(op["pusta"][k][m]) for m in MODELE] for k in KAT + ["razem"]])
    o("![Naturalny koniec i powtórzenia](charts/koniec_powtorzenia.svg)")
    o("")
    so = L["sonda_eos_kod_lfm"]
    o(f"Prawie wszystkie odpowiedzi kończą się przed limitem tokenów, bo szablon daje modelom znacznik następnego "
      f"polecenia, który zatrzymuje generację. Wyjątek to kod Bielika (naturalny koniec "
      f"{f(op['koniec']['kod']['bielik']['srednia'])}): długie funkcje dochodzą do limitu. Odsetek pustych odpowiedzi "
      f"LFM w kodzie to {f(op['pusta']['kod']['lfm']['srednia'])}: pierwszym tokenem jest `<|im_end|>` (id 7), który "
      f"protokół liczy jako EOS LFM. Sonda eksploracyjna (`code/sonda_eos_kod.py`, {so['n']} poleceń) daje medianę "
      f"p tego tokenu na starcie odpowiedzi {f(so['mediana_p_im_end'], 2)}. Wynik LFM w kodzie zależy więc od "
      f"definicji EOS; zostaje według protokołu.")
    o("")


    def tab_par(met):
        rows = []
        for k in KAT:
            if k not in L["porownania"][met]:
                continue
            for p in PARY:
                r = por(met, k, p)
                rows.append([ET[k], PARA_ET[p], f(r["roznica"]), f(r["se"]), f(r["z"], 2) if r["z"] is not None else "—",
                             r["werdykt"], fp(r.get("p_holm")), r.get("werdykt_holm", "—")])
        tabela(["kategoria", "para", "różnica", "SE", "z", "werdykt", "p Holma", "werdykt po Holmie"], rows)


    o("**Mapa różnic par (eksploracyjna poza wierszami z tabeli hipotez).** Poprawność, różnica X−Y, Holm w rodzinie "
      "para × metryka po kategoriach:")
    o("")
    tab_par("poprawnosc")
    o("BPB, różnica X−Y (ujemna = X przypisuje wzorcowi wyższe prawdopodobieństwo):")
    o("")
    tab_par("bpb_A")

    o("**Ocena sędziów** (42 polecenia otwarte × 3 pary = 126 par, odpowiedź seed 1 szablonu A, strony i kolejność "
      "losowane, klucz poza paczką).")
    o("")
    o(f"Zgodność dwóch sędziów: kappa Cohena {f(sed['kappa'], 3)}, zgodność surowa {f(sed['zgodnosc_surowa'], 3)} (po "
      f"przełożeniu stron na tożsamość modeli). Sędzia 2 dostał pary w odwrotnej kolejności. Skłonność do strony A "
      f"(odsetek wyborów A wśród werdyktów bez remisu):")
    o("")
    tabela(["sędzia", "A", "B", "remis", "odsetek A", "SE", "z", "werdykt"],
           [[s.replace("sedzia", "sędzia "), x["A"], x["B"], x["remis"], f(x["strona_A_odsetek"]), f(x["strona_A_se"]),
             f(x["strona_A_z"], 2), x["strona_A_werdykt"]] for s, x in sed["sedziowie"].items()])
    o("Żaden sędzia nie wybiera strony A wyraźnie częściej niż B. Ponownej oceny z zamienionymi stronami nie było "
      "(NOT RUN), więc jedynym sprawdzeniem kolejności jest odwrócona kolejność par u sędziego 2.")
    o("")
    o(f"W {sed['pary_z_pusta_odpowiedzia']} parach jedna z odpowiedzi była pusta po obcięciu białych znaków; instrukcja "
      f"nie mówiła, jak je oceniać (ograniczenia, sekcja 9).")
    o("")
    o("Odsetek wygranych drugiego modelu pary (remis = 0,5), osobno dla każdego sędziego i łącznie; z wobec 0,5 "
      "(brak preferencji). Zamiast modelu Bradleya-Terry'ego podaję odsetek wygranych z SE po poleceniach (protokół, "
      "metryka (e)):")
    o("")
    rows = []
    for k, et in (("bielik_nad_slayer", "B nad S"), ("lfm_nad_slayer", "L nad S"), ("lfm_nad_bielik", "L nad B")):
        for zakres in ("razem", "pl_jezyk", "angielski", "tekst_techniczny"):
            for s in ("sedzia1", "sedzia2", "lacznie"):
                x = sed["wygrane"][k][zakres][s]
                rows.append([et, ET[zakres], {"sedzia1": "sędzia 1", "sedzia2": "sędzia 2", "lacznie": "łącznie"}[s], x["n"],
                             f(x["srednia"]), f(x["se"]), f(x["z"], 2) if x["z"] is not None else "—", x["werdykt"]])
    tabela(["para", "zakres", "sędzia", "n", "odsetek wygranych", "SE", "z", "werdykt"], rows)
    o("Wiersze per kategoria są opisowe (n od 6 do 30); potwierdzające są tylko wiersze „razem, łącznie” dla H9.")
    o("")
    o("![Preferencje sędziów](charts/sedziowie.svg)")
    o("")

    # ---------------------------------------------------------------- 6. werdykty hipotez
    o("## 6. Werdykty hipotez")
    o("")
    o("Każde porównanie osobno, Holm w rodzinie jednej hipotezy (kategorie). „Znak w greedy / B”: czy różnica ma ten sam "
      "znak w greedy szablonu A i w szablonie B (wtórne, protokół sekcja 5).")
    o("")
    rows = []
    for h in L["hipotezy"]:
        for r in h["wiersze"]:
            wt = [v for k, v in r.items() if k.startswith("wtorne_")]
            znak = "—" if not wt else "/".join("tak" if v["ten_sam_znak"] else "nie" for v in wt)
            rows.append([h["id"], PARA_ET.get(f"{h['a']}-{h['b']}"), ET[r["kategoria"]], f(r["roznica"]), f(r["se"]),
                         f(r["z"], 2) if r["z"] is not None else "—", r["werdykt"], fp(r["p_holm"]), r["werdykt_holm"],
                         r["teza"], znak])
    tabela(["teza", "para", "kategoria", "różnica", "SE", "z", "werdykt", "p Holma", "werdykt po Holmie", "stan tezy",
            "znak w greedy / B"], rows)
    o("H6.1 (równoważność, bez Holma): teza potwierdzona, gdy górna granica bootstrapowego CI95 różnicy S−B jest poniżej "
      "marginesu 0,05 bit/bajt, obalona, gdy dolna granica jest powyżej. " + POZA)
    o("")
    tabela(["kategoria", "różnica S−B", "SE", "z", "werdykt", "CI95 bootstrap", "stan tezy"],
           [[ET[r["kategoria"]], f(r["roznica"]), f(r["se"]), f(r["z"], 2), r["werdykt"],
             f"[{f(r['ci95_bootstrap'][0])}; {f(r['ci95_bootstrap'][1])}]", r["teza"]] for r in L["h6_1"]])
    h7 = L["h7"]
    o(f"**H7 (przecieki):** żadna z 240 × 4 odpowiedzi szablonu A (3 próbki i greedy) żadnego modelu nie zawiera `<think>` ani znaczników czatu; "
      f"teza {h7['teza']}. Przeciek z pilota się nie powtórzył; możliwe wyjaśnienie to inny format promptu w pilocie (nie sprawdzone).")
    o("")
    o(f"**H8 (format GSM8K):** w matematyce żaden model nie użył `<<a=b>>` ani `#### n`; teza "
      f"{wiersz_h('H8.1', 'matematyka')['teza']} (SE = 0). Polskie polecenia i przykłady few-shot w innym formacie "
      f"mogły ten nawyk LFM wyłączyć.")
    o("")
    tabela(["teza", "porównanie", "n", "odsetek wygranych", "SE", "z", "werdykt", "stan tezy"],
           [["H9.1", "B nad S", h91["n"], f(h91["odsetek"]), f(h91["se"]), f(h91["z"], 2), h91["werdykt"], h91["teza"]],
            ["H9.2", "L nad S", h92["n"], f(h92["odsetek"]), f(h92["se"]), f(h92["z"], 2), h92["werdykt"], h92["teza"]]])

    o("**Wyjaśnienia zastępcze, teza po tezie.**")
    o("")
    r = wiersz_h("H1.1", "kod")
    rt = wiersz_h("H1.2", "tekst_techniczny")
    bo = op["bajty_odpowiedzi"]["kod"]
    o(f"- **H1.1–H1.2 (koniec).** W żadnej kategorii S nie kończy rzadziej niż B ani L po Holmie, bo znacznik "
      f"następnego polecenia zatrzymuje generację każdego modelu. W kodzie S kończy częściej niż B, różnica {zz(r)}, "
      f"a w tekście technicznym częściej niż L, {zz(rt)}; w tych kategoriach teza jest obalona. Zastępcze wyjaśnienie "
      f"dla kodu: odpowiedzi B są dłuższe (średnio {f(bo['bielik']['srednia'], 1)} bajtów wobec "
      f"{f(bo['slayer']['srednia'], 1)} u S) i częściej dochodzą do limitu, a limit liczony w tokenach różnych "
      f"tokenizerów daje różną długość w bajtach. Metryka nie mierzy więc umiejętności zakończenia bez podpowiedzi "
      f"szablonu.")
    r3 = wiersz_h("H1.3", "matematyka")
    r4 = wiersz_h("H1.4", "matematyka")
    o(f"- **H1.3–H1.4 (sonda EOS).** Po wzorcowej odpowiedzi S daje EOS prawdopodobieństwo o rzędy wielkości niższe: "
      f"w matematyce log10 p różni się od B o {zz(r3)}, od L o {zz(r4)}; teza potwierdzona w "
      f"{sum(x['teza'] == 'potwierdzona' for x in hip('H1.3')['wiersze'])} z 6 kategorii wobec B i w "
      f"{sum(x['teza'] == 'potwierdzona' for x in hip('H1.4')['wiersze'])} z 6 wobec L. Zastępcze wyjaśnienie: sonda mierzy koniec dokumentu po tekście „Pytanie/Odpowiedź” bez "
      f"przykładów, a B i L mogły widzieć dużo krótkich dokumentów tego kształtu (dane instrukcyjne), S mniej; to "
      f"wskazuje na dane, nie na architekturę.")
    o(f"- **H2.1–H2.2 (powtórzenia).** Wszystkie różnice rep3 to szum po Holmie; teza nierozstrzygnięta. Powtórzenia z "
      f"pilota mogły wynikać z dłuższych odpowiedzi bez znacznika stopu.")
    r = wiersz_h("H3.1", "wiedza_ogolna")
    r2 = wiersz_h("H3.2", "pl_wiedza")
    o(f"- **H3.1–H3.2 (wiedza).** Wiedza ogólna: poprawność S−B {zz(r)}; BPB wiedzy o Polsce S−B {zz(r2)}. Zastępcze "
      f"wyjaśnienia: B ma 1,5 mld parametrów wobec ok. 1 mld i jest po pełnym treningu na korpusie z dużym udziałem "
      f"polskiego, a 1.08 jest checkpointem w toku. Wzorce w stylu Claude obniżają BPB modelu, który widział podobne "
      f"teksty. " + "<!-- liczba-spoza-wynikow: liczba parametrów z kart modeli -->")
    ra, rb = wiersz_h("H4.1", "matematyka"), wiersz_h("H4.2", "matematyka")
    o(f"- **H4.1–H4.4 (matematyka i rozumowanie).** Matematyka: poprawność S−B {zz(ra)}, S−L {zz(rb)}; odsetek "
      f"poprawnych rozwiązań S to {f(op['poprawnosc']['matematyka']['slayer']['srednia'])}. Zastępcze wyjaśnienia: B i L mogły "
      f"trenować na zadaniach tekstowych z rozwiązaniami krok po kroku (L w pilocie pisał w formacie GSM8K), więc różnica "
      f"mówi o obecności takich danych, nie o „zdolności rozumowania”. Rozumowanie S−L w poprawności to szum po Holmie, a "
      f"SNR tej kategorii jest niski (sekcja 4).")
    r5, r6 = wiersz_h("H5.1", "kod"), wiersz_h("H5.2", "kod")
    o(f"- **H5.1–H5.2 (kod).** S−B {zz(r5)}; S−L {zz(r6)}. S nie napisał ani jednej funkcji przechodzącej testy. "
      f"Porównanie z L jest skażone pustymi odpowiedziami LFM (`<|im_end|>` jako EOS, sekcja 5): przy innej definicji "
      f"EOS wynik L mógłby być wyższy (regeneracja NOT RUN).")
    ra, rb, rc = wiersz_h("H6.2", "pl_jezyk"), wiersz_h("H6.2", "tekst_techniczny"), wiersz_h("H10", "angielski")
    o(f"- **H6.1, H6.2, H10 (język danych).** Polszczyzna S wobec B: BPB wyższe o więcej niż margines w obu kategoriach "
      f"(H6.1 obalona). Wobec L: BPB S niższe, w tekście technicznym {zz(rb)}, w języku polskim {zz(ra)}; angielski S−L "
      f"{zz(rc)}. Oczywiste wyjaśnienie to skład danych: S ma ok. 17,5% angielskiego, L jest głównie angielski, B "
      f"polski. Te wyniki opisują proporcje języków w treningu, nie jakość modelu. "
      + "<!-- liczba-spoza-wynikow: udział angielskiego z notatki lab-modeli -->")
    o(f"- **H9 (sędziowie).** B nad S: odsetek {f(h91['odsetek'])} (SE {f(h91['se'])}, z = {f(h91['z'], 2)}, "
      f"{h91['werdykt']}), potwierdzona. L nad S: odsetek {f(h92['odsetek'])} (SE {f(h92['se'])}, z = "
      f"{f(h92['z'], 2)}, {h92['werdykt']}), nierozstrzygnięta. Zastępcze wyjaśnienie: sędziowie to modele Claude, "
      f"a wzorce i kryteria też pisał Claude, więc mogą premiować styl, nie treść; kappa {f(sed['kappa'], 3)} mówi "
      f"tylko, że dwaj sędziowie tej samej rodziny się zgadzają.")
    o("")

    # ---------------------------------------------------------------- 7. przykładowe rozmowy
    o("## 7. Przykładowe rozmowy")
    o("")
    o(f"Reguła wyboru: po jednym poleceniu na kategorię, `random.Random({SEED_PRZYKLADOW}).sample(posortowane id "
      f"kategorii, 1)`, odpowiedź seed 1 szablonu A każdego modelu, dosłownie. Wszystkie polecenia: "
      f"[`ROZMOWY.md`](ROZMOWY.md).")
    o("")
    poz = {p["id"]: p for p in jsonl(BADANIE / "dane/polecenia.jsonl")}
    oceny = {(x["model"], x["id"]): x for x in jsonl(BADANIE / "wyniki/oceny_pozycji.jsonl.gz")[1:]}
    gen = {}
    for m in MODELE:
        for x in jsonl(BADANIE / f"wyniki/surowe/gen_{m}_A.jsonl.gz"):
            if not x.get("naglowek"):
                gen[(m, x["id"])] = {w["dekodowanie"]: w["odpowiedz"] for w in x["wyniki"]}
    rng = random.Random(SEED_PRZYKLADOW)
    for k in KAT:
        pid = rng.sample(sorted(i for i, p in poz.items() if p["kat"] == k), 1)[0]
        p = poz[pid]
        o(f"**{ET[k]}, `{pid}`.** Polecenie: {p['polecenie']}")
        o("")
        if p["typ"] == "kod":
            o("Wzorzec:")
            o("")
            o("```python\n" + p["wzorzec"].rstrip("\n") + "\n```")
        else:
            o(f"Wzorzec: {p['wzorzec']}")
        o("")
        for m in MODELE:
            v = oceny[(m, pid)]["dekodowania"]["A_s1"]["poprawna"]
            ocena = "bez oceny automatycznej" if p["typ"] == "otwarte" else ("poprawna" if v == 1 else "niepoprawna")
            t = gen[(m, pid)]["s1"].replace("```", "` ` `")
            o(f"{N[m]} (ocena: {ocena}):")
            o("")
            o("```text\n" + (t.rstrip("\n") if t.strip() else "(pusta odpowiedź)") + "\n```")
            o("")

    # ---------------------------------------------------------------- 8. dane i nowe testy
    o("## 8. Dane do treningu i nowe testy (interpretacja)")
    o("")
    o("Każda propozycja wskazuje lukę, którą ma wypełnić, i siłę dowodu tej luki. Licencje źródeł nie były sprawdzane w "
      "tym badaniu i są oznaczone „do sprawdzenia”. Wzorców i poleceń tego zestawu nie wolno używać do treningu "
      "(warunki Anthropic dla treści Claude).")
    o("")
    pm, km = por("poprawnosc", "matematyka", "slayer-bielik"), por("poprawnosc", "kod", "slayer-bielik")
    pj = por("poprawnosc", "pl_jezyk", "slayer-bielik")
    bm = por("bpb_A", "matematyka", "slayer-bielik")
    eos = wiersz_h("H1.3", "pl_wiedza")
    o(f"1. **Polskie zadania tekstowe z rozwiązaniem krok po kroku i jawnym wynikiem.** Luka: matematyka, poprawność "
      f"S−B {zz(pm)}, BPB S−B {zz(bm)}. Siła: wysoka dla istnienia różnicy, niska dla przyczyny (zastępcze wyjaśnienia w "
      f"sekcji 6). Źródło: zbiory zadań szkolnych na otwartej licencji albo tłumaczenia zbiorów angielskich; licencja "
      f"do sprawdzenia dla każdego zbioru.")
    o(f"2. **Kod Pythona z testami (funkcja + test).** Luka: kod, S−B {zz(km)}, S bez ani jednej funkcji "
      f"przechodzącej testy. Siła: średnia, bo {a1['kod']['zawsze_zle']} z 30 poleceń nie rozwiązał żaden model i "
      f"kategoria rozróżnia głównie poziom zera. Źródło: kod z otwartych repozytoriów z licencją pozwalającą na trening; "
      f"licencja do sprawdzenia per plik.")
    o(f"3. **Ćwiczenia z odmiany i poprawiania polskich zdań w formie polecenie → odpowiedź.** Luka: język polski, "
      f"poprawność S−B {zz(pj)}, mimo że w teście par minimalnych S ma wynik najwyższy z trzech (sekcja 4, A3). S "
      f"rozpoznaje poprawną formę, ale jej nie produkuje na polecenie. Siła: średnia (24 polecenia). Źródło: materiały "
      f"dydaktyczne i słowniki fleksyjne; licencja do sprawdzenia.")
    o(f"4. **Krótkie dokumenty pytanie–odpowiedź zakończone tokenem końca dokumentu.** Luka: sonda EOS, np. wiedza o "
      f"Polsce log10 p(EOS) S−B {zz(eos)}. Siła: wysoka dla zjawiska w sondzie, nieznana dla generacji bez znacznika "
      f"stopu (to wymaga testu nr 2 niżej). Do sprawdzenia w potoku danych, czy dokumenty treningowe S kończą się EOS.")
    o("5. **Wiedza o Polsce w tekście encyklopedycznym.** Luka: BPB wiedzy o Polsce i wiedzy ogólnej wyższe niż B "
      f"(H3.2, {zz(r2)}). Siła: średnia, bo wzorce są w stylu Claude, a B jest po pełnym treningu. Źródło: polska "
      f"Wikipedia i podobne; licencja do sprawdzenia dla wersji zrzutu.")
    o("")
    o("Nowe testy (każdy zamyka lukę pomiaru, nie modelu):")
    o("")
    o("1. **Matematyka i kod po polsku z n ≥ 100 na kategorię**, bo MDE poprawności przy n = 30 wynosi kilkanaście do "
      "kilkudziesięciu punktów (sekcja 2), a kod ma za dużo pozycji „zawsze źle”: zadania stopniowane od jednego kroku.")
    o("2. **Koniec odpowiedzi bez znacznika stopu w szablonie**: generacja 0-shot z limitem, mierzony EOS, bo obecna "
      "metryka (c) nie odróżnia modeli (sekcja 6, H1.1).")
    o("3. **Ocena sędziów z zamienionymi stronami** tych samych 126 par, żeby zmierzyć wpływ pozycji wprost.")
    o("4. **Kod LFM z EOS bez `<|im_end|>`**: regeneracja 30 poleceń kodu, żeby rozdzielić umiejętność od definicji EOS.")
    o("5. **Polecenia napisane przez człowieka** (choćby 30), żeby zmierzyć, ile różnic BPB wynika ze stylu Claude we "
      "wzorcach.")
    o("")

    # ---------------------------------------------------------------- 9. ograniczenia
    o("## 9. Ograniczenia")
    o("")
    o("- **Checkpoint w toku.** 1.08 to krok serii, która trenuje się dalej; Bielik i LFM są po pełnym treningu. Wnioski "
      "dotyczą checkpointu 1.08.")
    o("- **Udział języków i rozmiar.** Każda różnica w polszczyźnie i angielskim ma wyjaśnienie w składzie danych; B ma "
      "więcej parametrów.")
    o("- **Tokenizery.** BPB na bajt usuwa najprostszy efekt, ale limit tokenów daje różne długości odpowiedzi w bajtach.")
    o("- **Claude jako autor i sędzia.** Polecenia, wzorce, kryteria i obaj sędziowie to Claude; audyt robiłam ja (też "
      "Claude), znając ocenę automatyczną i reguły, więc audyt nie był ślepy.")
    o("- **Niejasności zgłoszone przez sędziów.** Instrukcja sędziego nie rozstrzygała trzech sytuacji: (1) pusta "
      "odpowiedź wobec odpowiedzi słabej, (2) błąd faktów wobec odpowiedzi ogólnikowej bez błędu, (3) odpowiedź nie na "
      "temat wobec drugiej słabej. Sędziowie rozstrzygali je sami, niezależnie od siebie; te pary mogą przesuwać odsetki "
      "wygranych w obie strony, a ich liczby per sędzia nie mierzyłam.")
    o("- **LFM i EOS.** Wynik LFM w kodzie zależy od tego, że `<|im_end|>` (id 7) jest w zbiorze EOS z protokołu.")
    o("- **Szablon.** W wiedzy ogólnej zmiana szablonu przesuwa BPB bardziej niż różnice modeli (sekcja 4, A2).")
    o("- **Mały n i jeden przebieg.** 24–30 poleceń na kategorię, 42 polecenia otwarte; brak przeliczenia na innym sprzęcie.")
    o("- **Trafność zewnętrzna** jest słaba poza matematyką (sekcja 4, A3); wyników nie wolno przenosić na testy wyboru "
      "opcji ani odwrotnie.")
    o("")

    # ---------------------------------------------------------------- 10. odstępstwa i NOT RUN
    o("## 10. Odstępstwa od protokołu i rzeczy niewykonane")
    o("")
    o("Odstępstwa:")
    o("")
    o("- Trzy procesy modeli równolegle (po jednym na model) zamiast jednej kolejki, decyzja orkiestratora w trakcie "
      "przebiegu Slayera; najniższa wolna pamięć 25%, powrotu do kolejki nie było (`wyniki/przebieg.json`). Wynik "
      "modelu nie zależy od procesu obok (osobne procesy i generatory seedów).")
    o("- Batch 4 w generacji (zapisany w protokole jako świadome odstępstwo); greedy batch 4 wobec batch 1: 0 różnic na "
      "10 pozycjach każdego modelu.")
    o("- Audyt oceny automatycznej: 63 oceny zamiast 60, żeby każda z 21 komórek model × kategoria miała po 3.")
    o("- Wrażliwość na 6 reguł oceny i sonda EOS kodu LFM dodane po pomiarze: eksploracyjne.")
    o("- Odsetek wygranych z SE zamiast modelu Bradleya-Terry'ego (protokół przewidywał odsetek wygranych).")
    o("")
    o("NOT RUN:")
    o("")
    o("- A3 dla wiedzy o Polsce, kodu i tekstu technicznego: brak testu dla wszystkich trzech modeli w przebiegu centralnym.")
    o("- Ocena sędziów z zamienionymi stronami (wpływ pozycji mierzony tylko odsetkiem wyborów A i odwrotną kolejnością "
      "par u sędziego 2).")
    o("- Regeneracja kodu LFM bez `<|im_end|>` w zbiorze EOS.")
    o("- Przeliczenie `needs-recheck` na innym sprzęcie.")
    o("")

    # ---------------------------------------------------------------- 11. pliki
    o("## 11. Pliki i odtworzenie")
    o("")
    o("- `code/analiza.py` → `wyniki/LICZBY.json` (wejścia z sha256 w polu `wejscia`); `code/paper.py` → ten plik; "
      "`code/rozmowy.py` → `ROZMOWY.md`; `code/wykresy.py` → `charts/*.svg`.")
    o("- `code/test_niezalezny.py`: przelicza średnie BPB z surowych log p, poprawność i z z ocen pozycji, bez "
      "importu kodu analizy, i porównuje z `LICZBY.json`.")
    o("- Surowe wyniki: `wyniki/surowe/*.jsonl.gz` (sha w `wyniki/SHA256SUMS`); oceny sędziów i kontroli wzorców leżą "
      "poza repo, ich sha256 w `LICZBY.json`.")
    o("")

    return "\n".join(out)


def pliki(liczby, L):
    """Bramka (g) tools/sprawdz_raporty.py: pliki raportu dokładnie takie, jakie generator pisze z LICZBY.json."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import rozmowy
    return {"PAPER.md": tresc(L), "ROZMOWY.md": rozmowy.tresc(L)}


if __name__ == "__main__":
    L = json.loads((BADANIE / "wyniki/LICZBY.json").read_text(encoding="utf-8"))
    for nazwa, t in pliki(None, L).items():
        (BADANIE / nazwa).write_text(t, encoding="utf-8")
        print(nazwa, len(t.splitlines()), "linii")
