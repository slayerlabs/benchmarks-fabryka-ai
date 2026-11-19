"""Compatibility with the repository's existing results contract (`urn:fabryka-ai:benchmark-results:2`).

This is a compatibility check against what is available locally, not validation against the contract's full JSON
Schema, which is not in this repository (`research/common/README.md` names it `results.schema.json`, kept in the
Space). Two things are checked, read-only:

- The observation vocabulary in `codesota.results.schema` equals the one research/common/metryki.py checks
  (`WYMAGANE_OBS`, `STANY`), read from its source without importing it.
- Every `results.json` written by the research pipeline under research/results/central-run/ passes
  `observation_issues`, and its bytes are unchanged afterwards.
"""

import ast
import json
from pathlib import Path

import pytest

from codesota.results import observation_issues, schema

REPO = Path(__file__).resolve().parents[2]
METRYKI = REPO / "research" / "common" / "metryki.py"
CENTRAL_RUN = REPO / "research" / "results" / "central-run"
RESULTS = sorted(CENTRAL_RUN.glob("*/*/results.json"))


def research_constant(name: str) -> object:
    """The literal value of a module-level constant in research/common/metryki.py."""
    for node in ast.parse(METRYKI.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} not found in {METRYKI}")


@pytest.mark.skipif(not METRYKI.is_file(), reason="research/ is not in this checkout")
def test_observation_vocabulary_matches_research_pipeline() -> None:
    assert research_constant("WYMAGANE_OBS") == list(schema.OBSERVATION_FIELDS)
    assert research_constant("STANY") == set(schema.STATES)


@pytest.mark.skipif(not RESULTS, reason="research/ results are not in this checkout")
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
