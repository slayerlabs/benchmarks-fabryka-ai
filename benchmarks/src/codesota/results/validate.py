"""Validation of a CodeSOTA run directory: manifest, per-sample records, aggregates, and checksums.

A run directory holds `manifest.json` and the artifacts it lists, among them exactly one per-sample JSONL file
(role `samples`). Nothing here runs a model, calls a network, or rescores outputs.

What a passing report establishes, and what it does not:

- Structural validity: fields and types, consistent sample records, recomputed `mean`/`micro_mean` aggregates, and
  unmodified artifacts. Checked.
- Provenance completeness: the identities and settings listed in `schema.PROVENANCE_REQUIRED` are recorded, not
  left unknown. Checked for presence only; the validator cannot tell whether a recorded revision is the true one.
- Scientific verification: that the benchmark is implemented and scored correctly (official scorer and protocol,
  dataset integrity, benchmark-specific evidence). Not checked here; it is established by review.

Unknown metadata is written as `{"unknown": "<why it is unknown>"}`, never guessed. `null` means "does not apply"
(for example `top_p` under greedy decoding) and is accepted only where a field allows it.
"""

import datetime
import hashlib
import json
import math
import re
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

from codesota.results import schema

SHA256 = re.compile(r"[0-9a-f]{64}")
GIT_COMMIT = re.compile(r"[0-9a-f]{40}")
RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,199}")
# ISO 8601 date-time in UTC, as written by datetime.isoformat() or with a trailing Z.
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+00:00)")
# Recomputed aggregates must match the recorded value to this absolute tolerance (in the metric's unit).
TOLERANCE = 1e-9

Json = Any
Check = Callable[[Json], bool]


@dataclass(frozen=True)
class Issue:
    """One finding: a stable code for tests and tools, the JSON path, and a sentence."""

    code: str
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} at {self.path}: {self.message}"


@dataclass
class Report:
    """Result of validating one run. `issues` make the run invalid; `warnings` do not, but are reported."""

    run_dir: Path
    run_id: str | None = None
    issues: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    manifest_sha256: str | None = None
    samples_sha256: str | None = None
    # Every field of schema.PROVENANCE_REQUIRED is recorded and not unknown (independent of the manifest's claim).
    provenance_complete: bool = False
    # Metrics whose recorded value was not recomputed from the samples (aggregation `external`).
    not_recomputed: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def add(self, code: str, path: str, message: str) -> None:
        self.issues.append(Issue(code, path, message))

    def warn(self, code: str, path: str, message: str) -> None:
        self.warnings.append(Issue(code, path, message))

    def codes(self) -> set[str]:
        return {i.code for i in self.issues}

    def warning_codes(self) -> set[str]:
        return {i.code for i in self.warnings}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def source_id_digest(sample_ids: Iterable[object]) -> str:
    """Digest of the selected sample IDs in record order, as research/common/ewaluuj.py computes `source_id_digest`
    (SHA-256 of the IDs joined with newlines)."""
    return hashlib.sha256("\n".join(str(i) for i in sample_ids).encode("utf-8")).hexdigest()


def is_unknown(value: Json) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"unknown"}
        and isinstance(value["unknown"], str)
        and bool(value["unknown"].strip())
    )


# Value checks. Each takes a JSON value and says whether it is acceptable.
def text(v: Json) -> bool:
    return isinstance(v, str) and bool(v.strip())


def integer(v: Json) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def count(v: Json) -> bool:
    return integer(v) and v >= 0


def positive(v: Json) -> bool:
    return integer(v) and v > 0


def number(v: Json) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool) and math.isfinite(v)


def boolean(v: Json) -> bool:
    return isinstance(v, bool)


def one_of(values: frozenset[str]) -> Check:
    return lambda v: isinstance(v, str) and v in values


def matches(pattern: re.Pattern[str]) -> Check:
    return lambda v: isinstance(v, str) and pattern.fullmatch(v) is not None


def timestamp(v: Json) -> bool:
    return matches(TIMESTAMP)(v) and parse_time(v) is not None


def parse_time(v: Json) -> datetime.datetime | None:
    """A UTC timestamp matching TIMESTAMP and naming a real date and time, else None."""
    if not matches(TIMESTAMP)(v):
        return None
    try:
        return datetime.datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        return None


def is_null(v: Json) -> bool:
    return v is None


def mapping(v: Json) -> bool:
    return isinstance(v, dict)


def any_of(*checks: Check) -> Check:
    return lambda v: any(c(v) for c in checks)


def known_or_unknown(check: Check) -> Check:
    return any_of(check, is_unknown)


def get(data: Json, path: Sequence[str]) -> Json:
    for key in path:
        if not isinstance(data, dict) or key not in data:
            return None
        data = data[key]
    return data


# The manifest's fields: path, accepted values, and a short description of them for the error message.
FIELDS: tuple[tuple[tuple[str, ...], Check, str], ...] = (
    (("format",), one_of(frozenset({schema.MANIFEST_FORMAT})), schema.MANIFEST_FORMAT),
    (("run_id",), matches(RUN_ID), "a run ID: letters, digits, . _ : -"),
    (("provenance_claim",), one_of(schema.PROVENANCE_CLAIMS), "complete or partial"),
    (("analysis", "kind"), one_of(schema.ANALYSIS_KINDS), "primary or exploratory"),
    (("benchmark", "id"), text, "a benchmark ID"),
    (("benchmark", "definition"), known_or_unknown(text), "where the benchmark is defined, or an unknown"),
    (("protocol", "id"), text, "a protocol ID"),
    (("protocol", "dataset", "repo"), known_or_unknown(text), "a dataset name, or an unknown"),
    (("protocol", "dataset", "revision"), known_or_unknown(text), "a dataset revision, or an unknown"),
    (("protocol", "dataset", "split"), known_or_unknown(text), "a split name, or an unknown"),
    (("protocol", "dataset", "n_population"), positive, "the number of samples in the dataset split"),
    (("protocol", "scorer", "name"), text, "the scorer"),
    (("protocol", "scorer", "version"), known_or_unknown(text), "a scorer version or commit, or an unknown"),
    (("protocol", "scorer", "randomness", "controlled"), boolean, "true or false"),
    (("protocol", "scorer", "randomness", "policy"), text, "how scorer randomness is handled"),
    (("protocol", "output_preprocessing"), text, "what is done to an output before scoring ('none' if nothing)"),
    (("model", "id"), text, "a model ID"),
    (("model", "repo"), known_or_unknown(text), "a model repository, or an unknown"),
    (("model", "revision"), known_or_unknown(text), "a model revision, or an unknown"),
    (("model", "weights_sha256"), any_of(matches(SHA256), is_unknown, is_null), "a sha256, an unknown, or null"),
    (("inference", "backend", "name"), text, "a backend (engine or provider)"),
    (("inference", "backend", "version"), known_or_unknown(text), "a backend version, or an unknown"),
    (("inference", "dtype"), known_or_unknown(text), "a dtype, or an unknown"),
    (("inference", "quantization"), any_of(text, is_unknown, is_null), "a quantization, an unknown, or null"),
    (("inference", "temperature"), known_or_unknown(number), "a number, or an unknown"),
    (("inference", "top_p"), any_of(number, is_unknown, is_null), "a number, an unknown, or null"),
    (("inference", "max_output_tokens"), known_or_unknown(positive), "a positive integer, or an unknown"),
    (("inference", "context_length"), any_of(positive, is_unknown, is_null), "a positive integer, unknown, or null"),
    (("inference", "chat_template"), any_of(text, is_unknown, is_null), "a template, an unknown, or null"),
    (("inference", "system_prompt"), known_or_unknown(text), "what system prompt the model saw, or an unknown"),
    (("inference", "thinking"), known_or_unknown(text), "thinking mode, or an unknown"),
    (("inference", "batch_size"), any_of(positive, is_unknown, is_null), "a positive integer, an unknown, or null"),
    (("inference", "concurrency"), any_of(positive, is_unknown, is_null), "a positive integer, an unknown, or null"),
    (("inference", "seed"), any_of(integer, is_unknown, is_null), "an integer, an unknown, or null"),
    (("execution", "started_at"), known_or_unknown(timestamp), "a UTC timestamp, or an unknown"),
    (("execution", "finished_at"), known_or_unknown(timestamp), "a UTC timestamp, or an unknown"),
    (("execution", "source_commit"), known_or_unknown(matches(GIT_COMMIT)), "a 40-hex git commit, or an unknown"),
    (("execution", "environment"), any_of(mapping, is_unknown), "an object, or an unknown"),
    (("publication", "outputs"), one_of(schema.OUTPUT_PUBLICATION), "included or withheld"),
    (("publication", "license"), known_or_unknown(text), "the license of the published outputs, or an unknown"),
)


def check_manifest(manifest: Json, report: Report) -> None:
    if not isinstance(manifest, dict):
        report.add("manifest.type", "$", "the manifest is not a JSON object")
        return
    for path, check, expected in FIELDS:
        where = "$." + ".".join(path)
        value = get(manifest, path)
        parent = get(manifest, path[:-1]) if len(path) > 1 else manifest
        if not isinstance(parent, dict) or path[-1] not in parent:
            report.add("field.missing", where, f"required; expected {expected}")
        elif not check(value):
            report.add("field.invalid", where, f"expected {expected}, got {json.dumps(value)[:80]}")

    started = parse_time(get(manifest, ("execution", "started_at")))
    finished = parse_time(get(manifest, ("execution", "finished_at")))
    if started and finished and finished < started:
        report.add("execution.time_order", "$.execution.finished_at", "the run finishes before it starts")

    randomness = get(manifest, ("protocol", "scorer", "randomness"))
    if (
        isinstance(randomness, dict)
        and randomness.get("controlled") is False
        and not text(randomness.get("limitations"))
    ):
        report.add(
            "scorer.randomness",
            "$.protocol.scorer.randomness.limitations",
            "the scorer has uncontrolled randomness; describe the reproducibility limitation",
        )

    analysis = manifest.get("analysis")
    if isinstance(analysis, dict) and analysis.get("kind") == "exploratory":
        if not text(analysis.get("description")):
            report.add("analysis.description", "$.analysis.description", "an exploratory analysis says what it did")
        if not any_of(matches(RUN_ID), is_unknown)(analysis.get("derived_from")):
            report.add("analysis.derived_from", "$.analysis.derived_from", "the run ID it derives from, or unknown")
        if analysis.get("derived_from") == manifest.get("run_id"):
            report.add("analysis.derived_from", "$.analysis.derived_from", "an analysis cannot derive from itself")

    unknown = [p for p in schema.PROVENANCE_REQUIRED if not known(get(manifest, p), manifest, p)]
    report.provenance_complete = not unknown
    if manifest.get("provenance_claim") == "complete":
        for path in unknown:
            report.add(
                "provenance.incomplete",
                "$." + ".".join(path),
                "the manifest claims complete provenance, but this is missing or unknown",
            )


def known(value: Json, manifest: Json, path: Sequence[str]) -> bool:
    """Recorded and not an explicit unknown (and present in the manifest)."""
    parent = get(manifest, path[:-1])
    return isinstance(parent, dict) and path[-1] in parent and value is not None and not is_unknown(value)


METRIC_FIELDS: tuple[tuple[str, Check, str], ...] = (
    ("id", text, "a metric ID"),
    ("sample_key", text, "the per-sample score key"),
    ("unit", one_of(schema.UNITS), "one of " + ", ".join(sorted(schema.UNITS))),
    ("higher_is_better", boolean, "true or false"),
    ("aggregation", one_of(schema.AGGREGATIONS), "one of " + ", ".join(sorted(schema.AGGREGATIONS))),
    ("kind", one_of(schema.METRIC_KINDS), "quality or efficiency"),
)


def check_metrics(manifest: Json, report: Report) -> dict[str, dict[str, Json]]:
    """Valid metric definitions by ID. An invalid definition is reported and left out."""
    metrics = manifest.get("metrics") if isinstance(manifest, dict) else None
    if not isinstance(metrics, list) or not metrics:
        report.add("metrics.missing", "$.metrics", "at least one metric definition is required")
        return {}
    by_id: dict[str, dict[str, Json]] = {}
    seen: set[str] = set()
    for n, m in enumerate(metrics):
        where = f"$.metrics[{n}]"
        if not isinstance(m, dict):
            report.add("metrics.invalid", where, "not an object")
            continue
        bad = [key for key, check, _ in METRIC_FIELDS if not check(m.get(key))]
        for key, _, expected in METRIC_FIELDS:
            if key in bad:
                report.add("metrics.invalid", f"{where}.{key}", f"expected {expected}")
        if text(m.get("id")):
            if m["id"] in seen:
                report.add("metrics.duplicate", f"{where}.id", f"metric {m['id']!r} is defined twice")
            seen.add(m["id"])
            if not bad:
                by_id[m["id"]] = m
    return by_id


def check_artifacts(manifest: Json, run_dir: Path, report: Report) -> Path | None:
    """Verify every listed file against its checksum and size; return the path of the samples file."""
    artifacts = manifest.get("artifacts") if isinstance(manifest, dict) else None
    if not isinstance(artifacts, list) or not artifacts:
        report.add("artifacts.missing", "$.artifacts", "the manifest lists no artifacts")
        return None
    samples: list[Path] = []
    seen: set[str] = set()
    root = run_dir.resolve()
    for n, a in enumerate(artifacts):
        where = f"$.artifacts[{n}]"
        if not isinstance(a, dict) or not text(a.get("path")):
            report.add("artifacts.invalid", where, "an artifact needs a path")
            continue
        rel = PurePosixPath(a["path"])
        if rel.is_absolute() or ".." in rel.parts or "\\" in a["path"] or ":" in a["path"]:
            report.add("artifacts.path", f"{where}.path", "paths are relative to the run directory, with /")
            continue
        if a["path"] in seen:
            report.add("artifacts.duplicate", f"{where}.path", f"{a['path']} is listed twice")
        seen.add(a["path"])
        if a["path"] == "manifest.json":
            report.add("artifacts.path", f"{where}.path", "the manifest cannot list itself")
            continue
        if not one_of(schema.ARTIFACT_ROLES)(a.get("role")):
            report.add("artifacts.invalid", f"{where}.role", "one of " + ", ".join(sorted(schema.ARTIFACT_ROLES)))
        if not matches(SHA256)(a.get("sha256")) or not count(a.get("bytes")):
            report.add("artifacts.invalid", where, "an artifact needs sha256 (64 hex) and bytes")
            continue
        path = (root / rel).resolve()
        if root not in path.parents or not path.is_file():
            report.add("artifacts.absent", f"{where}.path", f"{a['path']} does not exist in the run directory")
            continue
        if path.stat().st_size != a["bytes"] or sha256_file(path) != a["sha256"]:
            report.add("checksum.mismatch", f"{where}.sha256", f"{a['path']} does not match its recorded checksum")
        if a.get("role") == "samples":
            samples.append(path)
    if len(samples) != 1:
        report.add("artifacts.samples", "$.artifacts", f"exactly one artifact with role samples, found {len(samples)}")
        return None
    return samples[0]


def read_samples(path: Path, report: Report) -> list[dict[str, Json]]:
    records: list[dict[str, Json]] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                report.add("samples.json", f"{path.name}:{line_no}", f"not valid JSON: {e.msg}")
                continue
            if not isinstance(record, dict):
                report.add("samples.json", f"{path.name}:{line_no}", "a record is a JSON object")
                continue
            records.append(record)
    return records


def scored_metric_ids(manifest: Json) -> set[str]:
    """Metrics with an observation in state ok: every scored sample must carry their per-sample score. A metric
    whose observation is not ok (for example `blocked_judge`) is not scored, so samples do not carry it."""
    observations = manifest.get("observations") if isinstance(manifest, dict) else None
    if not isinstance(observations, list):
        return set()
    return {
        o["metric"]
        for o in observations
        if isinstance(o, dict) and o.get("state") == "ok" and isinstance(o.get("metric"), str)
    }


def check_samples(
    records: list[dict[str, Json]], manifest: Json, metrics: Mapping[str, dict[str, Json]], report: Report
) -> None:
    outputs = get(manifest, ("publication", "outputs"))
    scored_metrics = scored_metric_ids(manifest)
    ids = [r.get("sample_id") for r in records]
    # IDs are compared as text, as source_id_digest joins them: 7 and "7" are the same sample.
    for sample_id, n in Counter(map(str, ids)).items():
        if n > 1:
            report.add("samples.duplicate_id", f"samples[sample_id={sample_id}]", f"sample ID appears {n} times")
    if len({type(i) for i in ids if text(i) or integer(i)}) > 1:
        report.add("samples.id_type", "samples[*].sample_id", "sample IDs mix strings and integers")
    for n, r in enumerate(records):
        where = f"samples[{n}]"
        if not (text(r.get("sample_id")) or integer(r.get("sample_id"))):
            report.add("samples.invalid", f"{where}.sample_id", "a sample ID is a non-empty string or an integer")
        state = r.get("state")
        if not isinstance(state, str) or state not in schema.STATES:
            report.add("samples.state", f"{where}.state", f"state must be one of the schema states, got {state!r}")
            continue
        scores = r.get("scores")
        if state == "ok":
            if r.get("error") is not None:
                report.add("samples.contradiction", where, "a scored sample (state ok) cannot carry an error")
            if not isinstance(scores, dict):
                report.add("samples.scores", f"{where}.scores", "a scored sample needs its scores")
            else:
                for m in metrics.values():
                    if m["aggregation"] != "external" and m["id"] in scored_metrics and m["sample_key"] not in scores:
                        report.add(
                            "samples.scores", f"{where}.scores.{m['sample_key']}", "missing score of a declared metric"
                        )
            if outputs == "included":
                # An empty string is a legitimate model output (and scores as it scores); a missing one is not.
                for key in ("raw_output", "scored_output"):
                    if not isinstance(r.get(key), str):
                        report.add("samples.output", f"{where}.{key}", "outputs are declared included but missing")
        else:
            # A request or execution failure is not a wrong answer: no scores, and the reason is recorded.
            if scores is not None:
                report.add("samples.contradiction", f"{where}.scores", f"a {state} sample cannot have scores")
            if not text(r.get("error")):
                report.add("samples.error", f"{where}.error", f"a {state} sample records why it was not scored")
        if outputs == "withheld" and (r.get("raw_output") is not None or r.get("scored_output") is not None):
            report.add("samples.output", where, "outputs are declared withheld but the record contains them")
    report.counts = dict(Counter(str(r.get("state")) for r in records))


def flatten(values: list[Json], aggregation: str) -> list[float] | None:
    """The numbers a `mean` or `micro_mean` averages; None when a value has the wrong shape or type."""
    flat: list[Json] = []
    for v in values:
        if aggregation == "micro_mean":
            if not isinstance(v, list):
                return None
            flat.extend(v)
        else:
            flat.append(v)
    if not all(number(x) or isinstance(x, bool) for x in flat):
        return None
    return [float(x) for x in flat]


def check_observations(
    records: list[dict[str, Json]],
    manifest: Json,
    metrics: Mapping[str, dict[str, Json]],
    samples_sha256: str | None,
    report: Report,
) -> None:
    observations = manifest.get("observations") if isinstance(manifest, dict) else None
    if not isinstance(observations, list) or not observations:
        report.add("observations.missing", "$.observations", "at least one observation is required")
        return
    scored = [r for r in records if r.get("state") == "ok"]
    seen: set[str] = set()
    for n, obs in enumerate(observations):
        where = f"$.observations[{n}]"
        for issue in observation_issues(obs):
            target = report.warnings if issue.code == "observation.extra" else report.issues
            target.append(Issue(issue.code, f"{where}{issue.path[1:]}", issue.message))
        if not isinstance(obs, dict):
            continue
        name = obs.get("metric")
        metric = metrics.get(name) if isinstance(name, str) else None
        if not isinstance(name, str) or metric is None:
            report.add("observations.metric", f"{where}.metric", f"metric {name!r} has no valid definition")
            continue
        if name in seen:
            report.add("observations.duplicate", f"{where}.metric", f"two observations for {name!r}")
        seen.add(name)
        state = obs.get("state")
        expected: list[tuple[str, Json]] = [
            ("task_id", get(manifest, ("benchmark", "id"))),
            ("model_id", get(manifest, ("model", "id"))),
            ("protocol_id", get(manifest, ("protocol", "id"))),
            ("unit", metric["unit"]),
            ("higher_is_better", metric["higher_is_better"]),
            ("n_population", get(manifest, ("protocol", "dataset", "n_population"))),
        ]
        # research/common/ewaluuj.py writes n_selected None for a task that failed before selecting samples.
        if state == "ok" or obs.get("n_selected") is not None:
            expected.append(("n_selected", len(records)))
        for key, value in expected:
            if obs.get(key) != value:
                report.add(
                    "observations.contradiction", f"{where}.{key}", f"is {obs.get(key)!r}, the run says {value!r}"
                )
        if state != "ok":
            carrying = [r for r in scored if isinstance(r.get("scores"), dict) and metric["sample_key"] in r["scores"]]
            if carrying:
                report.add(
                    "observations.state",
                    f"{where}.state",
                    f"is {state!r}, but {len(carrying)} samples carry a score for it; a scored metric has state ok",
                )
            continue
        if obs.get("n_scored") != len(scored):
            report.add(
                "observations.n_scored", f"{where}.n_scored", f"is {obs.get('n_scored')}, {len(scored)} samples are ok"
            )
        if obs.get("results_sha256") != samples_sha256:
            report.add("observations.results_sha256", f"{where}.results_sha256", "differs from the samples artifact")
        if obs.get("source_id_digest") != source_id_digest(r.get("sample_id") for r in records):
            report.add(
                "observations.source_id_digest",
                f"{where}.source_id_digest",
                "differs from the digest of the selected sample IDs",
            )
        check_value(obs, metric, scored, where, report)
    for name in metrics:
        if name not in seen:
            report.add("metrics.unobserved", f"$.metrics[id={name}]", "a declared metric has no observation")


def check_value(
    obs: dict[str, Json], metric: dict[str, Json], scored: list[dict[str, Json]], where: str, report: Report
) -> None:
    """Range of the recorded value, and the recomputation of `mean` and `micro_mean` metrics."""
    if not number(obs.get("value")):
        return
    value = float(obs["value"])
    if metric["unit"] == "percent" and not 0 <= value <= 100:
        report.add("observations.range", f"{where}.value", f"a percent value is between 0 and 100, got {value}")
    if metric["aggregation"] == "external":
        report.not_recomputed.append(metric["id"])
        return
    flat = flatten([(r.get("scores") or {}).get(metric["sample_key"]) for r in scored], metric["aggregation"])
    if not flat:
        report.add("observations.recompute", f"{where}.value", "per-sample scores cannot be aggregated")
        return
    if metric["unit"] == "percent" and not all(0 <= x <= 1 for x in flat):
        # Percent metrics are recomputed as 100 * mean, so each per-sample score is a fraction.
        report.add("samples.range", f"$.metrics[id={metric['id']}]", "per-sample scores of a percent metric are 0-1")
        return
    mean = sum(flat) / len(flat)
    recomputed = 100 * mean if metric["unit"] == "percent" else mean
    if abs(recomputed - value) > TOLERANCE:
        report.add(
            "observations.value", f"{where}.value", f"recorded {value}, recomputed from the samples {recomputed}"
        )


def observation_issues(obs: Json) -> list[Issue]:
    """Checks of one schema-2 observation on its own.

    These are the fields and invariants that research/common/metryki.py `bledy_schematu` checks (required fields,
    states, value and digests for `ok`, no value otherwise), plus ci95 and unit checks. This is not validation
    against the full JSON Schema of the results contract, which is not in this repository. Fields outside the ones
    `metryki.py` writes are reported as `observation.extra`; `check_observations` treats them as warnings.
    """
    issues: list[Issue] = []
    if not isinstance(obs, dict):
        return [Issue("observation.type", "$", "an observation is a JSON object")]
    issues += [
        Issue("observation.missing", f"$.{k}", "required field") for k in schema.OBSERVATION_FIELDS if k not in obs
    ]
    allowed = set(schema.OBSERVATION_FIELDS) | schema.OBSERVATION_OPTIONAL_FIELDS
    issues += [
        Issue("observation.extra", f"$.{k}", "not a field research/common/metryki.py writes; not checked")
        for k in obs
        if k not in allowed
    ]
    state = obs.get("state")
    if not isinstance(state, str) or state not in schema.STATES:
        issues.append(Issue("observation.state", "$.state", f"state must be one of the schema states, got {state!r}"))
        return issues
    if not isinstance(obs.get("unit"), str) or obs["unit"] not in schema.UNITS:
        issues.append(Issue("observation.unit", "$.unit", f"unit must be one of {sorted(schema.UNITS)}"))
    if state == "ok":
        if not number(obs.get("value")) or not (count(obs.get("n_scored")) and obs["n_scored"] >= 1):
            issues.append(Issue("observation.value", "$.value", "state ok needs a value and n_scored >= 1"))
        for k in ("source_id_digest", "results_sha256", "runner_sha256"):
            if not matches(SHA256)(obs.get(k)):
                issues.append(Issue("observation.digest", f"$.{k}", "state ok needs a sha256"))
        ci = obs.get("ci95")
        if ci is not None:
            ok_ci = (
                isinstance(ci, dict)
                and number(ci.get("lower"))
                and number(ci.get("upper"))
                and number(obs.get("value"))
                and number(ci.get("level"))
                and 0 < ci["level"] < 1
            )
            if not ok_ci or not ci["lower"] <= obs["value"] <= ci["upper"]:
                issues.append(
                    Issue("observation.ci95", "$.ci95", "ci95 needs a level in (0, 1) and lower <= value <= upper")
                )
    else:
        if obs.get("value") is not None or obs.get("ci95") is not None:
            issues.append(Issue("observation.value", "$.value", f"state {state} has no value and no ci95"))
        if obs.get("n_scored") not in (0, None):
            issues.append(Issue("observation.n_scored", "$.n_scored", f"state {state} has n_scored 0"))
    return issues


def validate_run(run_dir: Path) -> Report:
    """Validate one run directory. The result lists every problem found; no issues means structurally valid."""
    report = Report(run_dir)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        report.add("manifest.absent", str(manifest_path), "no manifest.json in the run directory")
        return report
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        report.add("manifest.json", str(manifest_path), f"not valid UTF-8 JSON: {e}")
        return report
    report.manifest_sha256 = sha256_file(manifest_path)
    run_id = manifest.get("run_id") if isinstance(manifest, dict) else None
    report.run_id = run_id if isinstance(run_id, str) else None
    check_manifest(manifest, report)
    metrics = check_metrics(manifest, report)
    samples_path = check_artifacts(manifest, run_dir, report)
    records: list[dict[str, Json]] = []
    if samples_path:
        report.samples_sha256 = sha256_file(samples_path)
        try:
            records = read_samples(samples_path, report)
        except UnicodeDecodeError as e:
            report.add("samples.json", samples_path.name, f"not valid UTF-8: {e}")
        check_samples(records, manifest, metrics, report)
    check_observations(records, manifest, metrics, report.samples_sha256, report)
    return report


FINGERPRINT_SECTIONS = ("benchmark", "protocol", "model", "inference", "metrics")


def protocol_fingerprint(manifest: Json) -> str:
    """Digest of what defines a measurement: benchmark, protocol (data, scorer, preprocessing), model identity,
    inference settings, and metric definitions. Run ID, timing, environment, and artifacts are not part of it."""
    part = {k: manifest.get(k) for k in FINGERPRINT_SECTIONS} if isinstance(manifest, dict) else {}
    return hashlib.sha256(json.dumps(part, sort_keys=True).encode("utf-8")).hexdigest()


def validate_runs(run_dirs: Sequence[Path]) -> list[Report]:
    """Validate several runs together: each on its own, plus checks across runs.

    - Run IDs are unique, and no directory is listed twice.
    - Two runs of the same model may share a protocol ID only with an identical protocol fingerprint; otherwise one
      ID would name two different measurements (for example bf16 and a quantized model). Repeated runs of one
      protocol, to measure run-to-run variance, are allowed: they differ only in run ID and timing.
    - Runs with byte-identical samples get a warning: a copy relabelled as another run looks the same as a fully
      deterministic rerun, and the validator cannot tell them apart.
    """
    reports = [validate_run(d) for d in run_dirs]
    by_run: dict[str, Report] = {}
    by_dir: dict[Path, Report] = {}
    by_samples: dict[str, Report] = {}
    fingerprints: dict[tuple[str, str], tuple[str, Report]] = {}
    for d, report in zip(run_dirs, reports, strict=True):
        resolved = d.resolve()
        if resolved in by_dir:
            report.add("runs.duplicate_dir", "$", f"the same directory is listed twice ({by_dir[resolved].run_dir})")
            continue
        by_dir[resolved] = report
        if report.run_id is not None:
            if report.run_id in by_run:
                report.add(
                    "runs.duplicate_id",
                    "$.run_id",
                    f"run ID {report.run_id!r} is used by {by_run[report.run_id].run_dir}",
                )
            by_run.setdefault(report.run_id, report)
        if report.samples_sha256 is not None:
            if report.samples_sha256 in by_samples:
                report.warn(
                    "runs.same_samples",
                    "$.artifacts",
                    f"samples are byte-identical to {by_samples[report.samples_sha256].run_dir}",
                )
            by_samples.setdefault(report.samples_sha256, report)
        try:
            manifest = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        key = (json.dumps(get(manifest, ("protocol", "id"))), json.dumps(get(manifest, ("model", "id"))))
        fp = protocol_fingerprint(manifest)
        if key in fingerprints and fingerprints[key][0] != fp:
            report.add(
                "runs.protocol_reused",
                "$.protocol.id",
                f"protocol {get(manifest, ('protocol', 'id'))!r} has other settings in {fingerprints[key][1].run_dir}",
            )
        fingerprints.setdefault(key, (fp, report))
    return reports
