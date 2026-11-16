"""Contact buttons (assets/link-*.svg): one line icon, one label, same height.

The portfolio is the primary action (accent fill, readable on GitHub's dark and light themes); the others sit on the raised surface.
Icons are lucide paths, 16 px, stroke 1.5. Stdlib only.
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from _svg import ACCENT, BG, FG, FONT, LINE, RAISED, SUB

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

ICONS = {
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "linkedin": '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/>'
                '<rect width="4" height="12" x="2" y="9"/><circle cx="4" cy="4" r="2"/>',
    "mail": '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
}
LINKS = [  # (file, icon, label, primary)
    ("portfolio", "globe", "lucaslabonde.com", True),
    ("linkedin", "linkedin", "LinkedIn", False),
    ("email", "mail", "Email", False),
]

H = 40
SIDE = 16
ICON = 16
GAP = 8
FONT_SIZE = 13


def button(icon: str, label: str, primary: bool) -> str:
    tw = len(label) * FONT_SIZE * 0.6
    w = round(SIDE + ICON + GAP + tw + SIDE)
    fill, ink, icon_ink, stroke = (ACCENT, BG, BG, ACCENT) if primary else (RAISED, FG, SUB, LINE)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{H}" viewBox="0 0 {w} {H}" '
        f'font-family="{FONT}" role="img" aria-label="{escape(label)}">'
        f'<rect x=".5" y=".5" width="{w - 1}" height="{H - 1}" rx="8" fill="{fill}" stroke="{stroke}"/>'
        f'<g transform="translate({SIDE} {(H - ICON) / 2:g}) scale({ICON / 24:.4f})" fill="none" stroke="{icon_ink}" '
        f'stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round">{ICONS[icon]}</g>'
        f'<text x="{SIDE + ICON + GAP}" y="{H / 2 + 4.5:g}" font-size="{FONT_SIZE}" fill="{ink}" '
        f'textLength="{tw:.1f}" lengthAdjust="spacing">{escape(label)}</text></svg>\n'
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, icon, label, primary in LINKS:
        path = OUT / f"link-{name}.svg"
        path.write_text(button(icon, label, primary), encoding="utf-8")
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
