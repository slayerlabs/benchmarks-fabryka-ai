"""ckpt.pt trenera Arka -> katalog modelu dla slayer_eval/slayer_model.py (model.safetensors, config.json, tokenizer.json).

python wygaszanie/konwertuj.py <ckpt.pt> <katalog_wzorca_1.06> <katalog_wyjścia> [--porownaj]

Klucze i kształty brane ze wzorca (model.safetensors 1.06); head.weight (tied z tok.weight) pomijany.
--porownaj: wypisuje max |różnicę| względem wag wzorca (dla ckpt_13848 ma wyjść 0).
"""

import hashlib
import json
import shutil
import sys
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file


def main():
    ckpt, wzor, wyj = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    ck = torch.load(ckpt, map_location="cpu", weights_only=True)
    sd = {}
    for k, v in ck["model"].items():
        for pref in ("_orig_mod.", "module."):
            k = k.replace(pref, "")
        sd[k] = v
    ref = load_file(str(wzor / "model.safetensors"))
    out = {}
    for k, v in ref.items():
        if k not in sd:
            raise SystemExit(f"STOP: brak {k} w checkpoincie; klucze ckpt: {sorted(sd)[:10]}")
        if tuple(sd[k].shape) != tuple(v.shape):
            raise SystemExit(f"STOP: kształt {k} {tuple(sd[k].shape)} != {tuple(v.shape)}")
        out[k] = sd[k].to(torch.float32).contiguous()
    nadmiar = sorted(set(sd) - set(ref) - {"head.weight"})
    if "head.weight" in sd:
        assert torch.equal(sd["head.weight"], sd["tok.weight"]), "head.weight != tok.weight (nie tied?)"
    wyj.mkdir(parents=True, exist_ok=True)
    save_file(out, str(wyj / "model.safetensors"), metadata={"format": "pt"})
    cfg = json.loads((wzor / "config.json").read_text())
    cfg.update({"step": int(ck["step"]), "zrodlo_ckpt": str(ckpt), "uwaga": "konwersja (wygaszanie)"})
    (wyj / "config.json").write_text(json.dumps(cfg, indent=1))
    shutil.copy(wzor / "tokenizer.json", wyj / "tokenizer.json")
    info = {"step": int(ck["step"]), "nadmiarowe_klucze": nadmiar,
            "sha256_safetensors": hashlib.sha256((wyj / "model.safetensors").read_bytes()).hexdigest()}
    if "--porownaj" in sys.argv:
        info["max_abs_roznica_vs_wzorzec"] = max((out[k] - ref[k]).abs().max().item() for k in ref)
    print(json.dumps(info))


if __name__ == "__main__":
    main()
