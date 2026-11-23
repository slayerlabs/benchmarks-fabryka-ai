# Terminal-Bench 2.1

Whether an agent can finish real tasks in a Linux terminal: build and fix software, analyse data, configure
services, security tasks. Each of the 89 tasks runs in its own Docker container. The agent works there with shell
and file tools, and the task's own tests decide pass or fail afterwards. No judge model.

- Paper and site: [tbench.ai](https://www.tbench.ai), [Terminal-Bench 2.1 release](https://tbench.ai/news/terminal-bench-2-1)
- Harness: [harbor-framework/harbor](https://github.com/harbor-framework/harbor) v0.27.0 (`harbor` on PyPI)
- Agent: OpenCode, `opencode-ai` 1.19.6 from npm, installed by Harbor in each task container
- Data: [harbor-framework/terminal-bench-2-1](https://github.com/harbor-framework/terminal-bench-2-1) @
  `12b7565679ce5006230b820666353673a133db93`, all 89 tasks (the task images are prebuilt and pinned by tag)
- Metric: pass rate. A trial passes when the task's tests give reward 1. Score = the mean over tasks of the per-task
  pass rate over the trials; `stderr` = the standard error of that mean over the 89 tasks (trials of one task are
  not independent, so the per-trial formula would understate it)
- Settings (LFM3-1.7B card): OpenCode agent, up to 100 turns (OpenCode `steps: 100`), temperature 0.6, top_p 0.95,
  no output limit other than the context; 5 trials per task (the leaderboard's minimum; the card does not say)
- Extra services: none

## Results

| model | how it runs | score | stderr | n | date |
|---|---|---|---|---|---|
| LFM3-1.7B, model card | Liquid AI, OpenCode, up to 100 turns | 12.92 | | | |
| LFM3-1.7B (`lfm3-1.7b`) | own vLLM, bf16, 262144 context | TBD | | 89 | |
| Bielik 11B v3.1 (`bielik-11b-v3.1`) | own vLLM, bf16, 32768 context | TBD | | 89 | |
| Slayer 1B (`slayer1b-70000`) | not run | null | | 0 | |

Each line of `results/<model-id>.jsonl.gz` is one trial: task, trial name, score (0/1), the exception if the trial
ended with one, token counts, and `output`, Harbor's trajectory of the agent (every model message, reasoning, tool
call and tool result).

## Deviations

- **Own vLLM server, not the fabryka.ai API.** Both models run on one rented GPU (vast.ai, an Ubuntu 22.04 VM
  with one NVIDIA L40S 48 GB) with vLLM 0.34.0 in bf16 (`vllm.sh`):
  - LFM3-1.7B with the parsers from [Liquid AI's vLLM guide](https://docs.liquid.ai/deployment/gpu-inference/vllm)
    (`--reasoning-parser qwen3 --tool-call-parser qwen3_coder`);
  - Bielik with the tool-call and reasoning parsers from
    [speakleash/bielik-tools](https://github.com/speakleash/bielik-tools) @
    `2bcd696d5f1d8bee0c4821e3b8c9c666c075ae09`, the setup of the `-vllm` rows of IFEval and AutomationBench.

  The task containers run on the same VM, and the agent reaches the server on the VM's own address.
- **Number of trials.** The card does not say how many trials it averages. This run uses 5 per task.
- **The card's asterisk.** The card marks 12.92 with an asterisk that it does not explain.
- **Wall-clock limits.** Each task has its own agent time limit (15 minutes to over 3 hours). A slower server can
  turn a slow success into a timeout, so the speed of our GPU and the number of tasks run at once (8) are part of
  the setup.
- **Slayer cannot run the benchmark.** Slayer 1B is a base model without a chat template or a tool-call format;
  OpenCode can only drive a model through tool calls, so no valid step is possible. Its row is `null`, as in the
  AutomationBench card.

## Reproduce

On a Linux machine with Docker and an NVIDIA GPU (48 GB for Bielik):

```bash
bash vllm.sh lfm3-1.7b                       # serves on 127.0.0.1:8000; HOST=0.0.0.0 to reach it from containers
BASE_URL=http://<host-ip>:8000/v1 bash run.sh lfm3-1.7b
HF_TOKEN=hf_... RUN_DATE=YYYY-MM-DD bash vllm.sh bielik-11b-v3.1
BASE_URL=http://<host-ip>:8000/v1 bash run.sh bielik-11b-v3.1
bash run.sh slayer1b-70000                   # writes the null result
python3 summarize.py out/jobs/<model-id> --model <model-id>
```

`--limit N` runs the first N tasks once each and writes to `out/limit/`.
