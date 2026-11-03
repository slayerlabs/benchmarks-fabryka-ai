#!/usr/bin/env bash
# Central run: every model in MODELE x every task in common/zadania.py ZADANIA, full sets
# (common/ewaluuj.py --probka pelna), on one vast.ai GPU. Code in $K (= research/).
# Long stages run in the background (nohup) and end with $WS/stan/<name>.ok or .blad;
# every timed step appends a JSON line to $WS/czasy.jsonl.
#   lista                  model list: label|repo|revision|loader|env (read by tests/test_przebieg_centralny.py)
#   plan "LABEL ..."       ewaluuj.py commands that `licz` would run, without running them
#   przygotuj LIMIT_S      safety destroy after LIMIT_S, both venvs, HF download speed test
#   licz "LABEL ..."       in the background: per model download weights, every task, delete weights
#   ponow                  in the background: every (model, task) whose latest run failed, e.g. with BATCH=1 after an OOM
#   pakuj                  wyniki.tgz to copy back
#   stan                   state files, last log lines, GPU
# Instance files map to the repo as: wyniki/<benchmark>/<label>/ -> benchmarks/<benchmark>/results/<label>/,
# czasy.jsonl -> results/central-run/times_<gpu>.jsonl.
set -euo pipefail
K=${K:-/workspace/kod}
WS=${WS:-/workspace}
ST=$WS/stan
CZ=$WS/czasy.jsonl
BATCH=${BATCH:-auto}
# transformers 4.57.6 from the lock has no qwen3_5, and the LFM3 remote code imports
# use_kernel_func_from_hub_with_fallback (missing in 5.12.1). transformers 5 breaks lm_eval 0.4.9.1
# (AutoModelForVision2Seq) and peft 0.17.1 (HybridCache), so the "new" env moves those too.
NEW_ENV_PINS=(transformers==5.22.1 lm_eval==0.4.13 peft==0.21.2)
# EuroLLM's tokenizer load needs protobuf, which the lock does not carry
LOCK_ENV_PINS=(protobuf==7.36.2 sentencepiece==0.2.2)

# One list for the run; tests/test_przebieg_centralny.py checks it against METODOLOGIA.md ("Pięć modeli
# odniesienia" without Bielik, gated repo) and the Slayer revision named there.
# loader: slayer = common/slayer_lm.py, hf = HFLM, hf-trust = HFLM with trust_remote_code. env: lock | new.
MODELE=(
  "slayer1b-1.06|SlayerLab/Slayer1B-1.06|ef81be58742544ad32e1afab38db011fec209609|slayer|lock"
  "qwen3.5-0.8b-base|Qwen/Qwen3.5-0.8B-Base|dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68|hf|new"
  "lfm2.5-1.2b-base|LiquidAI/LFM2.5-1.2B-Base|7453bca97ca1e67754c4035a4b4c584e1c9dd725|hf|lock"
  "lfm3-1.7b-base|LiquidAI/LFM3-1.7B-Base|545fc8f4c7b5fa9f405105274cd29c4f8f44b526|hf-trust|new"
  "eurollm-1.7b|utter-project/EuroLLM-1.7B|c730cd9b616799ace3c65e927d63191446f59374|hf|lock"
)

# Task id -> benchmarks/<dir>; the test checks that ZADANIA_ID equals the keys of ZADANIA.
KATALOGI="T01:blimp T02:arc-challenge T03:wikitext-2 T04:multiblimp-pl T44:pubmedqa T45:medmcqa T46:social-iqa"
ZADANIA_ID=${ZADANIA_ID:-$(for p in $KATALOGI; do printf '%s ' "${p%%:*}"; done)}
katalog() { local p; for p in $KATALOGI; do [[ ${p%%:*} == "$1" ]] && echo "${p#*:}" && return 0; done; return 1; }

teraz() { date +%s.%N; }
zapisz_czas() {  # zapisz_czas STAGE START [JSON-fields]
  python3 -c "import json,sys,time; d={'etap':sys.argv[1],'s':round(time.time()-float(sys.argv[2]),1)}; d.update(json.loads(sys.argv[3] if len(sys.argv)>3 else '{}')); print(json.dumps(d))" "$@" >> "$CZ"
}

w_tle() {  # w_tle NAME COMMAND...
  local n=$1; shift
  rm -f "$ST/$n.ok" "$ST/$n.blad"
  nohup bash -c "( $* ) && touch $ST/$n.ok || touch $ST/$n.blad" > "$WS/logi/$n.log" 2>&1 &
  echo "start $n (pid $!), log $WS/logi/$n.log"
}

model() {  # model LABEL -> sets REPO REV LOADER ENV
  local m
  for m in "${MODELE[@]}"; do
    IFS='|' read -r l REPO REV LOADER ENV <<< "$m"
    [[ $l == "$1" ]] && return 0
  done
  echo "unknown model: $1" >&2
  return 1
}

polecenie() {  # polecenie LABEL TASK_ID -> ewaluuj.py command line
  local L=$1 T=$2
  model "$L"
  local args=(--model "$([[ $LOADER == slayer ]] && echo slayer || echo hf)" --repo "$REPO" --revision "$REV"
              --model_path "$WS/modele/$L" --zadania "$T" --probka pelna --device cuda --batch "$BATCH"
              --eval_gpu "$(gpu_nazwa)" --etykieta "$L" --wyjscie "$WS/wyniki/$(katalog "$T")/$L")
  [[ $LOADER == hf-trust ]] && args+=(--trust_remote_code)
  echo "$WS/venv-$ENV/bin/python $K/common/ewaluuj.py ${args[*]}"
}

gpu_nazwa() { nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 | tr ' ' '_' || echo cpu; }

licz_model() {  # licz_model LABEL: download, every task, delete weights; a failed task does not stop the rest
  local L=$1 t T kod
  model "$L"
  t=$(teraz)
  "$WS/venv-$ENV/bin/python" -c "from huggingface_hub import snapshot_download as s; s('$REPO', revision='$REV', local_dir='$WS/modele/$L')"
  zapisz_czas pobranie "$t" "{\"model\": \"$L\", \"bajty\": $(du -sb "$WS/modele/$L" | cut -f1)}"
  for T in $ZADANIA_ID; do
    t=$(teraz)
    kod=0
    $(polecenie "$L" "$T") > "$WS/logi/${L}_$T.log" 2>&1 || kod=$?
    zapisz_czas ewaluacja "$t" "{\"model\": \"$L\", \"zadanie\": \"$T\", \"kod\": $kod, \"gpu\": \"$(gpu_nazwa)\", \"batch\": \"$BATCH\"}"
  done
  rm -rf "$WS/modele/$L"
}

etap=${1:-}
case "$etap" in
  lista)
    printf '%s\n' "${MODELE[@]}"
    ;;
  katalogi)
    for T in $ZADANIA_ID; do echo "$T $(katalog "$T")"; done
    ;;
  plan)
    for L in ${2:-$(printf '%s\n' "${MODELE[@]}" | cut -d'|' -f1)}; do
      for T in $ZADANIA_ID; do polecenie "$L" "$T"; done
    done
    ;;
  przygotuj)
    LIMIT=${2:?safety limit in seconds}
    mkdir -p "$ST" "$WS/wyniki" "$WS/logi" "$WS/modele"
    nohup python3 $K/slayer-1b/wygaszanie/bezpiecznik.py po "$LIMIT" > $WS/logi/bezpiecznik.log 2>&1 &
    python3 $K/slayer-1b/wygaszanie/bezpiecznik.py sprawdz
    t=$(teraz)
    curl -sL -r 0-1073741823 -o /dev/null -w '%{speed_download}\n' \
      "https://huggingface.co/SlayerLab/Slayer1B-1.06/resolve/ef81be58742544ad32e1afab38db011fec209609/model.safetensors" \
      > $WS/logi/siec.txt
    zapisz_czas siec_1GB "$t" "{\"bajty_na_s\": $(cat $WS/logi/siec.txt)}"
    # the LFM3 remote code compiles a Triton conv kernel on CUDA; pytorch runtime images ship no C compiler
    command -v cc > /dev/null || { apt-get update -qq && apt-get install -y -qq gcc > /dev/null; }
    for E in lock new; do
      t=$(teraz)
      # --system-site-packages: torch 2.8.0 of the image is the locked one
      python3 -m venv --system-site-packages "$WS/venv-$E"
      "$WS/venv-$E/bin/pip" install -q -r $K/common/requirements.lock.txt
      if [[ $E == new ]]; then "$WS/venv-$E/bin/pip" install -q "${NEW_ENV_PINS[@]}"
      else "$WS/venv-$E/bin/pip" install -q "${LOCK_ENV_PINS[@]}"; fi
      "$WS/venv-$E/bin/pip" freeze > "$WS/logi/freeze_$E.txt"
      zapisz_czas "pip_$E" "$t"
    done
    "$WS/venv-lock/bin/python" -c "import torch, json; print(json.dumps({'torch': torch.__version__, 'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(0)}))" | tee $WS/srodowisko.json
    nproc; free -g; df -h $WS; nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
    ;;
  licz)
    LISTA=${2:?model labels}
    export PYTHONUNBUFFERED=1 NVIDIA_TF32_OVERRIDE=0 HF_HUB_DISABLE_PROGRESS_BARS=1
    w_tle "licz_${LISTA// /_}" "set -e; source $K/tools/przebieg_centralny.sh _funkcje; \
      for L in $LISTA; do t=\$(teraz); licz_model \$L; zapisz_czas model \$t \"{\\\"model\\\": \\\"\$L\\\"}\"; done"
    ;;
  ponow)  # in the background: (model, task) pairs whose latest czasy.jsonl entry has kod != 0, again
    export PYTHONUNBUFFERED=1 NVIDIA_TF32_OVERRIDE=0 HF_HUB_DISABLE_PROGRESS_BARS=1
    PARY=$(python3 -c "import json,sys; d={}
for l in open(sys.argv[1]):
    r=json.loads(l)
    if r['etap']=='ewaluacja': d[(r['model'],r['zadanie'])]=r['kod']
m={}
for (l,t),k in d.items():
    if k: m.setdefault(l,[]).append(t)
print(' '.join(l+':'+','.join(t) for l,t in m.items()))" "$CZ")
    echo "again: ${PARY:-nothing} (batch $BATCH)"
    [[ -n $PARY ]] && w_tle ponow "set -e; source $K/tools/przebieg_centralny.sh _funkcje; \
      for p in $PARY; do L=\${p%%:*}; ZADANIA_ID=\"\${p#*:}\"; ZADANIA_ID=\${ZADANIA_ID//,/ }; licz_model \$L; done"
    ;;
  pakuj)  # wyniki.tgz for the repo: per-question files gzipped, podsumowanie.md left out (number gate reads *.md)
    find $WS/wyniki -name '*.jsonl' -exec gzip -f {} +
    tar czf $WS/wyniki.tgz -C $WS --exclude podsumowanie.md wyniki czasy.jsonl srodowisko.json logi/freeze_lock.txt logi/freeze_new.txt
    ls -la $WS/wyniki.tgz
    ;;
  stan)
    ls -la $ST; for f in $WS/logi/*.log; do echo "== $f"; tail -n 2 "$f"; done; tail -n 5 $CZ 2>/dev/null
    nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv; df -h $WS | tail -1
    ;;
  _funkcje) ;;  # sourced: functions only
  *)
    echo "stages: lista | katalogi | plan 'LABEL ...' | przygotuj LIMIT_S | licz 'LABEL ...' | ponow | pakuj | stan"; exit 2
    ;;
esac
