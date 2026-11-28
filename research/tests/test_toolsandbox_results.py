"""ToolSandbox: the committed results recounted from the per-item file, without the harness.

From results/bielik-11b-v3.1.jsonl.gz alone this recomputes the score, the SE clustered by base scenario and the
independent SE, the category table, the sensitivity numbers, the Polish-reply counts, the exception and rerun counts,
and checks them against results/bielik-11b-v3.1.json and the numbers printed in README.md (parsed here, not by
summarize.py). It also checks the excluded list (224 = 28 base scenarios x 8) and the Slayer null file.
Needs only pytest and the standard library. Run: python3 -m pytest research/tests/test_toolsandbox_results.py
"""
import gzip
import json
import math
import re
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1] / "api-benchmarks" / "toolsandbox"
RES = BENCH / "results"
MODEL = "bielik-11b-v3.1"
SUFFIXES = ["_3_distraction_tools_arg_description_scrambled", "_3_distraction_tools_arg_type_scrambled",
            "_3_distraction_tools_tool_description_scrambled", "_3_distraction_tools_tool_name_scrambled",
            "_10_distraction_tools", "_3_distraction_tools", "_all_tools"]


def rows():
    with gzip.open(RES / f"{MODEL}.jsonl.gz", "rt", encoding="utf-8") as f:
        return [json.loads(l) for l in f]


def base(name):
    for s in SUFFIXES:
        if name.endswith(s):
            return name[: -len(s)]
    return name


def stats(xs, groups):
    """mean, independent SE, clustered SE (all x 100), n, k."""
    n = len(xs)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    by = {}
    for x, g in zip(xs, groups):
        by[g] = by.get(g, 0.0) + (x - m)
    k = len(by)
    se_c = math.sqrt(k / (k - 1) * sum(v * v for v in by.values())) / n
    return m * 100, sd / math.sqrt(n) * 100, se_c * 100, n, k


def readme():
    return (BENCH / "README.md").read_text(encoding="utf-8")


def test_scenarios_and_clusters():
    r = rows()
    ex = {l.strip() for l in open(BENCH / "rapid_api_scenarios.txt") if l.strip()}
    assert len(r) == 808 and len({x["task_id"] for x in r}) == 808
    assert len(ex) == 224 and not ({x["task_id"] for x in r} & ex)
    assert len({base(n) for n in ex}) == 28
    groups = {}
    for x in r:
        assert x["base_scenario"] == base(x["task_id"])
        groups.setdefault(x["base_scenario"], []).append(x)
    assert len(groups) == 101 and all(len(v) == 8 for v in groups.values())


def test_headline_and_json():
    r = rows()
    m, se_i, se_c, n, k = stats([x["score"] for x in r], [x["base_scenario"] for x in r])
    res = json.loads((RES / f"{MODEL}.json").read_text())
    assert (round(m, 2), round(se_c, 2), round(se_i, 2), n, k) == (45.18, 3.72, 1.49, 808, 101)
    assert (res["score"], res["stderr"], res["n"]) == (45.18, 3.72, 808)
    assert res["other_metrics"]["stderr_independent"] == 1.49 and res["other_metrics"]["clusters"] == 101
    # with 8 variants in every base the clustered SE is the sd of the base means / sqrt(k)
    means = [sum(x["score"] for x in r if x["base_scenario"] == b) / 8 for b in {x["base_scenario"] for x in r}]
    mm = sum(means) / len(means)
    assert abs(math.sqrt(sum((v - mm) ** 2 for v in means) / (len(means) - 1) / len(means)) * 100 - se_c) < 1e-9
    assert res["infrastructure_errors"] == 0 and res["scored_exceptions_by_type"] == {"KeyError": 2}
    assert res["scenarios_rerun_after_infra_error"] == ["update_contact_relationship_with_relationship_alt"]
    assert sum(1 for x in r if x["error_type"] == "KeyError" and x["output"] is None and x["error_message"]) == 2
    assert not any(x["infrastructure_error"] for x in r)


def test_categories_against_json_and_readme():
    r = rows()
    res = json.loads((RES / f"{MODEL}.json").read_text())
    cats = {}
    for x in r:
        for c in x["categories"]:
            cats.setdefault(c, []).append(x)
    text = readme()
    for c, v in cats.items():
        m, _, se_c, n, k = stats([x["score"] for x in v], [x["base_scenario"] for x in v])
        assert (res["category_scores"][c], res["category_stderr_clustered"][c], res["category_n"][c],
                res["category_clusters"][c]) == (round(m, 2), round(se_c, 2), n, k)
        line = next(l for l in text.splitlines() if l.startswith(f"| {c} |"))
        assert [c2.strip() for c2 in line.strip("|").split("|")] == [c, f"{m:.2f}", f"{se_c:.2f}", str(n), str(k)]


def test_insufficient_information_and_sensitivity():
    r = rows()
    kept = {}
    for line in open(BENCH / "rapid_api_kept_bases.txt"):
        if line.strip() and not line.startswith("#"):
            b, _, rp = line.rstrip("\n").split("\t")
            kept[b] = rp == "yes"
    assert len(kept) == 10 and sum(kept.values()) == 6
    k80 = [x for x in r if x["base_scenario"] in kept]
    assert len(k80) == 80 and all(x["score"] == 1.0 for x in k80)

    def s(sub):
        m, _, se_c, n, k = stats([x["score"] for x in sub], [x["base_scenario"] for x in sub])
        return f"{m:.2f} ± {se_c:.2f} (n = {n}, k = {k})"
    text = " ".join(readme().split())
    for sub in ([x for x in r if x["base_scenario"] not in kept],
                [x for x in r if x["base_scenario"] not in kept or kept[x["base_scenario"]]],
                [x for x in r if "INSUFFICIENT_INFORMATION" not in x["categories"]]):
        m, _, se_c, n, k = stats([x["score"] for x in sub], [x["base_scenario"] for x in sub])
        assert f"{m:.2f} ± {se_c:.2f} (n = {n}, k = {k})" in text, s(sub)


def test_polish_and_rapid_counts_against_readme():
    r = [x for x in rows() if x["output"]]
    pl = re.compile("[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")

    def asst(x):
        return [m["content"] for m in x["output"] if m["role"] == "assistant" and isinstance(m.get("content"), str)
                and m["content"].strip()]
    msgs = [t for x in r for t in asst(x)]
    a = sum(1 for x in r if any(pl.search(t) for t in asst(x)))
    b = sum(1 for x in r if any(len(pl.findall(t)) >= 2 for t in asst(x)))
    assert (len(r), a, b, len(msgs), sum(1 for t in msgs if pl.search(t))) == (806, 284, 277, 3374, 1134)
    assert not any(pl.search(m["content"]) for x in r for m in x["output"]
                   if m["role"] == "user" and isinstance(m.get("content"), str))
    rapid = {x["task_id"] for x in r for m in x["output"]
             if m["role"] == "tool" and "RAPID_API_KEY" in str(m.get("content"))}
    assert len(rapid) == 3
    text = " ".join(readme().split())
    assert "284 (35.2 percent)" in text and "1134 of the 3374" in text and "277 with two or more" in text
    assert round(284 / 806 * 100, 1) == 35.2


def test_slayer_null():
    d = json.loads((RES / "slayer1b-1.09-k70000.json").read_text())
    assert d["score"] is None and d["stderr"] is None and d["n"] == 0 and d["score_null_reason"]
    assert d["settings"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
