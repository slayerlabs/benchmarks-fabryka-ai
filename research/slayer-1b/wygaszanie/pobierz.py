"""Pobranie na instancji: wagi 1.06 i 1.03, checkpointy trenera 13848 i 13800, zbiory ewaluacji.

python wygaszanie/pobierz.py /workspace   -> /workspace/{m106,m103,ckpt}, pobrane.json (rewizje, sha256)
"""

import hashlib
import json
import sys
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download, snapshot_download

R106 = "ef81be58742544ad32e1afab38db011fec209609"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def main():
    baza = Path(sys.argv[1])
    api = HfApi()
    out = {}
    snapshot_download("SlayerLab/Slayer1B-1.06", revision=R106, local_dir=baza / "m106")
    out["m106"] = {"repo": "SlayerLab/Slayer1B-1.06", "rewizja": R106}
    r103 = api.model_info("SlayerLab/Slayer1B-1.03").sha
    snapshot_download("SlayerLab/Slayer1B-1.03", revision=r103, local_dir=baza / "m103",
                      allow_patterns=["*.json", "*.safetensors", "*.py", "SHA256SUMS"])
    out["m103"] = {"repo": "SlayerLab/Slayer1B-1.03", "rewizja": r103}
    rck = api.model_info("SlayerLab/Slayer1B-1.06-checkpoints").sha
    for krok in (13848, 13800):
        p = hf_hub_download("SlayerLab/Slayer1B-1.06-checkpoints", f"ckpt_{krok}.pt", revision=rck,
                            local_dir=baza / "ckpt")
        out[f"ckpt_{krok}"] = {"repo": "SlayerLab/Slayer1B-1.06-checkpoints", "rewizja": rck, "sha256": sha(p),
                               "rozmiar": Path(p).stat().st_size}
    cfg = json.loads((baza / "m106" / "config.json").read_text())
    out["ckpt_13848_zgodny_z_config_1.06"] = out["ckpt_13848"]["sha256"] == cfg.get("ckpt_sha256")
    out["trainer_sha256"] = sha(baza / "m106" / "train_gpt_ref_r23.py")
    out["trainer_zgodny_z_config"] = out["trainer_sha256"] == cfg.get("trainer_sha256")
    (baza / "pobrane.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
