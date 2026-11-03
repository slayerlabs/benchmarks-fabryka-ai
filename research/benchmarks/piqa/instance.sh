#!/usr/bin/env bash
# PIQA on a vast.ai GPU (PROTOCOL.md). Code: git clone of this repo into /workspace/repo.
#   instance.sh setup LIMIT_S   safety destroy after LIMIT_S, lockfile environment, data + Space files, weights
#   instance.sh pythia LABEL    Pythia-1B v0 @ step143000, full validation -> /workspace/out/LABEL.jsonl.gz
#   instance.sh slayer          Slayer 1.06 @ ef81be58, full validation -> /workspace/out/slayer-1.06.jsonl.gz
# Every step appends {"step", "s"} to /workspace/times.jsonl.
set -euo pipefail
R=/workspace/repo/research
WS=/workspace
export PYTHONUNBUFFERED=1 NVIDIA_TF32_OVERRIDE=0 HF_HUB_DISABLE_PROGRESS_BARS=1 TOKENIZERS_PARALLELISM=false
PY=$WS/venv/bin/python
SLAYER_REV=ef81be58742544ad32e1afab38db011fec209609

timed() {  # timed STEP COMMAND...
  local s=$1 t
  shift
  t=$(date +%s.%N)
  "$@"
  python3 -c "import json,sys,time; print(json.dumps({'step': sys.argv[1], 's': round(time.time()-float(sys.argv[2]), 1)}))" "$s" "$t" >> $WS/times.jsonl
}

case "${1:-}" in
  setup)
    nohup python3 $R/slayer-1b/wygaszanie/bezpiecznik.py po "${2:?limit in seconds}" > $WS/bezpiecznik.log 2>&1 &
    python3 $R/slayer-1b/wygaszanie/bezpiecznik.py sprawdz
    # venv with the image's torch (same 2.8.0 as the lockfile), the rest from the lockfile
    timed venv python3 -m venv --system-site-packages $WS/venv
    timed pip $PY -m pip install -q -r $R/common/requirements.lock.txt
    $PY $R/common/slayer_lm.py --install
    timed fetch $PY $R/benchmarks/piqa/piqa.py fetch --out $WS/data
    timed weights_slayer $PY -c "from huggingface_hub import snapshot_download as s; s('SlayerLab/Slayer1B-1.06', revision='$SLAYER_REV', local_dir='$WS/slayer-1.06')"
    timed weights_pythia $PY -c "from huggingface_hub import snapshot_download as s; s('EleutherAI/pythia-1b-v0', revision='step143000')"
    $PY -c "import torch, json; print(json.dumps({'torch': torch.__version__, 'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(0)}))" | tee $WS/env.json
    ;;
  pythia)
    timed "score_${2:?label}" $PY $R/benchmarks/piqa/piqa.py score --model hf --pretrained EleutherAI/pythia-1b-v0 \
      --repo EleutherAI/pythia-1b-v0 --revision step143000 --data $WS/data --out $WS/out/$2.jsonl.gz --device cuda --batch 1
    ;;
  slayer)
    timed score_slayer $PY $R/benchmarks/piqa/piqa.py score --model slayer --pretrained $WS/slayer-1.06 \
      --repo SlayerLab/Slayer1B-1.06 --revision $SLAYER_REV --data $WS/data --out $WS/out/slayer-1.06.jsonl.gz \
      --device cuda --batch 1
    ;;
  *)
    echo "usage: $0 setup LIMIT_S | pythia LABEL | slayer" >&2
    exit 64
    ;;
esac
