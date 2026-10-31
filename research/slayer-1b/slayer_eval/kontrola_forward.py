"""Official Slayer forward vs our scored run, on the 200 pairs of the sha256 Space panel.

The official model (`load_slayer.py` + `train_gpt_ref_r23.GPT` from the HF repo, CPU float32, batch 1) scores
each sentence of the panel; the result is compared with our per-pair log-likelihoods (slayer_model.py on MPS,
batch 64, `wyniki/blimp/raw/1.06.jsonl.gz`). Runs over CPU thread counts, with or without feeding the unscored
last token, and with a float32 or float64 sum of the token log-probs: all three move the max |d loglik| in its
second digit, so the max is reported as a range.

  huggingface-cli download SlayerLab/Slayer1B-1.06 --revision ef81be58742544ad32e1afab38db011fec209609 --local-dir <dir>
  BLIMP_DIR=<blimp snapshot> python slayer_eval/kontrola_forward.py --model <dir> \\
      --wyniki wyniki/blimp/raw/1.06.jsonl.gz --watki 1,6 --sumy float32,float64
  -> wyniki/blimp/kontrola_forward.json (then blimp.py zbierz, liczby.py, blimp.py raport)
"""
import argparse
import importlib.util
import json
import os
import platform
import sys
import time
from pathlib import Path

KATALOG = Path(__file__).resolve().parent
KORZEN = KATALOG.parent
sys.path.insert(0, str(KATALOG))

import blimp as B  # noqa: E402

WEJSCIA = ("bez_ostatniego", "pelne")
SUMY = ("float32", "float64")


def parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--model", required=True, help="directory of SlayerLab/Slayer1B-1.06 (load_slayer.py, tokenizer.json, weights)")
    p.add_argument("--wyniki", default=str(KORZEN / "wyniki/blimp/raw/1.06.jsonl.gz"),
                   help="our per-pair results of Slayer 1.06 (blimp.jsonl or raw .jsonl.gz)")
    p.add_argument("--dane", default=None, help="BLiMP snapshot directory (default: BLIMP_DIR or the HF cache)")
    p.add_argument("--watki", default=f"1,{os.cpu_count()}", help="comma-separated CPU thread counts")
    p.add_argument("--sumy", default=",".join(SUMY), help="sum precision of token log-probs: float32,float64")
    p.add_argument("--wejscia", default=",".join(WEJSCIA), help="bez_ostatniego (last token not fed), pelne")
    p.add_argument("--wyjscie", default=str(KORZEN / "wyniki/blimp/kontrola_forward.json"))
    return p


def argumenty(argv=None):
    a = parser().parse_args(argv)
    a.watki = sorted({int(x) for x in a.watki.split(",")})
    a.sumy = a.sumy.split(",")
    a.wejscia = a.wejscia.split(",")
    for nazwa, wart, dozw in (("--sumy", a.sumy, SUMY), ("--wejscia", a.wejscia, WEJSCIA)):
        zle = [x for x in wart if x not in dozw]
        if zle:
            parser().error(f"{nazwa}: {zle} not in {list(dozw)}")
    if min(a.watki) < 1:
        parser().error("--watki: thread counts must be >= 1")
    return a


SPRAWDZANE = ("model.safetensors", "tokenizer.json", "load_slayer.py", "train_gpt_ref_r23.py", "config.json")


def sprawdz_sumy(katalog, pliki=SPRAWDZANE):
    """Check the files of --model against the SHA256SUMS shipped in the model repo; SystemExit naming the file
    on a missing SHA256SUMS, a file it does not list, a missing file or a different hash."""
    import hashlib
    katalog = Path(katalog)
    sumy_plik = katalog / "SHA256SUMS"
    if not sumy_plik.exists():
        raise SystemExit(f"{sumy_plik}: missing; download the whole SlayerLab/Slayer1B-1.06 repo at the pinned revision")
    sumy = {}
    for l in sumy_plik.read_text().splitlines():
        if l.strip():
            h, nazwa = l.split(maxsplit=1)
            sumy[nazwa.strip().lstrip("*")] = h.lower()
    bledy = []
    for nazwa in pliki:
        p = katalog / nazwa
        if nazwa not in sumy:
            bledy.append(f"{nazwa}: not listed in {sumy_plik}")
        elif not p.exists():
            bledy.append(f"{p}: missing")
        else:
            h = hashlib.sha256()
            with open(p, "rb") as f:
                for blok in iter(lambda: f.read(1 << 20), b""):
                    h.update(blok)
            if h.hexdigest() != sumy[nazwa]:
                bledy.append(f"{p}: sha256 {h.hexdigest()} != {sumy[nazwa]} in SHA256SUMS")
    if bledy:
        raise SystemExit("model files do not match SHA256SUMS, nothing computed:\n  " + "\n  ".join(bledy))
    return {n: sumy[n] for n in pliki}


BOS = 0  # <|endoftext|> in the Slayer tokenizer: the one unscored prefix token (METHOD.md, lm-eval blimp)


def ll_zdania(model, encode, zdanie, wejscie, sumy):
    """Summed log-prob of " " + sentence after one BOS, as lm-eval blimp scores it: ids = [BOS] + encode(" " + s),
    the logits at position t predict ids[t + 1], so positions 0 .. len(ids) - 2 are scored. wejscie: feed all
    ids ("pelne") or all but the last ("bez_ostatniego"; its logits are never scored). -> {sum dtype: value}."""
    import torch
    ids = [BOS] + encode(" " + zdanie)
    out = model(torch.tensor([ids[:-1] if wejscie == "bez_ostatniego" else ids]))
    logits = out[0] if isinstance(out, tuple) else out
    lp = torch.log_softmax(logits[0, :len(ids) - 1].float(), -1)[torch.arange(len(ids) - 1), torch.tensor(ids[1:])]
    return {s: (lp.sum().item() if s == "float32" else sum(v.item() for v in lp)) for s in sumy}


def przebieg(roznice, przestawione, watki, wejscie, suma):
    """One run: |our ll - official ll| per sentence -> summary row."""
    return {"watki_cpu": watki, "wejscie": wejscie, "suma": suma, "max_abs_roznica_ll": max(roznice),
            "srednia_abs_roznica_ll": sum(roznice) / len(roznice), "przestawione_pary": przestawione}


def podsumuj(przebiegi, pary, wersje):
    """kontrola_forward.json: ranges over the runs (read by blimp.py zbierz -> LICZBY.json)."""
    mx = [p["max_abs_roznica_ll"] for p in przebiegi]
    sr = [p["srednia_abs_roznica_ll"] for p in przebiegi]
    return {"zdania": 2 * pary, "pary": pary,
            "max_abs_roznica_ll": [min(mx), max(mx)], "srednia_abs_roznica_ll": [min(sr), max(sr)],
            "przestawione_pary": max(p["przestawione_pary"] for p in przebiegi),
            "przebiegi": przebiegi, "wersje": wersje,
            "opis": f"official load_slayer.py GPT (HF repo @ ef81be58), CPU float32, batch 1, vs slayer_model.py on "
                    f"MPS, batch 64 (raw/1.06.jsonl.gz); sha256 panel pairs; {len(przebiegi)} runs: CPU threads x "
                    "input with or without the last token x float32 or float64 sum of token log-probs"}


def main(argv=None):
    a = argumenty(argv)
    sprawdz_sumy(a.model)  # before any import of the model code
    import torch
    import tokenizers
    from tokenizers import Tokenizer
    model_dir = Path(a.model)
    sys.path.insert(0, str(model_dir))  # load_slayer imports train_gpt_ref_r23 from its own directory
    spec = importlib.util.spec_from_file_location("load_slayer", model_dir / "load_slayer.py")
    ls = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ls)
    model = ls.load(str(model_dir))
    tok = Tokenizer.from_file(str(model_dir / "tokenizer.json"))

    def encode(s):
        return tok.encode(s, add_special_tokens=False).ids
    docs = B.wczytaj(a.dane)
    panel = B.panel(docs, "sha256")
    nasze = B.wczytaj_wyniki(a.wyniki)
    przebiegi = []
    with torch.no_grad():
        for watki in a.watki:
            torch.set_num_threads(watki)
            for wejscie in a.wejscia:
                t0 = time.time()
                roz = {s: [] for s in a.sumy}
                przest = {s: 0 for s in a.sumy}
                for d in panel:
                    ll = {s: [] for s in a.sumy}
                    for zd in d["opcje"]:
                        wart = ll_zdania(model, encode, zd, wejscie, a.sumy)
                        for s in a.sumy:
                            ll[s].append(wart[s])
                    n = nasze[d["id"]]["ll"]
                    for s in a.sumy:
                        roz[s] += [abs(ll[s][0] - n[0]), abs(ll[s][1] - n[1])]
                        przest[s] += B.trafienie_pary(d, {"ll": ll[s]}) != B.trafienie_pary(d, nasze[d["id"]])
                for s in a.sumy:
                    przebiegi.append(przebieg(roz[s], przest[s], watki, wejscie, s))
                print(f"threads {watki}, {wejscie}: {time.time() - t0:.0f}s", przebiegi[-len(a.sumy):], flush=True)
    wersje = {"python": platform.python_version(), "torch": torch.__version__, "tokenizers": tokenizers.__version__,
              "maszyna": platform.platform()}
    wynik = podsumuj(przebiegi, len(panel), wersje)
    Path(a.wyjscie).write_text(json.dumps(wynik, indent=1) + "\n")
    print(json.dumps({k: v for k, v in wynik.items() if k != "przebiegi"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
