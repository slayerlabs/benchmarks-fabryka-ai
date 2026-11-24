# IFStruct

Whether a model produces valid JSON or YAML that matches a target schema: the right format and fences, no extra
commentary, the asked top-level shape and item count, and every field valid against the schema. Checked by the
harness's validator, without a judge model.

- Harness: [Liquid4All/ifstruct](https://github.com/Liquid4All/ifstruct) @ `73e03a6d3a8508357ba430675a106d4887abedf3`
  (`ifstruct-eval`)
- Data: [LiquidAI/ifstruct-v1.0](https://huggingface.co/datasets/LiquidAI/ifstruct-v1.0) @
  `2e342ca5f2673fb1287411fdbadcdfde82b35682`, 2000 samples (full set: 1000 JSON, 1000 YAML)
- Metric: pass rate (a sample passes only if the validator reports no error); pass rates by format in
  `other_metrics`
- Settings: single turn, 1 trial. Bielik: temperature 0.6, top_p 0.95, up to 29603 output tokens (LFM3-1.7B card
  defaults, see Deviations). Slayer: greedy, up to 1280 output tokens, raw text
- Extra services: none

## Results

| model | score | stderr | n | date |
|---|---|---|---|---|
| Bielik 11B v3.1, own vLLM (`bielik-11b-v3.1-vllm`) | 30.95 | 1.03 | 2000 | 2026-11-19 |
| Slayer 1B, step 60000 (`slayer1b-60000`) | 0.00 | 0.00 | 2000 | 2026-11-19 |
| LFM3-1.7B, model card | 93.72 | | | |

Against an empty answer (which never passes the validator, so its score is 0), Bielik is 30.95 ± 1.03 points
higher (paired, z = 29.9). All 1381 failures are validation errors of the output, none are request errors; the most
common is a missing code block where the prompt asks for one (651). Each line of `results/<model-id>.jsonl.gz` holds
the sample seed, the 0/1 score, format, entity type, the validator's errors and the raw `output`; the prompt is not stored (look it up in the dataset by seed).

Slayer passes none of the 2000 samples (JSON 0/1000, YAML 0/1000), the same as an empty answer, so it cannot be
told apart from a trivial answer here. The base model under raw prompting runs to the 1280-token limit (2203 of
its 2216 server generations, retries included) and never produces a valid object; the most common validator errors
are missing required fields and a string where an object is expected. All 2000 samples got an answer (no request
error after retries, none outside the model's 4096-token window: the longest prompt is 1975 tokens).

## Deviations

- **Self-hosted vLLM, not the fabryka.ai API.** Bielik 11B v3.1 Instruct
  ([speakleash/Bielik-11B-v3.1-Instruct](https://huggingface.co/speakleash/Bielik-11B-v3.1-Instruct) @
  `d6e755d356ad418d0f0e30b8c428db267415ddb9`, bfloat16) is served by vLLM 0.34.0 on a rented NVIDIA RTX PRO 5000
  Blackwell (`vllm.sh`), with the chat template's defaults, including the provider system prompt, and the date pinned to
  2026-11-18. This is the setup of the `-vllm` rows of the IFEval benchmark (#313), not the API row: on
  IFEval the two differed by about 5 points.
- **The LFM3-1.7B card's sampling, not Bielik's own.** Bielik runs with the sampling the LFM3-1.7B card uses for
  its evaluations unless it lists an exception (temperature 0.6, top_p 0.95), because the protocol, fixed before the
  runs, compares every model with the card's table under the card's settings. The Bielik model card gives no
  evaluation settings; it sets only temperature 0.3 for its hosted inference widget. A run with Bielik's own settings
  would be a separate row with its own label.
- **top_p is set on the server.** `ifstruct-eval` sends only temperature and max_tokens, so the card's top_p 0.95
  is a server default (`--override-generation-config`), visible in vLLM's startup log. The harness has no seed
  option, so requests are not seeded.
- **Output limit 29603 instead of "no limit".** The card gives no output limit; the served context is 32768
  tokens, and the longest prompt of the set with the chat template is 3165 tokens. No prompt was cut.
- **Data from Hugging Face.** The pinned revision is identical to the repo's bundled `data/test.jsonl` (0 of 2000
  samples differ); `convert_hf.py` turns the parquet's JSON-string columns back into objects.
- **Requests are batched.** Bielik: 32 requests at a time, batched by vLLM; the harness retries a failed request
  twice. No request failed.
- **Slayer is a base model** without a chat template: `slayer_server.py` passes the prompt as raw text and
  decodes greedily up to 1280 tokens whatever `max_tokens` asks (the harness sends 4096), as in the IFEval
  benchmark (#313). Weights: [SlayerLab/Slayer1B-1.09-checkpoints](https://huggingface.co/SlayerLab/Slayer1B-1.09-checkpoints)
  @ `dc3b6a9b0f87305da7ceca39ca27a79fa60b34cd`, `wagi_60000.pt`, loaded by `slayer_package.py` into the GPT class of
  the public trainer `train_gpt_ref_r24_2.py`; rebuilding the package with `slayer_package.py` gives
  bitwise-identical weights (202/202 tensors) and identical logits (max |Δ| = 0.0 on 3 prompts) to the package
  used for these results. It ran on a rented NVIDIA GeForce RTX 4090
  in fp32 (TF32 off) with a KV cache, 32 requests per batch (`slayer_batch.py`), 32 harness threads.
- **Slayer serving code** (`slayer_server.py`, `slayer_batch.py`, `slayer_kv_lm.py`, `slayer_package.py`) lives in
  [`research/common/slayer_serving/`](../../common/slayer_serving/). The results were produced with byte-identical
  copies kept in this directory before the move; the shared README lists their hashes.
- **Slayer client timeouts.** At 32 threads a 1280-token answer takes about 85 s on average; 216 requests hit the
  harness's 120 s read timeout and 1 a reset connection, and each was retried once and answered. The server decodes
  greedily, and for each of the 216 prompts it generated twice, both generations have the same length and stop
  reason.

## Reproduce

```bash
HF_TOKEN=hf_... bash vllm.sh                # one GPU with at least 48 GB; serves on 127.0.0.1:8000
bash run.sh bielik-11b-v3.1-vllm            # in another shell
bash run.sh slayer1b-60000                  # one CUDA GPU with at least 24 GB; starts slayer_server.py itself
```

`--limit 5` runs only the first 5 samples and writes to `out/limit/`. `BASE_URL` points `run.sh` at another
endpoint that serves the model as `bielik`.
