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

| model | score | stderr | n | date |
|---|---|---|---|---|
| Slayer 1B 1.08 (`slayer1b-1.08`) | 18.11 | 1.66 | 541 | 2026-11-19 |
| Slayer 1B 1.08, Modal A100 (`slayer1b-1.08-modal`) | 16.82 | 1.61 | 541 | 2026-11-19 |
| Bielik 11B v3.1 (`bielik-11b-v3.1`) | 55.27 | 2.14 | 541 | 2026-11-19 |
| Bielik 11B v3.1, own vLLM, template defaults (`bielik-11b-v3.1-vllm`) | 60.63 | 2.10 | 541 | 2026-11-19 |
| Bielik 11B v3.1, own vLLM, no provider prompt (`bielik-11b-v3.1-vllm-no-provider`) | 57.30 | 2.13 | 541 | 2026-11-19 |
| LFM3-1.7B, own vLLM, reference (`lfm3-1.7b`) | 94.64 | 0.97 | 541 | 2026-11-19 |

The main row for Bielik is the API run. The two vLLM rows test the hidden prompt, and the LFM3-1.7B row checks
our setup against the LFM3-1.7B card (see Deviations, "Main metric").

## Deviations

- **Slayer runs on a local GPU, not through the API.** Slayer 1B 1.08 is not listed at `https://fabryka.ai/v1/models`.
  Weights: [SlayerLab/Slayer1B-1.08](https://huggingface.co/SlayerLab/Slayer1B-1.08) @
  `ea0945b11153e67517b70d21192e6076d161f658`, bfloat16, loaded through `research/common/slayer_lm.py`.
- **Slayer is a base model** (not instruction-tuned), with no chat template: it gets the raw IFEval prompt.
  It does not follow the instructions: it repeats the prompt or one sentence until the 1280-token limit. Its
  18.11 comes mostly from rules such output passes by accident. Of its 98 passing prompts, 44 outputs repeat the
  prompt (e.g. 1072, "400 or more words", passes with the prompt repeated), and the most frequent passing rules are
  `no_comma` (16), `number_highlighted_sections` (14), `title` (12) and `number_sentences` (11). Read the score
  as a floor for degenerate output, not as instruction following.
- **Slayer decodes greedily, up to 1280 tokens** (the `ifeval` task default). `SlayerLM.generate` supports only
  greedy decoding, and its context is 4096 tokens.
- **Greedy Slayer output depends on the GPU.** The same command on a Modal A100-80GB (`modal run modal_ifeval.py
  --model slayer1b-1.08`) instead of the local RTX 50xx gives identical outputs for 346 of 541 prompts; the rest
  diverge after a median of 134 characters, likely from bfloat16 rounding that flips a near tie in the argmax.
  Score 16.82 against 18.11: -1.29 ± 0.66 points (paired SE; 10 prompts pass only locally, 3 only on Modal). Treat
  differences of about 1.5 points between Slayer runs on different hardware as noise.
- **Slayer generates in batches.** `slayer_lm` runs a separate forward for each row of a batch, about 45 s per
  prompt here (6.8 h for the set). `lm_eval_slayer.py` replaces only its `generate` with one forward per step
  for the whole batch (masked left padding, per-row RoPE positions), batch 32. `check_batched.py` shows the same
  greedy tokens as `slayer_lm` on the first 16 prompts (400 tokens, bfloat16; 8 prompts in float32), 15x faster.
- **Two request fixes for the API.** lm-eval 0.4.9.1 sends `"type": "text"` in every chat message and
  `"stop": []`; the Fabryka API rejects both with 400. `lm_eval_fabryka.py` drops them and is otherwise the stock
  `lm_eval` CLI. The prompt text and sampling settings are unchanged.
  It also limits the load on the API: 2 requests at a time, and after any failed request all requests pause
  (10 s, doubling up to 5 minutes while failures continue), with up to 30 retries per prompt.
- **Thinking is cut off before scoring.** Bielik sometimes writes its reasoning into the answer and ends it with
  `</think>`. The Fabryka API rejects every switch that turns thinking off (`chat_template_kwargs`,
  `reasoning_effort`, `reasoning`: 400). `task/utils.py` scores only the text after the last `</think>`, as with
  an API that returns reasoning in a separate field; a response without `</think>` is scored unchanged. Each line
  of `results/<model-id>.jsonl.gz` holds the raw `output` and the `scored_output`.
  In the full run 9 of 541 Bielik responses hold `</think>`. In 2 of them (1436, 3109) the answer comes before
  `</think>` and only a comment on it after; both fail either way. Scoring the raw responses instead gives 298
  passes, not 299: 55.08 instead of 55.27, well within the stderr.
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
  The prompt changes the answer language. By the heuristic in `compare.py`, 44.5% of API answers and 39.7% of
  vLLM answers with the prompt are in Polish, against 8.7% without it (the IFEval prompts are in English). The
  score of Polish and non-Polish answers differs by at most 2.2 points in each run.
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

`--limit 5` runs only 5 prompts. The lm-eval output goes to `out/` (not committed).

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