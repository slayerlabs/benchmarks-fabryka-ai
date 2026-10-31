"""Loss na odłożonych danych: per okno 4096 tokenów, per komponent, fp32.

python wygaszanie/heldout.py --model <katalog> --dane /workspace/dane --wyjscie wyniki/heldout_<etykieta>.json

Okna nie przechodzą przez granice komponentów (heldout_meta.json). Strata liczona jak w treningu:
pierwsze 4096 tokenów okna -> następne 4096 (cel przesunięty o 1), bez dodatkowego BOS.
Zapisuje listę strat per okno (do parowanego bootstrapu w porownaj.py).
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "wspolne"))
from slayer_model import Slayer  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--dane", required=True)
    p.add_argument("--wyjscie", required=True)
    p.add_argument("--blok", type=int, default=4096)
    p.add_argument("--device", default="cuda")
    a = p.parse_args()
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    dane = np.fromfile(Path(a.dane) / "val.bin", dtype=np.uint16)
    meta = json.loads((Path(a.dane) / "heldout_meta.json").read_text())["zakresy"]
    m = Slayer(a.model, device=a.device)
    t0 = time.time()
    okna = []
    for k, (lo, hi) in meta.items():
        for s in range(lo, hi - a.blok - 1, a.blok):
            x = torch.from_numpy(dane[s:s + a.blok].astype(np.int64))[None].to(a.device)
            y = torch.from_numpy(dane[s + 1:s + a.blok + 1].astype(np.int64)).to(a.device)
            with torch.no_grad():
                h = m.ukryte(x)[0]
                loss = sum(F.cross_entropy(m.glowa(h[i:i + 1024]), y[i:i + 1024], reduction="sum").item()
                           for i in range(0, a.blok, 1024)) / a.blok
            okna.append({"komponent": k, "start": s, "loss": loss})
    straty = np.array([o["loss"] for o in okna])
    per = {k: float(np.mean([o["loss"] for o in okna if o["komponent"] == k])) for k in meta}
    out = {"model": a.model, "config_step": m.cfg.get("step"), "n_okien": len(okna), "blok": a.blok,
           "loss": float(straty.mean()), "se": float(straty.std(ddof=1) / np.sqrt(len(straty))),
           "per_komponent": per, "czas_s": round(time.time() - t0), "okna": okna}
    Path(a.wyjscie).parent.mkdir(parents=True, exist_ok=True)
    Path(a.wyjscie).write_text(json.dumps(out))
    print(json.dumps({k: v for k, v in out.items() if k != "okna"}))


if __name__ == "__main__":
    main()
