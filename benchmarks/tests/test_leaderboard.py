"""The results page: generated from the research result files, complete, and up to date. No matplotlib needed.

The values are checked against the source files directly (not against the generator's own output), so a swapped
column, a wrong scale, a lost standard error, or a swapped file fails a test.
"""

import json
import re
from pathlib import Path
from typing import Any

from codesota import leaderboard

REPO = leaderboard.REPO
FULL_RUN = REPO / leaderboard.FULL_RUN


def published() -> list[dict[str, Any]]:
    return [r for r in map(json.loads, (FULL_RUN / "manifest.jsonl").read_text(encoding="utf-8").splitlines())]


def written() -> list[dict[str, Any]]:
    return [json.loads(line) for line in (leaderboard.OUT / "results.jsonl").read_text(encoding="utf-8").splitlines()]


def ifeval_files() -> list[Path]:
    return sorted((REPO / leaderboard.IFEVAL_API).glob("*.json"))


def test_results_files_are_up_to_date() -> None:
    assert leaderboard.main(["--check"]) == 0


def test_every_published_result_is_written_once() -> None:
    rows = written()
    ok = [r for r in published() if r["stan"] == "ok"]
    assert len(rows) == len(ok) + len(ifeval_files())
    keys = [(r["benchmark"], r["model"], r["metric"]) for r in rows]
    assert len(keys) == len(set(keys))
    assert {r["source"] for r in rows if r["benchmark"] == "ifeval"} == {
        str(p.relative_to(REPO)).replace("\\", "/") for p in ifeval_files()
    }


def test_every_full_run_row_matches_its_sources() -> None:
    by = {(r["benchmark"], r["model"]): r for r in written() if r["protocol"] == "full-run-2026-11"}
    flags = {
        (x["benchmark"], x["model"]): x["flaga"]
        for x in map(json.loads, (FULL_RUN / "przeglad.jsonl").read_text(encoding="utf-8").splitlines())
    }
    for src in published():
        if src["stan"] != "ok":
            continue
        row = by[(src["benchmark"], src["model"])]
        assert (row["value"], row["se"], row["n"], row["revision"]) == (
            src["wartosc"],
            src["se"],
            src["n"],
            src["rewizja"],
        ), row
        observation = json.loads((REPO / row["source"]).read_text(encoding="utf-8"))["observations"][0]
        assert observation["value"] == row["value"], row
        assert observation.get("model_id", src["repo"]) == src["repo"], row  # EWoK's file has no model_id
        assert row["review_flag"] == flags.get((src["benchmark"], src["model"]), "ok")


def test_every_ifeval_row_matches_its_file() -> None:
    by = {r["source"]: r for r in written() if r["benchmark"] == "ifeval"}
    for path in ifeval_files():
        src = json.loads(path.read_text(encoding="utf-8"))
        row = by[str(path.relative_to(REPO)).replace("\\", "/")]
        assert (row["value"], row["se"], row["n"]) == (src["score"], src["stderr"], src["n"])
        assert row["model"] in (src["model"], f"{src['model']}-ifeval")


def headline_rows() -> list[tuple[str, list[str]]]:
    """The benchmark rows of the headline table: the benchmark's name and its cells' HTML."""
    readme = (leaderboard.OUT / "README.md").read_text(encoding="utf-8")
    out = []
    for row in re.findall(r"<tr><td>(.*?)</td>(.*?)</tr>", readme):
        out.append((row[0], re.findall(r'<td align="right">(.*?)</td>', row[1])))
    return out


def test_headline_cells_show_each_model_s_own_source_value() -> None:
    """Every cell of the headline table, recomputed from manifest.jsonl for its column's model."""
    src = {(r["benchmark"], r["model"]): r for r in published()}
    names = {leaderboard.benchmark_name(b): b for b in leaderboard.CATEGORY_OF}
    models = (*leaderboard.RANKED, *leaderboard.LARGER)
    checked = 0
    for name, cells in headline_rows():
        benchmark = names[name.removesuffix(" ↓")]
        assert len(cells) == len(models)
        for model, text in zip(models, cells, strict=True):
            row = src.get((benchmark, model))
            if row is None:
                assert text == "n/a"
                continue
            scale = 1.0 if row["metryka"] in ("accuracy", "byte_perplexity,none") else 100.0
            digits = 3 if row["metryka"].startswith("byte_perplexity") else 1
            assert re.sub(r"</?(b|ins)>", "", text) == f"{row['wartosc'] * scale:.{digits}f}", (benchmark, model)
            checked += 1
    assert checked >= 60


def test_headline_marks_the_best_and_second_of_the_ranked_models() -> None:
    """Bold is the best shown value of the ranked models, underlined the next one; the cells' values are checked
    against the sources above."""
    n = len(leaderboard.RANKED)
    for name, cells in headline_rows():
        values = [float(re.sub(r"</?(b|ins)>", "", t)) for t in cells[:n]]
        order = sorted(set(values), reverse=not name.endswith(" ↓"))
        for value, text in zip(values, cells[:n], strict=True):
            assert text.startswith("<b>") == (value == order[0]), (name, text)
            assert text.startswith("<ins>") == (value == order[1]), (name, text)
        assert not any(t.startswith(("<b>", "<ins>")) for t in cells[n:]), name  # the larger model is not ranked


def test_the_headline_has_no_flagged_result() -> None:
    # README.md says so in its notes; this keeps the sentence true.
    flagged = [r for r in leaderboard.collect() if r.model in leaderboard.HEADLINE and r.review_flag != "ok"]
    assert flagged == []


def test_flagged_results_are_marked_in_the_full_tables() -> None:
    flagged = [r for r in leaderboard.collect() if r.review_flag != "ok"]
    assert flagged
    text = (leaderboard.OUT / "all-models.md").read_text(encoding="utf-8")
    for r in flagged:
        assert f"{leaderboard.shown(r)} †" in text


def test_slayer_comes_first_and_every_headline_model_has_results() -> None:
    assert leaderboard.HEADLINE[0] == leaderboard.LATEST_SLAYER
    assert set(leaderboard.HEADLINE) <= {r.model for r in leaderboard.collect()}


def test_every_result_benchmark_has_a_category() -> None:
    assert {r.benchmark for r in leaderboard.collect()} <= set(leaderboard.CATEGORY_OF)


def test_bielik_versions_are_named_where_they_differ() -> None:
    names = {r.model_name for r in leaderboard.collect() if r.model.startswith("bielik-11b")}
    assert names == {"Bielik 11B v3.0 Instruct", "Bielik 11B v3.1 Instruct"}


def test_bos_follows_the_benchmark() -> None:
    rows = {(r.benchmark, r.model): r for r in leaderboard.collect()}
    assert rows[("blimp", leaderboard.LATEST_SLAYER)].variant.endswith(
        "BOS not applicable (empty context or rolling windows)"
    )
    assert rows[("arc-easy", leaderboard.LATEST_SLAYER)].variant.endswith("one BOS")
    assert rows[("arc-easy", "qwen3.5-0.8b-base")].variant.endswith("no BOS")
    assert rows[("ewok", "qwen3.5-0.8b-base")].harness.startswith("own code")
