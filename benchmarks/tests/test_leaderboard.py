"""The results page: generated from the research result files, complete, and up to date.

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


def section(text: str, heading: str) -> str:
    """The text of one `## ` section of a page, up to the next `## ` heading."""
    return text.split(f"\n{heading}\n", 1)[1].split("\n## ", 1)[0]


def written() -> list[dict[str, Any]]:
    return [json.loads(line) for line in (leaderboard.OUT / "results.jsonl").read_text(encoding="utf-8").splitlines()]


def ifeval_files() -> list[Path]:
    return sorted((REPO / leaderboard.IFEVAL_API).glob("*.json"))


def api_file(b: leaderboard.ApiBenchmark, column: str) -> dict[str, Any] | None:
    path = REPO / b.path(column)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def scored_api_files() -> list[str]:
    """The generative result files with a score, IFEval excepted (its rows come from every IFEval file)."""
    return [
        b.path(c)
        for b in leaderboard.API_BENCHMARKS
        if b.id != "ifeval"
        for c in b.labels
        if (f := api_file(b, c)) is not None and f["score"] is not None
    ]


def test_results_files_are_up_to_date() -> None:
    assert leaderboard.main(["--check"]) == 0


def test_every_published_result_is_written_once() -> None:
    rows = written()
    ok = [r for r in published() if r["stan"] == "ok"]
    assert len(rows) == len(ok) + len(ifeval_files()) + len(scored_api_files())
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


def source_cell(row: dict[str, Any]) -> tuple[str, str]:
    """A manifest row's value and SE as the page shows them."""
    scale = 1.0 if row["metryka"] in ("accuracy", "byte_perplexity,none") else 100.0
    digits = 3 if row["metryka"].startswith("byte_perplexity") else 1
    return f"{row['wartosc'] * scale:.{digits}f}", f"{row['se'] * scale:.{digits}f}"


def source_chance(benchmark: str) -> str:
    """The chance level of a test as the tables show it, read from a result file of each model that has one: it must
    be the same for all of them."""
    levels = set()
    for path in (FULL_RUN / benchmark).glob("*/results_rozszerzone.json"):
        o = json.loads(path.read_text(encoding="utf-8"))["observations"][0]
        c = (((o.get("dodatkowe") or {}).get("space") or {}).get("bazy") or {}).get("chance_value")
        levels.add("n/a" if c is None else f"{100 * c:.1f}")
    assert len(levels) == 1, (benchmark, levels)
    return levels.pop()


TABLES = (
    ("README.md", ("headline-table.svg", "headline-table-dark.svg"), leaderboard.HEADLINE),
    ("slayer-versions.md", ("slayer-versions.svg", "slayer-versions-dark.svg"), leaderboard.SLAYER_VERSIONS),
)


def test_values_tables_show_each_model_s_own_source_value_and_the_chance_level() -> None:
    """Every cell of each Values table, recomputed from manifest.jsonl for its column's model; the last column is the
    test's chance level from its result files."""
    src = {(r["benchmark"], r["model"]): r for r in published()}
    names = {leaderboard.benchmark_name(b): b for b in leaderboard.CATEGORY_OF}
    for page, _, models in TABLES:
        text = (leaderboard.OUT / page).read_text(encoding="utf-8")
        text = section(text, "## Values") if "## Values" in text else text
        checked = 0
        for name, html in re.findall(r"<tr><td>(.*?)</td>(.*?)</tr>", text):
            benchmark = names[name.removesuffix(" ↓")]
            cells = re.findall(r'<td align="right">(.*?)</td>', html)
            assert len(cells) == len(models) + 1, (page, benchmark)
            assert cells[-1] == source_chance(benchmark), (page, benchmark)
            for model, cell in zip(models, cells, strict=False):
                row = src.get((benchmark, model))
                if row is None:
                    assert cell == "n/a"
                    continue
                assert cell == " ± ".join(source_cell(row)), (page, benchmark, model)
                checked += 1
        assert checked >= 60, page


def test_table_images_show_source_values_and_mark_the_best_and_second() -> None:
    """All table images: each value is its model's source value, rank 1 (highlighted) is the best shown value of
    the row, rank 2 (underlined) the next one, and each row ends with the test's chance level."""
    src = {(r["benchmark"], r["model"]): r for r in published()}
    for _, images, models in TABLES:
        for name in images:
            svg = (leaderboard.OUT / "charts" / name).read_text(encoding="utf-8")
            cells = re.findall(r'data-benchmark="(.*?)" data-model="(.*?)" data-rank="(\d+)">(.*?)</text>', svg)
            rows: dict[str, list[tuple[str, int, str]]] = {}
            for benchmark, model, rank, text in cells:
                rows.setdefault(benchmark, []).append((model, int(rank), text))
            assert len(rows) >= 14, name
            chance = dict(re.findall(r'data-chance="(.*?)">(.*?)</text>', svg))
            for benchmark, row in rows.items():
                assert [m for m, _, _ in row] == list(models)
                assert chance[benchmark] == source_chance(benchmark), (name, benchmark)
                shown = {}
                for model, _, text in row:
                    source = src.get((benchmark, model))
                    assert text == ("n/a" if source is None else source_cell(source)[0]), (name, benchmark, model)
                    if source is not None:
                        shown[model] = float(text)
                lower = benchmark == "wikitext-2"
                order = sorted(set(shown.values()), reverse=not lower)
                for model, rank, _ in row:
                    expected = 0 if model not in shown else order.index(shown[model]) + 1
                    assert rank == expected, (name, benchmark, model, rank)


def test_the_latest_slayer_is_step_70000_and_every_slayer_version_is_on_its_page() -> None:
    assert leaderboard.LATEST_SLAYER == "slayer1b-1.09-k70000"
    slayers = {r["model"] for r in published() if r["model"].startswith("slayer1b-") and r["stan"] == "ok"}
    assert slayers == set(leaderboard.SLAYER_VERSIONS)


def test_the_headline_has_no_flagged_result() -> None:
    # README.md says so in its notes (the † of the research review); this keeps the sentence true. The generative
    # table marks its own in-review values with * instead.
    flagged = [
        r
        for r in leaderboard.collect()
        if r.model in leaderboard.HEADLINE and r.review_flag != "ok" and r.protocol == "full-run-2026-11"
    ]
    assert flagged == []


def test_flagged_results_are_marked_in_the_full_tables() -> None:
    flagged = [r for r in leaderboard.collect() if r.review_flag != "ok" and r.protocol == "full-run-2026-11"]
    assert flagged
    text = (leaderboard.OUT / "all-models.md").read_text(encoding="utf-8")
    for r in flagged:
        assert f"{leaderboard.shown(r)} †" in text


def test_slayer_comes_first_and_every_headline_model_has_results() -> None:
    assert leaderboard.HEADLINE[0] == leaderboard.LATEST_SLAYER
    assert set(leaderboard.HEADLINE) <= {r.model for r in leaderboard.collect()}


def test_every_result_benchmark_has_a_category() -> None:
    assert {r.benchmark for r in leaderboard.collect()} <= set(leaderboard.CATEGORY_OF) | set(leaderboard.API_BY_ID)


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


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def expected_cell(b: leaderboard.ApiBenchmark, column: str) -> tuple[str, str | None, dict[str, Any] | None]:
    """What a cell must show, read from the result file: its kind ("score", "null" or "not run"), the reason of a
    missing score, and the file. The file's own reason wins over the generator's fallback text."""
    src = api_file(b, column) if column in b.labels else None
    if src is not None and src["score"] is not None:
        return "score", None, src
    own = (src.get("reason") or src.get("score_null_reason")) if src is not None else None
    own = b.reason_text.get(column, own)
    if column in b.not_run:
        return "not run", own or b.not_run[column], src
    if src is not None or column in b.null_reasons:
        return "null", own or b.null_reasons.get(column) or "see the benchmark's README", src
    return "not run", None, src


def test_generative_values_table_shows_each_source_file() -> None:
    """Every cell of the Generative values table, from its result file: value ± SE (the benchmark's SE field) with *
    when the benchmark requires verification, or null / not run with the file's reason; last, the card's value."""
    text = section((leaderboard.OUT / "README.md").read_text(encoding="utf-8"), "## Generative values")
    rows = dict(re.findall(r"<tr><td>(.*?)</td>(.*?)</tr>", text))
    assert set(rows) == {b.name for b in leaderboard.API_BENCHMARKS}
    scored = 0
    for b in leaderboard.API_BENCHMARKS:
        cells = re.findall(r'<td align="right">(.*?)</td>', rows[b.name])
        assert len(cells) == len(leaderboard.API_COLUMNS) + 1, b.id
        assert cells[-1] == f"{b.card:.2f}", b.id
        star = "*" if b.pr or b.caveat else ""
        for column, cell in zip(leaderboard.API_COLUMNS, cells, strict=False):
            kind, reason, src = expected_cell(b, column)
            if kind == "score":
                assert src is not None
                se = float(src[b.se_field])
                assert cell == f"{src['score']:.1f} ± {se:.1f}{star}", (b.id, column)
                scored += 1
            else:
                assert cell == (f"{kind} <sub>{esc(reason)}</sub>" if reason else kind), (b.id, column)
    assert scored >= 20


def test_generative_table_images_show_source_values_and_stars() -> None:
    for name in ("api-benchmarks-table.svg", "api-benchmarks-table-dark.svg"):
        svg = (leaderboard.OUT / "charts" / name).read_text(encoding="utf-8")
        cells = re.findall(r'data-benchmark="(.*?)" data-model="(.*?)" data-rank="(\d+)">(.*?)</text>', svg)
        assert len(cells) == len(leaderboard.API_BENCHMARKS) * len(leaderboard.API_COLUMNS)
        for benchmark, model, _, text in cells:
            b = leaderboard.API_BY_ID[benchmark]
            column = next((c for c, label in b.labels.items() if label == model), None)
            if column is None:
                assert text == "not run", (name, benchmark, model)
                continue
            kind, _, src = expected_cell(b, column)
            if kind == "score":
                assert src is not None
                assert text == f"{src['score']:.1f}" + ("*" if b.pr or b.caveat else ""), (name, benchmark, model)
            else:
                assert text == kind, (name, benchmark, model)
        cards = dict(re.findall(r'data-card="(.*?)">(.*?)</text>', svg))
        assert cards == {b.id: f"{b.card:.1f}" for b in leaderboard.API_BENCHMARKS}


def test_a_clustered_standard_error_is_the_one_shown() -> None:
    """methodology.md, section 7: grouped items get a clustered SE. A benchmark whose result files carry
    `stderr_clustered` shows it, and SciCode's LFM3 cell is pinned to the SE its README reports (3.63), so a
    generator that shows the unclustered field fails here and not only in the README."""
    for b in leaderboard.API_BENCHMARKS:
        files = [api_file(b, column) for column in b.labels]
        if any(src is not None and "stderr_clustered" in src for src in files):
            assert b.se_field == "stderr_clustered", b.id
    readme = (REPO / leaderboard.API_DIR / "scicode" / "README.md").read_text(encoding="utf-8")
    assert "32.64 ± 2.76 (94/288; clustered 3.63)" in readme
    text = section((leaderboard.OUT / "README.md").read_text(encoding="utf-8"), "## Generative values")
    row = dict(re.findall(r"<tr><td>(.*?)</td>(.*?)</tr>", text))["SciCode"]
    cells = re.findall(r'<td align="right">(.*?)</td>', row)
    assert cells[leaderboard.API_COLUMNS.index("lfm3")] == "32.6 ± 3.6"


def test_an_unranked_row_has_no_best_or_second_mark() -> None:
    """AA-Omniscience's higher index for Slayer comes from answers graded not attempted, not from knowledge."""
    assert not leaderboard.API_BY_ID["aa-omniscience"].ranked
    for name in ("api-benchmarks-table.svg", "api-benchmarks-table-dark.svg"):
        svg = (leaderboard.OUT / "charts" / name).read_text(encoding="utf-8")
        ranks = re.findall(r'data-benchmark="aa-omniscience" data-model=".*?" data-rank="(\d+)"', svg)
        assert ranks and set(ranks) == {"0"}, name


def test_each_result_file_belongs_to_its_column() -> None:
    """The model a result file names is the column's model, so swapped labels or files fail."""
    checked = 0
    for b in leaderboard.API_BENCHMARKS:
        for column, label in b.labels.items():
            assert label.startswith(column), (b.id, column, label)
            src = api_file(b, column)
            if src is not None:
                assert str(src["model"]).startswith(column), (b.id, column, src["model"])
                checked += 1
    assert checked >= 30


def test_card_values_are_the_readmes() -> None:
    """The card value of each benchmark is written in that benchmark's README, a source outside the generator."""
    for b in leaderboard.API_BENCHMARKS:
        readme = (REPO / leaderboard.API_DIR / b.directory / "README.md").read_text(encoding="utf-8")
        assert f"{b.card:.2f}" in readme, b.id


def test_a_decision_not_to_run_is_never_shown_as_null() -> None:
    """research/METHODOLOGY.md keeps null for a model that cannot run the benchmark. A result file whose reason says
    it was not run (a cost decision, a budget stop) is shown as "not run"."""
    for b in leaderboard.API_BENCHMARKS:
        for column in b.labels:
            kind, reason, src = expected_cell(b, column)
            own = str((src or {}).get("reason") or (src or {}).get("score_null_reason") or "").lower()
            if own.startswith("not run") or "decision" in own or "budget" in own:
                assert kind == "not run", (b.id, column, reason)


def test_every_starred_benchmark_has_a_reason() -> None:
    for b in leaderboard.API_BENCHMARKS:
        if b.pr:
            assert f"#{b.pr}" in b.caveat, b.id
        assert b.starred == bool(b.pr or b.caveat), b.id
    page = (leaderboard.OUT / "api-benchmarks.md").read_text(encoding="utf-8")
    readme = (leaderboard.OUT / "README.md").read_text(encoding="utf-8")
    merged = readme.split("Merged and reviewed: ")[1].splitlines()[0].removesuffix(".")
    for b in leaderboard.API_BENCHMARKS:
        assert f"### {b.name}" in page
        if b.caveat:
            assert f"**Requires verification:** {b.caveat}." in page
        assert (b.name in merged.split(", ")) == (not b.starred), b.id
