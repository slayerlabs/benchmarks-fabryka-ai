"""Warunek startu z PROTOKOL.md: architektura i tokenizer checkpointu 1.09 równe 1.08, przed wynajmem karty.

    python sprawdz_architekture.py <wagi_40000.pt> <katalog modelu 1.08> <sha256 checkpointu> [--wyjscie plik.json]

Porównuje klucze i kształt każdego tensora checkpointu (bez prefiksów `_orig_mod.`/`module.`, bez `head.weight`
wiązanego z `tok.weight`) z `model.safetensors` 1.08, klucze architektury w `config` checkpointu z `config.json` 1.08
i sumę `tokenizer.json` 1.08 z prefiksem z karty. Kod 0: zgodne; kod 1: różnica (opis w JSON), STOP przed wynajmem.
"""
import hashlib
import json
import sys
from pathlib import Path

ARCHITEKTURA = ("vocab", "n_layer", "n_embd", "n_head", "block", "norm", "norm_eps", "pos", "rope_theta", "ffn",
                "ffn_mult", "value_residual", "qk_norm", "attn_bias", "logit_cap", "kv_heads", "loop", "xsa",
                "rope_dims", "imha_t", "tied_weights")
OCZEKIWANE = {"n_layer": 20, "n_embd": 2048, "vocab": 32768}
TOKENIZER_PREFIKS = "0640d3bd"
PREFIKSY = ("_orig_mod.", "module.")


def bez_prefiksu(k):
    for p in PREFIKSY:
        k = k.replace(p, "")
    return k


def porownaj(ksztalty_ckpt, ksztalty_wzorca, cfg_ckpt, cfg_wzorca, sha_tokenizera):
    """Czysta funkcja: {zgodne, ...różnice}. Kształty: {klucz: tuple}; konfiguracje: dict albo None."""
    ck = {bez_prefiksu(k): tuple(v) for k, v in ksztalty_ckpt.items()}
    wz = {k: tuple(v) for k, v in ksztalty_wzorca.items()}
    brak = sorted(set(wz) - set(ck))
    nadmiar = sorted(set(ck) - set(wz) - {"head.weight"})
    rozne = {k: (ck[k], wz[k]) for k in sorted(set(ck) & set(wz)) if ck[k] != wz[k]}
    if "head.weight" in ck and ck["head.weight"] != wz.get("tok.weight"):
        rozne["head.weight"] = (ck["head.weight"], wz.get("tok.weight"))
    cfg_ckpt = cfg_ckpt or {}
    arch = {k: (cfg_ckpt.get(k, "<brak>"), cfg_wzorca.get(k, "<brak>")) for k in ARCHITEKTURA
            if (k in cfg_ckpt or k in cfg_wzorca) and cfg_ckpt.get(k, "<brak>") != cfg_wzorca.get(k, "<brak>")
            and not (k == "tied_weights" and k not in cfg_ckpt)}
    inne = {k: (cfg_ckpt.get(k, "<brak>"), cfg_wzorca.get(k, "<brak>")) for k in sorted(set(cfg_ckpt) | set(cfg_wzorca))
            if k not in ARCHITEKTURA and cfg_ckpt.get(k, "<brak>") != cfg_wzorca.get(k, "<brak>")}
    oczekiwane = {k: (cfg_ckpt.get(k), v) for k, v in OCZEKIWANE.items() if cfg_ckpt.get(k) != v}
    tok_ok = sha_tokenizera.startswith(TOKENIZER_PREFIKS)
    zgodne = not (brak or nadmiar or rozne or arch or oczekiwane or not cfg_ckpt) and tok_ok
    return {"zgodne": zgodne, "tensory_ckpt": len(ck), "tensory_wzorca": len(wz), "brak_w_ckpt": brak,
            "nadmiar_w_ckpt": nadmiar, "rozne_ksztalty": {k: [list(a), list(b) if b else None] for k, (a, b) in rozne.items()},
            "config_architektura_rozne": arch, "config_oczekiwane_rozne": oczekiwane, "config_bez_architektury_rozne": inne,
            "config_w_ckpt": bool(cfg_ckpt), "tokenizer_sha256": sha_tokenizera, "tokenizer_zgodny": tok_ok}


def sha256_pliku(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for kawalek in iter(lambda: f.read(1 << 24), b""):
            h.update(kawalek)
    return h.hexdigest()


def main():
    import torch
    from safetensors import safe_open
    ckpt, wzor, sha_oczekiwana = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3].lower()
    sha = sha256_pliku(ckpt)
    if sha != sha_oczekiwana:
        raise SystemExit(f"STOP: sha256 {ckpt.name} = {sha}, oczekiwana {sha_oczekiwana}")
    ck = torch.load(ckpt, map_location="cpu", weights_only=True, mmap=True)
    with safe_open(str(wzor / "model.safetensors"), "pt") as f:
        ksz_wz = {k: tuple(f.get_slice(k).get_shape()) for k in f.keys()}
    ksz_ck = {k: tuple(v.shape) for k, v in ck["model"].items()}
    cfg_wz = json.loads((wzor / "config.json").read_text(encoding="utf-8"))
    wynik = porownaj(ksz_ck, ksz_wz, ck.get("config"), cfg_wz, sha256_pliku(wzor / "tokenizer.json"))
    wynik.update({"ckpt": ckpt.name, "ckpt_sha256": sha, "krok": int(ck.get("step", -1)),
                  "klucze_ckpt_najwyzszego_poziomu": sorted(ck), "parametry_ckpt_bez_head": sum(
                      v.numel() for k, v in ck["model"].items() if bez_prefiksu(k) != "head.weight"),
                  "dtype_ckpt": sorted({str(v.dtype) for v in ck["model"].values()}),
                  "config_ckpt": ck.get("config")})
    tekst = json.dumps(wynik, ensure_ascii=False, indent=1, default=str)
    if "--wyjscie" in sys.argv:
        Path(sys.argv[sys.argv.index("--wyjscie") + 1]).write_text(tekst + "\n", encoding="utf-8")
    print(tekst)
    return 0 if wynik["zgodne"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
