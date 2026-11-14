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


def raport(L: dict) -> str:
    out = []
    a = out.append
    s, P = L["podsumowanie"], L["srodowisko"] or {}
    a(f"# Slayer 1B {L['etykieta']}: porównanie z 1.08 na 15 testach")
    a("")
    a("<!-- Plik wygenerowany przez code/raport_md.py z LICZBY.json. Nie edytuj ręcznie. -->")
    a("")
    a(f"Etykieta: **{L['etykieta']}**. Checkpoint w trakcie treningu, nie wersja przyjęta i nie następca 1.08; "
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
