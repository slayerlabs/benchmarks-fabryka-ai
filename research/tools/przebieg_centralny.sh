#!/usr/bin/env bash
# Central run: every model in MODELE x every task in common/zadania.py ZADANIA, full sets
# (common/ewaluuj.py --probka pelna), on a vast.ai instance. Code in $K (= research/; by default the directory
# above this script, also when sourced). One-command start: tools/start.sh.
# Long stages run in the background (nohup) and end with $WS/stan/<name>.ok or .blad;
# every timed step appends a JSON line to $WS/czasy.jsonl.
#   gotowe                 task ids of the "✅ Gotowe" section of STATUS.md (GOTOWE), the default of tools/start.sh
#   lista                 model list, the MODELE rows (read by tests/test_przebieg_centralny.py)
#   plan "LABEL ..."       ewaluuj.py commands that `licz` would run, without running them ("# GPU N:" per queue)
#   przygotuj LIMIT_S      safety destroy after LIMIT_S, both venvs, HF download speed test
#   licz ["LABEL ..."]     no list: every MODELE row; a list must name what it leaves out in POMIN ("LABEL ...")
#                          or POMIN=reszta (lista_licz). In the background: per model download weights, every task (a stage B control model:
#                          only its TESTY_MODELU tests), delete weights (a gated
#                          repo the HF token cannot read is skipped: log line POMINIETY, $ST/pominiety_<label>.txt);
#                          with N > 1 GPUs (nvidia-smi -L) tools/queue_plan.py splits the (model, task) pairs into N
#                          queues by estimated time, one per GPU (CUDA_VISIBLE_DEVICES), a long model in parts on
#                          several GPUs, each with its own weights copy; queue log $WS/logi/<stage>_gpu<N>.log
# ENV_OVERRIDE=new WYNIKI=$WS/wyniki_nowe on licz: same models in the other venv, for the environment check.
#   ponow                  in the background: every (model, task) whose latest run failed
#   straznik               idle guard (also started by przygotuj): tools/straznik_bezczynnosci.py
#   proba_cpu ["LABEL ..."] load test on CPU: PROBA_N (2) questions, WikiText-2 1 document; every pair must finish
#   kontrola               sanity check of the full results (tools/kontrola_sensu.py) and, after licz, every pair
#                          of its plan has a result (kompletnosc); licz runs it at its end
#   pakuj                  wyniki.tgz to copy back
#   stan                   state files, last log lines, GPU
# Instance files map to the repo as: wyniki/<benchmark>/<label>/ -> results/central-run/<benchmark>/<label>/,
# czasy.jsonl -> results/central-run/times_<gpu>.jsonl. A run never writes under benchmarks/.
set -euo pipefail
K=${K:-$(CDPATH= cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}  # CDPATH: cd would also print the path into K
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
# odniesienia", "Modele porównawcze z #190") and the Slayer revision named there.
# Row: label|repo|revision|loader|env[|dtype[|ckpt_file|ckpt_sha256|template_repo@template_revision]]
# loader: slayer = common/slayer_lm.py, hf = HFLM, hf-trust = HFLM with trust_remote_code. env: lock | new.
# dtype: float32 (default, METODOLOGIA) | bfloat16 only for a model whose float32 weights do not fit the card;
# polecenie passes --dtype to ewaluuj.py and ewok.py, both write it into the results.
# slayer-ckpt = common/slayer_lm.py on weights converted on the machine: the repo holds only native training
# checkpoints, licz_model downloads the row's ckpt_file from it and converts it with tools/konwertuj.py
# against the row's template model (keys, shapes, config.json, tokenizer.json); a sha256 mismatch stops it.
# Bielik is a gated repo (LlamaForCausalLM, tokenizer.json, so the lock env loads it): counted when the HF token has
# access, otherwise licz_model skips it with a message in the log and $ST/pominiety_<label>.txt (`dostep_hf`).
# Last row: the stage B control model (METODOLOGIA "Model kontrolny etapu B", item 1); f3f1b6d5 is branch step143000.
# The 1.07 checkpoint is the final step (model card: "training complete at step 22327"), its sha256 from the
# SlayerLab/Slayer1B-1.07-checkpoints card, template the 1.06 model it continues.
MODELE=(
  "slayer1b-1.07|SlayerLab/Slayer1B-1.07-checkpoints|89630be756618acbb47a78fa5cafd4e4aa6f1a63|slayer-ckpt|lock|float32|ckpt_22327.pt|48cdb5eb16b69e0ee9a7a2ed72895ff47c0ba57aca0f4516b1f7e9cba286685c|SlayerLab/Slayer1B-1.06@ef81be58742544ad32e1afab38db011fec209609"
  "qwen3.5-0.8b-base|Qwen/Qwen3.5-0.8B-Base|dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68|hf|new"
  "lfm2.5-1.2b-base|LiquidAI/LFM2.5-1.2B-Base|7453bca97ca1e67754c4035a4b4c584e1c9dd725|hf|lock"
  "bielik-1.5b-v3|speakleash/Bielik-1.5B-v3|4b25049621bf3952a1fc9314c89773102eda0333|hf|lock"
  "lfm3-1.7b-base|LiquidAI/LFM3-1.7B-Base|545fc8f4c7b5fa9f405105274cd29c4f8f44b526|hf-trust|new"
  "eurollm-1.7b|utter-project/EuroLLM-1.7B|c730cd9b616799ace3c65e927d63191446f59374|hf|lock"
  "pythia-1b-v0|EleutherAI/pythia-1b-v0|f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0|hf|lock"
)
# Comparison models (METODOLOGIA "Modele porównawcze z #190"): same run, outside the five-reference comparison.
# A separate block, so tools/wykres_przebiegu.py and tools/ewaluacja read only the measured Slayer above.
# Bielik 11B: float32 weights ~45 GB do not fit a 32 GB card, so bfloat16 (as Bielik-11B-v3.0 in full-run-2026-11).
# Slayer 1.09: wagi_<step>.pt and its sha256 from SHA256SUMS of the -checkpoints revision; 1.09 starts from 1.08.
MODELE+=(
  "bielik-11b-v3.1-instruct|speakleash/Bielik-11B-v3.1-Instruct|d6e755d356ad418d0f0e30b8c428db267415ddb9|hf|lock|bfloat16"
  "lfm3-1.7b|LiquidAI/LFM3-1.7B|1da06bec6a819da10b54c67e5c90972b46d81871|hf-trust|new"
  "slayer1b-1.09-k40000|SlayerLab/Slayer1B-1.09-checkpoints|cff81fdcc05f0d91e9ba45b09fe78f769d7e0903|slayer-ckpt|lock|float32|wagi_40000.pt|f83f7017872f7121f002bc77499c625304bd28e2c87fb4afaa0e3d445bd31881|SlayerLab/Slayer1B-1.08@5f854a0cc7160594d54d1788d37a44e8ebabe16c"
  # TODO k50000: revision of SlayerLab/Slayer1B-1.09-checkpoints that has wagi_50000.pt, and that file's line in SHA256SUMS
  # "slayer1b-1.09-k50000|SlayerLab/Slayer1B-1.09-checkpoints|<REWIZJA>|slayer-ckpt|lock|float32|wagi_50000.pt|<SHA256>|SlayerLab/Slayer1B-1.08@5f854a0cc7160594d54d1788d37a44e8ebabe16c"
)
# Stage B control models (METODOLOGIA "Modele kontrolne etapu B w przebiegu"): the candidate of a card, item 3 of
# "Model kontrolny etapu B", that the central run reproduces. Each runs only its own tests (TESTY_MODELU), and stays
# outside the reference comparison, the SNR panel (tools/snr_panelu.py reads the first block) and the report
# (tools/ewaluacja/raport.py drops them). float32 unless the source counted a model of >= 6 B params in bfloat16.
# bloom-560m: a later revision than the WSC273 control (tools/ewaluacja/ewaluacja.py), hence the revision in the label.
MODELE+=(
  "bloom-560m-e985a63|bigscience/bloom-560m|e985a63cdc139290c5f700ff1929f0b5942cced2|hf|lock"
  "bloom-1b7|bigscience/bloom-1b7|258ce6c9fe66893de0218d9e6a322947987c8349|hf|lock"
  "pythia-1b|EleutherAI/pythia-1b|f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2|hf|lock"
  "qwen1.5-7b|Qwen/Qwen1.5-7B|e52fa2ef47411cc8bc9f752d1d8d9072b37742e7|hf|lock|bfloat16"
  "babyllama-10m-2024|babylm/babyllama-10m-2024|073b4258651a7a6268fc48e708cdbad6a20bddab|hf|lock"
)
# label:tests of a model that runs only those (comma-separated); every other model runs all of ZADANIA_ID
TESTY_MODELU="bloom-560m-e985a63:T20 bloom-1b7:T38,T40,T41 pythia-1b:T36 qwen1.5-7b:T35 babyllama-10m-2024:T52"

# Task id -> <benchmark> directory name under wyniki/ and results/central-run/; the test checks that ZADANIA_ID equals the keys of ZADANIA.
KATALOGI="T01:blimp T02:arc-challenge T03:wikitext-2 T04:multiblimp-pl T05:hellaswag T06:piqa T08:openbookqa
T09:sciq T10:boolq T11:copa T12:cb T13:wic T15:rte T16:anli-r3 T18:logiqa T19:mathqa T20:prost T21:sst2 T22:polemo2
T23:8tags T24:belebele-pl T25:dyk T26:ppc T27:psc T28:cbd T29:klej-ner T30:polqa T31:poquad T37:llmzszl T40:race T44:pubmedqa
T45:medmcqa T46:social-iqa T48:paws-en"
# (c): generation, groups with weights, corpus metrics, multi-context gold
KATALOGI+=" T07:winogrande T14:wsc273 T17:lambada T32:mmlu T33:gsm8k T34:math T35:truthfulqa T36:ifeval T38:squad2"
KATALOGI+=" T39:drop T41:coqa T42:nq-open T43:triviaqa T47:bbh T49:cola T50:record"
KATALOGI+=" T51:arc-easy T52:blimp-supplement T53:ewok"
# Tasks of the "✅ Gotowe" section of STATUS.md, counted by default by tools/start.sh. tests/test_start.py checks
# this line against STATUS.md: a row moved there without changing GOTOWE (or the reverse) fails the test.
GOTOWE="T01 T02 T03 T04 T05 T06 T07 T14 T17 T19 T22 T26 T44 T45 T46 T51 T53"
# Tasks with their own code (`kod` in ZADANIA): `polecenie` runs this script with the ewaluuj.py flags instead
KOD="T53:benchmarks/ewok/ewok.py"
ZADANIA_ID=${ZADANIA_ID:-$(for p in $KATALOGI; do printf '%s ' "${p%%:*}"; done)}
zadania_modelu() {  # zadania_modelu LABEL: $ZADANIA_ID, for a TESTY_MODELU label only its own tests among them
  local p t z wynik=""
  for p in $TESTY_MODELU; do
    [[ ${p%%:*} == "$1" ]] || continue
    z=" ${p#*:} "; z=${z//,/ }
    for t in $ZADANIA_ID; do [[ $z == *" $t "* ]] && wynik+="$t "; done
    echo "${wynik% }"; return 0
  done
  echo "$ZADANIA_ID"
}
katalog() { local p; for p in $KATALOGI; do [[ ${p%%:*} == "$1" ]] && echo "${p#*:}" && return 0; done; return 1; }
kod_zadania() { local p; for p in $KOD; do [[ ${p%%:*} == "$1" ]] && echo "${p#*:}" && return 0; done; return 0; }
etykiety() { local m; for m in "${MODELE[@]}"; do printf '%s ' "${m%%|*}"; done; }

lista_licz() {  # lista_licz ["ITEM ..."]: the items `licz` runs, ITEM = LABEL or LABEL:T01,T02; none = every MODELE row.
  # The model list lives only in MODELE: a list typed by hand must name every MODELE label it leaves out in POMIN
  # ("label ..."), or POMIN=reszta (one model per instance, tools/start.sh). An unknown label stops as well.
  local wszystkie lista x brak=()
  wszystkie=" $(etykiety)"
  lista=${1:-$wszystkie}
  for x in $lista; do
    [[ $wszystkie == *" ${x%%:*} "* ]] && continue
    echo "unknown label ${x%%:*}; labels: bash tools/przebieg_centralny.sh lista" >&2; return 2
  done
  for x in $wszystkie; do [[ " $lista " =~ [[:space:]]$x(:|[[:space:]]) ]] || brak+=("$x"); done
  if [[ ${POMIN:-} != reszta ]]; then
    for x in ${brak[@]+"${brak[@]}"}; do
      [[ " ${POMIN:-} " == *" $x "* ]] && continue
      echo "the list leaves out $x without saying so: add it, or POMIN=\"${brak[*]-}\" to leave out on purpose" >&2
      return 2
    done
  fi
  (( ${#brak[@]} == 0 )) || echo "left out of this run (POMIN=${POMIN:-}): ${brak[*]-}" >&2
  echo $lista
}

kompletnosc() {  # kompletnosc ITEM...: every (model, task) pair of the items has results_rozszerzone.json, unless
  # the model was skipped for a gated repo ($ST/pominiety_<label>.txt); prints the missing pairs, 1 when any
  local x L T zad brak=0
  for x in "$@"; do
    L=${x%%:*}
    [[ -e $ST/pominiety_$L.txt ]] && continue
    if [[ $x == *:* ]]; then zad=${x#*:}; zad=${zad//,/ }; else zad=$(zadania_modelu "$L"); fi
    for T in $zad; do
      [[ -s ${WYNIKI:-$WS/wyniki}/$(katalog "$T")/$L/results_rozszerzone.json ]] && continue
      echo "MISSING $L $T"; brak=1
    done
  done
  return $brak
}

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

model() {  # model LABEL -> sets REPO REV LOADER ENV DTYPE CKPT CKPT_SHA256 WZORZEC (template repo@revision)
  local m
  for m in "${MODELE[@]}"; do
    IFS='|' read -r l REPO REV LOADER ENV DTYPE CKPT CKPT_SHA256 WZORZEC <<< "$m"
    [[ $l == "$1" ]] || continue
    ENV=${ENV_OVERRIDE:-$ENV} DTYPE=${DTYPE:-float32}
    [[ $DTYPE == float32 || $DTYPE == bfloat16 ]] || { echo "model $1: dtype $DTYPE (float32 | bfloat16)" >&2; return 1; }
    if [[ $LOADER == slayer-ckpt && ( -z $CKPT || -z $CKPT_SHA256 || $WZORZEC != *@* ) ]]; then
      echo "model $1: slayer-ckpt needs ckpt_file|ckpt_sha256|template_repo@revision in its MODELE row" >&2; return 1
    fi
    return 0
  done
  echo "unknown model: $1" >&2
  return 1
}

polecenie() {  # polecenie LABEL TASK_ID -> ewaluuj.py command line (own-code task: its script, same flags)
  local L=$1 T=$2 kod dt=""
  model "$L"
  [[ $DTYPE == float32 ]] || dt=" --dtype $DTYPE"  # float32 rows keep the command of earlier runs
  kod=$(kod_zadania "$T")
  if [[ -n $kod ]]; then
    echo "$WS/venv-$ENV/bin/python $K/$kod przebieg --repo $REPO --revision $REV --model_path $(weights_dir "$L") --zadania $T" \
      "--probka ${PROBKA:-pelna} --device ${DEVICE:-cuda} --batch $BATCH --eval_gpu $(gpu_nazwa) --etykieta $L" \
      "--wyjscie ${WYNIKI:-$WS/wyniki}/$(katalog "$T")/$L$dt"
    return
  fi
  local args=(--model "$([[ $LOADER == slayer* ]] && echo slayer || echo hf)" --repo "$REPO" --revision "$REV"
              --model_path "$(weights_dir "$L")" --zadania "$T" --probka "$([[ $T == T03 && -n ${PROBKA_ROLLING:-} ]] && echo "$PROBKA_ROLLING" || echo "${PROBKA:-pelna}")" --device "${DEVICE:-cuda}" --batch "$BATCH"
              --eval_gpu "$(gpu_nazwa)" --etykieta "$L" --wyjscie "${WYNIKI:-$WS/wyniki}/$(katalog "$T")/$L")
  [[ $LOADER == hf-trust ]] && args+=(--trust_remote_code)
  [[ $T == T03 && $LOADER != slayer* ]] && args+=(--max_length "$OKNO_ROLLING")
  echo "$WS/venv-$ENV/bin/python $K/common/ewaluuj.py ${args[*]}$dt"
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

weights_dir() {  # weights_dir LABEL: weights directory of LABEL in this queue. Each GPU queue has its own copy
  # (.gpu<N>): parts of one model may run on two GPUs at once, and a queue deletes its weights when its part ends.
  echo "$WS/modele/$1${GPU_NR:+.gpu$GPU_NR}"
}

pobierz_wagi() {  # pobierz_wagi LABEL (after `model`): $(weights_dir LABEL) ready for ewaluuj.py --model_path
  local d py="$WS/venv-$ENV/bin/python"; d=$(weights_dir "$1")
  # weights kept by `ZOSTAW_WAGI=1 ... proba_cpu` sit in $WS/modele/LABEL: the first GPU queue that needs them takes
  # them over (rename, no second download, no copy left behind); another part of the same model downloads its own
  if [[ $d != "$WS/modele/$1" && ! -e $d && -d $WS/modele/$1 ]]; then mv "$WS/modele/$1" "$d" 2> /dev/null || true; fi
  if [[ $LOADER != slayer-ckpt ]]; then
    "$py" -c "from huggingface_hub import snapshot_download as s; s('$REPO', revision='$REV', local_dir='$d')"
    return
  fi
  # converted earlier on this machine (proba_cpu with ZOSTAW_WAGI=1, then licz): no second 9 GB download;
  # konwertuj.py writes the checkpoint's sha256 into config.json, so a directory of another checkpoint is redone
  if [[ -s $d/model.safetensors ]] && grep -q "\"ckpt_sha256\": \"$CKPT_SHA256\"" "$d/config.json" 2> /dev/null; then
    echo "wagi $1: juz skonwertowane z $CKPT"; return
  fi
  local wzor_repo=${WZORZEC%@*} wzor_rev=${WZORZEC#*@}
  "$py" -c "from huggingface_hub import hf_hub_download as h; h('$REPO', '$CKPT', revision='$REV', local_dir='$d.ckpt')"
  "$py" -c "from huggingface_hub import snapshot_download as s; s('$wzor_repo', revision='$wzor_rev', local_dir='$d.wzorzec', allow_patterns=['model.safetensors', 'config.json', 'tokenizer.json'])"
  "$py" "$K/tools/konwertuj.py" "$d.ckpt/$CKPT" "$d.wzorzec" "$d" --sha256 "$CKPT_SHA256"
  rm -rf "$d.ckpt" "$d.wzorzec"
}

licz_model() {  # licz_model LABEL: download, every task, delete weights; a failed task does not stop the rest
  local L=$1 t T kod powod zad
  model "$L"
  zad=$(zadania_modelu "$L")
  if [[ -z ${zad// /} ]]; then  # a control model none of whose tests is in this run: no download for nothing
    echo "BEZ TESTOW $L: zadne z jego testow ($TESTY_MODELU) nie jest w ZADANIA_ID"
    return 0
  fi
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
  # work marker for the idle guard (tools/straznik_bezczynnosci.py --praca): download, conversion and own-code
  # tasks (ewok.py) run no ewaluuj.py, and the guard would destroy the instance under them
  # (macOS bash 3.2 has no BASHPID: $$ is the script, alive while its queues run)
  local znacznik="$ST/praca/${BASHPID:-$$}_$L"
  mkdir -p "$ST/praca"; echo "$L" > "$znacznik"
  pobierz_wagi "$L"
  zapisz_czas pobranie "$t" "{\"model\": \"$L\", \"bajty\": $(bajty "$(weights_dir "$L")")}"
  for T in $zad; do
    t=$(teraz)
    kod=0
    echo "gpu ${GPU_NR:--} $(gpu_nazwa)" > "$WS/logi/${L}_${T}_$ENV.log"
    $(polecenie "$L" "$T") >> "$WS/logi/${L}_${T}_$ENV.log" 2>&1 || kod=$?
    zapisz_czas ewaluacja "$t" "{\"model\": \"$L\", \"zadanie\": \"$T\", \"kod\": $kod, \"gpu\": \"$(gpu_nazwa)\", \"gpu_nr\": \"${GPU_NR:-}\", \"batch\": \"$BATCH\", \"env\": \"$ENV\", \"dtype\": \"$DTYPE\", \"wyniki\": \"${WYNIKI:-$WS/wyniki}\"}"
  done
  # ZOSTAW_WAGI=1: proba_cpu followed by licz on the same instance downloads each model once
  [[ ${ZOSTAW_WAGI:-0} == 1 ]] || rm -rf "$(weights_dir "$L")"
  rm -f "$znacznik"
}

liczba_gpu() { nvidia-smi -L 2>/dev/null | grep -c '^GPU ' || true; }

item_tasks() {  # item_tasks ITEM: tasks of LABEL (zadania_modelu) or of LABEL:T01,T02 (those)
  local z
  if [[ $1 == *:* ]]; then z=${1#*:}; echo "${z//,/ }"; else zadania_modelu "$1"; fi
}

kolejki() {  # kolejki ITEM...: "<gpu> ITEM ..." per queue; one line "- ITEM ..." with 0 or 1 GPU.
  # With N > 1 GPUs tools/queue_plan.py splits the (model, task) pairs by estimated time (czasy.jsonl of earlier runs
  # in results/ and of this one), not by list order: a model longer than PART (1/3) of the ideal share total / N is
  # cut into LABEL:T.. parts that run on several GPUs. Estimates per queue: $ST/plan_kolejek.txt (only for N > 1).
  # A failed planner fails kolejki (pipefail); a model with no task in this run is named on stderr, not dropped silently.
  local n x z; n=$(liczba_gpu)
  rm -f "$ST/plan_kolejek.txt"
  if (( n <= 1 )); then echo "- $*"; return; fi
  mkdir -p "$ST"
  for x in "$@"; do
    z=$(item_tasks "$x")
    if [[ -z ${z// /} ]]; then echo "BEZ TESTOW $x: zadne z jego testow nie jest w ZADANIA_ID" >&2; continue; fi
    printf '%s\t%s\n' "$x" "$z"
  done | python3 "$K/tools/queue_plan.py" --gpus "$n" --repo "$K" --czasy "$CZ" 2> "$ST/plan_kolejek.txt" | tr -d '\r'
}

plan_kolejek() {  # plan_kolejek ITEM...: output of `kolejki`, or 1 with the planner's error on stderr (a process
  # substitution `< <(kolejki ...)` would hide the error from set -e and run zero queues with code 0)
  local q
  if ! q=$(kolejki "$@") || [[ -z $q ]]; then
    echo "queue plan failed for: $*" >&2; cat "$ST/plan_kolejek.txt" >&2 2> /dev/null || true
    return 1
  fi
  echo "$q"
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
  local nazwa=$1 nr reszta p q kod=0; shift
  local -a pidy=()
  q=$(plan_kolejek "$@") || return 1
  while read -r nr reszta; do
    if [[ $nr == - ]]; then licz_kolejke - $reszta; return; fi
    licz_kolejke "$nr" $reszta < /dev/null > "$WS/logi/${nazwa}_gpu$nr.log" 2>&1 &
    pidy+=($!)
  done <<< "$q"
  for p in "${pidy[@]}"; do wait "$p" || kod=1; done
  return $kod
}

etap=${1:-}
case "$etap" in
  gotowe)
    echo $GOTOWE
    ;;
  lista)
    printf '%s\n' "${MODELE[@]}"
    ;;
  katalogi)
    for T in $ZADANIA_ID; do echo "$T $(katalog "$T")"; done
    ;;
  plan)
    Q=$(plan_kolejek ${2:-$(printf '%s\n' "${MODELE[@]}" | cut -d'|' -f1)}) || exit 1
    while read -r nr reszta; do
      [[ $nr == - ]] || echo "# GPU $nr: $reszta"
      for p in $reszta; do L=${p%%:*}; for T in $(item_tasks "$p"); do
        if [[ $nr == - ]]; then polecenie "$L" "$T"
        else echo "CUDA_VISIBLE_DEVICES=$nr $(GPU_NR=$nr polecenie "$L" "$T")"; fi
      done; done
    done <<< "$Q"
    if [[ -s $ST/plan_kolejek.txt ]]; then cat "$ST/plan_kolejek.txt"; fi  # estimated hours per GPU (tools/queue_plan.py)
    ;;
  przygotuj)
    LIMIT=${2:?safety limit in seconds}
    mkdir -p "$ST/praca" "$WS/wyniki" "$WS/logi" "$WS/modele"
    # work marker for the whole stage: pip, NLTK and the network test leave the GPU idle longer than the guard window
    ZN_PRZYG="$ST/praca/$$_przygotuj"
    echo przygotuj > "$ZN_PRZYG"
    trap 'rm -f "$ZN_PRZYG"' EXIT
    # hard limit: pack, then destroy with the disk (the idle guard only stops the instance)
    nohup python3 $K/tools/bezpiecznik.py po "$LIMIT" "bash $K/tools/przebieg_centralny.sh pakuj" \
      > $WS/logi/bezpiecznik.log 2>&1 &
    bash "$0" straznik
    python3 $K/tools/bezpiecznik.py sprawdz
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
    LISTA=$(lista_licz "${2:-}") || exit 2
    mkdir -p "$ST" "$WS/logi"
    echo "$LISTA" > "$ST/plan_licz.txt"  # read by `kontrola` (pair completeness)
    zapisz_czas licz_plan "$(teraz)" "$(python3 -c 'import json,sys; print(json.dumps({"lista": sys.argv[1].split(), "pomin": sys.argv[2]}))' "$LISTA" "${POMIN:-}")"
    NAZWA="licz_${LISTA// /_}"
    [[ -n ${2:-} ]] || NAZWA=licz_wszystkie
    (( ${#NAZWA} <= 120 )) || NAZWA="licz_$(wc -w <<< "$LISTA" | tr -d ' ')_pozycji"  # file names stop at 255 bytes
    export PYTHONUNBUFFERED=1 NVIDIA_TF32_OVERRIDE=0 HF_HUB_DISABLE_PROGRESS_BARS=1
    w_tle "$NAZWA" "set -e; source $K/tools/przebieg_centralny.sh _funkcje; kod=0; \
      licz_rownolegle $NAZWA $LISTA || kod=1; \
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
  straznik)  # idle guard: GPU < 5% with no evaluation for STRAZNIK_OKNO s -> pack, copy to $WS/wyjscie, stop
    mkdir -p "$WS/logi"
    nohup python3 $K/tools/straznik_bezczynnosci.py --wyjscie "$WS/wyjscie" --okno "${STRAZNIK_OKNO:-600}" \
      --archiwum "$WS/wyniki.tgz" --praca "$ST/praca" --blad "$ST/STOP_NIEUDANY.txt" > $WS/logi/straznik.log 2>&1 &
    echo "idle guard pid $!"
    ;;
  proba_cpu)  # load test: PROBA_N questions (WikiText-2: 1 document) per model x task on CPU, every pair must finish
    export DEVICE=cpu PROBKA=${PROBA_N:-2} PROBKA_ROLLING=1 BATCH=1 WYNIKI=$WS/proba_cpu
    LISTA=${2:-$(printf '%s\n' "${MODELE[@]}" | cut -d'|' -f1)}
    if [[ ${SUCHO:-0} == 1 ]]; then
      for L in $LISTA; do for T in $(zadania_modelu "$L"); do polecenie "$L" "$T"; done; done
      exit 0
    fi
    mkdir -p "$ST" "$WS/logi" "$WS/modele"
    for L in $LISTA; do licz_model "$L"; done
    # a gated model skipped by licz_model has no outputs; its skip stays in $ST/pominiety_<label>.txt
    python3 $K/tools/kontrola_sensu.py --tylko-stan $(for L in $LISTA; do [[ -e $ST/pominiety_$L.txt ]] && continue
      for T in $(zadania_modelu "$L"); do echo "$WYNIKI/$(katalog "$T")/$L"; done; done)
    ;;
  kontrola)  # sanity of full results (score 1.000, below random - 5 points, ...): $WS/logi/kontrola_sensu.txt
    mkdir -p "$WS/logi"
    python3 $K/tools/kontrola_sensu.py "${WYNIKI:-$WS/wyniki}"/*/*/ > $WS/logi/kontrola_sensu.txt && kod=0 || kod=$?
    # pairs of the last `licz` plan without a result: a missing pair is an error, not silence
    if [[ -s $ST/plan_licz.txt ]]; then
      kompletnosc $(cat "$ST/plan_licz.txt") >> $WS/logi/kontrola_sensu.txt || kod=1
    fi
    cat $WS/logi/kontrola_sensu.txt; exit $kod
    ;;
  pakuj)  # wyniki.tgz for the repo: per-question files gzipped, podsumowanie.md left out (number gate reads *.md)
    find $WS/wyniki* -name '*.jsonl' -exec gzip -f {} +
    tar czf $WS/wyniki.tgz -C $WS --exclude podsumowanie.md $(cd $WS && ls -d wyniki*/) czasy.jsonl srodowisko.json logi/freeze_lock.txt logi/freeze_new.txt
    ls -la $WS/wyniki.tgz
    ;;
  stan)
    cat $ST/STOP_NIEUDANY.txt 2>/dev/null || true
    ls -la $ST; cat $ST/pominiety_*.txt 2>/dev/null || true; for f in $WS/logi/*.log; do echo "== $f"; tail -n 2 "$f"; done; tail -n 5 $CZ 2>/dev/null
    nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv; df -h $WS | tail -1
    ;;
  _funkcje) ;;  # sourced: functions only
  *)
    echo "stages: gotowe | lista | katalogi | plan 'LABEL ...' | przygotuj LIMIT_S | licz ['LABEL ...'] | ponow | straznik | proba_cpu ['LABEL ...'] | kontrola | pakuj | stan"; exit 2
    ;;
esac
