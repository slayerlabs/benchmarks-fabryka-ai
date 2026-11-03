#!/usr/bin/env bash
# BLiMP: Pythia-1B v0 control and agreement with lm-eval on one vast.ai GPU (LM_EVAL_PROTOCOL.md).
# Code: research/ copied to $WS/repo/research. Everything after `start` runs in one background process:
#   lm_eval_instance.sh hf_test          MB/s of the first 1 GB of the Pythia v0 weights from HF
#   lm_eval_instance.sh start LIMIT_S    safety destroy after LIMIT_S and 1200 s after the end, then `queue` in the
#                                        background: venv + downloads in parallel, P1, P4, P2, P3, extraction, comparison
#   lm_eval_instance.sh state            state files, last log lines, GPU
# Results: $WS/out (layout of benchmarks/blimp/results), $WS/state/{ok,error,end}; per step $WS/state/<step>.{ok,error}
# (a failed step is recorded and the queue goes on). Local CPU smoke test (no safety destroy, existing venv and weights):
#   WS=<dir> R=<research> PY=<python> DEVICE=cpu LIMIT=5 TASKS=blimp_adjunct_island,blimp_anaphor_gender_agreement \
#   PYTHIA_DIR=<dir> SLAYER_DIR=<dir> SKIP_SETUP=1 bash lm_eval_instance.sh queue
set -euo pipefail
WS=${WS:-/workspace}
R=${R:-$WS/repo/research}
PY=${PY:-$WS/venv/bin/python}
DEVICE=${DEVICE:-cuda}
BATCH=${BATCH:-64}
LIMIT=${LIMIT:-}
TASKS=${TASKS:-blimp}
PYTHIA_DIR=${PYTHIA_DIR:-$WS/pythia-1b-v0}
SLAYER_DIR=${SLAYER_DIR:-$WS/slayer-1.06}
export BLIMP_DIR=${BLIMP_DIR:-$WS/blimp_data}
export PYTHONUNBUFFERED=1 NVIDIA_TF32_OVERRIDE=0 HF_HUB_DISABLE_PROGRESS_BARS=1 TOKENIZERS_PARALLELISM=false
ST=$WS/state
OUT=$WS/out
LOGS=$WS/logs
PYTHIA_REV=step143000
SLAYER_REV=ef81be58742544ad32e1afab38db011fec209609
BLIMP_REV=877fba0801ffb7cbd8c39c1ff314a46f053f6036
mkdir -p "$ST" "$OUT" "$LOGS"

timed() {  # timed STEP COMMAND... : appends {"step", "s", "exit"} to times.jsonl, returns the exit code
  local s=$1 t rc=0
  shift
  t=$(python3 -c "import time; print(time.time())")
  "$@" || rc=$?
  python3 -c "import json,sys,time; print(json.dumps({'step': sys.argv[1], 's': round(time.time()-float(sys.argv[2]), 1), 'exit': int(sys.argv[3])}))" "$s" "$t" "$rc" >> $OUT/times.jsonl
  return $rc
}

step() {  # step NAME COMMAND... : state file per step, the queue goes on after an error
  local n=$1
  shift
  rm -f "$ST/$n.ok" "$ST/$n.error"
  if timed "$n" "$@" > "$LOGS/$n.log" 2>&1; then touch "$ST/$n.ok"; else touch "$ST/$n.error"; echo "step $n failed" >&2; fi
}

lm_eval_cli() {  # lm-eval CLI with the `slayer` model registered from this checkout (no .pth needed)
  $PY -c "import sys; sys.path.insert(0, sys.argv.pop(1)); import slayer_lm; from lm_eval.__main__ import cli_evaluate; sys.argv[0] = 'lm_eval'; cli_evaluate()" "$R/common" "$@"
}

sha() {  # sha256 lines in the sha256sum format (GNU on the instance, shasum on macOS)
  if command -v sha256sum > /dev/null; then sha256sum "$@"; else shasum -a 256 "$@"; fi
}

# Functions below run inside `if` (step), where `set -e` does not apply: every command is chained with &&.
ours() {  # ours LABEL MODEL_DIR -> $OUT/<LABEL>.jsonl.gz (our scorer, hipoteza_formatu.py licz --zadania blimp)
  local d=$WS/ours/$1
  rm -rf "$d" &&
  PYTHONPATH=$R/benchmarks/blimp $PY $R/common/hipoteza_formatu.py licz --model "$2" --zadania blimp --wyjscie "$d" --device $DEVICE --batch $BATCH ${LIMIT:+--limit $LIMIT} &&
  mkdir -p "$(dirname $OUT/$1)" &&
  gzip -c "$d/blimp.jsonl" > "$OUT/$1.jsonl.gz"
}

lm_eval_run() {  # lm_eval_run LABEL MODEL MODEL_ARGS -> raw samples in $WS/lm-eval-raw/LABEL, compact rows in $OUT/lm-eval/LABEL.jsonl.gz
  local d=$WS/lm-eval-raw/$1
  rm -rf "$d" &&
  lm_eval_cli --model "$2" --model_args "$3" --tasks $TASKS --batch_size $BATCH --device $DEVICE \
    --output_path "$d" --log_samples ${LIMIT:+--limit $LIMIT} &&
  $PY $R/benchmarks/blimp/lm_eval_compare.py extract --samples "$d" --out "$OUT/lm-eval/$1.jsonl.gz" &&
  mkdir -p $OUT/lm-eval-raw &&
  tar -czf "$OUT/lm-eval-raw/$1.tar.gz" -C "$WS/lm-eval-raw" "$1"
}

download() {  # download REPO REVISION DIR [dataset]
  $PY -c "import sys; from huggingface_hub import snapshot_download as s; print(s(sys.argv[1], revision=sys.argv[2], local_dir=sys.argv[3], repo_type=sys.argv[4]))" "$1" "$2" "$3" "${4:-model}"
}

prewarm_lm_eval_data() {  # the 67 blimp configs as lm-eval loads them (path `blimp`, no pinned revision)
  $PY - <<'EOF'
import glob, json, os, yaml
import lm_eval
d = os.path.join(os.path.dirname(lm_eval.__file__), "tasks", "blimp")
names = sorted(yaml.safe_load(open(f))["dataset_name"] for f in glob.glob(os.path.join(d, "*.yaml")) if not f.endswith("_blimp.yaml"))
import datasets
for n in names:
    datasets.load_dataset("blimp", n)
print(json.dumps({"configs": len(names)}))
EOF
}

environment() {
  $PY - "$OUT/env.json" <<'EOF'
import glob, json, os, platform, subprocess, sys
import torch, transformers, lm_eval, datasets
from importlib.metadata import version
env = {"python": platform.python_version(), "torch": torch.__version__, "cuda": torch.version.cuda,
       "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
       "transformers": transformers.__version__, "lm_eval": version("lm_eval"), "datasets": datasets.__version__,
       "NVIDIA_TF32_OVERRIDE": os.environ.get("NVIDIA_TF32_OVERRIDE"),
       "hf_dataset_snapshots": sorted(glob.glob(os.path.expanduser("~/.cache/huggingface/hub/datasets--*blimp*/snapshots/*"))),
       # datasets caches each config under blimp/<config>/0.0.0/<dataset revision>: the revision lm-eval loaded
       "lm_eval_dataset_revisions": sorted({p.rstrip("/").split("/")[-1] for p in glob.glob(os.path.expanduser("~/.cache/huggingface/datasets/blimp/*/*/*/"))}),
       "lm_eval_dataset_configs": len(glob.glob(os.path.expanduser("~/.cache/huggingface/datasets/blimp/*/")))}
try:
    env["nvidia_smi"] = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
                                       capture_output=True, text=True).stdout.strip()
except OSError:
    pass
open(sys.argv[1], "w").write(json.dumps(env, indent=1) + "\n")
print(json.dumps(env))
EOF
}

setup() {
  timed venv python3 -m venv --system-site-packages $WS/venv &&
  timed pip_hub $PY -m pip install -q huggingface_hub==0.36.2 hf-xet==1.7.1 || return 1
  # weights and data download while the lockfile installs
  ( timed weights_pythia download EleutherAI/pythia-1b-v0 $PYTHIA_REV $PYTHIA_DIR > $LOGS/dl_pythia.log 2>&1 && touch $ST/dl_pythia.ok ) &
  ( timed weights_slayer download SlayerLab/Slayer1B-1.06 $SLAYER_REV $SLAYER_DIR > $LOGS/dl_slayer.log 2>&1 && touch $ST/dl_slayer.ok ) &
  ( timed data_blimp download nyu-mll/blimp $BLIMP_REV $BLIMP_DIR dataset > $LOGS/dl_blimp.log 2>&1 && touch $ST/dl_blimp.ok ) &
  local rc=0
  timed pip $PY -m pip install -q -r $R/common/requirements.lock.txt || rc=$?
  wait
  [[ $rc == 0 ]] || return 1
  for f in dl_pythia dl_slayer dl_blimp; do [[ -f $ST/$f.ok ]] || { echo "download $f failed"; return 1; }; done
  sha $PYTHIA_DIR/pytorch_model.bin $PYTHIA_DIR/tokenizer.json $SLAYER_DIR/model.safetensors $SLAYER_DIR/tokenizer.json > $OUT/weights.sha256 &&
  (cd $SLAYER_DIR && sha256sum -c SHA256SUMS) >> $OUT/weights.sha256
}

queue() {
  rm -f $ST/ok $ST/error $ST/end
  [[ -n ${SKIP_SETUP:-} ]] || step setup setup
  ( step prewarm prewarm_lm_eval_data ) &
  local pw=$!
  step p1_ours_pythia_v0 ours pythia-1b-v0/blimp $PYTHIA_DIR
  step p4_ours_slayer ours gpu-check/slayer-1.06 $SLAYER_DIR
  wait $pw || true
  step p2_lm_eval_pythia_v0 lm_eval_run pythia-1b-v0 hf "pretrained=$PYTHIA_DIR,dtype=float32"
  step p3_lm_eval_slayer lm_eval_run slayer-1.06 slayer "pretrained=$SLAYER_DIR,dtype=float32"
  step environment environment
  step compare $PY $R/benchmarks/blimp/lm_eval_compare.py compare --results $OUT --out $OUT/lm_eval_agreement.json ${LIMIT:+--partial}
  cp $LOGS/*.log $OUT/ 2>/dev/null || true
  (cd $OUT && find . -type f ! -name SHA256SUMS | sort | while read -r f; do sha "$f"; done > SHA256SUMS) || true
  if ls $ST/*.error > /dev/null 2>&1; then touch $ST/error; else touch $ST/ok; fi
  touch $ST/end
}

case "${1:-}" in
  hf_test)
    curl -sL -r 0-1073741823 -o /dev/null -w '{"bytes": %{size_download}, "MB_s": %{speed_download}}\n' \
      "https://huggingface.co/EleutherAI/pythia-1b-v0/resolve/$PYTHIA_REV/pytorch_model.bin" \
      | python3 -c "import json,sys; d=json.load(sys.stdin); d['MB_s']=round(d['MB_s']/1e6,1); print(json.dumps(d))"
    ;;
  start)
    LIM=${2:?safety limit in seconds}
    nohup python3 $R/slayer-1b/wygaszanie/bezpiecznik.py po "$LIM" > $LOGS/safety_limit.log 2>&1 &
    nohup python3 $R/slayer-1b/wygaszanie/bezpiecznik.py po_pliku $ST/end 1200 > $LOGS/safety_idle.log 2>&1 &
    python3 $R/slayer-1b/wygaszanie/bezpiecznik.py sprawdz
    nohup bash $R/benchmarks/blimp/lm_eval_instance.sh queue > $LOGS/queue.log 2>&1 &
    echo "queue pid $!, log $LOGS/queue.log"
    ;;
  queue)
    queue
    ;;
  state)
    ls $ST; tail -n 3 $LOGS/queue.log 2>/dev/null; tail -n 4 $OUT/times.jsonl 2>/dev/null
    for f in $LOGS/p*.log; do [[ -f $f ]] && { echo "== $f"; tail -c 300 "$f"; echo; }; done
    nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader 2>/dev/null || true
    ;;
  *)
    echo "usage: $0 hf_test | start LIMIT_S | queue | state" >&2
    exit 64
    ;;
esac
