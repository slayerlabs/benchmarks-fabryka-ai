# ToolSandbox: setup

Status: **setup and protocol only. No result yet.** Refs #289. Details and deviations: [PROTOCOL.md](PROTOCOL.md).

- Harness: [apple/ToolSandbox](https://github.com/apple/ToolSandbox) @ `c8571d7854316d2e1c5f288e59fe1e34e53f6dd1`,
  Python 3.9, exact pins of its `pyproject.toml` (plus `httpx==0.27.2`)
- Data: the 1032 scenarios of the harness (code, `tool_sandbox/scenarios`)
- Metric: mean `similarity` x 100 (milestone and minefield matching, no judge model)
- Settings: agent Bielik 11B v3.1 through the Fabryka AI API, temperature 0, 1024 tokens per turn (LFM3-1.7B card);
  user simulator configurable (`TS_USER_*`, see `ts_run.py`)

## Results

| model | score | stderr | n | date |
|---|---|---|---|---|
| Bielik 11B v3.1 | not run | | | |
| Slayer 1B | null (`run.sh slayer1b`) | | 0 | |
| LFM3-1.7B, model card | 80.36 | | | |

## Deviations

The card names no user simulator or subset; the harness's own simulators are GPT models on the OpenAI API, not
available here. The Fabryka API adds a hidden provider system prompt (#277). Scenarios that need `RAPID_API_KEY`
score 0 without a key (see PROTOCOL.md, "Known risks").

## Files

`run.sh <model-id> [--limit N]`, `smoke.sh` (free, not a result), `ts_run.py` (endpoint wrapper), `common.sh`.
