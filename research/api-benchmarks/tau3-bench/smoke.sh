#!/usr/bin/env bash
# Smoke test, not a result: 1 task per domain with Bielik as agent, simulator and NL judge (free API).
# Checks that the chain runs end to end and saves transcripts to out/tau2-bench/data/simulations/smoke_*.
set -euo pipefail
source "$(dirname "$0")/common.sh"
export NL_JUDGE_LLM="$AGENT"
for d in "${DOMAINS[@]}"; do run_domain "$d" "smoke_$d" "$AGENT" 1; done
