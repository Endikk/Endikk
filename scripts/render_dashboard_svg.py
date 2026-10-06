"""Render data/contributions.json as a stats dashboard (assets/stats-dashboard.svg).

Six stat tiles (streaks, totals, best day, average) and a contributions-per-month bar
chart. Sits next to the ASCII portrait, so its height follows the portrait's.
Tiles fade up one after another, then the bars grow - once, no loop.
STATIC=1 writes the final frame only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from xml.sax.saxutils import escape

from _svg import BAR, BORDER, FG, GREEN, MUTED, TITLE_H, fr_date, fr_number, height_beside, svg_doc, window

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
PORTRAIT = ROOT / "assets" / "lucas-ascii.svg"
OUT = ROOT / "assets" / "stats-dashboard.svg"
STATIC = os.environ.get("STATIC") == "1"

W = 490  # README widths: portrait 370 + dashboard 490 = heatmap 860
PAD = 14
GAP = 10
TILE_H = 72
BAR_COLOR, TOP_COLOR = "#26a641", "#69f0a0"
INITIALS = "JFMAMJJASOND"


def span(streak: dict, empty: str) -> str:
    if not streak["days"]:
        return empty
    a, b = fr_date(streak["start"]), fr_date(streak["end"])
    return a if a == b else f"{a} → {b}"


def days_unit(n: int) -> str:
    return "jour" if n <= 1 else "jours"  # French: 0 jour, 1 jour, 2 jours


def tile(x: float, y: float, w: float, label: str, value: str, unit: str, sub: str, delay: float) -> str:
    unit_markup = f'<tspan font-size="12" font-weight="400" fill="{MUTED}"> {escape(unit)}</tspan>' if unit else ""
    return (
        f'<g class="t" style="animation-delay:{delay:.2f}s">'
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{TILE_H}" rx="6" fill="{BAR}" stroke="{BORDER}"/>'
        f'<text x="{x + 12:.1f}" y="{y + 19:.1f}" font-size="11" fill="{MUTED}">$ {escape(label)}</text>'
        f'<text x="{x + 12:.1f}" y="{y + 46:.1f}" font-size="24" font-weight="700" fill="{GREEN}">'
        f"{escape(value)}{unit_markup}</text>"
        f'<text x="{x + 12:.1f}" y="{y + 62:.1f}" font-size="10" fill="{MUTED}">{escape(sub)}</text>'
        "</g>"
    )


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    s = data["stats"]
    height = height_beside(PORTRAIT)

    cur, best = s["current_streak"], s["longest_streak"]
    avg = s["total"] / s["active_days"] if s["active_days"] else 0
    best_day = s["best_day"]
    tiles = [
        ("série en cours", str(cur["days"]), days_unit(cur["days"]), span(cur, "aucune en cours")),
        ("plus longue série", str(best["days"]), days_unit(best["days"]), span(best, "aucune pour l'instant")),
        ("contributions", fr_number(s["total"]), "", "sur la dernière année"),
        ("jours actifs", str(s["active_days"]), f"/ {s['days']}",
         f"{fr_number(100 * s['active_days'] / s['days'])} % de l'année"),
        ("meilleur jour", fr_number(best_day["count"]), "", fr_date(best_day["date"]) if best_day["count"] else "—"),
        ("moy. / jour actif", fr_number(avg, 1), "", "contributions"),
    ]

    body = [window(W, height, "lucas@github: ~/stats.sh")]
    tw = (W - 2 * PAD - GAP) / 2
    y0 = TITLE_H + PAD
    for i, (label, value, unit, sub) in enumerate(tiles):
        col, row = i % 2, i // 2
        body.append(tile(PAD + col * (tw + GAP), y0 + row * (TILE_H + GAP), tw, label, value, unit, sub, 0.2 + i * 0.12))

    # --- contributions / month ------------------------------------------------
    cy = y0 + 3 * (TILE_H + GAP)
    ch = height - PAD - cy
    cw = W - 2 * PAD
    months = list(s["monthly"].items())
    top = max(v for _, v in months) or 1
    # Highlight a single bar: the most recent of the best months.
    top_i = max((i for i, (_, v) in enumerate(months) if v == top), default=-1)
    chart_delay = 0.2 + len(tiles) * 0.12
    body.append(
        f'<g class="t" style="animation-delay:{chart_delay:.2f}s">'
        f'<rect x="{PAD}" y="{cy:.1f}" width="{cw}" height="{ch:.1f}" rx="6" fill="{BAR}" stroke="{BORDER}"/>'
        f'<text x="{PAD + 12}" y="{cy + 19:.1f}" font-size="11" fill="{MUTED}">$ contributions / mois</text></g>'
    )
    base = cy + ch - 24  # bars stand on this line, initials sit below it
    max_h = base - (cy + 44)
    slot = (cw - 24) / len(months)
    bw = slot * 0.62
    for i, (month, v) in enumerate(months):
        bx = PAD + 12 + i * slot + (slot - bw) / 2
        bh = max(v / top * max_h, 2)
        is_top = i == top_i and v > 0
        delay = chart_delay + 0.3 + i * 0.06
        body.append(
            f'<rect class="b" style="animation-delay:{delay:.2f}s" x="{bx:.1f}" y="{base - bh:.1f}" width="{bw:.1f}" '
            f'height="{bh:.1f}" rx="2" fill="{TOP_COLOR if is_top else BAR_COLOR}" opacity="{1 if v else 0.35}">'
            f"<title>{escape(month)} : {v}</title></rect>"
            f'<text class="t" style="animation-delay:{chart_delay:.2f}s" x="{bx + bw / 2:.1f}" y="{base + 15:.1f}" '
            f'text-anchor="middle" font-size="10" fill="{MUTED}">{INITIALS[int(month[5:]) - 1]}</text>'
        )
        if is_top:
            body.append(
                f'<text class="t" style="animation-delay:{delay + 0.5:.2f}s" x="{bx + bw / 2:.1f}" y="{base - bh - 6:.1f}" '
                f'text-anchor="middle" font-size="11" font-weight="700" fill="{FG}">{fr_number(v)}</text>'
            )

    style = ""
    if not STATIC:
        style = (
            "@keyframes up{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
            "@keyframes grow{from{transform:scaleY(0)}to{transform:none}}"
            ".t{animation:up .45s ease-out both}"
            ".b{transform-box:fill-box;transform-origin:50% 100%;animation:grow .6s cubic-bezier(.2,.8,.3,1) both}"
        )

    label = (
        f"Statistiques GitHub : {s['total']} contributions, série en cours {cur['days']} j, "
        f"plus longue série {best['days']} j, {s['active_days']} jours actifs"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg_doc(W, height, "".join(body), style, label), encoding="utf-8")
    print(f"{len(months)} months, {W}x{height} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
