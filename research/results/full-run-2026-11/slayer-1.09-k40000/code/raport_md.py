"""RAPORT.md z LICZBY.json (jedyne źródło liczb); bez liczb wpisanych ręką.

    python raport_md.py <LICZBY.json> <RAPORT.md>
"""
import json
import sys
from pathlib import Path


def f(x, cyfry=4, plus=False):
    if x is None:
        return "–"
    tekst = f"{abs(x):.{cyfry}f}".replace(".", ",")
    return ("−" if x < 0 and float(tekst.replace(",", ".")) != 0 else ("+" if plus and x > 0 else "")) + tekst


def cyfry(t):
    return 4 if t["wyzej_lepiej"] else 3


def statystyka(p):
    if p.get("t") is not None:
        return f"t = {f(p['t'], 2)}, df = {p['df']}"
    return f"z = {f(p['z'], 2)}" if p.get("z") is not None else "–"


def baza(t):
    czesci = []
    if t.get("chance") is not None:
        czesci.append(f"losowa {f(t['chance'])}")
    if t.get("majority") is not None:
        czesci.append(f"większościowa {f(t['majority'])}")
    return ", ".join(czesci) or "nie dotyczy"


def eksploracja(L: dict, a) -> None:
    """Sekcja analiz po wyniku (LICZBY.json „eksploracyjne”); żadna z nich nie zmienia werdyktów protokołu."""
    E = L["eksploracyjne"]
    nazwy = {t["benchmark"]: t["nazwa"] for t in L["testy"]}
    A_, B_ = L["model"], L["odniesienie"]
    a("## Analizy eksploracyjne (po wyniku)")
    a("")
    a("Dopisane po pierwszym wyniku, na żądanie weryfikacji; nie były ustalone w protokole i nie zmieniają głównego "
      "twierdzenia ani werdyktów tabeli. Werdykty niżej są opisowe, bez korekty na wielokrotne testowanie, chyba że "
      "kolumna mówi inaczej. Ustalone przed pomiarem było tylko to, co stoi w sekcjach wyżej.")
    a("")
    a("### Remisy")
    a("")
    a(f"Reguła (stan runnera, zapisany po wyniku w aneksie protokołu): {E['regula_remisu']}. Remis to pytanie, w którym "
      "najwyższy wynik reguły wyboru ma więcej niż jedna opcja; „z poprawną” to remis obejmujący poprawną opcję "
      "(liczony jako trafienie, gdy poprawna ma najniższy indeks).")
    a("")
    a("| test | n | remisy 1.09 | z poprawną 1.09 | remisy 1.08 | z poprawną 1.08 | pytania ze zdublowaną opcją |")
    a("|---|---:|---:|---:|---:|---:|---:|")
    for b, r in E["remisy"].items():
        x, y = r[A_], r[B_]
        a(f"| {nazwy[b]} | {x['n']} | {x['remisy']} | {x.get('remisy_z_poprawna', '–')} | {y['remisy']} | "
          f"{y.get('remisy_z_poprawna', '–')} | {x.get('pytan_ze_zdublowana_opcja', '–')} |")
    a("")
    for b, d in (E.get("definicja_lm_eval") or {}).items():
        t = next(t for t in L["testy"] if t["benchmark"] == b)
        p = d["porownanie"]
        a(f"### {nazwy[b]}: dwie definicje acc_norm")
        a("")
        a(f"Runner (`metryki.oceny_mc`, definicja pełnego przebiegu i manifestu 1.08) dzieli loglik przez długość "
          f"kontynuacji bez wiodących spacji; lm_eval (pole próbki) przez długość wyboru. Na {nazwy[b]} rozchodzą się na "
          f"{d['pytan_rozne_od_runnera'][A_]} pytaniach 1.09 i {d['pytan_rozne_od_runnera'][B_]} pytaniach 1.08.")
        a("")
        a("| definicja | 1.08 | 1.09 k40000 | Δ | SE Δ | statystyka | werdykt |")
        a("|---|---:|---:|---:|---:|---|---|")
        pt = t["porownanie"]
        a(f"| runner (tabela wyżej) | {f(t['v108_przeliczone']['wartosc'], 6)} | {f(t['v109']['wartosc'], 6)} | "
          f"{f(pt['roznica'], 6, plus=True)} | {f(pt['se'])} | z = {f(pt['z'], 2)} | {pt['werdykt']} |")
        a(f"| lm_eval | {f(d['v108'], 6)} | {f(d['v109'], 6)} | {f(p['roznica'], 6, plus=True)} | {f(p['se'])} | "
          f"z = {f(p['z'], 2)} | {p['werdykt']} |")
        a("")
        taki_sam = p["werdykt_holm"] == pt["werdykt_holm"]
        a(f"Werdykt po Holmie w definicji lm_eval (pełny Holm w rodzinie 15 porównań protokołu, z tym p w miejscu p "
          f"runnera): {p['werdykt_holm']} (p Holma {f(p['p_holm_w_rodzinie'], 4)}); w definicji runnera "
          f"{pt['werdykt_holm']} (p Holma {f(pt['p_holm'], 4)}). "
          + ("Wynik testu się nie zmienia." if taki_sam else "WERDYKT ZALEŻY OD DEFINICJI."))
        a("")
    a("### Rozbicie zadań złożonych")
    a("")
    a("Wartość grupy z przedziałem Walda ±1,96 SE przyciętym do [0; 1]; Δ parowane (z), Holm w obrębie rozbicia "
      "(m = liczba grup). SE każdej grupy liczone z pozycji traktowanych jako niezależne (pary BLiMP i MultiBLiMP-PL, "
      "rekordy EWoK), bez klastrów: w EWoK rekordy jednego szablonu są skorelowane, a porównanie główne liczy SE po "
      "szablonach, więc tu SE jest zaniżone, a werdykty grup za mocne. "
      "<!-- liczba-spoza-wynikow: 1,96 to kwantyl rozkładu normalnego, nie wynik -->")
    a("")
    for b, r in E["rozbicie"].items():
        licz = ", ".join(f"{k}: {v}" for k, v in sorted(r["po_holmie"].items()))
        a(f"<details>\n<summary><b>{nazwy[b]}</b> po polu `{r['pole']}`, k = {r['k']} (po Holmie {licz})</summary>\n")
        a("| grupa | n | 1.08 [CI95] | 1.09 k40000 [CI95] | Δ | SE Δ | z | werdykt | p Holma | po Holmie |")
        a("|---|---:|---:|---:|---:|---:|---|---|---:|---|")
        for g in r["grupy"]:
            p = g["porownanie"]
            ci = lambda v: (f"{f(v['wartosc'])} [{f(v['ci95'][0])}; {f(v['ci95'][1])}]" if v["ci95"] else f(v["wartosc"]))
            a(f"| {g['grupa']} | {g['n']} | {ci(g['v108'])} | {ci(g['v109'])} | {f(p['roznica'], plus=True)} | "
              f"{f(p['se'])} | {('z = ' + f(p['z'], 2)) if p['z'] is not None else '–'} | {p['werdykt']} | "
              f"{f(p['p_holm'])} | {p['po_holmie']} ({p['werdykt_holm']}) |")
        a("\n</details>\n")
    a("### Formaty odpowiedzi i rozkład wyborów")
    a("")
    a("Każdy plik próbek testu (space: format pełnego przebiegu; mc: litera; cloze: treść odpowiedzi). BPB poprawnej "
      "odpowiedzi: niżej = lepiej. Wybory według metryki testu, obok rozkład poprawnych pozycji. SE Δ w tej tabeli jest "
      "parowane po pozycjach bez klastrów, więc dla BLiMP, WinoGrande i WSC273 (protokół: SE po klastrach) werdykt tu "
      "jest za mocny i nie zastępuje tabeli protokołu.")
    a("")
    a("| test | wariant | n | acc 1.08 · 1.09 | acc_norm 1.08 · 1.09 | BPB poprawnej 1.08 · 1.09 | Δ acc (z, werdykt) | Δ acc_norm (z, werdykt) |")
    a("|---|---|---:|---:|---:|---:|---|---|")
    for b, ws in E["formaty"].items():
        for war, w in ws.items():
            x, y = w[B_], w[A_]
            da, dn = w["delta_acc"], w["delta_acc_norm"]
            st = lambda d: f"{f(d['roznica'], plus=True)} (z = {f(d['z'], 2)}, {d['werdykt']})" if d["z"] is not None else "–"
            a(f"| {nazwy[b]} | {war} | {w['n']} | {f(x['acc'])} · {f(y['acc'])} | {f(x['acc_norm'])} · {f(y['acc_norm'])} | "
              f"{f(x['bpb_poprawnej'])} · {f(y['bpb_poprawnej'])} | {st(da)} | {st(dn)} |")
    a("")
    a("| test | wariant | poprawne pozycje | wybrane 1.08 | wybrane 1.09 k40000 |")
    a("|---|---|---|---|---|")
    poz = lambda c: " ".join(f"{k}:{v}" for k, v in c.items())
    for b, ws in E["formaty"].items():
        for war, w in ws.items():
            a(f"| {nazwy[b]} | {war} | {poz(w[A_]['poprawne'])} | {poz(w[B_]['wybrane'])} | {poz(w[A_]['wybrane'])} |")
    a("")
    a("### Wobec bazy (stała odpowiedź albo losowa)")
    a("")
    a("`wobec_b` z plików wyników runnera: b = wyższa z bazy losowej i stałej odpowiedzi; przy stałej odpowiedzi "
      "porównanie parowane z jej wynikami per pytanie.")
    a("")
    a("| test | b | baza | 1.08 − b (statystyka, werdykt) | 1.09 − b (statystyka, werdykt) |")
    a("|---|---:|---|---|---|")
    for b, wb in E["wobec_bazy"].items():
        if not wb:
            continue
        st = lambda d: (f"{f(d['roznica'], plus=True)} ({'t = ' + f(d['t'], 2) + ', df = ' + str(d['df']) if d.get('t') is not None else 'z = ' + f(d['z'], 2)}, {d['werdykt']})")
        a(f"| {nazwy[b]} | {f(wb[A_]['b'])} | {wb[A_]['baza']} | {st(wb[B_])} | {st(wb[A_])} |")
    a("")
    if E.get("wrazliwosc"):
        a("### Wrażliwość werdyktów „prawdopodobne” po Holmie")
        a("")
        for b, w in E["wrazliwosc"].items():
            mc = w["mcnemar"]
            a(f"- {nazwy[b]}: p Holma {f(w['p_holm'])} przy progu {f(w['prog'])}. "
              + (f"Zamiana {w['wygranych_do_szumu']} wygranej 1.09 na remis (najbardziej wpływowej) daje werdykt szum. "
                 if w["wygranych_do_szumu"] else "Do 50 zamienionych wygranych werdykt się nie zmienia. ")
              + f"Test McNemara na pozycjach "
              f"(wygrane 1.09: {mc['wygrane_109']}, wygrane 1.08: {mc['wygrane_108']}): p {f(mc['p'])}, po Holmie w "
              f"rodzinie protokołu (to p w miejscu p testu) {f(mc['p_holm_w_rodzinie'])}, czyli "
              f"{'szum' if mc['p_holm_w_rodzinie'] > w['prog'] else 'ponad próg'}. Werdykt protokołu (SE po parach zdań) "
              "zostaje, ale jest na granicy progu.")
        a("")


def raport(L: dict) -> str:
    out = []
    a = out.append
    s, P = L["podsumowanie"], L["srodowisko"] or {}
    a(f"# Slayer 1B {L['etykieta']}: porównanie z 1.08 na 15 testach")
    a("")
    a("<!-- Plik wygenerowany przez code/raport_md.py z LICZBY.json. Nie edytuj ręcznie. -->")
    a("")
    a(f"Etykieta: **{L['etykieta']}**. Checkpoint w trakcie treningu, kontynuacja 1.08, jeszcze nie wydana wersja; "
      "porównanie nie mówi nic o modelu końcowym 1.09. Protokół: [`PROTOKOL.md`](PROTOKOL.md).")
    a("")
    a("## Główne twierdzenie")
    a("")
    a(s["twierdzenie"])
    a("")
    holm = {t["nazwa"]: t["porownanie"]["werdykt_holm"] for t in L["testy"]}
    a(f"- lepszy: {'; '.join(f'{n} ({holm[n]} po Holmie)' for n in s['lepsze']) or 'żaden'}")
    a(f"- gorszy: {'; '.join(f'{n} ({holm[n]} po Holmie)' for n in s['gorsze']) or 'żaden'}")
    a(f"- szum: {', '.join(s['szum']) or 'żaden'}")
    a(f"- nierozstrzygnięty: {', '.join(s['nierozstrzygniete']) or 'żaden'}")
    a("")
    a(f"Obalenie: {s['obalenie']}. „Szum” znaczy różnicę poniżej progu, nie brak różnicy.")
    a("")
    a("## Tabela")
    a("")
    a(f"Δ = 1.09 k40000 − 1.08 przeliczone na tej samej karcie, na tych samych pytaniach. SE Δ parowane po pytaniach (z) "
      "albo po klastrach testu (t, df = k − 1): BLiMP po paradygmatach, WinoGrande po parach zdań, WSC273 po schematach, "
      "EWoK po szablonach. WikiText-2: Δ w byte perplexity (niżej = lepiej), SE i statystyka na bits per byte z dokumentem "
      f"jako klastrem. Werdykt: |z| ≥ 3 pewne, 2–3 prawdopodobne, < 2 szum; t przez p. Holm: m = {L['m_holm']}. Kolumna "
      "1.08 to wartość z `manifest.jsonl` przebiegu.")
    a("")
    a("| test | n | 1.08 (manifest) ± SE | 1.09 k40000 ± SE | Δ | SE Δ | statystyka | werdykt | p Holma | po Holmie | wynik |")
    a("|---|---:|---:|---:|---:|---:|---|---|---:|---|---|")
    for t in L["testy"]:
        p, c = t["porownanie"], cyfry(t)
        se = f(p["se"], 4) + (" bpb" if t["benchmark"] == "wikitext-2" else "")
        a(f"| {t['nazwa']} | {t['v109']['n']} | {f(t['v108_manifest']['wartosc'], c)} ± {f(t['v108_manifest']['se'])} | "
          f"{f(t['v109']['wartosc'], c)} ± {f(t['v109']['se'])} | {f(p['roznica'], c, plus=True)} | {se} | {statystyka(p)} | "
          f"{p['werdykt']} | {f(p['p_holm'], 4)} | {p['po_holmie']} ({p['werdykt_holm']}) | {t['werdykt_koncowy']} |")
    a("")
    a("## Kontrola narzędzia")
    a("")
    a("1.08 przeliczone tu wobec 1.08 z `manifest.jsonl` przebiegu (karta RTX 5090). Zgodna: to samo n i "
      f"|różnica| ≤ {f(L['testy'][0]['kontrola']['prog_se'], 1)} SE testu z manifestu.")
    a("")
    a("| test | 1.08 manifest | 1.08 przeliczone | różnica | w SE | n równe | kontrola |")
    a("|---|---:|---:|---:|---:|---|---|")
    for t in L["testy"]:
        k, c = t["kontrola"], cyfry(t)
        a(f"| {t['nazwa']} | {f(t['v108_manifest']['wartosc'], 6)} | {f(t['v108_przeliczone']['wartosc'], 6)} | "
          f"{f(k['roznica'], 6, plus=True)} | {f(k['w_se'], 2, plus=True)} | {'tak' if k['n_zgodne'] else 'nie'} | "
          f"{'zgodna' if k['zgodna'] else 'NIEZGODNA'} |")
    a("")
    if s["kontrole_niezgodne"]:
        a(f"Niezgodne: {', '.join(s['kontrole_niezgodne'])}. Inna karta niż w przebiegu (RTX 5090) to możliwe źródło różnicy.")
        a("")
    a("## Bazy i kontrola sensu")
    a("")
    a("| test | metryka | bazy | 1.08 przeliczone ± SE | kontrola sensu 1.09 | kontrola sensu 1.08 |")
    a("|---|---|---|---:|---|---|")
    for t in L["testy"]:
        ks = t["kontrola_sensu"]
        a(f"| {t['nazwa']} | {t['metryka']} | {baza(t)} | {f(t['v108_przeliczone']['wartosc'], cyfry(t))} ± "
          f"{f(t['v108_przeliczone']['se'])} | {'; '.join(ks[L['model']]) or 'ok'} | {'; '.join(ks[L['odniesienie']]) or 'ok'} |")
    a("")
    if L.get("eksploracyjne"):
        eksploracja(L, a)
    a("## Środowisko")
    a("")
    for k in sorted(P):
        a(f"- {k}: {P[k]}")
    a("")
    if L.get("najem"):
        a("## Karta")
        a("")
        for k in sorted(L["najem"]):
            a(f"- {k}: {L['najem'][k]}")
        a("")
    if L.get("odstepstwa"):
        a("## Odstępstwa od protokołu")
        a("")
        for x in L["odstepstwa"]:
            a(f"- {x}")
        a("")
    if L.get("problemy"):
        a("## Problemy poza tym pomiarem")
        a("")
        for x in L["problemy"]:
            a(f"- {x}")
        a("")
    if L.get("not_run"):
        a("## Niepoliczone (NOT RUN)")
        a("")
        for x in L["not_run"]:
            a(f"- {x}")
        a("")
    a("## Pliki")
    a("")
    w = L["wejscia"]
    a(f"- surowe wyniki: paczka eksportu `{(w.get('paczka') or {}).get('nazwa')}` (sha256 "
      f"`{(w.get('paczka') or {}).get('sha256')}`); jej pliki leżą w repo (próbki, trace i podsumowania jako gzip), sumy "
      f"każdego pliku przed kompresją i po niej w [`probki_sha256.json`](probki_sha256.json) (sha256 `{w['probki_sha256']}`)")
    a(f"- `manifest.jsonl` przebiegu: sha256 `{w['manifest_przebiegu']}`")
    a("- `wyniki/<test>/slayer1b-1.08/`: 1.08 przeliczone; 1.09 w `../<test>/slayer1b-1.09-k40000/`; `eksport/`: "
      "manifest, środowisko i czasy z instancji; `logi/`: logi par")
    a("- `code/`: konwersja i sprawdzenie architektury, kolejka na instancji, `dolacz_wyniki.py`, `liczby_109.py`, "
      "`raport_md.py`, `przelicz_niezaleznie.py`, `sprawdz_raport.py`, `mutacje.py`")
    a("- odtworzenie każdej liczby z plików repo: [`ODTWORZENIE.md`](ODTWORZENIE.md)")
    a("")
    return "\n".join(out)


def main():
    L = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    Path(sys.argv[2]).write_text(raport(L), encoding="utf-8")


if __name__ == "__main__":
    main()
