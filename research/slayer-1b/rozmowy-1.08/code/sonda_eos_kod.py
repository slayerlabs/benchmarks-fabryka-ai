"""Diagnoza po pomiarze (eksploracyjna): który token EOS kończy pustą odpowiedź LFM na poleceniach `kod`.

python -I code/sonda_eos_kod.py <model>  -> wyniki/sonda_eos_kod_<model>.json
Dla każdego polecenia `kod` (szablon A): p każdego tokenu z EOS modelu i 5 najbardziej prawdopodobnych tokenów
jako pierwszego tokenu odpowiedzi.
"""
import json
import sys
from pathlib import Path

import torch

KOD = Path(__file__).resolve().parent
sys.path.insert(0, str(KOD))
import modele  # noqa: E402
import szablony  # noqa: E402
from generuj import BADANIE, wczytaj_zestaw  # noqa: E402

m = modele.wczytaj(sys.argv[1])
pozycje, shoty = wczytaj_zestaw()
out = []
for p in pozycje:
    if p["typ"] != "kod":
        continue
    ids = m.encode(szablony.prompt("A", p, shoty[p["kat"]]))
    pr = torch.softmax(m.logity_pelne(ids)[-1].double(), -1)
    top = torch.topk(pr, 5)
    out.append(dict(id=p["id"], p_eos={str(e): float(pr[e]) for e in sorted(m.eos)},
                    top5=[(m.decode([int(i)]), float(v)) for v, i in zip(top.values, top.indices)]))
(BADANIE / "wyniki" / f"sonda_eos_kod_{sys.argv[1]}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
for o in out[:5]:
    print(o)
