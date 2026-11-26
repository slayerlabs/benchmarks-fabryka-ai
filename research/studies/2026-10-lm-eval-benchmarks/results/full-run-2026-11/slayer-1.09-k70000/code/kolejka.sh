#!/usr/bin/env bash
# Measurement queue of PROTOKOL.md on one 8-GPU instance, one background process:
# 1. wagi_70000.pt -> model.safetensors (architecture check, konwertuj.py with the 1.08 template), then the .pt and
#    the template weights are deleted (32 GB disk);
# 2. datasets prepared once, before the runners (they share the cache and the readiness markers);
# 3. one runner per GPU (CUDA_VISIBLE_DEVICES), its pairs from plan_gpu.txt, each with its own results directory;
#    a failed pair is recorded and its runner goes on;
# 4. the per-GPU results merged into one directory, then one export with per-question samples.
# Progress: $WS/logi/kolejka.log; end: $WS/KONIEC.
set -u
K=/workspace/repos/fabryka/research
WS=/workspace
export K WS HF_HOME=$WS/.hf_home PYTHONUNBUFFERED=1 NVIDIA_TF32_OVERRIDE=0 HF_HUB_DISABLE_PROGRESS_BARS=1 NLTK_DATA=$WS/nltk_data
PY=$WS/venv-lock/bin/python
R=$K/tools/ewaluacja/ewaluacja.py
P=$K/studies/2026-10-lm-eval-benchmarks/results/full-run-2026-11/slayer-1.09-k70000/code
P40=$K/studies/2026-10-lm-eval-benchmarks/results/full-run-2026-11/slayer-1.09-k40000/code
WY=$WS/wyniki/k70
LOG=$WS/logi/kolejka.log
REPO=SlayerLab/Slayer1B-1.09-checkpoints
# label | weights file | revision | sha256 of the .pt (SHA256SUMS of the revision)
CKPTS=(
  "slayer1b-1.09-k70000|wagi_70000.pt|adfaf3fd5402bc7f3adbfe077798f20262979433|9ed73494fc139422f5314f72b4f970242454a7ab9d8caceee6b52fe5bdfc40c0"
)

mkdir -p "$WY" "$WS/logi"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%S) $*" >> "$LOG"; }

log start
N_GPU=$(nvidia-smi -L | wc -l)
log "gpu $N_GPU"
if [[ $N_GPU -ne 8 ]]; then log "STOP: plan_gpu.txt needs 8 GPUs"; touch "$WS/KONIEC"; exit 1; fi

WZ=$("$PY" -c "from huggingface_hub import snapshot_download as s; print(s('SlayerLab/Slayer1B-1.08', revision='5f854a0cc7160594d54d1788d37a44e8ebabe16c', allow_patterns=['*.json', '*.txt', '*.py', 'tokenizer*', '*.safetensors']))" 2>> "$LOG" | tail -1)
log "template $WZ"
for c in "${CKPTS[@]}"; do
  IFS='|' read -r ETYK PLIK REW SHA <<< "$c"
  CK=$("$PY" -c "from huggingface_hub import hf_hub_download as h; print(h('$REPO', '$PLIK', revision='$REW'))" 2>> "$LOG" | tail -1)
  log "ckpt $ETYK $CK"
  "$PY" "$P40/sprawdz_architekture.py" "$CK" "$WZ" "$SHA" --wyjscie "$WS/logi/architektura_$ETYK.json" > /dev/null 2>> "$LOG"
  KOD=$?
  log "architecture $ETYK exit $KOD"
  if [[ $KOD -ne 0 ]]; then log "STOP: architecture differs from 1.08"; touch "$WS/KONIEC"; exit 1; fi
  "$PY" "$K/slayer-1b/wygaszanie/konwertuj.py" "$CK" "$WZ" "$K/tools/ewaluacja/modele/$ETYK" --sha256 "$SHA" \
    > "$WS/logi/konwersja_$ETYK.json" 2>> "$LOG"
  log "conversion $ETYK exit $?"
  rm -f "$(readlink -f "$CK")" "$CK"
done
for f in "$WZ"/*.safetensors; do rm -f "$(readlink -f "$f")" "$f"; done
log "disk $(df -h /workspace | tail -1)"

# the 15 tests of PROTOKOL.md (the tests of plan_gpu.txt)
TESTY=T01,T02,T03,T04,T05,T06,T07,T14,T17,T19,T44,T45,T46,T51,T53
"$PY" "$R" --python-lock "$PY" przygotuj --zadania "$TESTY" --cpu 8 > "$WS/logi/przygotuj_zbiory.log" 2>&1
log "datasets exit $?"

for G in 0 1 2 3 4 5 6 7; do
  (
    export CUDA_VISIBLE_DEVICES=$G
    grep -v '^#' "$P/plan_gpu.txt" | awk -v g="$G" '$1 == g {print $2, $3}' | while read -r ETYK ZADANIA; do
      "$PY" "$R" --wyniki "$WS/gpu$G/wyniki" --python-lock "$PY" licz "$ETYK" --zadania "$ZADANIA" \
        --rownolegle "${ROWNOLEGLE:-2}" >> "$WS/logi/runner_gpu$G.log" 2>&1
      log "gpu $G $ETYK $ZADANIA exit $?"
    done
  ) &
done
wait
log "runners done"

# Merge: every (test, model) directory comes from exactly one GPU (plan_gpu.txt), so nothing is overwritten.
for G in 0 1 2 3 4 5 6 7; do
  cp -rn "$WS/gpu$G/wyniki/." "$WY/"
  cat "$WS/gpu$G/czasy.jsonl" >> "$WS/wyniki/czasy.jsonl" 2> /dev/null
done
log "merged $(find "$WY" -name results.json | wc -l) results.json"
"$PY" "$R" --wyniki "$WY" --python-lock "$PY" eksport --wyjscie "$WS/eksport_k70.tgz" > "$WS/logi/eksport.log" 2>&1
log "export exit $?"
sha256sum "$WS/eksport_k70.tgz" > "$WS/eksport_k70.sha256"
touch "$WS/KONIEC"
log end
