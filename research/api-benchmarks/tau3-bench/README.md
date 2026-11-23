# tau3-bench: setup and user simulator probe

Status: **setup and protocol only. No result yet.** Refs #291. Measurement plan: [PROTOCOL.md](PROTOCOL.md).

- Harness: [sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench) @
  `fc0055dc4e0a316c3f83133267fbd6faaa770992` (tag `v1.0.1`, the tau3-bench line), `uv sync --frozen --extra knowledge`
- Data: bundled with the harness at the same commit
- Metric: average reward over the 4 domains (airline, retail, telecom, banking_knowledge), 1 trial
- Settings: agent Bielik 11B v3.1 through the Fabryka AI API, temperature 0.6, top_p 0.95 (LFM3-1.7B card defaults);
  user simulator set by `USER_LLM`; NL-assertion judge set by `NL_JUDGE_LLM` (`tau3_run.py`); `bm25` retrieval for
  `banking_knowledge`; 2 requests at a time

## Results

| model | score | stderr | n | date |
|---|---|---|---|---|
| Bielik 11B v3.1 | not run | | | |
| Slayer 1B | null (`run.sh slayer1b`) | | 0 | |
| LFM3-1.7B, model card | 68.01 | | | |

## Deviations from the card and the harness

- The card names no user simulator, judge, domains, trials, split or retrieval setup (see PROTOCOL.md); ours are
  assumptions listed there.
- The harness default simulator and NL-assertion judge are `gpt-4.1-2025-04-14`. Here the simulator is Claude and the
  judge is Bielik, so scores are not comparable with published tau3-bench numbers.
- The Fabryka API adds a hidden provider system prompt to every request (#277).

## Files

| file | content |
|---|---|
| `run.sh <model-id> [--limit N]` | full tau3-bench for one model; `USER_LLM` and `NL_JUDGE_LLM` required |
| `run_sim_probe.sh` | the simulator probe of PROTOCOL.md: 20 sampled tasks x 2 Claude simulators; needs a go, costs money |
| `smoke.sh` | 1 task per domain, Bielik as agent, simulator and judge (free); not a result |
| `sample_tasks.py`, `sample.json` | the seeded 20-task sample |
| `tau3_run.py` | `tau2 run` with a configurable NL-assertion judge |
| `cost.py` | Claude cost from `usage` tokens |
