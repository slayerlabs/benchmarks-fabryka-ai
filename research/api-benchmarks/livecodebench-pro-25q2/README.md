# LiveCodeBench Pro 25Q2

Whether a model writes a C++ program that the judge accepts on the hidden tests of a recent Codeforces/ICPC/IOI
problem. The pre-registered question, control (K1), hypotheses (K2, K3) and verdict rules are in
[PROTOCOL.md](PROTOCOL.md); this file says how the run is done. Refs #296.

- Paper: [Zheng et al. 2025, LiveCodeBench Pro: How Do Olympiad Medalists Judge LLMs in Competitive
  Programming?](https://arxiv.org/abs/2506.11928)
- Harness and scorer: [GavinZhengOI/LiveCodeBench-Pro](https://github.com/GavinZhengOI/LiveCodeBench-Pro) @
  `d614eef4f95b3654bf0758c64e1194b2575850b8` with its judge submodule
  [LightCPVerifier](https://github.com/YanagiOrigami/LightCPVerifier) @ `021d121c882e70856b66113142495e31b9fe1d80`:
  the prompt of `api_interface.LLMInterface` (built by its own `generate_solution`), the code extraction
  `util.extract_longest_cpp_code`, the judge `judge.LightCPVerifierJudge` and the counting of `benchmark.print_stats`
  (only the verdict `Accepted` counts), with the harness's dependencies at the versions of its `uv.lock`
- Data: [QAQAQAQAQ/LiveCodeBench-Pro](https://huggingface.co/datasets/QAQAQAQAQ/LiveCodeBench-Pro) @
  `adebffce047dddb7768a86bace6aea4f7425e3bc` (gated: a Hugging Face login that accepted its terms), split
  `quater_2025_4_6`: 167 problems (easy 97, medium 57, hard 13), sorted by `problem_id` (2084A first). Tests:
  [QAQAQAQAQ/LiveCodeBench-Pro-Testcase](https://huggingface.co/datasets/QAQAQAQAQ/LiveCodeBench-Pro-Testcase) @
  `5257736c0a4e30ba0949d41c56a257c323d9c600`, one zip per problem (public)
- Metric: pass@1 in percent over all 167 problems (one sample per problem; a problem that is not accepted counts as
  a fail, including a missing test zip and a judge or request error that persisted after its retry), stderr
  `sqrt(p(1-p)/n)`. `other_metrics` in each result file: the secondary score with the problems left out whose zip is
  missing or whose judging or request failed in the infrastructure (and their count by reason), accepted/n per
  difficulty, the count of each category (accepted, wrong_answer, time_limit, memory_limit, runtime_error,
  output_limit, compile_error, no_code, unfinished, no_tests, judge_error, request_error, unsupported), output tokens
  per answer (mean, median, max), unfinished answers, length stops, the share of answers containing `<think>`, and
  on the API the check of the local prompt count against the API's
- Settings: the harness's prompt `LLMInterface().prompt + problem_statement` as the only user message (no system
  message of ours; LFM3-1.7B's chat template at `1da06bec` has no default system prompt, so its prompt has none;
  Bielik gets the system prompt the API adds; PROTOCOL.md, Amendment 1), temperature
  0.6, top_p 0.95, seed 20261122. On our vLLM every request also carries `top_k` 0, `repetition_penalty` 1.0,
  frequency and presence penalty 0 and `max_tokens` = 262144 minus the prompt tokens from the server's `/tokenize`;
  `lfm3-1.7b-nothink` adds `chat_template_kwargs: {"enable_thinking": false}`. On the Fabryka API `max_tokens` =
  32768 minus the prompt counted locally with Bielik's tokenizer and chat template (with its provider prompt) minus
  64. The code is `extract_longest_cpp_code` of the text after the last `</think>`; with thinking on, an answer
  without `</think>` or not stopped by `stop` is unfinished and not judged. Judge: the harness's
  `LightCPVerifierJudge` with 8 workers (the `worker` of `benchmark.py`), its image built once (`setup_scoring_vm.sh`)
  and its id recorded in each result
- Extra services: the Fabryka AI API for Bielik; one GPU for LFM3-1.7B (written for an H100 80 GB, `vllm serve` or a
  shared server through `BASE_URL`); a Linux x86_64 machine with privileged Docker for the judge (written for a
  32-vCPU EPYC 7302P KVM VM, Ubuntu 22.04)

## How to run

Generation and judging are separate steps on separate machines; both resume where they stopped.

| step | machine | command |
|---|---|---|
| LFM3-1.7B, thinking on | GPU box, vLLM 0.34.0 already serving the pinned revision as `lfm3-1.7b` with `--max-model-len 262144` and no `--reasoning-parser` | `BASE_URL=http://localhost:8000 bash run.sh lfm3-1.7b` |
| LFM3-1.7B, thinking off | the same server | `BASE_URL=http://localhost:8000 bash run.sh lfm3-1.7b-nothink` |
| Bielik 11B v3.1 | any machine with Python 3.12 and `uv` (Mac or Linux); `FABRYKA_API_KEY` and a Hugging Face login with access to the problem set and to `speakleash/Bielik-11B-v3.1-Instruct` | `bash run.sh bielik-11b-v3.1` |
| Slayer 1B | none | `bash run.sh slayer1b-1.09-k70000` (writes the `null` result) |
| prepare the judge, once | fresh Ubuntu 22.04 x86_64 VM with Docker, as root, with this repo cloned | `bash setup_scoring_vm.sh` |
| judge one model | that VM, after all generation has finished, with `out/<model-id>/` copied from the generating machine and no other job on the VM (time limits are CPU-bound); the three models one after another | `bash run.sh <model-id> --score` |
| exploratory re-judging (whole-answer extraction, Bielik with a header prefix) | that VM, after the three are judged | `HF_HOME=$PWD/.cache/hf HF_HUB_OFFLINE=1 .venv/bin/python rejudge.py out results` |
| K1-K3 | anywhere | `python3 compare.py results` |
| raw-output check, exploratory tables, README blocks | the Mac with the raw outputs | `python3 raw_outputs.py <export.tgz> && python3 explore.py && python3 readme.py` |

`--limit N` in any generating or judging command takes the first N problems; its result goes to
`out/<model-id>/<model-id>-limitN.json`, never to `results/`. Generation writes
`out/<model-id>/{generations.jsonl,problems.json,api-events.jsonl,run.json,manifest.json}` (raw outputs with
thinking, not committed). Judging downloads the test zips (about 3 GB for 25Q2) into `.cache/hf`, writes
`out/<model-id>/{tests.json,graded.jsonl}` and then `results/<model-id>.json` and `.jsonl.gz` (the extracted code
per problem, no thinking). Each step records our code commit, the runner checksums and the machine in `run.json`
and the sha256 of what it wrote in `manifest.json`; the next step stops if its input no longer matches.

`compare.py` writes `results/hypotheses.json` with K1, K2 and K3 as PROTOCOL.md defines them and a `group_tests`
list (K2 and K3: z, one-sided `p_support` = Φ(z), `p_refute` = 1 − Φ(z), raw outcome) that the SciCode benchmark
reads with its own `--group`; Holm runs with m = 4 over the two benchmarks' K2 and K3, separately for the two
directions. Without `--group` the other benchmark's two tests count with p = 1.

Tests: `uv run --no-project --python 3.12 --with pytest --with huggingface_hub==0.35.0 --with openai==1.108.1
--with certifi python -m pytest research/tests/test_livecodebench_pro_25q2.py` (the prompt and extraction tests
need the harness clone that `run.sh` makes in `.cache/`).

## Results

Generated by `readme.py` from `results/` (`python3 readme.py --check` exits 1 if this file is stale).

<!-- readme.py: results (generated from results/ by readme.py; edit readme.py, not this block) -->

| model | thinking | serving | output limit | accepted (%) | stderr | n | mean output tokens | date |
|---|---|---|---|---|---|---|---|---|
| LFM3-1.7B (`lfm3-1.7b`) | on (template default) | vLLM 0.34.0, bf16, H100 | context minus prompt tokens (context 262144) | 32.34 | 3.62 | 167 | 32880.6 | 2026-11-22 |
| LFM3-1.7B (`lfm3-1.7b-nothink`) | off requested (`enable_thinking: false`) | the same vLLM server | context minus prompt tokens (context 262144) | 28.74 | 3.50 | 167 | 24544.8 | 2026-11-22 |
| Bielik 11B v3.1 (`bielik-11b-v3.1`) | no reasoning switch through the API; 34/167 answers close a `</think>` draft | Fabryka AI API, with the API's provider system prompt | context minus prompt tokens minus a margin of 64 (context 32768) | 1.80 | 1.03 | 167 | 1123.1 | 2026-11-22 |
| Slayer 1B 1.09 at update 70 000 (`slayer1b-1.09-k70000`) | no (base model) | local, research/common/slayer_lm.py, bf16, greedy | context minus prompt tokens (context 4096) | 0.00 | 0.00 | 167 | 3130.0 | 2026-11-24 |

Accepted (%) ± stderr (accepted/n): all problems (headline), without the problems whose test zip is missing or whose judging or request failed (secondary), and per difficulty; where none was accepted, the exact (Clopper-Pearson) 95% interval instead of the stderr, which is 0 there:

| run | all | secondary | left out of secondary | easy | medium | hard |
|---|---|---|---|---|---|---|
| lfm3-1.7b | 32.34 ± 3.62 (54/167) | 32.93 ± 3.67 (54/164) | no_tests 3 | 53.61 ± 5.06 (52/97) | 3.51 ± 2.44 (2/57) | 0.00 (0/13; exact 95% CI 0 to 24.71) |
| lfm3-1.7b-nothink | 28.74 ± 3.50 (48/167) | 29.27 ± 3.55 (48/164) | no_tests 3 | 49.48 ± 5.08 (48/97) | 0.00 (0/57; exact 95% CI 0 to 6.27) | 0.00 (0/13; exact 95% CI 0 to 24.71) |
| bielik-11b-v3.1 | 1.80 ± 1.03 (3/167) | 1.83 ± 1.05 (3/164) | no_tests 3 | 3.09 ± 1.76 (3/97) | 0.00 (0/57; exact 95% CI 0 to 6.27) | 0.00 (0/13; exact 95% CI 0 to 24.71) |
| slayer1b-1.09-k70000 | 0.00 (0/167; exact 95% CI 0 to 2.18) | 0.00 (0/167; exact 95% CI 0 to 2.18) | none | 0.00 (0/97; exact 95% CI 0 to 3.73) | 0.00 (0/57; exact 95% CI 0 to 6.27) | 0.00 (0/13; exact 95% CI 0 to 24.71) |

Judge categories (problems):

| run | AC | WA | TLE | MLE | RE | OLE | CE | no code | unfinished | no tests | judge error | request error | over context |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lfm3-1.7b | 54 | 73 | 18 | 0 | 4 | 0 | 11 | 4 | 0 | 3 | 0 | 0 | 0 |
| lfm3-1.7b-nothink | 48 | 82 | 14 | 0 | 4 | 0 | 10 | 6 | 0 | 3 | 0 | 0 | 0 |
| bielik-11b-v3.1 | 3 | 84 | 8 | 0 | 10 | 0 | 59 | 0 | 0 | 3 | 0 | 0 | 0 |
| slayer1b-1.09-k70000 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 167 | 0 | 0 | 0 | 0 | 0 |

| run | output tokens mean / median / max | unfinished (thinking on) | stopped by the length limit | answers containing `<think>` | answers closing a reasoning block with `</think>` | median share of the answer before its last `</think>` | accepted answers closing `</think>` |
|---|---|---|---|---|---|---|---|
| lfm3-1.7b | 32880.6 / 31756 / 71802 | 0 | 0 | 0 of 167 (0.0%) | 167 of 167 | 93.5% | 54 of 54 |
| lfm3-1.7b-nothink | 24544.8 / 21101 / 261165 | 0 | 1 | 63 of 167 (37.7%) | 153 of 167 | 93.1% | 46 of 48 |
| bielik-11b-v3.1 | 1123.1 / 1046 / 2241 | 0 | 0 | 0 of 167 (0.0%) | 34 of 167 | 75.6% | 2 of 3 |
| slayer1b-1.09-k70000 | 3130.0 / 3192 / 3774 | 0 | 167 | 0 of 167 (0.0%) | ? of 167 |  | ? of 0 |

Bielik's prompt: the API's `usage.prompt_tokens` minus our local count with Bielik's own template: min 0, max 0 over its 167 answers.

Baselines: 0 for random and majority answers (no fixed output passes a problem's hidden tests). The LFM3-1.7B card reports 31.74; the control is in Hypotheses.

Judge: all three runs on one machine, one after another: AMD EPYC 7302P 16-Core Processor, 30 vCPUs, 8 judge workers, image `sha256:a04214fc3f8a0274d252c161a2b58cf59606aa6f37a019da19d7b94c2c9acad0`, go-judge v1.9.6; test zips at `5257736c0a4e30ba0949d41c56a257c323d9c600` (tests.json sha256 `b117dd792c35485aa35d655f57ffa96769aa3edfd7093fbd2060176700b11e28`, the same for all three runs; 164 zips, missing: 2086F, 2101F, 2109B).
Slayer was judged separately on AMD EPYC 7B13 64-Core Processor, 30 vCPUs; see Deviations.

Raw outputs (with thinking, not committed): the LFM3-1.7B runs in `labaj-agency/out/coding-group/box/export.tgz`, sha256 `2bcf89771f031feb5fbae69617bcd5a60d2d73359c58cadf3c62e7ba218c51c6`; Bielik's in `out/bielik-11b-v3.1/generations.jsonl on the generating Mac`. Each run's generations.jsonl sha256 equals its result file's `raw_outputs.sha256` (results/raw-outputs.json).

No code extracted, `lfm3-1.7b`: a ```python block instead of C++: 4 (2096F, 2106F, 2113C, 2113E).

No code extracted, `lfm3-1.7b-nothink`: a `<tool_call>` instead of an answer: 3 (2097D, 2115C, 2118B); a ```python block instead of C++: 2 (2098A, 2118E); cut by the output limit inside the code: 1 (2118D1).

<!-- readme.py: end results -->

How the runs went (from `run.json` in each result's `provenance`):

- LFM3-1.7B, both modes: one shared vLLM 0.34.0 server on an NVIDIA H100 80GB; each mode first ran `--limit 20`,
  then the full set resumed it, all at our commit `8a48eb90` with a clean tree.
- Bielik: the 2-problem smoke run (2084A, 2084B) at `99534b5a` with uncommitted README edits, then the full set
  resumed it at `8a48eb90` with a clean tree; `lcbpro.py` is the same file in both (`runner_sha256`).
- Judging: all three on the scoring VM at `8a48eb90`, one after another. The second and third are marked
  `dirty: true` only because the first one's `summarize.py` had rewritten the tracked `results/manifest.json`.
- Re-summarized (PROTOCOL.md, Amendment 1, item 4): `summarize.py` ran again on the VM at `494a5c48` on the same
  `graded.jsonl` files to add the test-zip manifest; scores and verdicts are unchanged. The second and third files
  say `dirty: true` for the same reason as above (the first had rewritten `results/`).

## Hypotheses

<!-- readme.py: hypotheses (generated from results/ by readme.py; edit readme.py, not this block) -->

K1 control: passed: LFM3-1.7B 32.34 ± 3.62 vs card 31.74, z = +0.16

| test | value ± SE (pp) | z | one-sided p (support / refute) | verdict of this test alone | read |
|---|---|---|---|---|---|
| K2 | +1.80 ± 3.05 | -5.70 | 5.94e-09 / 1 | supported (clear) | yes |
| K3 | +11.68 ± 2.36 | +4.94 | 1 / 3.86e-07 | refuted (clear) | yes |
| K3 lead on − B (precondition z ≥ 3) | +30.54 ± 3.57 | +8.54 | | | |

Holm over the Coding group (m = 4: K2 and K3 here and in SciCode): not applied here; computed in research/api-benchmarks/coding-group/holm.json, once, from this benchmark's and SciCode's hypotheses.json as merged on main (PROTOCOL.md, Amendment 2).

K3 robustness (DESCRIPTIVE, added after the results; PROTOCOL.md Amendment 1):

| view | D ± SE (pp) | z | n |
|---|---|---|---|
| SE clustered by contest | +11.68 ± 2.63 | +4.44 | 26 contests |
| easy only (accepted on / off / Bielik: 52 / 48 / 3) | +21.13 ± 3.72 | +5.67 | 97 |
| medium only (accepted on / off / Bielik: 2 / 0 / 0) | -1.75 ± 1.23 | -1.43 | 57 |
| hard only (accepted on / off / Bielik: 0 / 0 / 0) | +0.00 ± 0.00 |  | 13 |

Sign test over contests: 17 with D > 0, 2 with D < 0, 7 with D = 0; one-sided binomial p = 0.00036.

Reading:

- **K2** (supported (clear)) compares Bielik through the API with a number on the card, not with a model run here: LFM2.5-2.6B's 19.16, with the SE floor of PROTOCOL.md.
- **K3** refuted under the pre-registered switch (`enable_thinking: false`): with the switch off LFM3 keeps most of its lead (D = +11.68 ± 2.36, z = +4.94); the switch does not remove reasoning (153/167 answers reason and close `</think>`), so how much of the lead thinking itself buys is undetermined. With the switch off the median answer has 93% of its characters before its last `</think>`, 46 of its 48 accepted answers close one, and it writes 24545 output tokens per answer on average (PROTOCOL.md, Amendment 1).
- **Holm over the Coding group** (PROTOCOL.md, Hypotheses) is not applied in this file, so each verdict above is the test's own. It needs SciCode's K2 and K3 as merged on main and is computed once, after both benchmarks are merged (PROTOCOL.md, Amendment 2). Holm can only raise a p, so a verdict there can weaken, not strengthen.

<!-- readme.py: end hypotheses -->

## Exploratory

<!-- readme.py: exploratory (generated from results/ by readme.py; edit readme.py, not this block) -->

**EXPLORATORY: added after the results were seen (PROTOCOL.md, Amendment 1); no verdict reads it.**

Accepted within an output budget (a problem counts only if it was accepted and its answer used at most B output tokens, thinking included):

| run | B = 4096 | B = 8192 | B = 16384 | B = 32768 | no limit | n |
|---|---|---|---|---|---|---|
| lfm3-1.7b | 2 | 7 | 17 | 43 | 54 | 167 |
| lfm3-1.7b-nothink | 5 | 12 | 22 | 40 | 48 | 167 |
| bielik-11b-v3.1 | 3 | 3 | 3 | 3 | 3 | 167 |

Compile errors by cause, from the judge's compiler message (explore.py: the compiler's own "did you forget to '#include'" note; else a first error naming an undeclared standard-library name from a fixed list; else other):

| run | compile errors | g++ names the missing header | a standard-library name used without its header | other (syntax, types, undefined own names) |
|---|---|---|---|---|
| lfm3-1.7b | 11 | 0 | 0 | 11 |
| lfm3-1.7b-nothink | 10 | 0 | 0 | 10 |
| bielik-11b-v3.1 | 59 | 11 | 10 | 38 |

Bielik's 59 compile errors re-judged with `#include <bits/stdc++.h>` and `using namespace std;` put before the code (rejudge.py): CE 40, WA 14, RE 5. Re-judged on AMD EPYC 7302P 16-Core Processor with 4 workers while another job shared the machine (official judging: 8 workers, idle machine), same image (`sha256:a04214fc3f8a…`) and test zips.

<!-- readme.py: end exploratory -->

## Deviations

- **The judge image is built from a copy of the pinned Dockerfile with two "latest" steps fixed to their versions
  of 2025-09-07**, the date of the pinned LightCPVerifier commit. On 2026-11-22 the pinned Dockerfile does not
  build: `npm install -g npm@latest` fetches npm 12, which refuses the image's Node 20 (EBADENGINE), and go-judge's
  latest release (v1.14.1) lists an init-binary tarball first, so the Dockerfile's asset selection unpacks a
  tarball without `go-judge`. The copy installs npm 11.6.0 and takes go-judge from the release `v1.9.6` (same
  asset selection, `go-judge_1.9.6_linux_amd64v2.tar.gz`), the "latest" of both on that date. The judge code and
  the checkout are unchanged; the judge finds the image by its name and does not rebuild it. Its id and go-judge's
  version are in every result (`settings.judge`). Effect: the sandbox is the one the authors' Dockerfile gave in
  September 2025 rather than an image of today.
- **The test zips are pinned without changing the judge.** `judge.py` calls `hf_hub_download` for `{pid}.zip`
  without a revision. `lcbpro.py tests` downloads each zip at the pinned revision into a Hugging Face cache of this
  benchmark's own (`.cache/hf`) and points the cached repository's `refs/main` at that revision; `lcbpro.py score`
  runs with `HF_HUB_OFFLINE=1` and refuses to start otherwise, so the judge's own call resolves to the pinned files.
  Problems without a zip at the pinned revision are never submitted and count as `no_tests`.
- **One split, at a pinned revision.** `benchmark.py` loads all splits of the dataset without a revision and
  generates for the union; we load `quater_2025_4_6` at the pinned revision, as PROTOCOL.md fixes.
- **Generation goes through an OpenAI-compatible chat endpoint, judging through the harness's judge class**, as
  `benchmark.py` does with its `LLMInterface`: the prompt comes from the harness's own `generate_solution`, the
  answer goes to `extract_longest_cpp_code` and the code to `LightCPVerifierJudge.submit`/`get_result`. Two things
  are ours: the text after the last `</think>` is extracted (PROTOCOL.md), and for a `Judge Failed` verdict the
  judge's `result.json` (`/result/<sid>`) is read to tell a compile error (`Error: compile failed: …`, the model's
  code) from an error of the judge itself (any other text, including `checker compile failed`).
  **Effect of the extraction**, measured after the results (rejudge.py, PROTOCOL.md Amendment 1): the harness's
  `benchmark.py` extracts from the whole answer. Its fence pattern needs ```` ```cpp ```` at the start of a line,
  so an answer that ends its reasoning with `</think>```cpp` loses that block and falls back to the `int main(`
  heuristic. Re-judging the whole-answer extraction of every answer whose code changes:

<!-- readme.py: extraction (generated from results/ by readme.py; edit readme.py, not this block) -->

| run | accepted, after the last `</think>` (official) | accepted, whole answer (the harness) | problems whose code changes | lost | gained | answers with `</think>` and a fence on the same line |
|---|---|---|---|---|---|---|
| lfm3-1.7b | 54 | 54 | 2 | none | none | 8 |
| lfm3-1.7b-nothink | 48 | 44 | 36 | 2086B, 2086C, 2094C, 2112B | none | 28 |
| bielik-11b-v3.1 | 3 | 3 | 1 | none | none | 0 |

Re-judged on AMD EPYC 7302P 16-Core Processor with 4 workers while another job shared the machine (official judging: 8 workers, idle machine), same image (`sha256:a04214fc3f8a…`) and test zips.

<!-- readme.py: end extraction -->

- **Retries.** A judge error that is not a compile error, or an exception while submitting, is submitted once more;
  if it persists it is `judge_error`. A request is retried with a shared pause (API: up to 30 attempts; vLLM: 3), a
  request still failing is tried once more at the end of the session, and then it stays `request_error`.
- **What PROTOCOL.md leaves open, decided here before any model output:**
  - "unfinished" applies only to thinking on (`lfm3-1.7b`), as PROTOCOL.md words it. For `lfm3-1.7b-nothink` and
    Bielik a length stop is judged like any other answer (what the harness would do) and counted as `length_stops`.
  - The secondary score leaves out `no_tests`, `judge_error`, `request_error` and `unsupported` (prompt over the
    context): all infrastructure outcomes, not the model's code.
  - K3 and its lead precondition use the headline 0/1 per problem over all 167 problems; the precondition reads
    the raw paired z (it is not one of the four tested hypotheses). Holm is applied separately to the four
    `p_support` (toward "supported") and the four `p_refute` (toward "refuted"); a test without a p (not run,
    precondition not met, other benchmark absent) stays in m = 4 with p = 1. While K1 has not passed, K2 and K3 are
    computed but marked `read: false`.
  - Judge workers: 8, the harness's `benchmark.py` default (its README asks for at most the physical cores), on
    the scoring VM (AMD EPYC 7302P, 16 cores, 30 vCPUs given to the VM), so each test runs on an idle core.
- **Bielik runs on the Fabryka AI API, with its hidden provider system prompt.** The API applies Bielik's chat
  template itself, with the system prompt of that template, and rejects `chat_template_kwargs`, so there is no
  reasoning switch through the API; some answers still close a short `</think>` draft before answering again
  (how many, and the share of characters before it, in Results). Its prompt is counted locally with Bielik's
  tokenizer and chat template at
  `d6e755d356ad418d0f0e30b8c428db267415ddb9` and 64 tokens are kept free for what the API's rendering adds, as in
  livecodebench-v6. The API's own prompt count equals ours in every answer (Results), so the margin was not needed;
  whether the API's system prompt carries a date is not visible from the counts.
- **Slayer 1B 1.09 at update 70 000** was run under Amendment 3 as a descriptive row (outside K1–K3 and Holm). The maintainer originally recorded a cost-decision `null` (Amendment 2); this run confirms that decision. It measured 0.00 (0/167 accepted, 167/167 no_code, 167/167 length stops). See `results/slayer1b-1.09-k70000.json` and PROTOCOL.md Amendment 3.
- **Contamination.** The 25Q2 problems and their editorials have been public since mid-2025, before LFM3-1.7B and
  Bielik v3.1 were trained; no contamination-free claim is made (PROTOCOL.md, Limits).
