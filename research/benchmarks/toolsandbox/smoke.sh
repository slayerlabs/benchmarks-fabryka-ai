#!/usr/bin/env bash
# Smoke test, not a result: 2 scenarios with Bielik 11B v3.1 (Fabryka AI API) as agent AND user simulator (free).
# Checks that the chain runs end to end and saves transcripts to out/data/smoke/.
set -euo pipefail
source "$(dirname "$0")/common.sh"
cd "$OUT"
"$PY" "$HERE/ts_run.py" --agent GPT_4_o_2024_05_13 --user GPT_4_o_2024_05_13 --parallel 1 -o "$OUT/data/smoke" \
  -s send_message_with_contact_content_cellular_off_multiple_user_turn \
     find_temperature_f_with_location_and_time_diff_multiple_user_turn
