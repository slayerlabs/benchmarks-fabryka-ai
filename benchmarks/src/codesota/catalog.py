"""The benchmark registry: every benchmark the repository knows, and where each stands in CodeSOTA.

A benchmark is in one of three states:

- `verified`: the runner implements it, a published reference result was reproduced with the protocol the runner
  uses, and the runner reproduces the research pipeline's per-question results for that protocol.
- `needs-reference-check`: the runner implements it and reproduces the research pipeline, but no published reference
  result has been reproduced for this protocol yet. Its scores are measurements, not yet validated against a
  reference.
- `not-implemented`: the benchmark has a directory in `research/benchmarks/`, but the runner cannot run it yet.

The state of each implemented benchmark is justified in its `evidence`, with the report it rests on. The IDs are the
benchmark directory names in `research/benchmarks/`; the research pipeline's task IDs (`T01`-`T53`) are kept as
`legacy_id` and accepted as aliases. Which benchmarks a run selects is resolved by `select`.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Final, Literal

Status = Literal["verified", "needs-reference-check", "not-implemented"]
STATUSES: Final[tuple[Status, ...]] = ("verified", "needs-reference-check", "not-implemented")

# How a benchmark is scored: one log-likelihood per answer option (`multiple_choice`), one per document with a
# greedy-match flag (`loglikelihood`), or rolling windows over whole documents for perplexity (`rolling`).
Kind = Literal["multiple_choice", "loglikelihood", "rolling"]

# How the dataset is read. `hub`: `datasets.load_dataset(repo, config, revision=...)`. `parquet`: the parquet files of
# `parquet_path` at `parquet_revision` (a pinned commit of the repository's `refs/convert/parquet` branch). `tsv`: one
# tab-separated file of the repository at `revision`. `unpinned-parquet`: the `refs/convert/parquet` branch itself,
# which has no pinned commit (recorded as a limitation).
Source = Literal["hub", "parquet", "tsv", "unpinned-parquet"]


@dataclass(frozen=True)
class Dataset:
    repo: str
    revision: str
    split: str
    n_population: int
    source: Source = "hub"
    config: str | None = None
    parquet_revision: str | None = None
    parquet_path: str | None = None
    file: str | None = None
    id_field: str | None = None
    """Document field used as the sample ID; without one, the document's index in the split."""
    research_id_field: str | None = None
    """The field the research pipeline used for `source_id_digest`, when it is not a unique ID (it is then recorded
    as `research_source_id_digest`, so the selection can still be compared with research results)."""


@dataclass(frozen=True)
class Scoring:
    kind: Kind
    decision_metric: str
    """The metric the benchmark's card names as its result."""
    unit: Literal["score", "percent", "byte_ppl"] = "score"
    higher_is_better: bool = True
    fixed_classes: bool = True
    """Answer options are a fixed set of positions, so a constant answer is a meaningful baseline."""
    clusters: Literal["winogrande-pairs", "wsc273-schemas"] | None = None
    """Questions that are not independent (twin sentences, schemas): uncertainty is computed over clusters."""
    baseline: Literal["choices", "cloze", "none"] = "choices"


@dataclass(frozen=True)
class Benchmark:
    id: str
    name: str
    language: Literal["EN", "PL"]
    legacy_id: str | None = None
    status: Status = "not-implemented"
    aliases: tuple[str, ...] = ()
    packs: tuple[str, ...] = ()
    dataset: Dataset | None = None
    scoring: Scoring | None = None
    evidence: str = ""
    """Why the benchmark has its status, with the report the status rests on."""
    limitations: tuple[str, ...] = field(default=())

    @property
    def definition(self) -> str:
        return f"research/benchmarks/{self.id}/"

    @property
    def cost(self) -> "Cost | None":
        return COST.get(self.id)


@dataclass(frozen=True)
class Cost:
    """What one run of a benchmark costs, measured on the reference setup (REFERENCE_SETUP).

    `requests` (log-likelihood requests to the model) does not depend on the hardware or the model, but it is not a
    measure of work on its own: a WikiText-2 request is a whole document. `seconds` is the measured wall-clock time;
    another model or GPU scales it but keeps the order, so the size is the benchmark's relative amount of work, for
    building packs, not a time estimate.
    """

    requests: int
    seconds: int

    @property
    def size(self) -> "Size":
        return "small" if self.seconds < SMALL_BELOW else "medium" if self.seconds < BIG_FROM else "big"


Size = Literal["small", "medium", "big"]
SIZES: Final[tuple[Size, ...]] = ("small", "medium", "big")
SMALL_BELOW, BIG_FROM = 100, 600  # seconds on the reference setup
REFERENCE_SETUP: Final = (
    "EleutherAI/pythia-1b-v0 (1B parameters), float32, batch 1, one BOS, NVIDIA GeForce RTX 5060 Ti, "
    "codesota.runner verification run of November 2026 (docs/running.md)"
)
# (requests, seconds) of the one-BOS verification run on the reference setup.
COST: Final[dict[str, Cost]] = {
    benchmark: Cost(requests, seconds)
    for benchmark, requests, seconds in (
        ("arc-challenge", 4687, 110),
        ("arc-easy", 9501, 189),
        ("hellaswag", 40168, 1060),
        ("lambada", 5153, 156),
        ("mathqa", 14925, 201),
        ("medmcqa", 16732, 115),
        ("multiblimp-pl", 6544, 123),
        ("piqa", 3676, 88),
        ("pubmedqa", 1500, 46),
        ("social-iqa", 5862, 125),
        ("wikitext-2", 62, 76),
        ("winogrande", 2534, 60),
        ("wsc273", 546, 21),
    )
}


FULL_RUN = "full-run-2026-11"
ARC_REPO, ARC_REVISION = "allenai/ai2_arc", "210d026faf9955653af8916fad021475a3f00453"

IMPLEMENTED: Final[tuple[Benchmark, ...]] = (
    Benchmark(
        id="arc-easy",
        name="ARC-Easy",
        language="EN",
        legacy_id="T51",
        status="verified",
        aliases=("arce", "arc-e"),
        packs=(FULL_RUN,),
        dataset=Dataset(
            repo=ARC_REPO, revision=ARC_REVISION, config="ARC-Easy", split="test", n_population=2376, id_field="id"
        ),
        scoring=Scoring(kind="multiple_choice", decision_metric="acc"),
        evidence=(
            "Pythia-1B v0 reproduces its published acc 0.5585 (window 0.5381-0.5789) without BOS "
            "(research/benchmarks/arc-easy/REPRODUCTION.md); with one BOS it scores 0.5690, inside the same window "
            "(research/results/full-run-2026-11/bos-window-check/RAPORT.md)."
        ),
    ),
    Benchmark(
        id="piqa",
        name="PIQA",
        language="EN",
        legacy_id="T06",
        status="verified",
        packs=(FULL_RUN,),
        dataset=Dataset(
            repo="ybisk/piqa",
            revision="2e8ac2dffd59bac8c3c6714948f4c551a0848bb0",
            config="plain_text",
            split="validation",
            n_population=1838,
            source="parquet",
            parquet_revision="142c51238b3ca2bc61e9a075913871b8b600e8e1",
        ),
        scoring=Scoring(kind="multiple_choice", decision_metric="acc_norm"),
        evidence=(
            "Pythia-1B v0 reproduces its published acc_norm (window 0.6838-0.7264) without BOS "
            "(research/benchmarks/piqa/REPRODUCTION.md); with one BOS it scores 0.7095, inside the same window "
            "(bos-window-check)."
        ),
    ),
    Benchmark(
        id="winogrande",
        name="WinoGrande",
        language="EN",
        legacy_id="T07",
        status="verified",
        aliases=("wg",),
        packs=(FULL_RUN,),
        dataset=Dataset(
            repo="allenai/winogrande",
            revision="01e74176c63542e6b0bcb004dcdea22d94fb67b5",
            config="winogrande_xl",
            split="validation",
            n_population=1267,
        ),
        scoring=Scoring(kind="multiple_choice", decision_metric="acc", clusters="winogrande-pairs"),
        evidence=(
            "Pythia-1B v0 reproduces its published acc 0.5375 (window 0.5095-0.5655) without BOS "
            "(research/benchmarks/winogrande/REPRODUCTION.md); with one BOS it scores 0.5438, inside the same window "
            "(bos-window-check)."
        ),
    ),
    Benchmark(
        id="lambada",
        name="LAMBADA (OpenAI)",
        language="EN",
        legacy_id="T17",
        status="verified",
        aliases=("lambada-openai",),
        packs=(FULL_RUN,),
        dataset=Dataset(
            repo="EleutherAI/lambada_openai",
            revision="900124bf3b8235c6daf21033af9948b3f07346c4",
            config="default",
            split="test",
            n_population=5153,
        ),
        scoring=Scoring(kind="loglikelihood", decision_metric="acc", fixed_classes=False, baseline="cloze"),
        evidence=(
            "Pythia-1B v0 reproduces its published acc 0.5622 (window 0.5422-0.5822) without BOS "
            "(research/benchmarks/lambada/REPRODUCTION.md); with one BOS it scores 0.5605, inside the same window "
            "(bos-window-check)."
        ),
    ),
    Benchmark(
        id="hellaswag",
        name="HellaSwag",
        language="EN",
        legacy_id="T05",
        status="needs-reference-check",
        aliases=("hs",),
        packs=(FULL_RUN,),
        dataset=Dataset(
            repo="Rowan/hellaswag",
            revision="218ec52e09a7e7462a5400043bb9a69a41d06b76",
            split="validation",
            n_population=10042,
            research_id_field="ind",
        ),
        scoring=Scoring(kind="multiple_choice", decision_metric="acc_norm"),
        evidence=(
            "The reference check (EuroLLM-1.7B, met) was computed 10-shot with separate code; this protocol is "
            "0-shot, so no reference result has been reproduced for it (research/STATUS.md)."
        ),
        limitations=(
            "Sample IDs are positions in the split: the dataset's `ind` field, which the research pipeline used, is "
            "not unique in the validation split.",
        ),
    ),
    Benchmark(
        id="arc-challenge",
        name="ARC-Challenge",
        language="EN",
        legacy_id="T02",
        status="needs-reference-check",
        aliases=("arcc", "arc-c"),
        packs=(FULL_RUN,),
        dataset=Dataset(
            repo=ARC_REPO,
            revision=ARC_REVISION,
            config="ARC-Challenge",
            split="test",
            n_population=1172,
            id_field="id",
        ),
        scoring=Scoring(kind="multiple_choice", decision_metric="acc_norm"),
        evidence="Stage B has no reference check (research/STATUS.md, 'bez kontroli').",
    ),
    Benchmark(
        id="wsc273",
        name="WSC273",
        language="EN",
        legacy_id="T14",
        status="needs-reference-check",
        aliases=("wsc",),
        packs=(FULL_RUN,),
        dataset=Dataset(
            repo="ErnestSDavis/winograd_wsc",
            revision="8052c534a4cecd8328c0bc879f6a5aa07404c4da",
            config="wsc273",
            split="test",
            n_population=273,
            source="parquet",
            parquet_revision="24cdebf4993560f25ff220b171e40f1027f3d9e6",
        ),
        scoring=Scoring(kind="multiple_choice", decision_metric="acc", clusters="wsc273-schemas"),
        evidence=(
            "Stage B has no reference check, and its control model is outside the methodology's list "
            "(research/STATUS.md, marked for review)."
        ),
    ),
    Benchmark(
        id="mathqa",
        name="MathQA",
        language="EN",
        legacy_id="T19",
        status="needs-reference-check",
        packs=(FULL_RUN,),
        dataset=Dataset(
            repo="allenai/math_qa",
            revision="c4f1cc784c04c4957b50c97858f23893b633eea6",
            config="default",
            split="test",
            n_population=2985,
            source="parquet",
            parquet_revision="fafb9f7ee5b9ec4da9499f9c4177a4c91389f2d6",
        ),
        scoring=Scoring(kind="multiple_choice", decision_metric="acc_norm"),
        evidence="Stage B has no reference check (research/STATUS.md, 'bez kontroli').",
    ),
    Benchmark(
        id="pubmedqa",
        name="PubMedQA",
        language="EN",
        legacy_id="T44",
        status="needs-reference-check",
        packs=(FULL_RUN,),
        dataset=Dataset(
            repo="bigbio/pubmed_qa",
            revision="15578e80ef02c2c9636d33fdd7eb6b05b987ba60",
            config="pubmed_qa_labeled_fold0_source",
            split="test",
            n_population=500,
            source="parquet",
            parquet_revision="13a7d15476092370cbabb6475390e7e69b74d2f2",
        ),
        scoring=Scoring(kind="multiple_choice", decision_metric="acc"),
        evidence="Stage B has no reference check (research/STATUS.md, 'bez kontroli').",
    ),
    Benchmark(
        id="medmcqa",
        name="MedMCQA",
        language="EN",
        legacy_id="T45",
        status="needs-reference-check",
        packs=(FULL_RUN,),
        dataset=Dataset(
            repo="openlifescienceai/medmcqa",
            revision="91c6572c454088bf71b679ad90aa8dffcd0d5868",
            split="validation",
            n_population=4183,
            id_field="id",
        ),
        scoring=Scoring(kind="multiple_choice", decision_metric="acc"),
        evidence="Stage B has no reference check, and the benchmark is marked for review (research/STATUS.md).",
    ),
    Benchmark(
        id="social-iqa",
        name="Social IQa",
        language="EN",
        legacy_id="T46",
        status="needs-reference-check",
        aliases=("siqa",),
        packs=(FULL_RUN,),
        dataset=Dataset(
            repo="allenai/social_i_qa",
            revision="8835ceb9141d7896d9d968634a9b21ae440e3ec5",
            split="validation",
            n_population=1954,
            source="unpinned-parquet",
        ),
        scoring=Scoring(kind="multiple_choice", decision_metric="acc"),
        evidence="Stage B has no reference check (research/STATUS.md, 'bez kontroli').",
        limitations=(
            "The data are read from the repository's refs/convert/parquet branch, which has no pinned commit; the "
            "recorded revision is that of the main branch, so a later conversion could change the documents.",
        ),
    ),
    Benchmark(
        id="wikitext-2",
        name="WikiText-2",
        language="EN",
        legacy_id="T03",
        status="needs-reference-check",
        aliases=("wikitext", "wt2"),
        packs=(FULL_RUN,),
        dataset=Dataset(
            repo="EleutherAI/wikitext_document_level",
            revision="647234772b9554e208af6c826f23b99e3cac88c8",
            config="wikitext-2-raw-v1",
            split="test",
            n_population=62,
        ),
        scoring=Scoring(
            kind="rolling",
            decision_metric="byte_perplexity",
            unit="byte_ppl",
            higher_is_better=False,
            fixed_classes=False,
            baseline="none",
        ),
        evidence="Stage B has no reference check (research/STATUS.md, 'bez kontroli').",
    ),
    Benchmark(
        id="multiblimp-pl",
        name="MultiBLiMP (Polish)",
        language="PL",
        legacy_id="T04",
        status="needs-reference-check",
        aliases=("mblimp-pl",),
        packs=(FULL_RUN,),
        dataset=Dataset(
            repo="jumelet/multiblimp",
            revision="de923efa8d2483d6b13364ee68e65308e990a991",
            split="pol/data.tsv",
            n_population=3272,
            source="tsv",
            file="pol/data.tsv",
        ),
        scoring=Scoring(kind="multiple_choice", decision_metric="acc", unit="percent", fixed_classes=False),
        evidence=(
            "Stage B has no reference check, and a possible leak of the test set into training data is open "
            "(research/STATUS.md, #36)."
        ),
    ),
)

# Benchmarks with a directory in research/benchmarks/ that the runner does not run yet: (id, name, language, legacy).
_NOT_IMPLEMENTED: Final[tuple[tuple[str, str, Literal["EN", "PL"], str | None, tuple[str, ...]], ...]] = (
    ("8tags", "8TAGS", "PL", "T23", ()),
    ("anli-r3", "ANLI (round 3)", "EN", "T16", ()),
    ("bbh", "BIG-Bench Hard", "EN", "T47", ()),
    ("belebele-pl", "Belebele (Polish)", "PL", "T24", ()),
    ("blimp", "BLiMP", "EN", "T01", (FULL_RUN,)),
    ("blimp-supplement", "BLiMP Supplement", "EN", "T52", ()),
    ("boolq", "BoolQ", "EN", "T10", ()),
    ("cb", "CommitmentBank", "EN", "T12", ()),
    ("cbd", "CBD", "PL", "T28", ()),
    ("cola", "CoLA", "EN", "T49", ()),
    ("copa", "COPA", "EN", "T11", ()),
    ("coqa", "CoQA", "EN", "T41", ()),
    ("drop", "DROP", "EN", "T39", ()),
    ("dyk", "DYK", "PL", "T25", ()),
    ("ewok", "EWoK", "EN", "T53", (FULL_RUN,)),
    ("ewok-pl", "EWoK (Polish)", "PL", None, ()),
    ("gsm8k", "GSM8K", "EN", "T33", ()),
    ("ifeval", "IFEval", "EN", "T36", ()),
    ("klej-ner", "NKJP-NER (KLEJ)", "PL", "T29", ()),
    ("llmzszl", "LLMzSzL", "PL", "T37", ()),
    ("logiqa", "LogiQA", "EN", "T18", ()),
    ("math", "MATH", "EN", "T34", ()),
    ("mmlu", "MMLU", "EN", "T32", ()),
    ("nq-open", "Natural Questions (open)", "EN", "T42", ()),
    ("openbookqa", "OpenBookQA", "EN", "T08", ()),
    ("paws-en", "PAWS (English)", "EN", "T48", ()),
    ("polemo2", "PolEmo 2.0 (in-domain)", "PL", "T22", ()),
    ("polqa", "PolQA", "PL", "T30", ()),
    ("poquad", "PoQuAD", "PL", "T31", ()),
    ("ppc", "PPC", "PL", "T26", ()),
    ("prost", "PROST", "EN", "T20", ()),
    ("psc", "PSC", "PL", "T27", ()),
    ("race", "RACE", "EN", "T40", ()),
    ("record", "ReCoRD", "EN", "T50", ()),
    ("rte", "RTE", "EN", "T15", ()),
    ("sciq", "SciQ", "EN", "T09", ()),
    ("squad2", "SQuAD 2.0", "EN", "T38", ()),
    ("sst2", "SST-2", "EN", "T21", ()),
    ("triviaqa", "TriviaQA", "EN", "T43", ()),
    ("truthfulqa", "TruthfulQA (MC2)", "EN", "T35", ()),
    ("uncheatable-eval", "UncheatableEval", "EN", None, ()),
    ("wic", "WiC", "EN", "T13", ()),
)

CATALOG: Final[dict[str, Benchmark]] = {
    b.id: b
    for b in sorted(
        (
            *IMPLEMENTED,
            *(Benchmark(id=i, name=n, language=lang, legacy_id=t, packs=p) for i, n, lang, t, p in _NOT_IMPLEMENTED),
        ),
        key=lambda b: b.id,
    )
}


def packs() -> dict[str, tuple[str, ...]]:
    """Named groups of benchmarks, selected as `@name`: declared packs, one per language, one per status, and one
    per size (`@small`, `@medium`, `@big`: the implemented benchmarks by their amount of work)."""
    out: dict[str, list[str]] = {"all": list(CATALOG)}
    for b in CATALOG.values():
        for p in b.packs:
            out.setdefault(p, []).append(b.id)
        out.setdefault(b.language.lower(), []).append(b.id)
        out.setdefault(b.status, []).append(b.id)
        if b.status != "not-implemented":
            out.setdefault("implemented", []).append(b.id)
        if b.cost is not None:
            out.setdefault(b.cost.size, []).append(b.id)
    return {k: tuple(v) for k, v in sorted(out.items())}


def _key(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def aliases() -> dict[str, str]:
    """Every accepted spelling of a benchmark name, mapped to its ID: the ID, its legacy task ID, and its aliases.
    Underscores and hyphens are interchangeable, and case does not matter."""
    out: dict[str, str] = {}
    for b in CATALOG.values():
        for name in (b.id, *(b.aliases), *((b.legacy_id,) if b.legacy_id else ())):
            key = _key(name)
            if out.get(key, b.id) != b.id:
                raise ValueError(f"alias {name!r} names both {out[key]} and {b.id}")
            out[key] = b.id
    return out


class SelectionError(ValueError):
    """A selection names something that is not in the catalog."""


def select(selection: str | Iterable[str]) -> list[Benchmark]:
    """Benchmarks named by a selection, in the order given, each once.

    A selection is a comma-separated string or a list of items. An item is a benchmark ID, an alias, a legacy task ID
    (`T51`), `@<pack>` (see `packs`), or `all`. Every unknown item is reported before anything runs.
    """
    items = [s for part in ([selection] if isinstance(selection, str) else selection) for s in part.split(",")]
    items = [s.strip() for s in items if s.strip()]
    if not items:
        raise SelectionError("no benchmark selected")
    names, groups = aliases(), packs()
    chosen: list[str] = []
    unknown: list[str] = []
    for item in items:
        if item.lower() == "all" or item.startswith("@"):
            pack = "all" if item.lower() == "all" else item[1:].lower()
            if pack not in groups:
                unknown.append(item)
                continue
            chosen += groups[pack]
        elif _key(item) in names:
            chosen.append(names[_key(item)])
        else:
            unknown.append(item)
    if unknown:
        raise SelectionError(
            "unknown benchmark or pack: "
            + ", ".join(unknown)
            + ". Benchmarks: python -m codesota.runner --list; packs: "
            + ", ".join("@" + p for p in groups)
        )
    return [CATALOG[i] for i in dict.fromkeys(chosen)]


def markdown() -> str:
    """The catalog as BENCHMARKS.md (tests/test_catalog.py keeps the file equal to this)."""
    counts = {s: sum(b.status == s for b in CATALOG.values()) for s in STATUSES}
    lines = [
        "# Benchmarks",
        "",
        "Every benchmark the repository has a directory for, and where it stands in CodeSOTA. Generated from",
        "[`src/codesota/catalog.py`](src/codesota/catalog.py); regenerate with",
        "`uv run python -c \"from codesota.catalog import markdown; print(markdown(), end='')\" > BENCHMARKS.md`.",
        "",
        "| status | meaning |",
        "|---|---|",
        "| `verified` | the runner implements it; a published reference result was reproduced with this protocol, "
        "and the runner reproduces the research pipeline for it |",
        "| `needs-reference-check` | the runner implements it and reproduces the research pipeline, but no "
        "published reference result has been reproduced for this protocol; its scores are measurements, not yet "
        "validated |",
        "| `not-implemented` | the benchmark has a directory in `research/benchmarks/`; the runner cannot run it yet |",
        "",
        f"{counts['verified']} verified, {counts['needs-reference-check']} need a reference check, "
        f"{counts['not-implemented']} not implemented. Run them with `python -m codesota.runner` "
        "([`docs/running.md`](docs/running.md)).",
        "",
        "## Implemented",
        "",
        "| benchmark | ID | legacy ID | aliases | packs | decision metric | size | status | evidence |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for status in STATUSES[:2]:
        for b in sorted((b for b in CATALOG.values() if b.status == status), key=lambda b: b.id):
            assert b.scoring is not None and b.cost is not None
            evidence = " ".join((b.evidence, *b.limitations))
            cost = f"`{b.cost.size}`: {b.cost.requests} requests, {b.cost.seconds} s"
            lines.append(
                f"| {b.name} | `{b.id}` | {b.legacy_id or ''} | {', '.join(f'`{a}`' for a in b.aliases)} | "
                f"{', '.join(f'`@{p}`' for p in b.packs)} | `{b.scoring.decision_metric}` | {cost} | `{b.status}` | "
                f"{evidence} |"
            )
    lines += [
        "",
        f"**Size** is the benchmark's amount of work, measured on the reference setup: {REFERENCE_SETUP}. "
        f"`small` takes under {SMALL_BELOW} s there, `medium` under {BIG_FROM} s, `big` {BIG_FROM} s or more. A "
        "larger model or another GPU changes the seconds, not the order; every run records its own time and request "
        "count (`execution.timing`).",
    ]
    lines += ["", "## Not implemented", "", "| benchmark | ID | legacy ID | language |", "|---|---|---|---|"]
    for b in sorted((b for b in CATALOG.values() if b.status == "not-implemented"), key=lambda b: b.id):
        lines.append(f"| {b.name} | `{b.id}` | {b.legacy_id or ''} | {b.language} |")
    lines += [
        "",
        "## Packs",
        "",
        "Select a pack with `@name`, for example `--benchmarks @verified,arc-challenge` or `--benchmarks @small`.",
        "",
        "| pack | benchmarks |",
        "|---|---|",
    ]
    for name, ids in packs().items():
        lines.append(f"| `@{name}` | {len(ids)} |")
    return "\n".join(lines) + "\n"
