#!/usr/bin/env bash
# Second run of the tasks that ended WITHOUT a reward in a full run (infrastructure error: API capacity, a judge answer
# that is not JSON, an empty assistant message). Rule: reward missing, never "reward low". Tasks with a reward are not rerun.
#   USER_LLM=anthropic/claude-haiku-5-5 NL_JUDGE_LLM=openai/bielik-11b-v3.1 SAVE_TAG=haiku bash retry_infra.sh bielik-11b-v3.1
# Reads out/tau2-bench/data/simulations/<model>_<tag>_<domain>, writes <model>_<tag>_retry_<domain> (same parameters as run.sh).
# This is the procedure that produced the *_haiku_retry_* runs of results/ (run on 2026-11-24 from an untracked chain script).
set -euo pipefail
MODEL="${1:?usage: bash retry_infra.sh <model-id>}"
source "$(dirname "$0")/common.sh"
: "${USER_LLM:?set USER_LLM}"; : "${NL_JUDGE_LLM:?set NL_JUDGE_LLM}"; export NL_JUDGE_LLM
: "${SAVE_TAG:?set SAVE_TAG (the tag of the full run to retry)}"
export TAU3_USAGE_LOG="$OUT/usage_${SAVE_TAG}_retry.jsonl"; touch "$TAU3_USAGE_LOG"   # read by summarize.py (cost)
UARGS=(); [[ "$USER_LLM" == anthropic/* ]] && UARGS=(--user-llm-args '{}')
for d in "${DOMAINS[@]}"; do
  ids=(); while IFS= read -r id; do ids+=("$id"); done < <("$PY" - "$d" "$OUT/tau2-bench/data/simulations/${MODEL}_${SAVE_TAG}_$d/results.json" <<'P'
import json, sys
for s in json.load(open(sys.argv[2]))["simulations"]:
    if (s.get("reward_info") or {}).get("reward") is None:
        print(s["task_id"])
P
  )
  [[ ${#ids[@]} -eq 0 ]] && { echo "$d: nothing to retry"; continue; }
  echo "$d: retrying ${#ids[@]} tasks"
  extra=(); [[ "$d" == banking_knowledge ]] && extra=(--retrieval-config bm25)
  "$PY" "$HERE/tau3_run.py" run --domain "$d" --agent-llm "$AGENT" --agent-llm-args "$AGENT_ARGS" --user-llm "$USER_LLM" "${UARGS[@]}" \
    --task-ids "${ids[@]}" --num-trials 1 --max-concurrency 2 --save-to "${MODEL}_${SAVE_TAG}_retry_$d" "${extra[@]}"
done
