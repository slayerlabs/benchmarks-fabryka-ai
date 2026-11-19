"""Validation of a CodeSOTA run directory: manifest, per-sample records, aggregates, and checksums.

A run directory holds `manifest.json` and the artifacts it lists, among them exactly one per-sample JSONL file
(role `samples`). Nothing here runs a model, calls a network, or rescores outputs: the validator checks that the
recorded evidence is complete, consistent with itself, and unmodified.

Unknown metadata is written as `{"unknown": "<why it is unknown>"}`, never guessed. `null` means "does not apply"
(for example `top_p` under greedy decoding) and is accepted only where a field allows it.
"""

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
    """One reason a run is not valid: a stable code for tests and tools, the JSON path, and a sentence."""

    code: str
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} at {self.path}: {self.message}"


@dataclass
class Report:
    run_dir: Path
    run_id: str | None = None
    issues: list[Issue] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    manifest_sha256: str | None = None

    @property
    def ok(self) -> bool:
        return not self.issues

    def add(self, code: str, path: str, message: str) -> None:
        self.issues.append(Issue(code, path, message))

    def codes(self) -> set[str]:
        return {i.code for i in self.issues}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def source_id_digest(sample_ids: Iterable[object]) -> str:
    """Digest of the scored sample IDs in record order, as research/common/ewaluuj.py computes `source_id_digest`."""
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
    (("claim",), one_of(schema.CLAIMS), "one of " + ", ".join(sorted(schema.CLAIMS))),
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
    (("execution", "started_at"), known_or_unknown(matches(TIMESTAMP)), "a UTC timestamp, or an unknown"),
    (("execution", "finished_at"), known_or_unknown(matches(TIMESTAMP)), "a UTC timestamp, or an unknown"),
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

    if manifest.get("claim") == "verified":
        if isinstance(analysis, dict) and analysis.get("kind") != "primary":
            report.add("claim.verified", "$.analysis.kind", "an exploratory analysis cannot be a verified result")
        for path in schema.VERIFIED_REQUIRES_KNOWN:
            if is_unknown(get(manifest, path)):
                report.add(
                    "claim.verified",
                    "$." + ".".join(path),
                    "a verified result needs this provenance; it is recorded as unknown",
                )


def check_metrics(manifest: Json, report: Report) -> dict[str, Json]:
    metrics = manifest.get("metrics") if isinstance(manifest, dict) else None
    if not isinstance(metrics, list) or not metrics:
        report.add("metrics.missing", "$.metrics", "at least one metric definition is required")
        return {}
    by_id: dict[str, Json] = {}
    for n, m in enumerate(metrics):
        where = f"$.metrics[{n}]"
        if not isinstance(m, dict):
            report.add("metrics.invalid", where, "not an object")
            continue
        for key, check, expected in (
            ("id", text, "a metric ID"),
            ("sample_key", text, "the per-sample score key"),
            ("unit", one_of(schema.UNITS), "one of " + ", ".join(sorted(schema.UNITS))),
            ("higher_is_better", boolean, "true or false"),
            ("aggregation", one_of(schema.AGGREGATIONS), "one of " + ", ".join(sorted(schema.AGGREGATIONS))),
            ("kind", one_of(schema.METRIC_KINDS), "quality or efficiency"),
        ):
            if not check(m.get(key)):
                report.add("metrics.invalid", f"{where}.{key}", f"expected {expected}")
        if text(m.get("id")):
            if m["id"] in by_id:
                report.add("metrics.duplicate", f"{where}.id", f"metric {m['id']!r} is defined twice")
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
        if rel.is_absolute() or ".." in rel.parts or "\\" in a["path"]:
            report.add("artifacts.path", f"{where}.path", "paths are relative to the run directory, with /")
            continue
        if a["path"] in seen:
            report.add("artifacts.duplicate", f"{where}.path", f"{a['path']} is listed twice")
        seen.add(a["path"])
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


def check_samples(records: list[dict[str, Json]], manifest: Json, metrics: Mapping[str, Json], report: Report) -> None:
    outputs = get(manifest, ("publication", "outputs"))
    ids = [r.get("sample_id") for r in records]
    for sample_id, n in Counter(map(str, ids)).items():
        if n > 1:
            report.add("samples.duplicate_id", f"samples[sample_id={sample_id}]", f"sample ID appears {n} times")
    keys = [m["sample_key"] for m in metrics.values() if m.get("aggregation") != "external"]
    for n, r in enumerate(records):
        where = f"samples[{n}]"
        if not (text(r.get("sample_id")) or integer(r.get("sample_id"))):
            report.add("samples.invalid", f"{where}.sample_id", "a sample ID is a non-empty string or an integer")
        state = r.get("state")
        if state not in schema.STATES:
            report.add("samples.state", f"{where}.state", f"state must be one of the schema states, got {state!r}")
            continue
        scores = r.get("scores")
        if state == "ok":
            if r.get("error") is not None:
                report.add("samples.contradiction", where, "a scored sample (state ok) cannot carry an error")
            if not isinstance(scores, dict):
                report.add("samples.scores", f"{where}.scores", "a scored sample needs its scores")
            else:
                for key in keys:
                    if key not in scores:
                        report.add("samples.scores", f"{where}.scores.{key}", "missing score of a declared metric")
            if outputs == "included" and not isinstance(r.get("raw_output"), str):
                report.add("samples.output", f"{where}.raw_output", "outputs are declared included but missing")
        else:
            # A request or execution failure is not a wrong answer: no scores, and the reason is recorded.
            if scores is not None:
                report.add("samples.contradiction", f"{where}.scores", f"a {state} sample cannot have scores")
            if not text(r.get("error")):
                report.add("samples.error", f"{where}.error", f"a {state} sample records why it was not scored")
        if outputs == "withheld" and (r.get("raw_output") is not None or r.get("scored_output") is not None):
            report.add("samples.output", where, "outputs are declared withheld but the record contains them")
    report.counts = dict(Counter(str(r.get("state")) for r in records))


def aggregate(values: list[Json], aggregation: str) -> float | None:
    """Mean of the per-sample values; None when they are not numbers of the declared shape."""
    flat: list[Json] = []
    for v in values:
        if aggregation == "micro_mean":
            if not isinstance(v, list):
                return None
            flat.extend(v)
        else:
            flat.append(v)
    if not flat or not all(number(x) or isinstance(x, bool) for x in flat):
        return None
    return sum(float(x) for x in flat) / len(flat)


def check_observations(
    records: list[dict[str, Json]],
    manifest: Json,
    metrics: Mapping[str, Json],
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
            report.add(issue.code, f"{where}{issue.path[1:]}", issue.message)
        if not isinstance(obs, dict):
            continue
        metric = metrics.get(obs.get("metric", ""))
        if metric is None:
            report.add("observations.metric", f"{where}.metric", f"metric {obs.get('metric')!r} is not defined")
            continue
        if obs["metric"] in seen:
            report.add("observations.duplicate", f"{where}.metric", f"two observations for {obs['metric']!r}")
        seen.add(obs["metric"])
        for key, expected in (
            ("task_id", get(manifest, ("benchmark", "id"))),
            ("model_id", get(manifest, ("model", "id"))),
            ("protocol_id", get(manifest, ("protocol", "id"))),
            ("unit", metric.get("unit")),
            ("higher_is_better", metric.get("higher_is_better")),
            ("n_population", get(manifest, ("protocol", "dataset", "n_population"))),
            ("n_selected", len(records)),
        ):
            if obs.get(key) != expected:
                report.add(
                    "observations.contradiction", f"{where}.{key}", f"is {obs.get(key)!r}, the run says {expected!r}"
                )
        if obs.get("state") != "ok":
            continue
        if obs.get("n_scored") != len(scored):
            report.add(
                "observations.n_scored",
                f"{where}.n_scored",
                f"is {obs.get('n_scored')}, {len(scored)} samples have state ok",
            )
        if obs.get("results_sha256") != samples_sha256:
            report.add("observations.results_sha256", f"{where}.results_sha256", "differs from the samples artifact")
        if obs.get("source_id_digest") != source_id_digest(r.get("sample_id") for r in scored):
            report.add(
                "observations.source_id_digest",
                f"{where}.source_id_digest",
                "differs from the digest of the scored sample IDs",
            )
        if metric.get("aggregation") == "external" or not number(obs.get("value")):
            continue
        mean = aggregate([(r.get("scores") or {}).get(metric["sample_key"]) for r in scored], metric["aggregation"])
        if mean is None:
            report.add("observations.recompute", f"{where}.value", "per-sample scores cannot be aggregated")
            continue
        recomputed = 100 * mean if metric.get("unit") == "percent" else mean
        if abs(recomputed - obs["value"]) > TOLERANCE:
            report.add(
                "observations.value",
                f"{where}.value",
                f"recorded {obs['value']}, recomputed from the samples {recomputed}",
            )


def observation_issues(obs: Json) -> list[Issue]:
    """Checks of one schema-2 observation on its own, as research/common/metryki.py `bledy_schematu` does."""
    issues: list[Issue] = []
    if not isinstance(obs, dict):
        return [Issue("observation.type", "$", "an observation is a JSON object")]
    issues += [
        Issue("observation.missing", f"$.{k}", "required field") for k in schema.OBSERVATION_FIELDS if k not in obs
    ]
    allowed = set(schema.OBSERVATION_FIELDS) | schema.OBSERVATION_OPTIONAL_FIELDS
    issues += [
        Issue("observation.extra", f"$.{k}", "not a field of the results schema") for k in obs if k not in allowed
    ]
    state = obs.get("state")
    if state not in schema.STATES:
        issues.append(Issue("observation.state", "$.state", f"state must be one of the schema states, got {state!r}"))
        return issues
    if obs.get("unit") not in schema.UNITS:
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
            )
            if not ok_ci or not ci["lower"] <= obs["value"] <= ci["upper"]:
                issues.append(Issue("observation.ci95", "$.ci95", "ci95 needs lower <= value <= upper"))
    else:
        if obs.get("value") is not None or obs.get("ci95") is not None:
            issues.append(Issue("observation.value", "$.value", f"state {state} has no value and no ci95"))
        if obs.get("n_scored") not in (0, None):
            issues.append(Issue("observation.n_scored", "$.n_scored", f"state {state} has n_scored 0"))
    return issues


def validate_run(run_dir: Path) -> Report:
    """Validate one run directory. The result lists every problem found; an empty list means valid."""
    report = Report(run_dir)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        report.add("manifest.absent", str(manifest_path), "no manifest.json in the run directory")
        return report
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        report.add("manifest.json", str(manifest_path), f"not valid JSON: {e.msg}")
        return report
    report.manifest_sha256 = sha256_file(manifest_path)
    report.run_id = manifest.get("run_id") if isinstance(manifest, dict) else None
    check_manifest(manifest, report)
    metrics = check_metrics(manifest, report)
    samples_path = check_artifacts(manifest, run_dir, report)
    records = read_samples(samples_path, report) if samples_path else []
    if samples_path:
        check_samples(records, manifest, metrics, report)
    check_observations(records, manifest, metrics, sha256_file(samples_path) if samples_path else None, report)
    return report


def protocol_fingerprint(manifest: Json) -> str:
    """Digest of everything that defines how a run was produced: protocol, model identity, and inference settings."""
    part = {k: manifest.get(k) for k in ("protocol", "model", "inference")} if isinstance(manifest, dict) else {}
    return hashlib.sha256(json.dumps(part, sort_keys=True).encode("utf-8")).hexdigest()


def validate_runs(run_dirs: Sequence[Path]) -> list[Report]:
    """Validate several runs together: each on its own, plus run IDs unique and protocol IDs used consistently.

    Two runs of the same model may share a protocol ID only when their protocol, model, and inference settings are
    identical; otherwise one ID would stand for two different measurements (for example bf16 and a quantized model).
    Repeated runs of one protocol (to measure run-to-run variance) are allowed: they differ only in run ID.
    """
    reports = [validate_run(d) for d in run_dirs]
    by_run: dict[str, Report] = {}
    fingerprints: dict[tuple[str, str], tuple[str, Report]] = {}
    for d, report in zip(run_dirs, reports, strict=True):
        if report.run_id in by_run:
            report.add(
                "runs.duplicate_id", "$.run_id", f"run ID {report.run_id!r} is used by {by_run[report.run_id].run_dir}"
            )
        if report.run_id:
            by_run[report.run_id] = report
        try:
            manifest = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        key = (str(get(manifest, ("protocol", "id"))), str(get(manifest, ("model", "id"))))
        fp = protocol_fingerprint(manifest)
        if key in fingerprints and fingerprints[key][0] != fp:
            report.add(
                "runs.protocol_reused",
                "$.protocol.id",
                f"protocol {key[0]!r} has different settings in {fingerprints[key][1].run_dir}",
            )
        fingerprints.setdefault(key, (fp, report))
    return reports
