"""Fetch the pinned repositories from the public GitHub API into data/repos.json.

Stdlib only. Uses GITHUB_TOKEN when the workflow provides one (higher rate limit),
and works without it.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

USERNAME = os.environ.get("GH_USERNAME", "Endikk")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "repos.json"

# The four cards of the README, in order. Change this list to feature other repos
# (and the matching <a>/<img> pairs in README.md).
PINNED = ["Claudy", "Claudio", "EVAN", "VroumVroum-r3f"]


def fetch_all(user: str) -> list[dict]:
    headers = {"User-Agent": "profile-art-bot", "Accept": "application/vnd.github+json"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    repos, page = [], 1
    while True:
        req = urllib.request.Request(
            f"https://api.github.com/users/{user}/repos?per_page=100&page={page}", headers=headers
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            batch = json.load(resp)
        repos += batch
        if len(batch) < 100:
            return repos
        page += 1


def main() -> int:
    repos = {r["name"]: r for r in fetch_all(USERNAME)}
    missing = [name for name in PINNED if name not in repos]
    if missing:
        print(f"Pinned repos not found (renamed or private?): {', '.join(missing)}", file=sys.stderr)
        return 1
    payload = {
        "username": USERNAME,
        "public_repos": len(repos),
        "repos": [
            {
                "name": r["name"],
                "description": r["description"] or "",
                "language": r["language"] or "",
                "stars": r["stargazers_count"],
                "pushed": r["pushed_at"][:10],
                "url": r["html_url"],
            }
            for r in (repos[name] for name in PINNED)
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{USERNAME}: {len(repos)} public repos, {len(PINNED)} pinned -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
