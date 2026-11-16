"""Render data/contributions.json as the two stats panes that sit side by side:

  assets/stats-months.svg   wide: contributions per month, the best month in the accent
  assets/stats-records.svg  narrow: streaks, active days, best day, average

The README shows them at 66 % and 34 % with no space between, so the gutter lives inside
the SVGs and both share one height. Figures rise in, bars grow, once.
STATIC=1 writes the final frame only. Stdlib only.
"""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from _svg import (ACCENT, BODY_Y, EASE, FG, LINE, MONTHS_SHORT, MUTED, PAD, STATIC, SUB, W, delay, fr_date,
                  fr_number, panel, prompt, svg_doc)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "assets"

GUTTER = 16
MONTHS_W = 560
RECORDS_W = W - MONTHS_W - GUTTER
ROW = 48  # one record
ROWS = 5
H = BODY_Y + ROWS * ROW + PAD - 8
BAR_COLOR = "#2f363f"  # neutral step: only the best month takes the accent
BAR_W = 24


def span(streak: dict, empty: str) -> str:
    if not streak["days"]:
        return empty
    a, b = fr_date(streak["start"]), fr_date(streak["end"])
    return a if a == b else f"{a} → {b}"


def days_unit(n: int) -> str:
    return "jour" if n <= 1 else "jours"  # French: 0 jour, 1 jour, 2 jours


def months_pane(s: dict) -> str:
    head, t = prompt("./stats.sh --mois", "contributions par mois", width=MONTHS_W)
    base = H - PAD - 24  # the line the bars stand on, month names below it
    max_h = base - (BODY_Y + 28)
    months = list(s["monthly"].items())
    top = max(v for _, v in months) or 1
    # Highlight a single bar: the most recent of the best months.
    top_i = max((i for i, (_, v) in enumerate(months) if v == top), default=-1)

    body = [panel(H, MONTHS_W), head,
            f'<line{delay(t)} x1="{PAD}" y1="{base}.5" x2="{MONTHS_W - PAD}" y2="{base}.5" stroke="{LINE}"/>']
    slot = (MONTHS_W - 2 * PAD) / len(months)
    for i, (month, v) in enumerate(months):
        cx = PAD + (i + 0.5) * slot
        bh = max(v / top * max_h, 2)
        is_top = i == top_i and v > 0
        bt = t + 0.1 + i * 0.04
        grow = "" if STATIC else f' class="b" style="animation-delay:{bt:.2f}s"'
        body.append(
            f'<rect{grow} x="{cx - BAR_W / 2:.1f}" y="{base - bh:.1f}" width="{BAR_W}" height="{bh:.1f}" rx="3" '
            f'fill="{ACCENT if is_top else BAR_COLOR}"><title>{escape(month)} : {v}</title></rect>'
            f'<text{delay(bt + 0.3)} x="{cx:.1f}" y="{base - bh - 8:.1f}" text-anchor="middle" '
            f'font-size="12" fill="{FG if is_top else MUTED}">{fr_number(v)}</text>'
            f'<text{delay(t)} x="{cx:.1f}" y="{base + 20}" text-anchor="middle" font-size="12" '
            f'fill="{SUB if is_top else MUTED}">{MONTHS_SHORT[int(month[5:]) - 1]}</text>'
        )
    style = "" if STATIC else (
        "@keyframes grow{from{transform:scaleY(0)}to{transform:none}}"
        f".b{{transform-box:fill-box;transform-origin:50% 100%;animation:grow .5s {EASE} both}}"
    )
    label = "Contributions par mois : " + ", ".join(f"{m} {v}" for m, v in months)
    return svg_doc(MONTHS_W + GUTTER / 2, H, "".join(body), style, label)


def records_pane(s: dict) -> str:
    cur, best = s["current_streak"], s["longest_streak"]
    avg = s["total"] / s["active_days"] if s["active_days"] else 0
    best_day = s["best_day"]
    records = [  # (label, detail, value, unit)
        ("Série en cours", span(cur, "aucune en cours"), str(cur["days"]), days_unit(cur["days"])),
        ("Plus longue série", span(best, "aucune pour l'instant"), str(best["days"]), days_unit(best["days"])),
        ("Jours actifs", f"{fr_number(100 * s['active_days'] / s['days'])} % de l'année", str(s["active_days"]),
         f"/ {s['days']}"),
        ("Meilleur jour", f"le {fr_date(best_day['date'])}" if best_day["count"] else "—",
         fr_number(best_day["count"]), ""),
        ("Par jour actif", "en moyenne", fr_number(avg, 1), ""),
    ]
    head, t = prompt("./stats.sh", width=RECORDS_W)
    body = [panel(H, RECORDS_W), head]
    for i, (label, detail, value, unit) in enumerate(records):
        y = BODY_Y + i * ROW
        unit_markup = f'<tspan font-size="12" fill="{MUTED}"> {escape(unit)}</tspan>' if unit else ""
        rule = f'<line x1="{PAD}" y1="{y}.5" x2="{RECORDS_W - PAD}" y2="{y}.5" stroke="{LINE}"/>'
        body.append(
            f"<g{delay(t + i * 0.06)}>{rule}"
            f'<text x="{PAD}" y="{y + 21}" font-size="12" fill="{SUB}">{escape(label)}</text>'
            f'<text x="{PAD}" y="{y + 38}" font-size="12" fill="{MUTED}">{escape(detail)}</text>'
            f'<text x="{RECORDS_W - PAD}" y="{y + 32}" font-size="20" fill="{FG}" text-anchor="end">'
            f"{escape(value)}{unit_markup}</text></g>"
        )
    label = "Statistiques : " + ", ".join(f"{r[0]} {r[2]} {r[3]}".strip() for r in records)
    inner = f'<g transform="translate({GUTTER / 2:g} 0)">{"".join(body)}</g>'
    return svg_doc(RECORDS_W + GUTTER / 2, H, inner, label=label)


def main() -> None:
    s = json.loads(DATA.read_text(encoding="utf-8"))["stats"]
    OUT.mkdir(parents=True, exist_ok=True)
    for name, svg in (("stats-months", months_pane(s)), ("stats-records", records_pane(s))):
        (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
        print(f"assets/{name}.svg")


if __name__ == "__main__":
    main()
