"""Vocabulary of a CodeSOTA run: what a run manifest and its per-sample records may contain.

The aggregated results reuse the repository's existing contract, `urn:fabryka-ai:benchmark-results:2`
(`research/common/README.md`): every entry of a manifest's `observations` is an observation of that schema, with the
same required fields, units and states as `research/common/metryki.py` writes and checks. The manifest adds what an
observation does not carry: who ran what, how, on which data, scored by what, and which files hold the evidence.
"""

from typing import Final

MANIFEST_FORMAT: Final = "urn:codesota:run-manifest:1"
RESULTS_SCHEMA: Final = "urn:fabryka-ai:benchmark-results:2"

# Observation fields and states: identical to WYMAGANE_OBS and STANY in research/common/metryki.py.
OBSERVATION_FIELDS: Final = (
    "task_id",
    "model_id",
    "protocol_id",
    "metric",
    "unit",
    "higher_is_better",
    "n_population",
    "n_selected",
    "n_scored",
    "state",
    "value",
    "ci95",
    "source_id_digest",
    "results_sha256",
    "runner_sha256",
    "contamination",
    "contamination_receipt_sha256",
)
OBSERVATION_OPTIONAL_FIELDS: Final = frozenset({"reference", "reason"})
STATES: Final = frozenset(
    {
        "ok",
        "not_run",
        "blocked_access",
        "blocked_runtime",
        "blocked_security",
        "blocked_judge",
        "unsupported",
        "failed",
        "skipped",
    }
)
# Units of schema 2: `percent` is 0-100, `score` is a fraction (0-1 for accuracies), `byte_ppl` a perplexity.
UNITS: Final = frozenset({"percent", "score", "byte_ppl"})

# What a run claims to be. Only `verified` requires complete provenance; the others say why they are not.
CLAIMS: Final = frozenset({"verified", "unverified", "exploratory"})
# `primary`: the benchmark as defined. `exploratory`: a post-hoc analysis (a filtered subset, a corrected scorer)
# derived from another run; it never replaces that run's result.
ANALYSIS_KINDS: Final = frozenset({"primary", "exploratory"})
# How a metric's value follows from the per-sample scores. `mean`: mean of one number per scored sample.
# `micro_mean`: mean over all elements of a list per scored sample (for example per-instruction results).
# `external`: computed by the scorer in a way this package does not recompute; recorded, never checked.
AGGREGATIONS: Final = frozenset({"mean", "micro_mean", "external"})
# Accuracy-like results and resource measurements (tokens, latency, throughput, cost) are different metrics.
METRIC_KINDS: Final = frozenset({"quality", "efficiency"})
ARTIFACT_ROLES: Final = frozenset({"samples", "config", "log", "other"})
OUTPUT_PUBLICATION: Final = frozenset({"included", "withheld"})

# Fields that must be known (not an explicit unknown) for a run that claims to be `verified`.
VERIFIED_REQUIRES_KNOWN: Final = (
    ("model", "repo"),
    ("model", "revision"),
    ("protocol", "dataset", "repo"),
    ("protocol", "dataset", "revision"),
    ("protocol", "scorer", "version"),
    ("inference", "backend", "version"),
    ("execution", "source_commit"),
)
