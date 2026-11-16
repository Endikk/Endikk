"""The closing pane (assets/session.svg): the terminal keeps running.

Three commands are typed in turn, each prints one line, and the loop starts again.
It is the only thing on the profile that loops. STATIC=1 writes the first answer only.
Stdlib only; reads data/repos.json for the repo count.
"""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from _svg import ACCENT, ADV, FG, KEY, MUTED, PAD, PROMPT_FONT, PROMPT_Y, STATIC, SUB, USER, W, panel, svg_doc

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "repos.json"
OUT = ROOT / "assets" / "session.svg"

HOLD = 5.0  # s per command: typed, answered, read
ANSWER_Y = PROMPT_Y + 24
H = ANSWER_Y + PAD


def frames(pairs: list[tuple[float, object]], total: float) -> str:
    """SMIL discrete keyframes from (time, value) pairs; the value before the first pair is 0."""
    if pairs[0][0] > 0:
        pairs = [(0, 0)] + pairs
    values = ";".join(f"{v:.1f}" if isinstance(v, float) else str(v) for _, v in pairs)
    times = ";".join(f"{t / total:.4f}" for t, _ in pairs)
    return f'values="{values}" keyTimes="{times}" calcMode="discrete" dur="{total:g}s" repeatCount="indefinite"'


def main() -> None:
    repos = json.loads(DATA.read_text(encoding="utf-8"))["public_repos"]
    lines = [
        ("cat hors-code.txt", "Formule 1 · Basket · Veille tech"),
        ("ls ~/projets | wc -l", f"{repos} dépôts publics, dont les quatre épinglés plus haut"),
        ("cat contact.txt", "Un projet, une opportunité ou une question tech : écris-moi"),
    ]
    total = HOLD * len(lines)
    cw = PROMPT_FONT * ADV
    head = f"{USER} ~ $ "
    x_cmd = PAD + len(head) * cw
    top = PROMPT_Y - PROMPT_FONT + 1

    body = [
        panel(H),
        f'<text x="{PAD}" y="{PROMPT_Y}" font-size="{PROMPT_FONT}" textLength="{len(head.rstrip()) * cw:.1f}" '
        f'lengthAdjust="spacing"><tspan fill="{SUB}">{USER}</tspan><tspan fill="{MUTED}"> ~ $</tspan></text>',
    ]
    cursor_x: list[tuple[float, object]] = []
    for i, (cmd, answer) in enumerate(lines):
        t0, n = i * HOLD + 0.6, len(cmd)
        typed = t0 + n * KEY
        text = (f'<text x="{x_cmd:.1f}" y="{PROMPT_Y}" font-size="{PROMPT_FONT}" fill="{FG}" '
                f'textLength="{n * cw:.1f}" lengthAdjust="spacing"')
        reply = f'<text x="{PAD}" y="{ANSWER_Y}" font-size="{PROMPT_FONT}" fill="{SUB}"'
        answer = escape(answer).replace(" · ", f'<tspan fill="{MUTED}"> · </tspan>')
        if STATIC:
            if i == 0:
                body.append(f"{text}>{escape(cmd)}</text>{reply}>{answer}</text>")
                cursor_x.append((0, x_cmd + n * cw))
            continue
        end = (i + 1) * HOLD
        widths = [(t0 + j * KEY, j * cw) for j in range(n + 1)]
        shown: list[tuple[float, object]] = [(typed + 0.3, 1)]
        if end < total:  # the last command is cleared by the loop restarting
            widths.append((end, 0.0))
            shown.append((end, 0))
        body.append(
            f'<clipPath id="c{i}"><rect x="{x_cmd:.1f}" y="{top - 2}" width="0" height="{PROMPT_FONT + 9}">'
            f'<animate attributeName="width" {frames(widths, total)}/></rect></clipPath>'
            f'{text} clip-path="url(#c{i})">{escape(cmd)}</text>'
            f'{reply} opacity="0">{answer}<animate attributeName="opacity" {frames(shown, total)}/></text>'
        )
        cursor_x += [(i * HOLD, x_cmd)] + [(t0 + j * KEY, x_cmd + j * cw) for j in range(1, n + 1)]

    cursor = f'<rect y="{top}" width="{cw:.1f}" height="{PROMPT_FONT + 3}" fill="{ACCENT}"'
    if STATIC:
        body.append(f'{cursor} x="{cursor_x[0][1]:.1f}"/>')
    else:
        body.append(
            f'{cursor} x="{x_cmd:.1f}"><animate attributeName="x" {frames(cursor_x, total)}/>'
            f'<animate attributeName="opacity" values="1;0" keyTimes="0;.6" calcMode="discrete" dur="1.1s" '
            f'repeatCount="indefinite"/></rect>'
        )

    label = "Terminal : " + " / ".join(f"{cmd} → {answer}" for cmd, answer in lines)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg_doc(W, H, "".join(body), label=label), encoding="utf-8")
    print(f"{len(lines)} commands, {W}x{H} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
