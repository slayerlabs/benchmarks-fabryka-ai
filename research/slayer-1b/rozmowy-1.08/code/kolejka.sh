#!/bin/bash
# Cała kolejka pomiaru jednym procesem w tle, jeden model naraz (Mac, MPS). Błąd jednego kroku jest logowany,
# kolejka idzie dalej. Użycie: bash code/kolejka.sh <python_modeli> <katalog_danych_kontroli> > log 2>&1
PY="$1"
KONTROLA="$2"
KOD="$(cd "$(dirname "$0")" && pwd)"
krok() { echo "=== START $* $(date -u +%FT%TZ)"; "$PY" -I "$@" || echo "=== BLAD $* kod $?"; echo "=== KONIEC $* $(date -u +%FT%TZ)"; }
krok "$KOD/kontrola.py" licz "$KONTROLA"
for M in slayer bielik lfm; do
  krok "$KOD/generuj.py" "$M" A
  krok "$KOD/generuj.py" "$M" B
  krok "$KOD/bpb.py" "$M"
done
echo "=== KOLEJKA ZAKONCZONA $(date -u +%FT%TZ)"
