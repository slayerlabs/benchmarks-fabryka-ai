"""Rozbicie sondy EOS na pojedyncze tokeny zbioru EOS (runda poprawek 2, po pomiarze, eksploracyjne).
Ten sam tekst sondy co code/bpb.py (szablony.prompt_sondy, bez i z „\\n”), p każdego tokenu z EOS osobno.

python -I code/sonda_tokeny.py <model>  -> wyniki/surowe/sonda_tokeny_<model>.jsonl
"""
import json
import sys
from pathlib import Path

import torch

KOD = Path(__file__).resolve().parent
sys.path.insert(0, str(KOD))
import generuj  # noqa: E402
import modele  # noqa: E402
import szablony  # noqa: E402
from bpb import KROTKIE  # noqa: E402


@torch.no_grad()
def main():
    klucz = sys.argv[1]
    pozycje, _ = generuj.wczytaj_zestaw()
    m = modele.wczytaj(klucz)
    out = generuj.BADANIE / "wyniki" / "surowe" / f"sonda_tokeny_{klucz}.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for p in pozycje:
            if p["typ"] not in KROTKIE:
                continue
            w = dict(id=p["id"], kat=p["kat"])
            for nl in (False, True):
                ids = m.encode(szablony.prompt_sondy(p, nl))
                pr = torch.softmax(m.logity_pelne(ids)[-1].double(), -1)
                w["nl" if nl else "bez_nl"] = {str(t): float(pr[t]) for t in sorted(m.eos)}
            f.write(json.dumps(w, ensure_ascii=False) + "\n")
    print(klucz, "zapisano", out.name)


if __name__ == "__main__":
    main()
