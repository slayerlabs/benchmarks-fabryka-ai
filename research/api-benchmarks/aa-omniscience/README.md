# AA-Omniscience (public)

Whether a model knows facts across six domains and, when it does not, says so instead of guessing. A judge model
grades each short answer as correct, partially correct, incorrect or not attempted; the Omniscience Index rewards
correct answers and penalizes incorrect ones, so abstaining scores better than a wrong guess.

- Paper: [AA-Omniscience: Evaluating Cross-Domain Knowledge Reliability in Large Language Models](https://huggingface.co/datasets/ArtificialAnalysis/AA-Omniscience-Public)
  (Artificial Analysis; PDF in the dataset repo)
- Harness: the answer prompt and grader template from the dataset README (`OMNISCIENCE_ANSWER_PROMPT`,
  `OMNISCIENCE_GRADER_TEMPLATE`), cut verbatim by `prepare.py`; `generate.py` asks the model, `judge.py` grades
- Data: [ArtificialAnalysis/AA-Omniscience-Public](https://huggingface.co/datasets/ArtificialAnalysis/AA-Omniscience-Public)
  @ `e4883edbb9f5ccf2b2a8fdc6fb65e01a58e99849`, 600 questions (full public set, 6 domains x 100)
- Metric: Omniscience Index, OI = 100 (correct - incorrect) / N; accuracy, hallucination rate
  (incorrect / all not-correct) and the grade counts in `other_metrics`
- Settings: single turn, 1 trial, one judge pass. Bielik: temperature 0.6, top_p 0.95, no output limit other than the
  context (LFM3-1.7B card defaults). Slayer: greedy, up to 1280 output tokens, raw text
- Extra services: a judge model (see Deviations)

## Results

| model | score | stderr | n | date |
|---|---|---|---|---|
| Bielik 11B v3.1, own vLLM (`bielik-11b-v3.1-vllm`) | -77.33 | 2.58 | 600 | 2026-11-19 |
| Slayer 1B, step 60000 (`slayer1b-60000`) | -59.33 | 2.14 | 600 | 2026-11-19 |
| LFM3-1.7B, model card | 0.50 | | | |

**The judge is not the official grader.** AA-Omniscience is graded by Gemini 2.5 Flash Preview (09-2025); our grades
come from GPT-6.1 Sol (see Deviations). The Bielik and Slayer scores therefore cannot be compared with the numbers
published by Artificial Analysis or with the LFM3-1.7B card value 0.50 in this table.

Bielik answers 67 of 600 questions correctly (accuracy 11.17 ± 1.29), 531 incorrectly and 2 partially, and
answers "I don't know" to none of them (hallucination rate 99.62). Against the constant answer "I don't know." its
OI is 77.33 ± 2.58 points lower (paired, z = -30.0), while its accuracy is above that constant's 0 (z = +8.7). None
of its answers stops at a length limit.

Read OI together with accuracy and the hallucination rate. Bielik knows more than Slayer (accuracy 11.17 against
1.67) but has the lower OI (-77.33 against -59.33), because OI subtracts every wrong answer and Bielik never
abstains, while Slayer does not attempt 223 questions.

Slayer answers 10 of 600 questions correctly (accuracy 1.67 ± 0.52), 366 incorrectly, 1 partially, and does not
attempt 223. Against the constant answer "I don't know." (OI 0, accuracy 0), its OI is 59.33 ± 2.14 points lower
(paired, z = -27.7): the base model guesses instead of abstaining. 598 of its 600 answers stop at the 1280-token
limit, and the judge grades the whole text.

To limit contamination, each line of `results/<model-id>.jsonl.gz` holds only the question id, domain, grade and
score (+1 / 0 / -1), with `output` set to null. No question text or model answer is in this directory.
`results/<model-id>-judge.jsonl.gz` holds the 612 raw judge replies of each run (12 controls, then the 600 answers
in call order), one line per call with the question id, `kind` (`control` with its `expected` letter, or `answer`)
and the judge's reply text, which is one letter each time. Mapping the replies with A correct, B incorrect,
C partial, D not attempted reproduces every grade in `results/<model-id>.jsonl.gz` and the scores above without
calling the judge again.

## Deviations

- **Judge model.** The AA-Omniscience README names Gemini 2.5 Flash Preview (09-2025) as the grader. Our grades come
  from GPT-6.1 Sol (`openai-codex/gpt-6.1-sol`, thinking high), served through the OMP coding-agent command-line
  client (`omp -p`, no tools, no session, offline mode) on a subscription login, not an API key, with the official
  grader template as the only message and a reply of exactly one letter. Every one of the 612 replies of each run
  reports that model id. Slayer was graded on 2026-11-19 from 14:34 to 14:46 UTC, Bielik on 2026-11-19 from 15:38
  to 15:48 UTC. `judge.py` sends the same prompt to any OpenAI-compatible
  endpoint (`JUDGE_BASE_URL`, `JUDGE_MODEL`, `JUDGE_API_KEY`), so a rerun with another judge can differ.
  Before grading, 12 controls (4 questions x {gold answer -> A, another question's gold answer -> B, "I don't
  know." -> D}) must all pass; they did (12/12). Each answer is graded once, in a single judge pass with no
  repeats, as AA does; all 600 got a grade on that pass. `judge.py` builds the same 612 prompts (12 controls + 600
  answers), byte for byte, as the grader that produced our grades, and its parser turns the recorded judge replies
  into the same 600 grades.
- **Self-hosted vLLM, not the fabryka.ai API.** Bielik 11B v3.1 Instruct
  ([speakleash/Bielik-11B-v3.1-Instruct](https://huggingface.co/speakleash/Bielik-11B-v3.1-Instruct) @
  `d6e755d356ad418d0f0e30b8c428db267415ddb9`, bfloat16) is served by vLLM 0.34.0 on a rented GPU (NVIDIA RTX 6000
  Ada Generation)
  (`vllm.sh`), with the chat template's defaults, including the provider system prompt, and the date pinned to
  2026-11-18. This is the setup of the `-vllm` rows of the IFEval benchmark (#313), not the API row.
- **The LFM3-1.7B card's sampling, not Bielik's own.** Bielik runs with the sampling the LFM3-1.7B card uses for
  its evaluations unless it lists an exception (temperature 0.6, top_p 0.95), because the protocol, fixed before the
  runs, compares every model with the card's table under the card's settings. The Bielik model card gives no
  evaluation settings; it sets only temperature 0.3 for its hosted inference widget. A run with Bielik's own settings
  would be a separate row with its own label.
- **Per-question seeds.** Bielik requests carry seed 20261119 + question index.
- **Slayer is a base model** without a chat template: `slayer_server.py` turns the system prompt and the question
  into raw text (system + blank line + question) and decodes greedily up to 1280 tokens, as in the IFEval benchmark
  (#313). Weights: [SlayerLab/Slayer1B-1.09-checkpoints](https://huggingface.co/SlayerLab/Slayer1B-1.09-checkpoints)
  @ `dc3b6a9b0f87305da7ceca39ca27a79fa60b34cd`, `wagi_60000.pt`, loaded by `slayer_package.py` into the GPT class of the
  public trainer `train_gpt_ref_r24_2.py`; rebuilding the package with `slayer_package.py` gives bitwise-identical
  weights (202/202 tensors) and identical logits (max |Δ| = 0.0 on 3 prompts) to the package used for these
  results. It ran on a rented NVIDIA GeForce RTX 4090 in
  fp32 (TF32 off) with a KV cache, 32 requests per batch (`slayer_batch.py`). The server's command-line flags are
  in English (`--limit-mode fixed`, `--batch`, `--default-seed`); no other change from the code that produced the
  result.
- **Slayer serving code** (`slayer_server.py`, `slayer_batch.py`, `slayer_kv_lm.py`, `slayer_package.py`) lives in
  [`research/common/slayer_serving/`](../../common/slayer_serving/). The results were produced with byte-identical
  copies kept in this directory before the move; the shared README lists their hashes.

## Reproduce

```bash
export JUDGE_BASE_URL=https://... JUDGE_MODEL=... JUDGE_API_KEY=...
HF_TOKEN=hf_... bash vllm.sh                # one GPU with at least 48 GB; serves on 127.0.0.1:8000
bash run.sh bielik-11b-v3.1-vllm            # in another shell
bash run.sh slayer1b-60000                  # local CUDA GPU with at least 24 GB; downloads the public step-60000 weights
```

`--limit 5` asks only the first 5 questions and writes to `out/limit/`; the 12 judge controls still run.
