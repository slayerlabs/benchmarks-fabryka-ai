"""tools/queue_plan.py: split (model, task) pairs into GPU queues by estimated time. No GPU, no network."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "tools"))
import queue_plan as Q  # noqa: E402


def koszt(tabela):
    return lambda m, t: tabela[(m, t)]


def test_lpt_longest_queue_within_ideal_plus_longest_pair():
    tabela = {(f"m{i}", f"T{j}"): float((i + 1) * (j + 1)) for i in range(10) for j in range(5)}
    modele = [(f"m{i}", [f"T{j}" for j in range(5)]) for i in range(10)]
    kolejki, razem = Q.plan(modele, 8, koszt(tabela))
    assert len(kolejki) == 8
    assert max(l for l, _ in kolejki) <= razem / 8 + max(tabela.values())
    assert abs(sum(l for l, _ in kolejki) - razem) < 1e-6


def test_every_pair_once_and_a_long_model_cut_into_parts():
    tabela = {("duzy", f"T{j}"): 100.0 for j in range(6)}
    tabela.update({("maly", "T0"): 10.0, ("maly", "T1"): 10.0})
    modele = [("duzy", [f"T{j}" for j in range(6)]), ("maly", ["T0", "T1"])]
    kolejki, _ = Q.plan(modele, 3, koszt(tabela))
    pary = []
    for _, pozycje in kolejki:
        for p in pozycje:
            m, _, z = p.partition(":")
            pary += [(m, t) for t in (z.split(",") if z else dict(modele)[m])]
    assert sorted(pary) == sorted(tabela)
    assert sum(1 for _, pozycje in kolejki for p in pozycje if p.startswith("duzy:")) >= 3  # cut: 600 s > 610 / 3
    assert any(p == "maly" for _, pozycje in kolejki for p in pozycje)  # short model stays whole


def test_item_with_tasks_stays_as_given_when_not_cut():
    b = [f"T{j}" for j in range(10)]
    kolejki, _ = Q.plan([("a:T1,T2", ["T1", "T2"]), ("b", b)], 2, lambda m, t: 1.0)
    pozycje = [p for _, ps in kolejki for p in ps]
    assert "a:T1,T2" in pozycje  # 2 s, not longer than a third of the 6 s share
    assert all(p.startswith("b:") for p in pozycje if p != "a:T1,T2")  # 10 s, cut


def test_same_input_same_plan():
    tabela = {(m, t): float(len(m) * 7 + int(t[1:]) * 3) for m in ("a", "bb", "ccc", "dddd") for t in ("T1", "T2", "T3")}
    modele = [(m, ["T1", "T2", "T3"]) for m in ("a", "bb", "ccc", "dddd")]
    assert Q.plan(modele, 3, koszt(tabela)) == Q.plan(modele, 3, koszt(tabela))


def test_estimates_measured_then_task_median_times_model_ratio_then_default():
    zmierzone = {("szybki", "T1"): 10.0, ("szybki", "T2"): 20.0, ("wolny", "T1"): 30.0}
    koszt_, nieznane = Q.estimator(zmierzone)
    assert koszt_("szybki", "T1") == 10.0
    # wolny is 1.5x the T1 median (20): T2 median 20 -> 30
    assert koszt_("wolny", "T2") == 20.0 * 1.5
    assert koszt_("nowy", "T1") == 20.0  # unknown model: task median, ratio 1
    assert koszt_("nowy", "T9") == Q.DEFAULT_S and nieznane == {"T9"}


def test_reads_only_finished_evaluations():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "czasy.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in [
            {"etap": "ewaluacja", "model": "a", "zadanie": "T1", "kod": 0, "s": 5},
            {"etap": "ewaluacja", "model": "a", "zadanie": "T1", "kod": 0, "s": 7},
            {"etap": "ewaluacja", "model": "a", "zadanie": "T2", "kod": 1, "s": 999},
            {"etap": "pobranie", "model": "a", "s": 50}]) + "\nnie json\n")
        assert Q.read_times([str(p), str(Path(d) / "brak.jsonl")]) == {("a", "T1"): 6.0}


def test_cli_prints_one_line_per_gpu():
    wynik = subprocess.run([sys.executable, str(KORZEN / "tools" / "queue_plan.py"), "--gpus", "2", "--repo",
                            tempfile.mkdtemp()], input="a\tT1 T2\nb\tT1\n", capture_output=True, text=True, check=True)
    assert [l.split()[0] for l in wynik.stdout.splitlines()] == ["0", "1"]
    assert "never timed" in wynik.stderr
