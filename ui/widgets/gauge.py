# -*- coding: utf-8 -*-
"""Discriminability gauge — where D sits, at a glance.

The bare number "D = 1.03 [0.49, 1.80]" tells a newcomer nothing. Four zones
(indistinguishable · borderline · usable · comfortable) are painted, the point
estimate is a vertical line, and the 95% interval is a horizontal bracket. A
bracket straddling the gate line (1.0) IS the "undecided" verdict, visually.
Zone boundaries and their basis come from core.diagnostics.D_LEVELS alone.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from core.diagnostics import D_COMFORTABLE, D_RECOMMENDED, D_THRESHOLD
from .. import theme

ZONES = [(0.0, D_THRESHOLD, theme.ZONE_BAD, "indistinguishable"),
         (D_THRESHOLD, D_RECOMMENDED, theme.ZONE_EDGE, "borderline"),
         (D_RECOMMENDED, D_COMFORTABLE, theme.ZONE_GOOD, "usable"),
         (D_COMFORTABLE, None, theme.ZONE_BEST, "comfortable")]


class DGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = None
        self.lo = None
        self.hi = None
        self.setMinimumHeight(96)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_value(self, value, lo=None, hi=None) -> None:
        self.value, self.lo, self.hi = value, lo, hi
        self.update()

    def _xmax(self) -> float:
        top = max(4.5, (self.hi or 0) + 0.4, (self.value or 0) + 0.6)
        return min(top, 12.0)

    def paintEvent(self, event) -> None:                       # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        left, right = 12, w - 12
        bar_y, bar_h = 40, 16
        xmax = self._xmax()

        def X(v: float) -> float:
            return left + (right - left) * min(v, xmax) / xmax

        small = QFont(self.font())
        small.setPixelSize(theme.SMALL - 1)
        p.setFont(small)

        # zone bands + names
        for lo, hi, colour, name in ZONES:
            x0, x1 = X(lo), X(hi if hi is not None else xmax)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(colour))
            p.drawRect(QRectF(x0, bar_y, x1 - x0, bar_h))
            p.setPen(QColor(theme.TEXT_MUTED))
            p.drawText(QRectF(x0, bar_y + bar_h + 2, x1 - x0, 18), Qt.AlignHCenter | Qt.AlignTop, name)

        # boundary ticks
        p.setPen(QPen(QColor(theme.TEXT_MUTED), 1))
        for v in (D_THRESHOLD, D_RECOMMENDED, D_COMFORTABLE):
            x = X(v)
            p.drawLine(int(x), bar_y - 3, int(x), bar_y + bar_h + 3)
            p.drawText(QRectF(x - 24, bar_y + bar_h + 18, 48, 16), Qt.AlignHCenter | Qt.AlignTop, f"{v:g}")
        p.drawText(QRectF(left - 10, bar_y + bar_h + 18, 30, 16), Qt.AlignHCenter | Qt.AlignTop, "0")

        if self.value is None:
            p.setPen(QColor(theme.TEXT_FAINT))
            p.drawText(QRectF(left, 8, right - left, 22), Qt.AlignLeft | Qt.AlignVCenter,
                       "Replicate measurements are needed to compute D")
            return

        # 95% interval bracket
        if self.lo is not None and self.hi is not None:
            x0, x1 = X(self.lo), X(self.hi)
            pen = QPen(QColor(theme.TEXT), 2)
            p.setPen(pen)
            y = bar_y - 12
            p.drawLine(int(x0), y, int(x1), y)
            p.drawLine(int(x0), y - 5, int(x0), y + 5)
            p.drawLine(int(x1), y - 5, int(x1), y + 5)

        # point-estimate line + value
        x = X(self.value)
        p.setPen(QPen(QColor(theme.TEXT), 2.5))
        p.drawLine(int(x), bar_y - 14, int(x), bar_y + bar_h + 2)
        bold = QFont(self.font())
        bold.setPixelSize(theme.FONT_SIZE)
        bold.setBold(True)
        p.setFont(bold)
        p.setPen(QColor(theme.TEXT))
        label = f"D = {self.value:.2f}"
        if self.lo is not None:
            label += f"   [{self.lo:.2f}, {self.hi:.2f}]"
        tw = 200
        tx = min(max(left, x - tw / 2), right - tw)
        p.drawText(QRectF(tx, 4, tw, 20), Qt.AlignHCenter | Qt.AlignVCenter, label)
