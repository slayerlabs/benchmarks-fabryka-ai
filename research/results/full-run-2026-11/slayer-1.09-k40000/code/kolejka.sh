#!/usr/bin/env bash
# Kolejka pomiaru z PROTOKOL.md na instancji, jeden proces w tle: wagi_40000.pt -> model.safetensors (konwertuj.py,
# wzorzec 1.08), potem 30 par (1.08 i 1.09-k40000 x 15 testow GOTOWE) runnerem ewaluacja.py (blad pary zapisuje sie,
# kolejka idzie dalej), na koncu eksport z probkami per pytanie. Postep: $WS/logi/kolejka.log, koniec: $WS/KONIEC.
set -u
K=/workspace/repos/fabryka/research
WS=/workspace
ST=$WS/stan
export K WS HF_HOME=$WS/.hf_home PYTHONUNBUFFERED=1 NVIDIA_TF32_OVERRIDE=0 HF_HUB_DISABLE_PROGRESS_BARS=1 NLTK_DATA=$WS/nltk_data
PY=$WS/venv-lock/bin/python
R=$K/tools/ewaluacja/ewaluacja.py
WY=$WS/wyniki/k109
M=$K/tools/ewaluacja/modele/slayer1b-1.09-k40000
LOG=$WS/logi/kolejka.log
SHA_CKPT=f83f7017872f7121f002bc77499c625304bd28e2c87fb4afaa0e3d445bd31881

mkdir -p "$ST/praca" "$WY" "$WS/logi"
ZN="$ST/praca/$$_kolejka"
echo kolejka > "$ZN"
trap 'rm -f "$ZN"' EXIT
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%S) $*" >> "$LOG"; }

log start
CK=$("$PY" -c "from huggingface_hub import hf_hub_download as h; print(h('SlayerLab/Slayer1B-1.09-checkpoints', 'wagi_40000.pt', revision='cff81fdcc05f0d91e9ba45b09fe78f769d7e0903'))" 2>> "$LOG" | tail -1)
log "ckpt $CK"
WZ=$("$PY" -c "from huggingface_hub import snapshot_download as s; print(s('SlayerLab/Slayer1B-1.08', revision='5f854a0cc7160594d54d1788d37a44e8ebabe16c', allow_patterns=['*.json', '*.txt', '*.py', 'tokenizer*', '*.safetensors']))" 2>> "$LOG" | tail -1)
log "wzorzec $WZ"
"$PY" "$K/results/full-run-2026-11/slayer-1.09-k40000/code/sprawdz_architekture.py" "$CK" "$WZ" "$SHA_CKPT" \
  --wyjscie "$WS/logi/architektura.json" > /dev/null 2>> "$LOG"
log "architektura kod $?"
"$PY" "$K/slayer-1b/wygaszanie/konwertuj.py" "$CK" "$WZ" "$M" --sha256 "$SHA_CKPT" > "$WS/logi/konwersja.json" 2>> "$LOG"
log "konwersja kod $?"
"$PY" "$R" --wyniki "$WY" --python-lock "$PY" licz slayer1b-1.08 slayer1b-1.09-k40000 --zadania gotowe --pobierz \
  --rownolegle "${ROWNOLEGLE:-4}" > "$WS/logi/runner.log" 2>&1
log "runner kod $?"
"$PY" "$R" --wyniki "$WY" --python-lock "$PY" eksport --wyjscie "$WS/eksport_k109.tgz" > "$WS/logi/eksport.log" 2>&1
log "eksport kod $?"
sha256sum "$WS/eksport_k109.tgz" > "$WS/eksport_k109.sha256"
touch "$WS/KONIEC"
log koniec
