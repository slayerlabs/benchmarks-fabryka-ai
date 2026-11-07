"""slayer-1b/wygaszanie/konwertuj.py on a tiny stand-in checkpoint and template (no network, no real weights):
the weights and the step land in the output, a checkpoint with another architecture in its config stops."""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file

KORZEN = Path(__file__).resolve().parent.parent
SKRYPT = KORZEN / "slayer-1b" / "wygaszanie" / "konwertuj.py"
CFG = {"n_layer": 1, "n_embd": 4, "n_head": 2, "vocab": 8, "qk_norm": True, "data_seed": 1}


def przygotuj(cfg_ckpt, extra=None):
    d = Path(tempfile.mkdtemp())
    wzor = d / "wzorzec"
    wzor.mkdir()
    save_file({"tok.weight": torch.zeros(8, 4), "blocks.0.w": torch.zeros(4, 4)}, str(wzor / "model.safetensors"))
    (wzor / "config.json").write_text(json.dumps({**CFG, "step": 100}))
    (wzor / "tokenizer.json").write_text("{}")
    tok = torch.arange(32, dtype=torch.float32).reshape(8, 4)
    model = {"_orig_mod.tok.weight": tok, "_orig_mod.head.weight": tok.clone(), "_orig_mod.blocks.0.w": torch.eye(4)}
    model.update(extra or {})
    torch.save({"model": model, "opt": {}, "step": 200, "config": cfg_ckpt}, d / "ckpt_200.pt")
    return d


def konwertuj(d):
    return subprocess.run([sys.executable, str(SKRYPT), str(d / "ckpt_200.pt"), str(d / "wzorzec"), str(d / "wyj")],
                          capture_output=True, text=True)


def test_same_architecture_converts_weights_step_and_checkpoint_sha():
    d = przygotuj({**CFG, "data_seed": 2})  # another data seed is not another architecture
    wynik = konwertuj(d)
    assert wynik.returncode == 0, wynik.stderr
    w = load_file(str(d / "wyj" / "model.safetensors"))
    assert set(w) == {"tok.weight", "blocks.0.w"} and torch.equal(w["blocks.0.w"], torch.eye(4))
    cfg = json.loads((d / "wyj" / "config.json").read_text())
    assert cfg["step"] == 200 and cfg["n_layer"] == 1
    assert cfg["ckpt_sha256"] == hashlib.sha256((d / "ckpt_200.pt").read_bytes()).hexdigest()
    assert cfg["zrodlo_ckpt"].endswith("/ckpt_200.pt")  # przebieg_centralny.sh pobierz_wagi reads this
    assert (d / "wyj" / "tokenizer.json").read_text() == "{}"


def test_other_architecture_in_checkpoint_config_stops_without_output():
    d = przygotuj({**CFG, "n_layer": 2})
    wynik = konwertuj(d)
    assert wynik.returncode != 0 and "n_layer" in wynik.stderr
    assert not (d / "wyj").exists()


def test_checkpoint_module_missing_in_template_stops():
    d = przygotuj(CFG, extra={"_orig_mod.blocks.0.nowy": torch.zeros(2)})
    wynik = konwertuj(d)
    assert wynik.returncode != 0 and "blocks.0.nowy" in wynik.stderr


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
