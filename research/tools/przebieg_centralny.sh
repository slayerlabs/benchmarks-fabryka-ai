#!/usr/bin/env bash
# Central run: every model in MODELE x every task in common/zadania.py ZADANIA, full sets
# (common/ewaluuj.py --probka pelna), on a vast.ai instance. Code in $K (= research/).
# Long stages run in the background (nohup) and end with $WS/stan/<name>.ok or .blad;
# every timed step appends a JSON line to $WS/czasy.jsonl.
#   lista                  model list: label|repo|revision|loader|env (read by tests/test_przebieg_centralny.py)
#   plan "LABEL ..."       ewaluuj.py commands that `licz` would run, without running them ("# GPU N:" per queue)
#   przygotuj LIMIT_S      safety destroy after LIMIT_S, both venvs, HF download speed test
#   licz "LABEL ..."       in the background: per model download weights, every task, delete weights (a gated
#                          repo the HF token cannot read is skipped: log line POMINIETY, $ST/pominiety_<label>.txt);
#                          with N > 1 GPUs (nvidia-smi -L) models go round robin to N queues, one per GPU
#                          (CUDA_VISIBLE_DEVICES), queue log $WS/logi/<stage>_gpu<N>.log
# ENV_OVERRIDE=new WYNIKI=$WS/wyniki_nowe on licz: same models in the other venv, for the environment check.
#   ponow                  in the background: every (model, task) whose latest run failed
#   straznik               idle guard (also started by przygotuj): tools/straznik_bezczynnosci.py
#   proba_cpu ["LABEL ..."] load test on CPU: PROBA_N (2) questions, WikiText-2 1 document; every pair must finish
#   kontrola               sanity check of the full results (tools/kontrola_sensu.py); licz runs it at its end
#   pakuj                  wyniki.tgz to copy back
#   stan                   state files, last log lines, GPU
# Instance files map to the repo as: wyniki/<benchmark>/<label>/ -> results/central-run/<benchmark>/<label>/,
# czasy.jsonl -> results/central-run/times_<gpu>.jsonl. A run never writes under benchmarks/.
set -euo pipefail
K=${K:-/workspace/kod}
WS=${WS:-/workspace}
ST=$WS/stan
CZ=$WS/czasy.jsonl
# METODOLOGIA "Ustawienia przebiegu centralnego": batch size 1 for every task (padding in a batch shifts float32 logits and greedy generation)
BATCH=${BATCH:-1}
# WikiText-2 window for HF models: the config default (128k-262k tokens for Qwen3.5 and LFM) puts a whole
# document in one float32 forward and ends in CUDA OOM on 24 GB even at batch 1. EuroLLM's own is 4096.
OKNO_ROLLING=${OKNO_ROLLING:-4096}
# transformers 4.57.6 from the lock has no qwen3_5, and the LFM3 remote code imports
# use_kernel_func_from_hub_with_fallback (missing in 5.12.1). transformers 5 breaks lm_eval 0.4.9.1
# (AutoModelForVision2Seq) and peft 0.17.1 (HybridCache), so the "new" env moves those too.
# Levenshtein (PolQA/PoQuAD metric of the OpenPL fork, T30, T31) and langdetect (IFEval) come from the lock.
NEW_ENV_PINS=(transformers==5.22.1 lm_eval==0.4.13 peft==0.21.2)
# EuroLLM's tokenizer load needs protobuf, which the lock does not carry
LOCK_ENV_PINS=(protobuf==7.36.2 sentencepiece==0.2.2)
# IFEval (T36): lm-eval downloads NLTK punkt_tab on import when missing; przygotuj stages it once instead
NLTK_DANE=${NLTK_DANE:-$WS/nltk_data}
export NLTK_DATA=$NLTK_DANE

# One list for the run; tests/test_przebieg_centralny.py checks it against METODOLOGIA.md ("Pięć modeli
# odniesienia") and the Slayer revision named there.
# loader: slayer = common/slayer_lm.py, hf = HFLM, hf-trust = HFLM with trust_remote_code. env: lock | new.
# slayer-ckpt = common/slayer_lm.py on weights converted on the machine: the repo holds only native training
# checkpoints, licz_model downloads $SLAYER_CKPT from it and converts it with slayer-1b/wygaszanie/konwertuj.py
# against the $SLAYER_WZORZEC model (keys, shapes, config.json, tokenizer.json).
# Bielik is a gated repo (LlamaForCausalLM, tokenizer.json, so the lock env loads it): counted when the HF token has
# access, otherwise licz_model skips it with a message in the log and $ST/pominiety_<label>.txt (`dostep_hf`).
# Last row: the stage B control model (METODOLOGIA "Model kontrolny etapu B", item 1); f3f1b6d5 is branch step143000.
MODELE=(
  "slayer1b-1.07|SlayerLab/Slayer1B-1.07-checkpoints|89630be756618acbb47a78fa5cafd4e4aa6f1a63|slayer-ckpt|lock"
  "qwen3.5-0.8b-base|Qwen/Qwen3.5-0.8B-Base|dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68|hf|new"
  "lfm2.5-1.2b-base|LiquidAI/LFM2.5-1.2B-Base|7453bca97ca1e67754c4035a4b4c584e1c9dd725|hf|lock"
  "bielik-1.5b-v3|speakleash/Bielik-1.5B-v3|4b25049621bf3952a1fc9314c89773102eda0333|hf|lock"
  "lfm3-1.7b-base|LiquidAI/LFM3-1.7B-Base|545fc8f4c7b5fa9f405105274cd29c4f8f44b526|hf-trust|new"
  "eurollm-1.7b|utter-project/EuroLLM-1.7B|c730cd9b616799ace3c65e927d63191446f59374|hf|lock"
  "pythia-1b-v0|EleutherAI/pythia-1b-v0|f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0|hf|lock"
)
# slayer-ckpt: the 1.07 final step (model card: "training complete at step 22327") and the 1.06 model it continues
SLAYER_CKPT=ckpt_22327.pt
SLAYER_WZORZEC="SlayerLab/Slayer1B-1.06|ef81be58742544ad32e1afab38db011fec209609"

# Task id -> <benchmark> directory name under wyniki/ and results/central-run/; the test checks that ZADANIA_ID equals the keys of ZADANIA.
KATALOGI="T01:blimp T02:arc-challenge T03:wikitext-2 T04:multiblimp-pl T05:hellaswag T06:piqa T08:openbookqa
T09:sciq T10:boolq T11:copa T12:cb T13:wic T15:rte T16:anli-r3 T18:logiqa T19:mathqa T20:prost T21:sst2 T22:polemo2
T23:8tags T24:belebele-pl T25:dyk T26:ppc T27:psc T28:cbd T29:klej-ner T30:polqa T31:poquad T40:race T44:pubmedqa
T45:medmcqa T46:social-iqa T48:paws-en"
# (c): generation, groups with weights, corpus metrics, multi-context gold
KATALOGI+=" T07:winogrande T14:wsc273 T17:lambada T32:mmlu T33:gsm8k T34:math T35:truthfulqa T36:ifeval T38:squad2"
KATALOGI+=" T39:drop T41:coqa T42:nq-open T43:triviaqa T47:bbh T49:cola T50:record"
KATALOGI+=" T51:arc-easy T52:blimp-supplement T53:ewok"
# Tasks with their own code (`kod` in ZADANIA): `polecenie` runs this script with the ewaluuj.py flags instead
KOD="T53:benchmarks/ewok/ewok.py"
ZADANIA_ID=${ZADANIA_ID:-$(for p in $KATALOGI; do printf '%s ' "${p%%:*}"; done)}
katalog() { local p; for p in $KATALOGI; do [[ ${p%%:*} == "$1" ]] && echo "${p#*:}" && return 0; done; return 1; }
kod_zadania() { local p; for p in $KOD; do [[ ${p%%:*} == "$1" ]] && echo "${p#*:}" && return 0; done; return 0; }

# python, not `date +%N` / `du -b`: proba_cpu also runs on macOS (BSD date and du)
teraz() { python3 -c 'import time; print(time.time())'; }
bajty() { python3 -c 'import os, sys; print(sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(sys.argv[1]) for f in fs))' "$1"; }
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
    [[ $l == "$1" ]] && { ENV=${ENV_OVERRIDE:-$ENV}; return 0; }
  done
  echo "unknown model: $1" >&2
  return 1
}

polecenie() {  # polecenie LABEL TASK_ID -> ewaluuj.py command line (own-code task: its script, same flags)
  local L=$1 T=$2 kod
  model "$L"
  kod=$(kod_zadania "$T")
  if [[ -n $kod ]]; then
    echo "$WS/venv-$ENV/bin/python $K/$kod przebieg --repo $REPO --revision $REV --model_path $WS/modele/$L --zadania $T" \
      "--probka ${PROBKA:-pelna} --device ${DEVICE:-cuda} --batch $BATCH --eval_gpu $(gpu_nazwa) --etykieta $L" \
      "--wyjscie ${WYNIKI:-$WS/wyniki}/$(katalog "$T")/$L"
    return
  fi
  local args=(--model "$([[ $LOADER == slayer* ]] && echo slayer || echo hf)" --repo "$REPO" --revision "$REV"
              --model_path "$WS/modele/$L" --zadania "$T" --probka "$([[ $T == T03 && -n ${PROBKA_ROLLING:-} ]] && echo "$PROBKA_ROLLING" || echo "${PROBKA:-pelna}")" --device "${DEVICE:-cuda}" --batch "$BATCH"
              --eval_gpu "$(gpu_nazwa)" --etykieta "$L" --wyjscie "${WYNIKI:-$WS/wyniki}/$(katalog "$T")/$L")
  [[ $LOADER == hf-trust ]] && args+=(--trust_remote_code)
  [[ $T == T03 && $LOADER != slayer* ]] && args+=(--max_length "$OKNO_ROLLING")
  echo "$WS/venv-$ENV/bin/python $K/common/ewaluuj.py ${args[*]}"
}

gpu_nazwa() {  # NVIDIA name (of GPU $GPU_NR when set), otherwise "<cpu brand> <device>", e.g. Apple_M5_Pro_mps
    local n; n=$(nvidia-smi ${GPU_NR:+-i "$GPU_NR"} --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    [ -n "$n" ] || n="$(sysctl -n machdep.cpu.brand_string 2>/dev/null || uname -m) ${DEVICE:-cpu}"
    echo "$n" | tr ' ' '_'
}

dostep_hf() {  # dostep_hf: 0 = the HF token may read $REPO, 3 = gated repo without access (message on stdout);
  # any other error (network) is not a skip: the download below fails as it would without the check
  "$WS/venv-$ENV/bin/python" -c "import sys
from huggingface_hub import auth_check
from huggingface_hub.errors import GatedRepoError
try:
    auth_check(sys.argv[1])
except GatedRepoError as e:
    print(f'{type(e).__name__}: {str(e).splitlines()[0]}')
    sys.exit(3)" "$REPO"
}

pobierz_wagi() {  # pobierz_wagi LABEL (after `model`): $WS/modele/LABEL ready for ewaluuj.py --model_path
  local d=$WS/modele/$1 py="$WS/venv-$ENV/bin/python"
  if [[ $LOADER != slayer-ckpt ]]; then
    "$py" -c "from huggingface_hub import snapshot_download as s; s('$REPO', revision='$REV', local_dir='$d')"
    return
  fi
  # converted earlier on this machine (proba_cpu with ZOSTAW_WAGI=1, then licz): no second 9 GB download
  if [[ -s $d/model.safetensors ]] && grep -q "\"zrodlo_ckpt\": \".*/$SLAYER_CKPT\"" "$d/config.json" 2> /dev/null; then
    echo "wagi $1: juz skonwertowane z $SLAYER_CKPT"; return
  fi
  local wzor_repo=${SLAYER_WZORZEC%%|*} wzor_rev=${SLAYER_WZORZEC#*|}
  "$py" -c "from huggingface_hub import hf_hub_download as h; h('$REPO', '$SLAYER_CKPT', revision='$REV', local_dir='$d.ckpt')"
  "$py" -c "from huggingface_hub import snapshot_download as s; s('$wzor_repo', revision='$wzor_rev', local_dir='$d.wzorzec', allow_patterns=['model.safetensors', 'config.json', 'tokenizer.json'])"
  "$py" "$K/slayer-1b/wygaszanie/konwertuj.py" "$d.ckpt/$SLAYER_CKPT" "$d.wzorzec" "$d"
  rm -rf "$d.ckpt" "$d.wzorzec"
}

licz_model() {  # licz_model LABEL: download, every task, delete weights; a failed task does not stop the rest
  local L=$1 t T kod powod
  model "$L"
  t=$(teraz)
  mkdir -p "$ST"
  kod=0; powod=$(dostep_hf) || kod=$?
  if (( kod == 3 )); then  # gated repo, no access: the model is left out, the run goes on with the next one
    echo "POMINIETY $L ($REPO @ $REV): token HF bez dostepu do repo z bramka zgody; $powod" > "$ST/pominiety_$L.txt"
    cat "$ST/pominiety_$L.txt"
    zapisz_czas pominiety "$t" "{\"model\": \"$L\", \"repo\": \"$REPO\", \"powod\": \"brak dostepu do repo z bramka\"}"
    return 0
  fi
  rm -f "$ST/pominiety_$L.txt"
  pobierz_wagi "$L"
  zapisz_czas pobranie "$t" "{\"model\": \"$L\", \"bajty\": $(bajty "$WS/modele/$L")}"
  for T in $ZADANIA_ID; do
    t=$(teraz)
    kod=0
    echo "gpu ${GPU_NR:--} $(gpu_nazwa)" > "$WS/logi/${L}_${T}_$ENV.log"
    $(polecenie "$L" "$T") >> "$WS/logi/${L}_${T}_$ENV.log" 2>&1 || kod=$?
    zapisz_czas ewaluacja "$t" "{\"model\": \"$L\", \"zadanie\": \"$T\", \"kod\": $kod, \"gpu\": \"$(gpu_nazwa)\", \"gpu_nr\": \"${GPU_NR:-}\", \"batch\": \"$BATCH\", \"env\": \"$ENV\", \"wyniki\": \"${WYNIKI:-$WS/wyniki}\"}"
  done
  # ZOSTAW_WAGI=1: proba_cpu followed by licz on the same instance downloads each model once
  [[ ${ZOSTAW_WAGI:-0} == 1 ]] || rm -rf "$WS/modele/$L"
}

liczba_gpu() { nvidia-smi -L 2>/dev/null | grep -c '^GPU ' || true; }

kolejki() {  # kolejki ITEM...: "<gpu> ITEM ..." per queue, items round robin; one line "- ITEM ..." with 0 or 1 GPU
  local n i=0 x; n=$(liczba_gpu)
  if (( n <= 1 )); then echo "- $*"; return; fi
  local -a q=()
  for x in "$@"; do q[i % n]+=" $x"; i=$((i + 1)); done
  for i in "${!q[@]}"; do echo "$i${q[i]}"; done
}

licz_kolejke() {  # licz_kolejke GPU ITEM...: ITEM = LABEL (whole model, logs the model stage) or LABEL:T01,T02
  local nr=$1 p t z; shift
  [[ $nr == - ]] || export CUDA_VISIBLE_DEVICES=$nr GPU_NR=$nr
  for p in "$@"; do
    t=$(teraz)
    if [[ $p == *:* ]]; then z=${p#*:}; ZADANIA_ID=${z//,/ } licz_model "${p%%:*}"
    else licz_model "$p"; zapisz_czas model "$t" "{\"model\": \"$p\", \"gpu_nr\": \"${GPU_NR:-}\"}"; fi
  done
}

licz_rownolegle() {  # licz_rownolegle NAME ITEM...: the `kolejki` queues side by side; fails when any queue fails
  local nazwa=$1 nr reszta p kod=0; shift
  local -a pidy=()
  while read -r nr reszta; do
    if [[ $nr == - ]]; then licz_kolejke - $reszta; return; fi
    licz_kolejke "$nr" $reszta < /dev/null > "$WS/logi/${nazwa}_gpu$nr.log" 2>&1 &
    pidy+=($!)
  done < <(kolejki "$@")
  for p in "${pidy[@]}"; do wait "$p" || kod=1; done
  return $kod
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
    while read -r nr reszta; do
      [[ $nr == - ]] || echo "# GPU $nr: $reszta"
      for L in $reszta; do for T in $ZADANIA_ID; do
        if [[ $nr == - ]]; then polecenie "$L" "$T"
        else echo "CUDA_VISIBLE_DEVICES=$nr $(GPU_NR=$nr polecenie "$L" "$T")"; fi
      done; done
    done < <(kolejki ${2:-$(printf '%s\n' "${MODELE[@]}" | cut -d'|' -f1)})
    ;;
  przygotuj)
    LIMIT=${2:?safety limit in seconds}
    mkdir -p "$ST" "$WS/wyniki" "$WS/logi" "$WS/modele"
    nohup python3 $K/slayer-1b/wygaszanie/bezpiecznik.py po "$LIMIT" > $WS/logi/bezpiecznik.log 2>&1 &
    bash "$0" straznik
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
    "$WS/venv-lock/bin/python" -c "import nltk, sys; sys.exit(0 if nltk.download('punkt_tab', download_dir='$NLTK_DANE', quiet=True) else 1)"
    "$WS/venv-lock/bin/python" -c "import torch, json; print(json.dumps({'torch': torch.__version__, 'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(0)}))" | tee $WS/srodowisko.json
    nproc; free -g; df -h $WS; nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
    ;;
  licz)
    LISTA=${2:?model labels}
    export PYTHONUNBUFFERED=1 NVIDIA_TF32_OVERRIDE=0 HF_HUB_DISABLE_PROGRESS_BARS=1
    w_tle "licz_${LISTA// /_}" "set -e; source $K/tools/przebieg_centralny.sh _funkcje; kod=0; \
      licz_rownolegle licz_${LISTA// /_} $LISTA || kod=1; \
      bash $K/tools/przebieg_centralny.sh kontrola || true; exit \$kod"
    ;;
  ponow)  # in the background: (model, task) pairs whose latest czasy.jsonl entry has kod != 0, again
    export PYTHONUNBUFFERED=1 NVIDIA_TF32_OVERRIDE=0 HF_HUB_DISABLE_PROGRESS_BARS=1
    PARY=$(python3 -c "import json,sys; d={}
for l in open(sys.argv[1]):
    r=json.loads(l)
    if r['etap']=='ewaluacja' and r.get('wyniki', sys.argv[2])==sys.argv[2]: d[(r['model'],r['zadanie'])]=r['kod']
m={}
for (l,t),k in d.items():
    if k: m.setdefault(l,[]).append(t)
print(' '.join(l+':'+','.join(t) for l,t in m.items()))" "$CZ" "${WYNIKI:-$WS/wyniki}")
    echo "again: ${PARY:-nothing} (batch $BATCH)"
    [[ -n $PARY ]] && w_tle ponow "set -e; source $K/tools/przebieg_centralny.sh _funkcje; \
      licz_rownolegle ponow $PARY"
    ;;
  straznik)  # idle guard: GPU < 5% with no evaluation for STRAZNIK_OKNO s -> pack, copy to $WS/wyjscie, destroy
    mkdir -p "$WS/logi"
    nohup python3 $K/tools/straznik_bezczynnosci.py --wyjscie "$WS/wyjscie" --okno "${STRAZNIK_OKNO:-600}" \
      --archiwum "$WS/wyniki.tgz" > $WS/logi/straznik.log 2>&1 &
    echo "idle guard pid $!"
    ;;
  proba_cpu)  # load test: PROBA_N questions (WikiText-2: 1 document) per model x task on CPU, every pair must finish
    export DEVICE=cpu PROBKA=${PROBA_N:-2} PROBKA_ROLLING=1 BATCH=1 WYNIKI=$WS/proba_cpu
    LISTA=${2:-$(printf '%s\n' "${MODELE[@]}" | cut -d'|' -f1)}
    if [[ ${SUCHO:-0} == 1 ]]; then
      for L in $LISTA; do for T in $ZADANIA_ID; do polecenie "$L" "$T"; done; done
      exit 0
    fi
    mkdir -p "$ST" "$WS/logi" "$WS/modele"
    for L in $LISTA; do licz_model "$L"; done
    # a gated model skipped by licz_model has no outputs; its skip stays in $ST/pominiety_<label>.txt
    python3 $K/tools/kontrola_sensu.py --tylko-stan $(for L in $LISTA; do [[ -e $ST/pominiety_$L.txt ]] && continue
      for T in $ZADANIA_ID; do echo "$WYNIKI/$(katalog "$T")/$L"; done; done)
    ;;
  kontrola)  # sanity of full results (score 1.000, below random - 5 points, ...): $WS/logi/kontrola_sensu.txt
    mkdir -p "$WS/logi"
    python3 $K/tools/kontrola_sensu.py "${WYNIKI:-$WS/wyniki}"/*/*/ > $WS/logi/kontrola_sensu.txt && kod=0 || kod=$?
    cat $WS/logi/kontrola_sensu.txt; exit $kod
    ;;
  pakuj)  # wyniki.tgz for the repo: per-question files gzipped, podsumowanie.md left out (number gate reads *.md)
    find $WS/wyniki* -name '*.jsonl' -exec gzip -f {} +
    tar czf $WS/wyniki.tgz -C $WS --exclude podsumowanie.md $(cd $WS && ls -d wyniki*/) czasy.jsonl srodowisko.json logi/freeze_lock.txt logi/freeze_new.txt
    ls -la $WS/wyniki.tgz
    ;;
  stan)
    ls -la $ST; cat $ST/pominiety_*.txt 2>/dev/null || true; for f in $WS/logi/*.log; do echo "== $f"; tail -n 2 "$f"; done; tail -n 5 $CZ 2>/dev/null
    nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv; df -h $WS | tail -1
    ;;
  _funkcje) ;;  # sourced: functions only
  *)
    echo "stages: lista | katalogi | plan 'LABEL ...' | przygotuj LIMIT_S | licz 'LABEL ...' | ponow | straznik | proba_cpu ['LABEL ...'] | kontrola | pakuj | stan"; exit 2
    ;;
esac
