# Benchmarks

Every benchmark with a directory in `research/studies/2026-10-lm-eval-benchmarks/benchmarks/`, and its status
in CodeSOTA. Generated from [`src/codesota/catalog.py`](src/codesota/catalog.py); how to run them:
[`docs/running.md`](docs/running.md).

- `verified` (4): a published reference result was reproduced with this protocol.
- `needs-reference-check` (9): runs and matches the research pipeline, but no reference result is reproduced yet.
- `not-implemented` (42): not in the runner yet.

A status applies to the protocol (0-shot, log-likelihood scoring through lm-eval), not to every model or setup ([`docs/running.md`](docs/running.md#what-a-status-means)).

## Implemented

| benchmark | ID | aliases | metric | size | time | status | note |
|---|---|---|---|---|---|---|---|
| ARC-Easy | `arc-easy` | `arce`, `arc-e`, `T51` | `acc` | `medium` | ~3 min | `verified` | published reference reproduced |
| LAMBADA (OpenAI) | `lambada` | `lambada-openai`, `T17` | `acc` | `medium` | ~3 min | `verified` | published reference reproduced |
| PIQA | `piqa` | `T06` | `acc_norm` | `small` | ~1 min | `verified` | published reference reproduced |
| WinoGrande | `winogrande` | `wg`, `T07` | `acc` | `small` | ~1 min | `verified` | published reference reproduced |
| ARC-Challenge | `arc-challenge` | `arcc`, `arc-c`, `T02` | `acc_norm` | `medium` | ~2 min | `needs-reference-check` | no reference check in research |
| HellaSwag | `hellaswag` | `hs`, `T05` | `acc_norm` | `big` | ~18 min | `needs-reference-check` | reference reproduced 10-shot only; this protocol is 0-shot |
| MathQA | `mathqa` | `T19` | `acc_norm` | `medium` | ~3 min | `needs-reference-check` | no reference check in research |
| MedMCQA | `medmcqa` | `T45` | `acc` | `medium` | ~2 min | `needs-reference-check` | no reference check; marked for review in research |
| MultiBLiMP (Polish) | `multiblimp-pl` | `mblimp-pl`, `T04` | `acc` | `medium` | ~2 min | `needs-reference-check` | no reference check; possible test-set leak (#36) |
| PubMedQA | `pubmedqa` | `T44` | `acc` | `small` | < 1 min | `needs-reference-check` | no reference check in research |
| Social IQa | `social-iqa` | `siqa`, `T46` | `acc` | `medium` | ~2 min | `needs-reference-check` | no reference check; data branch not pinned |
| WikiText-2 | `wikitext-2` | `wikitext`, `wt2`, `T03` | `byte_perplexity` | `small` | ~1 min | `needs-reference-check` | no reference check in research |
| WSC273 | `wsc273` | `wsc`, `T14` | `acc` | `small` | < 1 min | `needs-reference-check` | no reference check; marked for review in research |

Size and time are approximate, from one repeatable reference run (Pythia-1B, float32, one GPU); they scale with the model and hardware and are not requirements.

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

Select a pack with `@name`, for example `--benchmarks @verified` or `--benchmarks @small,arc-challenge`.

| pack | benchmarks |
|---|---|
| `@all` | 55 |
| `@big` | 1 |
| `@en` | 42 |
| `@full-run-2026-11` | 15 |
| `@implemented` | 13 |
| `@medium` | 7 |
| `@needs-reference-check` | 9 |
| `@not-implemented` | 42 |
| `@pl` | 13 |
| `@small` | 5 |
| `@verified` | 4 |
