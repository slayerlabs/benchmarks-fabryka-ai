#!/usr/bin/env bash
# Central run in one command on a vast.ai GPU instance (pytorch image, /workspace): `przygotuj`, then `licz`.
#   bash research/tools/start.sh MODEL [gotowe|wszystkie]
# gotowe (default): the GOTOWE tasks of przebieg_centralny.sh (= "✅ Gotowe" in STATUS.md); wszystkie: every task.
# K (code) comes from this file's location, so the repo may be cloned anywhere. HF_TOKEN must be exported.
# LIMIT_S (172800): safety limit of `przygotuj`. START_SUCHO=1: print the two commands instead of running them.
set -euo pipefail
K=$(CDPATH= cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)  # CDPATH: cd would also print the path into K
export K
WS=${WS:-/workspace}
P=$K/tools/przebieg_centralny.sh
UZYCIE="uzycie: bash $K/tools/start.sh MODEL [gotowe|wszystkie]"

MODEL=${1:-}
ZAKRES=${2:-gotowe}
if [[ -z $MODEL ]]; then
  echo "$UZYCIE" >&2
  echo "modele: $(bash "$P" lista | cut -d'|' -f1 | tr '\n' ' ')" >&2
  exit 2
fi
if ! bash "$P" lista | cut -d'|' -f1 | grep -qxF "$MODEL"; then
  echo "nieznany model: $MODEL; modele: $(bash "$P" lista | cut -d'|' -f1 | tr '\n' ' ')" >&2
  exit 2
fi
case "$ZAKRES" in
  gotowe) Z=$(bash "$P" gotowe); POZYCJA="$MODEL:${Z// /,}" ;;
  wszystkie) Z=$(bash "$P" katalogi | cut -d' ' -f1 | tr '\n' ' '); Z=${Z% }; POZYCJA=$MODEL ;;
  *) echo "$UZYCIE" >&2; exit 2 ;;
esac
if [[ -z ${HF_TOKEN:-} ]]; then
  echo "Brak HF_TOKEN. Najpierw: export HF_TOKEN=<token HF z dostepem do ewok-core/ewok-core-1.0>" >&2
  echo "(bez dostepu T53 konczy sie GatedRepoError; Bielik bez dostepu zostaje pominiety)" >&2
  exit 3
fi
export HF_TOKEN

echo "kod (K): $K"
echo "model: $MODEL, testy ($ZAKRES, $(wc -w <<< "$Z" | tr -d ' ')): $Z"
if [[ ${START_SUCHO:-0} == 1 ]]; then
  echo "bash $P przygotuj ${LIMIT_S:-172800}"
  echo "bash $P licz \"$POZYCJA\""
else
  bash "$P" przygotuj "${LIMIT_S:-172800}"
  bash "$P" licz "$POZYCJA"
fi

cat <<KONIEC

Liczenie idzie w tle; po nim instancje zatrzymuje straznik bezczynnosci.
  postep:    bash $P stan    (log: $WS/logi/licz_$POZYCJA.log)
  wyniki:    $WS/wyniki/<benchmark>/$MODEL/, po koncu archiwum $WS/wyniki.tgz (kopia w $WS/wyjscie/)
  padniete:  bash $P ponow    (powtarza pary model-test zakonczone bledem)
  zatrzymanie: plik $WS/stan/STOP_NIEUDANY.txt znaczy, ze straznik NIE zatrzymal instancji (zatrzymaj recznie)
KONIEC
