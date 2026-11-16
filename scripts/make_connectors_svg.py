"""Connectors between the panes (assets/flow-*.svg): the page reads as one git graph.

A green trunk runs down the middle. Where the layout splits into two columns it forks into
a blue and a violet branch that land on the centre of each column, and it merges back to
green before the next full-width pane. A dot of light travels down every line.
Static assets: run once, or again when the layout changes. Stdlib only.
"""

from __future__ import annotations

from pathlib import Path

from _svg import ACCENT, BG, FONT, MUTED, STATIC, W

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

BLUE, VIOLET = "#58a6ff", "#bc8cff"
MID = W / 2
H = 64
NODE = 16  # distance between the commit dot and the trunk's end
FLOW = 2.6  # s for the light to travel one connector

# Column centres of the two-column rows (see render_projects_svg.py and render_dashboard_svg.py).
PROJECTS = (211, 649)
STATS = (280, 718)


def doc(height: int, body: str, defs: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" '
        f'font-family="{FONT}" fill="none" stroke-width="2" stroke-linecap="round" aria-hidden="true">'
        f"<defs>{defs}</defs>{body}</svg>\n"
    )


def light(path: str, color: str, begin: float = 0) -> str:
    """A dot that runs along `path`, fading in and out, forever."""
    if STATIC:
        return ""
    return (
        f'<circle r="3" fill="{color}" opacity="0">'
        f'<animateMotion path="{path}" dur="{FLOW}s" begin="{begin}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.15;.8;1" dur="{FLOW}s" '
        f'begin="{begin}s" repeatCount="indefinite"/></circle>'
    )


def node(y: float) -> str:
    return f'<circle cx="{MID}" cy="{y}" r="4.5" fill="{BG}" stroke="{ACCENT}"/>'


def gradient(uid: str, x: float, color: str) -> str:
    """Green at the trunk, the branch colour at its column."""
    return (f'<linearGradient id="{uid}" gradientUnits="userSpaceOnUse" x1="{MID}" y1="0" x2="{x}" y2="0">'
            f'<stop offset="0" stop-color="{ACCENT}"/><stop offset="1" stop-color="{color}"/></linearGradient>')


def trunk(height: int = 32) -> str:
    path = f"M{MID} 2V{height - 2}"
    return doc(height, f'<path d="{path}" stroke="{ACCENT}"/>' + light(path, "#aff5c0"))


def fork(columns: tuple[int, int], label: str) -> str:
    body = [f'<path d="M{MID} 2V{NODE}" stroke="{ACCENT}"/>']
    defs = []
    for i, (x, color) in enumerate(zip(columns, (BLUE, VIOLET))):
        curve = f"C{MID} {NODE + 30} {x} {NODE + 6} {x} {H - 2}"
        defs.append(gradient(f"g{i}", x, color))
        body.append(f'<path d="M{MID} {NODE}{curve}" stroke="url(#g{i})"/>')
        body.append(light(f"M{MID} 2V{NODE}{curve}", color, i * 0.3))
    body.append(node(NODE))
    body.append(f'<text x="{MID + 16}" y="{NODE + 4}" font-size="12" fill="{MUTED}" stroke="none">{label}</text>')
    return doc(H, "".join(body), "".join(defs))


def merge(columns: tuple[int, int]) -> str:
    y = H - NODE
    body, defs = [], []
    for i, (x, color) in enumerate(zip(columns, (BLUE, VIOLET))):
        curve = f"M{x} 2C{x} {y - 6} {MID} {y - 30} {MID} {y}"
        defs.append(gradient(f"g{i}", x, color))
        body.append(f'<path d="{curve}" stroke="url(#g{i})"/>')
        body.append(light(f"{curve}V{H - 2}", color, i * 0.3))
    body.append(f'<path d="M{MID} {y}V{H - 2}" stroke="{ACCENT}"/>')
    body.append(node(y))
    return doc(H, "".join(body), "".join(defs))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "flow-trunk": trunk(),
        "flow-fork-projects": fork(PROJECTS, "git checkout projets"),
        "flow-merge-projects": merge(PROJECTS),
        "flow-fork-stats": fork(STATS, "git checkout stats"),
        "flow-merge-stats": merge(STATS),
    }
    for name, svg in files.items():
        (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
        print(f"assets/{name}.svg")


if __name__ == "__main__":
    main()
