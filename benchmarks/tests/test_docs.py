"""Documentation contract for benchmarks/: relative links resolve, and v2 docs stay in English."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DOCS = sorted([*ROOT.glob("*.md"), *ROOT.glob("docs/*.md")])
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
# Polish diacritics: v2 documents are English-only (benchmarks/AGENTS.md). Proper nouns with diacritics would need
# an explicit allowance here, in a reviewed change.
POLISH = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")


def relative_links(path: Path) -> list[str]:
    text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
    return [t for t in LINK.findall(text) if not re.match(r"[a-z]+:", t) and not t.startswith("#")]


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: str(p.relative_to(ROOT)))
def test_relative_links_resolve(doc: Path) -> None:
    missing = [t for t in relative_links(doc) if not (doc.parent / t.split("#")[0]).resolve().exists()]
    assert missing == []


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: str(p.relative_to(ROOT)))
def test_document_is_english(doc: Path) -> None:
    lines = [i for i, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1) if POLISH.search(line)]
    assert lines == []


def test_docs_exist_and_stay_inside_the_repository() -> None:
    assert {p.name for p in DOCS} >= {"README.md", "AGENTS.md", "contributing.md", "security-and-governance.md"}
    for doc in DOCS:
        for target in relative_links(doc):
            assert (doc.parent / target.split("#")[0]).resolve().is_relative_to(REPO)
