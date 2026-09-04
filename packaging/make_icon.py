# -*- coding: utf-8 -*-
"""Generate the program icon — drawn by code, not by hand.

    .venv/bin/python packaging/make_icon.py

Outputs (assets/): seqopt.png (512) · seqopt.ico (Windows) · seqopt.icns (macOS)

**The shape**: a rising curve on a blue rounded square (the response improving),
two measured points on it, and a target at the end (where to measure next).
Shrunk to 16px, the curve and the target survive. The color is the screen's
ACCENT (#0969da) — inside and outside the window must read as one program.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
ACCENT = (9, 105, 218)
ACCENT_DEEP = (7, 84, 176)
WHITE = (255, 255, 255)


def _bezier(p0, p1, p2, p3, n=64):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0]
        y = u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]
        pts.append((x, y))
    return pts


def draw(size: int = 1024) -> Image.Image:
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # base — rounded square, slightly darker at the bottom (flat, but reads like paper)
    radius = int(s * 0.22)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=radius, fill=ACCENT_DEEP)
    inset = int(s * 0.012)
    d.rounded_rectangle([0, 0, s - 1, s - 1 - inset], radius=radius, fill=ACCENT)

    # the rising curve
    pts = _bezier((0.20 * s, 0.74 * s), (0.46 * s, 0.74 * s),
                  (0.46 * s, 0.30 * s), (0.72 * s, 0.30 * s), n=600)
    # a thick line() shows its joints — densely stamped circles come out smooth
    w = s * 0.031
    for x, y in pts:
        d.ellipse([x - w, y - w, x + w, y + w], fill=WHITE)

    # two measured points
    r = s * 0.052
    for t in (0.18, 0.52):
        x, y = pts[int(t * (len(pts) - 1))]
        d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE)

    # the target — where to measure next
    cx, cy = pts[-1]
    ro, stroke, ri = s * 0.13, int(s * 0.05), s * 0.045
    d.ellipse([cx - ro, cy - ro, cx + ro, cy + ro], fill=ACCENT, outline=WHITE, width=stroke)
    d.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=WHITE)
    return img


def main() -> None:
    OUT.mkdir(exist_ok=True)
    big = draw(1024)
    big.resize((512, 512), Image.LANCZOS).save(OUT / "seqopt.png")
    sizes = [16, 24, 32, 48, 64, 128, 256]
    big.resize((256, 256), Image.LANCZOS).save(
        OUT / "seqopt.ico", sizes=[(n, n) for n in sizes])
    big.save(OUT / "seqopt.icns")
    for p in sorted(OUT.iterdir()):
        print(f"  {p.name:14s} {p.stat().st_size / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
