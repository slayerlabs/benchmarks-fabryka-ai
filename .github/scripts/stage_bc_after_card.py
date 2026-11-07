"""Open the stage B+C issue when an "Karta oryginału: <benchmark>" issue is closed as completed.

The workflow runs this on `issues: closed`. A card closed as "not planned" gives nothing. When an issue for
stage B+C of the same benchmark already exists (open or closed), nothing is created, so closing and reopening
a card never makes a duplicate. The new issue goes to the org project board with Status Ready.

Tokens: GITHUB_TOKEN (issues: write) for the repo; PROJECT_TOKEN (PAT with project scope) for the board. Without
PROJECT_TOKEN the issue is still created and the board step ends with a warning, not an error.

Usage: python stage_bc_after_card.py [--dry-run] [--event <path to event JSON>]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
CARD_PREFIX = "Karta oryginału: "
PROJECT_ID = "PVT_kwDOEWWqgM4Bplf8"
STATUS_FIELD_ID = "PVTSSF_lADOEWWqgM4Bplf8zhoAdYQ"
READY_OPTION_ID = "703eb7e4"
LABELS = ["research"]

BLOB = "https://github.com/{repo}/blob/main/"
CATALOG_RE = re.compile(r"research/benchmarks/([A-Za-z0-9][A-Za-z0-9._-]*)/ORIGINAL\.md")


def benchmark_name(card_title):
    """Benchmark name from a card title, or None when the title is not a card."""
    if not card_title or not card_title.startswith(CARD_PREFIX):
        return None
    name = card_title[len(CARD_PREFIX):].strip()
    return name or None


def stage_bc_title(name):
    return f"{name} nie jest podpięty do przebiegu centralnego"


def card_catalog(card_body):
    """The single benchmark directory named in the card as research/benchmarks/<dir>/ORIGINAL.md.

    Returns None when there is no such path or when the card names more than one directory.
    """
    found = {m for m in CATALOG_RE.findall(card_body or "") if m != "_template"}
    return found.pop() if len(found) == 1 else None


def files_decision(catalog, has_original, has_reproduction):
    """Return (create, catalog to link) from what is on main for the card's directory.

    REPRODUCTION.md on main means stage B is done, so nothing is created. ORIGINAL.md missing means the
    issue links only the card. Without a known directory the issue is created and links only the card.
    """
    if not catalog:
        return True, None
    if has_reproduction:
        return False, None
    return True, catalog if has_original else None


def marker(card_number):
    return f"<!-- stage-bc-card: #{card_number} -->"


def is_stage_bc_for(issue, name, card_number):
    """True when an existing issue is the stage B+C issue for this card.

    Matches the marker this script writes, a body that starts work after this card ("karty oryginału #N"),
    or a title that starts with the benchmark name followed by "nie" / "ma" (the convention of the
    hand-written B+C issues, e.g. "ARC-Challenge nie spełnia ...").
    """
    if issue.get("number") == card_number or "pull_request" in issue:
        return False
    title = issue.get("title") or ""
    body = issue.get("body") or ""
    if title.startswith(CARD_PREFIX):
        return False
    if marker(card_number) in body:
        return True
    if re.search(rf"karty oryginału #{card_number}(?!\d)", body, re.IGNORECASE):
        return True
    return re.match(rf"{re.escape(name)} (nie|ma) ", title) is not None


def decide(event, existing_issues):
    """Return (name, title) of the issue to create, or (None, reason) when nothing should be created."""
    issue = event.get("issue") or {}
    if event.get("action") != "closed":
        return None, "event is not issues.closed"
    name = benchmark_name(issue.get("title"))
    if name is None:
        return None, "closed issue is not a card"
    if issue.get("state_reason") != "completed":
        return None, f"card closed as {issue.get('state_reason')!r}, not completed"
    for other in existing_issues:
        if is_stage_bc_for(other, name, issue["number"]):
            return None, f"stage B+C issue already exists: #{other['number']}"
    return name, stage_bc_title(name)


def stage_bc_body(repo, name, card_number, catalog):
    """Fixed body: links to METODOLOGIA stages B and C, the card and, when known, its ORIGINAL.md."""
    blob = BLOB.format(repo=repo)
    met = blob + "research/METODOLOGIA.md"
    where = (
        f"w katalogu `research/benchmarks/{catalog}/`"
        if catalog
        else "w katalogu benchmarku z karty oryginału"
    )
    card_line = f"- Karta oryginału: #{card_number}"
    if catalog:
        card_line += f", plik [`research/benchmarks/{catalog}/ORIGINAL.md`]({blob}research/benchmarks/{catalog}/ORIGINAL.md)"
    card_line += ". Zbiór, wersję zadania, metrykę i wyniki referencyjne bierzesz z karty."
    return "\n".join([
        "## Cel",
        "",
        f"{name} jest opisany i podpięty do przebiegu centralnego, więc jedno uruchomienie przebiegu liczy go "
        "razem z resztą benchmarków na Slayerze i modelach odniesienia. Na GPU niczego nie liczysz.",
        "",
        "## Co zrobić",
        "",
        f"Etap B i C benchmarku według [„B. Odtworzenie wyniku oryginalnym kodem (REPRODUCTION.md)”]"
        f"({met}#b-odtworzenie-wyniku-oryginalnym-kodem-reproductionmd) z modelem z "
        f"[„Model kontrolny etapu B”]({met}#model-kontrolny-etapu-b) i [„C. Kod w repo”]({met}#c-kod-w-repo), "
        f"{where} ze [wzoru]({blob}research/benchmarks/_template/README.md). Wpis w `ZADANIA` "
        "(`research/common/zadania.py`) i w `KATALOGI` (`research/tools/przebieg_centralny.sh`).",
        "",
        "## Dane wejściowe",
        "",
        card_line,
        f"- Warunek odtworzenia i postępowanie, gdy nie jest spełniony: sekcja B "
        f"[METODOLOGII]({met}#b-odtworzenie-wyniku-oryginalnym-kodem-reproductionmd).",
        "",
        "## Gotowe, gdy",
        "",
        "- [ ] `REPRODUCTION.md` ma wartość referencyjną, model kontrolny i warunek odtworzenia albo „bez kontroli” "
        "z listą przeszukanych miejsc; werdykt wpisuje się po przebiegu centralnym.",
        "- [ ] Benchmark ma wpis w `ZADANIA` i `KATALOGI`, a test bez sieci i bez wag sprawdza ten wpis.",
        f"- [ ] Spełnia [„Definicja „zrobione””]({met}#definicja-zrobione); "
        f"[bramka liczb i testy]({blob}research/README.md#bramka-liczb) kończą się kodem 0.",
        f"- [ ] PR do `main` ma `Refs #N` z numerem tego zadania "
        f"([CONTRIBUTING, „PR”]({blob}CONTRIBUTING.md#pr)).",
        "",
        "Sprawdzenie: recenzja.",
        "",
        marker(card_number),
        "",
    ])


def _request(token, method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "stage-bc-after-card",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read() or b"null")


def list_issues(token, repo):
    page = 1
    while True:
        batch = _request(token, "GET", f"{API}/repos/{repo}/issues?state=all&per_page=100&page={page}")
        yield from batch
        if len(batch) < 100:
            return
        page += 1


def file_exists(token, repo, path):
    try:
        _request(token, "GET", f"{API}/repos/{repo}/contents/{urllib.parse.quote(path)}?ref=main")
        return True
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return False
        raise


def add_to_board(token, issue_node_id):
    def gql(query, variables):
        payload = _request(token, "POST", f"{API}/graphql", {"query": query, "variables": variables})
        if payload.get("errors"):
            raise RuntimeError(json.dumps(payload["errors"]))
        return payload["data"]

    item = gql(
        "mutation($p: ID!, $c: ID!) { addProjectV2ItemById(input: {projectId: $p, contentId: $c}) { item { id } } }",
        {"p": PROJECT_ID, "c": issue_node_id},
    )["addProjectV2ItemById"]["item"]["id"]
    gql(
        "mutation($p: ID!, $i: ID!, $f: ID!, $o: String!) { updateProjectV2ItemFieldValue(input: "
        "{projectId: $p, itemId: $i, fieldId: $f, value: {singleSelectOptionId: $o}}) { projectV2Item { id } } }",
        {"p": PROJECT_ID, "i": item, "f": STATUS_FIELD_ID, "o": READY_OPTION_ID},
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="only print what would be created")
    parser.add_argument("--event", default=os.environ.get("GITHUB_EVENT_PATH"))
    args = parser.parse_args(argv)

    with open(args.event, encoding="utf-8") as fh:
        event = json.load(fh)
    repo = event["repository"]["full_name"]
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("GITHUB_TOKEN is not set", file=sys.stderr)
        return 1

    name, result = decide(event, list(list_issues(token, repo)))
    if name is None:
        print(f"nothing to do: {result}")
        return 0

    card = event["issue"]
    catalog = card_catalog(card.get("body"))
    has = {}
    if catalog:
        for fname in ("REPRODUCTION.md", "ORIGINAL.md"):
            has[fname] = file_exists(token, repo, f"research/benchmarks/{catalog}/{fname}")
    create, catalog = files_decision(catalog, has.get("ORIGINAL.md", False), has.get("REPRODUCTION.md", False))
    if not create:
        print(f"nothing to do: research/benchmarks/{card_catalog(card.get('body'))}/REPRODUCTION.md is on main")
        return 0
    body = stage_bc_body(repo, name, card["number"], catalog)

    if args.dry_run:
        print(f"[dry-run] would create: {result}\n\n{body}")
        return 0

    created = _request(token, "POST", f"{API}/repos/{repo}/issues",
                       {"title": result, "body": body, "labels": LABELS})
    print(f"created #{created['number']}: {created['html_url']}")

    project_token = os.environ.get("PROJECT_TOKEN")
    if not project_token:
        print(f"::warning::PROJECT_TOKEN is not set: add {created['html_url']} to the board (Ready) by hand.")
        return 0
    try:
        add_to_board(project_token, created["node_id"])
    except (urllib.error.URLError, OSError, RuntimeError, KeyError, TypeError) as err:
        print(f"::error::board update failed, add {created['html_url']} to the board (Ready) by hand: {err}")
        return 1
    print("added to the board with Status Ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
