"""The opening pane (assets/neofetch.svg): neofetch, with the ASCII portrait as its logo.

Left, data/portrait-prepped.png as a monochrome ASCII portrait, each row printed by a
left-to-right wipe with a small block cursor riding the edge. Right, the name and the
facts the contribution graph can't tell, printing line by line while the portrait draws.
It plays once and freezes. STATIC=1 writes the final frame only.

Needs pillow + numpy, so it runs locally (once per photo or text change), not in the workflow.
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

from _svg import ACCENT, BODY_Y, FG, MUTED, PAD, RAMP, STATIC, SUB, W, delay, panel, prompt, svg_doc

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "portrait-prepped.png"
OUT = ROOT / "assets" / "neofetch.svg"

NAME = "Lucas Labonde"
ROLE = "Développeur full-stack & cloud · Normandie, France"
# Groups of (key, value); an empty key continues the value above.
INFO = [
    [
        ("Études", "Mastère Archi. des SI · CESI (Bac+5)"),
        ("Parcours", "5 ans d'alternance en grande entreprise"),
        ("Focus", "Archi logicielle · systèmes distribués"),
        ("", "Pipelines de données · IA"),
    ],
    [
        ("Langages", "Python · C# · TypeScript · JavaScript"),
        ("Front/Back", "React · .NET"),
        ("Cloud", "GCP · Docker · GitLab CI"),
        ("Data", "PostgreSQL · MySQL · MongoDB"),
        ("Outils", "Git · Figma"),
    ],
]

# --- portrait -------------------------------------------------------------------
RAMP_CHARS = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense)
#             ^ leading space keeps the background empty
COLS, ROWS = 96, 54
# Head-and-shoulders framing (left, top, right, bottom as fractions of the prepped photo):
# a tight crop gives the face enough characters for eyes, nose and beard to read.
CROP = (0.22, 0.0, 0.90, 0.66)
PORTRAIT_W = 352
CW = PORTRAIT_W / COLS  # char cell width
LH = CW * 2.0  # monospace glyphs are ~2x taller than wide
BOTTOM = BODY_Y + ROWS * LH
H = round(BOTTOM + PAD)

ROW_STAGGER = 0.04  # s between two rows starting
ROW_DUR = 0.3  # s for one row to print

# --- info column ----------------------------------------------------------------
X = PAD + PORTRAIT_W + 32
KEY_W = 96
STEP = 24  # line height
GROUP_GAP = 12
LINE_STAGGER = 0.1


def to_grid(img: Image.Image) -> list[str]:
    """Fit the subject into COLS x ROWS cells and map brightness to glyphs."""
    gray = np.asarray(img.getchannel("L"), np.float32) / 255
    alpha = np.asarray(img.getchannel("A"), np.float32) / 255
    h, w = gray.shape

    # Letterbox into the grid's aspect (cells are 1:2), anchored to the bottom.
    target = COLS * CW / (ROWS * LH)
    if w / h > target:
        pad_h = int(w / target) - h
        gray = np.pad(gray, ((pad_h, 0), (0, 0)))
        alpha = np.pad(alpha, ((pad_h, 0), (0, 0)))
    else:
        pad_w = int(h * target) - w
        gray = np.pad(gray, ((0, 0), (pad_w // 2, pad_w - pad_w // 2)))
        alpha = np.pad(alpha, ((0, 0), (pad_w // 2, pad_w - pad_w // 2)))

    def shrink(a: np.ndarray) -> np.ndarray:
        return np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((COLS, ROWS), Image.LANCZOS),
                          np.float32) / 255

    g, a = shrink(gray), shrink(alpha)
    lo, hi = np.percentile(g[a > 0.5], [3, 99])
    g = np.clip((g - lo) / max(hi - lo, 1e-6), 0, 1)
    # Ink = darkness, like pencil on paper: hair, brows and eyes print dense,
    # highlights and the removed background fall back to spaces.
    ink = (1 - g) * np.clip((a - 0.25) / 0.5, 0, 1)
    idx = np.clip((ink * (len(RAMP_CHARS) - 1)).round().astype(int), 0, len(RAMP_CHARS) - 1)
    return ["".join(RAMP_CHARS[i] for i in row) for row in idx]


def nbsp(row: str) -> str:
    # Non-breaking spaces survive SVG whitespace collapsing in every renderer.
    return escape(row).replace(" ", " ")


def portrait(begin: float) -> str:
    src = Image.open(SRC).convert("LA")
    w, h = src.size
    rows = to_grid(src.crop((round(CROP[0] * w), round(CROP[1] * h), round(CROP[2] * w), round(CROP[3] * h))))

    defs, text, cursors = [], [], []
    printed = 0
    for i, row in enumerate(rows):
        if not row.strip():
            continue
        y = BODY_Y + i * LH
        attrs = f'x="{PAD}" y="{y + LH * 0.78:.2f}" textLength="{PORTRAIT_W}" lengthAdjust="spacing"'
        if STATIC:
            text.append(f"<text {attrs}>{nbsp(row)}</text>")
            continue
        t = begin + printed * ROW_STAGGER
        printed += 1
        # Wipe only across the row's ink, so the cursor never crawls through empty space.
        x0 = PAD + (len(row) - len(row.lstrip())) * CW
        span = len(row.strip()) * CW
        defs.append(
            f'<clipPath id="r{i}"><rect x="{x0:.2f}" y="{y:.2f}" width="0" height="{LH + 0.5:.2f}">'
            f'<animate attributeName="width" from="0" to="{span:.2f}" begin="{t:.2f}s" dur="{ROW_DUR}s" fill="freeze"/>'
            f"</rect></clipPath>"
        )
        text.append(f'<text clip-path="url(#r{i})" {attrs}>{nbsp(row)}</text>')
        cursors.append(
            f'<rect x="{x0:.2f}" y="{y + 1:.2f}" width="{CW:.2f}" height="{LH - 2:.2f}" fill="{ACCENT}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{t:.2f}s"/>'
            f'<animate attributeName="x" from="{x0:.2f}" to="{x0 + span:.2f}" begin="{t:.2f}s" dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{t + ROW_DUR:.2f}s"/>'
            f"</rect>"
        )
    return (
        (f"<defs>{''.join(defs)}</defs>" if defs else "")
        + f'<g fill="{FG}" font-size="{CW / 0.6:.2f}">{"".join(text)}</g>'
        + "".join(cursors)
    )


def value_markup(value: str) -> str:
    sep = f'<tspan fill="{MUTED}"> · </tspan>'
    return sep.join(escape(part) for part in value.split(" · "))


def info(begin: float) -> str:
    out, n = [], 0

    def line(markup: str) -> None:
        nonlocal n
        out.append(f"<g{delay(begin + n * LINE_STAGGER)}>{markup}</g>")
        n += 1

    line(f'<text x="{X}" y="{BODY_Y + 32}" font-size="28" font-weight="600" fill="{FG}">{escape(NAME)}</text>')
    line(f'<text x="{X}" y="{BODY_Y + 60}" font-size="14" fill="{SUB}">{value_markup(ROLE)}</text>')

    y = BODY_Y + 104
    for group in INFO:
        for key, value in group:
            key_markup = f'<tspan x="{X}" fill="{MUTED}">{escape(key)}</tspan>' if key else ""
            line(f'<text y="{y}" font-size="13">{key_markup}'
                 f'<tspan x="{X + KEY_W}" fill="{FG}">{value_markup(value)}</tspan></text>')
            y += STEP
        y += GROUP_GAP

    # neofetch ends on the terminal's palette; this terminal's palette is the contribution ramp.
    blocks = "".join(
        f'<rect x="{X + i * 28}" y="{BOTTOM - 16:.1f}" width="24" height="16" rx="3" fill="{c}"/>'
        for i, c in enumerate(RAMP)
    )
    line(blocks)
    return "".join(out)


def main() -> None:
    head, typed = prompt("neofetch")
    body = panel(H) + head + portrait(typed) + info(typed + 0.2)
    label = f"{NAME} — {ROLE}. " + " / ".join(f"{k} : {v}" if k else v for g in INFO for k, v in g)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg_doc(W, H, body, label=label), encoding="utf-8")
    print(f"{COLS}x{ROWS} chars, {W}x{H} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
