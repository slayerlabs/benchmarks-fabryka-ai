"""Batched greedy generation for Slayer 1B.

Reuses the batched forward from research/api-benchmarks/ifeval/lm_eval_slayer.py:
left padding, per-row RoPE positions, preallocated KV cache, per-row stop at EOS
or at max_total tokens. Greedy only, default Slayer variant (gptj RoPE, vr add).
"""

from __future__ import annotations

import torch
import torch.nn.functional as F

from slayer_model import rmsnorm


def _rope(x, cos, sin):
    """Interleaved (gptj) RoPE with per-row angles: x [B,H,T,hd], cos/sin [B,1,T,hd/2]."""
    xf = x.float()
    x1, x2 = xf[..., 0::2], xf[..., 1::2]
    return torch.stack([x1 * cos - x2 * sin, x1 * sin + x2 * cos], -1).flatten(-2).to(x.dtype)


@torch.no_grad()
def batched_forward(m, ids, pos, kcache, vcache, start, key_ok):
    """Hidden state after lnf for `ids` [B,T] written at cache slots start..start+T-1.

    pos [B,T]: RoPE positions of new tokens. key_ok [B,start+T]: real cache slots.
    kcache/vcache: per layer [B,H,S,hd], filled in place.
    """
    w = m.w
    x = w["tok.weight"][ids]
    B, T, _ = x.shape
    end = start + T
    cos, sin = m.cos[pos][:, None], m.sin[pos][:, None]
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
        a = F.scaled_dot_product_attention(q, kcache[i][:, :, :end], vcache[i][:, :, :end],
                                           attn_mask=mask, scale=m.skala)
        x = x + a.transpose(1, 2).reshape(B, T, m.d) @ w[p + "proj.weight"].T
        h = rmsnorm(x, w[p + "ln2.weight"], m.eps)
        x = x + (F.silu(h @ w[p + "mlp.gate.weight"].T) * (h @ w[p + "mlp.up.weight"].T)) @ w[p + "mlp.down.weight"].T
    return rmsnorm(x, w["lnf.weight"], m.eps)


@torch.no_grad()
def generate_batch(model, prompt_ids_list: list[list[int]], max_total: int = 4096,
                   stop_id: int | None = None) -> list[list[int]]:
    """Greedy batched generation. Returns generated token ids per row.

    BOS rule (matches research/api-benchmarks/ifeval/lm_eval_slayer.py and
    research/common/slayer_lm.py): every request starts with exactly one leading
    BOS token. Each row stops at `stop_id` (included, default model.bos) or when
    total real tokens (BOS + prompt + generated) reach `max_total`.
    """
    m = model
    if m.rope != "gptj" or m.vr != "add" or m.qk_po_rope:
        raise NotImplementedError("slayer_batch: only default Slayer variant (gptj RoPE, vr add)")
    stop = m.bos if stop_id is None else stop_id
    device = m.device
    rows = [list(r) for r in prompt_ids_list]
    B = len(rows)
    if B == 0:
        return []
    width = max((len(r) for r in rows), default=0)
    # BOS first, left pad zeros, then prompt - same layout as SlayerLM.tok_batch_encode.
    ids = torch.tensor([[m.bos] + [0] * (width - len(r)) + r for r in rows],
                       dtype=torch.long, device=device)
    key_ok = torch.tensor([[1] + [0] * (width - len(r)) + [1] * len(r) for r in rows],
                          dtype=torch.bool, device=device)
    lengths = key_ok.sum(1)  # real prompt length per row, including BOS
    max_new = int((max_total - lengths).clamp(min=0).max().item())
    if max_new == 0:
        return [[] for _ in range(B)]
    if max_total > m.blok:
        raise ValueError(f"Slayer: max_total {max_total} exceeds block = {m.blok} (highest position {max_total - 1})")
    size = width + max_new
    shape = (B, m.n_head, size, m.hd)
    kcache = [torch.empty(shape, dtype=m.dtype, device=device) for _ in range(m.n_layer)]
    vcache = [torch.empty(shape, dtype=m.dtype, device=device) for _ in range(m.n_layer)]
    key_ok_full = torch.cat([key_ok, key_ok.new_ones(B, max_new)], 1)
    pos = (key_ok.long().cumsum(1) - 1).clamp(min=0)
    finished = torch.zeros(B, dtype=torch.bool, device=device)
    # rows already at limit
    finished = finished | (lengths >= max_total)
    out: list[list[int]] = [[] for _ in range(B)]
    pending, start, step_pos = ids, 0, pos
    for _ in range(max_new):
        if bool(finished.all()):
            break
        end = start + pending.shape[1]
        h = batched_forward(m, pending, step_pos, kcache, vcache, start, key_ok_full[:, :end])
        next_tokens = m.glowa(h[:, -1]).argmax(dim=-1)
        next_tokens = next_tokens.masked_fill(finished, stop)
        for i in range(B):
            if not bool(finished[i]):
                out[i].append(int(next_tokens[i].item()))
        finished = finished | (next_tokens == stop)
        generated = end - width  # tokens generated so far including this one
        finished = finished | (lengths + generated >= max_total)
        if bool(finished.all()):
            break
        pending, start = next_tokens[:, None], end
        step_pos = (lengths + generated - 1)[:, None].clamp(max=max_total - 1)
    return out
