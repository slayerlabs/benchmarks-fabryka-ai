"""Download one trainer checkpoint and log revision, size, time, speed and SHA-256 against the HF LFS id.

python benchmarks/blimp/download_checkpoint.py <repo> <step> <dir> [--log czasy.jsonl]
  -> <dir>/ckpt_<step>.pt ; one JSON line to stdout and to --log
Exit code 3 when the SHA-256 of the file differs from the LFS object id of the listing.
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def main(argv=None):
    from huggingface_hub import HfApi, hf_hub_download
    p = argparse.ArgumentParser()
    p.add_argument("repo")
    p.add_argument("krok", type=int)
    p.add_argument("katalog")
    p.add_argument("--log")
    a = p.parse_args(argv)
    api = HfApi()
    nazwa = f"ckpt_{a.krok}.pt"
    rew = api.model_info(a.repo).sha
    info = next(iter(api.get_paths_info(a.repo, [nazwa], revision=rew)))
    t0 = time.time()
    plik = Path(hf_hub_download(a.repo, nazwa, revision=rew, local_dir=a.katalog))
    t1 = time.time()
    sha = sha256(plik)
    t2 = time.time()
    rozmiar = plik.stat().st_size
    out = {"etap": "pobranie", "repo": a.repo, "rewizja": rew, "krok": a.krok, "plik": str(plik), "bajty": rozmiar,
           "s": round(t1 - t0, 1), "MB_s": round(rozmiar / 1e6 / max(t1 - t0, 1e-9), 1),
           "sha256": sha, "sha256_s": round(t2 - t1, 1), "lfs_oid": info.lfs.sha256 if info.lfs else None}
    out["zgodny_z_lfs"] = out["sha256"] == out["lfs_oid"]
    linia = json.dumps(out)
    print(linia, flush=True)
    if a.log:
        with open(a.log, "a") as f:
            f.write(linia + "\n")
    return 0 if out["zgodny_z_lfs"] else 3


if __name__ == "__main__":
    sys.exit(main())
