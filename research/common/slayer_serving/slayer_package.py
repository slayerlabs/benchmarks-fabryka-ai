"""Builds the Slayer 1B step-60000 package that slayer_kv_lm.py loads, from public pinned files only.

Usage: python slayer_package.py --out <dir>

Downloads (Hugging Face, by revision, no token):
  - SlayerLab/Slayer1B-1.09-checkpoints @ dc3b6a9b...: wagi_60000.pt, the native training checkpoint (fp32 weights + config);
  - SlayerLab/Slayer1B-1.09 @ 58d8f359...: train_gpt_ref_r24_2.py, the trainer that defines the GPT class;
  - SlayerLab/Slayer1B-1.08 @ 5f854a0c...: tokenizer.json.
Every file is checked against its sha256 below. The package holds config.json (the checkpoint's config plus step and
checkpoint digest), tokenizer.json, the trainer and load_slayer.py, which loads the checkpoint strictly into the
trainer's GPT class and ties the output head to the token embedding, as the public Slayer1B-1.09 load_slayer.py does.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys

from huggingface_hub import hf_hub_download

FILES = {
    "wagi_60000.pt": ("SlayerLab/Slayer1B-1.09-checkpoints", "dc3b6a9b0f87305da7ceca39ca27a79fa60b34cd",
                      "a46e6cfaa37e80a2b6e45b1161099d586f09a502d8bdbf45303709d946e2b58a"),
    "train_gpt_ref_r24_2.py": ("SlayerLab/Slayer1B-1.09", "58d8f359c1fdd887f1b7344ec52c5511c111f790",
                               "46f83b51fcec18ffc3273d80fb9eab29e182c52d8667800dab27b80f7ff18afc"),
    "tokenizer.json": ("SlayerLab/Slayer1B-1.08", "5f854a0cc7160594d54d1788d37a44e8ebabe16c",
                       "0640d3bd3674d7a6e59c540d945a2ad275a12e1bcaeb6007c37a90751f9815dd"),
}

LOADER = '''"""Loads wagi_60000.pt into the GPT class of train_gpt_ref_r24_2.py (float32, eval mode)."""
import importlib.util
import os
from types import SimpleNamespace

import torch


def load(path, device="cpu"):
    spec = importlib.util.spec_from_file_location("slayer_trainer", os.path.join(path, "train_gpt_ref_r24_2.py"))
    trainer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trainer)  # the trainer guards its training entry point with __main__
    state = torch.load(os.path.join(path, "wagi_60000.pt"), map_location="cpu", weights_only=True)
    cfg = SimpleNamespace(**state["config"])
    model = trainer.GPT(cfg.vocab, cfg.n_layer, cfg.n_embd, cfg.n_head, cfg.block, cfg)
    model.load_state_dict(state["model"], strict=True)
    model.head.weight = model.tok.weight
    return model.to(device).float().eval()
'''


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f"slayer_package.py: {a.out} exists")
    os.makedirs(a.out)
    for name, (repo, revision, digest) in FILES.items():
        src = hf_hub_download(repo, name, revision=revision)
        if sha256(src) != digest:
            sys.exit(f"slayer_package.py: {repo}/{name} @ {revision[:8]} is not {digest[:12]}")
        shutil.copyfile(src, os.path.join(a.out, name))
    import torch
    state = torch.load(os.path.join(a.out, "wagi_60000.pt"), map_location="cpu", weights_only=True)
    cfg = dict(state["config"])
    cfg.update({"step": int(state["step"]), "ckpt_sha256": FILES["wagi_60000.pt"][2],
                "tokenizer_sha256": FILES["tokenizer.json"][2], "trainer": "train_gpt_ref_r24_2.py",
                "trainer_sha256": FILES["train_gpt_ref_r24_2.py"][2]})
    if cfg["step"] != 60000:
        sys.exit(f"slayer_package.py: checkpoint step {cfg['step']}, expected 60000")
    with open(os.path.join(a.out, "config.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(cfg, f, indent=1, sort_keys=True)
    with open(os.path.join(a.out, "load_slayer.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write(LOADER)
    print(f"slayer_package.py: {a.out} (step {cfg['step']}, vocab {cfg['vocab']}, block {cfg['block']})")


if __name__ == "__main__":
    main()
