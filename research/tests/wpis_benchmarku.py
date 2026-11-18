"""Shared checks of tests/test_<name>.py for the central-run tasks, runnable in the CI job `light` (no lm-eval).

`common/zadania.py` imports `lm_eval` only for the path of its task YAMLs; without lm-eval installed (CI `light`)
a placeholder module stands in, so ZADANIA and tests/test_zgodnosc_karty.py import and nothing that would read an
lm-eval YAML is called. `MA_LM_EVAL` marks the checks that need the real package (they run in .venv-eval).

`sprawdz_wpis` ties one ZADANIA entry to its four records: the card (test_zgodnosc_karty.rozbieznosci), RECIPE.md
(`repo@rewizja` and `--zadania T..`), the README row "Benchmarki i typy" (task id and type) and the `klastry` key
(`+klastry` in the type <=> a cluster rule). `modul_forka` loads a copied OpenPL/lm-eval helper file; Levenshtein,
datasets and sklearn are replaced by placeholders only when missing (the helpers call them in functions the tests
do not use, except `Levenshtein.distance`, which gets a plain edit distance).
"""
import importlib.util
import re
import sys
import types
from pathlib import Path

TESTY = Path(__file__).resolve().parent
KORZEN = TESTY.parent
MA_LM_EVAL = importlib.util.find_spec("lm_eval") is not None
sys.path.insert(0, str(TESTY))
if MA_LM_EVAL or "zadania" in sys.modules:
    import test_zgodnosc_karty as ZK  # noqa: E402
else:
    _atrapa = types.ModuleType("lm_eval")
    _atrapa.__file__ = str(KORZEN / "brak_lm_eval" / "__init__.py")  # ZADANIA_LM_EVAL points nowhere, never read
    sys.modules["lm_eval"] = _atrapa
    try:
        import test_zgodnosc_karty as ZK  # noqa: E402
    finally:
        # GOTCHA: only for the import of zadania; left in sys.modules it makes find_spec("lm_eval") raise
        # ValueError in other tests of the same process (test_blimp checks for lm-eval that way)
        del sys.modules["lm_eval"]

Z = ZK.Z


def wiersz_readme(katalog):
    """(task id, type, groups) of the README table "Benchmarki i typy" row of `benchmarks/<katalog>`."""
    wzor = re.compile(rf"^\| \[`{re.escape(katalog)}`\]\(benchmarks/{re.escape(katalog)}/README\.md\) \| (T\d\d) \| "
                      r"`([^`]+)` \|([^|]*)\|", re.M)
    trafienia = wzor.findall((KORZEN / "README.md").read_text(encoding="utf-8"))
    assert len(trafienia) == 1, f"README: {len(trafienia)} rows for {katalog}"
    return trafienia[0][0], trafienia[0][1], trafienia[0][2].strip()


def sprawdz_wpis(task_id, oczekiwane, shoty, typ):
    """The entry has the values copied from the card (`oczekiwane`, `shoty`) and every record agrees with it.

    Returns (meta, card text) for checks specific to the benchmark."""
    meta = Z.ZADANIA[task_id]
    katalog = ZK.KATALOGI[task_id]
    karta = ZK.karta(task_id).read_text(encoding="utf-8")
    assert {k: meta.get(k) for k in oczekiwane} == oczekiwane
    assert ZK.shoty(meta) == shoty
    assert ZK.rozbieznosci(meta, karta) == {}
    recipe = (KORZEN / "benchmarks" / katalog / "RECIPE.md").read_text(encoding="utf-8")
    assert f"`{meta['repo']}@{meta['rewizja']}" in recipe and f"--zadania {task_id} " in recipe
    tid, typ_readme, _ = wiersz_readme(katalog)
    assert (tid, typ_readme) == (task_id, typ)
    assert ("+klastry" in typ) == bool(meta.get("klastry"))
    return meta, karta


def _levenshtein(a, b):
    poprzedni = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        biezacy = [i]
        for j, y in enumerate(b, 1):
            biezacy.append(min(poprzedni[j] + 1, biezacy[j - 1] + 1, poprzedni[j - 1] + (x != y)))
        poprzedni = biezacy
    return poprzedni[-1]


def modul_forka(sciezka_wzgledna):
    """A helper file under benchmarks/ (e.g. `polqa/lm_eval_tasks/polish_polqa/utils.py`) as a module."""
    for nazwa in ("Levenshtein", "datasets", "sklearn"):
        if nazwa not in sys.modules and importlib.util.find_spec(nazwa) is None:
            modul = types.ModuleType(nazwa)
            modul.distance = _levenshtein
            modul.Dataset = object
            sys.modules[nazwa] = modul
            if nazwa == "sklearn":  # `import sklearn.metrics` needs the submodule too
                modul.metrics = sys.modules["sklearn.metrics"] = types.ModuleType("sklearn.metrics")
    plik = KORZEN / "benchmarks" / sciezka_wzgledna
    spec = importlib.util.spec_from_file_location(f"forka_{plik.parent.name}_{plik.stem}", plik)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul
