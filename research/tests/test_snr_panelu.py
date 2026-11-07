"""tools/snr_panelu.py on dummies: panel from MODELE without Slayer, spread, SE, SNR, bootstrap and leave-one-out.
Each test names the mutation it must catch.
Run: pytest tests/test_snr_panelu.py
"""
import gzip
import json
import math
import statistics
import subprocess
import sys
from pathlib import Path

import pytest

KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "tools"))
import snr_panelu as S  # noqa: E402
import statystyka  # noqa: E402

SKRYPT = 'A=1\nMODELE=(\n  "slayer1b-9|SlayerLab/S|{0}|slayer|lock"\n  "m1|o/m1|{0}|hf|new"\n  "m2|o/m2|{0}|hf|lock"\n' \
         '  "m3|o/m3|{0}|hf|lock"\n  "m4|o/m4|{0}|hf|lock"\n  "m5|o/m5|{0}|hf|lock"\n)\nB=2\n'.format("0" * 40)
# per-question correctness of 8 questions in 4 paradigms (UID), one row per model
WARTOSCI = {"m1": [1, 0, 0, 0, 1, 0, 0, 0], "m2": [1, 1, 0, 0, 1, 0, 1, 0], "m3": [1, 1, 1, 0, 1, 1, 0, 0],
            "m4": [1, 1, 1, 1, 1, 1, 1, 0], "slayer1b-9": [0, 0, 0, 0, 0, 0, 0, 0]}
UID = ["a", "a", "b", "b", "c", "c", "d", "d"]


def zapisz(katalog, model, wartosci, uid=UID):
    d = katalog / model / "probki"
    d.mkdir(parents=True)
    with gzip.open(d / "T99_space.jsonl.gz", "wt", encoding="utf-8") as fh:
        for i, (x, u) in enumerate(zip(wartosci, uid)):
            fh.write(json.dumps({"doc_id": i, "doc": {"UID": u}, "acc": float(x)}) + "\n")


@pytest.fixture
def przebieg(tmp_path):
    (tmp_path / "przebieg.sh").write_text(SKRYPT)
    k = tmp_path / "wyniki"
    for m, w in WARTOSCI.items():
        zapisz(k, m, w)
    return tmp_path


def cli(przebieg, *extra):
    r = subprocess.run([sys.executable, str(KORZEN / "tools" / "snr_panelu.py"), str(przebieg / "wyniki"),
                        "--probki", "T99_space", "--metryka", "acc", "--skrypt", str(przebieg / "przebieg.sh"),
                        "--powtorzenia", "300", *extra], capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout)


def test_panel_is_modele_without_slayer_in_order(przebieg):
    # mutation: SlayerLab row kept in the panel, or rows read out of order
    assert S.panel_z_modele(przebieg / "przebieg.sh") == ["m1", "m2", "m3", "m4", "m5"]


def test_spread_se_snr_by_hand_and_slayer_dir_ignored(przebieg):
    # mutation: pstdev instead of stdev, SE without n - 1, Slayer (all zeros) counted in the spread
    kod, w = cli(przebieg)
    m = [statistics.fmean(WARTOSCI[x]) for x in ("m1", "m2", "m3", "m4")]
    se = statistics.fmean(statistics.stdev(WARTOSCI[x]) / math.sqrt(8) for x in ("m1", "m2", "m3", "m4"))
    assert kod == 0 and w["panel"] == ["m1", "m2", "m3", "m4"] and w["bez_probek"] == ["m5"]
    assert w["rozrzut"] == pytest.approx(statistics.stdev(m)) and w["se"] == pytest.approx(se)
    assert w["snr"] == pytest.approx(statistics.stdev(m) / se)


def test_clustered_se_matches_statystyka_se_k(przebieg):
    # mutation: --klaster ignored (SE over questions) or cluster SE without k/(k-1)
    kod, w = cli(przebieg, "--klaster", "UID")
    se = statistics.fmean(statystyka.se_k(WARTOSCI[x], UID)["se"] for x in ("m1", "m2", "m3", "m4"))
    assert kod == 0 and w["klastry"] == 4 and w["se"] == pytest.approx(se)


def test_leave_one_out_and_bootstrap(przebieg):
    # mutation: leave-one-out keeps the model, interval not around the point, seed not used
    kod, w = cli(przebieg)
    for m in w["panel"]:
        reszta = [statistics.fmean(WARTOSCI[x]) for x in w["panel"] if x != m]
        se = statistics.fmean(statistics.stdev(WARTOSCI[x]) / math.sqrt(8) for x in w["panel"] if x != m)
        assert w["bez_jednego"][m] == pytest.approx(statistics.stdev(reszta) / se)
    assert w["snr_min_bez_jednego"] == min(w["bez_jednego"].values())
    lo, hi = w["przedzial95"]
    assert lo < w["snr"] < hi and w["ziarno"] == S.ZIARNO
    assert cli(przebieg)[1]["przedzial95"] == w["przedzial95"]
    assert cli(przebieg, "--ziarno", "1")[1]["przedzial95"] != w["przedzial95"]


def test_bootstrap_draws_the_same_questions_for_every_model():
    # mutation: independent draws per model (unpaired bootstrap); identical models keep SNR 0 only when paired
    dane = {m: {i: (float(i % 3 == 0), i) for i in range(30)} for m in ("a", "b", "c", "d")}
    w = S.policz(dane, 200)
    assert w["snr"] == 0 and w["przedzial95"] == [0, 0]


def test_short_panel_is_undetermined_with_exit_code_3(przebieg):
    # mutation: SNR reported from 3 models, or exit code 0 for an undetermined SNR
    kod, w = cli(przebieg, "--modele", "m1,m2,m3")
    assert kod == 3 and w["status"] == "nieustalony" and "snr" not in w


def test_different_questions_refused(tmp_path):
    # mutation: models compared on different question sets
    dane = {m: {i: (1.0, i) for i in range(5)} for m in ("a", "b", "c")}
    dane["d"] = {i: (1.0, i) for i in range(1, 6)}
    with pytest.raises(ValueError):
        S.policz(dane, 10)
