# IFEval

Whether a model follows verifiable instructions in a prompt ("write at least 300 words", "no commas", "wrap the
answer in JSON"), checked by rules, without a judge model.

- Paper: [Zhou et al. 2023, Instruction-Following Evaluation for Large Language Models](https://arxiv.org/abs/2311.07911)
- Harness: [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) v0.4.9.1, task `ifeval`
  (the authors' rule code, ported)
- Data: [google/IFEval](https://huggingface.co/datasets/google/IFEval) @ `966cd89545d6b6acfd7638bc708b98261ca58e84`,
  541 prompts (full set)
- Metric: `prompt_level_strict_acc` (see Deviations)
- Settings: single turn, 1 trial. Bielik: temperature 0.6, top_p 0.95, up to 30720 output tokens (LFM3-1.7B card
  defaults). Slayer: greedy, up to 1280 output tokens (see Deviations)
- Extra services: none

## Results

| model | how it runs | score | stderr | n | date |
|---|---|---|---|---|---|
| Slayer 1B 1.08 (`slayer1b-1.08`) | local RTX 50xx, bf16, greedy, batch 32 | 18.11 | 1.66 | 541 | 2026-11-19 |
| Slayer 1B 1.08 (`slayer1b-1.08-modal`) | Modal A100, otherwise the same | 16.82 | 1.61 | 541 | 2026-11-19 |
| Bielik 11B v3.1 (`bielik-11b-v3.1`) | Fabryka API, temperature 0.6, top_p 0.95 | 55.27 | 2.14 | 541 | 2026-11-18 |
| Bielik 11B v3.1 (`bielik-11b-v3.1-vllm`) | vLLM 0.11.0 on A100, template defaults, same sampling | 60.63 | 2.10 | 541 | 2026-11-19 |
| Bielik 11B v3.1 (`bielik-11b-v3.1-vllm-no-provider`) | as above, no provider system prompt | 57.30 | 2.13 | 541 | 2026-11-19 |
| LFM3-1.7B (`lfm3-1.7b`) | vLLM 0.34.0, bf16, card settings, reasoning on | 94.64 | 0.97 | 541 | 2026-11-19 |

The main row for Bielik is the API run. The two vLLM rows test the hidden prompt, and the LFM3-1.7B row checks
our setup against the LFM3-1.7B card (see Deviations, "Main metric"). Rows with a different setup are not
interchangeable: compare Bielik with Bielik only through the paired differences below.

IFEval also has a central-run task, [T36 (`research/benchmarks/ifeval/`)](../../benchmarks/ifeval/README.md), on
the same dataset revision. T36 runs Slayer in float32 with batch 1 through `common/ewaluuj.py`; this directory
runs it in bf16 with a batched forward. Do not treat a Slayer number from here and one from T36 as the same
measurement. T36 has no results yet.

## Deviations

- **Slayer runs on a local GPU, not through the API.** Slayer 1B 1.08 is not listed at `https://fabryka.ai/v1/models`.
  Weights: [SlayerLab/Slayer1B-1.08](https://huggingface.co/SlayerLab/Slayer1B-1.08) @
  `ea0945b11153e67517b70d21192e6076d161f658`, bfloat16, loaded through `research/common/slayer_lm.py`.
- **Slayer is a base model** (not instruction-tuned), with no chat template: it gets the raw IFEval prompt.
  It mostly does not follow the instructions, and its output runs to the 1280-token limit: only 11 of 541
  outputs stop under 200 words. In the local run, 143 outputs repeat the prompt, and 92 open a `<think>` block
  written in Polish, like a chat model's reasoning; 26 of them close it and answer after it, often in Polish. Most
  of the rest repeat one sentence or list line (for example, 1098: "The name of God is:" numbered over and over).
  Many passes are accidental. Of the 98 passing prompts, 45 repeat the prompt (for example, 1072, "400 or more
  words"), and the rules passed most often are `no_comma` (16), `number_highlighted_sections` (14), `title` (12),
  and `number_sentences` (11). Read 18.11 as the score of mostly degenerate output, not as instruction following.
- **Slayer decodes greedily, up to 1280 tokens** (the `ifeval` task default). `SlayerLM.generate` supports only
  greedy decoding, and its context is 4096 tokens.
- **Greedy Slayer output depends on the GPU.** The same command on a Modal A100-80GB (`modal run modal_ifeval.py
  --model slayer1b-1.08`) instead of the local RTX 50xx gives identical outputs for 346 of 541 prompts; the rest
  diverge after a median of 134 characters, likely from bfloat16 rounding that flips a near tie in the argmax.
  Score 16.82 against 18.11: -1.29 ± 0.66 points (paired SE; 10 prompts pass only locally, 3 only on Modal). Treat
  differences of about 1.5 points between Slayer runs on different hardware as noise.
- **Slayer generates in batches.** `slayer_lm` runs a separate forward for each row of a batch, about 45 s per
  prompt here (6.8 h for the set). `lm_eval_slayer.py` replaces only its `generate` with one forward per step
  for the whole batch (masked left padding, per-row RoPE positions), batch 32, about 15x faster.
  `check_batched.py` compares it with `slayer_lm` on the first 16 prompts, up to 1280 tokens each, with the input
  laid out as lm-eval passes it. In float32 both give the same greedy tokens on all 16 prompts on a Modal A100
  (and on the first 5 on the local RTX 50xx). In bfloat16 the batch changes the matrix kernels and so the rounding:
  locally 15 of 16 match (prompt 4 diverges at token 481), on the A100 12 of 16 (prompts 0, 11, 12 and 15 diverge
  at tokens 2, 13, 14 and 185). This is the same near-tie effect as between GPUs (above), not a different model.
- **Two request fixes for the API.** lm-eval 0.4.9.1 sends `"type": "text"` in every chat message and
  `"stop": []`; the Fabryka API rejects both with 400. `lm_eval_fabryka.py` drops them and is otherwise the stock
  `lm_eval` CLI. The prompt text and sampling settings are unchanged.
  It also limits the load on the API: 2 requests at a time, and after any failed request all requests pause
  (10 s, doubling up to 5 minutes while failures continue), with up to 30 retries per prompt.
- **Thinking is cut off before scoring, for every model.** Bielik sometimes writes its reasoning into the answer
  and ends it with `</think>`. The Fabryka API rejects every switch that turns thinking off (`chat_template_kwargs`,
  `reasoning_effort`, `reasoning`: 400). `task/utils.py` scores only the text after the last `</think>`, as with
  an API that returns reasoning in a separate field; a response without `</think>` is scored unchanged. The task
  applies this to all models, not only Bielik. Each line of `results/<model-id>.jsonl.gz` holds the raw `output`
  and the `scored_output`. Responses with `</think>`, and the score of the raw responses:
  - Bielik, API: 9 of 541. In 2 of them (1436, 3109) the answer comes before `</think>` and only a comment on it
    after; both fail either way. Raw: 298 passes instead of 299, 55.08 instead of 55.27.
  - Slayer: 26 of 541 locally, 27 on Modal. Raw: 99 passes instead of 98 locally (18.30 instead of 18.11), 94
    instead of 91 on Modal (17.38 instead of 16.82).
  - Bielik on vLLM: none. LFM3-1.7B: all 541, see "Main metric".

  Each change is well within the stderr.
- **Scoring is not fully deterministic.** The lm-eval 0.4.9.1 rules use randomness in two places, and nothing
  seeds it:
  - The 31 prompts with a `language:response_language` rule call `langdetect`, whose result can change between
    runs on the same text.
  - Prompts 1122 and 1129 ask for a count of `#` and `!`. The `letter_frequency` rule accepts only a to z, so for
    these two it checks a randomly chosen letter instead.

  The published scores come from the scoring pass of each run. Rescoring the saved outputs with 10 seeds moves a
  score by at most 3 prompts (LFM3-1.7B: 510 to 513 passes, 0.55 points), well within the stderr. We keep the
  published scores until the repository settles on a seeding policy shared with T36; the saved outputs can then
  be rescored without running the models again.
- **The API adds a hidden prompt.** A one-sentence user message is billed as about 1065 prompt tokens. The text
  comes from Bielik's official chat template: by default it adds a provider system prompt (in Polish, with the
  current date), and the API rejects `chat_template_kwargs`, so it cannot be turned off there.
  To measure its effect we served the same weights with vLLM 0.11.0 on a rented A100 (`vllm.sh`, run through
  `modal_ifeval.py`), same task and sampling settings, date pinned to the API run day, in two runs:
  - **template defaults** (`bielik-11b-v3.1-vllm`): 60.63. That is 5.36 ± 1.86 points above the API run
    (paired SE, 66 prompts pass only here, 37 only on the API). So our vLLM setup does not reproduce the API
    exactly; the cause is unknown (serving settings, quantization or template version on the API side). The API
    run also has 9 responses with `</think>`; the vLLM runs have none.
  - **`provider_system_prompt=false`** (`bielik-11b-v3.1-vllm-no-provider`): 57.30, 3.33 ± 2.06 points below
    the run with the prompt (paired SE, z = -1.6). The difference is within noise: the hidden prompt does not
    lower the IFEval score.
  The prompt changes the answer language. By the heuristic in `compare.py`, 39.0% of API answers and 34.2% of
  vLLM answers with the prompt are in Polish, against none without it (the IFEval prompts are in English). On
  the API, Polish and other answers score the same (55.5 and 55.2). On vLLM with the prompt, Polish answers score
  55.7 and the rest 63.2 (-7.5 ± 4.5, z = -1.7, not significant; the two groups are different prompts, so this
  is not a clean effect of the language).
  `python compare.py bielik-11b-v3.1-vllm bielik-11b-v3.1 bielik-11b-v3.1-vllm-no-provider` prints these numbers.
- **Main metric.** The LFM3-1.7B card does not say which IFEval metric it reports. We report
  `prompt_level_strict_acc` and give the other three (`inst_level_strict_acc`, `prompt_level_loose_acc`,
  `inst_level_loose_acc`) in `other_metrics` of each result file.
  To find the card's metric we ran LFM3-1.7B itself (`lfm3.sh`: vLLM 0.34.0, bf16, temperature 0.6, top_p 0.95,
  reasoning on, the template's default system prompt, as in the card's "Evaluation details"). The card reports
  96.66. Our four metrics, with the distance from 96.66 in SE of our run:

  | metric | score | SE | minus card |
  |---|---|---|---|
  | `prompt_level_strict_acc` | 94.64 | 0.97 | -2.02 (z = -2.1) |
  | `inst_level_strict_acc` | 96.40 | 0.65 | -0.26 (z = -0.4) |
  | `prompt_level_loose_acc` | 96.49 | 0.79 | -0.17 (z = -0.2) |
  | `inst_level_loose_acc` | 97.72 | 0.52 | +1.06 (z = 2.0) |
  | mean of the four | 96.31 | | -0.35 |

  The instruction-level SE treats the 834 instructions as independent, so it is too small. Three readings match
  the card within noise: `prompt_level_loose_acc`, `inst_level_strict_acc` and the mean of the four. The card
  probably does not report `prompt_level_strict_acc` (z = -2.1), but one run at temperature 0.6 cannot single out
  one of the other three. The card has no output limit; we used 32768 tokens, and all 541 responses ended their
  reasoning with `</think>` before it (longest response: 75914 characters).

## Reproduce

```bash
export FABRYKA_API_KEY=...
bash run.sh bielik-11b-v3.1
bash run.sh slayer1b-1.08      # local CUDA GPU
```

`--limit 5` runs only 5 prompts and writes its summary to `out/<model-id>/<model-id>-limit5.*`, not to `results/`,
so a smoke test does not replace a published result. The lm-eval output goes to `out/` (not committed). The
`date` in a result file is the day the run started (local time of the machine that ran `summarize.py`).

The two vLLM runs need a GPU with at least 40 GB and a Hugging Face token with access to the gated
`speakleash/Bielik-11B-v3.1-Instruct`. On [Modal](https://modal.com) (about 10 minutes on an A100-80GB with the weights cached):

```bash
uv tool install modal && modal setup
modal secret create huggingface HF_TOKEN=hf_...
modal run modal_ifeval.py --limit 5    # smoke test
modal run modal_ifeval.py
```

On any other GPU machine: `HF_TOKEN=hf_... bash vllm.sh`. Slayer on Modal: `modal run modal_ifeval.py --model
slayer1b-1.08` (about 10 minutes, written as `results/slayer1b-1.08-modal.*`). LFM3-1.7B: `modal run
modal_ifeval.py --model lfm3-1.7b`, or `bash lfm3.sh` on any GPU machine (no token needed).