#!/usr/bin/env bash
# tau3-bench (tau2-bench v1.0.1, 4 domains) for one model: bash run.sh <model-id> [--limit N]
#   bielik-11b-v3.1   agent through the Fabryka AI API; needs USER_LLM (simulator, litellm id, e.g.
#                     anthropic/claude-sonnet-5-5 with ANTHROPIC_API_KEY set) and NL_JUDGE_LLM
#   slayer1b-1.09-k70000  cannot run the benchmark: writes results/slayer1b-1.09-k70000.json with score null
# Full set = the `base` split of airline (50), retail (114), telecom (114) and all banking_knowledge tasks (97), 1 trial.
# --limit N runs the first N tasks of each domain. Simulations land in out/tau2-bench/data/simulations/<model-id>_<domain>.
# Not a measurement of the user simulator: that is run_sim_probe.sh (PROTOCOL.md).
set -euo pipefail
MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"; shift
LIMIT=""; [[ "${1:-}" == "--limit" ]] && LIMIT="${2:?--limit needs N}"
source "$(dirname "$0")/common.sh"
case "$MODEL" in
  bielik-11b-v3.1) ;;
  slayer1b-1.09-k70000)
    mkdir -p "$HERE/results"
    cat > "$HERE/results/slayer1b-1.09-k70000.json" <<J
{
  "benchmark": "tau3-bench",
  "model": "slayer1b-1.09-k70000",
  "metric": "mean of the 4 domain pass rates (airline, retail, telecom, banking_knowledge), 1 trial, percent",
  "score": null,
  "stderr": null,
  "n": null,
  "date": "2026-11-23",
  "harness": "sierra-research/tau2-bench @ $TAU2_COMMIT (tag v1.0.1, the tau3-bench release line)",
  "data": "bundled with the harness at the same commit",
  "settings": {"agent": "none: no request could be sent"},
  "other_metrics": {"reason": "Slayer 1B is a base model without a chat template or a tool-calling format, and it is not served by the Fabryka AI API: /v1/models lists no Slayer and a request for slayer1b returns HTTP 400 'Input should be a published model ID', with and without tools (checked 2026-11-23), so no tool call can be made. The benchmark is not cut down to fit."},
  "deviations": "none (not run: no agent can be served, see other_metrics.reason)"
}
J
    exit 0 ;;
  *) echo "unknown model-id: $MODEL (bielik-11b-v3.1 | slayer1b-1.09-k70000)" >&2; exit 2 ;;
esac
: "${USER_LLM:?set USER_LLM (user simulator, litellm model id)}"
: "${NL_JUDGE_LLM:?set NL_JUDGE_LLM (litellm model id)}"; export NL_JUDGE_LLM
# Claude 5.5 simulators reject temperature, so they get empty LLM args; others keep the harness default.
UARGS=(); [[ "$USER_LLM" == anthropic/* ]] && UARGS=(--user-llm-args '{}')
TAG="${SAVE_TAG:-}"   # e.g. haiku / sonnet, so runs with different simulators do not overwrite each other
# Usage log of every simulator and agent call (tau3_run.py), read by summarize.py for the cost; an optional USD limit for the
# simulator calls is checked after each domain (COST_LIMIT_USD with PRICE_IN, PRICE_OUT in USD per Mtok).
export TAU3_USAGE_LOG="${TAU3_USAGE_LOG:-$OUT/usage_${MODEL}${TAG:+_$TAG}.jsonl}"; touch "$TAU3_USAGE_LOG"
if [[ -n "${COST_LIMIT_USD:-}" ]]; then
  : "${PRICE_IN:?set PRICE_IN (USD per Mtok)}" "${PRICE_OUT:?set PRICE_OUT}"
fi
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
    --task-ids "${ids[@]}" --num-trials 1 --max-concurrency 2 --save-to "${MODEL}${TAG:+_$TAG}_$d" "${extra[@]}" "${UARGS[@]}"
  if [[ -n "${COST_LIMIT_USD:-}" ]]; then
    c=$("$PY" "$HERE/cost.py" "$TAU3_USAGE_LOG" "$USER_LLM" "$PRICE_IN" "$PRICE_OUT" | "$PY" -c "import json,sys; print(json.load(sys.stdin)['cost_usd'])")
    echo "$d done, simulator cost so far $c USD (limit $COST_LIMIT_USD)"
    "$PY" -c "import sys; sys.exit(0 if $c <= $COST_LIMIT_USD else 1)" || { echo "cost limit passed, stopping" >&2; exit 3; }
  fi
done
