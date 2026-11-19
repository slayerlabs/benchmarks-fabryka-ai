"""lm_eval CLI with batched greedy generation for Slayer; otherwise the stock `lm_eval` CLI with `slayer_lm`.

`research/common/slayer_lm.py` generates each row of a batch on its own, one token per forward. A 1B model on
one token is bound by kernel launches (about 29 forwards per second here whatever the batch), so a prompt with
1,280 output tokens takes about 45 s and `--batch_size` does not help. This file replaces
`_SlayerModule.generate` with a decode that runs one forward per step for the whole batch:

- left padding stays in the batch and is masked out of attention,
- each row gets its own RoPE positions (counted from its first real token),
- K and V go into a preallocated cache.

The math per row is that of `Slayer.ukryte` (same weights, RMSNorm, qk_norm, RoPE, value residual, SDPA scale);
`check_batched.py` compares both on IFEval prompts. Greedy decoding only, as in `slayer_lm`.

Usage: python lm_eval_slayer.py <lm_eval arguments> --model slayer ...
"""

import sys
from pathlib import Path

import torch
import torch.nn.functional as F

COMMON_DIR = Path(__file__).resolve().parents[2] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

import slayer_lm  # noqa: E402  registers the `slayer` model (the .pth hook runs only for the lm_eval script)
from slayer_model import rmsnorm  # noqa: E402


def _rope(x, cos, sin):
    """Interleaved (gptj) RoPE with per-row angles: x [B, H, T, hd], cos/sin [B, 1, T, hd/2]."""
    xf = x.float()
    x1, x2 = xf[..., 0::2], xf[..., 1::2]
    return torch.stack([x1 * cos - x2 * sin, x1 * sin + x2 * cos], -1).flatten(-2).to(x.dtype)


@torch.no_grad()
def batched_forward(m, ids, pos, kcache, vcache, start, key_ok):
    """Hidden state after lnf for `ids` [B, T] written at cache slots start..start+T-1.

    pos [B, T]: RoPE positions of the new tokens. key_ok [B, start+T]: which cache slots hold real tokens.
    kcache/vcache: per layer [B, H, S, hd] buffers, filled in place.
    """
    w = m.w
    x = w["tok.weight"][ids]
    B, T, _ = x.shape
    end = start + T
    cos, sin = m.cos[pos][:, None], m.sin[pos][:, None]
    # Causal within the new tokens, and only real keys. A pad query may see itself, so no row of the mask is empty
    # (SDPA gives NaN there); pad outputs are never read.
    q_slot = torch.arange(start, end, device=x.device)
    k_slot = torch.arange(end, device=x.device)
    mask = (k_slot[None, :] <= q_slot[:, None])[None] & key_ok[:, None, :]
    mask = mask | (k_slot[None, None, :] == q_slot[None, :, None])
    mask = mask[:, None]
    v0 = None
    for i in range(m.n_layer):
        p = f"blocks.{i}."
        h = rmsnorm(x, w[p + "ln1.weight"], m.eps)
        q, k, v = (h @ w[p + "qkv.weight"].T).split(m.d, -1)
        q = q.view(B, T, m.n_head, m.hd).transpose(1, 2)
        k = k.view(B, T, m.n_head, m.hd).transpose(1, 2)
        v = v.view(B, T, m.n_head, m.hd).transpose(1, 2)
        if m.cfg.get("value_residual"):
            if v0 is None:
                v0 = v
            else:
                v = v + w[p + "vr_lambda"] * v0
        q = _rope(rmsnorm(q, w[p + "q_norm.weight"], m.eps), cos, sin)
        k = _rope(rmsnorm(k, w[p + "k_norm.weight"], m.eps), cos, sin)
        kcache[i][:, :, start:end] = k
        vcache[i][:, :, start:end] = v
        a = F.scaled_dot_product_attention(q, kcache[i][:, :, :end], vcache[i][:, :, :end], attn_mask=mask,
                                           scale=m.skala)
        x = x + a.transpose(1, 2).reshape(B, T, m.d) @ w[p + "proj.weight"].T
        h = rmsnorm(x, w[p + "ln2.weight"], m.eps)
        x = x + (F.silu(h @ w[p + "mlp.gate.weight"].T) * (h @ w[p + "mlp.up.weight"].T)) @ w[p + "mlp.down.weight"].T
    return rmsnorm(x, w["lnf.weight"], m.eps)


@torch.no_grad()
def generate(self, input_ids, attention_mask=None, max_length=None, stopping_criteria=None, **kwargs):
    """Same contract as `_SlayerModule.generate` in slayer_lm (greedy, end of text, lm-eval stopping criterion)."""
    if kwargs.get("do_sample"):
        raise NotImplementedError("SlayerLM: generate_until supports greedy only (do_sample=False).")
    m = self.slayer
    if m.rope != "gptj" or m.vr != "add" or m.qk_po_rope:
        raise NotImplementedError("lm_eval_slayer: only the default Slayer variant (gptj RoPE, vr add)")
    device = m.device
    output = input_ids.to(device)
    B, L = output.shape
    limit = 0 if max_length is None else int(max_length) - L
    if attention_mask is None:
        key_ok = torch.ones(B, L, dtype=torch.bool, device=device)
    else:
        key_ok = attention_mask.to(device, dtype=torch.bool)
    ids = output
    empty = ~key_ok.any(1)
    if bool(empty.any()):  # empty context: start from BOS, as slayer_lm does
        ids = ids.clone()
        ids[empty, -1] = m.bos
        key_ok = key_ok.clone()
        key_ok[empty, -1] = True
    lengths = key_ok.sum(1)
    pos = (key_ok.long().cumsum(1) - 1).clamp(min=0)
    # The last new token is never fed back, so the forward passes use lengths + limit - 1 positions (as slayer_lm).
    if int(lengths.max()) + limit - 1 > m.blok:
        raise ValueError(f"Slayer: {int(lengths.max()) + limit - 1} positions, but block = {m.blok}")
    size = L + max(limit, 0)
    shape = (B, m.n_head, size, m.hd)
    kcache = [torch.empty(shape, dtype=m.dtype, device=device) for _ in range(m.n_layer)]
    vcache = [torch.empty(shape, dtype=m.dtype, device=device) for _ in range(m.n_layer)]
    key_ok = torch.cat([key_ok, key_ok.new_ones(B, max(limit, 0))], 1)
    finished = output.new_zeros(B, dtype=torch.bool)
    pending, start, step_pos = ids, 0, pos
    for _ in range(limit):
        end = start + pending.shape[1]
        h = batched_forward(m, pending, step_pos, kcache, vcache, start, key_ok[:, :end])
        last_logits = m.glowa(h[:, -1])
        next_tokens = last_logits.argmax(dim=-1).masked_fill(finished, m.bos)
        finished = finished | (next_tokens == m.bos)
        output = torch.cat([output, next_tokens[:, None]], dim=1)
        if bool(finished.all()):
            break
        if stopping_criteria is not None:
            stop = stopping_criteria(output, last_logits)
            if bool(stop.all() if hasattr(stop, "all") else all(stop)):
                break
        pending, start = next_tokens[:, None], end
        step_pos = (lengths + (end - L))[:, None]
    return output.to(input_ids.device)


_per_row_generate = slayer_lm._SlayerModule.generate
slayer_lm._SlayerModule.generate = generate

if __name__ == "__main__":
    from lm_eval.__main__ import cli_evaluate

    cli_evaluate()
