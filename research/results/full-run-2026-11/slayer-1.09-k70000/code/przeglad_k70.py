"""Rows of step 70 000 in the run's `manifest.jsonl` (SE) and `przeglad.jsonl` (review), as the report generator
writes them for every other row, without regenerating the run's README.

    python przeglad_k70.py <results/full-run-2026-11>

- SE: `tools/ewaluacja/raport.py` `wczytaj_wyniki` (the statistic of the report: EWoK over templates, MultiBLiMP over
  items), in the unit of the file. Checked first on step 40 000: it must give that label's manifest SE exactly.
- Review row: the fields of the step 40 000 row of the same test (baseline b, lm_eval, contamination label), flag
  `ok`, the label of this measurement as the only note, not in the CodeSOTA table (a checkpoint in training).
Refuses when `przeglad.jsonl` already has rows of step 70 000.
"""
import json
import sys
from pathlib import Path

A, REF = "slayer1b-1.09-k70000", "slayer1b-1.09-k40000"
NOTE = "1.09, step 70 000, training in progress, preliminary result (RTX 4090, slayer-1.09-k70000/PROTOKOL.md)"


def rows(p: Path) -> list:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def write(p: Path, rs: list) -> None:
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rs) + "\n", encoding="utf-8")


def main() -> int:
    run = Path(sys.argv[1]).resolve()
    sys.path[:0] = [str(run.parent.parent / "tools" / "ewaluacja"), str(run.parent.parent / "common")]
    import raport

    se = {(r["benchmark"], r["model"]): (None if r["se"] is None else r["se"] * r["skala_w_pliku"])
          for r in raport.wczytaj_wyniki(run) if r["model"] in (A, REF)}
    manifest = rows(run / "manifest.jsonl")
    for r in manifest:
        if r["model"] == REF and se[(r["benchmark"], REF)] != r["se"]:
            raise SystemExit(f"{r['benchmark']}: wczytaj_wyniki gives {se[(r['benchmark'], REF)]} for {REF}, "
                             f"manifest has {r['se']}")
    for r in manifest:
        if r["model"] == A:
            r["se"] = se[(r["benchmark"], A)]
    przeglad = rows(run / "przeglad.jsonl")
    if any(r.get("model") == A for r in przeglad):
        raise SystemExit(f"przeglad.jsonl already has rows of {A}")
    ref = {r["benchmark"]: r for r in przeglad if r.get("model") == REF}
    for r in manifest:
        if r["model"] != A:
            continue
        b = ref[r["benchmark"]]
        przeglad.append({"benchmark": r["benchmark"], "zadanie": r["zadanie"], "model": A, "metryka": r["metryka"],
                         "wartosc": r["wartosc"], "se": r["se"], "n": r["n"], "dtype": r["dtype"], "flaga": "ok",
                         "uwagi": [NOTE], "kontaminacja": b["kontaminacja"], "lm_eval": b["lm_eval"],
                         "baza_b": b["baza_b"], "w_tabeli_codesota": False})
    write(run / "manifest.jsonl", manifest)
    write(run / "przeglad.jsonl", przeglad)
    print({r["benchmark"]: r["se"] for r in manifest if r["model"] == A})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
