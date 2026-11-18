#!/usr/bin/env bash
# Na instancji: rozpakowanie kodu, `przygotuj` z repo fabryki, potem kolejka pomiaru. Jeden proces w tle.
set -u
WS=/workspace
K=$WS/repos/fabryka/research
mkdir -p "$WS/repos/fabryka" "$WS/pomiar" "$WS/logi" "$WS/stan/praca"
tar xzf "$WS/paczka.tgz" -C "$WS/repos/fabryka"
tar xzf "$WS/pomiar.tgz" -C "$WS/pomiar"
export K WS
bash "$K/tools/przebieg_centralny.sh" przygotuj 6000 > "$WS/logi/przygotuj.log" 2>&1
echo "przygotuj kod $?" > "$WS/PRZYGOTUJ_KOD"
bash "$WS/pomiar/kolejka.sh" > "$WS/logi/kolejka_stdout.log" 2>&1
