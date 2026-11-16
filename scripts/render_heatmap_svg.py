"""Render data/contributions.json as the contribution heatmap (assets/contrib-heatmap.svg).

`./contributions.sh` is typed, the year's total rolls up like an odometer, and
53 weeks x 7 days of boxes drop in along the diagonal. Once, then it freezes.
STATIC=1 writes the final frame only.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

from _svg import (BODY_Y, EASE, FG, MUTED, PAD, RAMP, SPLINE, STATIC, SUB, W, delay, fr_date, fr_number, panel,
                  prompt, svg_doc)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "assets" / "contrib-heatmap.svg"

MONTHS = ["Janv", "Févr", "Mars", "Avr", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"]

LABEL_W = 32
GAP = 3
STEP = 0.022  # delay between two diagonals (s)
DROP = 0.4  # duration of one box's drop-in (s)

TOTAL_FONT = 28
TOTAL_Y = BODY_Y + 32  # baseline of the big figure
LINE_H = 32  # one odometer step


def level_of(day: dict, top: int) -> int:
    if day["level"] >= 4 and top and day["count"] >= 0.85 * top:
        return 5
    return day["level"]


def odometer(text: str, x: float, begin: float) -> tuple[str, float]:
    """The total as digit wheels that roll up to their value. Returns (markup, end x)."""
    adv = TOTAL_FONT * 0.6
    attrs = f'font-size="{TOTAL_FONT}" fill="{FG}" text-anchor="middle"'
    out, wheel = [], 0
    for ch in text:
        if not ch.isdigit():  # thousands separator
            x += adv * 0.35
            continue
        cx = x + adv / 2
        if STATIC:
            out.append(f'<text x="{cx:.1f}" y="{TOTAL_Y}" {attrs}>{ch}</text>')
        else:
            # Wheels further right spin longer, like a counter catching up.
            seq = [j % 10 for j in range(min(wheel, 2) * 10 + int(ch) + 1)]
            digits = "".join(f'<tspan x="{cx:.1f}" y="{TOTAL_Y + j * LINE_H}">{d}</tspan>' for j, d in enumerate(seq))
            travel = (len(seq) - 1) * LINE_H
            out.append(
                f'<clipPath id="o{wheel}"><rect x="{x - 1:.1f}" y="{TOTAL_Y - 25}" width="{adv + 2:.1f}" height="{LINE_H}"/></clipPath>'
                f'<g clip-path="url(#o{wheel})"><text {attrs}>{digits}'
                f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -{travel}" '
                f'keyTimes="0;1" calcMode="spline" keySplines="{SPLINE}" begin="{begin + wheel * 0.12:.2f}s" '
                f'dur="{1.1 + wheel * 0.15:.2f}s" fill="freeze"/></text></g>'
            )
        wheel += 1
        x += adv
    return "".join(out), x


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    days, stats = data["days"], data["stats"]

    first = date.fromisoformat(days[0]["date"])
    start = first - timedelta(days=(first.weekday() + 1) % 7)  # Sunday of first week
    last = date.fromisoformat(days[-1]["date"])
    ncols = (last - start).days // 7 + 1

    pitch = (W - 2 * PAD - LABEL_W) / ncols
    cell = round(pitch - GAP, 2)
    gx = PAD + LABEL_W
    gy = TOTAL_Y + 44
    top = max(d["count"] for d in days)

    head, typed = prompt("./contributions.sh", f"{ncols} semaines · à jour le {fr_date(days[-1]['date'])}")

    # --- header: total + legend ----------------------------------------------
    wheels, x = odometer(fr_number(stats["total"]), PAD, typed)
    header = [
        wheels,
        f'<text{delay(typed)} x="{x + 12:.1f}" y="{TOTAL_Y}" font-size="14" fill="{SUB}">contributions sur un an</text>',
    ]
    lx = W - PAD - 6 * (cell + 4) - 36
    legend = [f'<text x="{lx - 8}" y="{TOTAL_Y}" font-size="12" fill="{MUTED}" text-anchor="end">Moins</text>']
    for i, color in enumerate(RAMP):
        legend.append(
            f'<rect x="{lx + i * (cell + 4):.2f}" y="{TOTAL_Y - cell + 1:.2f}" width="{cell}" height="{cell}" rx="2.5" fill="{color}"/>'
        )
    legend.append(f'<text x="{lx + 6 * (cell + 4) + 4:.2f}" y="{TOTAL_Y}" font-size="12" fill="{MUTED}">Plus</text>')
    header.append(f'<g{delay(typed)}>{"".join(legend)}</g>')

    # --- month / weekday labels ----------------------------------------------
    labels = []
    prev_month, last_label_col = None, -99
    for col in range(ncols):
        d = start + timedelta(weeks=col)
        if d < first:
            d = first
        if d.month != prev_month:
            prev_month = d.month
            if col - last_label_col >= 3 and col <= ncols - 3:
                labels.append(
                    f'<text x="{gx + col * pitch:.2f}" y="{gy - 8}" font-size="12" fill="{MUTED}">{MONTHS[d.month - 1]}</text>'
                )
                last_label_col = col
    for row, name in ((1, "Lun"), (3, "Mer"), (5, "Ven")):
        labels.append(
            f'<text x="{PAD}" y="{gy + row * pitch + cell - 2:.2f}" font-size="12" fill="{MUTED}">{name}</text>'
        )

    # --- grid ---------------------------------------------------------------
    cells = []
    for d in days:
        offset = (date.fromisoformat(d["date"]) - start).days
        col, row = divmod(offset, 7)
        n = d["count"]
        tip = f"{n} contribution{'s' if n != 1 else ''} le {fr_date(d['date'])}"
        cells.append(
            f'<rect class="c d{col + row}" x="{gx + col * pitch:.2f}" y="{gy + row * pitch:.2f}" width="{cell}" '
            f'height="{cell}" rx="2.5" fill="{RAMP[level_of(d, top)]}"><title>{escape(tip)}</title></rect>'
        )
    height = round(gy + 7 * pitch - GAP + PAD)

    style = ""
    if not STATIC:
        style = (
            "@keyframes drop{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:none}}"
            f".c{{animation:drop {DROP}s {EASE} both}}"
            + "".join(f".d{i}{{animation-delay:{typed + i * STEP:.3f}s}}" for i in range(ncols + 6))
        )

    body = panel(height) + head + "".join(header) + f'<g{delay(typed)}>{"".join(labels)}</g>' + "".join(cells)
    label = f"{stats['total']} contributions GitHub au cours de la dernière année"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg_doc(W, height, body, style, label), encoding="utf-8")
    print(f"{ncols} weeks, {len(days)} days, {W}x{height} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
