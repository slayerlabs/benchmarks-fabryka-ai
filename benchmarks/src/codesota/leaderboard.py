"""The results page: every published result in one place, normalized, with Slayer 1B first.

`python -m codesota.leaderboard` reads the results the research pipeline published and writes `benchmarks/results/`:

- `results.jsonl`: one line per benchmark, model, and metric, with its uncertainty, protocol, and source file;
- `README.md`: the latest Slayer 1B next to the headline reference models, by category and language;
- `all-models.md`: every model of every run, by category;
- `instruction-following.md`: instruction-following benchmarks, which use a different protocol per model;
- `charts/headline-table*.svg`: the headline table as an image, light and dark.

The source files stay where they are: this module only reads them. Nothing here is recomputed; values, standard
errors, and counts are those of the source. `python -m codesota.leaderboard --check` fails when the files differ from
what the sources give (`tests/test_leaderboard.py` runs it).
"""

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
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
LATEST_SLAYER: Final = "slayer1b-1.09-k70000"
HEADLINE: Final = (LATEST_SLAYER, "bielik-11b-v3-instruct", "lfm3-1.7b-base", "bielik-1.5b-v3", "qwen3.5-0.8b-base")
MODELS: Final[dict[str, Model]] = {
    m.label: m
    for m in (
        Model(LATEST_SLAYER, "Slayer 1B 1.09 (step 70 000, training in progress)", "base", "Slayer"),
        Model("slayer1b-60000", "Slayer 1B 1.09 (step 60 000)", "base", "Slayer"),
        Model("slayer1b-1.09-k40000", "Slayer 1B 1.09 (step 40 000)", "base", "Slayer"),
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


# --- generative and agentic benchmarks (research/api-benchmarks/) ---

API_DIR = "research/api-benchmarks"
MINUS: Final = "\u2212"
# The three models of the generative table: the column key, its header, and its family.
API_COLUMNS: Final = ("slayer", "bielik", "lfm3")
API_HEADER: Final[dict[str, tuple[str, str]]] = {
    "slayer": ("Slayer 1B", "1.09 / 1.08"),
    "bielik": ("Bielik 11B", "v3.1 Instruct"),
    "lfm3": ("LFM3", "1.7B Instruct"),
}


@dataclass(frozen=True)
class ApiBenchmark:
    """One generative or agentic benchmark of `research/api-benchmarks/<directory>/`, with the result file of each
    column (its model label; the file is `results/<label>.json` unless `files` names another stem) and the value the
    LFM3-1.7B card reports.

    - `pr` is the open pull request the results come from (None once merged). `caveat` says why the results need
      verification: a PR in review, or a merged result that is not the benchmark's main row. Either marks every value
      of the benchmark with *.
    - A column without a score is "null" when the model cannot run the benchmark (research/METHODOLOGY.md), and
      "not run" when it was not run, by decision, for budget, or not yet. `not_run` names the columns of the second
      kind, with a reason for when the result file has none; `null_reasons` gives the reason of a null whose file has
      none. A result file's own `reason` or `score_null_reason` wins over both; `reason_text` replaces it with a
      shorter wording of the same reason when the file's text is written for the benchmark's maintainers.
    - `se_field` is the result file's field shown as the standard error.
    - `note` is what a reader needs to read the values right; it is shown next to them, without *.
    - `ranked` is False when the order of the scores would mislead (the best value is not the better model); the row
      is then shown without the best and second marks."""

    id: str
    name: str
    section: str
    directory: str
    unit: str
    labels: Mapping[str, str]
    how: Mapping[str, str]
    card: float | None
    pr: int | None = None
    caveat: str = ""
    files: Mapping[str, str] = field(default_factory=dict)
    null_reasons: Mapping[str, str] = field(default_factory=dict)
    not_run: Mapping[str, str] = field(default_factory=dict)
    reason_text: Mapping[str, str] = field(default_factory=dict)
    se_field: str = "stderr"
    note: str = ""
    ranked: bool = True

    @property
    def starred(self) -> bool:
        return self.pr is not None or bool(self.caveat)

    def path(self, column: str) -> str:
        label = self.labels[column]
        return f"{API_DIR}/{self.directory}/results/{self.files.get(column, label)}.json"


NO_TOOL_CALLS: Final = "base model without a chat template or a tool-call format, so the agent cannot drive it"
SLAYER_COST: Final = (
    "a cost decision: Slayer 1B passed 0 of the 30 Python tasks of PAPER.md, H5.1, so the benchmark was judged not "
    "worth its cost"
)
OWN_VLLM: Final = "own vLLM, chat template"
API: Final = "Fabryka API, chat template"
LM_EVAL: Final = "local lm-eval, CoT, greedy, 8192 tokens"
SLAYER_RAW: Final = "raw prompt, no chat template"
STEP_60K: Final = f"step 60 000, {SLAYER_RAW}"
API_BENCHMARKS: Final[tuple[ApiBenchmark, ...]] = (
    ApiBenchmark(
        "ifeval",
        "IFEval",
        "Instruction following",
        "ifeval",
        "percent",
        {"slayer": "slayer1b-1.08", "bielik": "bielik-11b-v3.1", "lfm3": "lfm3-1.7b-ifeval"},
        {"slayer": "1.08, local GPU, raw prompt, greedy", "bielik": API, "lfm3": "own vLLM, card settings"},
        96.66,
        files={"lfm3": "lfm3-1.7b"},
        note="the values are prompt-level strict accuracy. The card does not name its metric and probably does not "
        "report strict: LFM3 scores 94.64 strict and 96.49 prompt-level loose, against the card's 96.66 (README, "
        "Deviations). Bielik's value is the API run; with its template defaults on our vLLM it scores 60.63, "
        "5.36 ± 1.86 points higher",
    ),
    ApiBenchmark(
        "ifbench",
        "IFBench",
        "Instruction following",
        "ifbench",
        "percent",
        {"slayer": "slayer1b-60000", "bielik": "bielik-11b-v3.1-vllm"},
        {"slayer": STEP_60K, "bielik": OWN_VLLM},
        73.03,
    ),
    ApiBenchmark(
        "ifstruct",
        "IFStruct",
        "Instruction following",
        "ifstruct",
        "percent",
        {"slayer": "slayer1b-60000", "bielik": "bielik-11b-v3.1-vllm"},
        {"slayer": STEP_60K, "bielik": OWN_VLLM},
        93.72,
    ),
    ApiBenchmark(
        "multi-if",
        "Multi-IF",
        "Instruction following",
        "multi-if",
        "percent",
        {"slayer": "slayer1b-60000", "bielik": "bielik-11b-v3.1-vllm"},
        {"slayer": STEP_60K, "bielik": OWN_VLLM},
        89.10,
        not_run={"slayer": "run stopped for compute budget"},
        note="n counts turns: 13447 turns of 4501 conversations; the standard error is a cluster bootstrap over "
        "conversations",
    ),
    ApiBenchmark(
        "gpqa-diamond",
        "GPQA Diamond",
        "Knowledge",
        "gpqa-diamond",
        "percent",
        {"slayer": LATEST_SLAYER, "bielik": "bielik-11b-v3.1", "lfm3": "lfm3-1.7b"},
        {"slayer": "not run", "bielik": LM_EVAL, "lfm3": LM_EVAL},
        63.37,
        caveat="an exploratory local run, which the benchmark's README marks as a draft: its main row (Fabryka API, "
        "the card's settings) is not computed, and these values do not close its issue (#302)",
        not_run={"slayer": "not run yet, an open item of the README (no result file)"},
        note="the exploratory run caps answers at 8192 tokens, and 74 of LFM3's 198 answers are cut there (13 of "
        "them still score correct). With a larger cap LFM3 reaches 58.59 at 16384 and 62.63 to 64.65 at 32768 (two "
        "compositions), within noise of the card's 63.37. Bielik is not limited by the cap (36.36 at 2048). Both "
        "models ran locally with lm-eval, on different GPUs",
    ),
    ApiBenchmark(
        "aa-omniscience",
        "AA-Omniscience",
        "Knowledge",
        "aa-omniscience",
        "index",
        {"slayer": "slayer1b-60000", "bielik": "bielik-11b-v3.1-vllm"},
        {"slayer": STEP_60K, "bielik": OWN_VLLM},
        0.50,
        note="Slayer's higher index is not more knowledge: it answers 10 of 600 correctly (accuracy 1.67, Bielik "
        "11.17), and its index is higher only because 223 of its answers, cut at the 1280-token limit, are graded "
        "not attempted, which the index does not subtract. The row is therefore not ranked. Our grades come from a "
        "different judge (GPT-6.1 Sol) than the official grader (Gemini 2.5 Flash Preview), so the values cannot be "
        "compared with the card's 0.50 or with Artificial Analysis' numbers (README)",
        ranked=False,
    ),
    ApiBenchmark(
        "livecodebench-v6",
        "LiveCodeBench v6",
        "Coding",
        "livecodebench-v6",
        "percent",
        {"slayer": LATEST_SLAYER, "bielik": "bielik-11b-v3.1", "lfm3": "lfm3-1.7b"},
        {"slayer": "not run", "bielik": f"{API}, no reasoning (API default)", "lfm3": "own vLLM, thinking"},
        73.46,
        not_run={"slayer": f"{SLAYER_COST} (README, Deviations; no result file)"},
        note="Bielik without reasoning (the API default; reasoning cannot be switched on through the API). LFM3 "
        "with the card's sampling: 73.08 ± 1.37",
    ),
    ApiBenchmark(
        "livecodebench-pro-25q2",
        "LiveCodeBench Pro 25Q2",
        "Coding",
        "livecodebench-pro-25q2",
        "percent",
        {"slayer": "slayer1b-1.09-k70000", "bielik": "bielik-11b-v3.1", "lfm3": "lfm3-1.7b"},
        {"slayer": f"step 70 000, {SLAYER_RAW}, greedy, context 4096", "bielik": API, "lfm3": "own vLLM, thinking"},
        31.74,
        note="LFM3 without thinking: 28.74 ± 3.50",
    ),
    ApiBenchmark(
        "scicode",
        "SciCode",
        "Coding",
        "scicode",
        "percent",
        {"slayer": "slayer1b-1.09-k70000", "bielik": "bielik-11b-v3.1", "lfm3": "lfm3-1.7b"},
        {
            "slayer": f"step 70 000, {SLAYER_RAW}, greedy, context 4096",
            "bielik": API,
            "lfm3": "own vLLM, thinking, with background",
        },
        28.47,
        se_field="stderr_clustered",
        reason_text={
            "slayer": "with background, 216 of 288 prompts leave fewer than 256 of its 4096 context tokens for the "
            "answer, so the score is null (README, PROTOCOL.md Amendment 3)",
        },
        note="n counts the 288 steps; the standard error is clustered over the 65 problems, as in the README (over "
        "steps it would be 2.76 for LFM3). The control against the card passes both with and without background "
        "(22.92), so it cannot confirm the card's setup. LFM3 without thinking: 24.65. Slayer without background: "
        "0.00 (0/288)",
    ),
    ApiBenchmark(
        "ruler-128k",
        "RULER 128K",
        "Long context",
        "ruler-128k",
        "percent",
        {"slayer": "slayer1b-1.09-k70000", "bielik": "bielik-11b-v3.1", "lfm3": "lfm3-1.7b"},
        {"slayer": "4096-token context", "bielik": f"{API}, 32768-token context", "lfm3": "own vLLM, 262144 tokens"},
        65.56,
        note="RULER's substring scorer has no answer cap here, so 71.69 is not comparable to RULER numbers in the "
        "literature; capped to RULER's answer budget: 67.20 ± 1.00. The control against the card failed",
    ),
    ApiBenchmark(
        "aa-lcr",
        "AA-LCR",
        "Long context",
        "aa-lcr",
        "percent",
        {"slayer": LATEST_SLAYER, "bielik": "bielik-11b-v3.1"},
        {"slayer": "4096-token context", "bielik": f"{API}, 32768-token context"},
        52.83,
        null_reasons={
            "slayer": "the 4096-token window holds no AA-LCR prompt (shortest 85211 tokens)",
            "bielik": "the 32768-token window holds no AA-LCR prompt (shortest 100913 tokens)",
        },
    ),
    ApiBenchmark(
        "bfcl-v4",
        "BFCL V4",
        "Tool use",
        "bfcl-v4",
        "percent",
        {"slayer": "slayer1b-60000", "bielik": "bielik-11b-v3.1-vllm"},
        {"slayer": "step 60 000", "bielik": OWN_VLLM},
        71.39,
        not_run={"bielik": "web_search categories not run"},
        note="Bielik's Overall is not computed, because the web_search categories (20% of its weight) were not run. "
        "The other categories bound it: at least 28.41, and at most 48.41 with web_search at 100, below the card's "
        "71.39",
    ),
    ApiBenchmark(
        "terminal-bench-2-1",
        "Terminal-Bench 2.1",
        "Agentic coding",
        "terminal-bench-2-1",
        "percent",
        {"slayer": LATEST_SLAYER, "lfm3": "lfm3-1.7b"},
        {"slayer": "step 70 000", "lfm3": "own vLLM, OpenCode, 5 trials per task"},
        12.92,
        341,
        "PR #341 in review; Bielik not run yet",
        null_reasons={"slayer": NO_TOOL_CALLS},
    ),
    ApiBenchmark(
        "automationbench",
        "AutomationBench",
        "Agents",
        "automationbench",
        "percent",
        {"slayer": "slayer1b-60000", "bielik": "bielik-11b-v3.1-vllm"},
        {"slayer": "step 60 000", "bielik": OWN_VLLM},
        41.29,
    ),
)
API_BY_ID: Final = {b.id: b for b in API_BENCHMARKS}


def _api_file(repo: Path, b: ApiBenchmark, column: str) -> dict[str, Any] | None:
    path = repo / b.path(column)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def api_results(repo: Path = REPO) -> list[Result]:
    """Every scored result of the generative table, except IFEval (read by `ifeval`)."""
    out = []
    for b in API_BENCHMARKS:
        if b.id == "ifeval":
            continue
        for column, label in b.labels.items():
            row = _api_file(repo, b, column)
            if row is None or row["score"] is None:
                continue
            model = MODELS[label]
            out.append(
                Result(
                    benchmark=b.id,
                    legacy_id=None,
                    category=b.section,
                    language="EN" if b.id != "multi-if" else "multi",
                    metric=str(row["metric"]),
                    unit=b.unit,
                    higher_is_better=True,
                    model=label,
                    model_name=model.name,
                    repo=None,
                    revision=None,
                    value=float(row["score"]),
                    se=None if row[b.se_field] is None else float(row[b.se_field]),
                    n=int(row["n"]),
                    protocol="api-benchmarks",
                    variant=b.how[column],
                    harness=str(row["harness"]),
                    codesota_status=_status(b.id),
                    source=b.path(column),
                    se_source=b.path(column) if b.se_field == "stderr" else f"{b.path(column)} ({b.se_field})",
                    review_flag="in_review" if b.pr else "exploratory" if b.caveat else "ok",
                    review_notes=(b.caveat,) if b.caveat else (),
                )
            )
    return out


def collect(repo: Path = REPO) -> list[Result]:
    order = {label: i for i, label in enumerate(MODELS)}
    bench_order = {b: i for i, b in enumerate([*CATEGORY_OF, *(x.id for x in API_BENCHMARKS if x.id != "ifeval")])}
    rows = full_run(repo) + ifeval(repo) + api_results(repo)
    return sorted(rows, key=lambda r: (bench_order[r.benchmark], order[r.model], r.metric))


# --- formatting ---


def shown(r: Result) -> str:
    """Accuracies as percent with one decimal (66.6 ± 1.0); perplexity as is (1.702 ± 0.011)."""
    if r.unit == "byte_ppl":
        return f"{r.value:.3f}" + (f" ± {r.se:.3f}" if r.se is not None else "")
    scale = 1.0 if r.unit in ("percent", "index") else 100.0
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
    LATEST_SLAYER: ("Slayer 1B", "1.09 step 70k"),
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
    "second underlined · Random: chance level"
)
# The Slayer versions page: every Slayer of the full run, oldest first, with the same table.
SLAYER_VERSIONS: Final = (
    "slayer1b-1.00",
    "slayer1b-1.01",
    "slayer1b-1.02",
    "slayer1b-1.03",
    "slayer1b-1.04",
    "slayer1b-1.05",
    "slayer1b-1.06",
    "slayer1b-1.07-hf",
    "slayer1b-1.08",
    "slayer1b-1.09-k40000",
    LATEST_SLAYER,
)
SLAYER_HEADER: Final[dict[str, tuple[str, str]]] = {
    **{m: (m.removeprefix("slayer1b-"), "") for m in SLAYER_VERSIONS[:7]},
    "slayer1b-1.07-hf": ("1.07", "HF weights"),
    "slayer1b-1.08": ("1.08", ""),
    "slayer1b-1.09-k40000": ("1.09", "step 40k"),
    LATEST_SLAYER: ("1.09", "step 70k"),
}
SLAYER_LEGEND: Final = (
    "Accuracy in %, 0-shot · ↓ lower is better · best version highlighted, second underlined · Random: chance level"
)


def majority_level(benchmark: str, repo: Path = REPO) -> float:
    """Score of always giving the most common answer of a test, in percent (`bazy.majority_value`)."""
    path = repo / FULL_RUN / benchmark / LATEST_SLAYER / "results_rozszerzone.json"
    o = json.loads(path.read_text(encoding="utf-8"))["observations"][0]
    return 100 * float(o["dodatkowe"]["space"]["bazy"]["majority_value"])


def chance_levels(repo: Path = REPO) -> dict[str, float | None]:
    """Chance level of each benchmark of the tables, in percent, from its result file (`bazy.chance_value`: the mean
    of 1 / number of options, a property of the test). None where there is none (WikiText-2)."""
    out: dict[str, float | None] = {}
    for _, benchmarks in SECTIONS:
        for b in benchmarks:
            path = repo / FULL_RUN / b / LATEST_SLAYER / "results_rozszerzone.json"
            o = json.loads(path.read_text(encoding="utf-8"))["observations"][0]
            space = (o.get("dodatkowe") or {}).get("space") or {}
            c = (space.get("bazy") or {}).get("chance_value")
            out[b] = None if c is None else 100 * c
    return out


def value_text(r: Result) -> str:
    """The value alone, as the headline shows it: accuracy in percent with one decimal, perplexity with three."""
    if r.unit == "byte_ppl":
        return f"{r.value:.3f}"
    return f"{r.value * (1.0 if r.unit in ('percent', 'index') else 100.0):.1f}"


def ranks(cells: Sequence[Result | None]) -> list[int | None]:
    """Rank of each cell among the others (1 = best), by the shown value, so equal shown values share a rank."""
    present = [c for c in cells if c is not None]
    values = sorted({float(value_text(c)) for c in present}, reverse=present[0].higher_is_better)
    return [None if c is None else values.index(float(value_text(c))) + 1 for c in cells]


Cell = tuple[str, Result | None, int | None]  # benchmark, result, rank


def headline_rows(
    rows: Sequence[Result], models: Sequence[str] = HEADLINE
) -> list[tuple[str, list[tuple[str, list[Cell]]]]]:
    """Row groups of a results table: per section, per benchmark its shown name and one cell per model."""
    by = {(r.benchmark, r.model): r for r in rows if r.protocol == "full-run-2026-11"}
    out = []
    for section, benchmarks in SECTIONS:
        lines = []
        for b in benchmarks:
            cells = [by.get((b, m)) for m in models]
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


def headline_svg(
    rows: Sequence[Result],
    t: Theme,
    chance: Mapping[str, float | None],
    models: Sequence[str] = HEADLINE,
    header: Mapping[str, tuple[str, str]] = HEADER,
    legend: str = LEGEND,
    col: int = 100,
) -> str:
    """A results table as an SVG image, styled as GitHub cannot style a Markdown table: no grid, the best value of
    each row highlighted in red, the second underlined, the chance level last. Each value carries its benchmark,
    model, and rank; each chance level its benchmark."""
    name_width, pad, row_h = 220, 20, 34
    width = pad * 2 + name_width + col * (len(models) + 1)

    def center(i: int) -> float:
        return pad + name_width + col * i + col / 2

    body: list[str] = []
    for i, (top, sub) in enumerate([*(header[m] for m in models), ("Random", "chance")]):
        weight = "600" if i < len(models) else "400"
        body.append(f'<text x="{center(i)}" y="38" text-anchor="middle" font-weight="{weight}">{_esc(top)}</text>')
        body.append(
            f'<text x="{center(i)}" y="56" text-anchor="middle" font-size="12" fill="{t.muted}">{_esc(sub)}</text>'
        )
    body.append(f'<text x="{pad}" y="56" font-size="12" fill="{t.muted}">Benchmark</text>')
    y = 70
    body.append(f'<line x1="{pad}" x2="{width - pad}" y1="{y}" y2="{y}" stroke="{t.rule}"/>')
    for section, lines in headline_rows(rows, models):
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
                    f'data-model="{models[i]}" data-rank="{k or 0}">{"n/a" if c is None else value_text(c)}</text>'
                )
            level = chance[cells[0][0]]
            body.append(
                f'<text x="{center(len(models))}" y="{base}" text-anchor="middle" fill="{t.muted}" '
                f'data-chance="{cells[0][0]}">{"n/a" if level is None else f"{level:.1f}"}</text>'
            )
    y += 8
    body.append(f'<line x1="{pad}" x2="{width - pad}" y1="{y}" y2="{y}" stroke="{t.rule}"/>')
    y += 24
    body.append(f'<text x="{pad}" y="{y}" font-size="12" fill="{t.muted}">{_esc(legend)}</text>')
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


def values_table(
    rows: Sequence[Result],
    chance: Mapping[str, float | None],
    models: Sequence[str] = HEADLINE,
    header: Mapping[str, tuple[str, str]] = HEADER,
) -> list[str]:
    """A table's values with their standard errors and the chance level, as an HTML table (Markdown tables have no
    group rows)."""
    head = "".join(f"<th>{header[m][0]}<br><sub>{header[m][1]}</sub></th>" for m in models)
    out = ["<table>", f'<tr><th align="left">Benchmark</th>{head}<th>Random<br><sub>chance</sub></th></tr>']
    for section, lines in headline_rows(rows, models):
        out.append(f'<tr><td colspan="{2 + len(models)}"><b>{section}</b></td></tr>')
        for name, cells in lines:
            tds = "".join(f'<td align="right">{"n/a" if c is None else shown(c)}</td>' for _, c, _ in cells)
            level = chance[cells[0][0]]
            tds += f'<td align="right">{"n/a" if level is None else f"{level:.1f}"}</td>'
            out.append(f"<tr><td>{name}</td>{tds}</tr>")
    out.append("</table>")
    return out


@dataclass(frozen=True)
class ApiCell:
    """One cell of the generative table: a score, a null (the model cannot run the benchmark), or "not run" (not
    run by decision, for budget, or not yet); the last two with their reason when one is known."""

    result: Result | None
    kind: str  # "score", "null" or "not run"
    reason: str | None
    starred: bool

    def text(self) -> str:
        """The cell in the image."""
        if self.result is not None:
            return value_text(self.result) + ("*" if self.starred else "")
        return self.kind

    def detail(self) -> str:
        """The cell in the values table: the value with its SE, or the kind with its reason."""
        if self.result is not None:
            return shown(self.result) + ("*" if self.starred else "")
        return f"{self.kind} <sub>{_esc(self.reason)}</sub>" if self.reason else self.kind


API_SECTIONS: Final = tuple(dict.fromkeys(b.section for b in API_BENCHMARKS))
API_LEGEND: Final = (
    f"Score in % (AA-Omniscience: index from {MINUS}100 to 100) · * requires verification",
    "null: the model cannot run it · not run: no score yet or by decision (reasons under Values)",
    "Best of the scored models highlighted, second underlined (rows with two or more scores) · LFM3 card: not ours",
)


def api_cells(rows: Sequence[Result], repo: Path = REPO) -> list[tuple[str, list[tuple[ApiBenchmark, list[ApiCell]]]]]:
    """Row groups of the generative table: per section, per benchmark one cell per column of API_COLUMNS."""
    by = {(r.benchmark, r.model): r for r in rows if r.protocol in ("api-benchmarks", "ifeval-api")}
    out = []
    for section in API_SECTIONS:
        lines = []
        for b in (x for x in API_BENCHMARKS if x.section == section):
            cells = []
            for column in API_COLUMNS:
                label = b.labels.get(column)
                result = by.get((b.id, label)) if label else None
                if result is not None:
                    cells.append(ApiCell(result, "score", None, b.starred))
                    continue
                row = _api_file(repo, b, column) if label is not None else None
                own = (row.get("reason") or row.get("score_null_reason")) if row is not None else None
                own = b.reason_text.get(column, own)
                if column in b.not_run:
                    cells.append(ApiCell(None, "not run", str(own or b.not_run[column]), b.starred))
                elif row is not None or column in b.null_reasons:
                    reason = own or b.null_reasons.get(column) or "see the benchmark's README"
                    cells.append(ApiCell(None, "null", str(reason), b.starred))
                else:
                    cells.append(ApiCell(None, "not run", None, b.starred))
            lines.append((b, cells))
        out.append((section, lines))
    return out


def api_ranks(cells: Sequence[ApiCell], ranked: bool = True) -> list[int | None]:
    """Rank of each scored cell, as in the headline table; no ranks in a row with fewer than two scores or in a row
    that is not ranked."""
    scored = [c.result for c in cells if c.result is not None]
    if not ranked or len(scored) < 2:
        return [None] * len(cells)
    values = sorted({float(value_text(r)) for r in scored}, reverse=True)
    return [None if c.result is None else values.index(float(value_text(c.result))) + 1 for c in cells]


def api_svg(rows: Sequence[Result], t: Theme, repo: Path = REPO, col: int = 110) -> str:
    """The generative table as an image, styled as the headline table, with the LFM3 card's value last."""
    name_width, pad, row_h = 220, 20, 34
    width = pad * 2 + name_width + col * (len(API_COLUMNS) + 1)

    def center(i: int) -> float:
        return pad + name_width + col * i + col / 2

    body: list[str] = []
    for i, (top, sub) in enumerate([*(API_HEADER[c] for c in API_COLUMNS), ("LFM3 card", "reported")]):
        weight = "600" if i < len(API_COLUMNS) else "400"
        body.append(f'<text x="{center(i)}" y="38" text-anchor="middle" font-weight="{weight}">{_esc(top)}</text>')
        body.append(
            f'<text x="{center(i)}" y="56" text-anchor="middle" font-size="12" fill="{t.muted}">{_esc(sub)}</text>'
        )
    body.append(f'<text x="{pad}" y="56" font-size="12" fill="{t.muted}">Benchmark</text>')
    y = 70
    body.append(f'<line x1="{pad}" x2="{width - pad}" y1="{y}" y2="{y}" stroke="{t.rule}"/>')
    for section, lines in api_cells(rows, repo):
        y += row_h
        body.append(
            f'<text x="{pad}" y="{y - 10}" font-size="13" font-weight="600" fill="{t.muted}">{_esc(section)}</text>'
        )
        for b, cells in lines:
            body.append(f'<line x1="{pad}" x2="{width - pad}" y1="{y}" y2="{y}" stroke="{t.row_rule}"/>')
            y += row_h
            base = y - 11
            body.append(f'<text x="{pad}" y="{base}">{_esc(b.name)}</text>')
            for i, (c, k) in enumerate(zip(cells, api_ranks(cells, b.ranked), strict=True)):
                if k == 1:
                    body.append(
                        f'<rect x="{center(i) - 38}" y="{base - 16}" width="76" height="22" rx="5" '
                        f'fill="{t.best_fill}"/>'
                    )
                elif k == 2:
                    body.append(
                        f'<line x1="{center(i) - 20}" x2="{center(i) + 20}" y1="{base + 3}" y2="{base + 3}" '
                        f'stroke="{t.text}"/>'
                    )
                style = (
                    f' font-weight="700" fill="{t.accent}"'
                    if k == 1
                    else f' fill="{t.muted}"'
                    if c.result is None
                    else ""
                )
                size = ' font-size="12"' if c.kind == "not run" else ""
                body.append(
                    f'<text x="{center(i)}" y="{base}" text-anchor="middle"{style}{size} data-benchmark="{b.id}" '
                    f'data-model="{b.labels.get(API_COLUMNS[i], "")}" data-rank="{k or 0}">{_esc(c.text())}</text>'
                )
            card = "n/a" if b.card is None else f"{b.card:.1f}"
            body.append(
                f'<text x="{center(len(API_COLUMNS))}" y="{base}" text-anchor="middle" fill="{t.muted}" '
                f'data-card="{b.id}">{card}</text>'
            )
    y += 8
    body.append(f'<line x1="{pad}" x2="{width - pad}" y1="{y}" y2="{y}" stroke="{t.rule}"/>')
    for text in API_LEGEND:
        y += 20
        body.append(f'<text x="{pad}" y="{y}" font-size="12" fill="{t.muted}">{_esc(text)}</text>')
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


def api_values_table(rows: Sequence[Result], repo: Path = REPO) -> list[str]:
    """The generative table's values with standard errors, nulls with their reason, and the card's value."""
    head = "".join(f"<th>{API_HEADER[c][0]}<br><sub>{API_HEADER[c][1]}</sub></th>" for c in API_COLUMNS)
    out = ["<table>", f'<tr><th align="left">Benchmark</th>{head}<th>LFM3 card<br><sub>reported</sub></th></tr>']
    for section, lines in api_cells(rows, repo):
        out.append(f'<tr><td colspan="{2 + len(API_COLUMNS)}"><b>{section}</b></td></tr>')
        for b, cells in lines:
            tds = ""
            for c in cells:
                tds += f'<td align="right">{c.detail()}</td>'
            tds += f'<td align="right">{"n/a" if b.card is None else f"{b.card:.2f}"}</td>'
            out.append(f"<tr><td>{b.name}</td>{tds}</tr>")
    out.append("</table>")
    return out


def api_benchmarks_page(rows: Sequence[Result], repo: Path = REPO) -> str:
    """Per benchmark: its source, how each model ran, and why its results need verification."""
    lines = [
        "# Generative and agentic benchmarks",
        "",
        "Generated by `python -m codesota.leaderboard`. [Back to the results](README.md).",
        "",
        "Each benchmark has its own protocol, harness and settings, written down in its directory under "
        f"[`{API_DIR}/`](../../{API_DIR}/). Values are copied from its `results/<model>.json`, not recomputed. "
        "Results marked * require verification: they come from a pull request that is still in review, or they "
        'are not the benchmark\'s main row, for the reason given below. "null": the model cannot run the benchmark; '
        '"not run": no score, by decision, for budget, or not yet.',
        "",
    ]
    for section, benchmark_lines in api_cells(rows, repo):
        lines += [f"## {section}", ""]
        for b, cells in benchmark_lines:
            source = f"[`{API_DIR}/{b.directory}/`](../../{API_DIR}/{b.directory}/README.md)"
            status = f"in review, PR #{b.pr}" if b.pr else "merged, exploratory" if b.caveat else "merged"
            lines += [f"### {b.name}", "", f"Source: {source} ({status}). LFM3-1.7B card: {b.card:.2f}.", ""]
            if b.caveat:
                lines += [f"**Requires verification:** {b.caveat}.", ""]
            if b.note:
                lines += [f"**Note:** {b.note}.", ""]
            lines += ["| model | how it ran | value | n |", "|---|---|---:|---:|"]
            for column, c in zip(API_COLUMNS, cells, strict=True):
                label = b.labels.get(column)
                if label is None:
                    lines.append(f"| {API_HEADER[column][0]} | not run | | |")
                elif c.result is not None:
                    lines.append(f"| {c.result.model_name} | {b.how[column]} | {c.detail()} | {c.result.n} |")
                else:
                    value = f"{c.kind}: {c.reason}" if c.reason else c.kind
                    lines.append(
                        f"| {MODELS[label].name if label in MODELS else label} | {b.how[column]} | {value} | |"
                    )
            lines.append("")
    return "\n".join(lines)


def bielik_setups() -> str:
    """Which benchmarks ran Bielik through the Fabryka API, our own vLLM, or local lm-eval, from `how`."""
    groups: dict[str, list[str]] = {"the Fabryka API": [], "our own vLLM": [], "local lm-eval, greedy": []}
    for b in API_BENCHMARKS:
        how = b.how.get("bielik")
        if how is None:
            continue
        key = (
            "the Fabryka API"
            if how.startswith("Fabryka API")
            else "our own vLLM"
            if how.startswith("own vLLM")
            else "local lm-eval, greedy"
        )
        groups[key].append(b.name)
    return "; ".join(f"{k} ({', '.join(v)})" for k, v in groups.items() if v)


K70_PROTOCOL: Final = f"../../{FULL_RUN}/slayer-1.09-k70000/PROTOKOL.md"
K70_NOTE: Final = (
    "Step 70 000 was measured in its own run, on 8 x RTX 4090 with the same code and settings "
    f"([protocol]({K70_PROTOCOL})); every other result of the full run on an RTX 5090."
)


def readme(rows: Sequence[Result], chance: Mapping[str, float | None]) -> str:
    n_api = len(API_BENCHMARKS)
    lines = [
        "# Results",
        "",
        "Slayer 1B next to its reference models. Two tables: the log-likelihood benchmarks, measured for every model "
        "with the same code and settings, and the generative and agentic benchmarks, where each model answers in "
        "its own format and each benchmark has its own protocol.",
        "",
        "## Log-likelihood benchmarks",
        "",
        "<picture>",
        '  <source media="(prefers-color-scheme: dark)" srcset="charts/headline-table-dark.svg">',
        '  <img src="charts/headline-table.svg" alt="Results table: Slayer 1B 1.09, Bielik 11B, LFM3-1.7B-Base, '
        'Bielik 1.5B v3 and Qwen3.5-0.8B-Base on 14 benchmarks; the same values are in the Values table below" '
        'width="100%">',
        "</picture>",
        "",
        "## Generative and agentic benchmarks",
        "",
        "<picture>",
        '  <source media="(prefers-color-scheme: dark)" srcset="charts/api-benchmarks-table-dark.svg">',
        '  <img src="charts/api-benchmarks-table.svg" alt="Results table: Slayer 1B, Bielik 11B v3.1 and LFM3-1.7B '
        f"on {n_api} generative and agentic benchmarks, with the values of the LFM3-1.7B card; the same values are in "
        'the Generative values table below" width="100%">',
        "</picture>",
        "",
        "**\\* requires verification:** the result comes from a pull request that is still in review, or it is not "
        "the benchmark's main row; the reason for each benchmark is on [Generative and agentic benchmarks]"
        f"(api-benchmarks.md). Merged and reviewed: {', '.join(b.name for b in API_BENCHMARKS if not b.starred)}.",
        "",
        '- **Incomplete by design:** "null" means the model cannot run the benchmark (for example, its context '
        'window is too short, or it has no tool-call format; research/METHODOLOGY.md). "not run" means the '
        "benchmark was not run for the model: by decision, for compute budget, or not yet. The Generative values "
        "table gives the reason of each. Neither is a zero.",
        "- **Slayer 1B is a base model** without a chat template or a tool-call format: on the agentic benchmarks it "
        "cannot run, and where it is scored its output is mostly degenerate. Its column mixes versions: IFEval is "
        "1.08, the instruction-following, knowledge, tool and agent rows step 60 000 of 1.09, the others step "
        "70 000.",
        f"- **Bielik 11B v3.1 ran in three setups**, depending on the benchmark: {bielik_setups()}. The setups "
        "are not interchangeable: on IFEval our vLLM with the template defaults scores 5.36 ± 1.86 points above the "
        "API. Where a benchmark samples, Bielik uses the LFM3 card's settings (temperature 0.6, top_p 0.95). "
        "**LFM3-1.7B** is the instruction-tuned model, with reasoning on; **LFM3 card** is the value Liquid AI "
        "reports for it, not measured by us.",
        *(f"- **{b.name}:** {b.note}." for b in API_BENCHMARKS if b.note),
        "",
        "[Slayer versions](slayer-versions.md) · [All models](all-models.md) · "
        "[Instruction following](instruction-following.md) · [Generative and agentic benchmarks](api-benchmarks.md) · "
        "[All results as JSONL](results.jsonl) · "
        "[Benchmark status](../BENCHMARKS.md)",
        "",
        "## Notes on the log-likelihood benchmarks",
        "",
        f"- **Slayer 1B 1.09 is a training checkpoint** (step 70 000), not a release. {K70_NOTE} Earlier versions "
        "and step 40 000: [Slayer versions](slayer-versions.md).",
        "- **Random** is the chance level: the score of picking an answer at random (the mean of 1 / number of "
        f"options). On PubMedQA, always giving its most common answer scores {majority_level('pubmedqa'):.1f}.",
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
        *values_table(rows, chance),
        "",
        "## Generative values",
        "",
        "Value ± standard error, in % (AA-Omniscience: index). Each benchmark's standard error is the one its "
        "directory reports (over tasks, questions, or problems; see its README).",
        "",
        *api_values_table(rows),
        "",
        "## Sources",
        "",
        f"- Log-likelihood benchmarks: [`{FULL_RUN}/`](../../{FULL_RUN}/README.md), manifest "
        f"[`manifest.jsonl`](../../{FULL_RUN}/manifest.jsonl) (commands, revisions, weight checksums).",
        f"- IFEval: [`{IFEVAL_API}/`](../../{IFEVAL_API}/), per-prompt outputs in `*.jsonl.gz`.",
        f"- Generative and agentic benchmarks: [`{API_DIR}/<benchmark>/results/`](../../{API_DIR}/), one directory "
        "per benchmark with its README, `run.sh`, and per-task outputs.",
        "- Every row of [`results.jsonl`](results.jsonl) names its source file.",
        "",
    ]
    return "\n".join(lines)


def slayer_versions(rows: Sequence[Result], chance: Mapping[str, float | None]) -> str:
    """Every Slayer 1B of the full run, oldest first, as the headline: table image, notes, values with SE."""
    return "\n".join(
        [
            "# Slayer 1B versions",
            "",
            "Every Slayer 1B release and the 1.09 training checkpoints, on the same benchmarks with the same settings. "
            "[Back to the results](README.md).",
            "",
            "<picture>",
            '  <source media="(prefers-color-scheme: dark)" srcset="charts/slayer-versions-dark.svg">',
            '  <img src="charts/slayer-versions.svg" alt="Results table: Slayer 1B 1.00 to 1.09 step 70 000 on 14 '
            'benchmarks; the same values are in the Values table below" width="100%">',
            "</picture>",
            "",
            "## Notes",
            "",
            "- **1.09 is still training:** steps 40 000 and 70 000 are checkpoints, not releases. 1.09 starts from the "
            "weights of 1.08.",
            f"- {K70_NOTE}",
            "- **1.07** is scored from its weights on the Hugging Face Hub (`SlayerLab/Slayer1B-1.07`).",
            "- **A version is not better on a test because its value is higher:** differences of one or two points "
            "are often within the standard errors below. The paired comparisons of 1.09 step 40 000 with 1.08 are in "
            f"[its report](../../{FULL_RUN}/slayer-1.09-k40000/RAPORT.md).",
            "- Generated by `python -m codesota.leaderboard` from the result files; do not edit by hand.",
            "",
            "## Values",
            "",
            f"Value ± standard error, accuracy in %. {SE_NOTE}",
            "",
            *values_table(rows, chance, SLAYER_VERSIONS, SLAYER_HEADER),
            "",
        ]
    )


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
    chance = chance_levels(repo)
    package_readme = (BENCHMARKS / "README.md").read_text(encoding="utf-8")
    return {
        "../README.md": with_snapshot(package_readme, rows),
        "README.md": readme(rows, chance),
        "slayer-versions.md": slayer_versions(rows, chance),
        "all-models.md": all_models(rows),
        "instruction-following.md": instruction_following(rows),
        "api-benchmarks.md": api_benchmarks_page(rows),
        "charts/api-benchmarks-table.svg": api_svg(rows, LIGHT),
        "charts/api-benchmarks-table-dark.svg": api_svg(rows, DARK),
        "results.jsonl": jsonl(rows),
        "charts/headline-table.svg": headline_svg(rows, LIGHT, chance),
        "charts/headline-table-dark.svg": headline_svg(rows, DARK, chance),
        "charts/slayer-versions.svg": headline_svg(
            rows, LIGHT, chance, SLAYER_VERSIONS, SLAYER_HEADER, SLAYER_LEGEND, 72
        ),
        "charts/slayer-versions-dark.svg": headline_svg(
            rows, DARK, chance, SLAYER_VERSIONS, SLAYER_HEADER, SLAYER_LEGEND, 72
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m codesota.leaderboard", description=__doc__.split("\n")[0])
    p.add_argument("--check", action="store_true", help="fail when the text files differ from the sources")
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
