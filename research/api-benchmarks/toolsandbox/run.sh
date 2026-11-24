#!/usr/bin/env bash
# ToolSandbox for one model: bash run.sh <model-id> [--limit N]
#   bielik-11b-v3.1   agent through the Fabryka AI API (needs TS_USER_BASE_URL, TS_USER_API_KEY_FILE, TS_USER_MODEL for
#                     the simulator; see ts_run.py)
#   slayer1b-1.09-k70000   cannot run the benchmark: writes results/slayer1b-1.09-k70000.json with score null
# Runs the 808 scenarios that need no RAPID_API_KEY (--limit N: the first N by name; --only FILE: just those names). Score = mean `similarity` x 100 (the harness's metric).
set -euo pipefail
MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"; shift
LIMIT=""; ONLY=""
[[ "${1:-}" == "--limit" ]] && LIMIT="${2:?--limit needs N}"
[[ "${1:-}" == "--only" ]] && ONLY="${2:?--only needs a file}"
source "$(dirname "$0")/common.sh"
case "$MODEL" in
  bielik-11b-v3.1) ;;
  slayer1b-1.09-k70000)
    # not run: written without calling any model. RESULT_DATE overrides today's date.
    mkdir -p "$HERE/results"
    cat > "$HERE/results/$MODEL.json" <<J
{
  "benchmark": "ToolSandbox",
  "model": "$MODEL",
  "metric": "mean similarity x 100, SE clustered by base scenario",
  "score": null,
  "stderr": null,
  "n": 0,
  "date": "${RESULT_DATE:-$(date +%F)}",
  "harness": "https://github.com/apple/ToolSandbox @ $TS_COMMIT",
  "data": "scenarios of the harness (code), default tool backend: 1032 in total, 224 needing RAPID_API_KEY excluded",
  "settings": {"agent": "not run", "user_simulator": "not used", "temperature": 0, "max_tokens_per_turn": 1024,
               "max_messages_per_scenario": 30, "trials": 1, "tool_backend": "DEFAULT"},
  "score_null_reason": "The harness sends tool definitions through the OpenAI \`tools\` parameter and returns tool results as \`tool\` messages. Slayer 1B 1.09 is a base model without a chat template or tool-calling format: the Slayer server of this repository (common/slayer_serving/slayer_server.py) answers HTTP 400 to \`tools\`, \`tool_choice\` and the \`tool\` role, and the Fabryka AI API does not serve Slayer (its /v1/models lists no Slayer, and a request for it returned HTTP 400 'Input should be a published model ID', with or without tools; observed during setup 2026-11-23, no log committed). No tool call can be made, so the benchmark was not run.",
  "deviations": "see README.md, Deviations"
}
J
    exit 0 ;;
  *) echo "unknown model-id: $MODEL (bielik-11b-v3.1 | slayer1b-1.09-k70000)" >&2; exit 2 ;;
esac
: "${TS_USER_MODEL:?set TS_USER_MODEL (and TS_USER_BASE_URL, TS_USER_API_KEY_FILE) for the user simulator}"
cd "$OUT"
# Scenarios whose milestones call a RapidAPI tool cannot be scored without RAPID_API_KEY: excluded (rapid_api_scenarios.txt).
# --only FILE (scenario names, one per line) runs just those, for the rerun of infrastructure errors.
NAMES=()
while IFS= read -r n; do NAMES+=("$n"); done < <("$PY" -W ignore -c "
import sys
from tool_sandbox.scenarios import named_scenarios
from tool_sandbox.common.tool_discovery import ToolBackend
alln = sorted(named_scenarios(preferred_tool_backend=ToolBackend.DEFAULT))
if '$ONLY':
    sel = [l.strip() for l in open('$ONLY') if l.strip()]
else:
    ex = {l.strip() for l in open('$HERE/rapid_api_scenarios.txt') if l.strip()}
    sel = [n for n in alln if n not in ex]
    if '$LIMIT': sel = sel[:int('$LIMIT')]
print('\\n'.join(sel))")
echo "scenarios to run: ${#NAMES[@]}" >&2
export TS_USAGE_LOG="${TS_USAGE_LOG:-$OUT/usage.jsonl}"
# 2 workers: the Fabryka API takes 2 requests at a time
"$PY" "$HERE/ts_run.py" --agent GPT_4_o_2024_05_13 --user GPT_4_o_2024_05_13 --parallel 2 -o "$OUT/data/${RUN_TAG:-$MODEL}" -s "${NAMES[@]}"
