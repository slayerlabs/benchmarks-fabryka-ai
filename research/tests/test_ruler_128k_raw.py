"""RULER 128K: the README's key numbers recomputed from the per-sample result files, without the benchmark's code.

Imports nothing from api-benchmarks/ruler-128k (no summarize.py, compare.py, report.py, statystyka.py): it reads
results/<model-id>.jsonl.gz (one row per sample: task, length, score, closed_think) with gzip and json, recomputes
the means, the strict means, R1's clustered t, sign count and the mean without the 2 lowest tasks, R3's category
drops and clustered t, the descriptive R2 table, and the request counts, and compares them with the numbers it
parses out of README.md with its own regular expressions. A number typed or swapped by hand in the README, or a
wrong computation in the benchmark's code, makes it fail.
Run: python3 tests/test_ruler_128k_raw.py (or pytest).
"""
import functools
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
    assert re.search(rf"Effective length \(longest length with a mean of at least 85\.6\), with the 13 tasks as "
                     rf"fixed: \d+ or {point}\.", text)
    # across tasks: t of the task means against 85.6, df 12, per length
    for x in LENGTHS:
        d = [v - 85.6 for v in task_means(LFM3)[x].values()]
        t = statistics.fmean(d) / (statistics.stdev(d) / math.sqrt(len(d)))
        m = re.search(rf"^\| {x} \| [^|]+\| [^|]+\| {NUMBER} \(12\), p {NUMBER} \|", text, re.M)
        assert m and close(float(m.group(1)), t) and close(float(m.group(2)), t_two_sided_p(t, 12), 0.0006), x
    below = sorted(t for t, v in task_means(LFM3)[4096].items() if v < 85.6)
    assert f"{len(below)} tasks ({', '.join(below)}) are below 85.6 already at 4096" in text


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


# ---- control, its rescorings, R3's aggregation t, the first-record mean: each check raises on a wrong README number
OUT = BENCH / "out" / "_box" / LFM3
CARD = 65.56
BUDGET = {"vt": 30, "cwe": 120, "fwe": 50, "qa_1": 32, "qa_2": 32}  # RULER @ db43f92 tokens_to_generate; niah 128
CAPS = [8192, 16384, 32768, 65536]
CUT = "answer cut to RULER's answer budget (about 0.75 words per token)"


def postprocess(text):
    """RULER evaluate.py postprocess_pred: strip, control characters to newlines, strip."""
    return re.sub(r"[\x00-\x1f]", "\n", text.strip()).strip()


def score(task, pred, refs):
    """RULER's string_match_part for qa_*, string_match_all otherwise, one sample, percent."""
    hits = [r.lower() in pred.lower() for r in refs]
    return 100.0 * (max(hits) if task.startswith("qa") else sum(hits) / len(refs))


def analytic_se(by_task):
    """SE of the unweighted mean of task means, samples within tasks (what the bootstrap estimates)."""
    return math.sqrt(sum(statistics.pvariance(s) / len(s) for s in by_task.values())) / len(by_task)


def z_fits(mean, se, z, reference=CARD):
    """Is the printed z what the printed mean and SE (each rounded to 0.01) give?"""
    bounds = [(m - reference) / s for m in (mean - 0.005, mean + 0.005) for s in (se - 0.005, se + 0.005)]
    return min(bounds) - 0.005 <= z <= max(bounds) + 0.005


def references(length):
    """task -> index -> references, streamed from the RULER data of the out dir (None when it is not here)."""
    if not (OUT / str(length) / "data").is_dir():
        return None
    refs = {}
    for path in sorted((OUT / str(length) / "data").glob("*/validation.jsonl")):
        with open(path, encoding="utf-8") as f:
            refs[path.parent.name] = {(s := json.loads(line))["index"]: s["outputs"] for line in f if line.strip()}
    return refs


@functools.lru_cache(maxsize=None)
def variant_scores(length=131072):
    """name -> task -> scores of LFM3-1.7B at `length` under the exploratory rescorings; the answer-cut ones only
    where the out dir's RULER data (the references) are here."""
    at = [r for r in rows(LFM3) if r["length"] == length and r["score"] is not None]
    refs = references(length)
    out = {"pre-registered": {}, "strict": {}, **{f"output limit {c} tokens (a longer output scores 0)": {} for c in CAPS}}
    if refs is not None:
        out[CUT], out["strict and answer cut"] = {}, {}
    for r in at:
        add = {"pre-registered": r["score"], "strict": r["score"] if r["closed_think"] else 0.0,
               **{f"output limit {c} tokens (a longer output scores 0)": 0.0 if r["output_tokens"] > c else r["score"]
                  for c in CAPS}}
        if refs is not None:
            words = postprocess(r["answer"]).split()[:int(BUDGET.get(r["task"], 128) * 0.75)]
            cut = score(r["task"], " ".join(words), refs[r["task"]][r["index"]])
            add[CUT], add["strict and answer cut"] = cut, cut if r["closed_think"] else 0.0
        for name, value in add.items():
            out[name].setdefault(r["task"], []).append(value)
    return out


def check_control(text):
    m = re.search(rf"\*\*Control: [^*]*\*\* LFM3-1\.7B at 131072: {NUMBER} ± {NUMBER} against the card's 65\.56, "
                  rf"z = {NUMBER}", text)
    assert m, "control sentence"
    mean, se, z = map(float, m.groups())
    by_task = variant_scores()["pre-registered"]
    assert close(mean, statistics.fmean(statistics.fmean(s) for s in by_task.values())), "control mean"
    assert abs(se - analytic_se(by_task)) < 0.015, ("control SE", se, analytic_se(by_task))
    assert z_fits(mean, se, z), ("control z", mean, se, z)


def check_variants(text):
    table = section(text, "| scoring of LFM3-1.7B at 131072", "\n\n")
    scores = variant_scores()
    for name, by_task in scores.items():
        cells = table_row(table, name)
        m = re.match(rf"{NUMBER} ± {NUMBER}", cells[1])
        mean, se, z = float(m.group(1)), float(m.group(2)), float(cells[2])
        assert close(mean, statistics.fmean(statistics.fmean(s) for s in by_task.values())), (name, "mean")
        assert abs(se - analytic_se(by_task)) < 0.015, (name, "SE", se, analytic_se(by_task))
        assert z_fits(mean, se, z), (name, "z")
        assert cells[3] == ("yes" if abs(z) < 2 else "no"), (name, "within 2 SE")
    assert sum(line.startswith("|") for line in table.splitlines()[2:]) == 8  # header and separator first
    return len(scores)


def check_r3_aggregation(text):
    short, long = task_means(LFM3)[4096], task_means(LFM3)[131072]
    drops = {c: [short[t] - long[t] for t in ts] for c, ts in CATEGORIES.items()}
    value = statistics.fmean(drops["aggregation"]) - statistics.fmean(drops["retrieval"])
    se = math.hypot(*(statistics.stdev(drops[c]) / math.sqrt(len(drops[c])) for c in ("aggregation", "retrieval")))
    m = re.search(rf"aggregation - retrieval {NUMBER} ± {NUMBER} \(t = {NUMBER}, df (\d+)\)", text)
    assert m and close(float(m.group(1)), value) and close(float(m.group(2)), se), "R3 aggregation value, SE"
    assert close(float(m.group(3)), value / se) and int(m.group(4)) == 1, "R3 aggregation t"


@functools.lru_cache(maxsize=None)
def first_record_means(length=4096):
    """(mean, strict mean) over tasks at `length` scoring each sample's FIRST raw record with an output; None when
    the out dir is not here."""
    refs = references(length)
    if refs is None:
        return None
    pre, strict = {}, {}
    for task, by_index in refs.items():
        first = {}
        with open(OUT / str(length) / "raw" / f"{task}.jsonl", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if "output" in r and r["index"] not in first:
                    first[r["index"]] = r["output"]
        for i, output in first.items():
            s = score(task, postprocess(output.rsplit("</think>", 1)[-1]), by_index[i])
            pre.setdefault(task, []).append(s)
            strict.setdefault(task, []).append(s if "</think>" in output else 0.0)
    return tuple(statistics.fmean(statistics.fmean(v) for v in d.values()) for d in (pre, strict))


def check_first_record(text, means):
    m = re.search(rf"With the first record instead the mean at 4096 is {NUMBER} \(scored: {NUMBER}\), strict {NUMBER} "
                  rf"\({NUMBER}\)", text)
    assert m, "first-record sentence"
    assert close(float(m.group(1)), means[0]) and close(float(m.group(3)), means[1]), "first-record means"
    assert close(float(m.group(2)), length_mean(task_means(LFM3)[4096])), "scored mean"
    assert close(float(m.group(4)), length_mean(task_means(LFM3, strict=True)[4096])), "scored strict mean"


def test_control_and_its_rescorings():
    check_control(readme())
    n = check_variants(readme())
    print(f"test_control_and_its_rescorings: {n} of 8 rescorings recomputed"
          + ("" if n == 8 else " (the answer-cut ones need out/_box/lfm3-1.7b/131072/data)"))


def test_r3_aggregation_t():
    check_r3_aggregation(readme())


def test_first_record_mean():
    means = first_record_means()
    if means is None:
        print("test_first_record_mean: no out/_box/lfm3-1.7b/4096 here, not run")
        return
    check_first_record(readme(), means)


def bump(text, pattern, by):
    """`text` with the number in group 1 of the first match of `pattern` moved by `by`."""
    m = re.search(pattern, text)
    assert m, pattern
    old = m.group(0)
    start, end = m.start(1) - m.start(0), m.end(1) - m.start(0)
    return text.replace(old, old[:start] + f"{float(m.group(1)) + by:.2f}" + old[end:], 1)


def fails(check, text):
    try:
        check(text)
    except AssertionError:
        return True
    return False


def test_a_swapped_number_fails():
    """Swap one README number at a time in a copy: the checks above must fail on each."""
    text = readme()
    row = "| " + " | ".join(table_row(text, f"LFM3-1.7B (`{LFM3}`)")) + " |"
    swapped = text.replace(row, row.replace(table_row(text, f"LFM3-1.7B (`{LFM3}`)")[4], "71.68 ± 0.93", 1))
    assert swapped != text
    assert not close(lead(table_row(swapped, f"LFM3-1.7B (`{LFM3}`)")[4]), length_mean(task_means(LFM3)[131072]))
    swaps = [  # (check, README with one number moved): control SE, a rescoring's mean and z, R3 aggregation t
        (check_control, bump(text, r"LFM3-1\.7B at 131072: \d+\.\d+ ± (\d+\.\d+)", 0.02)),
        (check_variants, bump(text, r"\| output limit 8192 tokens \(a longer output scores 0\) \| (\d+\.\d+)", 0.10)),
        (check_variants, bump(text, r"\| strict \| \d+\.\d+ ± \d+\.\d+ \| (\d+\.\d+) \|", 0.10)),
        (check_r3_aggregation, bump(text, r"aggregation - retrieval -?\d+\.\d+ ± \d+\.\d+ \(t = (-?\d+\.\d+)", 0.10)),
    ]
    means = first_record_means()
    if means is not None:
        swaps.append((lambda t: check_first_record(t, means),
                      bump(text, r"With the first record instead the mean at 4096 is (\d+\.\d+)", 0.10)))
    for i, (check, changed) in enumerate(swaps):
        assert changed != text, i
        assert fails(check, changed), f"swap {i} was not caught"


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} passed")
