"""Prep a photo for ASCII conversion: isolate the subject, boost local contrast.

usage: python scripts/prep_photo.py [photo path or URL]   (default: your GitHub avatar)

1. Background removal with rembg (falls back to OpenCV GrabCut if rembg isn't installed).
2. CLAHE on the luminance, so a flatly-lit face gets real highlights and shadows.
3. Crop to the subject and save gray + alpha to data/portrait-prepped.png.

Run once per photo; the daily workflow never needs this.
"""

from __future__ import annotations

import io
import sys
import urllib.request
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "portrait-prepped.png"
DEFAULT_SRC = "https://github.com/Endikk.png?size=460"


def load(src: str) -> Image.Image:
    if src.startswith(("http://", "https://")):
        with urllib.request.urlopen(src, timeout=30) as resp:
            src = io.BytesIO(resp.read())
    img = Image.open(src).convert("RGBA")
    # Flatten any transparency (round avatars) onto white before segmenting.
    flat = Image.new("RGBA", img.size, (255, 255, 255, 255))
    flat.alpha_composite(img)
    return flat.convert("RGB")


def subject_mask(rgb: Image.Image) -> np.ndarray:
    """Float mask in [0, 1], 1 = subject."""
    try:
        from rembg import remove

        return np.asarray(remove(rgb, post_process_mask=True).getchannel("A"), np.float32) / 255
    except ImportError:
        print("rembg not installed - using GrabCut (rougher edges)", file=sys.stderr)
        bgr = cv2.cvtColor(np.asarray(rgb), cv2.COLOR_RGB2BGR)
        h, w = bgr.shape[:2]
        mask = np.zeros((h, w), np.uint8)
        rect = (int(w * 0.08), int(h * 0.04), int(w * 0.84), int(h * 0.95))
        cv2.grabCut(bgr, mask, rect, np.zeros((1, 65)), np.zeros((1, 65)), 6, cv2.GC_INIT_WITH_RECT)
        fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1.0, 0.0).astype(np.float32)
        return cv2.GaussianBlur(fg, (5, 5), 0)


def main() -> None:
    rgb = load(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC)
    alpha = subject_mask(rgb)

    gray = cv2.cvtColor(np.asarray(rgb), cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)

    ys, xs = np.nonzero(alpha > 0.15)
    m = 6
    y0, y1 = max(ys.min() - m, 0), min(ys.max() + m, gray.shape[0])
    x0, x1 = max(xs.min() - m, 0), min(xs.max() + m, gray.shape[1])

    la = np.dstack([gray[y0:y1, x0:x1], (alpha[y0:y1, x0:x1] * 255).astype(np.uint8)])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(la).save(OUT)  # (h, w, 2) uint8 -> "LA"
    print(f"{x1 - x0}x{y1 - y0} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
