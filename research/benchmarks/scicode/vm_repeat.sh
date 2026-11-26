#!/usr/bin/env bash
# Scores one official step file again N times on coding-judge-vm (window_rescore.py, scoring image, no network, one
# container at a time), for a step whose test is not deterministic; each run's compare.json is copied into
# results/scoring-vm/ as repeat-<model-id>-<setting>-<step>-run<i>.json (scoring_events.py counts them).
# Usage: bash vm_repeat.sh <model-id> <setting> <step> <runs> <work-dir>
# Run 2026-11-23 for lfm3-1.7b-nothink step 14.2, both settings, 10 runs each.
set -euo pipefail
MODEL=$1 SETTING=$2 STEP=$3 RUNS=$4 WORK=$5
C=/root/scicode/check-d83/repo/research/api-benchmarks/scicode
O=/root/scicode/repo/research/api-benchmarks/scicode/out
mkdir -p "$WORK"
for i in $(seq 1 "$RUNS"); do
  docker run --rm --network none --memory 48g -v "$C:$C:ro" -v "$C/.cache/hf-scoring:$C/.cache/hf-scoring" \
    -v "$O:$O:ro" -v "$WORK:/work" -w "$C" -e HF_HOME="$C/.cache/hf-scoring" \
    scicode-scoring python window_rescore.py "$O/$MODEL" "$SETTING" "/work/run$i" "$STEP" > "$WORK/run$i.log" 2>&1
done
