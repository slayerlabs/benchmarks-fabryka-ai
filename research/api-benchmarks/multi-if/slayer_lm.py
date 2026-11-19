"""slayer_lm.py - lm-eval adapter for Slayer1B (exported package: load_slayer.py + the trainer's model code).
Slayer is not a Hugging Face transformers model, so vLLM and HFLM cannot serve it. The adapter follows the
conventions of the Slayer evaluation board: start token 0 before the context, the (context, continuation) pair as in
lm-eval HFLM._encode_pair, fp32, TF32 off. No truncation: input + limit > block stops with "out of context".
- loglikelihood: log-likelihood of the continuation + is_greedy (as HFLM);
- generate_until: greedy decoding. By default with a KV cache, one row at a time (prefill with is_causal, then one
  token at a time; RoPE with a position offset, value residual and qk-norm as the trainer's Block.forward). --no-kv =
  the older batched path without a cache (full forward per token). Stop: token 0 (end of text), any string from
  'until', or max_gen_toks. No sampling (do_sample/temperature > 0 stops).
- --compare-kv N: KV check against the full forward on N prompts from --prompts (argmax at every position, max
  difference).
- loglikelihood_rolling: not supported (stops).
Usage: python slayer_lm.py --pkg <package dir> --tasks ifeval --out result.json [--limit N] [--no-kv]
       python slayer_lm.py --pkg <package dir> --prompts in.jsonl --responses out.jsonl --out result.json
"""
import argparse
import json
import os
import sys
import time

START_ID = 0
MAX_TOK = 32768  # rows x length in one forward (as on the board)


def stop(msg):
    print(f"STOP: {msg}", flush=True)
    sys.exit(2)


def model_from_package(pkg, dev):
    from tokenizers import Tokenizer
    with open(os.path.join(pkg, "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    tok = Tokenizer.from_file(os.path.join(pkg, "tokenizer.json"))
    if cfg["vocab"] != tok.get_vocab_size():
        stop(f"vocab config {cfg['vocab']} != tokenizer {tok.get_vocab_size()}")
    sys.path.insert(0, pkg)
    import load_slayer
    if os.path.abspath(os.path.dirname(load_slayer.__file__)) != os.path.abspath(pkg):
        stop(f"load_slayer from outside the package: {load_slayer.__file__}")
    return load_slayer.load(pkg, dev), tok, cfg


def build_lm():
    import torch
    import torch.nn.functional as F
    from lm_eval.api.model import LM

    class SlayerLM(LM):
        def __init__(self, pkg, device="cuda", batch=32, kv=True):
            super().__init__()
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False
            self.model, self.tok, self.cfg = model_from_package(pkg, device)
            self.V, self.block, self.dev, self.batch = self.tok.get_vocab_size(), int(self.cfg["block"]), device, batch
            self.forward_tokens = 0
            self.stop_log = []  # per request: doc_id, generated, reason
            self.kv = kv
            if kv:  # the KV cache reproduces only the Slayer 1.09 configuration (A blocks, interleaved RoPE, qk-norm, value residual)
                c = self.model.cfg
                needed = {"arch": (getattr(c, "arch", "gpt"), "gpt"), "pos": (c.pos, "rope"), "qk_norm": (bool(c.qk_norm), True),
                            "value_residual": (bool(c.value_residual), True), "rope_style": (getattr(c, "rope_style", "interleaved"), "interleaved"),
                            "rope_dims": (int(getattr(c, "rope_dims", 0) or 0), 0), "imha_t": (int(getattr(c, "imha_t", 0) or 0), 0),
                            "xsa": (int(getattr(c, "xsa", 0) or 0), 0), "loop": (int(getattr(c, "loop", 1) or 1), 1),
                            "emb_dim": (int(getattr(c, "emb_dim", 0) or 0), 0), "logit_cap": (float(getattr(c, "logit_cap", 0.0) or 0.0), 0.0),
                            "mixer_layout": (set(getattr(c, "mixer_layout", None) or "A"), {"A"})}
                bad = {k: v[0] for k, v in needed.items() if v[0] != v[1]}
                if bad:
                    stop(f"the KV cache does not support this configuration: {bad} (use --no-kv)")
                self.theta = float(c.rope_theta)

        def enc(self, t):
            return self.tok.encode(t, add_special_tokens=False).ids

        def encode_pair(self, ctx, cont):  # lm-eval HFLM._encode_pair
            n = len(ctx) - len(ctx.rstrip())
            if n > 0:
                cont, ctx = ctx[-n:] + cont, ctx[:-n]
            whole, ce = self.enc(ctx + cont), self.enc(ctx)
            return ce, whole[len(ce):]

        def loglikelihood(self, requests):
            out = []
            with torch.inference_mode():
                for r in requests:
                    ctx, cont = r.args
                    ce, ke = self.encode_pair(ctx, cont)
                    if not ke:
                        stop(f"empty continuation: {cont!r}")
                    full = [START_ID] + ce + ke
                    if len(full) - 1 > self.block:  # no context truncation
                        stop(f"out of context: input {len(full) - 1} > block {self.block}")
                    x = torch.tensor([full[:-1]], dtype=torch.long, device=self.dev)
                    logits = self.model(x)[0][0, -len(ke):, :self.V].float()
                    self.forward_tokens += x.shape[1]
                    lp = F.log_softmax(logits, dim=-1)
                    target = torch.tensor(ke, dtype=torch.long, device=self.dev)
                    ll = float(lp[torch.arange(len(ke), device=self.dev), target].sum())
                    out.append((ll, bool((lp.argmax(-1) == target).all())))
            return out

        def loglikelihood_rolling(self, requests):
            stop("loglikelihood_rolling is not supported in slayer_lm")

        def _rope(self, x, pos0):
            """The trainer's apply_rope (interleaved, nrot 0) with positions shifted by pos0; the same fp32 arithmetic."""
            T, dim = x.shape[2], x.shape[3]
            pos = torch.arange(pos0, pos0 + T, device=x.device, dtype=torch.float32)
            freq = 1.0 / (self.theta ** (torch.arange(0, dim, 2, device=x.device, dtype=torch.float32) / dim))
            ang = torch.outer(pos, freq)
            cos, sin = ang.cos().to(x.dtype)[None, None], ang.sin().to(x.dtype)[None, None]
            even, odd = x[..., ::2], x[..., 1::2]
            return torch.stack((even * cos - odd * sin, even * sin + odd * cos), dim=-1).flatten(-2)

        def _new_cache(self, n):
            """Preallocated KV cache for n positions: per block K, V [1, nkv, n, hd] fp32; 'n' = number of stored positions."""
            m = self.model
            hd = m.blocks[0].d // m.blocks[0].nh
            return {"n": 0, "K": [torch.empty((1, b.nkv, n, hd), dtype=torch.float32, device=self.dev) for b in m.blocks],
                    "V": [torch.empty((1, b.nkv, n, hd), dtype=torch.float32, device=self.dev) for b in m.blocks]}

        def _step(self, idx, cache):
            """Forward with a KV cache (the trainer's Block.forward for A blocks): idx [1,T] new tokens written in place
            into the preallocated cache (no copy of the history). T > 1 only with an empty cache (prefill, is_causal);
            then one token at a time with full attention to positions 0..n."""
            m = self.model
            pos0, T = cache["n"], idx.shape[1]
            if T > 1 and pos0:
                stop("KV: several tokens with a non-empty cache")
            if pos0 + T > cache["K"][0].shape[2]:
                stop(f"KV: {pos0 + T} positions > buffer {cache['K'][0].shape[2]}")
            x = m.tok(idx)
            v0 = None
            for li, b in enumerate(m.blocks):
                B, _, D = x.size()
                hd = D // b.nh
                q, k, v = b.qkv(b.ln1(x)).split([b.d, b.kvd, b.kvd], dim=2)
                q = b.q_norm(q.view(B, T, b.nh, hd).transpose(1, 2))
                k = b.k_norm(k.view(B, T, b.nkv, hd).transpose(1, 2))
                v = v.view(B, T, b.nkv, hd).transpose(1, 2)
                q, k = self._rope(q, pos0), self._rope(k, pos0)
                if b.is_first:
                    v0 = v
                else:
                    v = v + b.vr_lambda * v0
                cache["K"][li][:, :, pos0:pos0 + T] = k
                cache["V"][li][:, :, pos0:pos0 + T] = v
                k, v = cache["K"][li][:, :, :pos0 + T], cache["V"][li][:, :, :pos0 + T]
                if b.nkv != b.nh:  # GQA (Slayer 1.09 is MHA, branch unused)
                    k, v = k.repeat_interleave(b.nh // b.nkv, dim=1), v.repeat_interleave(b.nh // b.nkv, dim=1)
                y = F.scaled_dot_product_attention(q, k, v, is_causal=T > 1)
                x = x + b.proj(y.transpose(1, 2).contiguous().view(B, T, D))
                x = x + b.mlp(b.ln2(x))
            cache["n"] = pos0 + T
            return m._head(m.lnf(x))[0, :, :self.V].float()

        def _gen_kv(self, pref, mx, until):
            """Greedy decoding of one row with a KV cache; the same stop conditions as the path without a cache.
            Returns (tokens, reason): eos | until | max_gen_toks | block."""
            cache = self._new_cache(min(self.block, len(pref) + mx))
            logits = self._step(torch.tensor([pref], dtype=torch.long, device=self.dev), cache)
            self.forward_tokens += len(pref)
            gen, length = [], len(pref)
            while True:
                t = int(logits[-1].argmax())
                if t == START_ID:
                    return gen, "eos"
                gen.append(t)
                length += 1
                if any(u and u in self.tok.decode(gen) for u in until):
                    return gen, "until"
                if len(gen) >= mx:
                    return gen, "max_gen_toks"
                if length >= self.block:
                    return gen, "block"
                logits = self._step(torch.tensor([[t]], dtype=torch.long, device=self.dev), cache)
                self.forward_tokens += 1

        def _forced(self, seq, k):
            """KV on a FIXED sequence: prefill seq[:k], then the tokens seq[k:] forced one at a time; compares the
            logits of positions k-1..len-2 with one full forward (the path without a cache) on seq[:-1]."""
            cache = self._new_cache(len(seq))
            logits = self._step(torch.tensor([seq[:k]], dtype=torch.long, device=self.dev), cache)
            kv = [logits[-1]]
            for t in seq[k:-1]:
                kv.append(self._step(torch.tensor([[t]], dtype=torch.long, device=self.dev), cache)[-1])
            kv = torch.stack(kv)
            ref = self.model(torch.tensor([seq[:-1]], dtype=torch.long, device=self.dev))[0][0, k - 1:, :self.V].float()
            finite = bool(torch.isfinite(kv).all()) and bool(torch.isfinite(ref).all())
            return {"length": len(seq), "prefill": k, "steps": len(kv), "argmax_equal": int((ref.argmax(-1) == kv.argmax(-1)).sum()),
                    "logits_finite": finite,
                    "max_abs_logit_diff": float((ref - kv).abs().max()) if finite else None}

        def compare_kv(self, prompts, mx):
            """KV check, at unchanged precision (fp32, TF32 off):
            (A) logits on identical prefixes: the prompt as a fixed sequence, prefill of half + the rest forced;
            (B) block boundary: a sequence of exactly block tokens (prompt repeated), prefill block-32 + 32 forced;
            (C) KV generation vs the path without a cache (until=[], EOS = token 0): text, token count, stop reason, speed.
            Each A/B item: finiteness of both paths' logits and max |difference|; the gate is computed in main() with an
            explicit threshold."""
            from types import SimpleNamespace
            kv_res = {"A_fixed_prefixes": [], "B_block_boundary": [], "C_generation": []}
            with torch.inference_mode():
                for p in prompts:
                    seq = [START_ID] + self.enc(p)
                    while len(seq) < 64:
                        seq += self.enc(p)
                    kv_res["A_fixed_prefixes"].append(self._forced(seq, len(seq) // 2))
                base = self.enc(prompts[0])
                seq = ([START_ID] + base * (self.block // max(1, len(base)) + 1))[:self.block]
                kv_res["B_block_boundary"].append(self._forced(seq, self.block - 32))
            for p in prompts:
                req = [SimpleNamespace(args=(p, {"until": [], "max_gen_toks": mx}))]
                t0 = time.time()
                self.kv = True
                tk, kk = self.generate_until(req)[0], self.stops[0]
                t1 = time.time()
                self.kv = False
                tb, kb = self.generate_until(req)[0], self.stops[0]
                t2 = time.time()
                self.kv = True
                first_diff = next((i for i, (x, y) in enumerate(zip(tk, tb)) if x != y), None if len(tk) == len(tb) else min(len(tk), len(tb)))
                kv_res["C_generation"].append({"text_equal": tk == tb, "first_different_char": first_diff, "stop_kv": kk, "stop_no_kv": kb,
                                            "stop_equal": kk == kb, "seconds_kv": round(t1 - t0, 2), "seconds_no_kv": round(t2 - t1, 2)})
            return kv_res

        def generate_until(self, requests):
            """Returns the texts; self.stops[i] = {doc_id, generated, reason} for every request (both paths)."""
            outputs = [None] * len(requests)
            self.stops = [None] * len(requests)
            jobs = []
            for i, r in enumerate(requests):
                ctx, kw = r.args
                kw = dict(kw or {})
                if kw.get("do_sample") or float(kw.get("temperature", 0.0) or 0.0) > 0:
                    stop(f"sampling is not supported: {kw}")
                until = kw.get("until") or []
                until = [until] if isinstance(until, str) else list(until)
                mx = int(kw.get("max_gen_toks", 256))
                pref = [START_ID] + self.enc(ctx)
                # no prompt truncation; prompts that are too long are collected and stop before the first forward
                jobs.append((len(pref), i, pref, until, mx, getattr(r, "doc_id", i)))
            bad = [(z[1], z[0], z[4]) for z in jobs if z[4] <= 0 or z[0] + z[4] > self.block]
            if bad:
                stop(f"out of context {len(bad)}/{len(jobs)} (block {self.block}; index, input, limit): {bad[:10]}")
            if self.kv:
                with torch.inference_mode():
                    for z in jobs:
                        gen, reason = self._gen_kv(z[2], z[4], z[3])
                        text = self.tok.decode(gen)
                        for u in z[3]:
                            if u and u in text:
                                text = text.split(u)[0]
                        outputs[z[1]] = text
                        self.stops[z[1]] = {"doc_id": z[5], "generated": len(gen), "reason": reason}
                self.stop_log.extend(self.stops)
                return outputs
            jobs.sort(key=lambda z: -z[0])
            with torch.inference_mode():
                j = 0
                while j < len(jobs):
                    T0 = jobs[j][0]
                    b = 1
                    while j + b < len(jobs) and b < self.batch and (b + 1) * min(self.block, T0 + jobs[j][4]) <= MAX_TOK:
                        b += 1
                    part = jobs[j:j + b]
                    seqs = [list(z[2]) for z in part]
                    gen = [[] for _ in part]
                    done = [None] * b  # stop reason of each row (None = still running)
                    mx = max(z[4] for z in part)
                    for _ in range(mx):
                        if all(done):
                            break
                        L = max(len(s) for s in seqs)
                        x = torch.zeros((b, L), dtype=torch.long)
                        for r, s in enumerate(seqs):
                            x[r, :len(s)] = torch.tensor(s, dtype=torch.long)
                        logits = self.model(x.to(self.dev))[0]
                        self.forward_tokens += b * L
                        for r, s in enumerate(seqs):
                            if done[r]:
                                continue
                            t = int(logits[r, len(s) - 1, :self.V].argmax())
                            if t == START_ID:
                                done[r] = "eos"
                                continue
                            gen[r].append(t)
                            s.append(t)
                            text = self.tok.decode(gen[r])
                            if any(u and u in text for u in part[r][3]):
                                done[r] = "until"
                            elif len(gen[r]) >= part[r][4]:
                                done[r] = "max_gen_toks"
                            elif len(s) >= self.block:
                                done[r] = "block"
                    for r, z in enumerate(part):
                        text = self.tok.decode(gen[r])
                        for u in z[3]:
                            if u and u in text:
                                text = text.split(u)[0]
                        outputs[z[1]] = text
                        self.stops[z[1]] = {"doc_id": z[5], "generated": len(gen[r]), "reason": done[r] or "max_gen_toks"}
                    j += b
            self.stop_log.extend(self.stops)
            return outputs

    return SlayerLM


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pkg", required=True)
    ap.add_argument("--tasks", default="", help="comma-separated lm-eval tasks, e.g. ifeval")
    ap.add_argument("--prompts", default="", help="raw-completion mode: JSONL with a 'prompt' field (e.g. IFBench) instead of lm-eval")
    ap.add_argument("--responses", default="", help="raw-completion mode: output JSONL {'prompt','response'} for the scorer")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-gen-toks", type=int, default=0, help="0 = as in the task")
    ap.add_argument("--no-kv", action="store_true", help="the older batched path without a KV cache")
    ap.add_argument("--compare-kv", type=int, default=0, help="N > 0: only the KV check against the full forward on N prompts from --prompts")
    ap.add_argument("--logit-threshold", type=float, default=None,
                    help="required with --compare-kv: explicit threshold for max |logit difference| in A/B, set before reading the numbers")
    a = ap.parse_args()
    t0 = time.time()
    if a.compare_kv:
        if not a.prompts or a.no_kv or a.logit_threshold is None or not a.logit_threshold > 0:
            stop("--compare-kv needs --prompts, the KV cache and --logit-threshold > 0")
        lm = build_lm()(a.pkg, a.device, a.batch, kv=True)
        rows = [json.loads(l) for l in open(a.prompts, encoding="utf-8") if l.strip()][:a.compare_kv]
        mx = a.max_gen_toks or 1280
        kv_res = lm.compare_kv([w["prompt"] for w in rows], mx)
        ab = kv_res["A_fixed_prefixes"] + kv_res["B_block_boundary"]
        gate = {"A_B_argmax_equal": all(w["argmax_equal"] == w["steps"] for w in ab),
                "A_B_logits_finite": all(w["logits_finite"] for w in ab),
                "A_B_max_diff_within_threshold": all(w["logits_finite"] and w["max_abs_logit_diff"] <= a.logit_threshold for w in ab),
                "C_text_and_stop_equal": all(w["text_equal"] and w["stop_equal"] for w in kv_res["C_generation"])}
        ok = all(gate.values())
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump({"mode": "compare-kv", "n": len(rows), "max_gen_toks": mx, "dtype": "fp32", "tf32": False,
                       "logit_threshold": a.logit_threshold, "gate": gate, "gate_ok": ok, "seconds": round(time.time() - t0, 1),
                       **kv_res}, fh, ensure_ascii=False, indent=1)
        print(f"SLAYER-KV-{'OK' if ok else 'MISMATCH'} {json.dumps(gate)}", flush=True)
        sys.exit(0 if ok else 3)
    if bool(a.tasks) == bool(a.prompts) or bool(a.prompts) != bool(a.responses):
        stop("either --tasks, or --prompts with --responses")
    lm = build_lm()(a.pkg, a.device, a.batch, kv=not a.no_kv)
    if a.prompts:  # the original prompt as a raw continuation, no system prompt or labels, greedy, until=[]
        from types import SimpleNamespace
        rows = [json.loads(l) for l in open(a.prompts, encoding="utf-8") if l.strip()]
        if a.limit:
            rows = rows[:a.limit]
        mx = a.max_gen_toks or 1280
        responses = lm.generate_until([SimpleNamespace(args=(w["prompt"], {"until": [], "max_gen_toks": mx})) for w in rows])
        with open(a.responses, "w", encoding="utf-8") as fh:
            for w, o in zip(rows, responses):
                fh.write(json.dumps({"prompt": w["prompt"], "response": o}, ensure_ascii=False) + "\n")
        summary = {"model": "Slayer1B", "mode": "raw-completion", "prompts": os.path.abspath(a.prompts), "n": len(rows),
                   "max_gen_toks": mx, "empty": sum(1 for o in responses if not o.strip()), "config_step": lm.cfg.get("step"),
                   "ckpt_sha256": lm.cfg.get("ckpt_sha256"), "batch": a.batch, "dtype": "fp32", "tf32": False, "kv_cache": lm.kv,
                   "forward_tokens": lm.forward_tokens, "seconds": round(time.time() - t0, 1),
                   "stop_per_prompt": [dict(k, prompt_idx=i) for i, k in enumerate(lm.stop_log)]}
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=1)
        print(f"SLAYER-LM-OK raw {len(rows)} {summary['seconds']} s -> {a.responses}", flush=True)
        return
    import lm_eval
    gk = f"max_gen_toks={a.max_gen_toks}" if a.max_gen_toks else None
    res = lm_eval.simple_evaluate(model=lm, tasks=a.tasks.split(","), limit=a.limit or None, log_samples=True,
                                  gen_kwargs=gk, bootstrap_iters=0)
    summary = {"model": "Slayer1B", "pkg": os.path.abspath(a.pkg), "config_step": lm.cfg.get("step"),
               "ckpt_sha256": lm.cfg.get("ckpt_sha256"), "lm_eval": lm_eval.__version__, "limit": a.limit,
               "max_gen_toks": a.max_gen_toks or "task", "batch": a.batch, "dtype": "fp32", "tf32": False, "kv_cache": lm.kv,
               "forward_tokens": lm.forward_tokens, "seconds": round(time.time() - t0, 1), "stop_per_request": lm.stop_log,
               "results": res["results"], "configs": res.get("configs"), "versions": res.get("versions"),
               "task_hashes": res.get("task_hashes"), "n_samples": res.get("n-samples"),
               "samples": {k: [{"doc_id": s.get("doc_id"), "resps": s.get("resps"), "filtered_resps": s.get("filtered_resps"),
                                **{m: s.get(m) for m in s if m.endswith("_acc") or m.endswith("_strict") or m.endswith("_loose")}}
                               for s in v] for k, v in (res.get("samples") or {}).items()}}
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1, default=str)
    print(f"SLAYER-LM-OK {a.tasks} {summary['seconds']} s -> {a.out}", flush=True)


if __name__ == "__main__":
    main()
