"""Run manifests and their validation: the evidence behind a CodeSOTA result.

See `benchmarks/docs/result-artifacts.md` for the format and `python -m codesota.results --help` for the command.
"""

from codesota.results.validate import (
    Issue,
    Report,
    observation_issues,
    protocol_fingerprint,
    sha256_file,
    source_id_digest,
    validate_run,
    validate_runs,
)

__all__ = [
    "Issue",
    "Report",
    "observation_issues",
    "protocol_fingerprint",
    "sha256_file",
    "source_id_digest",
    "validate_run",
    "validate_runs",
]
