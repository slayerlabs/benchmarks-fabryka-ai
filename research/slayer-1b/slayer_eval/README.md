# slayer_eval: niezależna ewaluacja checkpointów Slayera 1B

Jesteśmy zewnętrznym ewaluatorem dla SlayerLab: autor modelu (Arek) nie benchmarkuje go sam.
Pipeline liczy to samo co Space SlayerLab/Slayer1B-Benchmarks, a obok surowego acc także
metryki, które odróżniają „model nie wie" od „model nie radzi sobie z formatem odpowiedzi".

## Jak jest zbudowany Space (odczyt plików Space, 29.10.2026)

**SlayerLab/Slayer1B-Benchmarks**: statyczny Space (index.html + app.js + contract.js + style.css).
Sam niczego nie liczy, tylko wyświetla `results.json`. Plik jest weryfikowany przed wyświetleniem
po SHA-256 zapisanym w `results-feed.json`.

| plik | zawartość |
|---|---|
| `results.json` (181 kB) | schemat `urn:fabryka-ai:benchmark-results:2:protocol-0.3.1`: `schema_version`=2, `protocol_id` (`bench50-v0.3.1-panel200` albo `-fullB`), `run_id`, `models[]`, `tasks[]`, `observations[]`, `contrasts[]`, `provenance` |
| `results.schema.json` | JSON Schema (draft 2020-12, `additionalProperties: false` wszędzie) |
| `results-feed.json` | `{"results": "results.json", "sha256": …}` |
| `tasks_50.json` | rejestr 50 benchmarków: zadanie lm-eval, repo i rewizja zbioru, split, shoty, metryka, licencja |
| `METHOD.md` | protokół (niżej) |
| `contamination_field_roles.json` | które pola rekordu są skanowane na kontaminację |

**Protokół (METHOD.md):** 50 benchmarków (38 EN, 12 PL). EN liczy lm-evaluation-harness
w commicie `6d2abda4`, PL fork OpenPL w commicie `21d0ea9c`. Ustawienia: float32, batch 1,
kontekst do 4096 tokenów (dłuższe wejścia są odrzucane, nie przycinane), bez szablonu czatu,
jeden BOS. Seedy: python 0, numpy/torch/fewshot 1234. Próbka to `min(200, N)` dokumentów
rosnąco po SHA-256 `20261028|benchmark_id|member_task|source_id`, ta sama dla wszystkich modeli.
WikiText-2 idzie pełnym strumieniem (62 dokumenty). EN 0-shot, 12 zadań PL 5-shot, BBH 3-shot.
Jedna metryka główna na benchmark i brak średniej. CI95: bootstrap 10 000 powtórzeń, seed 20261028.
Kontrasty: sparowany test permutacyjny z poprawką Holma. Bazy odniesienia: losowa, większościowa
(tylko zadania o stałym zbiorze klas), udział najczęstszej predykcji, flaga stałej predykcji.
Kontaminacja: n-gramy 13 względem korpusu treningowego; dla flagowanych wyników także wartość
na pytaniach bez trafień.

**Obserwacja** (jedna na zadanie×model), pola wymagane: `task_id` (T01–T50), `model_id`,
`protocol_id`, `metric`, `unit` (`percent`|`score`|`byte_ppl`), `higher_is_better`,
`n_population`, `n_selected`, `n_scored`, `state` (`ok`|`not_run`|`blocked_*`|`failed`|…),
`value`, `ci95{lower,upper,level,method,replicates,seed}`, `source_id_digest`, `results_sha256`,
`runner_sha256`, `contamination`, `contamination_receipt_sha256`. Opcjonalnie `reference`
z polami `chance_value`, `majority_value`, `majority_prediction_share` i `constant_prediction`,
oraz pola hit-free.

**Modele w Space:** `SlayerLab/Slayer1B-1.06` @ `ef81be58…`, `LiquidAI/LFM2.5-1.2B-Base` @ `7453bca9…`.

**Stan Slayera 1.06 w naszym zestawie:**

| T | zadanie | metryka | 1.06 | LFM2.5 | losowa / większ. | najczęstsza pred. |
|---|---|---|---|---|---|---|
| T02 | ARC-C | acc_norm | 0,250 | 0,490 | 0,2495 / — | — |
| T03 | WikiText-2 | byte_ppl ↓ | 1,846 (n=62) | 1,735 | — | — |
| T04 | MultiBLiMP-PL | accuracy % | 99,0 | 86,5 | 50 / — | — |
| T44 | PubMedQA | acc | **not_run** | not_run | — | — |
| T45 | MedMCQA | acc | 0,245 | 0,405 | 0,25 / 0,305 | **0,88** |
| T46 | Social IQa | acc | **not_run** | not_run | — | — |

Slayer 1.06 ma `not_run` na T06, T14, T18, T19, T36, T44 i T46. Przy MedMCQA, BoolQ, CB, WiC,
RTE, ANLI, SST-2 i CoLA 85–100% jego predykcji to ta sama odpowiedź (`majority_prediction_share`
0,85–1,0). To ślad stałej litery, który ten pipeline rozkłada na części.

Drugi Space **SlayerLab/Slayer1B** prowadzi `scores-history.csv` (113 wierszy) i `scores-history-106.csv`
z kolumnami `model,step,tokens,checkpoint_sha256,arc_easy,blimp,wikitext2_token_ppl,wikitext2_byte_ppl,eff,multiblimp_pl,arc_easy_pl,eval_gpu`
(tokens = step·2^20, eval_gpu to litera A–E bez legendy w Space).

## Co liczymy

Dla każdego zadania MC i każdego wariantu promptu liczymy cztery reguły wyboru: **acc**
(największy loglik, jak Space), **acc_norm** (loglik na znak, konwencja lm-eval),
**acc_pmi** (loglik warunkowy minus bezwarunkowy, co kalibruje prior litery lub odpowiedzi) oraz
**BPB poprawnej odpowiedzi** (−loglik / (ln2·bajty), bez progu decyzyjnego). Każda z nich ma
n, SE i CI95 (bootstrap z seedem Space). Do tego baza losowa, większościowa i udział
najczęstszej predykcji.

| T | zadanie | warianty | uwagi |
|---|---|---|---|
| **T02** | **ARC-Challenge** | `space` (cloze, główna acc_norm) + `mc` (litery A–D) | **trace per pytanie** + tryb po checkpointach |
| T03 | WikiText-2 | `space` (rolling) | word/byte/token perplexity + bits per byte, pełny strumień |
| T04 | MultiBLiMP-PL | `space` (para minimalna, spacja przed zdaniem, suma logprob) | PMI pominięte (pusty kontekst) |
| T44 | PubMedQA | `space` (yes/no/maybe) | zbiór przez konwersję parquet |
| T45 | MedMCQA | `space` (litery) + `cloze` (treść odpowiedzi) | |
| T46 | Social IQa | `space` (cloze) | zbiór przez konwersję parquet |

**Trace ARC-C** (`trace/T02_<wariant>.jsonl`, jeden wiersz na pytanie): id, poprawna odpowiedź,
dla każdej opcji logprob (suma, na bajt, na token), logprob bezwarunkowy i PMI, długość w bajtach
i tokenach. Do tego wybór każdej reguły (acc / acc_norm / bpb / pmi) oraz to, czy wybrana opcja
jest najkrótsza albo najdłuższa. W `results_rozszerzone.json` stoi `rozklad_wyborow`: rozkład
pozycji A–D per reguła oraz udział najkrótszej i najdłuższej opcji, wybranej i poprawnej.

**Tryb po checkpointach:** `porownaj_checkpointy.py` bierze katalogi wyników kilku wersji
(1.00…1.06) na tej samej liście pytań. Dla każdej reguły wypisuje pytania, które przeszły
z błędnych na dobre i odwrotnie (z id), liczbę zmian wyboru i dokładny test McNemara.
Niczego nie stroimy pod benchmark: prompt i metryka główna są takie jak w Space, a warianty
służą do diagnozy.

## Uruchomienie

**Slayer: tylko `hipoteza_formatu.py`.** `ewaluuj.py` / `ewaluuj_slayer.sh` ładują model przez
`HFLM` (transformers), a `config.json` Slayera nie ma `model_type` ani kodu modelowania:
`AutoConfig.from_pretrained` kończy się `ValueError: Unrecognized model` (sprawdzone na 1.06 z
transformers 4.57.6). Ta ścieżka działa dla modeli z transformers (Pythia, Qwen). Wyniki Slayera w
`wyniki/raport_formatu.json` liczy `hipoteza_formatu.py` z forwardem `slayer_model.py`:

```bash
huggingface-cli download SlayerLab/Slayer1B-1.06 --revision ef81be58742544ad32e1afab38db011fec209609 \
  --local-dir models/slayer-1.06
.venv-eval/bin/python slayer_eval/hipoteza_formatu.py licz --model models/slayer-1.06 \
  --zadania arc_c_cloze,arc_c_mc --wyjscie wyniki/1.06 --device cpu
.venv-eval/bin/python slayer_eval/hipoteza_formatu.py wikitext --model models/slayer-1.06 --wyjscie wyniki/1.06
.venv-eval/bin/python slayer_eval/hipoteza_formatu.py analiza --wyniki wyniki
```

Pełna lista zadań i komenda dla Pythii: `paczka_testerzy/INSTRUKCJA.md`, sekcja „Jak wygenerować
surowe dane od zera”. Ścieżka lm-eval (model z transformers):

```bash
python3 -m venv .venv-eval && .venv-eval/bin/pip install -r slayer_eval/requirements.lock.txt
# raz, z siecią do HF: zbiory do cache (lista OK/BŁĄD na końcu; --lista wypisuje bez pobierania)
.venv-eval/bin/python slayer_eval/pobierz_zbiory.py
# dalej bez sieci (OFFLINE=1 ustawia HF_DATASETS_OFFLINE=1 i HF_HUB_OFFLINE=1);
# bez MODEL_PATH i OFFLINE model pobiera się z HF po nazwie i rewizji:
ETYKIETA=pythia-1b slayer_eval/ewaluuj_slayer.sh EleutherAI/pythia-1b <rewizja>
# diff ARC-C między wersjami:
.venv-eval/bin/python slayer_eval/porownaj_checkpointy.py --zadanie T02_space --wyjscie wyniki_slayer/arc_diff \
  wyniki_slayer/<1.05> wyniki_slayer/<1.06>
```

Wyjście: `results.json` (schemat Space, tylko pola schematu, kontaminacja `unscanned`),
`results_rozszerzone.json` (te same obserwacje i `dodatkowe`), `scores-history-wiersz.csv`
(wiersz w kolumnach scores-history.csv; `HISTORIA_CSV=` dopisuje go do istniejącego pliku),
`trace/`, `probki/` (pełne próbki lm-eval, lokalnie, bez publikacji), `podsumowanie.md`.

## Różnice wobec Space i rzeczy niezweryfikowane

- lm-eval **0.4.9.1 z PyPI**, nie commit `6d2abda4` (instalacja z gita nie była możliwa). Prompty
  zadań są przepisane 1:1 z definicji lm-eval, ale zgodności logitów z runnerem Space nie sprawdziliśmy.
- `source_id` w haszu próbki: używamy pola `id` zbioru (ARC, MedMCQA), a gdzie go brak, indeksu wiersza.
  Definicji z Space nie znamy, więc panel200 może nie być identyczny z panelem Space; porównania
  między wersjami Slayera robimy na NASZYM panelu.
- Nazwy kolumn TSV MultiBLiMP (`sen`/`wrong_sen`) i ścieżki parquet dla PubMedQA/SIQA nie zostały
  sprawdzone na prawdziwych danych.
- `wikitext2_byte_ppl` w scores-history.csv (np. 2,37) i `byte_perplexity` w bench50 (1,846) mają
  różne definicje (notatka T03: „not the historical Glint tp^(N/B) conversion"). Nasz wiersz CSV
  niesie byte_ppl w konwencji harnessu. Kolumny `arc_easy`, `blimp`, `eff` i `arc_easy_pl` zostają puste.
- Kontrastów i skanu kontaminacji nie liczymy: nie mamy korpusu treningowego.
