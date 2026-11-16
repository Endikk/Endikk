"""Render data/repos.json as one card per pinned repository (assets/project-<name>.svg).

The README lays them out two per row, each image at 50 % with no space between them, so the
gutter lives inside the SVG: left cards are padded on the right, right cards on the left.
Cards rise in one after the other. STATIC=1 writes the final frame only. Stdlib only.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from _svg import FG, MONTHS_SHORT, MUTED, PAD, SUB, delay, fr_date, fr_number, panel, svg_doc

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "repos.json"
OUT = ROOT / "assets"

# Used only while a repo has no description on GitHub (its "About" field wins as soon as it has one).
TAGLINES = {
    "Claudy": "Tes vrais quotas Claude, sur ton bureau macOS",
    "Claudio": "Tes vrais quotas Claude, sur ton bureau Windows",
}
# GitHub's language colours: a dot is the only place a card takes a hue.
LANG = {"C#": "#178600", "Swift": "#f05138", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
        "Python": "#3572a5", "Shell": "#89e051", "Ruby": "#701516"}

CARD_W, CARD_H = 422, 136
GUTTER = 16  # between two cards and between two rows
VIEW_W = CARD_W + GUTTER / 2
WRAP = 52  # characters per description line at 12 px
STAR = ("M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.12 2.12 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 "
        ".294.904l-3.736 3.638a2.12 2.12 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.12 "
        "2.12 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.12 2.12 0 0 0-.611-1.879L2.16 "
        "9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.12 2.12 0 0 0 1.597-1.16z")
ARROW = '<path d="M7 7h10v10"/><path d="M7 17 17 7"/>'


def pushed(iso: str, this_year: str) -> str:
    if iso[:4] == this_year:
        return fr_date(iso)
    return f"{MONTHS_SHORT[int(iso[5:7]) - 1]} {iso[:4]}"


def icon(paths: str, x: float, y: float, size: int = 14) -> str:
    return (f'<g transform="translate({x:g} {y:g}) scale({size / 24:.4f})" fill="none" stroke="{MUTED}" '
            f'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">{paths}</g>')


def card(repo: dict, index: int, this_year: str) -> str:
    x0 = 0 if index % 2 == 0 else GUTTER / 2
    lines = textwrap.wrap(repo["description"] or TAGLINES.get(repo["name"], ""), WRAP)
    if len(lines) > 2:
        lines = lines[:2]
        lines[1] = lines[1][: WRAP - 1].rstrip(" ,.:;") + "…"

    body = [
        panel(CARD_H, CARD_W),
        f'<text x="{PAD}" y="36" font-size="13"><tspan fill="{MUTED}">~/projets/</tspan>'
        f'<tspan font-size="15" font-weight="600" fill="{FG}">{escape(repo["name"])}</tspan></text>',
        icon(ARROW, CARD_W - PAD - 14, 24),
    ]
    for i, text in enumerate(lines):
        body.append(f'<text x="{PAD}" y="{62 + i * 18}" font-size="12" fill="{SUB}">{escape(text)}</text>')

    my = CARD_H - PAD + 2  # meta baseline
    x = PAD
    if repo["language"]:
        body.append(f'<circle cx="{x + 4}" cy="{my - 4}" r="4" fill="{LANG.get(repo["language"], MUTED)}"/>'
                    f'<text x="{x + 16}" y="{my}" font-size="12" fill="{SUB}">{escape(repo["language"])}</text>')
        x += 16 + len(repo["language"]) * 7.2 + 20
    if repo["stars"]:
        body.append(icon(f'<path d="{STAR}"/>', x, my - 11.5)
                    + f'<text x="{x + 20}" y="{my}" font-size="12" fill="{SUB}">{fr_number(repo["stars"])}</text>')
    body.append(f'<text x="{CARD_W - PAD}" y="{my}" font-size="12" fill="{MUTED}" text-anchor="end">'
                f'actif le {pushed(repo["pushed"], this_year)}</text>')

    inner = f'<g transform="translate({x0:g} 0)"><g{delay(0.15 + index * 0.08)}>{"".join(body)}</g></g>'
    label = f'{repo["name"]} — {" ".join(lines)}' if lines else repo["name"]
    return svg_doc(VIEW_W, CARD_H + GUTTER, inner, label=label)


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    this_year = max(r["pushed"] for r in data["repos"])[:4]
    OUT.mkdir(parents=True, exist_ok=True)
    for i, repo in enumerate(data["repos"]):
        path = OUT / f"project-{repo['name'].lower()}.svg"
        path.write_text(card(repo, i, this_year), encoding="utf-8")
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
