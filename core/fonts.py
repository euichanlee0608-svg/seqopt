# -*- coding: utf-8 -*-
"""CJK font lookup — screen, figures and PDF all follow the same rule.

Users may name their variables and conditions in Korean, Japanese or Chinese,
so the app keeps CJK rendering working wherever it can. **A PDF must embed the
font file** — without embedding, CJK text turns into squares (□) on another PC.

Search order
  1. `assets/fonts/*.ttf`  — a bundled font wins (the most reliable path)
  2. the OS default CJK font — Malgun Gothic on Windows · AppleGothic on macOS · Nanum/Noto on Linux
  3. none found → **fall back to Helvetica.** The report itself is English, so it
     stays readable; only user-entered CJK characters would degrade, and the
     caller can warn about that (`has_cjk`).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ASSET_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"

# reportlab reads TTF. TTC (collections) and OTF can fail, so they go last.
_CANDIDATES = {
    "win32": [
        r"C:\Windows\Fonts\malgun.ttf",
        r"C:\Windows\Fonts\NanumGothic.ttf",
        r"C:\Windows\Fonts\gulim.ttc",
    ],
    "darwin": [
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/Library/Fonts/NanumGothic.ttf",
    ],
    "linux": [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ],
}


def has_cjk(text: str) -> bool:
    """Does the text contain CJK characters (Hangul, Han, Kana)?"""
    return any(
        0xAC00 <= ord(c) <= 0xD7A3        # Hangul syllables
        or 0x4E00 <= ord(c) <= 0x9FFF     # CJK unified ideographs
        or 0x3040 <= ord(c) <= 0x30FF     # Kana
        or 0x1100 <= ord(c) <= 0x11FF     # Hangul jamo
        for c in text)


def bundled_fonts() -> list[Path]:
    if not ASSET_DIR.is_dir():
        return []
    return sorted(p for p in ASSET_DIR.iterdir() if p.suffix.lower() in (".ttf", ".ttc"))


def find_cjk_font() -> Path | None:
    """Path to a usable CJK font file, or None if the machine has none."""
    for p in bundled_fonts():
        return p
    key = "win32" if sys.platform.startswith("win") else \
          "darwin" if sys.platform == "darwin" else "linux"
    for path in _CANDIDATES[key]:
        if os.path.exists(path):
            return Path(path)
    return None


def register_pdf_font(name: str = "CJK") -> str:
    """Register a CJK-capable font with reportlab and return its name.

    Falls back to "Helvetica" when no CJK font exists — an English report must
    not fail to generate just because the machine has no Korean font installed.
    reportlab subsets fonts (only the glyphs actually used are embedded), so a
    15MB font does not bloat the PDF.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    if name in pdfmetrics.getRegisteredFontNames():
        return name
    path = find_cjk_font()
    if path is None:
        return "Helvetica"
    try:
        pdfmetrics.registerFont(TTFont(name, str(path)))
    except Exception:                            # noqa: BLE001
        return "Helvetica"                       # a broken font file must not block the report
    return name
