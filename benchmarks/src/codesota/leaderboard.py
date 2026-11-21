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
from typing import Any, Final

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
    kind: str  # "base" or "instruct"
    family: str


# The latest Slayer first, then the headline references (the maintainers' choice), then everything else.
LATEST_SLAYER: Final = "slayer1b-1.09-k40000"
HEADLINE: Final = (LATEST_SLAYER, "bielik-11b-v3-instruct", "lfm3-1.7b-base", "bielik-1.5b-v3", "qwen3.5-0.8b-base")
MODELS: Final[dict[str, Model]] = {
    m.label: m
    for m in (
        Model(LATEST_SLAYER, "Slayer 1B 1.09 (step 40 000, training in progress)", "base", "Slayer"),
        Model("bielik-11b-v3-instruct", "Bielik 11B v3.0 Instruct", "instruct", "Bielik"),
        Model("lfm3-1.7b-base", "LFM3-1.7B-Base", "base", "Liquid"),
        Model("bielik-1.5b-v3", "Bielik 1.5B v3", "base", "Bielik"),
        Model("qwen3.5-0.8b-base", "Qwen3.5-0.8B-Base", "base", "Qwen"),
        Model("lfm3-1.7b", "LFM3-1.7B", "instruct", "Liquid"),
        Model("lfm2.5-1.2b-base", "LFM2.5-1.2B-Base", "base", "Liquid"),
        Model("eurollm-1.7b", "EuroLLM-1.7B", "base", "EuroLLM"),
        Model("pythia-1b-v0", "Pythia-1B v0", "base", "Pythia"),
        *(
            Model(f"slayer1b-{v}", f"Slayer 1B {v.removesuffix('-hf')}", "base", "Slayer")
            for v in ("1.08", "1.07-hf", "1.06", "1.05", "1.04", "1.03", "1.02", "1.01", "1.00")
        ),
        Model("bielik-11b-v3.1", "Bielik 11B v3.1 Instruct", "instruct", "Bielik"),
        Model("bielik-11b-v3.1-vllm", "Bielik 11B v3.1 Instruct", "instruct", "Bielik"),
        Model("bielik-11b-v3.1-vllm-no-provider", "Bielik 11B v3.1 Instruct", "instruct", "Bielik"),
        Model("lfm3-1.7b-ifeval", "LFM3-1.7B", "instruct", "Liquid"),
        Model("slayer1b-1.08-modal", "Slayer 1B 1.08", "base", "Slayer"),
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
    se_source: str
    review_flag: str
    """The research review's flag of this result (`ok`, or `do_sprawdzenia`: to be checked), `ok` where the source
    has no review."""
    review_notes: tuple[str, ...]


# Benchmarks whose requests have no context to put a BOS token before (empty context, rolling windows), and the one
# whose own code applies the card's rule instead of the run's (research/results/full-run-2026-11/README.md).
NO_BOS: Final = frozenset({"blimp", "wikitext-2"})
CARD_BOS: Final = frozenset({"ewok"})


def bos_variant(benchmark: str, family: str) -> str:
    if benchmark in NO_BOS:
        return "BOS not applicable (empty context or rolling windows)"
    if benchmark in CARD_BOS:
        return "BOS as the card's rule gives it (tokenizer-dependent)"
    return "one BOS" if family == "Slayer" else "no BOS"


def review(repo: Path = REPO) -> dict[tuple[str, str], tuple[str, tuple[str, ...]]]:
    """The research review of the full run (`przeglad.jsonl`): flag and notes per benchmark and model."""
    out = {}
    for line in (repo / FULL_RUN / "przeglad.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        out[(row["benchmark"], row["model"])] = (row["flaga"], tuple(row["uwagi"]))
    return out


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
    flags = review(repo)
    for line in (repo / FULL_RUN / "manifest.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["stan"] != "ok":
            continue
        flag, notes = flags.get((row["benchmark"], row["model"]), ("ok", ()))
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
                variant=f"{row['dtype']}, {bos_variant(b.id, model.family)}",
                harness=f"lm-eval {row['lm_eval']}" if row["lm_eval"] else f"own code ({b.definition})",
                codesota_status=_status(b.id),
                source=_source(repo, f"{FULL_RUN}/{row['benchmark']}/{row['model']}"),
                se_source=f"{FULL_RUN}/manifest.jsonl",
                review_flag=flag,
                review_notes=notes,
            )
        )
    return out


# IFEval of #313: which committed result is which model, and how it ran.
IFEVAL_ROWS: Final = (
    ("slayer1b-1.08", "slayer1b-1.08", "local GPU, raw prompt, greedy"),
    ("slayer1b-1.08-modal", "slayer1b-1.08-modal", "Modal A100, raw prompt, greedy"),
    ("bielik-11b-v3.1", "bielik-11b-v3.1", "Fabryka API, chat template, sampled"),
    ("bielik-11b-v3.1-vllm", "bielik-11b-v3.1-vllm", "own vLLM, chat template, sampled"),
    ("bielik-11b-v3.1-vllm-no-provider", "bielik-11b-v3.1-vllm-no-provider", "own vLLM, no provider system prompt"),
    ("lfm3-1.7b", "lfm3-1.7b-ifeval", "own vLLM, card settings, reasoning on"),
)
# The source README's reading of Slayer's score (research/api-benchmarks/ifeval/README.md, Deviations).
SLAYER_IFEVAL_NOTE: Final = (
    "Slayer 1B is a base model without a chat template; its source reads 18.11 as the score of mostly degenerate "
    "output, not as instruction following."
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
                model_name=model.name,
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
                se_source=path,
                review_flag="ok",
                review_notes=(),
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
        lines.append(f"| {benchmark_name(b)} | `{first.metric}` {arrow} | " + " | ".join(cell(c) for c in cells) + " |")
    return lines


FLAG_NOTE: Final = (
    "† flagged `do_sprawdzenia` (to be checked) by the research review of this run "
    f"([`przeglad.jsonl`](../../{FULL_RUN}/przeglad.jsonl), with the reasons); shown, but not checked."
)
SE_NOTE: Final = (
    "Standard errors are over questions, except over minimal-pair paradigms for BLiMP, over item templates for "
    "EWoK, over twin-sentence pairs for WinoGrande, and over schemas for WSC273."
)


def cell(r: Result | None) -> str:
    if r is None:
        return "n/a"
    return shown(r) + (" †" if r.review_flag != "ok" else "")


# The headline table: the latest Slayer and the models of its size class, ranked per row, then a larger reference
# shown next to them but not ranked. Column headers: name and a second line.
RANKED: Final = (LATEST_SLAYER, "lfm3-1.7b-base", "bielik-1.5b-v3", "qwen3.5-0.8b-base")
LARGER: Final = ("bielik-11b-v3-instruct",)
HEADER: Final[dict[str, tuple[str, str]]] = {
    LATEST_SLAYER: ("Slayer 1B", "1.09 checkpoint"),
    "lfm3-1.7b-base": ("LFM3", "1.7B Base"),
    "bielik-1.5b-v3": ("Bielik", "1.5B v3"),
    "qwen3.5-0.8b-base": ("Qwen3.5", "0.8B Base"),
    "bielik-11b-v3-instruct": ("Bielik 11B", "v3.0 Instruct"),
}
# Row groups of the headline table: Polish first, then English by category.
SECTIONS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("Polish", CATEGORIES["Polish"]),
    ("English · reasoning and science", CATEGORIES["Reasoning and science"]),
    ("English · commonsense", CATEGORIES["Commonsense"]),
    ("English · medical knowledge", CATEGORIES["Knowledge (medical)"]),
    ("English · language modeling and grammar", CATEGORIES["Language modeling and linguistics"]),
)


def value_text(r: Result) -> str:
    """The value alone, as the headline shows it: accuracy in percent with one decimal, perplexity with three."""
    if r.unit == "byte_ppl":
        return f"{r.value:.3f}"
    return f"{r.value * (1.0 if r.unit == 'percent' else 100.0):.1f}"


def ranks(cells: Sequence[Result | None]) -> list[int | None]:
    """Rank of each cell among the others (1 = best), by the shown value, so equal shown values share a rank."""
    present = [c for c in cells if c is not None]
    values = sorted({float(value_text(c)) for c in present}, reverse=present[0].higher_is_better)
    return [None if c is None else values.index(float(value_text(c))) + 1 for c in cells]


def _marked(text: str, rank: int | None) -> str:
    return f"<b>{text}</b>" if rank == 1 else f"<ins>{text}</ins>" if rank == 2 else text


def headline_table(rows: Sequence[Result]) -> list[str]:
    """The headline as an HTML table (GitHub renders it; Markdown tables cannot have group rows)."""
    by = {(r.benchmark, r.model): r for r in rows if r.protocol == "full-run-2026-11"}
    models = (*RANKED, *LARGER)
    head = "".join(f"<th>{HEADER[m][0]}<br><sub>{HEADER[m][1]}</sub></th>" for m in models)
    lines = ["<table>", f'<tr><th align="left">Benchmark</th>{head}</tr>']
    for section, benchmarks in SECTIONS:
        lines.append(f'<tr><td colspan="{1 + len(models)}"><b>{section}</b></td></tr>')
        for b in benchmarks:
            cells = [by.get((b, m)) for m in models]
            if all(c is None for c in cells):
                continue
            ranked = ranks(cells[: len(RANKED)]) + [None] * len(LARGER)
            first = next(c for c in cells if c is not None)
            name = benchmark_name(b) + ("" if first.higher_is_better else " ↓")
            tds = "".join(
                f'<td align="right">{"n/a" if c is None else _marked(value_text(c), k)}</td>'
                for c, k in zip(cells, ranked, strict=True)
            )
            lines.append(f"<tr><td>{name}</td>{tds}</tr>")
    lines.append("</table>")
    return lines


def readme(rows: Sequence[Result]) -> str:
    ifeval_rows = {r.model: r for r in rows if r.benchmark == "ifeval"}
    slayer_if, bielik_if = ifeval_rows["slayer1b-1.08"], ifeval_rows["bielik-11b-v3.1"]
    lines = [
        "# Results",
        "",
        "Slayer 1B next to models of its size, on the same benchmarks with the same settings.",
        "",
        *headline_table(rows),
        "",
        "Accuracy in %, 0-shot. ↓ lower is better (WikiText-2: perplexity per byte). **Bold**: best of the four "
        "small models, <ins>underlined</ins>: second. Bielik 11B is about ten times larger and is shown for "
        "reference, without a rank.",
        "",
        f"**Instruction following (IFEval):** Bielik 11B v3.1 Instruct {value_text(bielik_if)}, "
        f"Slayer 1B 1.08 {value_text(slayer_if)}. Slayer is a base model without a chat template, so its score "
        "mostly reflects broken output, not instruction following. [Details](instruction-following.md).",
        "",
        '<p align="center"><img src="charts/headline.png" alt="Accuracy per benchmark: Slayer 1B 1.09 and the '
        'reference models" width="100%"></p>',
        "",
        "[All models](all-models.md) · [Instruction following](instruction-following.md) · "
        "[All results as JSONL](results.jsonl) · [Benchmark status](../BENCHMARKS.md)",
        "",
        "## Notes",
        "",
        "- **Slayer 1B 1.09 is a training checkpoint** (step 40 000), not a release.",
        "- **How it was measured:** the full test set of each benchmark, 0-shot, each answer scored by the "
        "model's probability of it (lm-eval; BLiMP and EWoK: their own code), float32 (Bielik 11B: bfloat16), "
        "no chat template. Slayer's "
        "inputs start with one BOS token, the other models' with none.",
        "- **Small differences are noise.** Values with their standard errors are in [all models](all-models.md) "
        f"and [`results.jsonl`](results.jsonl); a difference of one or two points is often within them. {SE_NOTE}",
        "- **Bielik 11B and LFM3-1.7B (in the full tables) are instruction-tuned**, scored here on raw text like "
        "the base models.",
        "- Results flagged for checking by the research review are marked † in the [full tables](all-models.md); "
        "none is on this page.",
        "- Generated by `python -m codesota.leaderboard` from the result files below; do not edit by hand.",
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
    by = {r.model: r for r in rows if r.benchmark == "ifeval"}
    for m in models:
        r = by[m]
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
        f"Protocol: {PROTOCOLS['full-run-2026-11']} {SE_NOTE}",
        "",
        FLAG_NOTE,
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
        f"Parameters from [`sizes.json`](../../{FULL_RUN}/sizes.json); n/a where it has no entry.",
        "",
        "| model | parameters | type | revision |",
        "|---|---:|---|---|",
    ]
    sizes = json.loads((REPO / FULL_RUN / "sizes.json").read_text(encoding="utf-8"))
    for m in present:
        r = next(x for x in log_lik if x.model == m)
        revision = (r.revision or "")[:8]
        params = f"{sizes[m]['params'] / 1e9:.2f}B" if m in sizes else "n/a"
        lines.append(f"| {MODELS[m].name} | {params} | {MODELS[m].kind} | `{r.repo}` @ `{revision}` |")
    return "\n".join(lines) + "\n"


def instruction_following(rows: Sequence[Result]) -> str:
    lines = [
        "# Instruction following",
        "",
        "Generated by `python -m codesota.leaderboard`. [Back to the results](README.md).",
        "",
        "## IFEval",
        "",
        f"{PROTOCOLS['ifeval-api']} {SLAYER_IFEVAL_NOTE}",
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
# The four benchmarks with a reproduced reference (`verified`), the largest English test (HellaSwag), and the Polish
# one.
SNAPSHOT_BENCHMARKS: Final = ("arc-easy", "piqa", "winogrande", "lambada", "hellaswag", "multiblimp-pl")


def snapshot(rows: Sequence[Result]) -> str:
    """The short table of benchmarks/README.md: the latest Slayer next to Bielik 11B on SNAPSHOT_BENCHMARKS, plus
    IFEval."""
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
    benchmarks = [b for _, bs in SECTIONS for b in bs if any(r.benchmark == b for r in log_lik)]
    by = {(r.benchmark, r.model): r for r in log_lik}
    models = (*RANKED, *LARGER)
    width = 0.8 / len(models)
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": "#cccccc", "axes.labelcolor": "#444444"})
    fig, ax = plt.subplots(figsize=(14, 5), dpi=120)
    # Slayer in red, the other small models in greys, the larger reference as an outline.
    styles: tuple[dict[str, Any], ...] = (
        {"color": "#b3202e"},
        {"color": "#55595f"},
        {"color": "#8b9097"},
        {"color": "#bfc3c8"},
        {"color": "white", "edgecolor": "#55595f", "linewidth": 0.8},
    )
    for i, (m, style) in enumerate(zip(models, styles, strict=True)):
        xs, ys, es = [], [], []
        for j, b in enumerate(benchmarks):
            r = by.get((b, m))
            if r is None:
                continue
            scale = 1.0 if r.unit == "percent" else 100.0
            xs.append(j - 0.4 + width * (i + 0.5))
            ys.append(r.value * scale)
            es.append((r.se or 0.0) * scale)
        label = " ".join(HEADER[m]) + (" (larger reference)" if m in LARGER else "")
        ax.bar(xs, ys, width, yerr=es, label=label, error_kw={"elinewidth": 0.6, "ecolor": "#777777"}, **style)
    ax.set_xticks(range(len(benchmarks)), [benchmark_name(b) for b in benchmarks], rotation=30, ha="right")
    ax.set_ylabel("accuracy (%)")
    ax.set_ylim(0, 100)
    ax.grid(axis="y", color="#eeeeee")
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(ncol=5, fontsize=9, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.1))
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
