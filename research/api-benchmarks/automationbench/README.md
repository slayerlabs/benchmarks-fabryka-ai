# AutomationBench (public)

Polish version: [README.pl.md](README.pl.md).

Whether an agent completes multi-step business workflows across simulated services (CRM, email, Slack, sheets,
calendars, ticketing): it finds the right API endpoints with a search tool, calls them over HTTP, and is scored on
the final state of the services by assertions, without a judge model.

- Harness: [zapier/AutomationBench](https://github.com/zapier/AutomationBench) @
  `4a8e1061254004d9dac807054eed33fad7d1ff14` (`auto-bench`, benchmark version 1.0.6)
- Data: bundled with the harness, the six public domains (sales, marketing, operations, support, finance, hr), 600
  tasks (full public set; the `simple` domain is a tool-use sanity check and not part of the score)
- Metric: pass rate (a task passes only if every scored assertion passes); mean partial credit and assertion counts
  in `other_metrics`
- Settings: toolset `api` (the harness default), up to 50 steps per task, 1 trial. Bielik: temperature 0.6,
  top_p 0.95, no output limit other than the context (LFM3-1.7B card: "up to 50 turns")
- Extra services: none (the services are simulated inside the harness)

## Results

| model | score | stderr | n | date |
|---|---|---|---|---|
| Bielik 11B v3.1, own vLLM (`bielik-11b-v3.1-vllm`) | 0.00 | 0.00 | 600 | 2026-11-19 |
| Slayer 1B, step 60000 (`slayer1b-60000`) | null | | 0 | 2026-11-19 |
| LFM3-1.7B, model card | 41.29 | | | |

Bielik passes no task and none of the 5729 scored assertions. The harness also records 3883 assertions that an
idle agent would satisfy (for example "no email sent to X"); it marks them `excluded` and does not score them, so a
model that does nothing scores 0. The environment works: calls to a connected service succeed. The failures are
the model's: `api_search` is often asked for a single result (`top_k: 1`) and returns an unrelated endpoint, and of
its 1618 tool calls the model makes 351 to services not connected to the task (401), 484 to unknown endpoints (404),
and 150 with invalid JSON arguments (400); 235 of 600 tasks end with a
text answer and no tool call at all. As a positive control, the same server and settings pass 15 of 200 tasks
(7.5%) on the harness's `simple` domain (`--domains simple`: Salesforce 8, HubSpot 2, Mailchimp 2, Jira 3); 5
rollouts were aborted by the harness because the model returned neither text nor a tool call, and count as
failures. So the harness and its tools do work with this model, and the 0/600 is the model's result on the public
tasks.

Each line of `results/<model-id>.jsonl.gz` holds the task id and name, the 0/1 score, partial credit, every
assertion's type with passed/excluded flags, the step and tool-call counts, and the `output`: the full conversation
without the system prompt (model messages, tool calls and tool results).

## Deviations

- **Self-hosted vLLM, not the fabryka.ai API.** Bielik 11B v3.1 Instruct
  ([speakleash/Bielik-11B-v3.1-Instruct](https://huggingface.co/speakleash/Bielik-11B-v3.1-Instruct) @
  `d6e755d356ad418d0f0e30b8c428db267415ddb9`, bfloat16) is served by vLLM 0.34.0 on a rented GPU (NVIDIA RTX 6000
  Ada Generation), with
  the tool-call and reasoning parsers from [speakleash/bielik-tools](https://github.com/speakleash/bielik-tools) @
  `2bcd696d5f1d8bee0c4821e3b8c9c666c075ae09` (`vllm.sh`) and the chat template's defaults, including the provider
  system prompt, with the date pinned to 2026-11-18. This is the setup of the `-vllm` rows of the IFEval benchmark
  (#313), not the API row.
- **One seed for all requests.** Every request carries the same `seed` (20261119); no task ended with an empty
  reply.
- **Tool calls left in the text.** In 10 of 600 tasks the model's last message holds a tool call written as text
  that the vLLM tool parser did not turn into a call; the harness treats it as a final answer.
- **Date.** The simulated services run at the real clock (2026-11-19), while the chat template tells the model
  2026-11-18.
- **Requests are batched.** 16 tasks at a time; the same vLLM server also served other benchmarks during the run.
- **Slayer cannot run the benchmark.** Slayer 1B is a base model without a chat template or tool-calling format;
  the serving endpoint rejects requests with tools (HTTP 400), so no syntactically valid call is possible.

## Reproduce

```bash
HF_TOKEN=hf_... bash vllm.sh                # one GPU with at least 48 GB; serves on 127.0.0.1:8000
bash run.sh bielik-11b-v3.1-vllm            # in another shell
DOMAINS=simple bash run.sh bielik-11b-v3.1-vllm   # the harness's tool-use sanity check (200 tasks, not scored)
bash run.sh slayer1b-60000                  # writes the null result
```

`--limit 5` runs only the first 5 tasks and writes to `out/limit/`. `BASE_URL` points `run.sh` at another endpoint
that serves the model as `bielik`.
