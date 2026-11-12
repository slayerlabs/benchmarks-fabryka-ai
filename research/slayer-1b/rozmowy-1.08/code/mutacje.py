"""Mutacje kodu pomiaru: każda wprowadzona osobno, potem code/test_rozmowy.py; mutacja ma zapalić test (kod != 0).
Plik źródłowy wraca bajt w bajt po każdej mutacji (także po błędzie).

python -I code/mutacje.py  -> wyniki/mutacje.json
"""
import json
import subprocess
import sys
from pathlib import Path

KOD = Path(__file__).resolve().parent
BADANIE = KOD.parent
COMMON = BADANIE.parents[1] / "common"

MUTACJE = [
    ("Slayer bez BOS", KOD / "modele.py", "return [self.m.bos] + self.m.encode(tekst)", "return self.m.encode(tekst)"),
    ("Slayer z BOS = 1", COMMON / "slayer_model.py", "    BOS = 0 ", "    BOS = 1 "),
    ("transformers z add_special_tokens=False", KOD / "modele.py",
     'return self.tok(tekst, add_special_tokens=True)["input_ids"]',
     'return self.tok(tekst, add_special_tokens=False)["input_ids"]'),
    ("EOS LFM bez 7", KOD / "modele.py", '"lfm": {2, 7}}', '"lfm": {2}}'),
    ("top-p odcina po skumulowanym p z tokenem", KOD / "generuj.py", 'ps[(cum - ps) > dek["top_p"]] = 0',
     'ps[cum > dek["top_p"]] = 0'),
    ("top-p 0,95 zamiast 0,9", KOD / "generuj.py", "temperatura=0.7, top_p=0.9,", "temperatura=0.7, top_p=0.95,"),
    ("seed bez numeru pozycji", KOD / "generuj.py", 'SEED_BAZA * d["seed"] + nr_pozycji', 'SEED_BAZA * d["seed"]'),
    ("tolerancja liczby 0,5", KOD / "ocena.py", "def ocen_liczba(odp, cel, tol=0.005):",
     "def ocen_liczba(odp, cel, tol=0.5):"),
    ("Holm wyłączony", KOD / "analiza.py", "        out[i] = biezace if ps[i] is not None else None",
     "        out[i] = ps[i]"),
]


def main():
    wyn = []
    for opis, plik, stare, nowe in MUTACJE:
        oryg = plik.read_bytes()
        tekst = oryg.decode("utf-8")
        assert tekst.count(stare) == 1, (opis, plik)
        try:
            plik.write_text(tekst.replace(stare, nowe), encoding="utf-8")
            r = subprocess.run([sys.executable, "-I", str(KOD / "test_rozmowy.py")], capture_output=True, text=True,
                               timeout=600)
        finally:
            plik.write_bytes(oryg)
        ostatnia = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
        wyn.append(dict(opis=opis, plik=plik.name, zapalona=r.returncode != 0, ostatnia_linia=ostatnia[0][:200]))
        print(("ZAPALONA " if r.returncode else "ZIELONA  ") + opis)
    r = subprocess.run([sys.executable, "-I", str(KOD / "test_rozmowy.py")], capture_output=True, text=True)
    assert r.returncode == 0, "po przywróceniu testy muszą przechodzić"
    (BADANIE / "wyniki/mutacje.json").write_text(json.dumps(wyn, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.exit(0 if all(x["zapalona"] for x in wyn) else 1)


if __name__ == "__main__":
    main()
