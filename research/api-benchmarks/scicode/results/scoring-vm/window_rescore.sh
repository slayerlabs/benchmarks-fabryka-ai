#!/usr/bin/env bash
# Re-scores the official step files whose logs were written 20:10-20:20 UTC on 2026-11-22 (disk-full window) and the
# time-outs that ran through it; 3 containers at most, network none, BLAS threads 1, the scoring image.
set -euo pipefail
cd /root/scicode/repo/research/api-benchmarks/scicode
mkdir -p /root/scicode/window
cp /root/scicode/window_rescore.py /root/scicode/window/window_rescore.py
steps() {  # model setting -> steps with logs written in the window, without time-outs
  find "out/$1/score/logs/$1/$2" -newermt "2026-11-22 20:10:00" ! -newermt "2026-11-22 20:20:00" -name '*.txt' \
    | while read -r f; do [[ "$(head -1 "$f")" == "time out" ]] || basename "$f" .txt; done | sort -V | tr '\n' ' '
}
run() {  # tag model setting steps...
  local tag=$1 model=$2 setting=$3
  shift 3
  docker run --rm --network none --memory 48g \
    -v /root/scicode/repo/research/api-benchmarks/scicode:/root/scicode/repo/research/api-benchmarks/scicode:ro \
    -v /root/scicode/repo/research/api-benchmarks/scicode/.cache/hf-scoring:/root/scicode/repo/research/api-benchmarks/scicode/.cache/hf-scoring \
    -v /root/scicode/window:/work -w /root/scicode/repo/research/api-benchmarks/scicode \
    -e HF_HOME=/root/scicode/repo/research/api-benchmarks/scicode/.cache/hf-scoring scicode-scoring \
    python /work/window_rescore.py "$model" "$setting" "$tag" "$@" > "/root/scicode/window/$tag.log" 2>&1
}
FAST="$(steps lfm3-1.7b-nothink without_background)"
echo "nothink fast: $FAST" > /root/scicode/window/steps.txt
echo "lfm3 window: $(steps lfm3-1.7b without_background)" >> /root/scicode/window/steps.txt
run nothink-window lfm3-1.7b-nothink without_background $FAST &
run nothink-64.6 lfm3-1.7b-nothink without_background 64.6 &
run lfm3-63.6 lfm3-1.7b without_background 63.6 &
wait
echo done >> /root/scicode/window/steps.txt
