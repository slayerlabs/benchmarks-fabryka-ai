# Pomiar: wplyw BOS na Pythie-1B v0 (PROTOKOL.md @ 7f09124)

## Pomiar wazny

KONTROLA T06: 0,709467, po zaokragleniu 0,7095, n = 1838, SE 0,0106. Warunek 0,7095: spelniony. results_sha256 taki jak w manifescie: tak.

Werdykt z protokolu: Wplyw maly: brak wplywu wiekszego niz 0,04 na Pythii na kazdym z 6 testow.

Wynik pod progiem to brak wplywu wiekszego niz 0,04 na Pythii, nie twierdzenie, ze BOS nie ma znaczenia, i nie dowod dla innych modeli.

## Stara i nowa wartosc

| zadanie | wariant | metryka | stara (SE) | nowa (SE) | n | roznica | SE roznicy | z | werdykt z | |d| < 0,04 | baza losowa | baza wiekszosciowa |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T51 | BOS | acc,none | 0,558502 (0,0102) | 0,569024 (0,0102) | 2376 | 0,010522 | 0,0144 | 0,73 | szum | tak | 0,2502 | 0,2664 |
| T05 | BOS | acc_norm,none | 0,467935 (0,0050) | 0,469528 (0,0050) | 10042 | 0,001593 | 0,0070 | 0,23 | szum | tak | 0,2500 | 0,2573 |
| T17 | BOS | acc,none | 0,565690 (0,0069) | 0,560450 (0,0069) | 5153 | -0,005240 | 0,0098 | -0,54 | szum | tak | 0,0000 | 0,0031 |
| T06 | BOS | acc_norm,none | 0,709467 (0,0106) | 0,709467 (0,0106) | 1838 | 0,000000 | 0,0150 | 0,00 | szum | tak | 0,5000 | 0,5049 |
| T07 | BOS | acc,none | 0,544594 (0,0125) | 0,543804 (0,0125) | 1267 | -0,000789 | 0,0177 | -0,04 | szum | tak | 0,5000 | 0,5043 |
| T14 | BOS | acc,none | 0,673993 (0,0211) | 0,681319 (0,0217) | 273 | 0,007326 | 0,0303 | 0,24 | szum | tak | 0,5000 | 0,5018 |
| T03 | OKNO | byte_perplexity,none | 2,423435 (0,0514) | 1,687701 (0,0139) | 62 | -0,735734 | 0,0533 | -13,82 | pewne | nie dotyczy | brak | brak |

SE roznicy: niezalezne, adnotacja „ostrozne”, bo probek starego przebiegu nie ma na tej maszynie.

## T06 w parach (KONTROLA i BOS per pytanie)

n = 1838, srednia roznica BOS minus KONTROLA 0,000000, SE 0,0050, z 0,00, werdykt szum, zmienione decyzje 84.

## ARC-Easy osobno

Slayer 1.07 0,598064 (SE 0,0101) minus nowa Pythia 0,569024 (SE 0,0102): 0,029040, SE 0,0143 (niezalezne, ostrozne), z 2,03, werdykt prawdopodobne. Stara roznica: 0,039562.
Werdykt stoi o wlos: roznica jest nad progiem |z| = 2 o 1,05 trafienia na 2376 pytan, przy SE niezaleznych, nie w parach.

## T03 a Slayer (eksploracyjne, dodane po pomiarze; nizsza perpleksja = lepiej)

Pythia stara 2,423435, nowa (okno 2048) 1,687701, Slayer 1.07 1,781674 (SE 0,0147). Pythia minus Slayer: stara 0,641761, nowa -0,093974, SE 0,0202 (niezalezne, ostrozne), z -4,64, werdykt pewne.
Znak roznicy Pythia minus Slayer jest przeciwny niz przed zmiana okna. Werdykt z dotyczy tylko tej roznicy; protokol nie przewiduje tego porownania ani wniosku z niego. Problemu okna u Slayera w tym pomiarze nie sprawdzono, wiec to nie jest porownanie modeli na rownych warunkach.

## WSC273: metryki poboczne, poza protokolem

bpb_poprawnej: stara 2,123, nowa 2,279, roznica 0,155. Udzial najczestszej predykcji: stary 0,524, nowy 0,568, roznica 0,044.
Protokol nie ustalal tych metryk ani progu, wiec nie wchodza do werdyktu.

## T07 i T14: SE klastrowe (eksploracyjne, dodane po pomiarze)

SE w tabeli wyzej jest klastrowe (metoda K). Obok SE nowej wartosci po pozycjach (stara wartosc z manifestu):
- T07: z po pozycjach -0,042, werdykt szum, w tabeli szum.
- T14: z po pozycjach 0,208, werdykt szum, w tabeli szum.

## KONTROLA-ARC (EuroLLM-1.7B, T02, 25-shot)

acc_norm 0,408703 (SE 0,0144), n = 1172. Odniesienie 0,4061, roznica 0,002603, |roznica| 0,002603, prog 0,0286.

Wynik: warunek liczbowy spelniony, ustawienie referencji nieodtworzone, kontrola nierozstrzygnieta.

Demonstracje w promptach (1172 pytan): 24 demonstracji: 27 pytan, 25 demonstracji: 1145 pytan. Demonstracji spoza splitu test: 0. Slad runnera: zadane 25, pytania_z_mniejsza_liczba 0, srednio 25,00; to pole jest niezgodne z rozkladem policzonym z promptow.
Przyczyna demonstracji z testu, z kodu: konfiguracja T02 w common/zadania.py ustawia tylko test_split, bez training_split, fewshot_split i validation_split, a arc_easy.yaml w lm-eval ma training_split: train. Przy braku tych pol fewshot_docs w lm-eval zwraca test_docs; log KONTROLI-ARC ma ostrzezenie „num_fewshot > 0 but fewshot_split is None. using preconfigured rule.”.
Zrodla demonstracji w Open LLM Leaderboard v1 nie ustalono, wiec ustawienia referencji nie odtworzono. Warunek liczbowy to nie jest potwierdzenie kontroli; prog bez zmian.

## Kontrola BOS (dziennik zadan i wywolan modelu)

| zadanie | zadan w dzienniku | zadan w probkach | zgodne | z jednym BOS | % jeden BOS | wywolan modelu | wywolan z jednym BOS |
|---|---|---|---|---|---|---|---|
| T51 | 19002 | 19002 | tak | 19002 | 100,00 | 14496 | 14496 |
| T05 | 80336 | 80336 | tak | 80336 | 100,00 | 80263 | 80263 |
| T17 | 5153 | 5153 | tak | 5153 | 100,00 | 5151 | 5151 |
| T06 | 7352 | 7352 | tak | 7352 | 100,00 | 7317 | 7317 |
| T07 | 2534 | 2534 | tak | 2534 | 100,00 | 2534 | 2534 |
| T14 | 546 | 546 | tak | 546 | 100,00 | 546 | 546 |

Probki lm-eval nie zapisuja tokenow, wiec liczba wiodacych BOS pochodzi z dziennika bos.jsonl pisanego przy zadaniu i przy wywolaniu modelu; zgodnosc liczby zadan z probkami podana wyzej.

## Srodowisko i odstepstwa

Kod @ fe82b632887857585cc5482741d19b500868698d, lm_eval 0.4.9.1, transformers 4.57.6, torch 2.8.0+cu129, float32, batch 1, NVIDIA GeForce RTX 5090, 32607 MiB, obraz pytorch/pytorch:2.8.0-cuda12.9-cudnn9-runtime, instancja 60052345, host 393738.
runner_sha256 7597c0de7273004dcd099c7e2fb7083b6232e43c17e1822fc291923210d5c1fa to sha sklejonych common/*.py i common/*.sh (sha256_runnera), zgodne z manifestem; sam common/ewaluuj.py ma 94a1bdaacc1673f8c2afb861d871a75d81f6f5b4aac4bd92b0775e39ac2a472d. Protokol podpisuje wartosc runnera jako sha pliku ewaluuj.py, protokolu nie zmieniano.
Wagi: Pythia 92589a02cfd745884f8473b0a975a93cea4cdaacf8333b0c047dab41623396b2, EuroLLM bfe9be53d19031a71d013ded9939747ae8e0c5dd7f07b9173cfa25521d7a9bc8.
Odstepstwo: sterownik karty 580.178.04, w pelnym przebiegu 615.71.09. KONTROLA rozstrzyga o waznosci srodowiska.
Odstepstwo: proba dymna przed wynajmem szla na malutkim modelu GPT-NeoX, nie na Pythii i EuroLLM; oba modele zaladowane na karcie przed kolejka.
Znacznik nowego startu kolejki: 2026-11-10T10:10:41 UTC. Wpisy sprzed znacznika pominiete: 0. Pierwszy start przerwano: logi/kolejka.log ma pusta sciezke wag Pythii i wpis „zaladunek pythia kod 1”.
Metryka acc_norm liczona regula runnera (dlugosc opcji bez spacji wiodacej), jak w manifescie; pole acc_norm z probek lm-eval uzywa innego dzielenia.
T06 BOS w parach: suma zmian zerowa, patrz sekcja par. OKNO T03 nie ma progu w protokole i nie wchodzi do werdyktu wplywu; roznica stara-nowa podana bez wniosku protokolowego, porownanie ze Slayerem jest eksploracyjne (osobna sekcja).
Odstepstwo: protokol wymagal testu mechanizmu BOS przed pomiarem. Uruchomiono go przed wynajmem, ale wynik nie zostal zapisany do pliku, wiec nie ma sladu z kodem wyjscia, a tamta wersja testu nie zapalala sie na mutacjach (BOS na sztywno, BOS z eot, wylaczona kontrola tensora). Test poprawiono po pomiarze; to nie zastepuje testu przed pomiarem.

## Koszt

```
{
 "instancje": [
  "60049161",
  "60049907",
  "60050593",
  "60051430",
  "60052345"
 ],
 "pozycje": [
  {
   "amount": "0.016",
   "description": "Instance 60049161 storage charge: hours * $/hr",
   "instance_id": 60049161,
   "quantity": "0.197",
   "rate": "0.0833",
   "timestamp": 1794268800,
   "type": "charge"
  },
  {
   "amount": "0.007",
   "description": "Instance 60049907 storage charge: hours * $/hr",
   "instance_id": 60049907,
   "quantity": "0.159",
   "rate": "0.0444",
   "timestamp": 1794268800,
   "type": "charge"
  },
  {
   "amount": "0.041",
   "description": "Instance 60050593 GPU  charge:    hours * $/hr",
   "instance_id": 60050593,
   "quantity": "0.076",
   "rate": "0.5333",
   "timestamp": 1794268800,
   "type": "charge"
  },
  {
   "amount": "0.003",
   "description": "Instance 60050593 storage charge: hours * $/hr",
   "instance_id": 60050593,
   "quantity": "0.130",
   "rate": "0.0222",
   "timestamp": 1794268800,
   "type": "charge"
  },
  {
   "amount": "0.046",
   "description": "Instance 60051430 GPU  charge:    hours * $/hr",
   "instance_id": 60051430,
   "quantity": "0.087",
   "rate": "0.5333",
   "timestamp": 1794268800,
   "type": "charge"
  },
  {
   "amount": "0.004",
   "description": "Instance 60051430 storage charge: hours * $/hr",
   "instance_id": 60051430,
   "quantity": "0.172",
   "rate": "0.0222",
   "timestamp": 1794268800,
   "type": "charge"
  },
  {
   "amount": "0.390",
   "description": "Instance 60052345 GPU  charge:    hours * $/hr",
   "instance_id": 60052345,
   "quantity": "0.731",
   "rate": "0.5333",
   "timestamp": 1794268800,
   "type": "charge"
  },
  {
   "amount": "0.017",
   "description": "Instance 60052345 storage charge: hours * $/hr",
   "instance_id": 60052345,
   "quantity": "0.752",
   "rate": "0.0222",
   "timestamp": 1794268800,
   "type": "charge"
  },
  {
   "amount": "0.033",
   "description": "Instance 60052345 download charge",
   "instance_id": 60052345,
   "quantity": "8.290",
   "rate": "0.004",
   "timestamp": 1794268800,
   "type": "charge"
  }
 ],
 "suma_usd": 0.557
}
```
