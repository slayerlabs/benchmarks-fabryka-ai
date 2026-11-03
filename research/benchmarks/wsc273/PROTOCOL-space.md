# Protokół: WSC273 dla Slayera 1.06 (T14) i kontrola

Ustalony przed jakimkolwiek liczeniem modelu. Korekty po wyniku trafiają do osobnej sekcji na końcu pliku.

**Pytanie.** Jaki jest wynik Slayera 1.06 na T14 (WSC273) według `METHOD.md` Space, na zamrożonej próbce i na pełnym
splicie, i czy nasz kod odtwarza opublikowaną wartość modelu kontrolnego?

**Dane.**
- Zbiór: `ErnestSDavis/winograd_wsc` @ `8052c534a4cecd8328c0bc879f6a5aa07404c4da` (rewizja z `tasks_50.json`).
  Bajty: `wsc273/test/0000.parquet` z `refs/convert/parquet` @ `24cdebf4993560f25ff220b171e40f1027f3d9e6`, bo
  skrypt ładujący nie działa w `datasets` 3.6.0. Plik ma 273 wiersze. <!-- liczba-spoza-wynikow: rozmiar splitu z karty zadania -->
- Zadanie: katalog `lm_eval_tasks/wsc273/`. `utils.py` to bajt w bajt plik lm-eval. `wsc273.yaml` różni się od
  `default.yaml` tylko źródłem danych. Test pilnuje obu warunków.
- Model: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`. <!-- liczba-spoza-wynikow: nazwa modelu -->
- Kontrola: `bigscience/bloom-560m` @ `ac2ae5fab2ce3f9f40dc79b5ca9f637430d24971`. <!-- liczba-spoza-wynikow: nazwa modelu -->

**Tożsamość dokumentu.** WSC273 nie ma natywnego id, a `METHOD.md` nie publikuje postaci kanonicznej. Wariant główny:
SHA-256 z `json.dumps(doc, sort_keys=True, ensure_ascii=False)` dla dokumentu po `process_docs`. Dokumenty identyczne
bajtowo dostałyby ordinal i wspólny klaster bootstrapu, ale w tym zbiorze ich nie ma.

**Próbka.** `min(200, N)` dokumentów według `common/metryki.ranking_panel("wsc273", "wsc273", id)`. Lista trafia do <!-- liczba-spoza-wynikow: rozmiar próbki z METHOD -->
`panel200.json` przed pierwszym uruchomieniem modelu.

**Wzory.** Wartość to średnia `acc`, SE z ddof=1, CI95 z bootstrapu (10 000 powtórzeń, seed 20261028). Bazy według <!-- liczba-spoza-wynikow: parametry bootstrapu z METHOD -->
`METODOLOGIA`, sekcja „Bazy: losowa i większościowa”: losowa, większościowa ze splitu i z próbki, udział najczęstszej
predykcji i flaga stałej predykcji. Model liczy osobny przebieg próbki i osobny przebieg pełnego splitu. Wynik próbki
ma być podzbiorem przebiegu pełnego.

**Warunek potwierdzenia kontroli.** Opublikowana wartość `bigscience/bloom-560m` to 0,66667 przy SE 0,02858, n = 273 <!-- liczba-spoza-wynikow: plik wyników lm-eval, afbf8e66, wartość opublikowana -->
([plik wyników lm-eval](https://github.com/EleutherAI/lm-evaluation-harness/blob/afbf8e6639c86490cc086eb949eac89b55ce58ab/results/bloom/bloom-560m/bloom-560m_common_sense_reasoning_0-shot.json)). <!-- liczba-spoza-wynikow: nazwa modelu i pliku w adresie URL -->
Dwa SE przekraczają 2 pkt, więc wynik kontroli na pełnych 273 dokumentach ma leżeć w [0,6095; 0,7238]. <!-- liczba-spoza-wynikow: próg protokołu ustalony przed pomiarem -->

**Warunek obalenia.** Wynik poza tym przedziałem zatrzymuje pracę i idzie do komentarza w zadaniu. Slayera wtedy nie
raportujemy. Obala też sprzeczność między przebiegiem próbki a podzbiorem przebiegu pełnego (inne `acc` albo logliki
różne o ponad 1e-3) oraz obcięcie kontekstu w którymkolwiek żądaniu. <!-- liczba-spoza-wynikow: próg protokołu ustalony przed pomiarem -->

**Kontrola wrażliwości.** Tożsamość dokumentu ma dwa inne rozsądne warianty: indeks wiersza i dokument przed
`process_docs`. Każdy daje inną próbkę. Wynik Slayera liczę na obu jako podzbiory przebiegu pełnego i podaję obok.
Space może używać innej postaci kanonicznej, więc opis PR podaje rozstęp tych wariantów.

## Korekty po wyniku

Dopisane 2026-11-02, po pomiarze i po recenzji zewnętrznej. Tekst powyżej zostaje bez zmian.

- **Kolejność.** Protokół, próbka i wyniki weszły do repo jednym commitem, więc historia gita nie potwierdza, że
  protokół powstał przed pomiarem.
- **SE wobec bazy większościowej.** Pierwszy raport porównywał z nią trafność przy SE samej trafności. Oba predyktory
  odpowiadają na te same pytania, więc obowiązuje SE parowane (`research/README.md`). Werdykty na obu próbkach zmieniły
  się z „prawdopodobne” na „szum”.
- **Kontrola wrażliwości.** Po wyniku doszły warianty bez `sort_keys`, wariant pól treści, 63 podzbiory pól i SD
  losowania 200 z 273 dokumentów. Rozstęp nazwanych wariantów to teraz 4,5 pkt zamiast 4,0 pkt. <!-- liczba-spoza-wynikow: rozstępy z results/wsc273.json przed korektą i po niej -->
- **Status kontroli.** Źródło kontroli jest spoza listy `METODOLOGIA.md`. Próg się nie zmienia, ale wynik Slayera jest
  wstępny, a kontrola nie jest nazywana spełnioną (`REPRODUCTION.md`).
- **BOS.** Ustalono po pomiarze z plików tokenizerów i kodu, bo przebiegi go nie zapisały (`RECIPE.md`).
