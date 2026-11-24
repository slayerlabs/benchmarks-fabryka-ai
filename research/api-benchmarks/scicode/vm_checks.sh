#!/usr/bin/env bash
# Checks run on coding-judge-vm after the final scoring (PROTOCOL.md Amendment 2, README Deviations), in the scoring
# image without network, at most 4 containers: window_rescore.py on the official steps whose verdicts were written
# around the disk-full window (the step list from the first, unchecked re-scoring of 2026-11-23) and the two time-outs
# that ran through it; reference_extraction.py for Bielik. Code from a clean clone ($C), the scored out dirs ($O)
# read-only; outputs in /root/scicode/round1/<tag>/, copied into results/scoring-vm/ as window-<tag>.json and
# reference-extraction-<model-id>.json.
set -euo pipefail
C=/root/scicode/check-d83/repo/research/api-benchmarks/scicode
O=/root/scicode/repo/research/api-benchmarks/scicode/out
mkdir -p /root/scicode/round1
run() {  # tag command...
  local tag=$1
  shift
  mkdir -p "/root/scicode/round1/$tag"
  docker run --rm --network none --memory 48g -v "$C:$C:ro" -v "$C/.cache/hf-scoring:$C/.cache/hf-scoring" \
    -v "$O:$O:ro" -v "/root/scicode/round1/$tag:/work" -w "$C" -e HF_HOME="$C/.cache/hf-scoring" \
    scicode-scoring python "$@" > "/root/scicode/round1/$tag.log" 2>&1
}
FAST="$(cat /root/scicode/window/steps.txt | sed -n 's/^nothink fast: //p')"
run nothink-window window_rescore.py "$O/lfm3-1.7b-nothink" without_background /work $FAST &
run nothink-64.6 window_rescore.py "$O/lfm3-1.7b-nothink" without_background /work 64.6 &
run lfm3-63.6 window_rescore.py "$O/lfm3-1.7b" without_background /work 63.6 &
run reference-bielik reference_extraction.py "$O/bielik-11b-v3.1" /work &
wait
echo done > /root/scicode/round1/done.txt
