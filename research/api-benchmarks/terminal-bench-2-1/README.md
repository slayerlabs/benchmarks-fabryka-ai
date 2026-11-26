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
  not independent, so the per-trial formula would understate it; see Deviations)
- Settings (LFM3-1.7B card): OpenCode agent, up to 100 turns (OpenCode `steps: 100`), temperature 0.6, top_p 0.95,
  no output limit other than the context (OpenCode caps one answer at 32000 tokens; for Bielik's 32768-token window
  the cap is 8192, see Deviations); 5 trials per task (the leaderboard's minimum; the card does not say)
- Extra services: none

## Results

| model | how it runs | score | stderr | n | date |
|---|---|---|---|---|---|
| LFM3-1.7B, model card | Liquid AI, OpenCode, up to 100 turns | 12.92 | | | |
| LFM3-1.7B (`lfm3-1.7b`) | own vLLM, bf16, 262144 context | 10.56 | 2.69 | 89 | 2026-11-23 |
| Bielik 11B v3.1 (`bielik-11b-v3.1`) | own vLLM, bf16, 32768 context | not run yet | | | |
| Slayer 1B (`slayer1b-1.09-k70000`) | not run | null | | 0 | 2026-11-24 |

LFM3-1.7B passes 47 of 445 trials. Its score is 2.36 points below the card's 12.92, inside one standard error of
ours (the card gives none), so this run does not show a difference from the card. This check has little power:
with two standard errors (5.4 points) anything from about 7.5 to 18.3 would agree with the card as well. The passes concentrate on few
tasks: 18 of 89 tasks have at least one pass. 4 tasks pass in all 5 trials (`constraints-scheduling`,
`git-leak-recovery`, `modernize-scientific-stack`, `multi-source-data-merger`), and 2 in 4 of 5
(`hf-model-inference`, `largest-eigenval`).

Each line of `results/<model-id>.jsonl.gz` is one trial: task, trial name, job, status, whether it is counted, score
(0/1), Harbor's exception label, the agent's exit code, how the agent's log ends, token counts, and `output`,
Harbor's trajectory of the agent. Every model message and tool call is whole; tool outputs over 2000 and reasoning
over 3000 characters keep their start and end, so the file stays under 10 MB (the full one is 17 MB). The full job
directories (logs, full trajectories, test output; without OpenCode's file snapshots) are kept off the repo,
`lfm3-1.7b-jobs.tar.gz`, sha256 `ed097fb4c36a4448c33066692a4dffe2ed20082713ff1e48c9c5fd7b826b163c`.

Bielik has not been run yet. `run.sh` and `vllm.sh` support it; it needs a 48 GB GPU and an HF token for the gated
weights. Its row is "not run yet", not `null`: nothing stops it from running.

### Which trials count

Harbor's exception label is a pattern match over the agent's output and is not used. For LFM3, 309 of 445 counted
trials end with OpenCode's exit code 1, and Harbor labels them "non-zero exit", "rate limit", "network" and so on.
In all of them the agent's run had already ended: OpenCode writes its last JSON event and then fails with `EPIPE`
writing to the `tee` that Harbor puts on its stdout. In 307 of them the last event is `step_finish/stop`, the
answer finished; in 2 it is `step_finish/length`, the last answer was cut at the output limit. The task's tests ran in every one. `summarize.py` decides from
the evidence instead:

- a trial with a test result counts with it. That includes 14 trials where the task's own container memory limit
  killed processes, the agent among them (exit 137 or 143; the kernel log shows the cgroup OOM kills), and 12 agent
  timeouts. Both are limits of the task, not of our machine;
- a trial without a test result is re-run once, and the re-run counts in its place. For LFM3 that was 15 trials:
  - 10 where the agent never started (`qemu-startup`, `qemu-alpine-ssh`, see Deviations);
  - 3 where the tests ran past their 1800 s limit;
  - 2 where Harbor read the agent's failed `git clone` of a GitHub URL as a login error and skipped the tests.

  Two re-runs had no test result again (one test timeout, one skipped test run) and count as failures;
- no trial has an error event from the model server, which would make it an infrastructure failure.

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
- **Standard error clustered by task.** [`research/api-benchmarks/README.md`](../README.md) gives
  `sqrt(p(1-p)/n)` for pass/fail tasks, here 1.46 over the 445 trials (`other_metrics.stderr_per_trial`). With 5
  trials of each task the trials are not independent, so `stderr` is the standard error of the mean of the 89
  per-task pass rates, 2.69. With the per-trial SE of 1.46 the difference from the card, −2.36, gives
  z = −1.62: noise.
- **Provider package not pinned.** OpenCode installs `@ai-sdk/openai-compatible` itself and its config takes no
  version. The run did not record which release it got; the newest one before the run date is 3.0.94 (2026-11-20).
- **The card's asterisk.** The card marks 12.92 with an asterisk that it does not explain.
- **Bielik's output cap.** vLLM rejects a request whose prompt plus `max_tokens` exceeds the context, and
  OpenCode's own cap of 32000 output tokens alone fills Bielik's 32768. Bielik's cap is set to 8192, which leaves the
  rest of the window to the conversation (not yet exercised, since Bielik has not run).
- **Debian 11 task images, agent install.** `qemu-startup` and `qemu-alpine-ssh` are the only tasks on Debian 11
  (bullseye). Since bullseye's end of life, `deb.debian.org/debian-security` lists packages its pool no longer
  serves (404), so Harbor's `apt-get install curl nodejs npm` fails there and the agent never starts.
  `opencode_agent.py` keeps Harbor's OpenCode agent and only adds a fallback: when that install fails on such an
  image, it points the security source at `archive.debian.org` and retries once. The LFM3 main job ran with the
  stock agent; the re-runs and every later run use the fallback, which changes nothing where the stock install works.
- **Wall-clock limits.** Each task has its own agent time limit (15 minutes to over 3 hours). A slower server can
  turn a slow success into a timeout, so the speed of our GPU and the number of tasks run at once (8 in the main job, 4 in
  the re-runs; `run.sh` defaults to 8, `CONCURRENCY` sets it) are part of the setup. `settings.jobs` in the result
  file records both; they were added from the run log, because the committed `trial_config_example` is the config
  of one trial and holds neither. The VM has 15 CPUs and 98 GB RAM, and the GPU was never the bottleneck (2-3
  requests at a time, KV cache under 1% used).
- **Disk.** The VM's 126 GB disk does not hold every task image at once, so a loop removes unused images
  (`docker image prune -a`) when the disk is over 70% full. Images are pulled again by tag, so this changes no
  task.
- **Slayer cannot run the benchmark.** Slayer 1B is a base model without a chat template or a tool-call format;
  OpenCode can only drive a model through tool calls, so no valid step is possible. Its row is `null`, as in the
  AutomationBench card.

## Reproduce

On a Linux machine with Docker and an NVIDIA GPU (48 GB for Bielik):

```bash
bash vllm.sh lfm3-1.7b                       # serves on 127.0.0.1:8000; HOST=0.0.0.0 to reach it from containers
BASE_URL=http://<host-ip>:8000/v1 bash run.sh lfm3-1.7b              # 8 tasks at a time
HF_TOKEN=hf_... RUN_DATE=YYYY-MM-DD bash vllm.sh bielik-11b-v3.1
BASE_URL=http://<host-ip>:8000/v1 bash run.sh bielik-11b-v3.1
bash run.sh slayer1b-1.09-k70000                   # writes the null result
python3 summarize.py out/jobs/<model-id> --model <model-id>
```

If some trials have no test result, `summarize.py` lists them and writes nothing. Re-run them with
`CONCURRENCY=4 TASKS="<task> ..." TRIALS=<k> JOB_NAME=<model-id>-rerun-a bash run.sh <model-id>` (one job per number
of missing trials; the LFM3 re-runs used 4 at a time) and pass each job with `--rerun out/jobs/<job>`.

`--limit N` runs the first N tasks once each and writes to `out/limit/`.
