"""Skan nakładania n-gramów słów (13 i, informacyjnie, 8) zestawu poleceń wobec GSM8K, ARC, OpenBookQA, HumanEval, MBPP.

python -I code/skazenie.py <katalog_zbiorow_humaneval_mbpp>   (środowisko z pyarrow, np. research/.venv-eval)
  -> wyniki/skazenie.json

Tekst pozycji = polecenie + wzorzec (+ testy w `kod`); słowa = \\w+ po małych literach (jak ocena.slowa).
Benchmarki z lokalnego cache HF (rewizje w ZRODLA) i z plików pobranych do katalogu z argumentu.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import pyarrow.parquet as pq

BADANIE = Path(__file__).resolve().parent.parent
HF = Path.home() / ".cache/huggingface/hub"


def slowa(t):
    return re.findall(r"\w+", t.lower())


def ngramy(t, n):
    s = slowa(t)
    return {tuple(s[i:i + n]) for i in range(len(s) - n + 1)}


def teksty(zbior, rows):
    for r in rows:
        if zbior == "gsm8k":
            yield r["question"] + " " + r["answer"]
        elif zbior.startswith("arc"):
            yield r["question"] + " " + " ".join(r["choices"]["text"])
        elif zbior == "openbookqa":
            yield r["question_stem"] + " " + " ".join(r["choices"]["text"])
        elif zbior == "humaneval":
            yield r["prompt"] + " " + r["canonical_solution"] + " " + r["test"]
        elif zbior == "mbpp":
            yield r["text"] + " " + r["code"] + " " + " ".join(r["test_list"])


def main():
    zew = Path(sys.argv[1])
    zrodla = {
        "gsm8k": [HF / f"datasets--openai--gsm8k/snapshots/740312add88f781978c0658806c59bc2815b9866/main/{s}-00000-of-00001.parquet" for s in ("train", "test")],
        "arc": [HF / f"datasets--allenai--ai2_arc/snapshots/210d026faf9955653af8916fad021475a3f00453/{c}/{s}-00000-of-00001.parquet"
                for c in ("ARC-Challenge", "ARC-Easy") for s in ("train", "validation", "test")],
        "openbookqa": [HF / f"datasets--allenai--openbookqa/snapshots/388097ea7776314e93a529163e0fea805b8a6454/main/{s}-00000-of-00001.parquet" for s in ("train", "validation", "test")],
        "humaneval": [zew / "he/test.parquet"],
        "mbpp": [zew / "mbpp/full.parquet"],
    }
    rewizje = {"humaneval": "openai/openai_humaneval@7dce6050", "mbpp": "google-research-datasets/mbpp@4bb6404f (full/test)"}
    pozycje = [json.loads(x) for x in (BADANIE / "dane" / "polecenia.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    wynik = dict(zbiory={}, n_pozycji=len(pozycje), trafienia={})
    for n in (13, 8):
        wynik["trafienia"][str(n)] = {}
    for zb, pliki in zrodla.items():
        g = {13: set(), 8: set()}
        n_rek = 0
        meta = []
        for p in pliki:
            if not p.exists():
                sys.exit(f"brak pliku zbioru: {p}")
            rows = pq.read_table(p).to_pylist()
            n_rek += len(rows)
            meta.append(dict(plik=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest(), n=len(rows)))
            for t in teksty("arc" if zb == "arc" else zb, rows):
                for n in (13, 8):
                    g[n] |= ngramy(t, n)
        wynik["zbiory"][zb] = dict(rekordy=n_rek, pliki=meta, rewizja=rewizje.get(zb, "cache HF, sha w ścieżce"))
        for n in (13, 8):
            traf = []
            for poz in pozycje:
                t = poz["polecenie"] + " " + poz["wzorzec"] + " " + poz.get("testy", "")
                wsp = ngramy(t, n) & g[n]
                if wsp:
                    traf.append(dict(id=poz["id"], wspolne=[" ".join(x) for x in sorted(wsp)][:5]))
            wynik["trafienia"][str(n)][zb] = traf
    (BADANIE / "wyniki" / "skazenie.json").write_text(json.dumps(wynik, ensure_ascii=False, indent=1), encoding="utf-8")
    for n in ("13", "8"):
        print(n, {zb: len(v) for zb, v in wynik["trafienia"][n].items()})


if __name__ == "__main__":
    main()
