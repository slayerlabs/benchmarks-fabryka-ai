"""Łatka na train_gpt_ref_r23.py (repo HF SlayerLab/Slayer1B-1.06): harmonogram z env + resume przez CPU.

python wygaszanie/latka_trenera.py <train_gpt_ref_r23.py> <wyjście train_wyg.py>

Zmiany (każda kotwica musi wystąpić dokładnie raz, inaczej STOP):
1. `_lr_sched`: WYGASZANIE_SCHED=stala -> a.lr; =liniowa -> a.lr * (a.steps - s) / (a.steps - WYGASZANIE_START),
   czyli 6e-4 w kroku startu i liniowo do 0 w kroku a.steps. Bez env: kod Arka bez zmian.
2. resume: checkpoint ładowany na CPU (8,9 GB na GPU obok modelu i optymalizatora nie mieści się w 24 GB),
   potem `del ck`.
"""

import sys
from pathlib import Path

ZMIANY = [
    ("    def _lr_sched(s):\n",
     "    def _lr_sched(s):\n"
     "        _wyg = os.environ.get(\"WYGASZANIE_SCHED\")\n"
     "        if _wyg == \"stala\":\n"
     "            return a.lr\n"
     "        if _wyg == \"liniowa\":\n"
     "            _s0 = int(os.environ[\"WYGASZANIE_START\"])\n"
     "            return a.lr * max(0.0, (a.steps - s) / max(1, a.steps - _s0))\n"),
    ("        ck = torch.load(ckpt_path, map_location=device, weights_only=True)  # r20\n",
     "        ck = torch.load(ckpt_path, map_location=\"cpu\", weights_only=True)  # r20\n"),
    ("        log(f\"RESUME @ {start_step}\")\n",
     "        log(f\"RESUME @ {start_step}\")\n"
     "        del ck\n"
     "        torch.cuda.empty_cache()\n"),
]


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    t = src.read_text()
    assert "\nimport os" in t or "import os," in t or ", os" in t, "brak import os"
    for stare, nowe in ZMIANY:
        n = t.count(stare)
        if n != 1:
            raise SystemExit(f"STOP: kotwica wystąpiła {n} razy: {stare!r}")
        t = t.replace(stare, nowe)
    dst.write_text(t)
    print(f"łatka OK: {dst}")


if __name__ == "__main__":
    main()
