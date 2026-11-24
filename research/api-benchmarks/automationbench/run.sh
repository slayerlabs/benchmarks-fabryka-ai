#!/usr/bin/env bash
# AutomationBench (public) for one model: bash run.sh <model-id> [--limit N]
#   bielik-11b-v3.1-vllm  Bielik 11B v3.1 Instruct served by vLLM (start it with vllm.sh) at BASE_URL
#                         (default http://127.0.0.1:8000/v1, served model name "bielik")
#   slayer1b-60000        cannot run the benchmark: writes results/slayer1b-60000.json with score null
# Installs AutomationBench at the pinned commit (uv sync --frozen), runs auto-bench on the six public domains (600
# tasks; the `simple` domain is not part of the score) and writes results/<model-id>.json and .jsonl.gz.
# --limit N runs only the first N tasks and writes to out/. DOMAINS=simple runs the harness's tool-use sanity check.
set -euo pipefail
export PYTHONUTF8=1

MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"
shift
LIMIT=()
if [[ "${1:-}" == "--limit" ]]; then LIMIT=(--num-examples "${2:?--limit needs N}"); fi

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${OUT_DIR:-$HERE/out}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000/v1}"
DOMAINS="${DOMAINS:-public}"
AB_COMMIT="4a8e1061254004d9dac807054eed33fad7d1ff14"

case "$MODEL" in
  bielik-11b-v3.1-vllm) ;;
  slayer1b-60000)
    python3 - "$HERE/results/$MODEL.json" <<'EOF'
import datetime, json, sys
r = {"benchmark": "AutomationBench (public)", "model": "slayer1b-60000", "metric": "pass_rate", "score": None,
     "stderr": None, "n": 0, "date": datetime.date.today().isoformat(),
     "harness": "https://github.com/zapier/AutomationBench @ 4a8e1061254004d9dac807054eed33fad7d1ff14",
     "data": "bundled with the harness, public domains", "settings": {},
     "score_null_reason": "Slayer 1B is a base model without a chat template or tool-calling format; the serving "
                          "endpoint rejects requests with tools (HTTP 400), so no syntactically valid call is possible.",
     "deviations": "see README.md, Deviations"}
open(sys.argv[1], "w", encoding="utf-8", newline="\n").write(json.dumps(r, indent=2) + "\n")
EOF
    exit 0 ;;
  *) echo "unknown model-id: $MODEL (bielik-11b-v3.1-vllm | slayer1b-60000)" >&2; exit 2 ;;
esac
curl -sf "$BASE_URL/models" | grep -q '"bielik"' || { echo "no model \"bielik\" at $BASE_URL (start vllm.sh first)" >&2; exit 1; }

mkdir -p "$OUT"
REPO="$OUT/AutomationBench"
if [[ ! -d "$REPO/.git" ]]; then
  git init -q "$REPO"
  git -C "$REPO" fetch -q --depth 1 https://github.com/zapier/AutomationBench.git "$AB_COMMIT"
  git -C "$REPO" checkout -q FETCH_HEAD
fi
[[ "$(git -C "$REPO" rev-parse HEAD)" == "$AB_COMMIT" ]] || { echo "AutomationBench checkout is not $AB_COMMIT" >&2; exit 1; }
cd "$REPO"
uv sync -q --frozen --no-dev

# LFM3-1.7B card: temperature 0.6, top_p 0.95, up to 50 turns, no output limit other than the context. The chat
# template's defaults (provider system prompt, date pinned to the run) are sent explicitly, as vllm.sh sets them.
EXTRA='{"temperature": 0.6, "top_p": 0.95, "seed": 20261119, "chat_template_kwargs": {"provider_system_prompt": true, "current_date": "2026-11-18", "current_day_of_week": "Wednesday"}}'
# SHARED_SERVER records whether the vLLM server also served other benchmarks during the run (affects timeouts
# and step limits, not decoding); the committed Bielik run: "the same vLLM server also served other benchmarks during the run".
SETTINGS=$(SHARED_SERVER="${SHARED_SERVER:-no}" python3 -c 'import json, os; print(json.dumps({"temperature": 0.6, "top_p": 0.95, "seed": 20261119, "max_tokens_per_turn": None, "max_concurrent": 16, "shared_server": os.environ["SHARED_SERVER"]}))')
mkdir -p results
uv run -q --frozen auto-bench --model bielik --base-url "$BASE_URL" --api-key EMPTY --api chat_completions \
  --toolset api --domains "$DOMAINS" --max-steps 50 --max-concurrent "${CONCURRENCY:-16}" "${LIMIT[@]}" \
  --extra-body "$EXTRA" --input-cost 0 --output-cost 0 --export-json "results/$MODEL-$DOMAINS.json"

if [[ "$DOMAINS" != public ]]; then echo "sanity run ($DOMAINS): results/$MODEL-$DOMAINS.json, not summarized"; exit 0; fi
TARGET="$HERE/results/$MODEL"; SUM_ARGS=()
if [[ ${#LIMIT[@]} -gt 0 ]]; then TARGET="$OUT/limit/$MODEL"; SUM_ARGS=(--limit); fi
python3 "$HERE/summarize.py" "results/$MODEL-public.json" "$TARGET" "$SETTINGS" "${SUM_ARGS[@]}"
