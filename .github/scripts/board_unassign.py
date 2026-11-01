"""Remove assignees from issues moved to Review or Independent Check on the project board.

Board field changes do not trigger GitHub Actions, so the workflow runs this script on a schedule.
For every issue whose Status is Review or Independent Check, an assignee is removed only when their
latest assignment happened before the Status change. A reviewer who assigns themselves after the
move stays assigned.

Token: PROJECT_TOKEN (or GH_TOKEN locally) with project + repo scopes. Without a token the script
prints a message and exits with 0.

Usage: python board_unassign.py [--dry-run] [--org slayerlabs] [--project 10]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime

API = "https://api.github.com"
TARGET_STATUSES = frozenset({"Review", "Independent Check"})

QUERY = """
query($org: String!, $number: Int!, $after: String) {
  organization(login: $org) {
    projectV2(number: $number) {
      items(first: 50, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          fieldValueByName(name: "Status") {
            ... on ProjectV2ItemFieldSingleSelectValue { name updatedAt }
          }
          content {
            ... on Issue {
              number
              url
              repository { nameWithOwner }
              assignees(first: 20) { nodes { login } }
              timelineItems(itemTypes: [ASSIGNED_EVENT], last: 100) {
                nodes {
                  ... on AssignedEvent {
                    createdAt
                    assignee { ... on User { login } ... on Bot { login } ... on Mannequin { login } }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""


def _ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def assignees_to_remove(status, status_updated_at, assignees, assigned_events):
    """Return the sorted logins to unassign.

    status: Status option name; status_updated_at: ISO time of the last Status change;
    assignees: current logins; assigned_events: iterable of (login, ISO createdAt) in any order.
    An assignee without any assignment event is treated as assigned before the change.
    """
    if status not in TARGET_STATUSES or not status_updated_at:
        return []
    changed = _ts(status_updated_at)
    last_assigned = {}
    for login, created_at in assigned_events:
        t = _ts(created_at)
        if login not in last_assigned or t > last_assigned[login]:
            last_assigned[login] = t
    return sorted(
        login for login in set(assignees)
        if login not in last_assigned or last_assigned[login] < changed
    )


def _request(token, method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "board-unassign",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read() or b"null")


def fetch_items(token, org, number):
    after = None
    while True:
        payload = _request(token, "POST", f"{API}/graphql",
                           {"query": QUERY, "variables": {"org": org, "number": number, "after": after}})
        if payload.get("errors"):
            raise RuntimeError(json.dumps(payload["errors"]))
        items = payload["data"]["organization"]["projectV2"]["items"]
        yield from items["nodes"]
        if not items["pageInfo"]["hasNextPage"]:
            return
        after = items["pageInfo"]["endCursor"]


def plan(items):
    """Turn raw project items into (repo, issue number, url, status, logins) to unassign."""
    for item in items:
        issue = item.get("content") or {}
        field = item.get("fieldValueByName") or {}
        if "number" not in issue:
            continue
        events = [
            (n["assignee"]["login"], n["createdAt"])
            for n in issue["timelineItems"]["nodes"]
            if n and n.get("assignee") and n["assignee"].get("login")
        ]
        logins = assignees_to_remove(
            field.get("name"), field.get("updatedAt"),
            [a["login"] for a in issue["assignees"]["nodes"]], events,
        )
        if logins:
            yield issue["repository"]["nameWithOwner"], issue["number"], issue["url"], field["name"], logins


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="only print what would be unassigned")
    parser.add_argument("--org", default="slayerlabs")
    parser.add_argument("--project", type=int, default=10)
    args = parser.parse_args(argv)

    token = os.environ.get("PROJECT_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("PROJECT_TOKEN is not set: skipping (add a PAT with project + repo scopes as a repo secret).")
        return 0

    count = 0
    for repo, number, url, status, logins in plan(fetch_items(token, args.org, args.project)):
        count += 1
        prefix = "[dry-run] would unassign" if args.dry_run else "unassign"
        print(f"{prefix} {', '.join(logins)} from {url} ({status})")
        if not args.dry_run:
            _request(token, "DELETE", f"{API}/repos/{repo}/issues/{number}/assignees", {"assignees": logins})
    print(f"issues to change: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
