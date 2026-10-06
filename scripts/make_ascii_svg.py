"""Turn data/portrait-prepped.png into a monochrome ASCII portrait that types itself in.

Each row is revealed by a left-to-right clip wipe (SMIL) with a small block cursor riding
the edge, staggered top to bottom. It prints once and freezes - no loop.

STATIC=1 writes the final frame only (handy for previews).
"""

from __future__ import annotations

import os
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

from _svg import BLUE, FG, GREEN, TITLE_H, svg_doc, window

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "portrait-prepped.png"
OUT = ROOT / "assets" / "lucas-ascii.svg"
STATIC = os.environ.get("STATIC") == "1"

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense)
#       ^ leading space keeps the background empty

COLS, ROWS = 96, 54
# Head-and-shoulders framing (left, top, right, bottom as fractions of the prepped photo):
# a tight crop gives the face enough characters for eyes, nose and beard to read.
CROP = (0.22, 0.0, 0.90, 0.66)
W = 600
DISPLAY_W = 370  # width the README shows it at
CHROME = W / DISPLAY_W  # scale the title bar to match the other panels on screen
PAD = 18
CW = (W - 2 * PAD) / COLS  # char cell width
LH = CW * 2.0  # monospace glyphs are ~2x taller than wide
TOP = TITLE_H * CHROME + PAD
# Prompt line under the portrait, sized in on-screen px then scaled like the chrome.
PROMPT = ("lucas@github", ":~ $ whoami  ", "Lucas Labonde")
PROMPT_FONT = 11.5 * CHROME
PROMPT_Y = TOP + ROWS * LH + 20 * CHROME
H = round(PROMPT_Y + 12 * CHROME)

ROW_STAGGER = 0.045  # s between two rows starting
ROW_DUR = 0.32  # s for one row to print
TYPE_DUR = 0.9  # s to type the prompt line


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
    idx = np.clip((ink * (len(RAMP) - 1)).round().astype(int), 0, len(RAMP) - 1)
    return ["".join(RAMP[i] for i in row) for row in idx]


def nbsp(row: str) -> str:
    # Non-breaking spaces survive SVG whitespace collapsing in every renderer.
    return escape(row).replace(" ", "\u00a0")


def main() -> None:
    src = Image.open(SRC).convert("LA")
    w, h = src.size
    rows = to_grid(src.crop((round(CROP[0] * w), round(CROP[1] * h), round(CROP[2] * w), round(CROP[3] * h))))
    inner = W - 2 * PAD
    font = CW / 0.6

    defs, text, cursors = [], [], []
    printed = 0
    for i, row in enumerate(rows):
        if not row.strip():
            continue
        y = TOP + i * LH
        attrs = (f'x="{PAD}" y="{y + LH * 0.78:.2f}" textLength="{inner}" lengthAdjust="spacing"')
        if STATIC:
            text.append(f"<text {attrs}>{nbsp(row)}</text>")
            continue
        t = printed * ROW_STAGGER
        printed += 1
        # Wipe only across the row's ink, so the cursor never crawls through empty space.
        x0 = PAD + (len(row) - len(row.lstrip())) * CW
        span = len(row.strip()) * CW
        defs.append(
            f'<clipPath id="r{i}"><rect x="{x0:.2f}" y="{y:.2f}" width="0" height="{LH + 0.5:.2f}">'
            f'<animate attributeName="width" from="0" to="{span:.2f}" begin="{t:.3f}s" dur="{ROW_DUR}s" fill="freeze"/>'
            f"</rect></clipPath>"
        )
        text.append(f'<text clip-path="url(#r{i})" {attrs}>{nbsp(row)}</text>')
        cursors.append(
            f'<rect x="{x0:.2f}" y="{y + 1:.2f}" width="{CW:.2f}" height="{LH - 2:.2f}" fill="{GREEN}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{t:.3f}s"/>'
            f'<animate attributeName="x" from="{x0:.2f}" to="{x0 + span:.2f}" begin="{t:.3f}s" dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{t + ROW_DUR:.3f}s"/>'
            f"</rect>"
        )

    # Prompt: typed once the portrait is done, then a blinking block cursor.
    # textLength pins its width, so the cursor lands right after it in any monospace font.
    n = sum(len(part) for part in PROMPT)
    prompt_w = n * PROMPT_FONT * 0.6
    user, mid, name = (escape(part) for part in PROMPT)
    clip = "" if STATIC else ' clip-path="url(#prompt)"'
    prompt = (
        f'<text x="{PAD}" y="{PROMPT_Y:.2f}" font-size="{PROMPT_FONT:.2f}" textLength="{prompt_w:.2f}" '
        f'lengthAdjust="spacing"{clip}>'
        f'<tspan fill="{GREEN}">{user}</tspan><tspan fill="{BLUE}">{mid}</tspan>'
        f'<tspan fill="{FG}" font-weight="700">{name}</tspan></text>'
    )
    cx, cy = PAD + prompt_w + PROMPT_FONT * 0.3, PROMPT_Y - PROMPT_FONT * 0.8
    cursor = f'<rect x="{cx:.2f}" y="{cy:.2f}" width="{PROMPT_FONT * 0.55:.2f}" height="{PROMPT_FONT:.2f}" fill="{FG}"'
    if STATIC:
        cursor += "/>"
    else:
        t = printed * ROW_STAGGER + ROW_DUR
        steps = ";".join(f"{i / n * (prompt_w + 2):.1f}" for i in range(n + 1))
        defs.append(
            f'<clipPath id="prompt"><rect x="{PAD}" y="{cy - 4:.2f}" width="0" height="{PROMPT_FONT * 1.6:.2f}">'
            f'<animate attributeName="width" values="{steps}" calcMode="discrete" begin="{t:.3f}s" '
            f'dur="{TYPE_DUR}s" fill="freeze"/>'
            f"</rect></clipPath>"
        )
        cursor += (
            f' opacity="0"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.1s" '
            f'begin="{t + TYPE_DUR:.3f}s" repeatCount="indefinite"/></rect>'
        )

    body = (
        window(W, H, "lucas@github: ~/portrait.txt", CHROME)
        + (f"<defs>{''.join(defs)}</defs>" if defs else "")
        + f'<g fill="{FG}" font-size="{font:.2f}">{"".join(text)}</g>'
        + "".join(cursors)
        + prompt
        + cursor
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg_doc(W, H, body, label="Portrait ASCII de Lucas"), encoding="utf-8")
    print(f"{COLS}x{ROWS} chars, {W}x{H} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
