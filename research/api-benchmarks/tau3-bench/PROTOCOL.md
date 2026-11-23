# tau3-bench user simulator probe: measurement protocol

Written and committed before any output of a Claude simulator. Nothing below changes after a result is seen; anything
added later goes into a dated amendment at the end.

Refs #291.

## Question

The LFM3-1.7B card reports tau3-bench 68.01 (average of 4 domains). In tau3-bench a second LLM plays the customer
(the user simulator), and the agent's score depends on how well the simulator behaves. The card does not name its
simulator. We cannot use the harness default (`gpt-4.1-2025-04-14`, OpenAI, paid account not available to the
team), so the simulator will be a Claude model. **Does the choice between a small and a larger Claude simulator
(Haiku 5.5 vs Sonnet 5.5) change how often the simulator itself breaks the task?** The probe measures the
simulator, not the agent: its primary outcome is the rate of simulator faults, not the agent's reward.

## Sources

- Harness: [sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench), tag `v1.0.1`, commit
  `fc0055dc4e0a316c3f83133267fbd6faaa770992` (the tau3-bench release line, v1.0.x; v1.0.1 fixed the
  `banking_knowledge` grading; v2.0.0 changed the prompts, tasks and the judge and is not used). Dependencies from its
  `uv.lock` (`uv sync --frozen --extra knowledge`).
- Data: bundled with the harness, `data/tau2/domains/*` at the same commit.
- Reference: [LiquidAI/LFM3-1.7B](https://huggingface.co/LiquidAI/LFM3-1.7B) card, "Benchmarks" and "Evaluation
  details".

## What the card states and what it does not

The card states for tau3-bench: "4 domains, average" and, for all evals not listed as exceptions, temperature 0.6,
top_p 0.95 and no output limit other than the context length. tau3-bench is not in the exception list.

The card does **not** state: which four domains, the number of trials, the user simulator, the judge model, the
split, the retrieval configuration of `banking_knowledge`, the step limit. The following are therefore our
assumptions, not the card's settings:

- Domains: `airline`, `retail`, `telecom`, `banking_knowledge` (the four domains of the tau3-bench release; the
  others in the harness, `mock` and `intake`, are test and entity-capture domains).
- Task sets: the `base` split of airline (50), retail (114), telecom (114) and all 97 tasks of `banking_knowledge`
  (it has no split file), 1 trial.
- `banking_knowledge` retrieval: `bm25` (offline; the harness default `alltools` needs an embeddings API).
- Harness defaults otherwise: `--max-steps 200`, `--max-errors 10`, `--seed 300`.

## Models

| role | model | how |
|---|---|---|
| agent | Bielik 11B v3.1 Instruct, `bielik-11b-v3.1` | Fabryka AI API, `https://fabryka.ai/v1` (OpenAI-compatible, litellm `openai/` provider), temperature 0.6, top_p 0.95, 2 requests at a time |
| user simulator, arm H | `anthropic/claude-haiku-5-5` | litellm, harness default simulator arguments (temperature 0.0) |
| user simulator, arm S | `anthropic/claude-sonnet-5-5` | same |
| NL-assertion judge | Bielik 11B v3.1, `openai/bielik-11b-v3.1`, temperature 0.0 | same judge in both arms |

The Fabryka API adds a hidden provider system prompt in Polish to every request (#277). It applies to the agent and
to the judge, and in the smoke test also to the simulator (both answered in Polish). The Claude simulators do not get
it. This is a deviation, stated in the README.

Slayer 1B: a base model without a chat template or tool-calling format, and not served by the API (`/v1/models`
lists no Slayer; a request for `slayer1b` returns HTTP 400 "Input should be a published model ID", with and without
`tools`, checked 2026-11-23). It gets `score: null` with that reason, as in BFCL (#328); no simulator is run for it.

## Deviation from the card and the harness default

The simulator is Claude (Haiku 5.5 or Sonnet 5.5) instead of the harness default `gpt-4.1-2025-04-14`; the card
does not say what its authors used. The NL-assertion judge is Bielik instead of `gpt-4.1-2025-04-14`
(hardcoded in the harness; `tau3_run.py` replaces it by environment variable and changes nothing else). Scores in
this probe are therefore **not comparable** with 68.01 or with any other published tau3-bench score. The retail
`NL_ASSERTION` part of the reward (112 of 114 retail tasks) is judged by a weak model; reward differences are read
as descriptive only.

## Sample

20 tasks, 5 per domain, drawn once with `random.Random(20261123).sample` from the task ids sorted as strings
(`sample_tasks.py`, output `sample.json`, committed with this protocol). Population: airline 50, retail 114,
telecom 114, banking_knowledge 97. Both simulators play **the same 20 tasks**, 1 trial each, same agent settings,
same seed (300), same step limit.

| domain | ids |
|---|---|
| airline | 18, 37, 41, 46, 8 |
| retail | 108, 16, 59, 60, 90 |
| telecom | `[mms_issue]airplane_mode_on\|break_app_both_permissions\|data_usage_exceeded\|user_abroad_roaming_disabled_off[PERSONA:None]`, `[mms_issue]break_app_storage_permission\|unseat_sim_card\|user_abroad_roaming_disabled_on[PERSONA:Easy]`, `[mobile_data_issue]airplane_mode_on\|bad_network_preference[PERSONA:Hard]`, `[service_issue]airplane_mode_on\|break_apn_settings\|overdue_bill_suspension\|unseat_sim_card[PERSONA:None]`, `[service_issue]break_apn_settings\|overdue_bill_suspension\|unseat_sim_card[PERSONA:Hard]` |
| banking_knowledge | task_004, task_012, task_016, task_060, task_089 |

Seen before this protocol: a Bielik-only smoke test (agent, simulator and judge all Bielik, free API) ran the first
sampled task of airline, retail, telecom and banking_knowledge, plus airline 0, retail 0, retail 2 and
banking_knowledge task_001 earlier while building the pipeline. It checked that the chain runs and saves
transcripts. It is not a result, was not scored against anything, and the sample was not redrawn.

## What counts as a simulator fault

A simulation is read from its transcript (`messages` in `results.json`) by two independent readers (agents, each
with only the task definition, the transcript and this section), without the reward. A **simulator fault** is any of:

1. **Goal drift**: the simulator asks for or accepts something that contradicts the task's user scenario
   (instructions, known information, stated preferences).
2. **Leak**: the simulator tells the agent the solution (the exact tool calls or the policy outcome to apply) or
   information its scenario says it does not know.
3. **Premature end**: the simulator ends the conversation (`###STOP###` or equivalent) before its goal was reached
   or refused with the agent still working on it.
4. **Instruction break**: the simulator breaks a rule of its own system prompt, for example plays the assistant,
   answers in a way that the persona forbids, or invents facts that contradict the task.

Not simulator faults: the agent's mistakes, tool errors, context-window overflow of the agent, API errors, step-limit
termination caused by the agent looping. These terminations are listed separately by `termination_reason` and the
simulation is marked "not assessable" for the simulator if the fault could not have occurred before it.

Readers give a per-simulation yes/no with the transcript turn and a one-line reason. Disagreement is resolved by a
third reading of the disputed turn; the disagreements and their number are reported.

## Metrics

- Primary: per arm, number and share of simulations with at least one simulator fault, among assessable ones; per
  fault type. n = 20 per arm, so shares are reported with the counts and a Wilson interval, no significance claim.
- Secondary: agent reward per arm and domain (descriptive: one trial, a stochastic agent and a weak judge make
  differences between arms noise at n = 20), termination reasons, number of turns.
- Cost: Claude cost from `usage` of the simulator's messages at Haiku 5.5 0.10 / 0.50 USD and Sonnet 5.5 2 / 10 USD
  per million input / output tokens (`cost.py`, from a usage log that `tau3_run.py` writes for every successful model call,
  including task attempts the harness discards and retries; the harness's own cost field reads 0 for these models).
  The harness default of 3 retries per task stays on: with Bielik as agent, an empty assistant message (observed in
  the smoke test) raises an infrastructure error, and without retries the task would be dropped.

## Cost

A Claude call needs a go from the person who owns the key. Order of calls: a one-token ping per model id, one task per
arm (expected about 0.005 USD for Haiku and about 0.1 USD for Sonnet per task; a deviation of more than 5x stops the
probe), then the rest. The running Claude cost is checked after every domain, and the probe stops above 5 USD in total.

## Not in scope

The full 375-task tau3-bench for any model, other simulators, the agent's score as a headline, ToolSandbox (own
directory and protocol).
