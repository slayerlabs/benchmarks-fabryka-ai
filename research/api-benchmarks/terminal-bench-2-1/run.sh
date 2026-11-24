#!/usr/bin/env bash
# Terminal-Bench 2.1 with the OpenCode agent through Harbor: bash run.sh <model-id> [--limit N]
#   lfm3-1.7b        LiquidAI/LFM3-1.7B, served by vllm.sh as "lfm3"
#   bielik-11b-v3.1  speakleash/Bielik-11B-v3.1-Instruct, served by vllm.sh as "bielik"
#   slayer1b-<step>  writes the null result (base model, no tool calls; see README)
# The model server (vllm.sh) runs first. Every task runs in its own Docker container on this machine, so the
# server must be reachable from the containers: BASE_URL (default http://host.docker.internal:8000/v1).
# TRIALS (default 5) attempts per task, CONCURRENCY tasks at a time (default 8, as in the LFM3 main job; the LFM3
# re-runs used 4). Concurrency is part of the setup: tasks have wall-clock limits (README, Deviations).
# --limit N runs the first N tasks (by name) once each and writes to out/limit/.
# TASKS="a b" runs only those tasks, as job JOB_NAME (default <model-id>-rerun); used to re-run trials that have no
# test result (see README, "Re-runs").
# Needs: Docker, git, uv. No API key: the server is ours.
set -euo pipefail

MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"
shift
LIMIT=""
if [[ "${1:-}" == "--limit" ]]; then LIMIT="${2:?--limit needs N}"; fi

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${OUT_DIR:-$HERE/out}"
HARBOR_VERSION="0.27.0"
OPENCODE_VERSION="1.19.6"
DATASET_REPO="https://github.com/harbor-framework/terminal-bench-2-1.git"
DATASET_COMMIT="12b7565679ce5006230b820666353673a133db93"
BASE_URL="${BASE_URL:-http://host.docker.internal:8000/v1}"
TRIALS="${TRIALS:-5}"
CONCURRENCY="${CONCURRENCY:-8}"
# LFM3-1.7B card: temperature 0.6, top_p 0.95, no output limit other than the context; OpenCode, up to 100 turns.
TEMPERATURE="0.6"
TOP_P="0.95"
STEPS="100"

case "$MODEL" in
  lfm3-1.7b) SERVED="lfm3"; CONTEXT="${MAX_MODEL_LEN:-262144}"; OUTPUT="$CONTEXT" ;;
  # vLLM rejects a request whose prompt plus max_tokens exceeds the context, and OpenCode asks for up to 32000
  # output tokens, which alone fills Bielik's 32768. 8192 leaves the rest of the window to the conversation.
  bielik-11b-v3.1) SERVED="bielik"; CONTEXT="${MAX_MODEL_LEN:-32768}"; OUTPUT="${MAX_OUTPUT:-8192}" ;;
  slayer1b-*)
    mkdir -p "$HERE/results"
    exec python3 "$HERE/summarize.py" --null "$MODEL" --out "$HERE/results/$MODEL.json" ;;
  *) echo "unknown model-id: $MODEL (lfm3-1.7b | bielik-11b-v3.1 | slayer1b-<step>)" >&2; exit 2 ;;
esac

DATA="$OUT/terminal-bench-2-1"
if [[ ! -d "$DATA/.git" ]]; then
  git init -q "$DATA"
  git -C "$DATA" fetch -q --depth 1 "$DATASET_REPO" "$DATASET_COMMIT"
  git -C "$DATA" checkout -q FETCH_HEAD
fi
[[ "$(git -C "$DATA" rev-parse HEAD)" == "$DATASET_COMMIT" ]] || { echo "dataset is not at $DATASET_COMMIT" >&2; exit 1; }

JOBS="$OUT/jobs"
NAME="$MODEL"
TASKS_YAML=""
if [[ -n "${TASKS:-}" ]]; then
  NAME="${JOB_NAME:-$MODEL-rerun}"
  TASKS_YAML="    task_names: [$(printf '"%s",' $TASKS | sed 's/,$//')]"
fi
if [[ -n "$LIMIT" ]]; then
  JOBS="$OUT/limit"
  NAME="$MODEL-limit-$LIMIT"
  TRIALS=1
  TASKS_YAML="    task_names: [$(find "$DATA/tasks" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort | head -n "$LIMIT" \
    | sed 's/.*/"&"/' | paste -sd, -)]"
fi

mkdir -p "$JOBS"
CONFIG="$JOBS/$NAME.yaml"
cat > "$CONFIG" <<EOF
job_name: $NAME
jobs_dir: $JOBS
n_attempts: $TRIALS
n_concurrent_trials: $CONCURRENCY
environment:
  type: docker
  delete: true
agents:
  - import_path: opencode_agent:OpenCodeAptFallback
    model_name: local/$SERVED
    kwargs:
      version: "$OPENCODE_VERSION"
      opencode_config:
        provider:
          local:
            # OpenCode installs this package itself and takes no version here (README, Deviations).
            npm: "@ai-sdk/openai-compatible"
            options:
              baseURL: "$BASE_URL"
              apiKey: "EMPTY"
            models:
              $SERVED:
                limit:
                  context: $CONTEXT
                  output: $OUTPUT
        agent:
          build:
            temperature: $TEMPERATURE
            top_p: $TOP_P
            steps: $STEPS
datasets:
  - path: $DATA/tasks
$TASKS_YAML
EOF

PYTHONPATH="$HERE${PYTHONPATH:+:$PYTHONPATH}" uvx --from "harbor==$HARBOR_VERSION" harbor run -c "$CONFIG"
echo "Harbor job in $JOBS/$NAME. Results: python3 $HERE/summarize.py $JOBS/$NAME --model $MODEL"
