"""Freezes reference logits of the official Slayer code for test_forward_matches_official_reference.

The official forward is the GPT class of train_gpt_ref_r23.py from the model repo on HF, loaded by its own
load_slayer.py. It runs on the small random checkpoint from tests/test_lm_eval_slayer.py, so no weights are needed.

    hf download SlayerLab/Slayer1B-1.06 --revision ef81be58742544ad32e1afab38db011fec209609 \
        --include "*.py" "config.json" --local-dir models/slayer-1.06-code
    .venv-eval/bin/python tests/make_slayer_reference.py models/slayer-1.06-code
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import torch
from safetensors.torch import load_file

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_lm_eval_slayer as t  # noqa: E402

REVISION = "ef81be58742544ad32e1afab38db011fec209609"


def main(hf_dir):
    hf_dir = Path(hf_dir)
    official_cfg = json.loads((hf_dir / "config.json").read_text(encoding="utf-8"))
    trainer = (hf_dir / official_cfg["trainer"]).read_bytes()
    trainer_sha = hashlib.sha256(trainer).hexdigest()
    if trainer_sha != official_cfg["trainer_sha256"]:
        sys.exit(f"{official_cfg['trainer']} sha256 {trainer_sha} differs from config.json")
    sys.path.insert(0, str(hf_dir))
    import load_slayer

    with tempfile.TemporaryDirectory() as tmp:
        model_dir, cfg = t.reference_model_dir(tmp)
        weights = load_file(str(model_dir / "model.safetensors"))
    model = load_slayer.build(cfg, str(hf_dir))
    state = dict(weights, **{"head.weight": weights["tok.weight"]})
    model.load_state_dict(state, strict=True)
    model.float().eval()

    g = torch.Generator().manual_seed(2)
    ids = torch.randint(1, cfg["vocab"], (2, cfg["block"]), generator=g)
    with torch.no_grad():
        logits, _ = model(ids)
    out = {
        "source": f"SlayerLab/Slayer1B-1.06@{REVISION} load_slayer.build + {official_cfg['trainer']}",
        "trainer_sha256": trainer_sha,
        "torch": torch.__version__,
        "config": cfg,
        "weights_sha256": t._weights_sha256(weights),
        "ids": ids.tolist(),
        "logits": [[[round(v, 6) for v in row] for row in seq] for seq in logits.tolist()],
    }
    t.REFERENCE.write_text(json.dumps(out, separators=(",", ":")) + "\n", encoding="utf-8")
    print(t.REFERENCE, tuple(logits.shape), f"std {logits.std().item():.3f}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python tests/make_slayer_reference.py <dir with load_slayer.py, train_gpt_ref_r23.py, config.json>")
    main(sys.argv[1])
