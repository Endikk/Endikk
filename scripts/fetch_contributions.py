"""Scrape the public GitHub contribution calendar (no token) into data/contributions.json.

GitHub serves the calendar as an HTML fragment at /users/<user>/contributions:
one <td data-date data-level> per day, and a <tool-tip for="<td id>"> holding
the exact count ("9 contributions on February 8th.").

Stdlib only, so the daily workflow needs no pip install.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from collections import OrderedDict
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path

USERNAME = os.environ.get("GH_USERNAME", "Endikk")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"
COUNT_RE = re.compile(r"^\s*([\d,]+)\s+contributions?\b", re.I)


class CalendarParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cells: dict[str, dict] = {}  # td id -> {date, level}
        self.tooltips: dict[str, str] = {}  # td id -> tooltip text
        self._tip_for: str | None = None
        self._tip_text: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "td" and "ContributionCalendar-day" in (a.get("class") or "") and a.get("data-date"):
            self.cells[a.get("id") or a["data-date"]] = {
                "date": a["data-date"],
                "level": int(a.get("data-level") or 0),
            }
        elif tag == "tool-tip" and a.get("for"):
            self._tip_for, self._tip_text = a["for"], []

    def handle_data(self, data):
        if self._tip_for is not None:
            self._tip_text.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self._tip_for is not None:
            self.tooltips[self._tip_for] = "".join(self._tip_text).strip()
            self._tip_for = None


def fetch_html(user: str) -> str:
    req = urllib.request.Request(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "profile-art-bot (+https://github.com/%s)" % user},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_days(html: str) -> list[dict]:
    p = CalendarParser()
    p.feed(html)
    days = []
    for cell_id, cell in p.cells.items():
        m = COUNT_RE.match(p.tooltips.get(cell_id, ""))
        count = int(m.group(1).replace(",", "")) if m else 0
        days.append({"date": cell["date"], "count": count, "level": cell["level"]})
    days.sort(key=lambda d: d["date"])
    return days


def streaks(days: list[dict]) -> tuple[dict, dict]:
    """Current and longest runs of active days, each as {days, start, end}.

    Today with 0 contributions doesn't break the current streak yet.
    """
    longest = {"days": 0, "start": None, "end": None}
    run, start = 0, None
    for d in days:
        if d["count"] == 0:
            run = 0
            continue
        if run == 0:
            start = d["date"]
        run += 1
        if run > longest["days"]:
            longest = {"days": run, "start": start, "end": d["date"]}

    current = {"days": 0, "start": None, "end": None}
    tail = days[:-1] if days and days[-1]["count"] == 0 else days
    for d in reversed(tail):
        if d["count"] == 0:
            break
        current["days"] += 1
        current["start"] = d["date"]
        current["end"] = current["end"] or d["date"]
    return current, longest


def build_stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)
    active = [d for d in days if d["count"] > 0]
    best = max(days, key=lambda d: d["count"]) if days else None
    current, longest = streaks(days)

    months: "OrderedDict[str, int]" = OrderedDict()
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    best_month = max(months.items(), key=lambda kv: kv[1]) if months else None

    return {
        "total": total,
        "days": len(days),
        "active_days": len(active),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]} if best else None,
        "best_month": {"month": best_month[0], "count": best_month[1]} if best_month else None,
        "monthly": months,
    }


def main() -> int:
    days = parse_days(fetch_html(USERNAME))
    if len(days) < 300:
        print(f"Only {len(days)} days parsed - GitHub markup changed?", file=sys.stderr)
        return 1

    # Sanity: dates must be contiguous, otherwise the grid would be misaligned.
    first = date.fromisoformat(days[0]["date"])
    expected = [(first + timedelta(i)).isoformat() for i in range(len(days))]
    if [d["date"] for d in days] != expected:
        print("Non-contiguous calendar dates", file=sys.stderr)
        return 1

    # A colored cell without a count means the tooltips moved: fail rather than commit zeros.
    if any(d["level"] > 0 and d["count"] == 0 for d in days):
        print("Colored days without a count - tooltip markup changed?", file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {"username": USERNAME, "stats": build_stats(days), "days": days}
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    s = payload["stats"]
    print(f"{USERNAME}: {s['total']} contributions, {len(days)} days, "
          f"streak {s['current_streak']['days']} (best {s['longest_streak']['days']}) -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
