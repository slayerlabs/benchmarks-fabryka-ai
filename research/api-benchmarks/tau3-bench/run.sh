#!/usr/bin/env bash
# tau3-bench (tau2-bench v1.0.1, 4 domains) for one model: bash run.sh <model-id> [--limit N]
#   bielik-11b-v3.1   agent through the Fabryka AI API; needs USER_LLM (simulator, litellm id, e.g.
#                     anthropic/claude-sonnet-5-5 with ANTHROPIC_API_KEY set) and NL_JUDGE_LLM
#   slayer1b          cannot run the benchmark: writes results/slayer1b.json with score null
# Full set = the `base` split of airline (50), retail (114), telecom (114) and all banking_knowledge tasks (97), 1 trial.
# --limit N runs the first N tasks of each domain. Simulations land in out/tau2-bench/data/simulations/<model-id>_<domain>.
# Not a measurement of the user simulator: that is run_sim_probe.sh (PROTOCOL.md).
set -euo pipefail
MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"; shift
LIMIT=""; [[ "${1:-}" == "--limit" ]] && LIMIT="${2:?--limit needs N}"
source "$(dirname "$0")/common.sh"
case "$MODEL" in
  bielik-11b-v3.1) ;;
  slayer1b)
    mkdir -p "$HERE/results"
    cat > "$HERE/results/slayer1b.json" <<J
{"benchmark": "tau3-bench", "model": "slayer1b", "metric": "avg_reward_4_domains", "score": null, "stderr": null, "n": 0,
 "date": "$(date +%F)", "harness": "sierra-research/tau2-bench @ $TAU2_COMMIT", "settings": {}, "deviations": "see README.md",
 "score_null_reason": "Slayer 1B is a base model without a chat template or tool-calling format, and it is not served by the Fabryka AI API (/v1/models lists no Slayer; a request returns HTTP 400 'Input should be a published model ID', with or without tools), so no tool call can be made."}
J
    exit 0 ;;
  *) echo "unknown model-id: $MODEL (bielik-11b-v3.1 | slayer1b)" >&2; exit 2 ;;
esac
: "${USER_LLM:?set USER_LLM (user simulator, litellm model id)}"
: "${NL_JUDGE_LLM:?set NL_JUDGE_LLM (litellm model id)}"; export NL_JUDGE_LLM
for d in "${DOMAINS[@]}"; do
  ids=(); while IFS= read -r id; do ids+=("$id"); done < <("$PY" - "$d" "$LIMIT" <<'P'
import json, sys
from pathlib import Path
d, n = sys.argv[1], sys.argv[2]
root = Path(__import__("os").environ["TAU2_DATA_DIR"]) / "tau2" / "domains" / d
tasks = json.loads((root / "tasks.json").read_text())
split = root / "split_tasks.json"
base = set(json.loads(split.read_text())["base"]) if split.exists() else None
ids = [str(t["id"]) for t in tasks if base is None or str(t["id"]) in base]
print("\n".join(ids[:int(n)] if n else ids))
P
  )
  extra=(); [[ "$d" == banking_knowledge ]] && extra=(--retrieval-config bm25)
  "$PY" "$HERE/tau3_run.py" run --domain "$d" --agent-llm "$AGENT" --agent-llm-args "$AGENT_ARGS" --user-llm "$USER_LLM" \
    --task-ids "${ids[@]}" --num-trials 1 --max-concurrency 2 --save-to "${MODEL}_$d" "${extra[@]}"
done
