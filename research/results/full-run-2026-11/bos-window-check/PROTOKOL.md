# Protokół: wpływ BOS na Pythię-1B v0 (pełny przebieg 2026-11)

Ustalony przed pierwszym wynikiem. Progów i wariantów nie zmieniamy po wynikach.

## Pytanie

Czy dokładnie jeden wiodący BOS w każdym żądaniu zmienia wynik Pythii-1B v0 na testach z kontekstem,
i czy ta zmiana jest większa niż przewaga Slayera 1B 1.07 z przebiegu 2026-11.

## Stałe

- Model: `EleutherAI/pythia-1b-v0` @ `f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0`, sha wag `92589a02cfd745884f8473b0a975a93cea4cdaacf8333b0c047dab41623396b2`.
- Kod: `slayerlabs/benchmarks-fabryka-ai` @ `fe82b632` (commit przebiegu), `research/common/ewaluuj.py` niezmieniony, sha `7597c0de7273004dcd099c7e2fb7083b6232e43c17e1822fc291923210d5c1fa`.
- Środowisko `lock`: `research/common/requirements.lock.txt`, lm_eval 0.4.9.1.
- Karta: RTX 5090 (ta sama co przebieg), float32, batch 1, pełne splity, seed domyślny runnera.

## Warianty

| id | zadania | zmiana względem komendy z `manifest.jsonl` |
|---|---|---|
| KONTROLA | T06 | żadna |
| BOS | T51, T05, T17, T06, T07, T14 | jeden wiodący BOS (`tokenizer.bos_token_id`) w każdym żądaniu |
| OKNO | T03 | `--max_length 2048` zamiast 4096; BOS bez zmian (rolling ma już token prefiksu) |

Mechanizm BOS: osobny plik uruchamiający, który woła niezmieniony `ewaluuj.py` i podmienia tylko kodowanie
tekstu w HFLM. Sama flaga `add_bos_token=True` może nie doklejać BOS przy tokenizerze Pythii, więc nie wolno
na niej polegać bez sprawdzenia. Test przed pomiarem, bez sieci i wag: brak BOS i podwójny BOS zapalają błąd.
Po pomiarze: w próbkach każdego zadania wariantu BOS liczba wiodących BOS wynosi 1 w 100% żądań.

## Wartości odniesienia (Pythia, `manifest.jsonl`)

T51 0,558502 (acc) · T05 0,467935 (acc_norm) · T17 0,565690 (acc) · T06 0,709467 (acc_norm) ·
T07 0,544594 (acc) · T14 0,673993 (acc) · T03 2,423435 (byte_perplexity).
Slayer 1B 1.07 z tego samego pliku.

## Warunki

- **Pomiar ważny:** KONTROLA daje 0,7095 po zaokrągleniu do 4 miejsc. Inaczej wynik BOS jest nieważny, kolejka staje, raport mówi „nierozstrzygnięte: środowisko”.
- **Wpływ mały:** na każdym z 6 testów |nowa − stara| < 0,04.
- **Wpływ duży:** na którymkolwiek z 6 testów |nowa − stara| ≥ 0,04. Wtedy wniosek: 88 par trzeba przeliczyć.
- **ARC-Easy osobno:** Slayer 1.07 minus nowa Pythia, SE niezależne (adnotacja „ostrożne”), werdykt z progów |z| ≥ 3 / 2–3 / < 2.
- **Wynik pod progiem to „brak wpływu większego niż 0,04 na Pythii”,** nie „BOS nie ma znaczenia” i nie dowód dla innych modeli.
- SE różnicy: T06 w parach (KONTROLA i BOS per pytanie), pozostałe SE niezależne z adnotacją „ostrożne”, bo próbek starego przebiegu nie ma na tej maszynie.
- Wartość 1,000 albo poniżej bazy losowej − 5 pkt to błąd kodu, nie wynik.

## Dodatek: kontrola ARC-Challenge (decyzja Ani 10.11.2026, dopisane przed liczeniem tego wariantu)

- Wariant KONTROLA-ARC: `utter-project/EuroLLM-1.7B` @ `c730cd9b616799ace3c65e927d63191446f59374`, T02, `research/tools/ewaluacja/ewaluuj_shoty.py 25`, reszta jak komenda tego modelu w `manifest.jsonl` (float32, batch 1, `lock` z protobuf, bez dodatkowego BOS).
- Wartość odniesienia: `acc_norm` 25-shot 0,4061, n = 1172, karta EuroLLM (`benchmarks/arc-challenge/ORIGINAL.md`), SE 0,0143.
- Warunek z `benchmarks/arc-challenge/REPRODUCTION.md`: ±2 pkt, a gdy 2 SE > 2 pkt, w granicach 2 SE. Tu 2 SE = 0,0286 > 0,02, więc **przechodzi, gdy |wynik − 0,4061| ≤ 0,0286**.
- Niezależna od warunku „Pomiar ważny” wariantów BOS. Nie przechodzi: ARC-Challenge zostaje poza tabelą, raport podaje wynik i różnicę.
- Sprawdza kod, zbiór, prompt i metrykę T02. Nie sprawdza ustawienia 0-shot ani wpływu BOS.

## Budżet

Jedna instancja RTX 5090 spoza CN, test 1 GB z HF po starcie. Limit 2 USD i 2 h, bezpiecznik czasu i strażnik
bezczynności na instancji, na koniec zero instancji i koszt z `vastai show invoices`.

Decyzja Ani 10.11.2026: pomiar za około 1 USD.
