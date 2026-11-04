"""common/zadania.py ZADANIA against the benchmark card, for every task the central run counts.

The card (`benchmarks/<dir>/ORIGINAL.md`, `DATASET.md` or `POLISH.md`, dir from KATALOGI in
tools/przebieg_centralny.sh) is the source of the test's settings; the ZADANIA entry must name the same dataset repo,
full revision, split, decision metric, shot count and lm-eval task or YAML. An entry without a card is skipped
("brak karty"), never passed. Run: python tests/test_zgodnosc_karty.py (or pytest -rs).
"""
import re
import sys
from pathlib import Path

import pytest

KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "common"))
import zadania as Z  # noqa: E402

KARTY = ("ORIGINAL.md", "DATASET.md", "POLISH.md")
# Card segments (table row field or `##` section) that state the run's protocol; reference results, SNR sources and
# other models' settings live elsewhere in the card and may name other shot counts or splits.
SPLIT = re.compile(r"^(Dane: split w (?!pracy)|Dane$)")  # the paper's own split list is not the run's split
PROTOKOL = re.compile(r"^(Dane: split w|Format zadania|Prompt|Ocena|Metryka decyzyjna)")
SHOTY = re.compile(r"\b(\d+)-shot\b|\bnum_fewshot: (\d+)\b|\b(zero)-shot\b")


def katalogi():
    tekst = (KORZEN / "tools" / "przebieg_centralny.sh").read_text(encoding="utf-8")
    pary = re.findall(r"\b(T\d\d):([\w.-]+)", " ".join(re.findall(r'^KATALOGI\+?="([^"]*)"', tekst, re.M | re.S)))
    return dict(pary)


KATALOGI = katalogi()


def karta(task_id):
    for nazwa in KARTY:
        p = KORZEN / "benchmarks" / KATALOGI[task_id] / nazwa
        if p.exists():
            return p
    return None


def segmenty(tekst):
    """[(field, text)]: table rows `| field | value |` and `## Section` bodies (cards come in both layouts)."""
    wynik, naglowek, linie = [], None, []
    for l in tekst.splitlines():
        if l.startswith("## "):
            if naglowek:
                wynik.append((naglowek, "\n".join(linie)))
            naglowek, linie = l[3:].strip(), []
        elif l.startswith("| ") and l.count("|") >= 3:
            wynik.append((l.split("|")[1].strip(), l))
        elif naglowek:
            linie.append(l)
    if naglowek:
        wynik.append((naglowek, "\n".join(linie)))
    return wynik


def tekst_pol(seg, wzor):
    return "\n".join(t for nazwa, t in seg if wzor.match(nazwa))


def slowo(wartosc, tekst):
    """`wartosc` as a whole token: `test` does not match inside `test_split` or `test_r3`."""
    return re.search(rf"(?<![\w/.-]){re.escape(wartosc)}(?![\w/-])", tekst) is not None


def shoty(meta):
    return meta.get("shots", meta.get("shoty", 0))  # (c) entries: `shots`, Polish YAML entries: `shoty`


def zadanie_lm_eval(meta):
    """What the card must name: the copied YAML file, else the lm-eval task or group, else the task name."""
    if meta.get("yaml"):
        return Path(meta["yaml"]).name
    return meta.get("lm_eval") or meta.get("grupa") or meta["task"]


def rozbieznosci(meta, tekst):
    seg = segmenty(tekst)
    rozne = {}
    if meta["repo"] not in tekst or meta["rewizja"] not in tekst:
        rozne["repo@rewizja"] = f"{meta['repo']} @ {meta['rewizja']} (pełny hash)"
    dane = tekst_pol(seg, SPLIT) or tekst
    if not slowo(meta["split"], dane):
        rozne["split"] = meta["split"]
    decyzyjna = tekst_pol(seg, re.compile(r"^Metryka decyzyjna")) or tekst_pol(seg, re.compile(r"^Ocena"))
    metryka = meta["metric"].split(",")[0]
    if f"`{metryka}`" not in decyzyjna:
        rozne["metryka decyzyjna"] = metryka
    n = shoty(meta)
    w_karcie = {int(a or b) if (a or b) else 0 for a, b, _ in SHOTY.findall(tekst_pol(seg, PROTOKOL))}
    if w_karcie != {n}:
        rozne["shots"] = (n, sorted(w_karcie))
    zad = zadanie_lm_eval(meta)
    if not (slowo(zad, tekst) or f"/{zad}" in tekst):
        rozne["zadanie lm-eval / YAML"] = zad
    return rozne


def test_katalogi_cover_zadania():
    assert set(KATALOGI) == set(Z.ZADANIA)


@pytest.mark.parametrize("task_id", sorted(Z.ZADANIA))
def test_entry_matches_card(task_id):
    p = karta(task_id)
    if p is None:
        pytest.skip(f"brak karty: benchmarks/{KATALOGI[task_id]}/ ({', '.join(KARTY)})")
    rozne = rozbieznosci(Z.ZADANIA[task_id], p.read_text(encoding="utf-8"))
    assert not rozne, f"{p.relative_to(KORZEN)}: {rozne}"


@pytest.mark.parametrize("task_id", sorted(Z.ZADANIA))
def test_run_passes_the_entry_shot_count(task_id):
    for wariant, cfg in Z.konfiguracje(task_id):
        assert (cfg.get("num_fewshot") or 0) == shoty(Z.ZADANIA[task_id]), (wariant, cfg.get("num_fewshot"))


def test_card_check_catches_wrong_settings():
    """Mutations against a real card: wrong revision, split, shots, metric each turn the check red."""
    meta = Z.ZADANIA["T10"]
    tekst = karta("T10").read_text(encoding="utf-8")
    assert rozbieznosci(meta, tekst) == {}
    zle = {"rewizja": meta["rewizja"][:-1] + "0", "split": "test", "shoty": 5, "metric": "acc_norm,none"}
    for pole, wartosc in zle.items():
        assert rozbieznosci({**meta, pole: wartosc}, tekst), pole


def bez_karty():
    return sorted(f"{t} ({KATALOGI[t]})" for t in Z.ZADANIA if karta(t) is None)


if __name__ == "__main__":
    kod = pytest.main([__file__, "-q", "-rs"])
    lista = bez_karty()
    print(f"\nbez karty ({len(lista)}): {', '.join(lista)}")
    raise SystemExit(kod)
