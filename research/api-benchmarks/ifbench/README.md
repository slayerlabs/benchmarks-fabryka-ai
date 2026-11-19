# IFBench

Polish version: [README.pl.md](README.pl.md).

Whether a model follows new, harder verifiable output constraints ("use exactly 3 palindromes", "end every
sentence with a different punctuation mark") on real user prompts, checked by rules, without a judge model.

- Paper: [Pyatkin et al. 2025, Generalizing Verifiable Instruction Following](https://arxiv.org/abs/2507.02833)
- Harness: [allenai/IFBench](https://github.com/allenai/IFBench) @ `488918665d53f867fa908a293769ec6e71e74aec`
  (`generate_responses.py`, `run_eval`)
- Data: [allenai/IFBench_test](https://huggingface.co/datasets/allenai/IFBench_test) @
  `ed7c12452594b7028b15807b86d3938150b663ae`, 300 prompts (full set, single turn)
- Metric: prompt-level strict accuracy (`follow_all_instructions` in `eval_results_strict`); instruction-level and
  loose scores in `other_metrics`
- Settings: single turn, 1 trial. Bielik: temperature 0.6, top_p 0.95, up to 31,238 output tokens (LFM3-1.7B card
  defaults, see Deviations). Slayer: greedy, up to 1280 output tokens, raw prompt
- Extra services: none

## Results

| model | score | stderr | n | date |
|---|---|---|---|---|
| Bielik 11B v3.1, own vLLM (`bielik-11b-v3.1-vllm`) | 18.33 | 2.23 | 300 | 2026-11-19 |
| Slayer 1B, step 60000 (`slayer1b-60000`) | 8.33 | 1.60 | 300 | 2026-11-19 |
| LFM3-1.7B, model card | 73.03 | | | |

Against an empty answer (which follows no constraint here, so its score is 0), Bielik is 18.33 ± 2.23 points
higher (paired, z = 8.2). Slayer also passes that test (z = 5.2), but it does not beat other trivial answers:
repeating the prompt scores 13.00 (39/300), and Slayer's own outputs shuffled across prompts score the same 25/300
(McNemar p = 1.0). Read Slayer's 8.33 as a floor for degenerate output, not as instruction following. Each line of
`results/<model-id>.jsonl.gz` holds the task key, the 0/1 score, the per-instruction strict and loose flags, the
prompt and the raw `output`.

## Deviations

- **Self-hosted vLLM, not the fabryka.ai API.** Bielik 11B v3.1 Instruct
  ([speakleash/Bielik-11B-v3.1-Instruct](https://huggingface.co/speakleash/Bielik-11B-v3.1-Instruct) @
  `d6e755d356ad418d0f0e30b8c428db267415ddb9`, bfloat16) is served by vLLM 0.34.0 on a rented NVIDIA RTX PRO 5000
  Blackwell (`vllm.sh`), with the chat template's defaults, including the provider system prompt, and the date pinned to
  2026-11-18. This is the setup of the `-vllm` rows of the IFEval benchmark (#313), not the API row: on
  IFEval the two differed by about 5 points.
- **top_p is set on the server.** `generate_responses.py` sends only temperature, max_tokens and seed, so the card's
  top_p 0.95 is a server default (`--override-generation-config`), visible in vLLM's startup log.
- **Output limit 31,238 instead of "no limit".** The card gives no output limit; the served context is 32,768
  tokens, and the longest prompt of the set with the chat template is 1,530 tokens. No prompt was cut.
- **One seed for all requests.** `generate_responses.py` sends the same `seed` (20261119) with every request, so
  sampling is reproducible per prompt on the same server, but the prompts do not get independent seeds.
- **Data from Hugging Face, not the repo copy.** The pinned Hugging Face revision differs from the repo's bundled
  `data/IFBench_test.jsonl` in 2 of 300 prompts (keys 13 and 19); we use the Hugging Face version
  (`convert_hf.py`, which also turns float kwargs from parquet back into ints).
- **Requests are batched.** 32 requests at a time, batched by vLLM.
- **Slayer is a base model** without a chat template: it gets the raw prompt and decodes greedily up to 1280
  tokens, as in the IFEval benchmark (#313). Its context is 4096 tokens. Weights:
  [SlayerLab/Slayer1B-1.09-checkpoints](https://huggingface.co/SlayerLab/Slayer1B-1.09-checkpoints) @
  `dc3b6a9b0f87305da7ceca39ca27a79fa60b34cd`, `wagi_60000.pt` (training step 60000). It ran on a rented NVIDIA
  GeForce RTX 4090 in fp32 (TF32 off) with a KV cache, one prompt at a time (`slayer_lm.py`). 280 of 300 outputs
  stop at the 1280-token limit and 1 is empty. Its outputs were scored with the same `run_eval`.
- **Slayer model code.** `slayer_package.py` loads the checkpoint into the GPT class of the public trainer
  `train_gpt_ref_r24_2.py` (SlayerLab/Slayer1B-1.09 @ `58d8f359c1fdd887f1b7344ec52c5511c111f790`), with the
  tokenizer of SlayerLab/Slayer1B-1.08 @ `5f854a0cc7160594d54d1788d37a44e8ebabe16c`. The reported run used an
  earlier trainer revision whose model classes are identical in source; rebuilding the package with
  `slayer_package.py` gives bitwise-identical weights (202/202 tensors) and identical logits (max |Δ| = 0.0 on 3
  prompts) to the package used for these results.
- **Sample files in the harness.** The IFBench repo ships `eval/eval_results_{strict,loose}.jsonl` (294 rows, not
  ours); `run_eval` writes ours as `eval/<model-id>-eval_results_*.jsonl`, and only those are read.

## Reproduce

```bash
HF_TOKEN=hf_... bash vllm.sh                # one GPU with at least 48 GB; serves on 127.0.0.1:8000
bash run.sh bielik-11b-v3.1-vllm            # in another shell
bash run.sh slayer1b-60000                  # local CUDA GPU with at least 24 GB; downloads the public step-60000 weights
```

`--limit 5` runs only the first 5 prompts and writes to `out/limit/`. `BASE_URL` points `run.sh` at another
endpoint that serves the model as `bielik`.
