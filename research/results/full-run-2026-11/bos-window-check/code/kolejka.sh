#!/usr/bin/env bash
# Kolejka pomiaru z PROTOKOL.md na instancji: KONTROLA T06, BOS x6, OKNO T03, KONTROLA-ARC.
# Blad pary zapisuje sie w /workspace/kolejka.jsonl i kolejka idzie dalej.
# KONTROLA inna niz 0,7095 (4 miejsca) konczy BOS i OKNO; KONTROLA-ARC jest od tego warunku niezalezna.
set -u
K=/workspace/repos/fabryka/research
WS=/workspace
ST=$WS/stan
KOD=$WS/pomiar
export K WS HF_HOME=$WS/.hf_home PYTHONUNBUFFERED=1 NVIDIA_TF32_OVERRIDE=0 HF_HUB_DISABLE_PROGRESS_BARS=1 NLTK_DATA=$WS/nltk_data
PY=$WS/venv-lock/bin/python
E=$K/common/ewaluuj.py
WY=$WS/wyniki
GPU=NVIDIA_GeForce_RTX_5090
PYT=EleutherAI/pythia-1b-v0
PREV=f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0
EUR=utter-project/EuroLLM-1.7B
EREV=c730cd9b616799ace3c65e927d63191446f59374
LOG=$WS/kolejka.jsonl

mkdir -p "$ST/praca" "$WY" "$WS/logi"
ZN="$ST/praca/$$_kolejka"
echo kolejka > "$ZN"
trap 'rm -f "$ZN"' EXIT

teraz() { date -u +%Y-%m-%dT%H:%M:%S; }
wpis() { echo "{\"wariant\":\"$1\",\"zadanie\":\"$2\",\"start\":\"$3\",\"koniec\":\"$(teraz)\",\"kod\":$4}" >> "$LOG"; }
wagi() { "$PY" -c "from huggingface_hub import snapshot_download as s; print(s('$1', revision='$2', ignore_patterns=['*.msgpack','*.h5','*.ot']))" | tail -1; }

MP=$(wagi "$PYT" "$PREV")
echo "pythia $MP" >> "$WS/logi/kolejka.log"
ME=$(wagi "$EUR" "$EREV")
echo "eurollm $ME" >> "$WS/logi/kolejka.log"
"$PY" "$KOD/zaladuj.py" "$MP" pythia-1b-v0 > "$WS/logi/zaladunek_pythia.txt" 2>&1; echo "zaladunek pythia kod $?" >> "$WS/logi/kolejka.log"
"$PY" "$KOD/zaladuj.py" "$ME" eurollm-1.7b > "$WS/logi/zaladunek_eurollm.txt" 2>&1; echo "zaladunek eurollm kod $?" >> "$WS/logi/kolejka.log"
PARG=(--model hf --repo "$PYT" --revision "$PREV" --model_path "$MP" --probka pelna --device cuda --batch 1 --eval_gpu "$GPU" --etykieta pythia-1b-v0)

katalog() { case "$1" in T51) echo arc-easy;; T05) echo hellaswag;; T17) echo lambada;; T06) echo piqa;; T07) echo winogrande;; T14) echo wsc273;; T03) echo wikitext-2;; esac; }

# KONTROLA: komenda z manifestu bez zmian
t=$(teraz); W=$WY/kontrola/piqa/pythia-1b-v0
"$PY" "$E" "${PARG[@]}" --zadania T06 --wyjscie "$W" > "$WS/logi/kontrola_T06.log" 2>&1; k=$?
wpis KONTROLA T06 "$t" "$k"

WAZNY=$("$PY" "$KOD/warunek_kontroli.py" "$W/results_rozszerzone.json")
echo "$WAZNY" > "$WS/POMIAR_WAZNY.txt"

if [ "$WAZNY" = "tak" ]; then
  for T in T51 T05 T17 T06 T07 T14; do
    t=$(teraz); W=$WY/bos/$(katalog "$T")/pythia-1b-v0
    BOS_LOG="$W/bos.jsonl" "$PY" "$KOD/bos_start.py" "$E" "${PARG[@]}" --zadania "$T" --wyjscie "$W" > "$WS/logi/bos_$T.log" 2>&1; k=$?
    wpis BOS "$T" "$t" "$k"
  done
  t=$(teraz); W=$WY/okno/wikitext-2/pythia-1b-v0
  "$PY" "$E" "${PARG[@]}" --zadania T03 --wyjscie "$W" --max_length 2048 > "$WS/logi/okno_T03.log" 2>&1; k=$?
  wpis OKNO T03 "$t" "$k"
fi

# Wagi Pythii sa niepotrzebne przy KONTROLI-ARC, ale dysk ma zapas, wiec zostaja do konca instancji.
t=$(teraz)
W=$WY/kontrola-arc/arc-challenge/eurollm-1.7b
"$PY" "$K/tools/ewaluacja/ewaluuj_shoty.py" 25 --model hf --repo "$EUR" --revision "$EREV" --model_path "$ME" --zadania T02 --probka pelna --device cuda --batch 1 --eval_gpu "$GPU" --etykieta eurollm-1.7b --wyjscie "$W" > "$WS/logi/kontrola_arc_T02.log" 2>&1; k=$?
wpis KONTROLA-ARC T02 "$t" "$k"

"$PY" "$K/tools/kontrola_sensu.py" "$WY"/*/*/*/ > "$WS/logi/kontrola_sensu.txt" 2>&1; echo "kontrola_sensu kod $?" >> "$WS/logi/kolejka.log"
"$WS/venv-lock/bin/pip" freeze > "$WS/logi/freeze_lock_koniec.txt" 2>/dev/null
touch "$WS/KOLEJKA_KONIEC"
