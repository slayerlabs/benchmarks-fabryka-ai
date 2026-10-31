"""lm-eval wrapper for Slayer 1B (model `slayer`).

Slayer's `config.json` has no `model_type`, so `HFLM` / `AutoConfig` ends with
`ValueError: Unrecognized model`. This class loads the weights through `slayer_model.py`
and takes `loglikelihood`, `loglikelihood_rolling` and `generate_until` from `HFLM`
(the same contract as `--model hf`).

CLI registration: `python common/slayer_lm.py --install` (once per venv and checkout,
the `.pth` file stores the path of this `common/`), then
`lm_eval --model slayer --model_args pretrained=models/slayer-1.06`.
"""

import json
import sys
from pathlib import Path

COMMON_DIR = Path(__file__).resolve().parent
# An `import` line in a `.pth` runs at every Python start, so the heavy imports happen only under the lm_eval command.
PTH_LINE = ("import os, sys; "
            "os.path.basename(sys.argv[0]).split('.')[0].replace('-', '_') == 'lm_eval' "
            "and __import__('slayer_lm')")


def install():
    """Adds `common/` to the venv and registers this wrapper when the `lm_eval` command starts (`.pth` file)."""
    import sysconfig
    if sys.prefix == sys.base_prefix:
        sys.exit("slayer_lm --install: not in a venv, run it with the venv's python")
    site_dir = Path(sysconfig.get_path("purelib"))
    site_dir.mkdir(parents=True, exist_ok=True)
    pth_file = site_dir / "slayer_lm_eval.pth"
    if pth_file.is_file():
        previous = pth_file.read_text(encoding="utf-8").splitlines()[0]
        if previous != str(COMMON_DIR):
            print(f"Replacing {previous}: one venv serves one checkout", file=sys.stderr)
    pth_file.write_text(f"{COMMON_DIR}\n{PTH_LINE}\n", encoding="utf-8")
    print(pth_file)


# Before the lm-eval imports: an old `.pth` imports this module at startup and a second `slayer` registration is an error.
if __name__ == "__main__":
    if "--install" in sys.argv:
        install()
        sys.exit(0)
    print("Usage: python common/slayer_lm.py --install", file=sys.stderr)
    sys.exit(2)

import torch  # noqa: E402
import transformers  # noqa: E402
from lm_eval.api.registry import register_model  # noqa: E402
from lm_eval.models.huggingface import HFLM  # noqa: E402
from lm_eval.models.utils import get_dtype  # noqa: E402

if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

import slayer_model  # noqa: E402

# `HFLM._create_model` arguments with their defaults. Slayer uses none of them, so another value is an error: without
# it `revision=abc` would score the local weights and report that revision.
UNUSED_LOAD_ARGS = {"revision": "main", "trust_remote_code": False, "parallelize": False, "max_memory_per_gpu": None,
                    "max_cpu_memory": None, "offload_folder": "./offload", "peft": None, "delta": None,
                    "autogptq": False, "gptqmodel": False, "gguf_file": None, "quantization_config": None,
                    "subfolder": ""}


def set_slayer_tokens(tokenizer):
    """Slayer has no tokenizer_config.json: BOS/EOS/PAD are `<|endoftext|>` (id 0).

    Without this, `configure_pad_token` adds a new `<|pad|>` token and an empty context
    does not get the single BOS that lm-eval uses.
    """
    eot = 0
    if hasattr(tokenizer, "convert_tokens_to_ids"):
        found = tokenizer.convert_tokens_to_ids("<|endoftext|>")
        if isinstance(found, int) and found >= 0:
            eot = found
    if getattr(tokenizer, "eos_token_id", None) is None:
        try:
            tokenizer.eos_token = "<|endoftext|>"
        except Exception:
            tokenizer.eos_token_id = eot
    if getattr(tokenizer, "eos_token_id", None) is None:
        tokenizer.eos_token_id = eot
    if getattr(tokenizer, "bos_token_id", None) is None:
        tokenizer.bos_token_id = tokenizer.eos_token_id
    if getattr(tokenizer, "pad_token_id", None) is None:
        try:
            tokenizer.pad_token = tokenizer.eos_token or "<|endoftext|>"
        except Exception:
            tokenizer.pad_token_id = tokenizer.eos_token_id
    return tokenizer


class _SlayerModule(torch.nn.Module):
    """`nn.Module` whose `forward` returns the logits of `slayer_model.Slayer`."""

    def __init__(self, slayer):
        super().__init__()
        self.slayer = slayer
        self.device = torch.device(slayer.device)
        self.dtype = slayer.dtype
        self.config = transformers.PretrainedConfig()
        self.config.model_type = "slayer"
        self.config.vocab_size = slayer.cfg.get("vocab", slayer.w["tok.weight"].shape[0])
        self.config.n_positions = slayer.blok

    def tie_weights(self):
        return

    def num_parameters(self, exclude_embeddings=False):
        return sum(t.numel() for t in self.slayer.w.values())

    def forward(self, input_ids, **kwargs):
        logits = self.slayer.logits(input_ids)
        return transformers.modeling_outputs.CausalLMOutput(logits=logits)

    @torch.no_grad()
    def generate(self, input_ids, attention_mask=None, max_length=None, stopping_criteria=None, **kwargs):
        """Greedy over the whole batch, until `max_length`, end of text or the lm-eval stopping criterion.

        The criterion gets the whole batch, as in `GenerationMixin`: a row past `until` keeps going until all rows
        finish, and `generate_until` cuts it at `until`. A row past end of text gets only that token, which lm-eval
        skips when decoding. Left padding does not enter the forward.
        """
        if kwargs.get("do_sample"):
            raise NotImplementedError("SlayerLM: generate_until supports greedy only (do_sample=False).")
        device = self.slayer.device
        output = input_ids.to(device)
        limit = 0 if max_length is None else int(max_length) - output.shape[1]
        finished = output.new_zeros(output.shape[0], dtype=torch.bool)
        rows = []
        for b in range(output.shape[0]):
            mask = None if attention_mask is None else attention_mask[b].to(device, dtype=torch.bool)
            real_tokens = output[b] if mask is None else output[b][mask]
            # Empty context: the forward starts from BOS, as `loglikelihood` in lm-eval; BOS does not reach the output.
            rows.append(real_tokens.view(1, -1) if real_tokens.numel() else output.new_full((1, 1), self.slayer.bos))
        for _ in range(limit):
            last_logits = torch.cat([self.slayer.logits(seq)[:, -1] for seq in rows])
            next_tokens = last_logits.argmax(dim=-1).masked_fill(finished, self.slayer.bos)
            finished = finished | (next_tokens == self.slayer.bos)
            rows = [torch.cat([seq, n.view(1, 1)], dim=1) for seq, n in zip(rows, next_tokens)]
            output = torch.cat([output, next_tokens[:, None]], dim=1)
            if bool(finished.all()):
                break
            if stopping_criteria is not None:
                stop = stopping_criteria(output, last_logits)
                if bool(stop.all() if hasattr(stop, "all") else all(stop)):
                    break
        return output.to(input_ids.device)


def _slayer_cfg(pretrained, subfolder=""):
    if not isinstance(pretrained, str):
        return None
    cfg_file = Path(pretrained) / subfolder / "config.json" if subfolder else Path(pretrained) / "config.json"
    if not cfg_file.is_file():
        return None
    raw = json.loads(cfg_file.read_text(encoding="utf-8"))
    if "model_type" in raw or "n_embd" not in raw:
        return None
    return raw


@register_model("slayer")
class SlayerLM(HFLM):
    """Slayer 1B in lm-eval. `pretrained` is a local directory with `config.json`, `tokenizer.json` and weights."""

    def __init__(self, pretrained, device=None, dtype="float32", max_length=None, **kwargs):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self._is_slayer = False
        self._slayer_cfg = None
        super().__init__(pretrained=pretrained, device=device, dtype=dtype, max_length=max_length, **kwargs)
        if self._is_slayer and max_length is None:
            self._max_length = int(self._slayer_cfg["block"])

    def _get_config(self, pretrained, revision="main", trust_remote_code=False, gguf_file=None, subfolder=""):
        raw = _slayer_cfg(pretrained, subfolder)
        if raw is None:
            return super()._get_config(pretrained, revision=revision, trust_remote_code=trust_remote_code,
                                        gguf_file=gguf_file, subfolder=subfolder)
        self._is_slayer = True
        self._slayer_cfg = raw
        cfg = transformers.PretrainedConfig()
        cfg.model_type = "slayer"
        cfg.vocab_size = raw.get("vocab")
        self._config = cfg

    def _create_tokenizer(self, pretrained, tokenizer, revision="main", trust_remote_code=False,
                          use_fast_tokenizer=True, gguf_file=None, add_bos_token=False, subfolder=""):
        if self._is_slayer and not tokenizer and isinstance(pretrained, str):
            # AutoTokenizer.from_pretrained calls AutoConfig and fails without model_type (transformers 4.57).
            tokenizer_file = Path(pretrained) / "tokenizer.json"
            self.tokenizer = transformers.PreTrainedTokenizerFast(tokenizer_file=str(tokenizer_file))
            set_slayer_tokens(self.tokenizer)
            return
        super()._create_tokenizer(pretrained, tokenizer, revision=revision, trust_remote_code=trust_remote_code,
                                  use_fast_tokenizer=use_fast_tokenizer, gguf_file=gguf_file,
                                  add_bos_token=add_bos_token, subfolder=subfolder)
        if self._is_slayer:
            set_slayer_tokens(self.tokenizer)

    def _create_model(self, pretrained, dtype=None, **kwargs):
        if not self._is_slayer:
            return super()._create_model(pretrained=pretrained, dtype=dtype, **kwargs)
        unused = sorted(k for k, v in kwargs.items()
                        if k != "gpus" and (k not in UNUSED_LOAD_ARGS or v != UNUSED_LOAD_ARGS[k]))
        if unused:
            raise ValueError(f"SlayerLM: {', '.join(unused)} not supported, `pretrained` is a local directory")
        if dtype in (None, "auto", "float32"):
            dt = torch.float32
        elif isinstance(dtype, torch.dtype):
            dt = dtype
        else:
            dt = get_dtype(dtype)
        slayer = slayer_model.Slayer(pretrained, device=str(self.device), dtype=dt)
        self._model = _SlayerModule(slayer)
