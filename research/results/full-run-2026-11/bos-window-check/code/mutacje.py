"""Mutacje kodu liczacego: kazda musi zapalic test. python mutacje.py <python z lm_eval> <katalog roboczy>. Kod 0 = baza zielona i wszystkie zapalone."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

KOD = Path(__file__).parent
PY, ROB = sys.argv[1], Path(sys.argv[2])
PLIKI = ["bos_start.py", "zbierz.py", "warunek_kontroli.py", "test_bos.py", "test_zbierz.py"]
ST = "                if n != 1:\n                    raise BladBos(f\"{n} wiodacych"
MUT = [
    ("BOS na sztywno 0", "bos_start.py", "bos = lm.tokenizer.bos_token_id", "bos = 0"),
    ("BOS z eot", "bos_start.py", "bos = lm.tokenizer.bos_token_id", "bos = lm.eot_token_id"),
    ("wylaczona kontrola tensora", "bos_start.py", ST, ST.replace("if n != 1:", "if False:")),
    ("prog wplywu 0,04 na 0,4", "zbierz.py", "PROG_WPLYW = 0.04", "PROG_WPLYW = 0.4"),
    ("odwrocony filtr znacznika", "zbierz.py", 'if w["start"] >= znacznik}', 'if w["start"] < znacznik}'),
    ("prog werdyktu 3 na 4", "zbierz.py", "a >= 3", "a >= 4"),
    ("prog werdyktu 2 na 1,5", "zbierz.py", "a >= 2", "a >= 1.5"),
    ("SE niezalezne bez pierwiastka", "zbierz.py", 'se_d = math.sqrt(ob["se"] ** 2 + st["se"] ** 2)', 'se_d = ob["se"] ** 2 + st["se"] ** 2'),
    ("SE w parach bez pierwiastka", "zbierz.py", "se = math.sqrt(wa / n)", "se = wa / n"),
    ("warunek kontroli 0,71 w zbierz", "zbierz.py", "round(k[\"value\"], 4) == 0.7095", "round(k[\"value\"], 4) == 0.71"),
    ("warunek kontroli 0,71 w skrypcie", "warunek_kontroli.py", "== 0.7095", "== 0.71"),
    ("wylaczona weryfikacja sha", "zbierz.py", "    if bledy:\n        print(\"NIEZGODNE", "    if False:\n        print(\"NIEZGODNE"),
    ("odwrocony warunek ARC", "zbierz.py", "liczbowy = abs(d) <= ARC_PROG", "liczbowy = abs(d) >= ARC_PROG"),
    ("usuniete sprawdz_wejscia z main", "zbierz.py", "    sprawdz_wejscia(sys.argv[4], sur, manifest, stary_wsc)\n", ""),
    ("pominiete sha manifestu", "zbierz.py", 'if sha(manifest) != z["manifest"]:', "if False:"),
    ("pominiete sha starego WSC", "zbierz.py", 'if sha(stary_wsc) != z["wsc273_stary"]:', "if False:"),
    ("ignorowany kod pary", "zbierz.py", 'if w and w["kod"] == 0 else None', "if w else None"),
    ("stara roznica ARC-Easy", "zbierz.py", '"stara_roznica": sl["wartosc"] - a51["stara"]', '"stara_roznica": sl["wartosc"] - a51["nowa"]'),
    ("kontrola_sensu zawsze prawda", "zbierz.py", 'def kontrola_sensu(ob):\n', "def kontrola_sensu(ob):\n    return True\n"),
    ("pole sensowny pary na sztywno", "zbierz.py", '"sensowny": kontrola_sensu(ob)', '"sensowny": True'),
    ("pole sensowny kontroli na sztywno", "zbierz.py", '"sensowny": kontrola_sensu(k)', '"sensowny": True'),
    ("pole sensowny ARC na sztywno", "zbierz.py", '"sensowny": kontrola_sensu(arc)', '"sensowny": True'),
    ("zliczenie zadan bez warunku BOS", "zbierz.py", '"zadan_z_jednym_bos": sum(1 for r in z if r["n"] == 1 and r["w"] == 1)', '"zadan_z_jednym_bos": len(z)'),
    ("zliczenie wywolan bez warunku BOS", "zbierz.py", '"wywolan_z_jednym_bos": sum(1 for r in m if r["n"] == 1)', '"wywolan_z_jednym_bos": len(m)'),
    ("warunek_kontroli bez stanu", "warunek_kontroli.py", 'obs["state"] == "ok" and ', ""),
    ("zbierz bez stanu kontroli", "zbierz.py", 'wazny = k["state"] == "ok" and ', "wazny = "),
]
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


def testy(k):
    w = subprocess.run([PY, "-m", "pytest", "test_bos.py", "test_zbierz.py", "-q", "-p", "no:cacheprovider", "--no-header", "-x"],
                       cwd=k, env=ENV, capture_output=True, text=True, timeout=240)
    return w.returncode, w.stdout.strip().splitlines()[-1] if w.stdout.strip() else ""


def przygotuj(k):
    shutil.rmtree(k, ignore_errors=True)
    k.mkdir(parents=True)
    for p in PLIKI:
        shutil.copy(KOD / p, k / p)


zle = 0
k = ROB / "baza"
przygotuj(k)
rc, ost = testy(k)
print(f"BAZA kod {rc}: {ost}")
zle += rc != 0
for nazwa, plik, old, new in MUT:
    k = ROB / "m"
    przygotuj(k)
    t = (k / plik).read_text(encoding="utf-8")
    if old not in t:
        print(f"NIE ZASTOSOWANO: {nazwa}")
        zle += 1
        continue
    (k / plik).write_text(t.replace(old, new), encoding="utf-8")
    rc, ost = testy(k)
    print(f"{'ZAPALONA' if rc else 'PRZESZLA'} [{nazwa}] kod {rc}: {ost[:110]}")
    zle += rc == 0
print("KOD", 1 if zle else 0)
sys.exit(1 if zle else 0)
