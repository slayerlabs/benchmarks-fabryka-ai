# Study 2026-11: can a small model match a large one?

**State: in progress.** Started November 2026 from the CodeSOTA list of 25 priority benchmarks
([research priorities](../../../benchmarks/docs/research-priorities.md)).

## Question

On generative and agentic benchmarks, how close do small models get to Bielik 11B v3.1? The small models are
LFM3-1.7B (Liquid AI, our reference) and Slayer 1B; Bielik 11B v3.1 is the large model.

## Models

Each model runs in its own configuration from the [evaluation methodology](../../../benchmarks/docs/methodology.md);
every benchmark README names how it ran (Fabryka API, our vLLM, or a GPU) and its deviations.

| model | role |
|---|---|
| Bielik 11B v3.1 | large model, mostly through the Fabryka AI API |
| LFM3-1.7B | small model, our reference, own vLLM |
| Slayer 1B | small model in training; `null` with the reason where it cannot run a benchmark (base model, 4096-token context) |

## Benchmarks

State on 26.11.2026. "Done" means merged results in the benchmark's directory for the models its task named; not
every benchmark has all three models, and each benchmark's README lists which ran. The issue closes on the board.

| # | benchmark | directory | task | state |
|---|---|---|---|---|
| 1 | LiveClaw | — | #282 | planned |
| 2 | Claw-Eval General (EN) | — | #283 | planned |
| 3 | BrowseComp-Plus (OpenClaw subset) | — | #284 | planned |
| 4 | WebArena-Verified | — | #285 | planned |
| 5 | EnterpriseOps-Gym | — | #286 | planned |
| 6 | AutomationBench | [`automationbench`](../../benchmarks/automationbench/README.md) | #287 | done |
| 7 | BFCL V4 | [`bfcl-v4`](../../benchmarks/bfcl-v4/README.md) | #288 | done |
| 8 | ToolSandbox | — | #289 | in review (PR #351) |
| 9 | MCP-Atlas | — | #290 | planned |
| 10 | τ³-bench | — | #291 | in review (PR #352) |
| 11 | SWE-bench Verified | — | #292 | planned |
| 12 | SWE-bench Multilingual | — | #293 | planned |
| 13 | Terminal-Bench 2.1 | [`terminal-bench-2-1`](../../benchmarks/terminal-bench-2-1/README.md) | #294 | results merged (LFM3-1.7B) |
| 14 | LiveCodeBench v6 | [`livecodebench-v6`](../../benchmarks/livecodebench-v6/README.md) | #295 | done |
| 15 | LiveCodeBench Pro 25Q2 | [`livecodebench-pro-25q2`](../../benchmarks/livecodebench-pro-25q2/README.md) | #296 | done |
| 16 | SciCode | [`scicode`](../../benchmarks/scicode/README.md) | #297 | done |
| 17 | IFEval | [`ifeval`](../../benchmarks/ifeval/README.md) | #298 | done |
| 18 | IFBench | [`ifbench`](../../benchmarks/ifbench/README.md) | #299 | done |
| 19 | IFStruct | [`ifstruct`](../../benchmarks/ifstruct/README.md) | #300 | done |
| 20 | Multi-IF | [`multi-if`](../../benchmarks/multi-if/README.md) | #301 | done |
| 21 | GPQA Diamond | [`gpqa-diamond`](../../benchmarks/gpqa-diamond/README.md) | #302 | done |
| 22 | Humanity's Last Exam | — | #303 | in review (PR #358) |
| 23 | AA-Omniscience | [`aa-omniscience`](../../benchmarks/aa-omniscience/README.md) | #304 | done |
| 24 | AA-LCR | [`aa-lcr`](../../benchmarks/aa-lcr/README.md) | #305 | done |
| 25 | RULER 128K | [`ruler-128k`](../../benchmarks/ruler-128k/README.md) | #306 | done |

## Hypotheses and thresholds

No study-level hypothesis was written before the first results. Five benchmarks wrote their own before measuring, in
their `PROTOCOL.md`: [AA-LCR](../../benchmarks/aa-lcr/PROTOCOL.md),
[LiveCodeBench v6](../../benchmarks/livecodebench-v6/PROTOCOL.md),
[LiveCodeBench Pro 25Q2](../../benchmarks/livecodebench-pro-25q2/PROTOCOL.md),
[SciCode](../../benchmarks/scicode/PROTOCOL.md) and [RULER 128K](../../benchmarks/ruler-128k/PROTOCOL.md).
Any comparison across the whole study added now is exploratory and says so.

## Board

Tasks of this study carry the label `study:small-vs-large`.

## Conclusion

Not written yet: the study is in progress.
