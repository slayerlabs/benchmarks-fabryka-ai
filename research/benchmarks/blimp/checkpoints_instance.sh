#!/usr/bin/env bash
# BLiMP over checkpoints and weight averaging on a vast.ai GPU (benchmarks/blimp/results/CHECKPOINTS_THRESHOLDS.md).
# Code in /workspace/kod (= research/). Long stages run in the background (nohup) and end with
# /workspace/stan/<name>.ok or .blad; every timed step appends a JSON line to /workspace/czasy.jsonl.
#   przygotuj LIMIT_S        safety destroy after LIMIT_S, dependencies, 1.06 weights, BLiMP data
#   kalibracja               GPU comparison job: ckpt 13848 -> BLiMP, ckpts 13800 + 13750 -> avg3 -> BLiMP
#   punkty "REPO:STEP ..."   curve points: download, convert, BLiMP, delete
#   srednie                  avg5 + avg10 (ckpts 13848..13400 of 1.06) -> BLiMP
#   heldout "MODEL ..."      held-out windows of the annealing run (dane.py) and loss of each model dir
#   stan                     state files, last log lines, GPU
# Instance files map to the repo as: czasy.jsonl -> results/checkpoints/times_<gpu>.jsonl,
# logi/konwersje.jsonl -> conversions.jsonl, logi/srednie.jsonl -> averages.jsonl, logi/punkty.log -> points_<gpu>.log,
# wyniki/<label>/blimp.jsonl.gz -> <label>.jsonl.gz, wyniki/heldout_statystyki.json -> heldout_stats.json.
set -euo pipefail
K=/workspace/kod
WS=/workspace
ST=$WS/stan
CZ=$WS/czasy.jsonl
mkdir -p "$ST" "$WS/wyniki" "$WS/logi" "$WS/ckpt"
export PYTHONUNBUFFERED=1 NVIDIA_TF32_OVERRIDE=0 HF_HUB_DISABLE_PROGRESS_BARS=1
export BLIMP_DIR=$WS/blimp_dane
R06=ef81be58742544ad32e1afab38db011fec209609
RB=877fba0801ffb7cbd8c39c1ff314a46f053f6036

teraz() { date +%s.%N; }
zapisz_czas() {  # zapisz_czas ETAP START [JSON-fields]
  python3 -c "import json,sys,time; d={'etap':sys.argv[1],'s':round(time.time()-float(sys.argv[2]),1)}; d.update(json.loads(sys.argv[3] if len(sys.argv)>3 else '{}')); print(json.dumps(d))" "$@" >> "$CZ"
}

w_tle() {  # w_tle NAME COMMAND...
  local n=$1; shift
  rm -f "$ST/$n.ok" "$ST/$n.blad"
  nohup bash -c "( $* ) && touch $ST/$n.ok || touch $ST/$n.blad" > "$WS/logi/$n.log" 2>&1 &
  echo "start $n (pid $!), log $WS/logi/$n.log"
}

blimp() {  # blimp LABEL MODEL_DIR : full BLiMP, GPU/CPU sampled every 2 s
  local E=$1 M=$2 t
  mkdir -p "$WS/wyniki/$E"
  python $K/benchmarks/blimp/sample_gpu.py "$WS/logi/probki_$E.csv" &
  local PG=$!
  t=$(teraz)
  python $K/common/hipoteza_formatu.py licz --model "$M" --zadania blimp --wyjscie "$WS/wyniki/$E" --device cuda --batch 64
  kill $PG || true
  local n
  n=$(wc -l < "$WS/wyniki/$E/blimp.jsonl")
  zapisz_czas "blimp" "$t" "$(python $K/benchmarks/blimp/sample_gpu.py --podsumuj "$WS/logi/probki_$E.csv" | python -c "import json,sys; d=json.load(sys.stdin); d.update(model='$E', pary=$n); print(json.dumps(d))")"
  gzip -kf "$WS/wyniki/$E/blimp.jsonl"
}

ckpt() {  # ckpt REPO STEP [porownaj|zostaw]
  local R=$1 S=$2 tryb=${3:-} t
  python $K/benchmarks/blimp/download_checkpoint.py "SlayerLab/Slayer1B-$R-checkpoints" "$S" $WS/ckpt --log "$CZ"
  t=$(teraz)
  python $K/slayer-1b/wygaszanie/konwertuj.py $WS/ckpt/ckpt_$S.pt $WS/m106 $WS/model_$S $([[ $tryb == porownaj ]] && echo --porownaj) \
    | tee -a $WS/logi/konwersje.jsonl
  zapisz_czas "konwersja" "$t" "{\"krok\": $S}"
  [[ $tryb == porownaj || $tryb == zostaw ]] || rm -f $WS/ckpt/ckpt_$S.pt
}

etap=${1:-}
case "$etap" in
  przygotuj)
    LIMIT=${2:?safety limit in seconds}
    nohup python $K/slayer-1b/wygaszanie/bezpiecznik.py po "$LIMIT" > $WS/logi/bezpiecznik.log 2>&1 &
    python $K/slayer-1b/wygaszanie/bezpiecznik.py sprawdz
    t=$(teraz); pip install -q tokenizers safetensors "huggingface_hub[hf_xet]" datasets pyarrow numpy; zapisz_czas pip "$t"
    t=$(teraz)
    python -c "from huggingface_hub import snapshot_download as s; s('SlayerLab/Slayer1B-1.06', revision='$R06', local_dir='$WS/m106')"
    zapisz_czas "pobranie_1.06" "$t" "{\"bajty\": $(du -sb $WS/m106 | cut -f1)}"
    t=$(teraz)
    python -c "from huggingface_hub import snapshot_download as s; s('nyu-mll/blimp', repo_type='dataset', revision='$RB', local_dir='$BLIMP_DIR')"
    zapisz_czas "pobranie_blimp" "$t"
    python -c "import torch, json; print(json.dumps({'torch': torch.__version__, 'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(0)}))" | tee $WS/srodowisko.json
    nproc; free -g; df -h $WS; nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
    ;;
  kalibracja)
    w_tle kalibracja "set -e; source $K/benchmarks/blimp/checkpoints_instance.sh _funkcje; \
      ckpt 1.06 13848 porownaj; blimp k13848 $WS/model_13848; \
      python $K/benchmarks/blimp/download_checkpoint.py SlayerLab/Slayer1B-1.06-checkpoints 13800 $WS/ckpt --log $CZ; \
      python $K/benchmarks/blimp/download_checkpoint.py SlayerLab/Slayer1B-1.06-checkpoints 13750 $WS/ckpt --log $CZ; \
      t=\$(teraz); python $K/benchmarks/blimp/average_weights.py --wzor $WS/m106 --wyjscie $WS --zapisz 3 \
        $WS/ckpt/ckpt_13848.pt $WS/ckpt/ckpt_13800.pt $WS/ckpt/ckpt_13750.pt | tee -a $WS/logi/srednie.jsonl; \
      zapisz_czas srednia_avg3 \$t; blimp avg3 $WS/avg3"
    ;;
  punkty)
    w_tle punkty "set -e; source $K/benchmarks/blimp/checkpoints_instance.sh _funkcje; \
      for p in $2; do R=\${p%%:*}; S=\${p##*:}; ckpt \$R \$S; blimp k\$S $WS/model_\$S; rm -rf $WS/model_\$S; done"
    ;;
  srednie)
    w_tle srednie "set -e; source $K/benchmarks/blimp/checkpoints_instance.sh _funkcje; \
      for S in 13848 13800 13750 13700 13650 13600 13550 13500 13450 13400; do \
        [[ -f $WS/ckpt/ckpt_\$S.pt ]] || python $K/benchmarks/blimp/download_checkpoint.py SlayerLab/Slayer1B-1.06-checkpoints \$S $WS/ckpt --log $CZ; done; \
      t=\$(teraz); python $K/benchmarks/blimp/average_weights.py --wzor $WS/m106 --wyjscie $WS --zapisz 3,5,10 --usun \
        \$(for S in 13848 13800 13750 13700 13650 13600 13550 13500 13450 13400; do echo $WS/ckpt/ckpt_\$S.pt; done) \
        | tee -a $WS/logi/srednie.jsonl; zapisz_czas srednie_3_5_10 \$t; \
      [[ -f $WS/wyniki/avg3/blimp.jsonl ]] || blimp avg3 $WS/avg3; blimp avg5 $WS/avg5; blimp avg10 $WS/avg10"
    ;;
  heldout)
    w_tle heldout "set -e; source $K/benchmarks/blimp/checkpoints_instance.sh _funkcje; \
      t=\$(teraz); python $K/slayer-1b/wygaszanie/dane.py --tokenizer $WS/m106/tokenizer.json --wyjscie $WS/dane --procesy \$(nproc); \
      zapisz_czas dane \$t; cp $WS/dane/statystyki.json $WS/wyniki/heldout_statystyki.json; \
      for M in $2; do t=\$(teraz); python $K/slayer-1b/wygaszanie/heldout.py --model $WS/\$M --dane $WS/dane --wyjscie $WS/wyniki/heldout_\$M.json; \
        zapisz_czas heldout \$t \"{\\\"model\\\": \\\"\$M\\\"}\"; done"
    ;;
  stan)
    ls -la $ST; for f in $WS/logi/*.log; do echo "== $f"; tail -n 2 "$f"; done; tail -n 5 $CZ 2>/dev/null
    nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv; df -h $WS | tail -1
    ;;
  _funkcje) ;;  # sourced: functions only
  *)
    echo "stages: przygotuj LIMIT_S | kalibracja | punkty 'REPO:STEP ...' | srednie | heldout 'MODEL ...' | stan"; exit 2
    ;;
esac
