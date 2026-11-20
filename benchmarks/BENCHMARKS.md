# Benchmarks

Every benchmark the repository has a directory for, and where it stands in CodeSOTA. Generated from
[`src/codesota/catalog.py`](src/codesota/catalog.py); regenerate with
`uv run python -c "from codesota.catalog import markdown; print(markdown(), end='')" > BENCHMARKS.md`.

| status | meaning |
|---|---|
| `verified` | the runner implements it; a published reference result was reproduced with this protocol, and the runner reproduces the research pipeline for it |
| `needs-reference-check` | the runner implements it and reproduces the research pipeline, but no published reference result has been reproduced for this protocol; its scores are measurements, not yet validated |
| `not-implemented` | the benchmark has a directory in `research/benchmarks/`; the runner cannot run it yet |

4 verified, 9 need a reference check, 42 not implemented. Run them with `python -m codesota.runner` ([`docs/running.md`](docs/running.md)).

## Implemented

| benchmark | ID | legacy ID | aliases | packs | decision metric | status | evidence |
|---|---|---|---|---|---|---|---|
| ARC-Easy | `arc-easy` | T51 | `arce`, `arc-e` | `@full-run-2026-11` | `acc` | `verified` | Pythia-1B v0 reproduces its published acc 0.5585 (window 0.5381-0.5789) without BOS (research/benchmarks/arc-easy/REPRODUCTION.md); with one BOS it scores 0.5690, inside the same window (research/results/full-run-2026-11/bos-window-check/RAPORT.md). |
| LAMBADA (OpenAI) | `lambada` | T17 | `lambada-openai` | `@full-run-2026-11` | `acc` | `verified` | Pythia-1B v0 reproduces its published acc 0.5622 (window 0.5422-0.5822) without BOS (research/benchmarks/lambada/REPRODUCTION.md); with one BOS it scores 0.5605, inside the same window (bos-window-check). |
| PIQA | `piqa` | T06 |  | `@full-run-2026-11` | `acc_norm` | `verified` | Pythia-1B v0 reproduces its published acc_norm (window 0.6838-0.7264) without BOS (research/benchmarks/piqa/REPRODUCTION.md); with one BOS it scores 0.7095, inside the same window (bos-window-check). |
| WinoGrande | `winogrande` | T07 | `wg` | `@full-run-2026-11` | `acc` | `verified` | Pythia-1B v0 reproduces its published acc 0.5375 (window 0.5095-0.5655) without BOS (research/benchmarks/winogrande/REPRODUCTION.md); with one BOS it scores 0.5438, inside the same window (bos-window-check). |
| ARC-Challenge | `arc-challenge` | T02 | `arcc`, `arc-c` | `@full-run-2026-11` | `acc_norm` | `needs-reference-check` | Stage B has no reference check (research/STATUS.md, 'bez kontroli'). |
| HellaSwag | `hellaswag` | T05 | `hs` | `@full-run-2026-11` | `acc_norm` | `needs-reference-check` | The reference check (EuroLLM-1.7B, met) was computed 10-shot with separate code; this protocol is 0-shot, so no reference result has been reproduced for it (research/STATUS.md). |
| MathQA | `mathqa` | T19 |  | `@full-run-2026-11` | `acc_norm` | `needs-reference-check` | Stage B has no reference check (research/STATUS.md, 'bez kontroli'). |
| MedMCQA | `medmcqa` | T45 |  | `@full-run-2026-11` | `acc` | `needs-reference-check` | Stage B has no reference check, and the benchmark is marked for review (research/STATUS.md). |
| MultiBLiMP (Polish) | `multiblimp-pl` | T04 | `mblimp-pl` | `@full-run-2026-11` | `acc` | `needs-reference-check` | Stage B has no reference check, and a possible leak of the test set into training data is open (research/STATUS.md, #36). |
| PubMedQA | `pubmedqa` | T44 |  | `@full-run-2026-11` | `acc` | `needs-reference-check` | Stage B has no reference check (research/STATUS.md, 'bez kontroli'). |
| Social IQa | `social-iqa` | T46 | `siqa` | `@full-run-2026-11` | `acc` | `needs-reference-check` | Stage B has no reference check (research/STATUS.md, 'bez kontroli'). The data are read from the repository's refs/convert/parquet branch, which has no pinned commit; the recorded revision is that of the main branch, so a later conversion could change the documents. |
| WikiText-2 | `wikitext-2` | T03 | `wikitext`, `wt2` | `@full-run-2026-11` | `byte_perplexity` | `needs-reference-check` | Stage B has no reference check (research/STATUS.md, 'bez kontroli'). |
| WSC273 | `wsc273` | T14 | `wsc` | `@full-run-2026-11` | `acc` | `needs-reference-check` | Stage B has no reference check, and its control model is outside the methodology's list (research/STATUS.md, marked for review). |

## Not implemented

| benchmark | ID | legacy ID | language |
|---|---|---|---|
| 8TAGS | `8tags` | T23 | PL |
| ANLI (round 3) | `anli-r3` | T16 | EN |
| BIG-Bench Hard | `bbh` | T47 | EN |
| Belebele (Polish) | `belebele-pl` | T24 | PL |
| BLiMP | `blimp` | T01 | EN |
| BLiMP Supplement | `blimp-supplement` | T52 | EN |
| BoolQ | `boolq` | T10 | EN |
| CommitmentBank | `cb` | T12 | EN |
| CBD | `cbd` | T28 | PL |
| CoLA | `cola` | T49 | EN |
| COPA | `copa` | T11 | EN |
| CoQA | `coqa` | T41 | EN |
| DROP | `drop` | T39 | EN |
| DYK | `dyk` | T25 | PL |
| EWoK | `ewok` | T53 | EN |
| EWoK (Polish) | `ewok-pl` |  | PL |
| GSM8K | `gsm8k` | T33 | EN |
| IFEval | `ifeval` | T36 | EN |
| NKJP-NER (KLEJ) | `klej-ner` | T29 | PL |
| LLMzSzL | `llmzszl` | T37 | PL |
| LogiQA | `logiqa` | T18 | EN |
| MATH | `math` | T34 | EN |
| MMLU | `mmlu` | T32 | EN |
| Natural Questions (open) | `nq-open` | T42 | EN |
| OpenBookQA | `openbookqa` | T08 | EN |
| PAWS (English) | `paws-en` | T48 | EN |
| PolEmo 2.0 (in-domain) | `polemo2` | T22 | PL |
| PolQA | `polqa` | T30 | PL |
| PoQuAD | `poquad` | T31 | PL |
| PPC | `ppc` | T26 | PL |
| PROST | `prost` | T20 | EN |
| PSC | `psc` | T27 | PL |
| RACE | `race` | T40 | EN |
| ReCoRD | `record` | T50 | EN |
| RTE | `rte` | T15 | EN |
| SciQ | `sciq` | T09 | EN |
| SQuAD 2.0 | `squad2` | T38 | EN |
| SST-2 | `sst2` | T21 | EN |
| TriviaQA | `triviaqa` | T43 | EN |
| TruthfulQA (MC2) | `truthfulqa` | T35 | EN |
| UncheatableEval | `uncheatable-eval` |  | EN |
| WiC | `wic` | T13 | EN |

## Packs

Select a pack with `@name`, for example `--benchmarks @verified,arc-challenge`.

| pack | benchmarks |
|---|---|
| `@all` | 55 |
| `@en` | 42 |
| `@full-run-2026-11` | 15 |
| `@implemented` | 13 |
| `@needs-reference-check` | 9 |
| `@not-implemented` | 42 |
| `@pl` | 13 |
| `@verified` | 4 |
