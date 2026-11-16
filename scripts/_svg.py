"""Shared look for the profile SVGs: one terminal pane per panel.

A pane is a hairline rectangle on GitHub's dark background. Its first line is the
command that produced it, typed once with a block cursor; the output follows.
One neutral ramp, one accent (the contribution green), one easing curve.
"""

import os
from xml.sax.saxutils import escape

FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', 'DejaVu Sans Mono', monospace"

BG = "#0d1117"  # GitHub dark page: the pane melts into it, only the hairline shows
RAISED = "#151b23"
LINE = "#232a33"  # hairline, ~ FG at 10 % on BG
FG = "#e6edf3"
SUB = "#9da7b3"
MUTED = "#7d8590"
ACCENT = "#39d353"
# Contribution levels: none -> brightest (level 5 marks the very best days).
RAMP = [RAISED, "#0e4429", "#006d32", "#26a641", ACCENT, "#69f0a0"]

EASE = "cubic-bezier(.22,1,.36,1)"
SPLINE = ".22 1 .36 1"  # the same curve, SMIL spelling

W = 860  # every pane, and the README column
PAD = 24
PROMPT_Y = 36  # baseline of a pane's first line
BODY_Y = 56  # where the output starts
ADV = 0.6  # monospace advance, in em
PROMPT_FONT = 13
USER = "lucas@endikk"
KEY = 0.055  # s per typed character

STATIC = os.environ.get("STATIC") == "1"

# Fade and rise, the only entrance: class "u" plus an inline animation-delay.
RISE = (
    "@keyframes u{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
    f".u{{animation:u .4s {EASE} both}}"
)


def panel(height: float, width: float = W) -> str:
    return f'<rect x=".5" y=".5" width="{width - 1:g}" height="{height - 1:g}" rx="12" fill="{BG}" stroke="{LINE}"/>'


def delay(t: float) -> str:
    return "" if STATIC else f' class="u" style="animation-delay:{t:.2f}s"'


def prompt(cmd: str, meta: str = "", y: float = PROMPT_Y, begin: float = 0.2, uid: str = "p",
           width: float = W) -> tuple[str, float]:
    """`lucas@endikk ~ $ cmd`, the command typed key by key. Returns (markup, time it ends).

    An empty `cmd` is an idle prompt: its cursor appears at `begin` and keeps blinking.
    textLength pins every width, so the cursor lands right in any monospace font.
    """
    cw = PROMPT_FONT * ADV
    head = f"{USER} ~ $ "
    x_cmd = PAD + len(head) * cw
    top, ch = y - PROMPT_FONT + 1, PROMPT_FONT + 3
    out = [
        f'<text x="{PAD}" y="{y}" font-size="{PROMPT_FONT}" textLength="{len(head.rstrip()) * cw:.1f}" '
        f'lengthAdjust="spacing"><tspan fill="{SUB}">{USER}</tspan><tspan fill="{MUTED}"> ~ $</tspan></text>'
    ]
    if meta:
        out.append(f'<text{delay(begin)} x="{width - PAD}" y="{y}" font-size="12" fill="{MUTED}" '
                   f'text-anchor="end">{escape(meta)}</text>')
    cursor = f'<rect y="{top:g}" width="{cw:.1f}" height="{ch}" fill="{ACCENT}"'

    if not cmd:  # idle: a live cursor is the one thing here allowed to loop
        if STATIC:
            return "".join(out) + f'{cursor} x="{x_cmd:.1f}"/>', begin
        out.append(
            f'{cursor} x="{x_cmd:.1f}" opacity="0"><animate attributeName="opacity" values="1;0" '
            f'calcMode="discrete" dur="1.1s" begin="{begin:.2f}s" repeatCount="indefinite"/></rect>'
        )
        return "".join(out), begin

    n = len(cmd)
    text = (f'<text x="{x_cmd:.1f}" y="{y}" font-size="{PROMPT_FONT}" fill="{FG}" '
            f'textLength="{n * cw:.1f}" lengthAdjust="spacing"')
    if STATIC:
        return "".join(out) + f"{text}>{escape(cmd)}</text>", begin
    dur = n * KEY
    widths = ";".join(f"{i * cw:.1f}" for i in range(n + 1))
    xs = ";".join(f"{x_cmd + i * cw:.1f}" for i in range(n + 1))
    out.append(
        f'<clipPath id="{uid}"><rect x="{x_cmd:.1f}" y="{top - 2:g}" width="0" height="{ch + 6}">'
        f'<animate attributeName="width" values="{widths}" calcMode="discrete" begin="{begin:.2f}s" '
        f'dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>'
        f'{text} clip-path="url(#{uid})">{escape(cmd)}</text>'
        f'{cursor} x="{x_cmd:.1f}">'
        f'<animate attributeName="x" values="{xs}" calcMode="discrete" begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0" begin="{begin + dur + 0.25:.2f}s"/></rect>'
    )
    return "".join(out), begin + dur + 0.25


def svg_doc(width: float, height: float, body: str, style: str = "", label: str = "") -> str:
    label = escape(label, {'"': "&quot;"})
    if not STATIC:
        style = RISE + style + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:g}" height="{height:g}" '
        f'viewBox="0 0 {width:g} {height:g}" font-family="{FONT}" role="img" aria-label="{label}">'
        f"<style>{style}</style>{body}</svg>\n"
    )


MONTHS_SHORT = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def fr_date(iso: str) -> str:
    """2026-09-29 -> '29 sept.'"""
    _, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {MONTHS_SHORT[m - 1]}"


def fr_number(n: float, decimals: int = 0) -> str:
    """French formatting: narrow no-break space for thousands, comma for decimals."""
    return f"{n:,.{decimals}f}".replace(",", " ").replace(".", ",")
