#!/usr/bin/env bash
# Simulator probe: the 20 sampled tasks x 2 user simulators, agent = Bielik 11B v3.1 through the Fabryka API.
# Needs ~/.config/claude-api.key (Anthropic key). Costs money: see PROTOCOL.md, "Cost". Do not run without a go.
#   bash run_sim_probe.sh [haiku|sonnet|both]   (default both)
# Prices, USD per million tokens (input/output): Haiku 5.5 0.10/0.50, Sonnet 5.5 2/10. Stops when the running
# Claude cost passes COST_LIMIT_USD (default 5).
set -euo pipefail
source "$(dirname "$0")/common.sh"
WHICH="${1:-both}"
LIMIT="${COST_LIMIT_USD:-5}"
export ANTHROPIC_API_KEY="$(cat "$HOME/.config/claude-api.key")"
export NL_JUDGE_LLM="$AGENT"            # same judge for both arms; Bielik keeps the Claude cost to the simulator only
declare -A MODEL=( [haiku]="anthropic/claude-haiku-5-5" [sonnet]="anthropic/claude-sonnet-5-5" )
declare -A PIN=( [haiku]="0.10" [sonnet]="2" ) POUT=( [haiku]="0.50" [sonnet]="10" )
base=0   # Claude cost of the arms finished so far
for arm in haiku sonnet; do
  [[ "$WHICH" == both || "$WHICH" == "$arm" ]] || continue
  # one-token ping: does the model id work
  "$PY" -c "import litellm; litellm.completion(model='${MODEL[$arm]}', messages=[{'role':'user','content':'OK'}], max_tokens=5)" >/dev/null
  USAGE="$OUT/usage_$arm.jsonl"; export TAU3_USAGE_LOG="$USAGE"; : > "$USAGE"
  for d in "${DOMAINS[@]}"; do
    run_domain "$d" "probe_${arm}_$d" "${MODEL[$arm]}" 0
    c=$("$PY" "$HERE/cost.py" "$USAGE" "${MODEL[$arm]}" "${PIN[$arm]}" "${POUT[$arm]}" | tee -a "$OUT/cost.jsonl" | "$PY" -c "import json,sys; print(json.load(sys.stdin)['cost_usd'])")
    total=$("$PY" -c "print(round($base + $c, 4))")   # c = cost of this arm so far
    echo "$arm $d cost $c total $total USD"
    "$PY" -c "import sys; sys.exit(0 if $total <= $LIMIT else 1)" || { echo "cost limit $LIMIT USD passed, stopping" >&2; exit 3; }
  done
  base=$total
done
