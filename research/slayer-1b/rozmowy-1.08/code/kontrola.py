"""Kontrola narzędzia: ARC-Challenge test i OpenBookQA test 0-shot dla Slayer1B-1.08 tym samym kodem logprob
(modele.logprob_ciagu), który liczy BPB w badaniu. Cel: acc i acc_norm z EVALUATION.json karty 1.08.

Krok 1 (środowisko z pyarrow, np. research/.venv-eval):
  python -I code/kontrola.py przygotuj <katalog_wyj>   # parquet z cache HF -> jsonl poza repo + sha256 parquetów
Krok 2 (środowisko modeli):
  python -I code/kontrola.py licz <katalog_wyj> [--limit N]  -> wyniki/surowe/kontrola_slayer.jsonl

Prompty jak w EVALUATION.json/protocol/task_protocols (lm-eval): ARC ctx='Question: {question}\\nAnswer:',
OBQA ctx=question_stem, ciąg=' '+tekst opcji; acc = argmax sumy log p; acc_norm = argmax (log p / len(tekst opcji
w znakach, bez spacji)), jak lm-eval multiple_choice; remis -> pierwsza opcja (np.argmax).
"""
import hashlib
import json
import sys
import time
from pathlib import Path

HF = Path.home() / ".cache/huggingface/hub"
ZRODLA = {
    "arc_challenge": HF / "datasets--allenai--ai2_arc/snapshots/210d026faf9955653af8916fad021475a3f00453/ARC-Challenge/test-00000-of-00001.parquet",
    "openbookqa": HF / "datasets--allenai--openbookqa/snapshots/388097ea7776314e93a529163e0fea805b8a6454/main/test-00000-of-00001.parquet",
}


def przygotuj(wyj):
    import pyarrow.parquet as pq
    wyj.mkdir(parents=True, exist_ok=True)
    meta = {}
    for zad, sciezka in ZRODLA.items():
        meta[zad] = dict(parquet=str(sciezka), sha256=hashlib.sha256(sciezka.read_bytes()).hexdigest())
        rows = pq.read_table(sciezka).to_pylist()
        with open(wyj / f"{zad}.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                if zad == "arc_challenge":
                    ctx = f"Question: {r['question']}\nAnswer:"
                    gold = r["choices"]["label"].index(r["answerKey"])
                else:
                    ctx = r["question_stem"]
                    gold = r["choices"]["label"].index(r["answerKey"].lstrip())
                f.write(json.dumps(dict(id=r["id"], ctx=ctx, opcje=r["choices"]["text"], gold=gold), ensure_ascii=False) + "\n")
        meta[zad]["n"] = len(rows)
    (wyj / "meta.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta, indent=1))


def argmax(xs):
    return max(range(len(xs)), key=lambda i: (xs[i], -i))


def licz(wej, limit):
    kod = Path(__file__).resolve().parent
    sys.path.insert(0, str(kod))
    import modele
    from generuj import BADANIE
    model = modele.wczytaj("slayer")
    meta = json.loads((wej / "meta.json").read_text())
    wyj = BADANIE / "wyniki" / "surowe" / f"kontrola_slayer{'_dym' if limit else ''}.jsonl"
    t0 = time.time()
    with open(wyj, "w", encoding="utf-8") as f:
        f.write(json.dumps(dict(naglowek=True, meta=meta, model="SlayerLab/Slayer1B-1.08"), ensure_ascii=False) + "\n")
        for zad in ZRODLA:
            rows = [json.loads(x) for x in (wej / f"{zad}.jsonl").read_text(encoding="utf-8").splitlines()]
            if limit:
                rows = rows[:limit]
            for r in rows:
                lps = []
                for o in r["opcje"]:
                    lp, n_tok, zg = modele.logprob_ciagu(model, r["ctx"], " " + o)
                    lps.append(lp)
                norm = [lp / len(o) for lp, o in zip(lps, r["opcje"])]
                f.write(json.dumps(dict(zadanie=zad, id=r["id"], gold=r["gold"], logprob=lps,
                                        acc=int(argmax(lps) == r["gold"]), acc_norm=int(argmax(norm) == r["gold"])),
                                   ensure_ascii=False) + "\n")
            print(zad, "gotowe", round(time.time() - t0), "s", flush=True)
    print("KONIEC kontrola", round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    tryb, katalog = sys.argv[1], Path(sys.argv[2])
    if tryb == "przygotuj":
        przygotuj(katalog)
    else:
        licz(katalog, int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None)
