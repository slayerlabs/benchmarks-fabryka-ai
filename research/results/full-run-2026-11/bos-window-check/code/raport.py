"""RAPORT.md wylacznie z LICZBY.json. python raport.py <LICZBY.json> <RAPORT.md>"""
import json
import sys
from pathlib import Path

L = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
SZ = L["testy_wariantu_bos"]


def f(x, n=4):
    return "brak" if x is None else f"{x:.{n}f}".replace(".", ",")


w = ["# Pomiar: wplyw BOS na Pythie-1B v0 (PROTOKOL.md @ " + L["protokol_commit"] + ")", ""]
k = L["kontrola"]
w += ["## Pomiar wazny", ""]
if k:
    w.append(f"KONTROLA T06: {f(k['value'], 6)}, po zaokragleniu {f(k['zaokraglone_4'])}, n = {k['n']}, SE {f(k['se'])}. "
             f"Warunek 0,7095: {'spelniony' if L['pomiar_wazny'] else 'NIESPELNIONY'}. "
             f"results_sha256 taki jak w manifescie: {'tak' if k['results_sha_taki_jak_w_manifescie'] else 'nie'}.")
else:
    w.append("KONTROLA T06: brak wyniku.")
w += ["", f"Werdykt z protokolu: {L['wplyw_tekst']}", "",
      "Wynik pod progiem to brak wplywu wiekszego niz 0,04 na Pythii, nie twierdzenie, ze BOS nie ma znaczenia, i nie dowod dla innych modeli.", "",
      "## Stara i nowa wartosc", "",
      "| zadanie | wariant | metryka | stara (SE) | nowa (SE) | n | roznica | SE roznicy | z | werdykt z | |d| < 0,04 | baza losowa | baza wiekszosciowa |",
      "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for t in SZ + ["T03"]:
    p = L["pary"][t]
    if p.get("nowa") is None:
        w.append(f"| {t} | {p['wariant']} | {p['metryka']} | {f(p['stara'], 6)} | brak ({p['stan']}) | | | | | | | | |")
        continue
    prog = ("tak" if p["ponizej_progu_0_04"] else "NIE") if t in SZ else "nie dotyczy"
    w.append(f"| {t} | {p['wariant']} | {p['metryka']} | {f(p['stara'], 6)} ({f(p['se_stara'])}) | {f(p['nowa'], 6)} ({f(p['se_nowa'])}) | "
             f"{p['n_nowa']} | {f(p['roznica'], 6)} | {f(p['se_roznicy'])} | {f(p['z'], 2)} | {p['werdykt_z']} | {prog} | {f(p['baza_losowa'])} | {f(p['baza_wiekszosciowa'])} |")
w += ["", "SE roznicy: niezalezne, adnotacja „ostrozne”, bo probek starego przebiegu nie ma na tej maszynie.", ""]
p6 = L["pary"]["T06"].get("w_parach")
if p6:
    w += ["## T06 w parach (KONTROLA i BOS per pytanie)", "",
          f"n = {p6['n']}, srednia roznica BOS minus KONTROLA {f(p6['srednia_roznica_bos_minus_kontrola'], 6)}, SE {f(p6['se'])}, z {f(p6['z'], 2)}, "
          f"werdykt {p6['werdykt_z']}, zmienione decyzje {p6['zmienione_pytania']}.", ""]
a = L.get("arc_easy")
if a:
    w += ["## ARC-Easy osobno", "",
          f"Slayer 1.07 {f(a['slayer_1_07'], 6)} (SE {f(a['se_slayer'])}) minus nowa Pythia {f(a['pythia_nowa'], 6)} (SE {f(a['se_pythia_nowa'])}): "
          f"{f(a['roznica'], 6)}, SE {f(a['se_roznicy'])} (niezalezne, ostrozne), z {f(a['z'], 2)}, werdykt {a['werdykt_z']}. Stara roznica: {f(a['stara_roznica'], 6)}.",
          f"Werdykt stoi o wlos: roznica jest nad progiem |z| = 2 o {f(a['trafien_nad_progiem_z_2'], 2)} trafienia na {L['pary']['T51']['n_nowa']} pytan, przy SE niezaleznych, nie w parach.", ""]
t3 = L.get("t03_slayer")
if t3:
    w += ["## T03 a Slayer (eksploracyjne, dodane po pomiarze; nizsza perpleksja = lepiej)", "",
          f"Pythia stara {f(t3['pythia_stara'], 6)}, nowa (okno 2048) {f(t3['pythia_nowa'], 6)}, Slayer 1.07 {f(t3['slayer_1_07'], 6)} (SE {f(t3['se_slayer'])}). "
          f"Pythia minus Slayer: stara {f(t3['stara_roznica_pythia_minus_slayer'], 6)}, nowa {f(t3['nowa_roznica_pythia_minus_slayer'], 6)}, SE {f(t3['se_nowej_roznicy'])} (niezalezne, ostrozne), z {f(t3['z'], 2)}, werdykt {t3['werdykt_z']}.",
          "Znak roznicy Pythia minus Slayer jest przeciwny niz przed zmiana okna. Werdykt z dotyczy tylko tej roznicy; protokol nie przewiduje tego porownania ani wniosku z niego. Problemu okna u Slayera w tym pomiarze nie sprawdzono, wiec to nie jest porownanie modeli na rownych warunkach.", ""]
pob = L.get("wsc273_poboczne_poza_protokolem")
if pob:
    w += ["## WSC273: metryki poboczne, poza protokolem", "",
          f"bpb_poprawnej: stara {f(pob['stare']['bpb_poprawnej'], 3)}, nowa {f(pob['nowe']['bpb_poprawnej'], 3)}, roznica {f(pob['roznica']['bpb_poprawnej'], 3)}. "
          f"Udzial najczestszej predykcji: stary {f(pob['stare']['udzial_najczestszej_predykcji'], 3)}, nowy {f(pob['nowe']['udzial_najczestszej_predykcji'], 3)}, roznica {f(pob['roznica']['udzial_najczestszej_predykcji'], 3)}.",
          "Protokol nie ustalal tych metryk ani progu, wiec nie wchodza do werdyktu.", ""]
kl = [(t, L["pary"][t].get("se_klastrowe")) for t in ("T07", "T14")]
if all(x for _, x in kl):
    w += ["## T07 i T14: SE klastrowe (eksploracyjne, dodane po pomiarze)", "",
          "SE w tabeli wyzej jest klastrowe (metoda K). Obok SE nowej wartosci po pozycjach (stara wartosc z manifestu):"]
    for t, x in kl:
        w.append(f"- {t}: z po pozycjach {f(x['z_po_pozycjach'], 3)}, werdykt {x['werdykt_po_pozycjach']}, w tabeli {L['pary'][t]['werdykt_z']}.")
    w.append("")
c = L.get("kontrola_arc")
w += ["## KONTROLA-ARC (EuroLLM-1.7B, T02, 25-shot)", ""]
if c:
    d = c["demonstracje"]
    sl = c["slad_runnera_demonstracje"]
    rozklad = ", ".join(f"{k} demonstracji: {v} pytan" for k, v in d["rozklad_liczby_demonstracji"].items())
    w += [f"acc_norm {f(c['value'], 6)} (SE {f(c['se'])}), n = {c['n']}. Odniesienie {f(c['odniesienie'])}, roznica {f(c['roznica'], 6)}, "
          f"|roznica| {f(c['abs_roznica'], 6)}, prog {f(c['prog'])}.", "",
          f"Wynik: {c['werdykt_kontroli']}.", "",
          f"Demonstracje w promptach ({d['pytan']} pytan): {rozklad}. Demonstracji spoza splitu test: {d['demonstracje_spoza_testu']}. "
          f"Slad runnera: zadane {sl['zadane']}, pytania_z_mniejsza_liczba {sl['pytania_z_mniejsza_liczba']}, srednio {f(sl['srednio_przykladow'], 2)}; to pole jest niezgodne z rozkladem policzonym z promptow.",
          "Przyczyna demonstracji z testu, z kodu: konfiguracja T02 w common/zadania.py ustawia tylko test_split, bez training_split, fewshot_split i validation_split, a arc_easy.yaml w lm-eval ma training_split: train. Przy braku tych pol fewshot_docs w lm-eval zwraca test_docs; log KONTROLI-ARC ma ostrzezenie „num_fewshot > 0 but fewshot_split is None. using preconfigured rule.”.",
          "Zrodla demonstracji w Open LLM Leaderboard v1 nie ustalono, wiec ustawienia referencji nie odtworzono. Warunek liczbowy to nie jest potwierdzenie kontroli; prog bez zmian.", ""]
else:
    w += ["Brak wyniku.", ""]
w += ["## Kontrola BOS (dziennik zadan i wywolan modelu)", "",
      "| zadanie | zadan w dzienniku | zadan w probkach | zgodne | z jednym BOS | % jeden BOS | wywolan modelu | wywolan z jednym BOS |",
      "|---|---|---|---|---|---|---|---|"]
for t in SZ:
    b = L["pary"][t].get("kontrola_bos")
    if b:
        w.append(f"| {t} | {b['zadan_w_dzienniku']} | {b['zadan_w_probkach']} | {'tak' if b['zgodne'] else 'NIE'} | {b['zadan_z_jednym_bos']} | {f(b['procent_jeden_bos'], 2)} | {b['wywolan_modelu']} | {b['wywolan_z_jednym_bos']} |")
    else:
        w.append(f"| {t} | brak | | | | | | |")
w += ["", "Probki lm-eval nie zapisuja tokenow, wiec liczba wiodacych BOS pochodzi z dziennika bos.jsonl pisanego przy zadaniu i przy wywolaniu modelu; zgodnosc liczby zadan z probkami podana wyzej.", ""]
s = L["srodowisko"]
w += ["## Srodowisko i odstepstwa", "",
      f"Kod @ {s['commit_kodu']}, lm_eval {s['lm_eval']}, transformers {s['transformers']}, torch {s['torch']}, {s['precyzja']}, batch {s['batch']}, {s['karta']}, obraz {s['obraz']}, instancja {s['instancja']}, host {s['host']}.",
      f"runner_sha256 {s['runner_sha256']} to sha sklejonych common/*.py i common/*.sh (sha256_runnera), zgodne z manifestem; sam common/ewaluuj.py ma {s['ewaluuj_py_sha256']}. Protokol podpisuje wartosc runnera jako sha pliku ewaluuj.py, protokolu nie zmieniano.",
      f"Wagi: Pythia {s['wagi_pythia_sha256']}, EuroLLM {s['wagi_eurollm_sha256']}.",
      f"Odstepstwo: sterownik karty {s['sterownik']}, w pelnym przebiegu {s['sterownik_pelnego_przebiegu']}. KONTROLA rozstrzyga o waznosci srodowiska.",
      "Odstepstwo: proba dymna przed wynajmem szla na malutkim modelu GPT-NeoX, nie na Pythii i EuroLLM; oba modele zaladowane na karcie przed kolejka.",
      f"Znacznik nowego startu kolejki: {L['znacznik_nowego_startu']} UTC. Wpisy sprzed znacznika pominiete: {L['wpisy_kolejki']['przed_znacznikiem_pominiete']}. Pierwszy start przerwano: logi/kolejka.log ma pusta sciezke wag Pythii i wpis „zaladunek pythia kod 1”.",
      "Metryka acc_norm liczona regula runnera (dlugosc opcji bez spacji wiodacej), jak w manifescie; pole acc_norm z probek lm-eval uzywa innego dzielenia.",
      "T06 BOS w parach: suma zmian zerowa, patrz sekcja par. OKNO T03 nie ma progu w protokole i nie wchodzi do werdyktu wplywu; roznica stara-nowa podana bez wniosku protokolowego, porownanie ze Slayerem jest eksploracyjne (osobna sekcja).",
      "Odstepstwo: protokol wymagal testu mechanizmu BOS przed pomiarem. Uruchomiono go przed wynajmem, ale wynik nie zostal zapisany do pliku, wiec nie ma sladu z kodem wyjscia, a tamta wersja testu nie zapalala sie na mutacjach (BOS na sztywno, BOS z eot, wylaczona kontrola tensora). Test poprawiono po pomiarze; to nie zastepuje testu przed pomiarem.", ""]
if L.get("koszt"):
    w += ["## Koszt", "", "```", json.dumps(L["koszt"], ensure_ascii=False, indent=1), "```", ""]
Path(sys.argv[2]).write_text("\n".join(w), encoding="utf-8")
