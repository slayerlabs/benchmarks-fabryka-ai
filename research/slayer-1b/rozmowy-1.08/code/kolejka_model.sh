#!/bin/bash
# Kolejka JEDNEGO modelu (generacje A, B, BPB) — trzy takie procesy idą równolegle, po jednym na model
# (decyzja orkiestratora 12.11, odstępstwo od „jeden ciężki proces naraz”: 51 GB RAM, ~78% wolne, MPS niewysycone).
# Wyniki modelu nie zależą od tego, co liczy się obok (osobny proces, własne generatory seedów).
# Użycie: bash code/kolejka_model.sh <python> <model> [pid_do_odczekania] > log 2>&1
PY="$1"; M="$2"; CZEKAJ="$3"
KOD="$(cd "$(dirname "$0")" && pwd)"
if [ -n "$CZEKAJ" ]; then while kill -0 "$CZEKAJ" 2>/dev/null; do sleep 10; done; fi
krok() { echo "=== START $* $(date -u +%FT%TZ)"; "$PY" -I "$@" || echo "=== BLAD $* kod $?"; echo "=== KONIEC $* $(date -u +%FT%TZ)"; }
krok "$KOD/generuj.py" "$M" A
krok "$KOD/generuj.py" "$M" B
krok "$KOD/bpb.py" "$M"
echo "=== KOLEJKA $M ZAKONCZONA $(date -u +%FT%TZ)"
