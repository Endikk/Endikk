"""Neofetch-style info card (assets/info-card.svg): the story the contribution graph can't tell.

Two columns under a user@host header, full README width. Each row fades and slides in
on a short stagger, as if printing. STATIC=1 writes the final frame only.
"""

from __future__ import annotations

import os
from pathlib import Path
from xml.sax.saxutils import escape

from _svg import BLUE, FG, GREEN, MUTED, TITLE_H, svg_doc, window

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

USER, HOST = "lucas", "endikk"
LEFT = [
    ("Rôle", "Développeur Full-Stack & Cloud"),
    ("Lieu", "Normandie, France"),
    ("Études", "Mastère Archi. des SI · CESI (Bac+5)"),
    ("Parcours", "5 ans d'alternance en grande entreprise"),
    ("Focus", "Archi logicielle · systèmes distribués"),
    ("", "Pipelines de données · IA"),
    ("Hors code", "Formule 1 · Basket · Veille tech"),
]
RIGHT = [
    ("Langages", "Python · C# · TypeScript · JavaScript"),
    ("Front/Back", "React · .NET"),
    ("Cloud", "GCP · Docker · GitLab CI"),
    ("Data", "PostgreSQL · MySQL · MongoDB"),
    ("Outils", "Git · Figma"),
    ("Contact", "labondepro@gmail.com"),
    ("Web", "lucaslabonde.com"),
]
COLORS = ["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#b1bac4"]

W = 860  # same width as the heatmap
PAD = 24
COL2 = 440  # x of the right column
KEY_W = 96
FONT = 13
STEP = 22  # line height
STAGGER = 0.12  # s between two rows
START = 0.25


def value_markup(value: str) -> str:
    sep = f'<tspan fill="{MUTED}"> · </tspan>'
    return sep.join(escape(part) for part in value.split(" · "))


def pair(x: float, key: str, value: str) -> str:
    key_markup = f'<tspan x="{x}" fill="{GREEN}" font-weight="700">{escape(key)}</tspan>' if key else ""
    return f'{key_markup}<tspan x="{x + KEY_W}" fill="{FG}">{value_markup(value)}</tspan>'


def main() -> None:
    y = TITLE_H + 30
    rows = [
        f'<tspan font-weight="700"><tspan fill="{GREEN}">{USER}</tspan><tspan fill="{FG}">@</tspan>'
        f'<tspan fill="{BLUE}">{HOST}</tspan></tspan>',
        f'<tspan fill="{MUTED}">{"-" * len(USER + "@" + HOST)}</tspan>',
    ]
    rows += [pair(PAD, *left) + pair(COL2, *right) for left, right in zip(LEFT, RIGHT)]

    body = []
    for i, row in enumerate(rows):
        body.append(
            f'<g class="l" style="animation-delay:{START + i * STAGGER:.2f}s">'
            f'<text x="{PAD}" y="{y + i * STEP}">{row}</text></g>'
        )
    by = y + len(rows) * STEP - 6
    blocks = "".join(
        f'<rect x="{PAD + i * 26}" y="{by}" width="22" height="14" rx="2" fill="{c}"/>' for i, c in enumerate(COLORS)
    )
    body.append(f'<g class="l" style="animation-delay:{START + len(rows) * STAGGER:.2f}s">{blocks}</g>')
    height = by + 14 + 20

    style = f"text{{font-size:{FONT}px}}"
    if not STATIC:
        style += (
            "@keyframes print{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
            ".l{animation:print .35s ease-out both}"
        )
    else:
        body = [b.replace(' class="l"', "") for b in body]

    body.insert(0, window(W, height, f"{USER}@github: ~ — neofetch"))
    label = f"{USER}@{HOST} — " + " / ".join(f"{k}: {v}" for k, v in LEFT + RIGHT if k)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg_doc(W, height, "".join(body), style, label), encoding="utf-8")
    print(f"{len(rows)} rows, {W}x{height} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
