# -*- coding: utf-8 -*-
"""Draws formulas as real formulas — matplotlib mathtext (no LaTeX install needed).

**Why HTML subscripts were not enough**

`σ<sub>w</sub> = √( 0.2436 / 30 )` is a row of characters, not a formula. The
radical does not cover its operand, fractions lie flat on one line, and
subscripts do not match the body size (users said "the formulas and symbols
render badly"). mathtext typesets a subset of TeX with its own engine —
radicals, fractions and scripts come out right, and the font (DejaVu) ships
inside matplotlib, so a frozen build renders identically.

**Rules**
  · matplotlib is imported **the first time a formula is drawn** — never before the window shows.
  · Each formula is typeset once (cached). First render ≈ 0.1 s, then 0.
  · No CJK inside mathtext (DejaVu has none). The explanation lives in the QLabel next to it.
"""
from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import QApplication, QGridLayout, QLabel, QSizePolicy, QWidget

from .. import theme


@lru_cache(maxsize=256)
def _render(tex: str, px: int, color: str, dpr: float) -> QImage:
    import numpy as np
    from matplotlib.font_manager import FontProperties
    from matplotlib.mathtext import MathTextParser

    parser = MathTextParser("agg")
    # At dpi 72, 1pt = 1px. Raising dpi by the scale factor (dpr) keeps hi-DPI screens sharp.
    out = parser.parse(f"${tex}$", dpi=72 * dpr, prop=FontProperties(size=px))
    alpha = np.asarray(out.image, dtype=np.uint8)
    h, w = alpha.shape
    c = QColor(color)
    a16 = alpha.astype(np.uint16)
    bgra = np.empty((h, w, 4), dtype=np.uint8)
    bgra[..., 0] = c.blue() * a16 // 255           # premultiplied alpha
    bgra[..., 1] = c.green() * a16 // 255
    bgra[..., 2] = c.red() * a16 // 255
    bgra[..., 3] = alpha
    img = QImage(bgra.data, w, h, w * 4, QImage.Format_ARGB32_Premultiplied).copy()
    img.setDevicePixelRatio(dpr)
    return img


def render(tex: str, px: int = 16, color: str = theme.TEXT) -> QPixmap:
    app = QApplication.instance()
    dpr = float(app.devicePixelRatio()) if app else 1.0
    return QPixmap.fromImage(_render(tex, px, color, dpr))


class MathLabel(QLabel):
    """One formula. `text()` returns the raw TeX (for tests and copying)."""

    def __init__(self, tex: str = "", px: int = 16, color: str = theme.TEXT, parent=None):
        super().__init__(parent)
        self._tex, self._px, self._color = "", px, color
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        if tex:
            self.set_tex(tex)

    def set_tex(self, tex: str) -> None:
        self._tex = tex
        self.setPixmap(render(tex, self._px, self._color))
        self.setToolTip(tex)

    def text(self) -> str:                                     # noqa: D102
        return self._tex


class FormulaCard(QWidget):
    """Several formula lines — formula left, prose right. Equals signs align vertically."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(18)
        self.grid.setVerticalSpacing(10)
        self.grid.setColumnStretch(1, 1)
        self._rows: list[tuple[str, str]] = []
        self.message = QLabel()
        self.message.setWordWrap(True)
        theme.set_role(self.message, "muted")
        self.message.setVisible(False)
        self.grid.addWidget(self.message, 0, 0, 1, 2)

    def clear(self) -> None:
        self._rows = []
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w is not None and w is not self.message:
                w.deleteLater()
        self.grid.addWidget(self.message, 0, 0, 1, 2)

    def set_lines(self, lines: list[tuple[str, str]], px: int = 16) -> None:
        """lines = [(tex, prose), …]. An empty tex inserts a separator gap."""
        self.clear()
        self.message.setVisible(False)
        row = 1
        for tex, note in lines:
            if not tex:
                self.grid.setRowMinimumHeight(row, 6)
                row += 1
                continue
            self._rows.append((tex, note))
            m = MathLabel(tex, px=px)
            self.grid.addWidget(m, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
            n = QLabel(note)
            n.setWordWrap(True)
            theme.set_role(n, "desc")
            # An alignment flag stops the label from filling its cell — it sits at
            # sizeHint size and word-wrap heights go wrong. Let it fill the cell
            # and center only the text vertically.
            n.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            n.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.grid.addWidget(n, row, 1)
            row += 1

    def set_message(self, text: str) -> None:
        self.clear()
        self.message.setText(text)
        self.message.setVisible(True)

    def text(self) -> str:
        """For tests — every formula (TeX) plus prose as one string."""
        return "\n".join(f"{tex}  {note}" for tex, note in self._rows) or self.message.text()
