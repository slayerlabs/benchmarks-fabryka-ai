"""Forward Slayera 1B odtworzony z config.json i nazw wag (repo HF nie ma kodu modelowania).

Architektura z config.json: pre-norm RMSNorm, fused qkv, qk_norm per głowa, RoPE (theta 500k),
SwiGLU, value residual (skalar `vr_lambda` w blokach 1..N-1 miesza V bloku z V bloku 0),
wagi tied tok/head, bez biasów i bez logit cap. Szczegóły, których config nie rozstrzyga
(styl RoPE, wzór value residual), są parametrami `wariant`; właściwy wybieramy po najniższym
BPB na WikiText-2 i zgodności z byte_ppl 1.06 opublikowanym w Space (1,846).

Weryfikacja 30.10 (odczyt train_gpt_ref_r23.py z repo HF SlayerLab/Slayer1B-1.06, bez uruchamiania):
forward zgodny z referencją - RMSNorm x*rsqrt(mean(x^2)+eps)*w, qk_norm przed RoPE, RoPE
„interleaved" na pełnym wymiarze głowy, v = v + vr_lambda*v0 (v0 = surowe V bloku 0), domyślna
skala SDPA, head = tok (tied), bez skalowania embeddingu. Jedyna różnica: referencja liczy kąty
RoPE w float32, my w float64 (różnica kąta < 1e-3 rad przy pozycji 4096). WikiText-2 byte_ppl
1,846284 wobec 1,846284 w Space przy mianowniku jak w lm-eval (benchmarks/wikitext-2/README.md).
"""

import json
import math
from pathlib import Path

import torch
import torch.nn.functional as F
from safetensors.torch import load_file
from tokenizers import Tokenizer


def rmsnorm(x, w, eps):
    xf = x.float()
    return (xf * torch.rsqrt(xf.pow(2).mean(-1, keepdim=True) + eps)).to(x.dtype) * w


class Slayer(torch.nn.Module):
    BOS = 0  # <|endoftext|> in the Slayer tokenizer.json (load_slayer.py: "id 0 is end-of-text")

    # Domyślne = wariant wybrany pomiarem 29.10 na 3 dokumentach WikiText-2 (1.06): RoPE przeplatany
    # (gptj) + v = v + lambda*v0 dał byte_ppl 1,98; neox 3,98-5,65, lerp 2,09, sigmoid 3,97. Liczby z mianownikiem
    # po detokenizacji (sprzed korekty), więc wyższe niż w konwencji lm-eval; ranking wariantów od tego nie zależy.
    def __init__(self, katalog, device="cpu", dtype=torch.float32, rope="gptj", vr="add"):
        super().__init__()
        katalog = Path(katalog)
        self.cfg = json.loads((katalog / "config.json").read_text())
        self.tok = Tokenizer.from_file(str(katalog / "tokenizer.json"))
        self.w = {k: v.to(device=device, dtype=dtype) for k, v in load_file(str(katalog / "model.safetensors")).items()}
        self.device, self.dtype, self.rope, self.vr = device, dtype, rope, vr
        self.qk_po_rope, self.skala = False, None  # warianty diagnostyczne (sonda WikiText)
        c = self.cfg
        self.n_layer, self.n_head, self.d = c["n_layer"], c["n_head"], c["n_embd"]
        self.hd = self.d // self.n_head
        self.eps = c["norm_eps"]
        self.blok = c["block"]
        self.bos = self.BOS
        inv = 1.0 / (c["rope_theta"] ** (torch.arange(0, self.hd, 2, dtype=torch.float64) / self.hd))
        t = torch.arange(self.blok, dtype=torch.float64)
        fr = torch.outer(t, inv)
        self.cos = fr.cos().to(device=device, dtype=torch.float32)
        self.sin = fr.sin().to(device=device, dtype=torch.float32)

    def encode(self, tekst):
        return self.tok.encode(tekst, add_special_tokens=False).ids

    def _rope(self, x, start=0):
        T = x.shape[-2]
        cos, sin = self.cos[start:start + T], self.sin[start:start + T]
        xf = x.float()
        if self.rope == "neox":
            x1, x2 = xf[..., : self.hd // 2], xf[..., self.hd // 2:]
            out = torch.cat([x1 * cos - x2 * sin, x1 * sin + x2 * cos], -1)
        else:
            x1, x2 = xf[..., 0::2], xf[..., 1::2]
            out = torch.stack([x1 * cos - x2 * sin, x1 * sin + x2 * cos], -1).flatten(-2)
        return out.to(x.dtype)

    @torch.no_grad()
    def logits(self, ids):
        """ids: LongTensor [B, T] -> logity [B, T, V] (float32)."""
        return self.glowa(self.ukryte(ids))

    @torch.no_grad()
    def glowa(self, h):
        return (h @ self.w["tok.weight"].T).float()

    @torch.no_grad()
    def krok(self, ids, cache):
        """Generacja z KV cache: ids [B, T] dalszych tokenów -> logity ostatniej pozycji [B, V] (float32).

        `cache` to lista (pusta na starcie sekwencji) uzupełniana w miejscu przez `ukryte`.
        """
        return self.glowa(self.ukryte(ids, cache)[:, -1])

    @torch.no_grad()
    def ukryte(self, ids, cache=None):
        """ids: LongTensor [B, T] -> stan po lnf [B, T, d].

        `cache`: lista par (K po RoPE, V po value residual) na warstwę; `ids` to wtedy tokeny po tych w cache,
        a pozycje RoPE zaczynają się od długości cache. Bez cache forward jest ten sam co przed jego dodaniem.
        """
        w = self.w
        x = w["tok.weight"][ids]
        B, T, _ = x.shape
        P = cache[0][0].shape[2] if cache else 0
        if P + T > self.blok:
            raise ValueError(f"Slayer: {P + T} pozycji, a block = {self.blok}")
        v0 = None
        for i in range(self.n_layer):
            p = f"blocks.{i}."
            h = rmsnorm(x, w[p + "ln1.weight"], self.eps)
            q, k, v = (h @ w[p + "qkv.weight"].T).split(self.d, -1)
            q = q.view(B, T, self.n_head, self.hd).transpose(1, 2)
            k = k.view(B, T, self.n_head, self.hd).transpose(1, 2)
            v = v.view(B, T, self.n_head, self.hd).transpose(1, 2)
            if self.cfg.get("value_residual"):
                if v0 is None:
                    v0 = v
                else:
                    lam = w[p + "vr_lambda"]
                    if self.vr == "add":
                        v = v + lam * v0
                    elif self.vr == "lerp":
                        v = (1 - lam) * v + lam * v0
                    elif self.vr == "sigmoid":
                        s = torch.sigmoid(lam)
                        v = (1 - s) * v + s * v0
            if self.qk_po_rope:
                q, k = self._rope(q, P), self._rope(k, P)
            q = rmsnorm(q, w[p + "q_norm.weight"], self.eps)
            k = rmsnorm(k, w[p + "k_norm.weight"], self.eps)
            if not self.qk_po_rope:
                q, k = self._rope(q, P), self._rope(k, P)
            if cache is not None:
                if P:
                    k = torch.cat([cache[i][0], k], 2)
                    v = torch.cat([cache[i][1], v], 2)
                if i < len(cache):
                    cache[i] = (k, v)
                else:
                    cache.append((k, v))
            if P == 0:
                a = F.scaled_dot_product_attention(q, k, v, is_causal=True, scale=self.skala)
            else:
                # is_causal w SDPA wyrównuje maskę do lewego górnego rogu, a zapytania stoją na pozycjach P..P+T-1.
                mask = None if T == 1 else torch.ones(T, P + T, dtype=torch.bool, device=x.device).tril(P)
                a = F.scaled_dot_product_attention(q, k, v, attn_mask=mask, scale=self.skala)
            x = x + a.transpose(1, 2).reshape(B, T, self.d) @ w[p + "proj.weight"].T
            h = rmsnorm(x, w[p + "ln2.weight"], self.eps)
            m = F.silu(h @ w[p + "mlp.gate.weight"].T) * (h @ w[p + "mlp.up.weight"].T)
            x = x + m @ w[p + "mlp.down.weight"].T
        return rmsnorm(x, w["lnf.weight"], self.eps)
