#!/bin/bash
# Niezależna ewaluacja jednego checkpointu Slayera 1B.
#   wspolne/ewaluuj_slayer.sh <repo_hf> <revision>
# np. wspolne/ewaluuj_slayer.sh SlayerLab/Slayer1B-1.06 ef81be58742544ad32e1afab38db011fec209609
#
# Zmienne (opcjonalne):
#   MODEL_PATH   katalog z wagami pobranymi wcześniej (np. models/slayer1b-106); bez niej HFLM pobiera z HF
#   DEVICE       cpu (domyślnie, pod nice -n 19) | cuda | mps
#   BATCH        rozmiar batcha (domyślnie 1 jak w Space; na GPU np. 16 albo auto)
#   PROBKA       panel200 (domyślnie, jak Space) | pelna | liczba dokumentów
#   ZADANIA      domyślnie T02,T03,T04,T44,T45,T46 (ARC-C pierwszy)
#   ETYKIETA, STEP, TOKENS, EVAL_GPU   kolumny wiersza scores-history.csv
#   HISTORIA_CSV istniejący scores-history.csv, do którego dopisać wiersz
#   WYJSCIE      katalog wyników (domyślnie wyniki_slayer/<repo>@<rev8>)
#   TRUST_REMOTE_CODE=1  gdy architektura modelu wymaga własnego kodu z repo
#   OFFLINE=1    bez sieci: zbiory z cache (najpierw wspolne/pobierz_zbiory.py), model z MODEL_PATH
set -euo pipefail
if [ "${OFFLINE:-0}" = "1" ]; then
  export HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1
fi

if [ $# -lt 2 ]; then
  echo "użycie: $0 <repo_hf> <revision>" >&2
  exit 64
fi
REPO="$1"
REV="$2"
KORZEN="$(cd "$(dirname "$0")/.." && pwd)"
PY="$KORZEN/.venv-eval/bin/python"
if [ ! -x "$PY" ]; then
  echo "brak $PY: python3 -m venv .venv-eval && .venv-eval/bin/pip install -r wspolne/requirements.lock.txt" >&2
  exit 69
fi

DEVICE="${DEVICE:-cpu}"
WYJSCIE="${WYJSCIE:-$KORZEN/wyniki_slayer/${REPO//\//_}@${REV:0:8}}"
ARGS=(--model hf --repo "$REPO" --revision "$REV" --device "$DEVICE" --batch "${BATCH:-1}"
      --probka "${PROBKA:-panel200}" --wyjscie "$WYJSCIE" --eval_gpu "${EVAL_GPU:-}")
[ -n "${ZADANIA:-}" ] && ARGS+=(--zadania "$ZADANIA")
[ -n "${MODEL_PATH:-}" ] && ARGS+=(--model_path "$MODEL_PATH")
[ -n "${ETYKIETA:-}" ] && ARGS+=(--etykieta "$ETYKIETA")
[ -n "${STEP:-}" ] && ARGS+=(--step "$STEP")
[ -n "${TOKENS:-}" ] && ARGS+=(--tokens "$TOKENS")
[ -n "${HISTORIA_CSV:-}" ] && ARGS+=(--historia_csv "$HISTORIA_CSV")
[ "${TRUST_REMOTE_CODE:-0}" = "1" ] && ARGS+=(--trust_remote_code)

NICE=()
[ "$DEVICE" = "cpu" ] && NICE=(nice -n 19)
mkdir -p "$WYJSCIE"
${NICE[@]+"${NICE[@]}"} "$PY" "$KORZEN/wspolne/ewaluuj.py" "${ARGS[@]}" 2> >(tee "$WYJSCIE/stderr.log" >&2)
