"""Documentation contract for benchmarks/: relative links resolve, and the docs stay in English."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DOCS = sorted([*ROOT.glob("*.md"), *ROOT.glob("docs/*.md")])
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
# Polish diacritics: documents in benchmarks/ are English-only (benchmarks/AGENTS.md). Proper nouns with diacritics
# need an explicit allowance here, in a reviewed change: a person's name is written as the person writes it.
POLISH = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")
PROPER_NOUNS = ("Wikieł",)  # docs/research-priorities.md: Kacper Wikieł


def relative_links(path: Path) -> list[str]:
    text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
    return [t for t in LINK.findall(text) if not re.match(r"[a-z]+:", t) and not t.startswith("#")]


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: str(p.relative_to(ROOT)))
def test_relative_links_resolve(doc: Path) -> None:
    missing = [t for t in relative_links(doc) if not (doc.parent / t.split("#")[0]).resolve().exists()]
    assert missing == []


def anchor(heading: str) -> str:
    """GitHub's heading anchor: lowercase, markup and punctuation dropped, spaces to hyphens."""
    text = re.sub(r"[`*_\[\]()]", "", heading.strip().lower())
    return "".join(c for c in text if c.isalnum() or c in " -").replace(" ", "-")


def anchors(path: Path) -> set[str]:
    text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
    return {anchor(m) for m in re.findall(r"(?m)^#{1,6} +(.+)$", text)}


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: str(p.relative_to(ROOT)))
def test_link_anchors_exist(doc: Path) -> None:
    text = re.sub(r"```.*?```", "", doc.read_text(encoding="utf-8"), flags=re.DOTALL)
    missing = []
    for target in LINK.findall(text):
        if re.match(r"[a-z]+:", target) or "#" not in target:
            continue
        path, fragment = target.split("#", 1)
        file = (doc.parent / path).resolve() if path else doc
        if file.suffix == ".md" and fragment not in anchors(file):
            missing.append(target)
    assert missing == []


def test_anchor_matches_github_for_headings_used_here() -> None:
    assert anchor("Getting started") == "getting-started"
    assert anchor("Methodology and reproducibility") == "methodology-and-reproducibility"
    assert anchor("`codesota` package") == "codesota-package"


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: str(p.relative_to(ROOT)))
def test_document_is_english(doc: Path) -> None:
    def polish(line: str) -> bool:
        for name in PROPER_NOUNS:
            line = line.replace(name, "")
        return bool(POLISH.search(line))

    lines = [i for i, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1) if polish(line)]
    assert lines == []


def test_docs_exist_and_stay_inside_the_repository() -> None:
    assert {p.name for p in DOCS} >= {"README.md", "AGENTS.md", "contributing.md", "security-and-governance.md"}
    for doc in DOCS:
        for target in relative_links(doc):
            assert (doc.parent / target.split("#")[0]).resolve().is_relative_to(REPO)
