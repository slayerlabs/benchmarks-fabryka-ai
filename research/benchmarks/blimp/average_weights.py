"""Uniform weight average of the last K trainer checkpoints (results/CHECKPOINTS_THRESHOLDS.md, question 2).

python benchmarks/blimp/average_weights.py --wzor <slayer-1.06 dir> --wyjscie <dir> --zapisz 3,5,10 ckpt_13848.pt ckpt_13800.pt ...

Checkpoints are read in the given order (newest first) one at a time (torch.load mmap), their model
weights summed in float64; after the K-th file the mean is written to <wyjscie>/avg<K> (model.safetensors
float32, config.json, tokenizer.json of the template). With --usun each .pt is deleted after reading.
Keys and shapes come from the template (as slayer-1b/wygaszanie/konwertuj.py); head.weight (tied) is checked and skipped.
"""

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path


def klucze_modelu(sd):
    """Trainer state dict -> plain keys (strip torch.compile / DDP prefixes)."""
    out = {}
    for k, v in sd.items():
        for pref in ("_orig_mod.", "module."):
            k = k.replace(pref, "")
        out[k] = v
    return out


class Srednia:
    """Running float64 sum of model weights restricted to the template keys; mean() -> float32 dict."""

    def __init__(self, wzor):
        import torch
        self.ksztalty = {k: tuple(v.shape) for k, v in wzor.items()}
        self.suma = {k: torch.zeros(s, dtype=torch.float64) for k, s in self.ksztalty.items()}
        self.n = 0

    def dodaj(self, sd):
        import torch
        sd = klucze_modelu(sd)
        for k, s in self.ksztalty.items():
            if k not in sd:
                raise ValueError(f"missing key {k}")
            if tuple(sd[k].shape) != s:
                raise ValueError(f"shape {k} {tuple(sd[k].shape)} != {s}")
        if "head.weight" in sd and not torch.equal(sd["head.weight"], sd["tok.weight"]):
            raise ValueError("head.weight != tok.weight (not tied)")
        for k in self.ksztalty:
            self.suma[k] += sd[k].to(torch.float64)
        self.n += 1

    def srednia(self):
        import torch
        return {k: (v / self.n).to(torch.float32).contiguous() for k, v in self.suma.items()}


def main(argv=None):
    import torch
    from safetensors.torch import load_file, save_file
    p = argparse.ArgumentParser()
    p.add_argument("--wzor", required=True)
    p.add_argument("--wyjscie", required=True)
    p.add_argument("--zapisz", required=True, help="K values, e.g. 3,5,10")
    p.add_argument("--usun", action="store_true")
    p.add_argument("ckpt", nargs="+")
    a = p.parse_args(argv)
    wzor = Path(a.wzor)
    ks = sorted(int(k) for k in a.zapisz.split(","))
    if ks[-1] > len(a.ckpt):
        raise SystemExit(f"K = {ks[-1]} needs {ks[-1]} checkpoints, got {len(a.ckpt)}")
    acc = Srednia(load_file(str(wzor / "model.safetensors")))
    kroki, log = [], []
    for plik in a.ckpt[:ks[-1]]:
        t0 = time.time()
        ck = torch.load(plik, map_location="cpu", weights_only=True, mmap=True)
        acc.dodaj(ck["model"])
        kroki.append(int(ck["step"]))
        del ck
        if a.usun:
            Path(plik).unlink()
        log.append({"plik": str(plik), "krok": kroki[-1], "s": round(time.time() - t0, 1)})
        if acc.n in ks:
            wyj = Path(a.wyjscie) / f"avg{acc.n}"
            wyj.mkdir(parents=True, exist_ok=True)
            save_file(acc.srednia(), str(wyj / "model.safetensors"), metadata={"format": "pt"})
            cfg = json.loads((wzor / "config.json").read_text())
            cfg.update({"step": kroki[0], "srednia_krokow": list(kroki), "uwaga": "uniform weight average (average_weights.py)"})
            (wyj / "config.json").write_text(json.dumps(cfg, indent=1))
            shutil.copy(wzor / "tokenizer.json", wyj / "tokenizer.json")
            sha = hashlib.sha256((wyj / "model.safetensors").read_bytes()).hexdigest()
            print(json.dumps({"model": f"avg{acc.n}", "kroki": kroki, "sha256_safetensors": sha, "czytanie": log}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
