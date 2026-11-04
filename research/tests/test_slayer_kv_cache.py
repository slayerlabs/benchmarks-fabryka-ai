"""KV cache of Slayer generation, without network or weights. Run: python tests/test_slayer_kv_cache.py [--speed]"""
import sys
import tempfile
import time

import torch

import test_lm_eval_slayer as base
import slayer_lm
import slayer_model
from lm_eval.api.instance import Instance


class _NoCache:
    """The same model without `krok`: `generate` recomputes the whole sequence at each step."""

    def __init__(self, slayer):
        self.s = slayer

    def __getattr__(self, name):
        if name == "krok":
            raise AttributeError(name)
        return getattr(self.s, name)


def _slayer(tmp):
    return slayer_model.Slayer(base._model_dir(tmp, base._questions(), weights=base.reference_weights), device="cpu")


def _prompts(slayer):
    texts = ["", "Answer:"] + [base.PROMPT.format(question=d["question"]) for d in base._questions()[:4]]
    return [[slayer.bos] + slayer.encode(t) for t in texts]


def _incremental(slayer, ids, chunks):
    """Logits of every position of `ids` fed to `ukryte` with a cache in chunks of the given sizes."""
    cache, out, start = [], [], 0
    for size in chunks:
        part = torch.tensor([ids[start:start + size]])
        out.append(slayer.glowa(slayer.ukryte(part, cache))[0])
        start += size
    assert start == len(ids)
    return torch.cat(out)


def test_cached_logits_match_full_forward():
    with tempfile.TemporaryDirectory() as tmp:
        slayer = _slayer(tmp)
        for rope, qk_after in (("gptj", False), ("neox", False), ("gptj", True)):
            slayer.rope, slayer.qk_po_rope = rope, qk_after
            for ids in _prompts(slayer):
                full = slayer.logits(torch.tensor([ids]))[0]
                n = len(ids)
                # one token at a time, then a prefill and multi-token chunks (explicit mask with an offset)
                for chunks in ([1] * n, [n], [max(1, n // 3), n - max(1, n // 3)] if n > 1 else [n]):
                    diff = (_incremental(slayer, ids, chunks) - full).abs().max().item()
                    assert diff < 1e-4, (rope, qk_after, n, chunks, diff)
                last = slayer.krok(torch.tensor([ids]), [])[0]
                assert (last - full[-1]).abs().max().item() < 1e-4


def test_cache_respects_block():
    with tempfile.TemporaryDirectory() as tmp:
        slayer = _slayer(tmp)
        cache = []
        slayer.ukryte(torch.zeros(1, slayer.blok, dtype=torch.long), cache)
        try:
            slayer.ukryte(torch.zeros(1, 1, dtype=torch.long), cache)
        except ValueError:
            return
        raise AssertionError("cache went past block")


def _batch(prompts):
    width = max(len(p) for p in prompts)
    ids = torch.zeros(len(prompts), width, dtype=torch.long)
    mask = torch.zeros(len(prompts), width, dtype=torch.long)
    for i, p in enumerate(prompts):
        ids[i, width - len(p):] = torch.tensor(p)
        mask[i, width - len(p):] = 1
    return ids, mask


def test_generate_with_cache_matches_without_token_for_token():
    with tempfile.TemporaryDirectory() as tmp:
        slayer = _slayer(tmp)
        prompts = _prompts(slayer)
        ids, mask = _batch(prompts)
        new = 30
        cached = slayer_lm._SlayerModule(slayer).generate(ids, attention_mask=mask, max_length=ids.shape[1] + new)
        plain = slayer_lm._SlayerModule(_NoCache(slayer)).generate(ids, attention_mask=mask,
                                                                     max_length=ids.shape[1] + new)
        assert cached.tolist() == plain.tolist()
        for i, p in enumerate(prompts):
            one = slayer_lm._SlayerModule(slayer).generate(torch.tensor([p]), max_length=len(p) + new)
            gen = one[0, len(p):].tolist()
            assert gen == cached[i, ids.shape[1]:ids.shape[1] + len(gen)].tolist(), i
        assert (cached[:, ids.shape[1]:] != slayer.bos).sum() > len(prompts), "every row ended at once"


def test_generate_until_with_cache_matches_without():
    with tempfile.TemporaryDirectory() as tmp:
        model_dir = base._model_dir(tmp, base._questions(), weights=base.reference_weights)
        contexts = ["", "Answer:"] + [base.PROMPT.format(question=d["question"]) for d in base._questions()[:4]]
        requests = [Instance("generate_until", {}, (c, {"until": ["\n"], "max_gen_toks": 20}), i)
                    for i, c in enumerate(contexts)]
        results = []
        for batch_size in (1, 4):
            for cached in (True, False):
                lm = base._lm(model_dir, batch_size)
                if not cached:
                    lm._model = slayer_lm._SlayerModule(_NoCache(lm._model.slayer))
                results.append(lm.generate_until(requests, disable_tqdm=True))
        assert all(r == results[0] for r in results), results


def speed(n_layer=4, n_embd=256, n_head=8, prompt=200, new=100, batch=4):
    """Generation time with and without cache on a random config (CPU, float32); returns (s cache, s without)."""
    with tempfile.TemporaryDirectory() as tmp:
        model_dir = base._model_dir(tmp, base._questions(), weights=base.reference_weights)
        cfg = base.json.loads((model_dir / "config.json").read_text())
        cfg.update(n_layer=n_layer, n_embd=n_embd, n_head=n_head, block=prompt + new + 8)
        (model_dir / "config.json").write_text(base.json.dumps(cfg))
        base.save_file(base.reference_weights(cfg, seed=0), model_dir / "model.safetensors")
        slayer = slayer_model.Slayer(model_dir, device="cpu")
        g = torch.Generator().manual_seed(0)
        ids = torch.randint(1, cfg["vocab"], (batch, prompt), generator=g)
        ids[:, 0] = slayer.bos
        slayer.bos = -1  # no id ends the text, so every row generates all `new` tokens
        times, outputs = [], []
        for model in (slayer, _NoCache(slayer)):
            start = time.perf_counter()
            outputs.append(slayer_lm._SlayerModule(model).generate(ids, max_length=prompt + new))
            times.append(time.perf_counter() - start)
        assert outputs[0].tolist() == outputs[1].tolist()
        return times


if __name__ == "__main__":
    torch.set_num_threads(4)
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            test()
            print("PASS", name)
    if "--speed" in sys.argv:
        with_cache, without = speed()
        print(f"speed: cache {with_cache:.2f} s, without {without:.2f} s, x{without / with_cache:.1f}")
