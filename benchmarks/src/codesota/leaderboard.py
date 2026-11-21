"""The results page: every published result in one place, normalized, with Slayer 1B first.

`python -m codesota.leaderboard` reads the results the research pipeline published and writes `benchmarks/results/`:

- `results.jsonl`: one line per benchmark, model, and metric, with its uncertainty, protocol, and source file;
- `README.md`: the latest Slayer 1B next to the headline reference models, by category and language, with charts;
- `all-models.md`: every model of every run, by category;
- `instruction-following.md`: instruction-following benchmarks, which use a different protocol per model;
- `charts/*.png`: the headline charts (needs the `report` extra, matplotlib).

The source files stay where they are: this module only reads them. Nothing here is recomputed; values, standard
errors, and counts are those of the source. `python -m codesota.leaderboard --check` fails when the files differ from
what the sources give (`tests/test_leaderboard.py` runs it for the text files).
"""

import argparse
import json
import sys
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

from codesota import catalog

PACKAGE = Path(__file__).resolve().parent
BENCHMARKS = PACKAGE.parent.parent
REPO = BENCHMARKS.parent
OUT = BENCHMARKS / "results"
FULL_RUN = "research/results/full-run-2026-11"
IFEVAL_API = "research/api-benchmarks/ifeval/results"

# Benchmark categories, in display order, as in the README's "Evaluation domains".
CATEGORIES: Final[dict[str, tuple[str, ...]]] = {
    "Reasoning and science": ("arc-easy", "arc-challenge", "mathqa"),
    "Commonsense": ("hellaswag", "piqa", "winogrande", "social-iqa", "wsc273", "ewok"),
    "Knowledge (medical)": ("medmcqa", "pubmedqa"),
    "Language modeling and linguistics": ("lambada", "wikitext-2", "blimp"),
    "Polish": ("multiblimp-pl",),
    "Instruction following": ("ifeval",),
}
CATEGORY_OF: Final = {b: c for c, bs in CATEGORIES.items() for b in bs}


@dataclass(frozen=True)
class Model:
    label: str
    name: str
    params_b: float
    kind: str  # "base" or "instruct"
    family: str


# The latest Slayer first, then the headline references (the maintainers' choice), then everything else.
LATEST_SLAYER: Final = "slayer1b-1.09-k40000"
HEADLINE: Final = (LATEST_SLAYER, "bielik-11b-v3-instruct", "lfm3-1.7b-base", "bielik-1.5b-v3", "qwen3.5-0.8b-base")
MODELS: Final[dict[str, Model]] = {
    m.label: m
    for m in (
        Model(LATEST_SLAYER, "Slayer 1B 1.09 (step 40 000, training in progress)", 1.07, "base", "Slayer"),
        Model("bielik-11b-v3-instruct", "Bielik 11B v3.0 Instruct", 11.17, "instruct", "Bielik"),
        Model("lfm3-1.7b-base", "LFM3-1.7B-Base", 1.73, "base", "Liquid"),
        Model("bielik-1.5b-v3", "Bielik 1.5B v3", 1.60, "base", "Bielik"),
        Model("qwen3.5-0.8b-base", "Qwen3.5-0.8B-Base", 0.87, "base", "Qwen"),
        Model("lfm3-1.7b", "LFM3-1.7B", 1.73, "instruct", "Liquid"),
        Model("lfm2.5-1.2b-base", "LFM2.5-1.2B-Base", 1.17, "base", "Liquid"),
        Model("eurollm-1.7b", "EuroLLM-1.7B", 1.66, "base", "EuroLLM"),
        Model("pythia-1b-v0", "Pythia-1B v0", 1.08, "base", "Pythia"),
        *(
            Model(f"slayer1b-{v}", f"Slayer 1B {v.removesuffix('-hf')}", 1.07, "base", "Slayer")
            for v in ("1.08", "1.07-hf", "1.06", "1.05", "1.04", "1.03", "1.02", "1.01", "1.00")
        ),
        Model("bielik-11b-v3.1", "Bielik 11B v3.1 Instruct", 11.17, "instruct", "Bielik"),
        Model("bielik-11b-v3.1-vllm", "Bielik 11B v3.1 Instruct", 11.17, "instruct", "Bielik"),
        Model("bielik-11b-v3.1-vllm-no-provider", "Bielik 11B v3.1 Instruct", 11.17, "instruct", "Bielik"),
        Model("lfm3-1.7b-ifeval", "LFM3-1.7B", 1.73, "instruct", "Liquid"),
    )
}

# Protocols of the sources, described once and referenced by every result.
PROTOCOLS: Final[dict[str, str]] = {
    "full-run-2026-11": (
        "research central run of November 2026: 0-shot log-likelihood scoring through lm-eval, full test sets, "
        "float32 (Bielik 11B: bfloat16), batch 1, no chat template. Slayer requests start with one BOS token, the "
        "reference models' requests with none (measured on Pythia-1B v0 only: at most 0.0105 difference)."
    ),
    "ifeval-api": (
        "IFEval (#313): lm-eval 0.4.9.1, 541 prompts. Slayer: local GPU, raw prompt, greedy, up to 1280 tokens. "
        "Bielik: Fabryka API with its chat template, temperature 0.6, top_p 0.95. The protocols differ per model."
    ),
}


@dataclass(frozen=True)
class Result:
    benchmark: str
    legacy_id: str | None
    category: str
    language: str
    metric: str
    unit: str
    higher_is_better: bool
    model: str
    model_name: str
    repo: str | None
    revision: str | None
    value: float
    se: float | None
    n: int
    protocol: str
    variant: str
    harness: str
    codesota_status: str
    source: str


def _status(benchmark: str) -> str:
    b = catalog.CATALOG.get(benchmark)
    return b.status if b else "not-implemented"


def _source(repo: Path, run_dir: str) -> str:
    """The result file of one run: results.json, or results_rozszerzone.json where the benchmark's own code wrote
    only that one (EWoK)."""
    for name in ("results.json", "results_rozszerzone.json"):
        if (repo / run_dir / name).is_file():
            return f"{run_dir}/{name}"
    raise FileNotFoundError(f"{run_dir}: no result file")


def full_run(repo: Path = REPO) -> list[Result]:
    """Every row of the full run's manifest: one benchmark on one model, with value, SE, and n as published."""
    out = []
    for line in (repo / FULL_RUN / "manifest.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["stan"] != "ok":
            continue
        b = catalog.CATALOG[row["benchmark"]]
        metric = row["metryka"].split(",")[0]
        unit = "byte_ppl" if metric == "byte_perplexity" else "percent" if metric == "accuracy" else "score"
        model = MODELS[row["model"]]
        out.append(
            Result(
                benchmark=b.id,
                legacy_id=b.legacy_id,
                category=CATEGORY_OF[b.id],
                language=b.language,
                metric=metric,
                unit=unit,
                higher_is_better=metric != "byte_perplexity",
                model=model.label,
                model_name=model.name,
                repo=row["repo"],
                revision=row["rewizja"],
                value=float(row["wartosc"]),
                se=None if row["se"] is None else float(row["se"]),
                n=int(row["n"]),
                protocol="full-run-2026-11",
                variant=f"{row['dtype']}, {'one BOS' if model.family == 'Slayer' else 'no BOS'}",
                harness=f"lm-eval {row['lm_eval']}",
                codesota_status=_status(b.id),
                source=_source(repo, f"{FULL_RUN}/{row['benchmark']}/{row['model']}"),
            )
        )
    return out


# IFEval of #313: which committed result is which model, and how it ran.
IFEVAL_ROWS: Final = (
    ("slayer1b-1.08", "slayer1b-1.08", "local GPU, raw prompt, greedy"),
    ("bielik-11b-v3.1", "bielik-11b-v3.1", "Fabryka API, chat template, sampled"),
    ("bielik-11b-v3.1-vllm", "bielik-11b-v3.1-vllm", "own vLLM, chat template, sampled"),
    ("lfm3-1.7b", "lfm3-1.7b-ifeval", "own vLLM, card settings, reasoning on"),
)


def ifeval(repo: Path = REPO) -> list[Result]:
    out = []
    for file, label, variant in IFEVAL_ROWS:
        path = f"{IFEVAL_API}/{file}.json"
        row = json.loads((repo / path).read_text(encoding="utf-8"))
        model = MODELS[label]
        data = row["data"].split(" @ ")
        out.append(
            Result(
                benchmark="ifeval",
                legacy_id="T36",
                category=CATEGORY_OF["ifeval"],
                language="EN",
                metric=row["metric"],
                unit="percent",
                higher_is_better=True,
                model=label,
                model_name=model.name if label != "slayer1b-1.08" else "Slayer 1B 1.08",
                repo=None,
                revision=None,
                value=float(row["score"]),
                se=float(row["stderr"]),
                n=int(row["n"]),
                protocol="ifeval-api",
                variant=variant,
                harness=row["harness"].split("/")[-1] + f" (data {data[-1][:12] if len(data) > 1 else 'unknown'})",
                codesota_status=_status("ifeval"),
                source=path,
            )
        )
    return out


def collect(repo: Path = REPO) -> list[Result]:
    order = {label: i for i, label in enumerate(MODELS)}
    bench_order = {b: i for i, b in enumerate(CATEGORY_OF)}
    rows = full_run(repo) + ifeval(repo)
    return sorted(rows, key=lambda r: (bench_order[r.benchmark], order[r.model], r.metric))


# --- formatting ---


def shown(r: Result) -> str:
    """Accuracies as percent with one decimal (66.6 ± 1.0); perplexity as is (1.702 ± 0.011)."""
    if r.unit == "byte_ppl":
        return f"{r.value:.3f}" + (f" ± {r.se:.3f}" if r.se is not None else "")
    scale = 1.0 if r.unit == "percent" else 100.0
    return f"{r.value * scale:.1f}" + (f" ± {r.se * scale:.1f}" if r.se is not None else "")


def benchmark_name(benchmark: str) -> str:
    b = catalog.CATALOG.get(benchmark)
    return b.name if b else benchmark


def table(rows: Sequence[Result], models: Sequence[str], benchmarks: Iterable[str]) -> list[str]:
    by = {(r.benchmark, r.model): r for r in rows}
    head = ["benchmark", "metric", *(f"{MODELS[m].name}" for m in models)]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * 2 + "---:|" * len(models)]
    for b in benchmarks:
        cells = [by.get((b, m)) for m in models]
        first = next((c for c in cells if c is not None), None)
        if first is None:
            continue
        arrow = "↑" if first.higher_is_better else "↓"
        lines.append(
            f"| {benchmark_name(b)} | `{first.metric}` {arrow} | "
            + " | ".join(shown(c) if c else "n/a" for c in cells)
            + " |"
        )
    return lines


def readme(rows: Sequence[Result]) -> str:
    log_lik = [r for r in rows if r.protocol == "full-run-2026-11"]
    lines = [
        "# Results",
        "",
        "Every published result of this repository in one place, generated from the research pipeline's result files",
        "by `python -m codesota.leaderboard` (do not edit by hand). Slayer 1B first, next to reference models.",
        "",
        "[All models](all-models.md) · [Instruction following](instruction-following.md) · "
        "[All results as JSONL](results.jsonl) · [Benchmark status](../BENCHMARKS.md)",
        "",
        '<p align="center"><img src="charts/headline.png" alt="Slayer 1B 1.09 and reference models, accuracy '
        'per benchmark" width="100%"></p>',
        "",
        "## Headline",
        "",
        f"Value ± standard error; accuracies in percent. Protocol: {PROTOCOLS['full-run-2026-11']}",
        "",
    ]
    for category, benchmarks in CATEGORIES.items():
        if category == "Instruction following":
            continue
        lines += [f"### {category}", "", *table(log_lik, HEADLINE, benchmarks), ""]
    lines += [
        "### Instruction following",
        "",
        "Bielik 11B is v3.1 here; the log-likelihood tables above have v3.0, the version the full run measured. "
        f"{PROTOCOLS['ifeval-api']} Details: [instruction-following.md](instruction-following.md).",
        "",
        *_ifeval_table(rows, ("slayer1b-1.08", "bielik-11b-v3.1")),
        "",
        "## Read with care",
        "",
        "- **Not one class.** Bielik 11B has ten times the parameters of the others, and it and LFM3-1.7B "
        "(in the full tables) are instruction-tuned models scored here on raw text.",
        "- **Slayer 1B 1.09 at step 40 000 is a training checkpoint**, not a release; its result is preliminary.",
        "- **A difference between two models needs a paired test**, not two overlapping intervals; the research "
        "report has them ([full run](../../research/results/full-run-2026-11/README.md)).",
        "- **Status.** Only benchmarks marked `verified` in [BENCHMARKS.md](../BENCHMARKS.md) have a reproduced "
        "reference result; the others are measurements without that check.",
        "",
        "## Sources",
        "",
        f"- Log-likelihood benchmarks: [`{FULL_RUN}/`](../../{FULL_RUN}/README.md), manifest "
        f"[`manifest.jsonl`](../../{FULL_RUN}/manifest.jsonl) (commands, revisions, weight checksums).",
        f"- IFEval: [`{IFEVAL_API}/`](../../{IFEVAL_API}/), per-prompt outputs in `*.jsonl.gz`.",
        "- Every row of [`results.jsonl`](results.jsonl) names its source file.",
        "",
    ]
    return "\n".join(lines)


def _ifeval_table(rows: Sequence[Result], models: Sequence[str]) -> list[str]:
    lines = ["| model | how it ran | prompt-level strict accuracy | n |", "|---|---|---:|---:|"]
    for r in rows:
        if r.benchmark == "ifeval" and r.model in models:
            lines.append(f"| {r.model_name} | {r.variant} | {shown(r)} | {r.n} |")
    return lines


def all_models(rows: Sequence[Result]) -> str:
    log_lik = [r for r in rows if r.protocol == "full-run-2026-11"]
    present = [m for m in MODELS if any(r.model == m for r in log_lik)]
    references = [m for m in present if MODELS[m].family != "Slayer" or m == LATEST_SLAYER]
    slayers = [m for m in present if MODELS[m].family == "Slayer"]
    lines = [
        "# All models",
        "",
        "Generated by `python -m codesota.leaderboard`. [Back to the results](README.md). "
        f"Protocol: {PROTOCOLS['full-run-2026-11']}",
        "",
        "## Reference models",
        "",
    ]
    for category, benchmarks in CATEGORIES.items():
        if category != "Instruction following":
            lines += [f"### {category}", "", *table(log_lik, references, benchmarks), ""]
    lines += ["## Slayer 1B versions", ""]
    for category, benchmarks in CATEGORIES.items():
        if category != "Instruction following":
            lines += [f"### {category}", "", *table(log_lik, slayers, benchmarks), ""]
    lines += [
        "## Models",
        "",
        "| model | parameters | type | revision |",
        "|---|---:|---|---|",
    ]
    for m in present:
        r = next(x for x in log_lik if x.model == m)
        revision = (r.revision or "")[:8]
        lines.append(f"| {MODELS[m].name} | {MODELS[m].params_b:.2f}B | {MODELS[m].kind} | `{r.repo}` @ `{revision}` |")
    return "\n".join(lines) + "\n"


def instruction_following(rows: Sequence[Result]) -> str:
    lines = [
        "# Instruction following",
        "",
        "Generated by `python -m codesota.leaderboard`. [Back to the results](README.md).",
        "",
        "## IFEval",
        "",
        PROTOCOLS["ifeval-api"],
        "Rows with different setups are not interchangeable measurements.",
        "",
        *_ifeval_table(rows, [label for _, label, _ in IFEVAL_ROWS]),
        "",
        f"Source: [`{IFEVAL_API}/`](../../{IFEVAL_API}/) and its README (deviations, the LFM3 card comparison).",
        "",
    ]
    return "\n".join(lines)


def jsonl(rows: Sequence[Result]) -> str:
    return "".join(json.dumps(asdict(r), ensure_ascii=False, sort_keys=True) + "\n" for r in rows)


SNAPSHOT_START, SNAPSHOT_END = "<!-- results-snapshot:start -->", "<!-- results-snapshot:end -->"
SNAPSHOT_BENCHMARKS: Final = ("arc-easy", "piqa", "winogrande", "lambada", "hellaswag", "multiblimp-pl")


def snapshot(rows: Sequence[Result]) -> str:
    """The short table of benchmarks/README.md: the latest Slayer next to Bielik 11B, on the benchmarks with a
    reproduced reference and two headline ones, plus IFEval."""
    log_lik = [r for r in rows if r.protocol == "full-run-2026-11"]
    lines = [
        SNAPSHOT_START,
        *table(log_lik, (LATEST_SLAYER, "bielik-11b-v3-instruct"), SNAPSHOT_BENCHMARKS),
        "",
        *_ifeval_table(rows, ("slayer1b-1.08", "bielik-11b-v3.1")),
        SNAPSHOT_END,
    ]
    return "\n".join(lines)


def with_snapshot(readme_text: str, rows: Sequence[Result]) -> str:
    start, end = readme_text.index(SNAPSHOT_START), readme_text.index(SNAPSHOT_END) + len(SNAPSHOT_END)
    return readme_text[:start] + snapshot(rows) + readme_text[end:]


def text_files(repo: Path = REPO) -> dict[str, str]:
    rows = collect(repo)
    package_readme = (BENCHMARKS / "README.md").read_text(encoding="utf-8")
    return {
        "../README.md": with_snapshot(package_readme, rows),
        "README.md": readme(rows),
        "all-models.md": all_models(rows),
        "instruction-following.md": instruction_following(rows),
        "results.jsonl": jsonl(rows),
    }


# --- charts ---


def charts(rows: Sequence[Result], out: Path) -> None:
    """The headline chart: accuracy per benchmark for the headline models, with ± 1 SE."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    log_lik = [r for r in rows if r.protocol == "full-run-2026-11" and r.unit != "byte_ppl"]
    benchmarks = [b for bs in CATEGORIES.values() for b in bs if any(r.benchmark == b for r in log_lik)]
    by = {(r.benchmark, r.model): r for r in log_lik}
    width = 0.8 / len(HEADLINE)
    fig, ax = plt.subplots(figsize=(14, 5.5), dpi=120)
    colors = ("#c0392b", "#2c3e50", "#7f8c8d", "#95a5a6", "#bdc3c7")
    for i, (m, color) in enumerate(zip(HEADLINE, colors, strict=True)):
        xs, ys, es = [], [], []
        for j, b in enumerate(benchmarks):
            r = by.get((b, m))
            if r is None:
                continue
            scale = 1.0 if r.unit == "percent" else 100.0
            xs.append(j - 0.4 + width * (i + 0.5))
            ys.append(r.value * scale)
            es.append((r.se or 0.0) * scale)
        ax.bar(xs, ys, width, yerr=es, color=color, label=MODELS[m].name, capsize=2, linewidth=0)
    ax.set_xticks(range(len(benchmarks)), [benchmark_name(b) for b in benchmarks], rotation=30, ha="right")
    ax.set_ylabel("accuracy (%)")
    ax.set_ylim(0, 100)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(ncol=3, fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.15))
    ax.set_title("Full run 2026-11, 0-shot log-likelihood, ± 1 SE", fontsize=10, pad=40)
    fig.tight_layout()
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "headline.png", metadata={"Software": None})
    plt.close(fig)


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m codesota.leaderboard", description=__doc__.split("\n")[0])
    p.add_argument("--check", action="store_true", help="fail when the text files differ from the sources")
    p.add_argument("--no-charts", action="store_true", help="write the text files only (no matplotlib needed)")
    args = p.parse_args(argv)
    files = text_files()
    if args.check:
        stale = [n for n, t in files.items() if not (OUT / n).is_file() or (OUT / n).read_text(encoding="utf-8") != t]
        for n in stale:
            print(f"benchmarks/results/{n} is out of date: run python -m codesota.leaderboard", file=sys.stderr)
        return 1 if stale else 0
    OUT.mkdir(parents=True, exist_ok=True)
    for n, t in files.items():
        (OUT / n).write_text(t, encoding="utf-8", newline="\n")
    if not args.no_charts:
        charts(collect(), OUT / "charts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
