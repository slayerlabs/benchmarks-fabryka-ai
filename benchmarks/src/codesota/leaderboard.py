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


# The headline table: column headers (name and a second line) of the HEADLINE models, and its row groups, Polish
# first, then English by category.
HEADER: Final[dict[str, tuple[str, str]]] = {
    LATEST_SLAYER: ("Slayer 1B", "1.09 checkpoint"),
    "bielik-11b-v3-instruct": ("Bielik 11B", "v3.0 Instruct"),
    "lfm3-1.7b-base": ("LFM3", "1.7B Base"),
    "bielik-1.5b-v3": ("Bielik", "1.5B v3"),
    "qwen3.5-0.8b-base": ("Qwen3.5", "0.8B Base"),
}
SECTIONS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("Polish", CATEGORIES["Polish"]),
    ("English · reasoning and science", CATEGORIES["Reasoning and science"]),
    ("English · commonsense", CATEGORIES["Commonsense"]),
    ("English · medical knowledge", CATEGORIES["Knowledge (medical)"]),
    ("English · language modeling and grammar", CATEGORIES["Language modeling and linguistics"]),
)
LEGEND: Final = (
    "Accuracy in %, 0-shot · ↓ lower is better (WikiText-2: perplexity per byte) · best of the five highlighted, "
    "second underlined"
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


Cell = tuple[str, Result | None, int | None]  # benchmark, result, rank


def headline_rows(rows: Sequence[Result]) -> list[tuple[str, list[tuple[str, list[Cell]]]]]:
    """The headline's row groups: per section, per benchmark its shown name and one cell per HEADLINE model."""
    by = {(r.benchmark, r.model): r for r in rows if r.protocol == "full-run-2026-11"}
    out = []
    for section, benchmarks in SECTIONS:
        lines = []
        for b in benchmarks:
            cells = [by.get((b, m)) for m in HEADLINE]
            if all(c is None for c in cells):
                continue
            first = next(c for c in cells if c is not None)
            name = benchmark_name(b) + ("" if first.higher_is_better else " ↓")
            lines.append((name, [(b, c, k) for c, k in zip(cells, ranks(cells), strict=True)]))
        out.append((section, lines))
    return out


@dataclass(frozen=True)
class Theme:
    background: str
    text: str
    muted: str
    rule: str
    row_rule: str
    best_fill: str
    accent: str


LIGHT: Final = Theme("#ffffff", "#1f2328", "#59636e", "#d1d9e0", "#eef1f4", "#fbe3e4", "#b3202e")
DARK: Final = Theme("#0d1117", "#e6edf3", "#9198a1", "#3d444d", "#21262d", "#4a1d22", "#ff8a80")
FONT: Final = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def headline_svg(rows: Sequence[Result], t: Theme) -> str:
    """The headline table as an SVG image, styled as GitHub cannot style a Markdown table: no grid, the best value
    of each row highlighted in red, the second underlined. Each value carries its benchmark, model, and rank."""
    name_width, col, pad, row_h = 300, 112, 24, 32
    width = pad * 2 + name_width + col * len(HEADLINE)

    def center(i: int) -> float:
        return pad + name_width + col * i + col / 2

    body: list[str] = []
    for i, m in enumerate(HEADLINE):
        body.append(f'<text x="{center(i)}" y="38" text-anchor="middle" font-weight="600">{_esc(HEADER[m][0])}</text>')
        body.append(
            f'<text x="{center(i)}" y="56" text-anchor="middle" font-size="12" fill="{t.muted}">'
            f"{_esc(HEADER[m][1])}</text>"
        )
    body.append(f'<text x="{pad}" y="56" font-size="12" fill="{t.muted}">Benchmark</text>')
    y = 70
    body.append(f'<line x1="{pad}" x2="{width - pad}" y1="{y}" y2="{y}" stroke="{t.rule}"/>')
    for section, lines in headline_rows(rows):
        y += row_h
        body.append(
            f'<text x="{pad}" y="{y - 10}" font-size="13" font-weight="600" fill="{t.muted}">{_esc(section)}</text>'
        )
        for name, cells in lines:
            body.append(f'<line x1="{pad}" x2="{width - pad}" y1="{y}" y2="{y}" stroke="{t.row_rule}"/>')
            y += row_h
            base = y - 11
            body.append(f'<text x="{pad}" y="{base}">{_esc(name)}</text>')
            for i, (b, c, k) in enumerate(cells):
                if k == 1:
                    body.append(
                        f'<rect x="{center(i) - 34}" y="{base - 16}" width="68" height="22" rx="5" '
                        f'fill="{t.best_fill}"/>'
                    )
                elif k == 2:
                    body.append(
                        f'<line x1="{center(i) - 18}" x2="{center(i) + 18}" y1="{base + 3}" y2="{base + 3}" '
                        f'stroke="{t.text}"/>'
                    )
                style = f' font-weight="700" fill="{t.accent}"' if k == 1 else f' fill="{t.muted}"' if c is None else ""
                body.append(
                    f'<text x="{center(i)}" y="{base}" text-anchor="middle"{style} data-benchmark="{b}" '
                    f'data-model="{HEADLINE[i]}" data-rank="{k or 0}">{"n/a" if c is None else value_text(c)}</text>'
                )
    y += 8
    body.append(f'<line x1="{pad}" x2="{width - pad}" y1="{y}" y2="{y}" stroke="{t.rule}"/>')
    y += 24
    body.append(f'<text x="{pad}" y="{y}" font-size="12" fill="{t.muted}">{_esc(LEGEND)}</text>')
    height = y + 16
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" font-family="{FONT}" font-size="14" fill="{t.text}">',
            f'<rect width="{width}" height="{height}" rx="8" fill="{t.background}"/>',
            *body,
            "</svg>",
            "",
        ]
    )


def values_table(rows: Sequence[Result]) -> list[str]:
    """The headline's values with their standard errors, as an HTML table (Markdown tables have no group rows)."""
    head = "".join(f"<th>{HEADER[m][0]}<br><sub>{HEADER[m][1]}</sub></th>" for m in HEADLINE)
    out = ["<table>", f'<tr><th align="left">Benchmark</th>{head}</tr>']
    for section, lines in headline_rows(rows):
        out.append(f'<tr><td colspan="{1 + len(HEADLINE)}"><b>{section}</b></td></tr>')
        for name, cells in lines:
            tds = "".join(f'<td align="right">{"n/a" if c is None else shown(c)}</td>' for _, c, _ in cells)
            out.append(f"<tr><td>{name}</td>{tds}</tr>")
    out.append("</table>")
    return out


def readme(rows: Sequence[Result]) -> str:
    ifeval_rows = {r.model: r for r in rows if r.benchmark == "ifeval"}
    slayer_if, bielik_if = ifeval_rows["slayer1b-1.08"], ifeval_rows["bielik-11b-v3.1"]
    lines = [
        "# Results",
        "",
        "Slayer 1B next to its reference models, on the same benchmarks with the same settings.",
        "",
        "<picture>",
        '  <source media="(prefers-color-scheme: dark)" srcset="charts/headline-table-dark.svg">',
        '  <img src="charts/headline-table.svg" alt="Results table: Slayer 1B 1.09, Bielik 11B, LFM3-1.7B-Base, '
        'Bielik 1.5B v3 and Qwen3.5-0.8B-Base on 14 benchmarks; the same values are in the Values table below" '
        'width="100%">',
        "</picture>",
        "",
        f"**Instruction following (IFEval):** Bielik 11B v3.1 Instruct {value_text(bielik_if)}, "
        f"Slayer 1B 1.08 {value_text(slayer_if)}. Slayer is a base model without a chat template, so its score "
        "mostly reflects broken output, not instruction following. [Details](instruction-following.md).",
        "",
        "<picture>",
        '  <source media="(prefers-color-scheme: dark)" srcset="charts/headline-dark.png">',
        '  <img src="charts/headline.png" alt="Accuracy per benchmark: Slayer 1B 1.09 and the reference models" '
        'width="100%">',
        "</picture>",
        "",
        "[All models](all-models.md) · [Instruction following](instruction-following.md) · "
        "[All results as JSONL](results.jsonl) · [Benchmark status](../BENCHMARKS.md)",
        "",
        "## Notes",
        "",
        "- **Slayer 1B 1.09 is a training checkpoint** (step 40 000), not a release.",
        "- **Bielik 11B is about ten times larger** than the others and instruction-tuned; it is the closest Polish "
        "reference. LFM3-1.7B (in the full tables) is instruction-tuned too. All are scored on raw text.",
        "- **How it was measured:** the full test set of each benchmark, 0-shot, each answer scored by the "
        "model's probability of it (lm-eval; BLiMP and EWoK: their own code), float32 (Bielik 11B: bfloat16), "
        "no chat template. Slayer's inputs start with one BOS token, the other models' with none.",
        "- **Small differences are noise:** a difference of one or two points is often within the standard errors "
        "below.",
        "- Results flagged for checking by the research review are marked † in the [full tables](all-models.md); "
        "none is on this page.",
        "- Generated by `python -m codesota.leaderboard` from the result files below; do not edit by hand.",
        "",
        "## Values",
        "",
        f"Value ± standard error, accuracy in %. {SE_NOTE}",
        "",
        *values_table(rows),
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
        "charts/headline-table.svg": headline_svg(rows, LIGHT),
        "charts/headline-table-dark.svg": headline_svg(rows, DARK),
    }


# --- charts ---


def charts(rows: Sequence[Result], out: Path) -> None:
    """The headline chart, light and dark: accuracy per benchmark for the headline models, with ± 1 SE."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    log_lik = [r for r in rows if r.protocol == "full-run-2026-11" and r.unit != "byte_ppl"]
    benchmarks = [b for _, bs in SECTIONS for b in bs if any(r.benchmark == b for r in log_lik)]
    by = {(r.benchmark, r.model): r for r in log_lik}
    width = 0.8 / len(HEADLINE)
    # Slayer in red, Bielik 11B darkest, the other references in lighter greys.
    greys = {LIGHT: ("#3d4148", "#6e737b", "#9da2a9", "#c9ccd1"), DARK: ("#c9d1d9", "#8b949e", "#6e7681", "#484f58")}
    out.mkdir(parents=True, exist_ok=True)
    for theme, name in ((LIGHT, "headline.png"), (DARK, "headline-dark.png")):
        colors = (theme.accent, *greys[theme])
        plt.rcParams.update(
            {
                "font.family": "DejaVu Sans",
                "text.color": theme.text,
                "axes.edgecolor": theme.rule,
                "axes.labelcolor": theme.muted,
                "xtick.color": theme.muted,
                "ytick.color": theme.muted,
            }
        )
        fig, ax = plt.subplots(figsize=(14, 5), dpi=120)
        fig.patch.set_facecolor(theme.background)
        ax.set_facecolor(theme.background)
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
            ax.bar(
                xs,
                ys,
                width,
                yerr=es,
                color=color,
                label=" ".join(HEADER[m]),
                error_kw={"elinewidth": 0.6, "ecolor": theme.muted},
            )
        ax.set_xticks(range(len(benchmarks)), [benchmark_name(b) for b in benchmarks], rotation=30, ha="right")
        ax.set_ylabel("accuracy (%)")
        ax.set_ylim(0, 100)
        ax.grid(axis="y", color=theme.row_rule)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(ncol=5, fontsize=9, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.1))
        fig.tight_layout()
        fig.savefig(out / name, metadata={"Software": None}, facecolor=theme.background)
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
        (OUT / n).parent.mkdir(parents=True, exist_ok=True)
        (OUT / n).write_text(t, encoding="utf-8", newline="\n")
    if not args.no_charts:
        charts(collect(), OUT / "charts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
