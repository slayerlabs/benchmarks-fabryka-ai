# Metodologia: zbiór danych do treningu Slayera 1B

<a href="DANE_TRENINGOWE.md"><img src="img/dane-treningowe.svg" alt="Dane treningowe" height="36"></a>
<a href="REJESTR_DATASETOW.md"><img src="img/rejestr.svg" alt="Rejestr zbiorów" height="36"></a>
<a href="https://github.com/LoIlita/slayer-lab/tree/dane/dclm-en/dane/dclm-en"><img src="img/przyklad-dclm.svg" alt="Przykład: DCLM-EN" height="36"></a>

Jeden przepis dla każdego zbioru, od rezerwacji do wiersza w [`DANE_TRENINGOWE.md`](DANE_TRENINGOWE.md). Format eksportu i docelowa wysyłka: [`SlayerLab/dataset-team-submissions`](https://huggingface.co/datasets/SlayerLab/dataset-team-submissions) (`README.md`, `AGENTS.md`, `LESSONS.md`, skill `source-rights-review`).

## 0. Co zostawia każdy zbiór

Pracujesz w swoim repo, w katalogu `dane/<zbiór>/`, i zostawiasz tam te pliki:

| plik | co w nim | przykład |
|---|---|---|
| `KARTA_ZRODLA.md` | 6 pól z kroku 2 | [`dclm-en/KARTA_ZRODLA.md`](https://github.com/LoIlita/slayer-lab/blob/dane/dclm-en/dane/dclm-en/KARTA_ZRODLA.md) |
| `skrypty/preregistracja.json` | progi i kolejność powodów z kroku 3, aneksy z datą | [`dclm-en/skrypty/preregistracja.json`](https://github.com/LoIlita/slayer-lab/blob/dane/dclm-en/dane/dclm-en/skrypty/preregistracja.json) |
| `skrypty/odtworz.sh` | każdy krok jako przypadek | [`dclm-en/skrypty/odtworz.sh`](https://github.com/LoIlita/slayer-lab/blob/dane/dclm-en/dane/dclm-en/skrypty/odtworz.sh) |
| `requirements.txt` | wynik `pip freeze` | [`dclm-en/requirements.txt`](https://github.com/LoIlita/slayer-lab/blob/dane/dclm-en/dane/dclm-en/requirements.txt) |
| `wyniki/*.json` | liczby kontrolne kroków 5-8 | [`dclm-en/wyniki/`](https://github.com/LoIlita/slayer-lab/blob/dane/dclm-en/dane/dclm-en/wyniki/) |
| `DZIENNIK.md` | sekcja na każdy krok 1-12: data, komenda, kod wyjścia, liczby, link do `wyniki/`; aneksy i przeglądy próbki jako podsekcje; na końcu „Historia odtworzeń” | [`dclm-en/DZIENNIK.md`](https://github.com/LoIlita/slayer-lab/blob/dane/dclm-en/dane/dclm-en/DZIENNIK.md) |

## 1. Zasady stałe

- Zbiór = katalog `dane/<zbiór>/`. Pliki robocze w `dane/<zbiór>/robocze/` (w `.gitignore`).
- Każdy krok to przypadek w `dane/<zbiór>/skrypty/odtworz.sh <krok>`, log w `robocze/logi/<krok>.log`. Wzór skryptu: [`dclm-en/skrypty/odtworz.sh`](https://github.com/LoIlita/slayer-lab/blob/dane/dclm-en/dane/dclm-en/skrypty/odtworz.sh).
- Długi krok: `nohup nice -n 10 bash dane/<zbiór>/skrypty/odtworz.sh <krok> > robocze/logi/<krok>.log 2>&1 &`, przy obciążonej maszynie pod strażnikiem pamięci ([`dclm-en/skrypty/straznik.sh`](https://github.com/LoIlita/slayer-lab/blob/dane/dclm-en/dane/dclm-en/skrypty/straznik.sh)).
- `odtworz.sh` zmieniasz tylko wtedy, gdy żaden krok go nie wykonuje.
- Wynik = kod wyjścia i liczby kontrolne. BLOCKED i NOT RUN to nie PASS i blokują publikację.
- Wadliwy dokument wyrzucasz w całości.
- Tokeny w wynikach liczysz tokenizerem v6 (słownik 32 768). Wyjątek: `token_count` w eksporcie to cl100k, bo tego wymaga `check.py`.
- Po każdym dniu pracy commit wszystkiego z `dane/<zbiór>/` poza `robocze/`.

## 2. Dwie bramki praw

| bramka | przechodzi, gdy | źródło reguły |
|---|---|---|
| można TRENOWAĆ | licencja tekstów albo wyjątek TDM (art. 4 dyr. 2019/790) z opisaną ścieżką takedown; opt-out TDM to uwaga, nie weto | notatka `komplet-kontroli-zbioru` §3 |
| można ZGŁOSIĆ | licencja per dokument, bez NC/ND i opt-outu TDM; licencja kompilacji ≠ licencja tekstów; niesprawdzone = nieprzyjęte | `AGENTS.md`, `LESSONS.md` reguła 5 |

## 3. Kroki

| nr | krok | co robisz | gotowe, gdy |
|---|---|---|---|
| 1 | Rezerwacja | na tablicy [Dataset team](https://github.com/orgs/slayerlabs/projects/11) sprawdzasz, czy nikt nie ma już tego źródła, i dodajesz kartę („Add item”): nazwa zbioru, cel (testy, tokeny v6), źródło; ustawiasz siebie w Assignees i Status „In progress”; wiersz „w budowie” w sekcji „Dopisane później” [`DANE_TRENINGOWE.md`](DANE_TRENINGOWE.md) | karta na tablicy z Tobą, wiersz jest |
| 2 | Karta źródła | `KARTA_ZRODLA.md` PRZED pobraniem: identyfikacja, prawa, zawartość, skala, ryzyka, nowość; każde twierdzenie V (sprawdzone: data, URL, hash) albo I (wywnioskowane); lista „nie sprawdzone” | 6 pól, obie bramki praw z wynikiem albo NIEROZSTRZYGNIĘTY |
| 3 | Preregistracja | `skrypty/preregistracja.json` PRZED próbką: rewizja źródła, seed, tokenizer, kolejność powodów odrzucenia, progi, kontrole dodatnie, ręczna próbka | commit starszy niż pierwszy wynik; każda późniejsza zmiana jako aneks z datą i powodem |
| 4 | Środowisko | venv w `robocze/venv`, wersje w `requirements.txt`: `odtworz.sh venv` | `pip freeze` = `requirements.txt` |
| 5 | Pobranie | tokenizer, próbka, testy, bazy do dedupu, każde z rewizją i sha256 | sumy i liczby wierszy zgodne z rejestrem; zła suma przerywa skrypt |
| 6 | Indeksy i kontrole | indeksy 13-gramów testów, poprzednich danych modelu, walidacji; kontrola dodatnia: wstawiasz znane PII, kawałki testów, kopie | każdy wstawiony dokument dostaje swój powód; kontrola po KAŻDEJ odbudowie indeksów |
| 7 | Przebieg | detektory na każdym dokumencie, wynik per jednostka, wznawialny | log kończy `KONIEC`, zero niedokończonych jednostek |
| 8 | Po przebiegu | pomiary (nakładanie, jakość), dedup, kaskada powodów, uzysk v6, szacunek skali, ręczna próbka oceniona przez niezależnego czytelnika | kod 0; suma kaskady = dokumenty próbki; próbka PRZESZŁO wg progów z kroku 3 |
| 9 | Eksport | w klonie `dataset-team-submissions`: `src/clean_<key>.py` z `shard.write(key, rows)` (maskuje PII, bramka języka, dedup Dynaword) i datasheet `data/<key>/<key>.md` z karty | `data/<key>/<key>.parquet`, `.stats.json`, `.md`; 12 kolumn |
| 10 | Kontrola końcowa | wpis w `src/sources.py`, `configs` w `README.md`, test kontraktowy; `pytest src/test_<key>_contract.py` i `python src/check.py --source <key>` | oba kod 0; niezależny agent na pliku o tym samym sha256 |
| 11 | Wysyłka | chwilowo: własne repo do wglądu Arka (sekcja 4); docelowo PR do `dataset-team-submissions` z przeglądem praw i osobą zatwierdzającą | Arek ma link i dostęp |
| 12 | Dane treningowe | PR zmieniający wiersz z kroku 1 w `DANE_TRENINGOWE.md`: po kroku 11 status „u Arka do wglądu” i link do Twojego repo; po zwykłej wysyłce link do zbioru i status „opublikowany” | każdy link w wierszu odpowiada 200 |

### Szczegóły kroków 2, 9-11

**Karta → datasheet `data/<key>/<key>.md` (krok 9):** identyfikacja, zawartość, skala → `## Source`; prawa → `## Rights review`; ryzyka (kopie, testy, OCR, syntetyki) i nowość → `## Cleaning` z kaskadą i uzyskiem z kroku 8; PII → `## Personal data`; ręczna próbka → `## Sample`.

**Kolumny eksportu (krok 9):** `id`, `text`, `source`, `added`, `created`, `token_count`, `license`, `author`, `language` (`pl`/`en`/`pl+en`), `text_origin` (`human`/`translated`/`synthetic`), `generator`, `derived_from`. `source`, `added`, `token_count` dopisuje `shard.write`. `text_origin=synthetic` wymaga `generator` w formacie `model@rewizja prompt:ścieżka`. Wyniki w `stats.json`: `dropped`, `lang_gate`, rekord `pii`.

**Kontrola końcowa (krok 10):** wpis w `src/sources.py` (`pretty`, `upstream`, `license`, `license_spdx`, `domain`, `added`, `created`, `provenance`, `traceable`, `is_ocr`, `language`, `text_origin`, `legal_note`), `configs` w `README.md`, test `src/test_<key>_contract.py`. `check.py` nie sprawdza podstawy licencji, to robi krok 11.

**Przegląd praw (krok 11, skill `source-rights-review`):** łańcuch praw (każde ogniwo: zapis, URL, data, hash), V/I przy każdym twierdzeniu, decyzja `admitted`/`excluded`/`held_for_review`, lista „not checked”, osoba zatwierdzająca; próbka treści stron trzecich: seed, ≥40 dok. na warstwę, przedział Wilsona. Opis PR: próbka z `src/render_sample.py`, przegląd praw, wersja PII, before/after. Kontakt z właścicielami praw i regulaminy: tylko ludzie.

**Rozjazdy notatki i repo zgłoszeń** (nasz przebieg / repo zgłoszeń): PII usuwane w całości / maskowane Presidio-NERGAL; prawa: TDM wystarcza / licencja per dokument; ręczna próbka 100+100 na powód / ≥40 na warstwę z Wilsonem; dedup pełna historia modelu / tylko Dynaword (containment ≥0,9). Robisz oba.

## 4. Wysyłka do wglądu Arka (chwilowo, od 15.11.2026)

Każdy wgrywa na SWOIM koncie Hugging Face. Pliki widzi tylko właściciel i Arek (`Maggio33`); publicznie widać nazwę repo i README. `<login>` to Twój login HF, `<key>` z kroku 9.

| nr | co robisz | komenda |
|---|---|---|
| 0 | raz na maszynie | `pip install -U huggingface_hub` i `hf auth login` (token z zapisem) |
| 1 | repo z bramką PRZED plikami i dostęp dla Arka | `python -c "from huggingface_hub import HfApi as A; a=A(); r='<login>/<key>-robocze'; a.create_repo(r, repo_type='dataset'); a.update_repo_settings(r, gated='manual', repo_type='dataset'); a.grant_access(r, 'Maggio33', repo_type='dataset')"` |
| 2 | sprawdź bramkę | okno incognito: strona repo nie pokazuje listy plików |
| 3 | wgraj | `hf upload <login>/<key>-robocze data/<key> data/<key> --repo-type dataset` |
| 4 | README | jedno zdanie „Zbiór roboczy do recenzji, nie do użytku.”; opis zbioru w `data/<key>/OPIS.md`, za bramką |
| 5 | wyślij Arkowi link | `https://huggingface.co/datasets/<login>/<key>-robocze` |

Arek pobiera po `hf auth login`: `hf download <login>/<key>-robocze --repo-type dataset`. Kolejna osoba: `grant_access` z jej loginem; odebranie: `reject_access_request`. Potem krok 12 ze statusem „u Arka do wglądu”.

## 5. Pułapki

- Gałąź `main` zamiast rewizji; „identyczna kopia” zbioru, która nie jest identyczna.
- Próg dobrany po zobaczeniu wyniku bez aneksu.
- Uzysk przeniesiony z innej porcji danych: mierzysz od nowa.
- Plik ręcznej próbki zawiera PII odrzuconych: zostaje w `robocze/`.
- Kilka ciężkich kroków naraz: uruchamiasz je po kolei.
- Status praw skopiowany z innego źródła.
