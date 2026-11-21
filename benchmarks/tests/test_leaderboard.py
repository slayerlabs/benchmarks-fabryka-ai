"""The results page: generated from the research result files, complete, and up to date. No matplotlib needed."""

import json

from codesota import leaderboard


def test_results_files_are_up_to_date() -> None:
    assert leaderboard.main(["--check"]) == 0


def test_every_published_result_is_in_the_jsonl_once() -> None:
    manifest = (leaderboard.REPO / leaderboard.FULL_RUN / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in (leaderboard.OUT / "results.jsonl").read_text(encoding="utf-8").splitlines()]
    published = sum(json.loads(line)["stan"] == "ok" for line in manifest)
    assert len(rows) == published + len(leaderboard.IFEVAL_ROWS)
    keys = [(r["benchmark"], r["model"], r["metric"]) for r in rows]
    assert len(keys) == len(set(keys))
    for r in rows:
        assert (leaderboard.REPO / r["source"]).is_file(), r["source"]


def test_values_are_copied_not_recomputed() -> None:
    rows = {(r.benchmark, r.model): r for r in leaderboard.collect()}
    slayer = rows[("arc-easy", leaderboard.LATEST_SLAYER)]
    source = json.loads((leaderboard.REPO / slayer.source).read_text(encoding="utf-8"))["observations"][0]
    assert slayer.value == source["value"] and slayer.n == source["n_scored"]
    assert rows[("ifeval", "bielik-11b-v3.1")].value == 55.27


def test_slayer_comes_first_and_every_headline_model_has_results() -> None:
    assert leaderboard.HEADLINE[0] == leaderboard.LATEST_SLAYER
    models = {r.model for r in leaderboard.collect()}
    assert set(leaderboard.HEADLINE) <= models
    readme = (leaderboard.OUT / "README.md").read_text(encoding="utf-8")
    first_table = readme[readme.index("| benchmark |") :].splitlines()[0]
    assert first_table.split("|")[3].strip().startswith("Slayer 1B 1.09")


def test_every_result_benchmark_has_a_category() -> None:
    assert {r.benchmark for r in leaderboard.collect()} <= set(leaderboard.CATEGORY_OF)


def test_bielik_versions_are_named_where_they_differ() -> None:
    names = {r.model_name for r in leaderboard.collect() if r.model.startswith("bielik-11b")}
    assert names == {"Bielik 11B v3.0 Instruct", "Bielik 11B v3.1 Instruct"}
