"""Equivalence: batched Slayer greedy generation == batch size 1.

CPU-only, tiny random model. Skipped when torch/safetensors/tokenizers unavailable.
On VM: also compare batch 1 vs batch N on 20 real prompts and report % identical
outputs (bf16 batching can differ slightly — report, don't hide).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("safetensors")
pytest.importorskip("tokenizers")

from safetensors.torch import save_file  # noqa: E402
from tokenizers import Tokenizer  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "common"
if str(COMMON) not in sys.path:
    sys.path.insert(0, str(COMMON))

from slayer_model import Slayer  # noqa: E402
from slayer_batch import generate_batch  # noqa: E402


def _tiny_model(tmp_path: Path, vocab=16384, n_layer=2, n_head=2, n_embd=32, block=64):
    hd = n_embd // n_head
    cfg = {
        "n_layer": n_layer, "n_head": n_head, "n_embd": n_embd, "block": block,
        "vocab": vocab, "norm_eps": 1e-5, "rope_theta": 500000.0, "value_residual": True,
    }
    (tmp_path / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    tok_src = ROOT / "slayer-1b" / "tokenizer" / "tokenizer.json"
    if not tok_src.is_file():
        pytest.skip(f"missing {tok_src}")
    shutil.copy(tok_src, tmp_path / "tokenizer.json")
    torch.manual_seed(0)
    w = {
        "tok.weight": torch.randn(vocab, n_embd, dtype=torch.float32) * 0.02,
        "lnf.weight": torch.ones(n_embd, dtype=torch.float32),
    }
    for i in range(n_layer):
        p = f"blocks.{i}."
        w[p + "ln1.weight"] = torch.ones(n_embd)
        w[p + "ln2.weight"] = torch.ones(n_embd)
        w[p + "qkv.weight"] = torch.randn(3 * n_embd, n_embd) * 0.02
        w[p + "proj.weight"] = torch.randn(n_embd, n_embd) * 0.02
        w[p + "q_norm.weight"] = torch.ones(hd)
        w[p + "k_norm.weight"] = torch.ones(hd)
        w[p + "vr_lambda"] = torch.tensor([0.5])
        w[p + "mlp.gate.weight"] = torch.randn(n_embd * 2, n_embd) * 0.02
        w[p + "mlp.up.weight"] = torch.randn(n_embd * 2, n_embd) * 0.02
        w[p + "mlp.down.weight"] = torch.randn(n_embd, n_embd * 2) * 0.02
    save_file(w, str(tmp_path / "model.safetensors"))
    return Slayer(str(tmp_path), device="cpu", dtype=torch.float32)


def _sequential(model, prompt_ids, max_total):
    """Reference: one leading BOS per request, greedy, stop at EOS or max_total."""
    device = model.device
    cache = []
    ids = torch.tensor([[model.bos] + list(prompt_ids)], dtype=torch.long, device=device)
    logits = model.krok(ids, cache)[0]
    prompt_len = 1 + len(prompt_ids)
    out = []
    for _ in range(max(0, max_total - prompt_len)):
        nxt = int(logits.argmax().item())
        out.append(nxt)
        if nxt == model.bos:
            break
        if prompt_len + len(out) >= max_total:
            break
        logits = model.krok(torch.tensor([[nxt]], dtype=torch.long, device=device), cache)[0]
    return out


def test_batched_equals_batch1_cpu(tmp_path):
    m = _tiny_model(tmp_path, block=64)
    prompts = [
        m.encode("Write a function that adds two numbers."),
        m.encode("Solve this problem."),
        m.encode("def f(x):\n    return x*x\n# explain"),
        m.encode("short"),
        m.encode("A longer prompt to exercise left padding and different lengths in the same batch."),
    ]
    max_total = 64
    seq = [_sequential(m, p, max_total) for p in prompts]
    b1 = generate_batch(m, prompts, max_total=max_total, stop_id=m.bos)
    bN = generate_batch(m, prompts, max_total=max_total, stop_id=m.bos)
    b2 = generate_batch(m, prompts[:2], max_total=max_total, stop_id=m.bos) + \
         generate_batch(m, prompts[2:], max_total=max_total, stop_id=m.bos)
    assert seq == b1
    assert seq == bN
    assert seq == b2
    for p, out in zip(prompts, bN):
        assert 1 + len(p) + len(out) <= max_total or (out and out[-1] == m.bos)
