"""Summary of a central-run output recomputed from its per-question samples with the current code, without a model.

For one-config MC tasks of common/ewaluuj.py: reads <DIR>/probki/<T>_space.jsonl(.gz), runs ewaluuj.podsumuj_wariant
and rewrites only what it computes from the samples: `dodatkowe.space` metrics and baselines, the observation's
ci95 and reference, and `references_sha256`. Value, n, sample digests and run provenance stay; results_rozszerzone.json
gets `podsumowanie_ponowne`. Used when the statistics change after a run (SE K of `+klastry`, the constant-answer
baseline of `mc`); a changed value means the samples or the scoring differ and stops the tool.
  python tools/podsumuj_ponownie.py DIR...   (DIR = results/central-run/<benchmark>/<model>)
"""
import gzip
import json
import sys
from pathlib import Path
from types import SimpleNamespace

KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "common"))
import ewaluuj as E  # noqa: E402
import metryki as M  # noqa: E402
import zadania as Z  # noqa: E402

POWOD = "SE K dla testów +klastry i stała odpowiedź testów mc (METODOLOGIA, „Typy testów”)"


def wczytaj_probki(katalog, task_id, wariant="space"):
    for nazwa, otworz in ((f"{task_id}_{wariant}.jsonl.gz", gzip.open), (f"{task_id}_{wariant}.jsonl", open)):
        plik = katalog / "probki" / nazwa
        if plik.exists():
            with otworz(plik, "rt", encoding="utf-8") as f:
                return [json.loads(w) for w in f if w.strip()]
    raise SystemExit(f"{katalog}: no probki/{task_id}_{wariant}.jsonl(.gz)")


def podsumuj(katalog):
    """Recomputed summary of one output directory; returns (results.json, results_rozszerzone.json) as dicts."""
    wyniki = json.loads((katalog / "results.json").read_text())
    roz = json.loads((katalog / "results_rozszerzone.json").read_text())
    obs, obs_r = wyniki["observations"][0], roz["observations"][0]
    task_id = obs["task_id"]
    meta = Z.ZADANIA[task_id]
    warianty = Z.konfiguracje(task_id, roz.get("dane", "hf"))
    nazwy = [w for w, _ in warianty]
    if meta["rodzaj"] != "mc" or len(nazwy) != len(set(nazwy)):
        raise SystemExit(f"{katalog}: {task_id} is not a one-config MC task")
    for wariant, cfg in warianty:  # space and, when the run logged it, cloze
        if wariant == "space" or list((katalog / "probki").glob(f"{task_id}_{wariant}.jsonl*")):
            probki = wczytaj_probki(katalog, task_id, wariant)
            # one config: the task object only gives the member weight, so a stand-in with its documents does
            podsumowanie = E.podsumuj_wariant(meta, [(meta["task"], cfg, SimpleNamespace(eval_docs=probki), probki)])
            stare = obs_r["dodatkowe"][wariant]
            stare.update({k: scal(stare.get(k), v) for k, v in podsumowanie.items()})
    nowe = obs_r["dodatkowe"]["space"]
    glowna = nowe.get("glowna") or nowe[meta.get("klucz", "acc")]
    if abs(M.skala(glowna["value"], meta["unit"]) - obs["value"]) > 1e-9:
        raise SystemExit(f"{katalog}: value {obs['value']} != recomputed {glowna['value']}")
    digests = {"source_id": obs["source_id_digest"], "results": obs["results_sha256"], "runner": obs["runner_sha256"]}
    nowa = M.obserwacja(task_id, meta, obs["model_id"], obs["protocol_id"], glowna, nowe["bazy"],
                        obs["n_population"], obs["n_selected"], digests)
    for o in (obs, obs_r):
        o["ci95"], o["reference"] = scal(o["ci95"], nowa["ci95"]), scal(o["reference"], nowa["reference"])
    # the run hashed {task: bazy}; old numbers kept above give the old hash back when b did not change
    referencje = M.sha256_tekstu(json.dumps({task_id: nowe["bazy"]}, sort_keys=True))
    for d in (wyniki, roz):
        d["provenance"]["references_sha256"] = referencje
    roz["podsumowanie_ponowne"] = {"narzedzie": "tools/podsumuj_ponownie.py", "powod": POWOD}
    return wyniki, roz


def scal(stare, nowe):
    """The recomputed tree, keeping each old number that differs only by float rounding (no noise in the diff)."""
    if isinstance(stare, dict) and isinstance(nowe, dict):
        return {k: scal(stare.get(k), v) for k, v in nowe.items()}
    if isinstance(stare, list) and isinstance(nowe, list) and len(stare) == len(nowe):
        return [scal(a, b) for a, b in zip(stare, nowe)]
    return stare if stare is not None and not rozne(stare, nowe) else nowe


def rozne(a, b, tol=1e-12):
    """JSON trees differ beyond float rounding (the last digit of a mean summed in another order is not a change)."""
    if isinstance(a, float) and isinstance(b, (int, float)) or isinstance(b, float) and isinstance(a, (int, float)):
        return abs(a - b) > tol * max(1.0, abs(a), abs(b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() != b.keys() or any(rozne(a[k], b[k], tol) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) != len(b) or any(rozne(x, y, tol) for x, y in zip(a, b))
    return a != b


def main(argv=None):
    for k in map(Path, argv if argv is not None else sys.argv[1:]):
        stare = json.loads((k / "results_rozszerzone.json").read_text())["observations"][0]
        wyniki, roz = podsumuj(k)
        if not rozne(stare, roz["observations"][0]):
            print(f"{k}: unchanged")
            continue
        (k / "results.json").write_text(json.dumps(wyniki, ensure_ascii=False, indent=1))
        (k / "results_rozszerzone.json").write_text(json.dumps(roz, ensure_ascii=False, indent=1))
        o = wyniki["observations"][0]
        print(f"{k}: ci95 {o['ci95']['lower']:.4f}-{o['ci95']['upper']:.4f}, reference {o['reference']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
