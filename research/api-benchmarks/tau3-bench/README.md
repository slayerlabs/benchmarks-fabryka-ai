# tau3-bench

Agent benchmark: an LLM agent serves a simulated customer (a second LLM, the user simulator) with tools and a domain
policy, and the final database state and the required statements are checked. Refs #291.

- Harness: [sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench) @
  `fc0055dc4e0a316c3f83133267fbd6faaa770992` (tag `v1.0.1`, the tau3-bench line), `uv sync --frozen --extra knowledge`
- Data: bundled with the harness at the same commit
- Metric: mean over 4 domains (airline, retail, telecom, banking_knowledge) of the pass rate (reward 1.0), 1 trial.
  Tasks: airline 50, retail 114, telecom 114 (split `base`), banking_knowledge 97 (no split file)
- Settings: agent Bielik 11B v3.1 through the Fabryka AI API, temperature 0.6, top_p 0.95 (LFM3-1.7B card defaults),
  2 requests at a time; `bm25` retrieval for banking_knowledge; harness defaults otherwise (`--max-steps 200`,
  `--max-errors 10`, `--seed 300`)
- Main result: user simulator Claude Haiku 5.5, NL-assertion judge Bielik 11B v3.1 (not the harness's `gpt-4.1`)
- Extra services: Anthropic API (user simulator, a paid key)
- The card of the reference (LFM3-1.7B) names no simulator, judge, domains, trials, split or retrieval; our choices
  are in [PROTOCOL.md](PROTOCOL.md)

## Results

`stderr` of the average is `sqrt(sum of the 4 domain SE squared) / 4` with domain SE `sqrt(p (1 - p) / n)`.
A task that ended without a reward is outside `n` and is never scored 0 (see "Tasks without a reward").

| model | score | stderr | n | date |
|---|---|---|---|---|
| Bielik 11B v3.1 (`bielik-11b-v3.1`), simulator Haiku 5.5 | 20.81 | 2.22 | 370 of 375 | 2026-11-24 |
| Slayer 1B | null | null | null | 2026-11-23 |
| LFM3-1.7B, model card (card only, not measured by us) | 68.01 | - | - | - |

| domain (Bielik, Haiku simulator) | score | stderr | passed / n | tasks |
|---|---|---|---|---|
| airline | 40.00 | 6.93 | 20 / 50 | 50 |
| retail | 22.73 | 4.00 | 25 / 110 | 114 |
| telecom | 19.47 | 3.72 | 22 / 113 | 114 |
| banking_knowledge | 1.03 | 1.03 | 1 / 97 | 97 |

Bounds for the 5 tasks without a reward: 20.56 if all count as 0, 21.66 if all count as 1.

- **Slayer 1B: null.** A base model without a chat template or tool-calling format, and not served by the API
  (`/v1/models` lists no Slayer; a request for `slayer1b` returns HTTP 400 "Input should be a published model ID",
  with and without `tools`, checked 2026-11-23). The benchmark is not cut down (`results/slayer1b-1.09-k70000.json`).
- **LFM3-1.7B 68.01 is the card's number only.** It was not run by us, and it is not like-for-like with ours: the card
  does not name its simulator (the harness default is `gpt-4.1`, ours is Claude Haiku 5.5), its judge or its API, and
  ours has a hidden provider prompt (below). The two numbers are shown side by side for orientation, with no reading
  of which is higher.
- Per-item files: `results/bielik-11b-v3.1.jsonl.gz` (one line per task: domain, reward or null, termination, `source`
  main or retry, error classes, message counts). `python summarize.py --check` recounts the scores, counts, bounds and
  paired tests of the JSON files from them. The files carry flags and rewards only, no model output (as in gpqa-diamond).
  Not recountable from the repo: the costs, the empty-completion counts, the 503 time window and the cost ratios below
  (usage and run logs in `out/`, not committed); `results/simulator-probe.json` comes from the probe's saved simulations.

### Tasks without a reward

The harness gives no reward to a simulation that ends in an infrastructure error. The Haiku full run (23 Nov) had 74
of these. They were run once more (`retry_infra.sh`, rule: reward missing, never reward low; decided after the main
run and before any retry result, see the PROTOCOL.md amendment) and 69 got a reward; the main result uses the retry
where the main run had none.

| cause of the first attempt | tasks | got a reward in the retry |
|---|---|---|
| HTTP 503 "Inference capacity is busy" (Fabryka API overload, 17:27-18:44 on 23 Nov; 59 telecom, 3 retail) | 62 | 61 |
| judge answer is not JSON (`Expecting value`, raised in the harness's NL-assertion evaluator, so by the Bielik judge) | 12 | 8 |

5 tasks still have no reward: retail 28, 63, 67 and 108 (judge answer not JSON again) and one telecom task (an empty
assistant message that survived the 5 repeats; its first attempt was a 503). The judge failure depends on the task:
retail 21, 39, 60 and 67 failed in both the Haiku main run and the Sonnet run, and retail 108 and 60 in the probe runs
(`results/simulator-probe.json`, `simulator-comparison.jsonl.gz`). So the 5 are not missing at random: 4 are retail
tasks whose NL-assertion part (112 of 114 retail tasks have one) the Bielik judge cannot answer in JSON.

## Simulator comparison (Haiku 5.5 vs Sonnet 5.5)

Before the full run, 20 sampled tasks (5 per domain) were played with both simulators (PROTOCOL.md; 4 of 18
assessable Haiku simulations and 4 of 20 Sonnet simulations had a simulator fault, readers agree on 30 of 38; 3 of 18
and 3 of 20 passed). The fault rates were not distinguishable, Sonnet cost about 7.5 times more, and Haiku was chosen
for the main result: a choice made after reading the probe, not by a rule written before it. The same 20 tasks x 3
repeats with Haiku (`probe3_haiku_*`) had 15 of 17 tasks with the same reward in all three repeats; the 2 others
(airline 41, retail 90) changed. The agent is stochastic (temperature 0.6), so one trial per task is noisy.

The full Sonnet run (airline, retail, telecom) was done afterwards. Paired per task, Sonnet minus Haiku, over the
tasks that have a reward in both arms; SE is `sd / sqrt(n)` of the per-task differences. Three tests form one family
(Holm, `tools/statystyka.py`); they were chosen after seeing the main results, so they are not pre-registered.

| domain | n | Haiku | Sonnet | Δ ± SE (points) | z | verdict | after Holm |
|---|---|---|---|---|---|---|---|
| airline | 50 | 40.00 | 40.00 | +0.00 ± 5.71 | z = 0.00 | noise | no (noise) |
| retail | 97 | 22.68 | 36.08 | +13.40 ± 5.41 | z = 2.48 | borderline | yes (borderline) |
| telecom | 113 | 19.47 | 25.66 | +6.19 ± 3.15 | z = 1.97 | noise | no (noise) |

The retail Δ is borderline and the telecom Δ is noise (z = 1.97, just under the 2 threshold). The Sonnet arm was not
retried: 14 of its 114 retail tasks have no reward (9 HTTP 503, 5 judge answer not JSON), while the Haiku arm got its
infrastructure failures retried. A descriptive row without that asymmetry uses only the Haiku first attempt (tasks
without a retry), no verdict attached:

| descriptive, Haiku first attempt only | n | Δ ± SE (points) | z |
|---|---|---|---|
| airline | 50 | +0.00 ± 5.71 | z = 0.00 |
| retail | 90 | +12.22 ± 5.66 | z = 2.16 |
| telecom | 55 | +10.91 ± 5.61 | z = 1.94 |

The telecom Haiku first attempt lost 59 of 114 tasks to the 503 overload, so its n is 55.

How the simulators behave (same 3 domains, simulations with at least one message, descriptive, no test):

| | Haiku 5.5 | Sonnet 5.5 |
|---|---|---|
| simulations | 273 | 264 |
| customer messages per simulation | 14.5 | 12.1 |
| words per customer message | 52.2 | 46.1 |
| customer messages with markdown bold | 184 of 3966 | 70 of 3185 |
| simulations where Bielik answered in Polish at least once | 46 | 29 |
| Bielik replies of at most 5 words | 155 of 3853 | 52 of 3144 |

In the 20-task probe the contrast was larger (about 53 against 43 words per message, 13 against 8 customer turns,
42 against 3 bold messages, Polish in 5 of 18 against 0 of 20 simulations; analysis kept outside the repo), and it
shrank in the full run. **Hypothesis, not tested:** the longer Haiku conversations, in which it also gives all
details at once and sometimes adds facts the scenario does not contain, push Bielik into a longer context where it
more often answers in a few words or in Polish and loses the thread, which would explain a higher pass rate with
Sonnet in retail and telecom and no difference in the short airline conversations. The data cannot separate this from
agent randomness. What the numbers support: Sonnet minus Haiku is +13.40 ± 5.41 (z = 2.48, borderline) in retail, +6.19 ± 3.15
(z = 1.97, noise) in telecom and +0.00 ± 5.71 (z = 0.00, noise) in airline, so the simulator can move a domain score by
more than its SE, and the main result is a Haiku-simulator number.

**Open: banking_knowledge with Sonnet.** Not measured (cost), planned for about 6 December. A team member with free
Anthropic credits can run it:

```bash
ANTHROPIC_API_KEY=... NL_JUDGE_LLM=openai/bielik-11b-v3.1 TAU3_DOMAINS="banking_knowledge" \
  USER_LLM=anthropic/claude-sonnet-5-5 SAVE_TAG=sonnet COST_LIMIT_USD=25 PRICE_IN=2 PRICE_OUT=10 \
  bash run.sh bielik-11b-v3.1
```

Expected cost 11 to 22 USD: Haiku spent 0.87 USD on this domain, and Sonnet cost 13 times (airline and retail) to 25
times (telecom) as much as Haiku on the other domains (from the run logs, not committed). `summarize.py` does not read the Sonnet banking run until `SONNET_DOMAINS` is
extended and the Sonnet comparison is rebuilt with it. The cost guard compares the
limit only after the domain finishes, so `COST_LIMIT_USD` does not stop a running domain.

## Deviations from the card and the harness

- The simulator is Claude Haiku 5.5 (main) and Sonnet 5.5 (comparison) instead of `gpt-4.1-2025-04-14`, run with
  empty LLM arguments (Claude 5.5 rejects `temperature`). The judge is Bielik instead of `gpt-4.1-2025-04-14`
  (hardcoded in the harness; `tau3_run.py` replaces it by an environment variable and changes nothing else). Scores
  are therefore not comparable with published tau3-bench numbers.
- The Fabryka API adds a hidden Polish provider system prompt to every request (#277). It applies to the agent and
  the judge, not to the Claude simulators. Bielik answered in Polish in 52 of 375 simulations (14%, 701 of 4973 of
  its replies; the customer writes English); the pass rate among those 52 is 15.4% against 18.9% among the other 318
  (descriptive, no test). Polish is detected by a heuristic (Polish letters or two common Polish words).
- Bielik through the API sometimes returns an empty completion. `tau3_run.py` repeats such a call up to 5 times and logs
  it: 432 repeated empty completions in 88 calls over every run in this directory (smoke tests, probes, full runs,
  retries; the log has no run id, so the share of the main result is unknown). Calls of the Claude simulators were
  repeated 7 times (3 calls).
- Tasks that ended without a reward were run once more (above). The 4 domains were taken as the average the card calls
  "4 domains, average"; the card does not list them.
- The harness's own retries (3 per task) stay on. Usage cost: Haiku simulator 4.04 USD in the full run plus 2.63 USD in the
  retry, Sonnet simulator 69.33 USD for 3 domains (it includes the 3 simulations of the aborted banking start),
  from `usage_*.jsonl` at 0.10 / 0.50 (Haiku) and 2 / 10 (Sonnet) USD per million tokens in / out.
- The first Sonnet process was interrupted after airline (an external `pkill` of another run killed its parent script;
  a child process finished airline); the remaining domains ran from a second script with the same parameters. No
  effect on the results.

## Reproduce

```bash
export ANTHROPIC_API_KEY=...   # simulator
export NL_JUDGE_LLM=openai/bielik-11b-v3.1   # judge; FABRYKA_API_KEY or ~/.config/fabryka-api.key for the agent
USER_LLM=anthropic/claude-haiku-5-5 SAVE_TAG=haiku bash run.sh bielik-11b-v3.1     # --limit N runs N tasks per domain
USER_LLM=anthropic/claude-haiku-5-5 SAVE_TAG=haiku bash retry_infra.sh bielik-11b-v3.1
USER_LLM=anthropic/claude-sonnet-5-5 SAVE_TAG=sonnet TAU3_DOMAINS="airline retail telecom" bash run.sh bielik-11b-v3.1
bash run.sh slayer1b-1.09-k70000                                                    # writes the null result
python summarize.py            # builds results/ from out/; python summarize.py --check recounts from results/ alone
```

`SAVE_TAG` keeps runs with different simulators in separate directories. `run_sim_probe.sh` is the 20-task probe
(`probe_fault_readings.csv` holds the two readers' judgments). `smoke.sh` is a free 1-task-per-domain check, not a result.

## Limitations

- One trial per task; Bielik at temperature 0.6 varies between repeats, so the domain scores carry the binomial SE
  only, not the repeat variance.
- Telecom tasks are variants of three issue types, so they are not independent; the SEs treat them as independent.
- The NL-assertion judge is a 11B model; its answer was not JSON for some retail tasks. The 5 missing tasks are
  not missing at random.
- The simulator comparison is 3 tests on one trial each, with an asymmetric retry. banking_knowledge is not compared.
- The probe's fault readings were made by two readers (one of them an agent); the first reader also adjudicated the
  disagreements, so the readings are indicative only.

## Files

| file | content |
|---|---|
| `run.sh <model-id> [--limit N]` | full tau3-bench for one model; `USER_LLM` and `NL_JUDGE_LLM` required |
| `retry_infra.sh <model-id>` | second run of the tasks without a reward |
| `summarize.py` | builds `results/*.json` and per-item `*.jsonl.gz`; `--check` recounts them |
| `results/` | main result, simulator comparison, simulator probe, Slayer null |
| `run_sim_probe.sh`, `probe_fault_readings.csv` | the 20-task simulator probe of PROTOCOL.md; needs a go, costs money |
| `smoke.sh` | 1 task per domain, Bielik as agent, simulator and judge (free); not a result |
| `sample_tasks.py`, `sample.json` | the seeded 20-task sample |
| `tau3_run.py`, `cost.py` | `tau2 run` with a configurable judge, repeated empty completions and a usage log; Claude cost from tokens |
