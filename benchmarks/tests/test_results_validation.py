"""Run manifest validation against synthetic runs: each test breaks one property and expects its issue code."""

import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

import runs
from codesota.results import protocol_fingerprint, sha256_file, source_id_digest, validate_run, validate_runs
from codesota.results.__main__ import main

Mutation = Callable[[dict[str, Any]], None]


def load(run_dir: Path) -> dict[str, Any]:
    manifest: dict[str, Any] = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    return manifest


def save(run_dir: Path, manifest: dict[str, Any]) -> None:
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def rewrite_samples(run_dir: Path, change: Callable[[list[dict[str, Any]]], None], *, fix_sha: bool) -> None:
    """Change the samples; with fix_sha, also update the recorded checksums so only the content check can fail."""
    path = run_dir / "samples.jsonl"
    recs = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    change(recs)
    path.write_bytes(b"".join(json.dumps(r).encode("utf-8") + b"\n" for r in recs))
    if fix_sha:
        m = load(run_dir)
        m["artifacts"][0].update(sha256=sha256_file(path), bytes=path.stat().st_size)
        for obs in m["observations"]:
            obs["results_sha256"] = sha256_file(path)
        save(run_dir, m)


@pytest.fixture
def local(tmp_path: Path) -> Path:
    return runs.local_bf16(tmp_path / "local")


@pytest.fixture
def api(tmp_path: Path) -> Path:
    return runs.provider_api(tmp_path / "api")


def test_committed_fixtures_are_valid() -> None:
    reports = validate_runs(sorted(p for p in runs.FIXTURES.iterdir() if p.is_dir()))
    assert len(reports) == 2
    assert [str(i) for r in reports for i in r.issues] == []


def test_fixtures_are_reproducible(tmp_path: Path) -> None:
    for name, build in (("local-bf16", runs.local_bf16), ("provider-api", runs.provider_api)):
        built = build(tmp_path / name)
        for f in ("manifest.json", "samples.jsonl"):
            assert (built / f).read_bytes() == (runs.FIXTURES / name / f).read_bytes(), f"{name}/{f}"


def test_valid_run_passes_and_counts_states(local: Path, api: Path) -> None:
    assert validate_run(local).ok
    report = validate_run(api)
    assert report.ok, [str(i) for i in report.issues]
    assert report.counts == {"ok": 5, "failed": 1}


def test_failed_sample_is_not_a_wrong_answer(api: Path) -> None:
    # 5 scored samples; the failed request is outside the denominator, not a zero.
    obs = {o["metric"]: o for o in load(api)["observations"]}["prompt_level_strict_acc"]
    assert (obs["n_selected"], obs["n_scored"], obs["value"]) == (6, 5, 60.0)


def test_failed_sample_counted_as_zero_is_rejected(api: Path) -> None:
    m = load(api)
    for obs in m["observations"]:
        obs["n_scored"] = 6
    save(api, m)
    assert "observations.n_scored" in validate_run(api).codes()


def test_duplicate_sample_id_is_rejected(local: Path) -> None:
    rewrite_samples(local, lambda recs: recs[1].update(sample_id=recs[0]["sample_id"]), fix_sha=True)
    assert "samples.duplicate_id" in validate_run(local).codes()


@pytest.mark.parametrize("state", ["", "pass", None])
def test_invalid_sample_state_is_rejected(local: Path, state: str | None) -> None:
    rewrite_samples(local, lambda recs: recs[2].update(state=state), fix_sha=True)
    assert "samples.state" in validate_run(local).codes()


def test_missing_sample_state_is_rejected(local: Path) -> None:
    rewrite_samples(local, lambda recs: recs[2].pop("state"), fix_sha=True)
    assert "samples.state" in validate_run(local).codes()


def test_invalid_observation_state_is_rejected(local: Path) -> None:
    m = load(local)
    m["observations"][0]["state"] = "passed"
    save(local, m)
    assert "observation.state" in validate_run(local).codes()


def test_failed_sample_with_scores_is_rejected(local: Path) -> None:
    rewrite_samples(local, lambda recs: recs[0].update(state="failed", error="timeout"), fix_sha=True)
    codes = validate_run(local).codes()
    assert "samples.contradiction" in codes  # a failed sample cannot also be scored
    assert "observations.n_scored" in codes


def test_blocked_sample_without_reason_is_rejected(local: Path) -> None:
    rewrite_samples(local, lambda recs: recs[0].update(state="blocked_access", scores=None), fix_sha=True)
    assert "samples.error" in validate_run(local).codes()


def test_recorded_score_that_does_not_match_samples_is_rejected(local: Path) -> None:
    m = load(local)
    m["observations"][0]["value"] += 0.01
    save(local, m)
    issues = [i for i in validate_run(local).issues if i.code == "observations.value"]
    assert len(issues) == 1 and issues[0].path == "$.observations[0].value"


def test_changed_sample_score_is_caught_by_recomputation(local: Path) -> None:
    # Flip one score and update the checksums too: the aggregate check must still catch it.
    rewrite_samples(local, lambda recs: recs[3]["scores"].update(prompt_level_strict_acc=True), fix_sha=True)
    assert "observations.value" in validate_run(local).codes()


def test_instruction_level_metric_is_recomputed_over_all_instructions(local: Path) -> None:
    obs = {o["metric"]: o for o in load(local)["observations"]}
    assert obs["inst_level_strict_acc"]["value"] == pytest.approx(100 * 8 / 11)
    assert obs["prompt_level_strict_acc"]["value"] == pytest.approx(50.0)
    assert obs["prompt_level_loose_acc"]["value"] == pytest.approx(100 * 4 / 6)


def test_modified_artifact_fails_checksum(local: Path) -> None:
    rewrite_samples(local, lambda recs: recs[0].update(raw_output="edited"), fix_sha=False)
    assert "checksum.mismatch" in validate_run(local).codes()


def test_missing_artifact_is_rejected(local: Path) -> None:
    (local / "samples.jsonl").unlink()
    assert "artifacts.absent" in validate_run(local).codes()


def test_artifact_path_cannot_leave_the_run_directory(local: Path) -> None:
    m = load(local)
    m["artifacts"][0]["path"] = "../local/samples.jsonl"
    save(local, m)
    assert "artifacts.path" in validate_run(local).codes()


@pytest.mark.parametrize(
    ("change", "code"),
    [
        (lambda m: m["observations"][0].update(model_id="example/other"), "observations.contradiction"),
        (lambda m: m["observations"][0].update(protocol_id="other"), "observations.contradiction"),
        (lambda m: m["observations"][0].update(unit="score"), "observations.contradiction"),
        (lambda m: m["observations"][0].update(n_population=7), "observations.contradiction"),
        (lambda m: m["observations"][0].update(metric="undeclared"), "observations.metric"),
        (lambda m: m["observations"][0].update(metric=["not", "a", "name"]), "observations.metric"),
        (lambda m: m["observations"].append(dict(m["observations"][0])), "observations.duplicate"),
        (lambda m: m["observations"].pop(), "metrics.unobserved"),
        (lambda m: m["observations"][0].update(source_id_digest="d" * 64), "observations.source_id_digest"),
        (lambda m: m["observations"][0].update(ci95={"lower": 60.0, "upper": 70.0, "level": 0.95}), "observation.ci95"),
        (lambda m: m["observations"][0].update(ci95={"lower": 40.0, "upper": 60.0}), "observation.ci95"),  # no level
        (lambda m: m["observations"][0].update(state="failed"), "observation.value"),
        (lambda m: m["metrics"].append(dict(m["metrics"][0])), "metrics.duplicate"),
        (lambda m: m["metrics"][0].update(kind="speed"), "metrics.invalid"),
        (lambda m: m["inference"].update(temperature="zero"), "field.invalid"),
        (lambda m: m["inference"].pop("dtype"), "field.missing"),
        (lambda m: m.pop("provenance_claim"), "field.missing"),
        (lambda m: m["execution"].update(started_at="yesterday"), "field.invalid"),
        (lambda m: m["execution"].update(started_at="2026-02-30T10:00:00Z"), "field.invalid"),  # no such date
        (lambda m: m["execution"].update(finished_at="2026-11-19T09:59:59Z"), "execution.time_order"),
        (lambda m: m["publication"].update(outputs="withheld"), "samples.output"),
        (lambda m: m.update(format="urn:other"), "field.invalid"),
        (lambda m: m["artifacts"].append({**m["artifacts"][0], "path": "manifest.json"}), "artifacts.path"),
    ],
)
def test_contradictory_or_malformed_manifest_is_rejected(local: Path, change: Mutation, code: str) -> None:
    m = load(local)
    change(m)
    save(local, m)
    assert code in validate_run(local).codes()


@pytest.mark.parametrize(
    "change",
    [
        lambda m: m.update(metrics="all"),
        lambda m: m.update(metrics=[{"id": "x"}]),
        lambda m: m["metrics"][0].pop("sample_key"),
        lambda m: m["metrics"][0].update(aggregation=None),
        lambda m: m.update(observations=[None, 3, "x"]),
        lambda m: m["observations"][0].update(state=["ok"], unit={"u": 1}),
        lambda m: m.update(artifacts=[{"path": 5}, None]),
        lambda m: m.update(protocol=None, model=[], inference="x", execution=7),
        lambda m: m["analysis"].update(kind=None),
        lambda m: m.update(run_id=12),
    ],
)
def test_malformed_values_are_reported_not_raised(local: Path, change: Mutation) -> None:
    m = load(local)
    change(m)
    save(local, m)
    assert not validate_run(local).ok


def test_manifest_that_is_not_an_object_is_reported(local: Path) -> None:
    (local / "manifest.json").write_text("[1, 2]", encoding="utf-8")
    assert "manifest.type" in validate_run(local).codes()


def test_extra_observation_field_is_a_warning(local: Path) -> None:
    # The full JSON Schema of the results contract is not in this repository, so a field outside what
    # research/common/metryki.py writes is reported, not rejected.
    m = load(local)
    m["observations"][0]["stderr"] = 1.0
    save(local, m)
    report = validate_run(local)
    assert report.ok and "observation.extra" in report.warning_codes()


@pytest.mark.parametrize("value", [None, "", {"unknown": ""}, {"unknown": "x", "guess": "y"}])
def test_unknown_must_be_explicit(local: Path, value: Any) -> None:
    m = load(local)
    m["model"]["revision"] = value
    save(local, m)
    assert "field.invalid" in validate_run(local).codes()


def test_unknown_provider_revision_is_preserved(api: Path) -> None:
    m = load(api)
    assert m["model"]["revision"] == {"unknown": "the provider does not expose the served model revision"}
    report = validate_run(api)
    assert report.ok and not report.provenance_complete


def test_complete_provenance_claim_requires_known_fields(api: Path) -> None:
    m = load(api)
    m["provenance_claim"] = "complete"
    save(api, m)
    paths = {i.path for i in validate_run(api).issues if i.code == "provenance.incomplete"}
    assert paths == {"$.model.revision", "$.inference.backend.version"}


def test_provenance_completeness_is_reported_independently_of_the_claim(local: Path) -> None:
    assert validate_run(local).provenance_complete
    m = load(local)
    m["execution"]["finished_at"] = {"unknown": "the log was lost"}
    m["provenance_claim"] = "partial"
    save(local, m)
    report = validate_run(local)
    assert report.ok and not report.provenance_complete


def test_uncontrolled_scorer_randomness_needs_a_stated_limitation(local: Path) -> None:
    m = load(local)
    m["protocol"]["scorer"]["randomness"] = {
        "controlled": False,
        "policy": "upstream scorer as released",
        "limitations": None,
    }
    save(local, m)
    assert "scorer.randomness" in validate_run(local).codes()
    m["protocol"]["scorer"]["randomness"]["limitations"] = "language detection is unseeded; rescoring may differ"
    save(local, m)
    assert validate_run(local).ok


def test_exploratory_analysis_is_labelled(local: Path) -> None:
    m = load(local)
    m["analysis"] = {"kind": "exploratory", "derived_from": m["run_id"]}
    save(local, m)
    codes = validate_run(local).codes()
    assert {"analysis.description", "analysis.derived_from"} <= codes  # no description; derives from itself
    m["analysis"] = {"kind": "exploratory", "derived_from": "synthetic.primary-run", "description": "excludes 2 items"}
    save(local, m)
    assert validate_run(local).ok


def test_non_ok_observation_cannot_hide_scored_samples(local: Path) -> None:
    # Samples carry scores for the metric, but its observation says it was not scored.
    m = load(local)
    m["observations"][0].update(state="failed", value=None, n_scored=0, reason="judge unavailable")
    save(local, m)
    assert "observations.state" in validate_run(local).codes()


def test_blocked_metric_is_consistent_when_samples_do_not_carry_it(local: Path) -> None:
    # One metric could not be scored (state blocked_judge): its samples have no score for it, the others do.
    def drop(recs: list[dict[str, Any]]) -> None:
        for r in recs:
            r["scores"].pop("prompt_level_loose_acc")

    rewrite_samples(local, drop, fix_sha=True)
    m = load(local)
    obs = next(o for o in m["observations"] if o["metric"] == "prompt_level_loose_acc")
    obs.update(state="blocked_judge", value=None, ci95=None, n_scored=0, reason="no judge access")
    save(local, m)
    report = validate_run(local)
    assert report.ok, [str(i) for i in report.issues]


def test_external_metric_is_listed_as_not_recomputed(local: Path) -> None:
    m = load(local)
    m["metrics"][0]["aggregation"] = "external"
    m["observations"][0]["value"] = 12.34  # not recomputable, so not checked against the samples
    save(local, m)
    report = validate_run(local)
    assert report.ok and report.not_recomputed == ["prompt_level_strict_acc"]


@pytest.mark.parametrize("value", [-0.1, 100.5])
def test_percent_value_out_of_range_is_rejected(local: Path, value: float) -> None:
    m = load(local)
    m["metrics"][0]["aggregation"] = "external"
    m["observations"][0]["value"] = value
    save(local, m)
    assert "observations.range" in validate_run(local).codes()


def test_per_sample_percent_scores_are_fractions(local: Path) -> None:
    rewrite_samples(local, lambda recs: recs[0]["scores"].update(prompt_level_strict_acc=100), fix_sha=True)
    assert "samples.range" in validate_run(local).codes()


def test_sample_ids_mixing_types_are_rejected(local: Path) -> None:
    rewrite_samples(local, lambda recs: recs[0].update(sample_id=7), fix_sha=True)
    assert "samples.id_type" in validate_run(local).codes()


def test_sample_ids_equal_as_text_are_duplicates(local: Path) -> None:
    def ids(recs: list[dict[str, Any]]) -> None:
        recs[0]["sample_id"], recs[1]["sample_id"] = 7, "7"

    rewrite_samples(local, ids, fix_sha=True)
    assert {"samples.duplicate_id", "samples.id_type"} <= validate_run(local).codes()


@pytest.mark.parametrize("sample_id", ["", "  ", True, None, 1.5])
def test_invalid_sample_id_is_rejected(local: Path, sample_id: Any) -> None:
    rewrite_samples(local, lambda recs: recs[0].update(sample_id=sample_id), fix_sha=True)
    assert "samples.invalid" in validate_run(local).codes()


@pytest.mark.parametrize("key", ["raw_output", "scored_output"])
def test_missing_output_is_rejected_when_outputs_are_included(local: Path, key: str) -> None:
    rewrite_samples(local, lambda recs: recs[0].pop(key), fix_sha=True)
    assert "samples.output" in validate_run(local).codes()


def test_empty_output_is_a_legitimate_answer(local: Path) -> None:
    # An empty response is what the model returned; it is scored like any other output (here: wrong).
    def empty(recs: list[dict[str, Any]]) -> None:
        recs[3].update(raw_output="", scored_output="")

    rewrite_samples(local, empty, fix_sha=True)
    assert validate_run(local).ok


def test_digest_covers_selected_samples_including_failed(api: Path) -> None:
    # As in research/common/ewaluuj.py: source_id_digest is over the selected IDs, not only the scored ones.
    m = load(api)
    recs = [json.loads(line) for line in (api / "samples.jsonl").read_text(encoding="utf-8").splitlines()]
    assert m["observations"][0]["source_id_digest"] == source_id_digest(r["sample_id"] for r in recs)


def test_runs_of_one_model_stay_distinguishable(local: Path, api: Path) -> None:
    reports = validate_runs([local, api])
    assert all(r.ok for r in reports)
    a, b = load(local), load(api)
    assert a["model"]["id"] == b["model"]["id"] and a["benchmark"]["id"] == b["benchmark"]["id"]
    assert a["run_id"] != b["run_id"] and a["protocol"]["id"] != b["protocol"]["id"]
    assert protocol_fingerprint(a) != protocol_fingerprint(b)


def test_duplicate_run_id_is_rejected(tmp_path: Path, local: Path) -> None:
    copy_dir = tmp_path / "copy"
    shutil.copytree(local, copy_dir)
    report = validate_runs([local, copy_dir])[1]
    assert "runs.duplicate_id" in report.codes() and "runs.same_samples" in report.warning_codes()


def test_same_directory_listed_twice_is_rejected(local: Path) -> None:
    assert "runs.duplicate_dir" in validate_runs([local, local])[1].codes()


def test_relabelled_copy_is_flagged(tmp_path: Path, local: Path) -> None:
    # A copy given a new run ID is not rejected (a deterministic rerun looks the same), but it is reported.
    copy_dir = tmp_path / "relabelled"
    shutil.copytree(local, copy_dir)
    m = load(copy_dir)
    m["run_id"] = "synthetic.relabelled"
    save(copy_dir, m)
    report = validate_runs([local, copy_dir])[1]
    assert report.ok and "runs.same_samples" in report.warning_codes()


@pytest.mark.parametrize(
    "change",
    [
        lambda m: m["inference"].update(quantization="nvfp4"),
        lambda m: m["inference"].update(concurrency=16),
        lambda m: m["inference"].update(thinking="disabled"),
        lambda m: m["protocol"]["scorer"].update(version="fixture-2"),
        lambda m: m["protocol"]["scorer"]["randomness"].update(policy="seed 0 per sample"),
        lambda m: m["protocol"].update(output_preprocessing="strip text before the last </think>"),
        lambda m: m["protocol"]["dataset"].update(revision="fixture-2"),
        lambda m: m["metrics"][1].update(aggregation="external"),
        lambda m: m["model"].update(revision="e" * 40),
    ],
)
def test_protocol_id_reused_with_other_settings_is_rejected(tmp_path: Path, local: Path, change: Mutation) -> None:
    # Same model and protocol ID, different inference or scoring: one protocol ID would name two measurements.
    m = runs.base_manifest("synthetic.toy.example-model-1b.variant.20261119T120000Z")
    change(m)
    other = runs.write_run(tmp_path / "variant", m, runs.records())
    assert "runs.protocol_reused" in validate_runs([local, other])[1].codes()


def test_repeated_run_of_one_protocol_is_allowed(tmp_path: Path, local: Path) -> None:
    m = runs.base_manifest("synthetic.toy.repeat.20261119T130000Z")
    m["execution"].update(started_at="2026-11-19T13:00:00Z", finished_at="2026-11-19T13:05:00Z")
    m["execution"]["environment"] = {"python": "3.12", "gpu": "another synthetic gpu"}
    again = runs.write_run(tmp_path / "again", m, runs.records())
    assert all(r.ok for r in validate_runs([local, again]))
    assert protocol_fingerprint(load(local)) == protocol_fingerprint(load(again))


def test_validation_is_deterministic(local: Path, api: Path) -> None:
    rewrite_samples(local, lambda recs: recs[1].update(sample_id=recs[0]["sample_id"]), fix_sha=False)
    first = [[str(i) for i in r.issues] for r in validate_runs([local, api])]
    assert first == [[str(i) for i in r.issues] for r in validate_runs([local, api])]


def test_validation_does_not_modify_the_run(local: Path) -> None:
    before = {p.name: p.read_bytes() for p in local.iterdir()}
    validate_run(local)
    assert {p.name: p.read_bytes() for p in local.iterdir()} == before


def test_command_line_reports_the_three_levels(local: Path, api: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(local), str(api)]) == 0
    out = capsys.readouterr().out
    assert "structure: valid" in out and "provenance: complete" in out and "provenance: partial" in out
    assert "scientific verification: not checked" in out
    rewrite_samples(local, lambda recs: recs[0].update(raw_output="edited"), fix_sha=False)
    assert main([str(local), "--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["structurally_valid"] is False and report["issues"][0]["code"] == "checksum.mismatch"
    assert report["scientific_verification"].startswith("not checked")
