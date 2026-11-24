"""slayer_batch.py - batched Slayer generation with a KV cache and sampling, on top of SlayerLM (slayer_kv_lm.py, unchanged).
The same block arithmetic as SlayerLM._step (qkv, qk-norm, interleaved RoPE with a position offset, value residual, MHA,
fp32, TF32 off), but B rows at once:
- prefill of each row on its own through SlayerLM._step (identical to the single-row path), K/V copied to the row's slot;
- batched decoding: one token per row, positions per row, attention with a mask valid only up to the row's position;
- sampling per row: T == 0 -> argmax; T > 0 -> softmax(logits / T), nucleus top_p, torch.multinomial with the row's
  own torch.Generator(cuda) seeded with the request's seed (same seed + same logits sequence = same text);
- end of a row: token 0 (eos) | a string from until | limit | block - the same conditions as SlayerLM._gen_kv.
The batch is static (collected by the server); a finished row stops counting (mask of active rows).
torch is imported lazily when BatchGenerator is created (Job needs no torch: the server's HTTP layer can be tested
without the model)."""
torch = F = None
START_ID = 0
MAX_POS = 40000  # KV positions per batch: about 13 GB fp32 on a 24 GB card with 4.3 GB of weights


class Job:
    __slots__ = ("pref", "limit", "until", "temperature", "top_p", "seed", "gen", "reason")

    def __init__(self, pref, limit, until, temperature=0.0, top_p=1.0, seed=None):
        self.pref, self.limit, self.until = list(pref), int(limit), list(until)
        self.temperature, self.top_p, self.seed = float(temperature), float(top_p), seed
        self.gen, self.reason = [], None


class BatchGenerator:
    def __init__(self, lm):
        global torch, F
        import torch
        import torch.nn.functional as F
        self.lm, self.m, self.dev = lm, lm.model, lm.dev
        b0 = self.m.blocks[0]
        self.hd = b0.d // b0.nh
        self.freq = 1.0 / (lm.theta ** (torch.arange(0, self.hd, 2, device=self.dev, dtype=torch.float32) / self.hd))

    def _rope_rows(self, x, pos):
        """x [B, h, 1, hd], pos [B] (long) - the trainer's interleaved apply_rope, the same arithmetic as SlayerLM._rope for T=1."""
        ang = pos.to(torch.float32)[:, None] * self.freq[None, :]          # [B, hd/2]
        cos, sin = ang.cos().to(x.dtype)[:, None, None, :], ang.sin().to(x.dtype)[:, None, None, :]
        even, odd = x[..., ::2], x[..., 1::2]
        return torch.stack((even * cos - odd * sin, even * sin + odd * cos), dim=-1).flatten(-2)

    def _sample(self, logits, z, gen):
        if z.temperature <= 0:
            return int(logits.argmax())
        p = F.softmax(logits / z.temperature, dim=-1)
        if z.top_p < 1.0:
            ps, idx = torch.sort(p, descending=True)
            keep = (ps.cumsum(-1) - ps) < z.top_p          # always at least the first
            ps = torch.where(keep, ps, torch.zeros_like(ps))
            ps = ps / ps.sum()
            return int(idx[torch.multinomial(ps, 1, generator=gen)])
        return int(torch.multinomial(p, 1, generator=gen))

    def _stop_reason(self, z, length):
        if z.until and any(u and u in self.lm.tok.decode(z.gen) for u in z.until):
            return "until"
        if len(z.gen) >= z.limit:
            return "max_gen_toks"
        if length >= self.lm.block:
            return "block"
        return None

    def generate(self, jobs):
        """Splits the jobs into batches of at most MAX_POS KV positions in total (about 0.33 MB per position in fp32: 20
        blocks x K,V x 16 x 128), sorted by length (less padding); results in the order of the jobs."""
        blk, results = self.lm.block, [None] * len(jobs)
        length = lambda i: min(blk, len(jobs[i].pref) + jobs[i].limit)
        order = sorted(range(len(jobs)), key=length)
        with torch.inference_mode():
            i = 0
            while i < len(order):
                j = i + 1
                while j < len(order) and (j + 1 - i) * length(order[j]) <= MAX_POS:
                    j += 1
                for k, o in zip(order[i:j], self._generate([jobs[k] for k in order[i:j]])):
                    results[k] = o
                i = j
        return results

    def _single(self, z):
        """Batch of 1: exactly the SlayerLM._gen_kv path - _step on the row's own cache - with _sample for sampling."""
        gen = None
        if z.temperature > 0:
            gen = torch.Generator(device=self.dev)
            gen.manual_seed(int(z.seed) if z.seed is not None else 0)
        c = self.lm._new_cache(min(self.lm.block, len(z.pref) + z.limit))
        log = self.lm._step(torch.tensor([z.pref], dtype=torch.long, device=self.dev), c)
        self.lm.forward_tokens += len(z.pref)
        length = len(z.pref)
        while True:
            t = self._sample(log[-1], z, gen)
            if t == START_ID:
                z.reason = "eos"
                break
            z.gen.append(t)
            length += 1
            z.reason = self._stop_reason(z, length)
            if z.reason:
                break
            log = self.lm._step(torch.tensor([[t]], dtype=torch.long, device=self.dev), c)
            self.lm.forward_tokens += 1
        text = self.lm.tok.decode(z.gen)
        for u in z.until:
            if u and u in text:
                text = text.split(u)[0]
        return text, len(z.gen), z.reason

    def _generate(self, jobs):
        """Returns a list of (text, generated, reason) in the order of the jobs; a batch of 1 -> _single."""
        if len(jobs) == 1:
            return [self._single(jobs[0])]
        m, B, blk = self.m, len(jobs), self.lm.block
        L = min(blk, max(len(z.pref) + z.limit for z in jobs))
        nkv = [b.nkv for b in m.blocks]
        K = [torch.zeros((B, n, L, self.hd), dtype=torch.float32, device=self.dev) for n in nkv]
        V = [torch.zeros((B, n, L, self.hd), dtype=torch.float32, device=self.dev) for n in nkv]
        gens = [None] * B
        pos = [0] * B  # positions on the host (no GPU synchronization in the loop)
        next_tok = [0] * B
        for r, z in enumerate(jobs):  # prefill of the row: the single-row path (SlayerLM._step), then K/V copied to the slot
            if z.temperature > 0:
                gens[r] = torch.Generator(device=self.dev)
                gens[r].manual_seed(int(z.seed) if z.seed is not None else 0)
            c = self.lm._new_cache(len(z.pref))
            log = self.lm._step(torch.tensor([z.pref], dtype=torch.long, device=self.dev), c)
            self.lm.forward_tokens += len(z.pref)
            for li in range(len(m.blocks)):
                K[li][r, :, :len(z.pref)] = c["K"][li][0]
                V[li][r, :, :len(z.pref)] = c["V"][li][0]
            pos[r] = len(z.pref)
            t = self._sample(log[-1], z, gens[r])
            if t == START_ID:
                z.reason = "eos"
            else:
                z.gen.append(t)
                next_tok[r] = t
                z.reason = self._stop_reason(z, len(z.pref) + 1)
        rows = torch.arange(B, device=self.dev)
        while True:
            active = [r for r, z in enumerate(jobs) if z.reason is None]
            if not active:
                break
            # the step runs for all B rows (no K/V copy by indexing); a finished row recomputes its last token at its own
            # position (the same values in its own slot), and its logits are ignored
            p = torch.tensor(pos, dtype=torch.long, device=self.dev)       # position of the new token, [B]
            x = m.tok(torch.tensor([[t] for t in next_tok], dtype=torch.long, device=self.dev))
            Lc = max(pos) + 1
            mask = (torch.arange(Lc, device=self.dev)[None, :] <= p[:, None])[:, None, None, :]  # [B,1,1,Lc]
            v0 = None
            for li, b in enumerate(m.blocks):
                Bb, T, D = x.size()
                q, k, v = b.qkv(b.ln1(x)).split([b.d, b.kvd, b.kvd], dim=2)
                q = b.q_norm(q.view(Bb, T, b.nh, self.hd).transpose(1, 2))
                k = b.k_norm(k.view(Bb, T, b.nkv, self.hd).transpose(1, 2))
                v = v.view(Bb, T, b.nkv, self.hd).transpose(1, 2)
                q, k = self._rope_rows(q, p), self._rope_rows(k, p)
                if b.is_first:
                    v0 = v
                else:
                    v = v + b.vr_lambda * v0
                K[li][rows, :, p] = k[:, :, 0]
                V[li][rows, :, p] = v[:, :, 0]
                kk, vv = K[li][:, :, :Lc], V[li][:, :, :Lc]
                if b.nkv != b.nh:
                    kk, vv = kk.repeat_interleave(b.nh // b.nkv, dim=1), vv.repeat_interleave(b.nh // b.nkv, dim=1)
                y = F.scaled_dot_product_attention(q, kk, vv, attn_mask=mask)
                x = x + b.proj(y.transpose(1, 2).contiguous().view(Bb, T, D))
                x = x + b.mlp(b.ln2(x))
            logits = m._head(m.lnf(x))[:, 0, :self.lm.V].float()
            self.lm.forward_tokens += len(active)
            for r in active:
                z = jobs[r]
                pos[r] += 1
                t = self._sample(logits[r], z, gens[r])
                if t == START_ID:
                    z.reason = "eos"
                    continue
                z.gen.append(t)
                next_tok[r] = t
                z.reason = self._stop_reason(z, pos[r] + 1)
        results = []
        for z in jobs:
            text = self.lm.tok.decode(z.gen)
            for u in z.until:
                if u and u in text:
                    text = text.split(u)[0]
            results.append((text, len(z.gen), z.reason))
        return results
