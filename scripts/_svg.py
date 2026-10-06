"""Shared look for the profile SVGs: one dark "terminal window" style."""

import re
from pathlib import Path
from xml.sax.saxutils import escape

FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', 'DejaVu Sans Mono', monospace"

BG = "#0d1117"
BAR = "#161b22"
BORDER = "#30363d"
FG = "#c9d1d9"
MUTED = "#8b949e"
GREEN = "#39d353"
BLUE = "#58a6ff"
DOTS = ("#ff5f56", "#ffbd2e", "#27c93f")

TITLE_H = 30


def window(width: float, height: float, title: str, scale: float = 1.0) -> str:
    """Rounded panel + macOS-style title bar. Content starts at y = TITLE_H * scale.

    `scale` > 1 enlarges the chrome for an SVG that the README displays smaller than its
    viewBox, so every window bar looks the same size on the profile.
    """
    w, h = width / scale, height / scale
    dots = "".join(
        f'<circle cx="{18 + i * 18}" cy="{TITLE_H / 2}" r="5.5" fill="{c}"/>' for i, c in enumerate(DOTS)
    )
    return (
        f'<g transform="scale({scale:g})">'
        f'<rect x="0.5" y="0.5" width="{w - 1:g}" height="{h - 1:g}" rx="10" fill="{BG}" stroke="{BORDER}"/>'
        f'<path d="M0.5 {TITLE_H}V10.5a10 10 0 0 1 10-10h{w - 21:g}a10 10 0 0 1 10 10V{TITLE_H}Z" fill="{BAR}"/>'
        f'<line x1="0.5" y1="{TITLE_H}" x2="{w - 0.5:g}" y2="{TITLE_H}" stroke="{BORDER}"/>'
        f"{dots}"
        f'<text x="{w / 2:g}" y="{TITLE_H / 2 + 4}" text-anchor="middle" font-size="12" fill="{MUTED}">{escape(title)}</text>'
        "</g>"
    )


def svg_doc(width: float, height: float, body: str, style: str = "", label: str = "") -> str:
    label = escape(label, {'"': "&quot;"})
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}" role="img" aria-label="{label}">'
        f"<style>{style}@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}</style>"
        f"{body}</svg>\n"
    )


MONTHS_SHORT = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def fr_date(iso: str) -> str:
    """2026-09-29 -> '29 sept.'"""
    _, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {MONTHS_SHORT[m - 1]}"


def fr_number(n: float, decimals: int = 0) -> str:
    """French formatting: narrow no-break space for thousands, comma for decimals."""
    return f"{n:,.{decimals}f}".replace(",", "\u202f").replace(".", ",")


def height_beside(portrait_svg: Path, portrait_display_w: float = 370) -> int:
    """On-screen height of the portrait in the README table, i.e. the viewBox height a
    panel shown at its own viewBox width needs to line up with it."""
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', portrait_svg.read_text(encoding="utf-8"))
    pw, ph = map(float, vb.groups())
    return round(portrait_display_w * ph / pw)
