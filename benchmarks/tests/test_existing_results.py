"""The observation checks accept the repository's existing schema-2 results, which they must not change.

Read-only: every `results.json` written by the research pipeline under research/results/central-run/ is parsed,
and each observation must pass `observation_issues`. The files' bytes are compared before and after.
"""

import json
from pathlib import Path

import pytest

from codesota.results import observation_issues, schema

REPO = Path(__file__).resolve().parents[2]
CENTRAL_RUN = REPO / "research" / "results" / "central-run"
RESULTS = sorted(CENTRAL_RUN.glob("*/*/results.json"))

pytestmark = pytest.mark.skipif(not RESULTS, reason="research/ results are not in this checkout")


@pytest.mark.parametrize("path", RESULTS, ids=lambda p: str(p.relative_to(CENTRAL_RUN).parent))
def test_existing_observations_pass(path: Path) -> None:
    before = path.read_bytes()
    results = json.loads(before)
    assert results["schema_version"] == 2
    assert results["observations"]
    for obs in results["observations"]:
        assert [str(i) for i in observation_issues(obs)] == []
        assert set(obs) >= set(schema.OBSERVATION_FIELDS)
    assert path.read_bytes() == before
