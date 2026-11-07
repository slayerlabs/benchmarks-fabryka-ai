#!/usr/bin/env bash
# HellaSwag on a vast.ai GPU. Code: git clone of this repo into /workspace/repo.
#   instance.sh setup LIMIT_S
#       safety destroy after LIMIT_S, lockfile environment, both parquets, EuroLLM and Slayer weights
#   instance.sh eurollm
#       EuroLLM-1.7B, 10-shot, full validation -> /workspace/out/eurollm-1.7b-10shot.jsonl.gz
#   instance.sh slayer
#       Slayer 1.06, 10-shot, same code -> /workspace/out/slayer-1.06-10shot.jsonl.gz
#   instance.sh slayer-space
#       Slayer 1.06, 0-shot, for the Space T05 panel -> /workspace/out/slayer-1.06-0shot.jsonl.gz
# Every step appends {"step", "s"} to /workspace/times.jsonl.
# 10-shot needs the train parquet: lm-eval draws the 10 examples from it.
set -euo pipefail
R=/workspace/repo/research
WS=/workspace
export PYTHONUNBUFFERED=1 NVIDIA_TF32_OVERRIDE=0 HF_HUB_DISABLE_PROGRESS_BARS=1 TOKENIZERS_PARALLELISM=false
PY=$WS/venv/bin/python
EUROLLM_REV=c730cd9b616799ace3c65e927d63191446f59374
SLAYER_REV=ef81be58742544ad32e1afab38db011fec209609

timed() {  # timed STEP COMMAND...
  local s=$1 t
  shift
  t=$(date +%s.%N)
  "$@"
  python3 -c "import json,sys,time; print(json.dumps({'step': sys.argv[1], 's': round(time.time()-float(sys.argv[2]), 1)}))" "$s" "$t" >> $WS/times.jsonl
}

score_one() {  # score_one LABEL MODEL PRETRAINED REPO REV FEWSHOT
  timed "score_$1" $PY $R/benchmarks/hellaswag/hellaswag.py score \
    --model "$2" --pretrained "$3" --repo "$4" --revision "$5" \
    --data $WS/data --out $WS/out/$1.jsonl.gz --fewshot "$6" --device cuda --batch 1
}

case "${1:-}" in
  setup)
    nohup python3 $R/slayer-1b/wygaszanie/bezpiecznik.py po "${2:?limit in seconds}" > $WS/bezpiecznik.log 2>&1 &
    python3 $R/slayer-1b/wygaszanie/bezpiecznik.py sprawdz
    timed venv python3 -m venv --system-site-packages $WS/venv
    timed pip $PY -m pip install -q -r $R/common/requirements.lock.txt
    $PY $R/common/slayer_lm.py --install
    timed fetch $PY $R/benchmarks/hellaswag/hellaswag.py fetch --out $WS/data
    timed weights_eurollm $PY -c "from huggingface_hub import snapshot_download as s; s('utter-project/EuroLLM-1.7B', revision='$EUROLLM_REV', local_dir='$WS/eurollm-1.7b')"
    timed weights_slayer $PY -c "from huggingface_hub import snapshot_download as s; s('SlayerLab/Slayer1B-1.06', revision='$SLAYER_REV', local_dir='$WS/slayer-1.06')"
    $PY -c "import torch, json; print(json.dumps({'torch': torch.__version__, 'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(0)}))" | tee $WS/env.json
    ;;
  eurollm)
    score_one eurollm-1.7b-10shot hf $WS/eurollm-1.7b utter-project/EuroLLM-1.7B $EUROLLM_REV 10
    ;;
  slayer)
    score_one slayer-1.06-10shot slayer $WS/slayer-1.06 SlayerLab/Slayer1B-1.06 $SLAYER_REV 10
    ;;
  slayer-space)
    score_one slayer-1.06-0shot slayer $WS/slayer-1.06 SlayerLab/Slayer1B-1.06 $SLAYER_REV 0
    ;;
  *)
    echo "usage: $0 setup LIMIT_S | eurollm | slayer | slayer-space" >&2
    exit 64
    ;;
esac
