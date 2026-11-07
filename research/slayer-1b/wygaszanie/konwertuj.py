"""ckpt.pt trenera Arka -> katalog modelu dla common/slayer_model.py (model.safetensors, config.json, tokenizer.json).

python wygaszanie/konwertuj.py <ckpt.pt> <katalog_wzorca_1.06> <katalog_wyjścia> [--porownaj]

Klucze i kształty brane ze wzorca (model.safetensors 1.06); head.weight (tied z tok.weight) pomijany.
--porownaj: wypisuje max |różnicę| względem wag wzorca (dla ckpt_13848 ma wyjść 0).
STOP także wtedy, gdy `config` checkpointu ma klucz o innej wartości niż config.json wzorca (inna architektura:
config wzorca byłby zły). Przebieg centralny woła ten skrypt dla loadera `slayer-ckpt` (tools/przebieg_centralny.sh).
"""

import hashlib
import json
import shutil
import sys
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file


# data seed of the run: does not change the forward, a next version may train on other data
POZA_ARCHITEKTURA = {"data_seed"}


def rozne_od_wzorca(cfg_ckpt, cfg_wzorca):
    """Config keys of the checkpoint that change the model and differ from (or are missing in) the template config."""
    return {k: (v, cfg_wzorca.get(k, "<brak>")) for k, v in sorted((cfg_ckpt or {}).items())
            if k not in POZA_ARCHITEKTURA and cfg_wzorca.get(k, "<brak>") != v}


def sha256_pliku(sciezka):
    h = hashlib.sha256()
    with open(sciezka, "rb") as f:
        for kawalek in iter(lambda: f.read(1 << 24), b""):
            h.update(kawalek)
    return h.hexdigest()


def main():
    ckpt, wzor, wyj = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    # mmap: the 1.07 checkpoint is 8.9 GB (weights + optimizer state); only the weights are read
    ck = torch.load(ckpt, map_location="cpu", weights_only=True, mmap=True)
    cfg = json.loads((wzor / "config.json").read_text())
    rozne = rozne_od_wzorca(ck.get("config"), cfg)
    if rozne:
        raise SystemExit(f"STOP: config checkpointu różni się od wzorca (ckpt, wzorzec): {rozne}")
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
    if nadmiar:  # a module the template does not have: slayer_model.py would silently skip it
        raise SystemExit(f"STOP: klucze checkpointu spoza wzorca: {nadmiar}")
    if "head.weight" in sd:
        assert torch.equal(sd["head.weight"], sd["tok.weight"]), "head.weight != tok.weight (nie tied?)"
    wyj.mkdir(parents=True, exist_ok=True)
    save_file(out, str(wyj / "model.safetensors"), metadata={"format": "pt"})
    cfg.update({"step": int(ck["step"]), "ckpt_sha256": sha256_pliku(ckpt), "zrodlo_ckpt": str(ckpt),
                "uwaga": "konwersja ckpt trenera (konwertuj.py)"})
    (wyj / "config.json").write_text(json.dumps(cfg, indent=1))
    shutil.copy(wzor / "tokenizer.json", wyj / "tokenizer.json")
    info = {"step": int(ck["step"]), "nadmiarowe_klucze": nadmiar,
            "sha256_safetensors": hashlib.sha256((wyj / "model.safetensors").read_bytes()).hexdigest()}
    if "--porownaj" in sys.argv:
        info["max_abs_roznica_vs_wzorzec"] = max((out[k] - ref[k]).abs().max().item() for k in ref)
    print(json.dumps(info))


if __name__ == "__main__":
    main()
