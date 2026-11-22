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
  message of ours; LFM3-1.7B gets its template's default system prompt, Bielik whatever the API adds), temperature
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
| K1-K3 | anywhere | `python3 compare.py results --group ../scicode/results/hypotheses.json` |

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

| model | how it runs | thinking | output limit | score | stderr | n | date |
|---|---|---|---|---|---|---|---|
| LFM3-1.7B (`lfm3-1.7b`) | vLLM 0.34.0, bf16, context 262144 | on (template default) | context − prompt | | | | |
| LFM3-1.7B (`lfm3-1.7b-nothink`) | the same server, `enable_thinking: false` | off | context − prompt | | | | |
| Bielik 11B v3.1 (`bielik-11b-v3.1`) | Fabryka AI API, context 32768, with the API's provider system prompt | none (the API has no switch) | 32768 − prompt − 64 | | | | |
| Slayer 1B 1.09 at update 70 000 (`slayer1b-1.09-k70000`) | not run (PROTOCOL.md, Models) | | | null | | | |

No model has been run yet. The smoke tests of this harness (2 problems, not results) are described in the PR.

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
  template itself (with a provider system prompt that carries the live date) and rejects `chat_template_kwargs`, so
  Bielik answers without thinking. Its prompt is counted locally with Bielik's tokenizer and chat template at
  `d6e755d356ad418d0f0e30b8c428db267415ddb9` and 64 tokens are kept free for what the API's rendering adds, as in
  livecodebench-v6; `api_prompt_minus_local` in the result checks it.
- **Slayer 1B is not run**: a base model with a 4096-token context that does not follow chat instructions; on 30
  Python tasks (`research/slayer-1b/rozmowy-1.08`) it wrote no function that passed its tests, so olympiad problems
  in C++ are below its floor (PROTOCOL.md, Models). Its result file is `score: null` with that reason.
- **Contamination.** The 25Q2 problems and their editorials have been public since mid-2025, before LFM3-1.7B and
  Bielik v3.1 were trained; no contamination-free claim is made (PROTOCOL.md, Limits).
