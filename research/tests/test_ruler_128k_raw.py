"""RULER 128K: the README's key numbers recomputed from the per-sample result files, without the benchmark's code.

Imports nothing from api-benchmarks/ruler-128k (no summarize.py, compare.py, report.py, statystyka.py): it reads
results/<model-id>.jsonl.gz (one row per sample: task, length, score, closed_think) with gzip and json, recomputes
the means, the strict means, R1's clustered t, sign count and the mean without the 2 lowest tasks, R3's category
drops and clustered t, the descriptive R2 table, and the request counts, and compares them with the numbers it
parses out of README.md with its own regular expressions. A number typed or swapped by hand in the README, or a
wrong computation in the benchmark's code, makes it fail.
Run: python3 tests/test_ruler_128k_raw.py (or pytest).
"""
import gzip
import json
import math
import re
import statistics
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1] / "api-benchmarks" / "ruler-128k"
LFM3, BIELIK, SLAYER = "lfm3-1.7b", "bielik-11b-v3.1", "slayer1b-1.09-k70000"
RETRIEVAL = ["niah_single_1", "niah_single_2", "niah_single_3", "niah_multikey_1", "niah_multikey_2", "niah_multikey_3",
             "niah_multivalue", "niah_multiquery"]
CATEGORIES = {"retrieval": RETRIEVAL, "tracing": ["vt"], "aggregation": ["cwe", "fwe"], "qa": ["qa_1", "qa_2"]}
LENGTHS = [4096, 8192, 16384, 32768, 65536, 131072]
NUMBER = r"(-?\d+\.\d+)"


def rows(model):
    with gzip.open(BENCH / "results" / f"{model}.jsonl.gz", "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def task_means(model, strict=False):
    """length -> task -> mean score (errors left out; strict: no `</think>` scores 0)."""
    by = {}
    for r in rows(model):
        if r["score"] is not None:
            score = 0.0 if strict and not r["closed_think"] else r["score"]
            by.setdefault(r["length"], {}).setdefault(r["task"], []).append(score)
    return {length: {t: statistics.fmean(s) for t, s in tasks.items()} for length, tasks in by.items()}


def readme():
    return (BENCH / "README.md").read_text(encoding="utf-8")


def table_row(text, *first_cells):
    """The cells of the first table row whose leading cells are `first_cells`."""
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells[:len(first_cells)] == list(first_cells):
            return cells
    raise AssertionError(f"no README row {first_cells}")


def section(text, start, end):
    """The README text from the first `start` to the next `end` after it."""
    i = text.index(start)
    return text[i:text.index(end, i)]


def lead(cell):
    m = re.match(NUMBER, cell)
    return None if m is None else float(m.group(1))


def close(a, b, tol=0.006):
    return a is not None and b is not None and abs(a - b) < tol


def t_two_sided_p(t, df):
    """Student t, two-sided p, by Simpson's rule on the density from 0 to |t| (independent of statystyka.p_t)."""
    c = math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2)) / math.sqrt(df * math.pi)
    n, h = 20000, abs(t) / 20000
    f = [c * (1 + (i * h) ** 2 / df) ** (-(df + 1) / 2) for i in range(n + 1)]
    area = h / 3 * (f[0] + f[-1] + 4 * sum(f[1:-1:2]) + 2 * sum(f[2:-1:2]))
    return 1 - 2 * area


def length_mean(means):
    return statistics.fmean(means.values())


def test_per_length_means_and_headline():
    text = readme()
    for model in (LFM3, BIELIK, SLAYER):
        for strict in (False, True) if model == LFM3 else (False,):
            means = task_means(model, strict)
            cells = table_row(text, model, "strict" if strict else "pre-registered")[2:]
            for length, cell in zip(LENGTHS, cells):
                if length in means:
                    assert close(lead(cell), length_mean(means[length])), (model, strict, length, cell)
                    tasks = len(means[length])
                    assert (f"({tasks} tasks)" in cell) == (tasks < 13), (model, length, cell)
                else:
                    assert cell == "null", (model, length, cell)
    headline = table_row(text, f"LFM3-1.7B (`{LFM3}`)")
    assert close(lead(headline[4]), length_mean(task_means(LFM3)[131072]))
    assert close(lead(headline[5]), length_mean(task_means(LFM3, strict=True)[131072]))
    assert headline[6] == str(sum(1 for r in rows(LFM3) if r["length"] == 131072 and r["score"] is not None))


def test_request_counts():
    text = section(readme(), "| model | requests scored", "\n\n")
    for model in (LFM3, BIELIK, SLAYER):
        all_rows = rows(model)
        assert table_row(text, model)[1:3] == [str(sum(r["score"] is not None for r in all_rows)),
                                               str(sum(r["score"] is None for r in all_rows))]
    assert f"Each of Bielik's {len(rows(BIELIK))} requests" in readme()


def test_r1_next_to_the_rule():
    text = readme()
    at = task_means(LFM3)[131072]
    diffs = [v - 85.6 for v in at.values()]
    t = statistics.fmean(diffs) / (statistics.stdev(diffs) / math.sqrt(len(diffs)))
    m = re.search(rf"clustered by task t = {NUMBER} \(df (\d+), p {NUMBER}", text)
    assert close(float(m.group(1)), t) and int(m.group(2)) == 12
    assert close(float(m.group(3)), t_two_sided_p(t, 12), 0.006)
    below = sum(v < 85.6 for v in at.values())
    assert re.search(rf"\b{below} of 13 tasks are below 85.6", text)
    lowest = sorted(at, key=lambda k: (at[k], k))[:2]
    rest = statistics.fmean(v for k, v in at.items() if k not in lowest)
    m = re.search(rf"\(({', '.join(lowest)})\) the mean is {NUMBER} ±", text)
    assert m and close(float(m.group(2)), rest)
    means = {x: length_mean(task_means(LFM3)[x]) for x in LENGTHS}
    point = max(x for x in LENGTHS if means[x] >= 85.6)
    assert re.search(rf"Effective length \(longest length with a mean of at least 85\.6\): \d+ or {point}\.", text)


def test_r3_drops_and_clustered_t():
    text = readme()
    short, long = task_means(LFM3)[4096], task_means(LFM3)[131072]
    drops = {c: statistics.fmean(short[t] - long[t] for t in ts) for c, ts in CATEGORIES.items()}
    retrieval = [short[t] - long[t] for t in RETRIEVAL]
    se = statistics.stdev(retrieval) / math.sqrt(len(retrieval))
    for c, ts in CATEGORIES.items():
        cells = table_row(text, c)
        assert cells[1] == str(len(ts)) and close(lead(cells[2]), drops[c]), (c, cells)
    assert close(lead(table_row(text, "retrieval")[3]), se)
    value = drops["tracing"] - drops["retrieval"]
    m = re.search(rf"Tracing - retrieval {NUMBER} ± {NUMBER} \(t = {NUMBER}, df (\d+), p {NUMBER}", text)
    assert close(float(m.group(1)), value) and close(float(m.group(2)), se)
    assert close(float(m.group(3)), value / se) and int(m.group(4)) == 7
    assert close(float(m.group(5)), t_two_sided_p(value / se, 7))
    # the point rule as coded before the results: refuted when retrieval's drop is not smaller than both others
    point = "refuted" if not (drops["tracing"] > drops["retrieval"] and drops["aggregation"] > drops["retrieval"]) \
        else "open"
    assert f"**R3: {point} by the pre-registered point rule" in text
    assert "**Across tasks the strength is undetermined**" in text


def test_r2_descriptive_table_on_the_same_tasks():
    text = section(readme(), "**R2:", "**R3:")
    lfm3, bielik = task_means(LFM3), task_means(BIELIK)
    for length in (4096, 8192, 16384):
        shared = sorted(set(lfm3[length]) & set(bielik[length]))
        cells = table_row(text, str(length))
        assert close(lead(cells[1]), length_mean(lfm3[length])) and close(lead(cells[2]), length_mean(bielik[length]))
        same = statistics.fmean(bielik[length][t] - lfm3[length][t] for t in shared)
        assert close(lead(cells[3]), same), (length, cells)
        if len(shared) < 13:
            m = re.search(rf"; {NUMBER} on the same {len(shared)} tasks", cells[1])
            assert m and close(float(m.group(1)), statistics.fmean(lfm3[length][t] for t in shared))


def test_a_swapped_number_fails():
    """Swap the LFM3-1.7B headline in a copy of the README: the parser above must see it."""
    text = readme()
    row = "| " + " | ".join(table_row(text, f"LFM3-1.7B (`{LFM3}`)")) + " |"
    swapped = text.replace(row, row.replace(table_row(text, f"LFM3-1.7B (`{LFM3}`)")[4], "71.68 ± 0.93", 1))
    assert swapped != text
    assert not close(lead(table_row(swapped, f"LFM3-1.7B (`{LFM3}`)")[4]), length_mean(task_means(LFM3)[131072]))


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} passed")
