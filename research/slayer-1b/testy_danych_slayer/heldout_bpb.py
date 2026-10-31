"""Loss i BPB na wspólnym heldoucie: per okno 4096 tokenów, per komponent, fp32.

python testy_danych_slayer/heldout_bpb.py --model <katalog> --dane /workspace/dane_ramion/heldout \
    --wyjscie wyniki/heldout_<etykieta>.json

Jak wygaszanie/heldout.py (okna w obrębie komponentu, cel przesunięty o 1, bez dodatkowego BOS), plus
bajty UTF-8 celów okna z tablicy bajtów tokenów (ByteLevel BPE: znak tokenu = 1 bajt, token specjalny = 0),
więc BPB = suma straty / (ln 2 · bajty) jest dokładne, bez dekodowania okien.
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

LN2 = math.log(2)


def bajty_tokenow(tok):
    """Tablica [vocab] bajtów UTF-8 na token. Tylko ByteLevel BPE; inny tokenizer = STOP (BPB byłoby błędne)."""
    cfg = json.loads(tok.to_str())
    dek = (cfg.get("decoder") or {}).get("type")
    if dek != "ByteLevel":
        raise SystemExit(f"STOP: dekoder {dek}, tablica bajtów obsługuje tylko ByteLevel")
    specjalne = {t["id"] for t in cfg.get("added_tokens", []) if t.get("special")}
    v = tok.get_vocab_size()
    out = np.zeros(v, dtype=np.int64)
    for i in range(v):
        s = tok.id_to_token(i)
        out[i] = 0 if (s is None or i in specjalne) else len(s)
    return out


def sprawdz_bajty(tok, tab, teksty):
    """Suma bajtów tokenów == len(tekst.encode()) dla próbek; zwraca listę rozbieżności."""
    zle = []
    for t in teksty:
        n = int(tab[tok.encode(t, add_special_tokens=False).ids].sum())
        if n != len(t.encode("utf-8")):
            zle.append((t[:40], n, len(t.encode("utf-8"))))
    return zle


def okna_komponentu(lo, hi, blok):
    return list(range(lo, hi - blok - 1, blok))


def main():
    import torch
    import torch.nn.functional as F
    from tokenizers import Tokenizer
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "wspolne"))
    from slayer_model import Slayer

    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--dane", required=True)
    p.add_argument("--wyjscie", required=True)
    p.add_argument("--tokenizer", help="domyślnie <model>/tokenizer.json")
    p.add_argument("--blok", type=int, default=4096)
    p.add_argument("--device", default="cuda")
    a = p.parse_args()
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    tok = Tokenizer.from_file(a.tokenizer or str(Path(a.model) / "tokenizer.json"))
    tab = bajty_tokenow(tok)
    zle = sprawdz_bajty(tok, tab, ["Zażółć gęślą jaźń.", "Mathematics, 2+2=4 — €5 ąę", "  wiele   spacji\n\nłódź"])
    if zle:
        raise SystemExit(f"STOP: tablica bajtów niezgodna: {zle}")
    dane = np.fromfile(Path(a.dane) / "val.bin", dtype=np.uint16)
    meta = json.loads((Path(a.dane) / "heldout_meta.json").read_text())["zakresy"]
    m = Slayer(a.model, device=a.device)
    t0 = time.time()
    okna = []
    for k, (lo, hi) in meta.items():
        for s in okna_komponentu(lo, hi, a.blok):
            x = torch.from_numpy(dane[s:s + a.blok].astype(np.int64))[None].to(a.device)
            yn = dane[s + 1:s + a.blok + 1].astype(np.int64)
            y = torch.from_numpy(yn).to(a.device)
            with torch.no_grad():
                h = m.ukryte(x)[0]
                suma = sum(F.cross_entropy(m.glowa(h[i:i + 1024]).float(), y[i:i + 1024], reduction="sum").item()
                           for i in range(0, a.blok, 1024))
            okna.append({"komponent": k, "start": s, "loss_suma": suma, "tokeny": a.blok, "bajty": int(tab[yn].sum())})
    per = {}
    for k in meta:
        w = [o for o in okna if o["komponent"] == k]
        if w:
            L, Tk, B = (sum(o[c] for o in w) for c in ("loss_suma", "tokeny", "bajty"))
            per[k] = {"n_okien": len(w), "loss": L / Tk, "bpb": L / (LN2 * B), "bajty_na_token": B / Tk}
    out = {"model": a.model, "config_step": m.cfg.get("step"), "n_okien": len(okna), "blok": a.blok,
           "per_komponent": per, "czas_s": round(time.time() - t0), "okna": okna}
    Path(a.wyjscie).parent.mkdir(parents=True, exist_ok=True)
    Path(a.wyjscie).write_text(json.dumps(out))
    print(json.dumps({k: v for k, v in out.items() if k != "okna"}, indent=1))


if __name__ == "__main__":
    main()
