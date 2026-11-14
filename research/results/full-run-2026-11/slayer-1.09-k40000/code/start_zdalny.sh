#!/usr/bin/env bash
# Na instancji: kod z git archive, cache EWoK (gated, bez tokenu HF na instancji), `przygotuj` (bezpiecznik z limitem
# z protokolu, straznik bezczynnosci, test 1 GB z HF, venv lock), potem kolejka.sh. Jeden proces w tle.
set -u
WS=/workspace
K=$WS/repos/fabryka/research
LIMIT_S=${LIMIT_S:-21000}
mkdir -p "$WS/repos/fabryka" "$WS/logi" "$WS/stan/praca" "$WS/.hf_home/hub"
tar xzf "$WS/paczka.tgz" -C "$WS/repos/fabryka"
tar xzf "$WS/ewok_cache.tgz" -C "$WS/.hf_home/hub"
export K WS HF_HOME=$WS/.hf_home
bash "$K/tools/przebieg_centralny.sh" przygotuj "$LIMIT_S" > "$WS/logi/przygotuj.log" 2>&1
echo "przygotuj kod $?" > "$WS/PRZYGOTUJ_KOD"
bash "$K/results/full-run-2026-11/slayer-1.09-k40000/code/kolejka.sh" > "$WS/logi/kolejka_stdout.log" 2>&1
