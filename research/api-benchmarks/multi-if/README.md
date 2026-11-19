# Multi-IF

Polish version: [README.pl.md](README.pl.md).

Whether a model keeps following instructions over a three-turn conversation in eight languages: each turn adds
IFEval-style instructions (length, format, keywords, language, ...) on top of the earlier ones, and every turn's
answer is checked by the harness's rule-based verifiers, without a judge model.

- Paper: [Multi-IF: Benchmarking LLMs on Multi-Turn and Multilingual Instructions Following](https://arxiv.org/abs/2410.15553)
- Harness: [facebookresearch/Multi-IF](https://github.com/facebookresearch/Multi-IF) @
  `1cdb53ed18499ad729e0766e5d3099dd5344406f` (`multi_turn_instruct_following_eval_api.py`, `metrics.py`), with
  `patch_api_client.py` (see Deviations)
- Data: [facebook/Multi-IF](https://huggingface.co/datasets/facebook/Multi-IF) @
  `0ab97ce0b45c7f57772e8ba2ac1616f4b00bd3aa`, `multiIF_20241018.csv` (sha256
  `6c588af031fe67b17c535b9ba0ccc14a1b9d77b4faf88c294f83aaa5a3000018`): 4501 conversations; 4501 have a second
  turn and 4445 a third, so 13,447 scored turns
- Metric: per turn, the harness's `all_languages_overall` (mean of prompt-level strict, instruction-level strict,
  prompt-level loose and instruction-level loose over all languages); the score is the mean over the three turns,
  as in the paper's Fig. 1 ("average ... across all languages and across all turns"). Per-turn values, the four
  components and per-language results are in `other_metrics`
- Settings: three turns, 1 trial. Bielik: temperature 0.6, top_p 0.95, seed 20261119, up to 8192 new tokens per
  turn. Slayer: greedy, up to 1280 new tokens per turn, raw text
- Extra services: none

## Results

| model | score | stderr | n | date |
|---|---|---|---|---|
| Bielik 11B v3.1, own vLLM (`bielik-11b-v3.1-vllm`) | 48.66 | 0.44 | 13447 | 2026-11-19 |
| Slayer 1B, step 60000 (`slayer1b-60000`) | null | null | 0 | 2026-11-19 |
| LFM3-1.7B, model card | 89.10 | | | |

`n` counts scored turns; `n_conversations` in the results files is 4501.

Bielik's overall falls with each turn: 62.21, 46.32 and 37.44 for turns 1 to 3; prompt-level strict falls from
56.39 to 29.95 and 15.28, while instruction-level strict stays between 64.33 and 56.54. All 13,447 requests got an
answer (no turn scored as failed).
By language, turn 1 ranges from 68.78 (English) to 54.03 (Russian).

Trivial answers do not score 0 here: repeating the turn's instruction scores 28.73 prompt-level strict in turn 1,
the model's own answers shuffled across conversations of the same language 10.89, and an empty answer 0.00.
Bielik's 56.39 is above all three (McNemar against the shuffled answers: p below 1e-160 in each of the three turns).

Slayer has no score: the run was stopped after 2 of 3 turns for compute budget (turn 3 ran at about 10 conversations
per minute), so `results/slayer1b-60000.json` has `score: null` and no `.jsonl.gz`. Its `other_metrics` copy the
all-languages and per-language overall of turns 1 and 2 from the metric files the harness wrote during the run (turn 1:
23.65, turn 2: 15.82). They are harness values, not re-scored: the one failed request in turn 2 is scored as the harness
does, not as an empty answer. There is no trivial-answer comparison for the stopped run.

Each line of `results/<model-id>.jsonl.gz` holds one scored turn: the conversation key, turn, language, the strict
and loose verdicts per instruction, whether the turn was scored as failed because a request failed, and the raw
`output`.

## Deviations

- **Turn aggregation.** The LFM3-1.7B card reports one Multi-IF number and does not state how turns are
  aggregated. We use the mean over the three turns of the harness's `all_languages_overall`, the aggregate of the
  paper's Fig. 1; the per-turn values are in `other_metrics`.
- **Failed requests are scored as failed.** A turn whose request failed (harness status other than `success`) has
  no model answer, and the harness would score its error text. `summarize.py` scores that turn and the later turns
  of the same conversation with an empty answer, i.e. as failed, in the full N, and counts them per turn. The 56
  conversations without a third turn have no turn-3 request (the harness marks the row `exception`) and are outside
  turn 3's N, as in `metrics.py`.
- **Standard error.** Turns of one conversation are not independent, so the stderr comes from a cluster bootstrap
  over conversations (all three turns together), 1000 resamples, seed 20261119.
- **Scoring is not fully deterministic.** The harness's language checks call `langdetect.detect`, and nothing in
  the harness at the pinned commit sets `DetectorFactory.seed`, which langdetect needs for repeatable results.
  Re-scoring the same answers with the harness's `metrics.py` moved turn scores by up to 0.013 points against the
  metric files the harness wrote during the run (Bielik: 62.212 / 46.307 / 37.432).
- **Self-hosted vLLM, not the fabryka.ai API.** Bielik 11B v3.1 Instruct
  ([speakleash/Bielik-11B-v3.1-Instruct](https://huggingface.co/speakleash/Bielik-11B-v3.1-Instruct) @
  `d6e755d356ad418d0f0e30b8c428db267415ddb9`, bfloat16) is served by vLLM 0.34.0 on a rented NVIDIA RTX PRO 5000
  Blackwell (`vllm.sh`), with the chat template's defaults, including the provider system prompt, and the date pinned to
  2026-11-18. This is the setup of the `-vllm` rows of the IFEval benchmark (#313), not the API row.
- **Output limit 8192 per turn instead of "no limit".** The harness sends one fixed `max_new_tokens` for every
  turn; the card gives no limit. With 8192, three answers take at most 24,576 of the 32,768-token context.
- **Patched API client.** `patch_api_client.py` makes two edits to the harness's `api_client.py`: the Anthropic,
  Gemini and Mistral libraries are imported inside their own backends (the Gemini and Mistral packages conflict with
  the vLLM environment), and `bielik` and `slayer` are added to the model names of the OpenAI-compatible backend.
  No backend's behaviour changes. `run.sh` points that backend at the local server (`OPENAI_BASE_URL`,
  `OPENAI_API_KEY=EMPTY`).
- **Slayer is a base model** without a chat template and a 4096-token window: `slayer_server.py` joins the
  conversation as "User: ... Assistant: ..." text and decodes greedily up to 1280 tokens per turn. A turn whose
  input plus 1280 tokens does not fit in 4096 is rejected (HTTP 400) and scored as failed, with the later turns of
  the conversation. Weights: [SlayerLab/Slayer1B-1.09-checkpoints](https://huggingface.co/SlayerLab/Slayer1B-1.09-checkpoints)
  @ `dc3b6a9b0f87305da7ceca39ca27a79fa60b34cd`, `wagi_60000.pt`, loaded by `slayer_package.py` into the GPT class of
  the public trainer `train_gpt_ref_r24_2.py`; rebuilding the package with `slayer_package.py` gives
  bitwise-identical weights (202/202 tensors) and identical logits (max |Δ| = 0.0 on 3 prompts) to the package
  used for these results. It ran on a rented NVIDIA GeForce RTX 4090 in fp32 (TF32 off) with a KV cache, 32
  requests per batch (`slayer_batch.py`).
- **Requests are batched.** 32 conversations at a time (`--max_workers 32`), batched by the server.

## Reproduce

```bash
HF_TOKEN=hf_... bash vllm.sh                # one GPU with at least 48 GB; serves on 127.0.0.1:8000
bash run.sh bielik-11b-v3.1-vllm            # in another shell
bash run.sh slayer1b-60000                  # one CUDA GPU with at least 24 GB; starts slayer_server.py itself
```

`--limit 5` keeps only the first 5 conversations (all their turns) and writes to `out/limit/`. `BASE_URL` points
`run.sh` at another endpoint that serves the model as `bielik`. `requirements.txt` pins the harness environment.
