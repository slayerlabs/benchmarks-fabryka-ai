# Przepis: Social IQa (T46), Slayer 1.06

## Środowisko

- Commit z wynikiem: `a80e693` (gałąź `research/siqa`, od `origin/main` @ `476ffa7`). PR scala się merge commitem,
  więc hash zostaje w historii `main`.
- lm-eval 0.4.9.1, transformers 4.57.6, torch 2.8.0+cu128, Python 3.9.25 (`C:/Users/taki1/bench/.venv-eval`).
- GPU NVIDIA GeForce RTX 5060 Ti 16 GB, Windows 11, `--device cuda --batch 8`.
- Model: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`, lokalna kopia `D:/models/slayer-1.06`.
- Zbiór: `allenai/social_i_qa`, skrypt na `main` @ `8835ceb9141d7896d9d968634a9b21ae440e3ec5`, dane z konwersji
  `refs/convert/parquet` (stan gałęzi `537a2ec8ec565adc0b70b70752893e59e024df26`, odczyt 2026-11-04), split `validation`.
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234. Precyzja: float32.

## Smoke test przed przebiegiem

Pięć dokumentów z panelu (`--probka 5`), sprawdzone ręcznie: prompt `Q: {context} {question}\nA:`, trzy kontynuacje
ze spacją na początku, cel `label - 1`. Identyfikatory i wynik: `doc_id` 260 (`label` 3 → `target` 2, kontynuacje
` accomplished`, ` apprehension for Aubrey`, ` energized`), 575, 851, 1273, 1708. Wszystkie pięć ma zgodny `target`
i kolejność opcji `answerA/B/C`.

## Slayer 1.06, T46 — panel Space (200)

```bash
C:/Users/taki1/bench/.venv-eval/Scripts/python.exe common/ewaluuj.py --model slayer \
  --model_path D:/models/slayer-1.06 --revision ef81be58742544ad32e1afab38db011fec209609 \
  --repo SlayerLab/Slayer1B-1.06 --zadania T46 --dane hf --probka panel200 \
  --wyjscie <dir> --device cuda --batch 8 --etykieta 1.06
```

- Wynik: `acc` 0,39 ±0,0346 (CI95 0,32–0,46, bootstrap 10 000, seed 20261028), n=200, n_population 1954.
- Pomocnicze: `acc_norm` 0,435 ±0,035, `acc_pmi` 0,36 ±0,034, BPB poprawnej 1,939 ±0,051.
- Bazy: losowa 0,3333, stała odpowiedź 0,405. Udział najczęstszej predykcji 0,345.
- `source_id_digest` `a0535087a4dce1a9f798e2e7f9ab66f5325ea0642b7c2b5fbb66b4f8597c0272`; `results_sha256` przebiegu
  `bc6393e1a27a1cb371386265512e666b718b2c548ed4ddf5ed8f7ee583cc7ea4`.

## Slayer 1.06, T46 — pełny split (1954)

Ta sama komenda z `--probka pelna`.

- Wynik: `acc` 0,3895 ±0,0110 (CI95 0,3680–0,4115), n=1954.
- Pomocnicze: `acc_norm` 0,424 ±0,011, `acc_pmi` 0,375 ±0,011, BPB poprawnej 1,945 ±0,017.
- Bazy: losowa 0,3333, stała odpowiedź 0,3362. Udział najczęstszej predykcji 0,348.
- `source_id_digest` `e92365ff54129c93eb518df4c5544bb39847ea762c2b5c970cef0ad5afeef808`; `results_sha256` przebiegu
  `d0c75d95cd8c52965150cf12e2c73b380d5a9b2819265039de99bdd21c8a79d4`.

## Jak powstał plik liczb

```bash
python benchmarks/social-iqa/zbierz_wyniki.py <katalog panelu> <katalog pełnego splitu>
```

Skrypt przepisuje z `results_rozszerzone.json` wartości, SE i CI95 (nie liczy metryk ponownie) i dokłada bazy
policzone z goldów, bo `ewaluuj.py` zostawia je puste przy `klasy_stale=False`. Wyniki per pytanie leżą w
`results/slayer-1.06/social_iqa.jsonl.gz` (panel) i `results/slayer-1.06/social_iqa_full.jsonl.gz` (pełny split).

## Kontrola

**Bez kontroli: nierozstrzygnięte** (METODOLOGIA, „Bez kontroli”; pełny wpis: [`REPRODUCTION.md`](REPRODUCTION.md)).
Żaden model z listy „Model kontrolny etapu B” nie ma opublikowanego wyniku zero-shot na Social IQa — szukano w pliku
wyników Pythii v0, na karcie EuroLLM-1.7B, na Open LLM Leaderboard v2 i w `results.json` Space. Repo woła wprost
zadanie lm-eval `social_iqa`, więc test zgodności implementacji niczego nie sprawdza, a wynik nie idzie do Space ani
do meta-oceny.
