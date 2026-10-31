"""lm-eval wrapper `slayer` without network or weights. Run: python tests/test_lm_eval_slayer.py"""
import argparse
import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

COMMON_DIR = Path(__file__).resolve().parent.parent / "common"
sys.path.insert(0, str(COMMON_DIR))

import torch  # noqa: E402
from safetensors.torch import save_file  # noqa: E402
from tokenizers import Regex, Tokenizer  # noqa: E402
from tokenizers.decoders import Fuse  # noqa: E402
from tokenizers.models import WordLevel  # noqa: E402
from tokenizers.pre_tokenizers import Split  # noqa: E402

import ewaluuj  # noqa: E402
import slayer_lm  # noqa: E402
import slayer_model  # noqa: E402
from lm_eval.api.instance import Instance  # noqa: E402
from lm_eval.api.registry import get_model  # noqa: E402

# A `.pth` from before the `lm_eval` condition imports `slayer_lm` of its own checkout at every Python start.
assert Path(slayer_lm.__file__).resolve().parent == COMMON_DIR, (
    f"slayer_lm comes from {slayer_lm.__file__}, run: python common/slayer_lm.py --install")


DATA = COMMON_DIR / "tests" / "data" / "arc_challenge.jsonl"
PROMPT = "Question: {question}\nAnswer:"


def _questions():
    lines = DATA.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 10, f"{DATA} has {len(lines)} questions, the test needs 10"
    return [json.loads(line) for line in lines[:10]]


def _tokenizer(model_dir, questions):
    chars = set("Question: \nAnswer:")
    for d in questions:
        chars.update(d["question"])
        for choice in d["choices"]["text"]:
            chars.update(choice)
    vocab = {"<|endoftext|>": 0}
    for i, char in enumerate(sorted(chars), start=1):
        vocab[char] = i
    tok = Tokenizer(WordLevel(vocab, unk_token="<|endoftext|>"))
    tok.pre_tokenizer = Split(Regex("."), behavior="isolated")
    tok.decoder = Fuse()
    tok.save(str(model_dir / "tokenizer.json"))
    (model_dir / "tokenizer_config.json").write_text(json.dumps({
        "tokenizer_class": "PreTrainedTokenizerFast",
        "bos_token": "<|endoftext|>",
        "eos_token": "<|endoftext|>",
        "pad_token": "<|endoftext|>",
        "unk_token": "<|endoftext|>",
        "model_max_length": 512,
    }), encoding="utf-8")
    (model_dir / "special_tokens_map.json").write_text(json.dumps({
        "bos_token": "<|endoftext|>",
        "eos_token": "<|endoftext|>",
        "pad_token": "<|endoftext|>",
        "unk_token": "<|endoftext|>",
    }), encoding="utf-8")
    return len(vocab)


def _weights(cfg, seed):
    g = torch.Generator().manual_seed(seed)
    def r(*shape, scale=0.02):
        return torch.randn(*shape, generator=g) * scale
    n, d, hd, ffn = cfg["n_layer"], cfg["n_embd"], cfg["n_embd"] // cfg["n_head"], 48
    w = {"tok.weight": r(cfg["vocab"], d), "lnf.weight": torch.ones(d)}
    for i in range(n):
        p = f"blocks.{i}."
        w[p + "ln1.weight"] = torch.ones(d)
        w[p + "ln2.weight"] = torch.ones(d)
        w[p + "qkv.weight"] = r(3 * d, d)
        w[p + "q_norm.weight"] = torch.ones(hd)
        w[p + "k_norm.weight"] = torch.ones(hd)
        w[p + "proj.weight"] = r(d, d)
        w[p + "mlp.gate.weight"] = r(ffn, d)
        w[p + "mlp.up.weight"] = r(ffn, d)
        w[p + "mlp.down.weight"] = r(d, ffn)
        if i:
            w[p + "vr_lambda"] = torch.zeros(1)
    return w


def _model_dir(tmp, questions):
    model_dir = Path(tmp)
    vocab = _tokenizer(model_dir, questions)
    cfg = {"n_layer": 2, "n_head": 4, "n_embd": 32, "vocab": vocab, "block": 512,
           "norm_eps": 1e-6, "rope_theta": 10000.0, "value_residual": True}
    (model_dir / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    save_file(_weights(cfg, seed=0), model_dir / "model.safetensors")
    return model_dir


def _requests(questions):
    requests = []
    i = 0
    for d in questions:
        ctx = PROMPT.format(question=d["question"])
        for choice in d["choices"]["text"]:
            requests.append(Instance("loglikelihood", {}, (ctx, " " + choice), i))
            i += 1
    return requests


def _lm(model_dir, batch_size):
    return get_model("slayer")(pretrained=str(model_dir), device="cpu", dtype="float32", batch_size=batch_size)


def direct(slayer, ctx, cont):
    """Log-prob of `cont` after `ctx` and whether it is greedy, computed from `Slayer.logits` without lm-eval."""
    c = slayer.encode(ctx) if ctx else [slayer.bos]
    k = slayer.encode(cont)
    assert len(c) + len(k) <= slayer.blok
    inputs = torch.tensor([(c + k)[:-1]])
    lp = torch.log_softmax(slayer.logits(inputs), -1)[0, len(c) - 1:]
    idx = torch.tensor(k)
    return lp[torch.arange(len(k)), idx].sum().item(), bool((lp.argmax(-1) == idx).all())


def _greedy(slayer, ctx, n):
    """Text up to the first `\n`: greedy over one row, without lm-eval."""
    start = slayer.encode(ctx)
    new_tokens = []
    for _ in range(n):
        next_token = int(slayer.logits(torch.tensor([start + new_tokens]))[0, -1].argmax())
        if next_token == slayer.bos:
            break
        new_tokens.append(next_token)
    return slayer.tok.decode(new_tokens, skip_special_tokens=True).split("\n")[0]


def test_loglikelihood_matches_direct():
    questions = _questions()
    with tempfile.TemporaryDirectory() as tmp:
        model_dir = _model_dir(tmp, questions)
        slayer = slayer_model.Slayer(model_dir, device="cpu")
        requests = _requests(questions)
        assert len({r.arguments[0] for r in requests}) == 10
        for batch_size in (1, 4):
            results = _lm(model_dir, batch_size).loglikelihood(requests, disable_tqdm=True)
            assert len(results) == len(requests)
            for request, (ll, is_greedy) in zip(requests, results):
                ll_direct, is_greedy_direct = direct(slayer, *request.arguments)
                assert abs(ll - ll_direct) < 1e-4, (batch_size, ll, ll_direct)
                assert is_greedy == is_greedy_direct


def test_loglikelihood_rolling_matches_direct():
    questions = _questions()
    with tempfile.TemporaryDirectory() as tmp:
        model_dir = _model_dir(tmp, questions)
        slayer = slayer_model.Slayer(model_dir, device="cpu")
        lm = _lm(model_dir, 1)
        for d in questions[:3]:
            request = [Instance("loglikelihood_rolling", {}, (d["question"],), 0)]
            result = lm.loglikelihood_rolling(request, disable_tqdm=True)
            assert abs(result[0] - direct(slayer, "", d["question"])[0]) < 1e-4


def test_generate_until_matches_greedy_for_any_batch_size():
    questions = _questions()
    with tempfile.TemporaryDirectory() as tmp:
        model_dir = _model_dir(tmp, questions)
        slayer = slayer_model.Slayer(model_dir, device="cpu")
        contexts = [PROMPT.format(question=d["question"]) for d in questions[:4]]
        assert len({len(c) for c in contexts}) > 1
        requests = [Instance("generate_until", {}, (c, {"until": ["\n"], "max_gen_toks": 6}), i)
                    for i, c in enumerate(contexts)]
        one_by_one = _lm(model_dir, 1).generate_until(requests, disable_tqdm=True)
        batched = _lm(model_dir, 4).generate_until(requests, disable_tqdm=True)
        assert one_by_one == batched == [_greedy(slayer, c, 6) for c in contexts]


class _ScriptedSlayer:
    """Replaces the forward: a row picks its token script by the first real token of its context."""
    device, dtype, blok, bos = "cpu", torch.float32, 16, 0
    cfg = {"vocab": 5}
    w = {"tok.weight": torch.zeros(5, 2)}
    SCRIPTS = {1: (1, [2, 0, 3, 3]), 2: (2, [2, 2, 3, 3])}

    def logits(self, ids):
        assert ids.shape[0] == 1 and int(ids[0, 0]) in self.SCRIPTS, ids
        length, script = self.SCRIPTS[int(ids[0, 0])]
        logits = torch.zeros(1, ids.shape[1], 5)
        logits[0, -1, script[ids.shape[1] - length]] = 1.0
        return logits


def test_generate_row_gets_only_eos_after_end_of_text():
    inputs = torch.tensor([[0, 1], [2, 2]])
    mask = torch.tensor([[0, 1], [1, 1]])
    seen = []

    def criterion(ids, scores):
        seen.append(ids.shape)
        return torch.tensor([False, False])

    output = slayer_lm._SlayerModule(_ScriptedSlayer()).generate(
        inputs, attention_mask=mask, max_length=6, stopping_criteria=criterion)
    assert output.tolist() == [[0, 1, 2, 0, 0, 0], [2, 2, 2, 2, 3, 3]]
    assert seen == [(2, 3), (2, 4), (2, 5), (2, 6)]


def test_generate_criterion_stops_whole_batch():
    inputs = torch.tensor([[0, 1], [2, 2]])
    mask = torch.tensor([[0, 1], [1, 1]])

    def criterion(ids, scores):
        return torch.tensor([ids.shape[1] >= 4] * 2)

    output = slayer_lm._SlayerModule(_ScriptedSlayer()).generate(
        inputs, attention_mask=mask, max_length=6, stopping_criteria=criterion)
    assert output.tolist() == [[0, 1, 2, 0], [2, 2, 2, 2]]


def test_rejects_arguments_slayer_does_not_use():
    with tempfile.TemporaryDirectory() as tmp:
        model_dir = _model_dir(tmp, _questions())
        for bad in ({"revision": "abc"}, {"peft": "/nope"}, {"unknown_arg": 1}):
            name = next(iter(bad))
            try:
                get_model("slayer")(pretrained=str(model_dir), device="cpu", **bad)
            except ValueError as e:
                assert name in str(e), e
            else:
                raise AssertionError(f"{name} was silently ignored")


def test_ewaluuj_model_id_without_repo():
    with tempfile.TemporaryDirectory() as tmp:
        model_dir = _model_dir(tmp, _questions())
        a = argparse.Namespace(model="slayer", model_path=str(model_dir), repo=None, revision=None,
                               batch="1", device="cpu")
        lm, model_id, revision = ewaluuj.zbuduj_model(a)
        assert isinstance(lm, slayer_lm.SlayerLM)
        assert (model_id, revision) == (model_dir.resolve().name, None)
        a.repo, a.revision = "SlayerLab/Slayer1B-1.06", "ef81be58"
        assert ewaluuj.zbuduj_model(a)[1:] == (a.repo, a.revision)


def _install(site_dir):
    stderr = io.StringIO()
    with mock.patch("sysconfig.get_path", return_value=str(site_dir)), mock.patch.object(sys, "prefix", "venv"), \
            mock.patch.object(sys, "base_prefix", "base"), contextlib.redirect_stderr(stderr), \
            contextlib.redirect_stdout(io.StringIO()):
        slayer_lm.install()
    return stderr.getvalue()


def test_install_reports_replaced_checkout():
    with tempfile.TemporaryDirectory() as tmp:
        pth_file = Path(tmp) / "slayer_lm_eval.pth"
        assert _install(tmp) == ""
        assert pth_file.read_text(encoding="utf-8").splitlines() == [str(COMMON_DIR), slayer_lm.PTH_LINE]
        assert _install(tmp) == ""
        pth_file.write_text("D:/other/common\n", encoding="utf-8")
        assert "D:/other/common" in _install(tmp)
        assert pth_file.read_text(encoding="utf-8").splitlines()[0] == str(COMMON_DIR)


def test_install_refuses_outside_venv():
    with tempfile.TemporaryDirectory() as tmp, mock.patch("sysconfig.get_path", return_value=tmp), \
            mock.patch.object(sys, "base_prefix", sys.prefix):
        try:
            slayer_lm.install()
        except SystemExit as e:
            assert "venv" in str(e)
        else:
            raise AssertionError("install wrote outside a venv")
        assert not list(Path(tmp).iterdir())


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            test()
            print("PASS", name)
