"""Render data/contributions.json as an animated contribution heatmap (assets/contrib-heatmap.svg).

53 weeks x 7 days of rounded boxes that drop in along the diagonal once, then freeze.
"""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

from _svg import FG, GREEN, MUTED, TITLE_H, fr_date, fr_number, svg_doc, window

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "assets" / "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#          none -> brightest (level 5 is a neon top end for the very best days)

MONTHS = ["Janv", "Févr", "Mars", "Avr", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"]

W = 860
PAD = 24
LABEL_W = 34
GAP = 3
STEP = 0.028  # delay between two diagonals (s)
DROP = 0.45  # duration of one box's drop-in (s)


def level_of(day: dict, top: int) -> int:
    if day["level"] >= 4 and top and day["count"] >= 0.85 * top:
        return 5
    return day["level"]


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
    gy = TITLE_H + 66
    top = max(d["count"] for d in days)

    # --- grid ---------------------------------------------------------------
    cells = []
    for d in days:
        offset = (date.fromisoformat(d["date"]) - start).days
        col, row = divmod(offset, 7)
        x, y = gx + col * pitch, gy + row * pitch
        lvl = level_of(d, top)
        n = d["count"]
        tip = f"{n} contribution{'s' if n != 1 else ''} le {fr_date(d['date'])}"
        cells.append(
            f'<rect class="c d{col + row}" x="{x:.2f}" y="{y:.2f}" width="{cell}" height="{cell}" rx="2.5" '
            f'fill="{PALETTE[lvl]}"><title>{escape(tip)}</title></rect>'
        )
    grid_h = 7 * pitch - GAP

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
                    f'<text x="{gx + col * pitch:.2f}" y="{gy - 9}" font-size="11" fill="{MUTED}">{MONTHS[d.month - 1]}</text>'
                )
                last_label_col = col
    for row, name in ((1, "Lun"), (3, "Mer"), (5, "Ven")):
        labels.append(
            f'<text x="{PAD}" y="{gy + row * pitch + cell - 2:.2f}" font-size="11" fill="{MUTED}">{name}</text>'
        )

    # --- header: total + legend ----------------------------------------------
    hy = TITLE_H + 30
    total = fr_number(stats["total"])
    header = (
        f'<text class="h" x="{PAD}" y="{hy}" font-size="14" fill="{FG}">'
        f'<tspan fill="{GREEN}" font-weight="700">{total}</tspan>'
        f" contributions au cours de la dernière année</text>"
    )
    lx = W - PAD - 6 * (cell + 4) - 36
    legend = [f'<text class="h" x="{lx - 8}" y="{hy}" font-size="11" fill="{MUTED}" text-anchor="end">Moins</text>']
    for i, color in enumerate(PALETTE):
        legend.append(
            f'<rect class="h" x="{lx + i * (cell + 4):.2f}" y="{hy - cell + 1:.2f}" width="{cell}" height="{cell}" rx="2.5" fill="{color}"/>'
        )
    legend.append(
        f'<text class="h" x="{lx + 6 * (cell + 4) + 4:.2f}" y="{hy}" font-size="11" fill="{MUTED}">Plus</text>'
    )

    height = round(gy + grid_h + PAD)

    # --- animation ------------------------------------------------------------
    ndiag = ncols + 6
    style = ""
    if not STATIC:
        style = (
            "@keyframes drop{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:none}}"
            "@keyframes fade{from{opacity:0}to{opacity:1}}"
            f".c{{animation:drop {DROP}s cubic-bezier(.2,.8,.3,1.2) both}}"
            ".h{animation:fade .5s ease-out both}"
            + "".join(f".d{i}{{animation-delay:{i * STEP:.3f}s}}" for i in range(ndiag))
        )

    body = (
        window(W, height, "lucas@github: ~/contributions")
        + header
        + "".join(legend)
        + "".join(labels)
        + "".join(cells)
    )
    label = f"{stats['total']} contributions GitHub au cours de la dernière année"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg_doc(W, height, body, style, label), encoding="utf-8")
    print(f"{ncols} weeks, {len(days)} days -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
